import os
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
import google.generativeai as genai
from supabase import create_client, Client

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
# Using gemini-2.5-flash for general fast generation
model = genai.GenerativeModel("gemini-2.5-flash")

# Define Pydantic models for the request and response
class IssueSubmitRequest(BaseModel):
    description: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image_url: Optional[str] = None

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
        extracted_data = json.loads(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process with Gemini: {str(e)}")
        
    # Step 2: Ensure we have location data
    missing_location_in_text = extracted_data.get("missing_location", True)
    has_gps = request.latitude is not None and request.longitude is not None
    
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
        
    # Step 3: Vectorize the complaint description
    try:
        embedding_result = genai.embed_content(
            model="models/gemini-embedding-001",
            content=request.description,
            task_type="retrieval_document"
        )
        embedding = embedding_result['embedding']
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

@app.get("/api/issues")
async def get_issues():
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not initialized")
    try:
        response = supabase.table("complaints").select("id, description, issue_type, severity, ward, latitude, longitude, upvote_count, status, created_at").order("created_at", desc=True).execute()
        
        # Map to what frontend expects
        issues = []
        for row in response.data:
            issues.append({
                "id": row.get("id"),
                "description": row.get("description"),
                "category": row.get("issue_type", "General"),
                "votes": row.get("upvote_count", 0),
                "emergency": row.get("severity") in ["High", "Critical"],
                "latitude": row.get("latitude"),
                "longitude": row.get("longitude")
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
        return json.loads(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse: {str(e)}")

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
