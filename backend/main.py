import os
import json
import math
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io
from typing import Optional
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core.exceptions import ResourceExhausted
from supabase import create_client, Client
from fpdf import FPDF

load_dotenv()

# Configure environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not GEMINI_API_KEY or not SUPABASE_URL or not SUPABASE_KEY:
    print("Warning: Missing required environment variables. Please check your .env file.")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

# Initialize Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

safety_settings = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}
# Migrate to flash-lite for higher quota
model = genai.GenerativeModel("gemini-2.5-flash-lite", safety_settings=safety_settings)

# Define Pydantic models for the request and response
class IssueSubmitRequest(BaseModel):
    description: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image_url: Optional[str] = None
    reporter_name: Optional[str] = None
    reporter_phone: Optional[str] = None

class CheckDuplicateRequest(BaseModel):
    description: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class GeneratePDFRequest(BaseModel):
    name: str
    phone: str
    description: str
    category: str
    location: str

app = FastAPI(title="Vox Backend", description="Vox civic grievance platform backend API")

@app.post("/api/submit-issue")
async def submit_issue(request: IssueSubmitRequest):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
        
    # Step 1: Use Gemini to extract issue details and check for missing location info
    extraction_prompt = f"""
    You are an AI assistant for a civic grievance platform called "Vox".
    Analyze the following issue description:
    "{request.description}"
    
    1. Extract the 'issue_type' (e.g., Pothole, Water Leak, Garbage, etc.).
    2. Extract the 'severity' (Low, Medium, High, Critical).
    3. Extract the 'ward' or specific location area if mentioned.
    4. Determine if sufficient location context is present in the description.
    
    Return a strictly valid JSON block containing:
    {{
        "issue_type": "string",
        "severity": "string",
        "ward": "string or null",
        "missing_location": boolean
    }}
    """
    
    try:
        response = model.generate_content(extraction_prompt, generation_config={"response_mime_type": "application/json"})
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        extracted_data = json.loads(raw_text.strip())
    except ResourceExhausted:
        return {"error": "rate_limit", "message": "City servers busy, using fallback location."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process with Gemini: {str(e)}")
        
    # Step 2: Ensure we have location data
    missing_location_in_text = extracted_data.get("missing_location", True)
    has_gps = request.latitude is not None and request.longitude is not None
    
    # Vikhroli Fallback
    if not has_gps:
        ward = extracted_data.get("ward") or ""
        if "vikhroli" in ward.lower() or "vikhroli" in request.description.lower():
            request.latitude = 19.1075
            request.longitude = 72.9372
            has_gps = True
    
    if missing_location_in_text and not has_gps:
        # Generate a targeted follow-up question
        question_prompt = f"""
        The user reported an issue: "{request.description}".
        We don't have GPS coordinates, and the description lacks a specific location (like a street name, landmark, or ward).
        Ask a very brief, polite question to find out exactly where this problem is located.
        """
        q_response = model.generate_content(question_prompt)
        return {
            "status": "incomplete",
            "question": q_response.text.strip()
        }
        
    # Step 3: Resolve Embeddings - Check DB first to avoid duplicate API Calls
    embedding = None
    try:
        existing = supabase.table("complaints").select("embedding").eq("description", request.description).limit(1).execute()
        if existing.data and len(existing.data) > 0:
            embedding = existing.data[0]["embedding"]
    except Exception as e:
        print(f"Warning: Failed to query existing embeddings: {e}")
        
    if not embedding:
        try:
            embedding_result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=request.description,
                task_type="retrieval_document"
            )
            embedding = embedding_result['embedding']
        except ResourceExhausted:
            return {"error": "rate_limit", "message": "City servers busy, using fallback location."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate embedding: {str(e)}")
        
    # Step 4: Semantic Deduplication using Supabase RPC
    try:
        # Call the match_complaints RPC function
        # Using a 90% cosine similarity threshold (0.90) and 100m radius if GPS is present
        rpc_params = {
            "query_embedding": embedding,
            "match_threshold": 0.90,
            "match_count": 1,
            "loc_lat": request.latitude,
            "loc_long": request.longitude,
            "radius_meters": 100.0 if has_gps else None
        }
        
        match_response = supabase.rpc("match_complaints", rpc_params).execute()
        matches = match_response.data
        
        if matches and len(matches) > 0:
            existing_issue = matches[0]
            # Increment upvote count
            new_count = existing_issue["upvote_count"] + 1
            update_res = supabase.table("complaints").update({"upvote_count": new_count}).eq("id", existing_issue["id"]).execute()
            
            return {
                "status": "success",
                "action": "deduplicated",
                "message": "A similar issue was found nearby. We have upvoted the existing complaint.",
                "data": update_res.data[0] if update_res.data else None
            }
            
    except Exception as e:
        print(f"Deduplication step warning: {str(e)}")
        # Continue to insert if deduplication fails rather than failing the whole request
        
    # Step 5: Insert new complaint
    try:
        new_complaint = {
            "description": request.description,
            "issue_type": extracted_data.get("issue_type"),
            "severity": extracted_data.get("severity"),
            "ward": extracted_data.get("ward"),
            "latitude": request.latitude,
            "longitude": request.longitude,
            "image_url": request.image_url,
            "reporter_name": request.reporter_name,
            "reporter_phone": request.reporter_phone,
            "embedding": embedding,
            "upvote_count": 1,
            "status": "pending"
        }
        
        insert_response = supabase.table("complaints").insert(new_complaint).execute()
        
        return {
            "status": "success",
            "action": "created",
            "message": "New complaint successfully registered.",
            "data": insert_response.data[0] if insert_response.data else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save complaint to database: {str(e)}")

@app.post("/api/parse-circular")
async def parse_circular(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    try:
        # Read the file bytes
        file_bytes = await file.read()
        
        # Pass the bytes directly to Gemini 
        pdf_part = {
            "mime_type": "application/pdf",
            "data": file_bytes
        }
        
        prompt = """
        Read the attached Marathi municipal circular.
        Translate it into English and extract the following details:
        - Affected Wards (if mentioned, otherwise null)
        - Dates (start and end dates of the inconvenience, or single dates)
        - Inconvenience Type (e.g., Water Cut, Road Closure, Power Outage, etc.)
        
        Return the result as a strictly valid JSON array of objects.
        Format:
        [
            {
                "wards": ["Ward A", "Ward B"],
                "dates": "Oct 12 to Oct 14",
                "inconvenience_type": "Water Cut",
                "summary": "Brief English summary of the circular"
            }
        ]
        """
        
        response = model.generate_content(
            [pdf_part, prompt],
            generation_config={"response_mime_type": "application/json"}
        )
        
        extracted_data = json.loads(response.text)
        return {
            "status": "success",
            "data": extracted_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse circular: {str(e)}")

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

@app.get("/api/issues")
async def get_issues(
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
    radius: Optional[float] = Query(None)
):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
    try:
        response = supabase.table("complaints").select("id, description, issue_type, severity, ward, latitude, longitude, upvote_count, status, created_at").order("created_at", desc=True).execute()
        
        # Map to what frontend expects
        issues = []
        for row in response.data:
            i_lat = row.get("latitude")
            i_lon = row.get("longitude")
            
            # Apply location filtering if parameters are provided
            if lat is not None and lon is not None and radius is not None and i_lat is not None and i_lon is not None:
                dist = calculate_distance(lat, lon, i_lat, i_lon)
                if dist > radius:
                    continue

            issues.append({
                "id": row.get("id"),
                "title": f"Civic Issue #{row.get('id')}",
                "description": row.get("description"),
                "category": row.get("issue_type", "General"),
                "votes": row.get("upvote_count", 0),
                "emergency": row.get("severity") in ["High", "Critical"],
                "latitude": i_lat,
                "longitude": i_lon,
                "status": str(row.get("status", "Pending")).title(),
                "date": row.get("created_at")[:10] if row.get("created_at") else "Recent",
                "ward": row.get("ward", "Unknown")
            })
        return issues
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch issues: {str(e)}")

@app.post("/api/vote/{issue_id}")
async def vote_issue(issue_id: int):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
    try:
        # Get current count
        res = supabase.table("complaints").select("upvote_count").eq("id", issue_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Issue not found")
            
        new_count = res.data[0]["upvote_count"] + 1
        update_res = supabase.table("complaints").update({"upvote_count": new_count}).eq("id", issue_id).execute()
        return {"status": "success", "new_count": new_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to vote: {str(e)}")

class ParseRequest(BaseModel):
    text: str

@app.post("/api/parse_issue")
async def parse_issue(request: ParseRequest):
    extraction_prompt = f"""
    Analyze the following issue description:
    "{request.text}"
    
    1. Extract the 'category' (e.g., Pothole, Water Leak, Garbage, etc.).
    2. Clean up the description.
    
    Return a strictly valid JSON block containing:
    {{
        "category": "string",
        "description": "string"
    }}
    """
    try:
        response = model.generate_content(extraction_prompt, generation_config={"response_mime_type": "application/json"})
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        return json.loads(raw_text.strip())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse: {str(e)}")

@app.post("/api/check_duplicate")
async def check_duplicate(request: CheckDuplicateRequest):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
        
    has_gps = request.latitude is not None and request.longitude is not None
    
    try:
        # 1. Embed description
        embedding_result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=request.description,
            task_type="retrieval_document"
        )
        embedding = embedding_result['embedding']
        
        # 2. Search Supabase
        rpc_params = {
            "query_embedding": embedding,
            "match_threshold": 0.90, # 90% strict similarity
            "match_count": 1,
            "loc_lat": request.latitude,
            "loc_long": request.longitude,
            "radius_meters": 100.0 if has_gps else None
        }
        
        match_response = supabase.rpc("match_complaints", rpc_params).execute()
        matches = match_response.data
        
        if matches and len(matches) > 0:
            existing_issue = matches[0]
            # Calculate rough distance if GPS exists
            distance = 0
            if has_gps and existing_issue.get("latitude") and existing_issue.get("longitude"):
                 # Haversine approximation or just return a static placeholder since rpc handles the 100m radius natively
                 distance = 50 
            
            return {
                "duplicate": True,
                "issue_id": existing_issue["id"],
                "description": existing_issue["description"],
                "votes": existing_issue["upvote_count"],
                "distance": distance
            }
            
        return {"duplicate": False}
        
    except Exception as e:
        print(f"Duplicate check error: {e}")
        return {"duplicate": False}

@app.post("/api/generate_pdf")
async def generate_pdf(request: GeneratePDFRequest):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Official Civic Grievance Complaint", ln=1, align='C')
    pdf.ln(10)
    
    # Body
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Reporting Citizen: {request.name}", ln=1)
    pdf.cell(200, 10, txt=f"Contact Phone: {request.phone}", ln=1)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Incident Details:", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Category: {request.category}", ln=1)
    pdf.cell(200, 10, txt=f"Location: {request.location}", ln=1)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Description:", ln=1)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=request.description)
    
    pdf.ln(20)
    pdf.cell(200, 10, txt="Generated automatically by the CivicSense framework.", ln=1, align='C')

    # Output to stream
    pdf_bytes = pdf.output(dest="S").encode("latin-1")
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes), 
        media_type="application/pdf", 
        headers={"Content-Disposition": f"attachment; filename=complaint.pdf"}
    )

@app.get("/api/dashboard_stats")
async def get_dashboard_stats():
    if not supabase: return {"total": 0, "active": 0, "resolved": 0, "emergency": 0}
    res = supabase.table("complaints").select("id, status, severity").execute()
    total = len(res.data)
    active = sum(1 for r in res.data if r.get("status", "").lower() in ["pending", "in progress"])
    resolved = sum(1 for r in res.data if r.get("status", "").lower() == "resolved")
    emergency = sum(1 for r in res.data if r.get("severity", "").lower() in ["high", "critical"])
    return {"total": total, "active": active, "resolved": resolved, "emergency": emergency}

@app.get("/api/insights")
async def get_insights():
    if not supabase: return {"top_category": "N/A", "top_ward": "General", "trending": []}
    res = supabase.table("complaints").select("issue_type, ward").execute()
    counts = {}
    ward_counts = {}
    for r in res.data:
        cat = r.get("issue_type")
        if cat: counts[cat] = counts.get(cat, 0) + 1
        w = r.get("ward")
        if w: ward_counts[w] = ward_counts.get(w, 0) + 1
        
    top_cat = max(counts, key=counts.get) if counts else "N/A"
    top_ward = max(ward_counts, key=ward_counts.get) if ward_counts else "General"
    
    return {
        "top_category": top_cat,
        "top_ward": top_ward,
        "trending": ["Pothole Hazards", "Monsoon Water Logging", "Uncollected Waste"]
    }

@app.get("/api/issues/{issue_id}")
async def get_issue(issue_id: int):
    if not supabase: raise HTTPException(status_code=500, detail="DB Error")
    res = supabase.table("complaints").select("*").eq("id", issue_id).execute()
    if not res.data: raise HTTPException(status_code=404, detail="Not Found")
    row = res.data[0]
    return {
        "id": row.get("id"),
        "title": f"{row.get('issue_type', 'General')} Issue",
        "description": row.get("description"),
        "category": row.get("issue_type", "General"),
        "votes": row.get("upvote_count", 0),
        "status": str(row.get("status", "Pending")).title(),
        "date": row.get("created_at")[:10] if row.get("created_at") else "Recent",
        "latitude": row.get("latitude"),
        "longitude": row.get("longitude"),
        "ward": row.get("ward", "Unknown")
    }

class CommentRequest(BaseModel):
    name: str
    text: str

COMMENTS_DB = {}

@app.post("/api/issues/{issue_id}/comments")
async def add_comment(issue_id: int, request: CommentRequest):
    if issue_id not in COMMENTS_DB:
        COMMENTS_DB[issue_id] = []
    
    import datetime
    new_comment = {"name": request.name, "text": request.text, "date": datetime.datetime.now().strftime("%I:%M %p")}
    COMMENTS_DB[issue_id].append(new_comment)
    return {"status": "success", "comment": new_comment}

@app.get("/api/issues/{issue_id}/comments")
async def get_comments(issue_id: int):
    base_comments = [
        {"name": "System", "text": "Issue logged and routed to concerned department.", "date": "System Log"}
    ]
    return base_comments + COMMENTS_DB.get(issue_id, [])

@app.get("/api/notices")
async def get_notices():
    # Placeholder for notices, can be connected to DB later
    return [
        {
            "title": "Scheduled Water Cut in Ward A",
            "summary": "There will be a scheduled water cut on Oct 12 due to pipeline maintenance.",
            "source": "Municipal Corporation",
            "date": "2023-10-10"
        }
    ]

@app.get("/")
def root():
    return {"message": "Welcome to the Vox Backend API!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
