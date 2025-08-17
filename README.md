# Brief Generator

Generate a concise brief (summary, decisions, action items, questions) from pasted text using Google Gemini and store results in Firestore. React on the front, Flask on the back.

## Quick start (Windows)

1) Put your keys in place (either option works):
- Google service account JSON: place in `Service account key/` or `server/` (or set `GOOGLE_APPLICATION_CREDENTIALS`).
- Gemini API key: put the key string in `Service account key/gemini api key.txt` (one line) or set `GEMINI_API_KEY`.

2) Run the starter

```powershell
./start.ps1
```

This will create a Python venv, install backend and frontend deps, and open two windows:
- API: http://localhost:5000 (health at `/health`)
- Web: http://localhost:3000

Prereqs: Python 3.8+ and Node.js 16+ installed and on PATH.

## Manual setup and run (Windows, no scripts)

Backend (Flask):

```powershell
cd server
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Optional if you didn't place files under "Service account key/":
# $env:GEMINI_API_KEY = "your-key"; $env:GOOGLE_APPLICATION_CREDENTIALS = "C:\\path\\to\\service-account.json"
python app.py
```

Frontend (React):

```powershell
cd client
npm install
npm start
```

## Minimal configuration

No .env is required. The server auto-detects credentials if you follow “Quick start”. You can also set env vars:
- `GOOGLE_APPLICATION_CREDENTIALS` — path to your service account JSON
- `GEMINI_API_KEY` — your Gemini API key
- `GCP_PROJECT_ID` — optional; derived from the JSON if omitted
- `FIRESTORE_DATABASE_ID` — default `briefmedatabase`
- `FIRESTORE_COLLECTION` — default `briefs`
- `FLASK_PORT` — default `5000`; `FLASK_DEBUG=true` for debug

## API (brief overview)

Base: `http://localhost:5000`

- POST `/api/briefs` — body: `{ source_text: string, client_session_id: uuid }`
- GET `/api/briefs?client_session_id=uuid&limit=10`
- GET `/api/briefs/{id}?client_session_id=uuid`
- DELETE `/api/briefs/{id}?client_session_id=uuid`

Response shape includes:
- `summary` (≤100 words)
- `decisions` string[]
- `actions` array of `{ task, assignee?, dueDate? }`
- `questions` string[]

## Notes and docs

- CORS is enabled for `http://localhost:3000` during development.
- Ensure Firestore is enabled in your GCP project. If listing recent briefs asks for an index, the server falls back automatically.
- More details: `discussion/GCP_SETUP_GUIDE.md`, `discussion/FIRESTORE_SECURITY_GUIDE.md`, and `server/README.md`.

## Troubleshooting

- Missing credentials: place files as in Quick start or set env vars above.
- 503 “Gemini not configured”: set `GEMINI_API_KEY` (or the txt file).
- Firestore auth errors: check service account permissions and `GCP_PROJECT_ID`.
- Port conflicts: change `FLASK_PORT` or CRA port via `PORT` env.
