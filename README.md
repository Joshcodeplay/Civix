# Civix

**Civix** is an AI-powered civic intelligence platform that turns raw citizen complaints into structured, actionable reports for local authorities — with duplicate detection, geolocation, PDF evidence generation, and an admin dashboard for tracking issue resolution.

## What it does

Citizens report civic issues (potholes, garbage, water leaks, safety hazards, etc.) in plain language, optionally attaching a photo and location. Civix uses Google's Gemini models to:

- Parse the free-text description into a structured complaint (issue type, severity, ward/location)
- Check for duplicate/nearby reports using vector similarity search (pgvector) so the same pothole doesn't get filed 50 times
- Route the issue to the responsible authority
- Generate PDF complaint/evidence documents for formal follow-up
- Surface aggregated insights and stats for admins

It also supports SOS-style urgent reports, community upvoting on issues, comment threads, a map view of open issues, and government circular/notice parsing.

## Tech stack

**Backend** — Python, [FastAPI](https://fastapi.tiangolo.com/), [Supabase](https://supabase.com/) (Postgres + pgvector for embeddings), [Google Gemini](https://ai.google.dev/) (`gemini-2.5-flash-lite`) for parsing/classification and embeddings, FPDF for PDF generation. Deployed on Vercel (`@vercel/python`).

**Frontend** — Python, [Streamlit](https://streamlit.io/), with `streamlit-folium` for maps, `streamlit-geolocation` for location capture, and `pdfplumber`/`beautifulsoup4` for document parsing.

## Project structure

```
Civix/
├── backend/
│   ├── main.py           # FastAPI app — all API routes
│   ├── schema.sql         # Supabase/Postgres schema (complaints table, pgvector similarity search)
│   └── requirements.txt
├── frontend/
│   ├── app.py             # Streamlit entry point
│   ├── admin_dashboard.py # Admin view — stats, status updates
│   ├── pages/              # Home, Report Issue, Issues Feed, Map View, My Reports, Issue Detail, Notices
│   ├── components/         # Shared UI (nav)
│   └── requirements.txt
└── vercel.json             # Deployment config (backend as a Vercel Python function)
```

## Key API endpoints

| Endpoint | Description |
|---|---|
| `POST /api/submit-issue` | Submit a new complaint |
| `POST /api/check_duplicate` | Vector-similarity check for nearby duplicate reports |
| `POST /api/parse_issue` | Parse free-text description into structured fields via Gemini |
| `POST /api/sos` | Report an urgent/SOS issue |
| `GET /api/active-sos` | List active SOS reports |
| `GET /api/issues` | List/filter issues |
| `GET /api/issues/{issue_id}` | Get a single issue's details |
| `POST /api/vote/{issue_id}` | Upvote an issue |
| `POST /api/issues/{issue_id}/comments` | Add a comment to an issue |
| `GET /api/timeline/{issue_id}` | Status/resolution timeline for an issue |
| `POST /api/generate_pdf` / `POST /api/generate_evidence_pdf` | Generate complaint/evidence PDFs |
| `POST /api/responsible_authority` | Determine the responsible authority for an issue |
| `POST /api/parse-circular` | Parse an uploaded government circular/notice |
| `GET /api/dashboard_stats` / `GET /api/admin/stats` | Aggregated stats for the dashboard |
| `PATCH /api/admin/update-status/{issue_id}` | Update an issue's status (admin) |
| `GET /api/insights` | AI-generated insights across complaints |
| `GET /api/notices` | Fetch public notices |

## Setup

### Prerequisites
- Python 3.10+
- A [Supabase](https://supabase.com/) project with the `pgvector` extension enabled
- A [Google Gemini API key](https://ai.google.dev/)

### Backend

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file in `backend/`:

```
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

Apply the schema in `backend/schema.sql` to your Supabase project, then run:

```bash
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

## Deployment

The backend is configured to deploy as a Vercel Python serverless function (see `vercel.json`), with the frontend deployable separately (e.g. Streamlit Community Cloud) pointed at the deployed API URL.

## License

No license specified yet.
