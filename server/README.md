# Brief Generator Backend (Flask)

Single-file API (`app.py`) that generates structured briefs with Google Gemini and stores them in Firestore.

## Run locally (Windows PowerShell)

```powershell
cd server
python -m venv venv; ./venv/Scripts/Activate.ps1
pip install -r requirements.txt
python app.py
```

API base: `http://localhost:5000`
- Health: `GET /health`
- Create brief: `POST /api/briefs` (json: `{ source_text, client_session_id }`)
- List briefs: `GET /api/briefs?client_session_id=...&limit=10`
- Get brief: `GET /api/briefs/{id}?client_session_id=...`
- Delete brief: `DELETE /api/briefs/{id}?client_session_id=...`

## Config

No .env is required. The app auto-detects if you place files as below, or set environment variables.

- Service account JSON: put under `Service account key/` (repo root) or next to `app.py`, or set `GOOGLE_APPLICATION_CREDENTIALS`.
- Gemini API key: put one-line key in `Service account key/gemini api key.txt`, or set `GEMINI_API_KEY`.
- Optional: `GCP_PROJECT_ID`, `FIRESTORE_DATABASE_ID` (default `briefmedatabase`), `FIRESTORE_COLLECTION` (default `briefs`), `FLASK_PORT` (default `5000`), `FLASK_DEBUG=true`.

## Notes

- CORS is enabled for `http://localhost:3000`.
- If a Firestore composite index is missing, the server uses a fallback for duplicate checks and recent lists.
- Logging goes to stdout; errors are returned as JSON with appropriate HTTP status codes.
