import os
import json
import logging
import re
import hashlib
import uuid
import google.generativeai as genai
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, request
from flask_cors import CORS
from google.cloud import firestore
from google.oauth2 import service_account

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
GCP_PROJECT_ID: Optional[str] = os.getenv("GCP_PROJECT_ID") or None
GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or None
GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY") or None
FRONTEND_URL: Optional[str] = os.getenv("FRONTEND_URL") or "https://brief-me-seven.vercel.app"
FIRESTORE_COLLECTION = os.getenv("FIRESTORE_COLLECTION", "briefs")
FIRESTORE_DATABASE_ID = os.getenv("FIRESTORE_DATABASE_ID", "briefmedatabase")
MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "10000"))
MAX_RECENT_BRIEFS = int(os.getenv("MAX_RECENT_BRIEFS", "10"))

app = Flask(__name__)
CORS(app, 
     origins="*",  # Allow all origins temporarily
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     supports_credentials=False)  # Set to False when using "*"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("brief-api")

if not GCP_PROJECT_ID:
    logger.warning("GCP_PROJECT_ID is not set. Set as environment variable.")
if not GOOGLE_APPLICATION_CREDENTIALS:
    logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set. Set as environment variable.")
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY is not set. Set as environment variable.")

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def _to_iso(dt: Any) -> Optional[str]:
    try:
        return dt.isoformat()
    except Exception:
        return None

def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)

def _is_uuid(s: str) -> bool:
    return bool(UUID_RE.match(s or ""))

def _trim_summary(summary: str, max_words: int = 100) -> str:
    words = summary.split()
    if len(words) <= max_words:
        return summary
    return " ".join(words[:max_words])

def _map_actions_to_ui(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = []
    for a in actions or []:
        if not isinstance(a, dict):
            continue
        task = a.get("task") or a.get("text") or a.get("action") or ""
        assignee = a.get("assignee") or a.get("owner")
        due = a.get("dueDate") or a.get("due_date")
        normalized.append({
            "task": task,
            "assignee": assignee,
            "dueDate": due,
        })
    return normalized

def _counts(brief: Dict[str, Any]) -> Dict[str, int]:
    return {
        "decisions_count": len(brief.get("decisions", []) or []),
        "actions_count": len(brief.get("actions", []) or []),
        "questions_count": len(brief.get("questions", []) or []),
    }

# ----------------------------------------------------------------------------
# Firestore
# ----------------------------------------------------------------------------
_db: Optional[firestore.Client] = None

def _get_db() -> firestore.Client:
    global _db
    if _db is None:
        try:
            if not GCP_PROJECT_ID:
                raise RuntimeError("GCP_PROJECT_ID environment variable is not set")
            
            if GOOGLE_APPLICATION_CREDENTIALS:
                try:
                    credentials_info = json.loads(GOOGLE_APPLICATION_CREDENTIALS)
                    credentials = service_account.Credentials.from_service_account_info(credentials_info)
                    
                    _db = firestore.Client(
                        project=GCP_PROJECT_ID, 
                        credentials=credentials,
                        database=FIRESTORE_DATABASE_ID
                    )
                    logger.info("Firestore initialized with service account credentials")
                except json.JSONDecodeError as e:
                    logger.error("Failed to parse GOOGLE_APPLICATION_CREDENTIALS as JSON: %s", e)
                    raise RuntimeError(f"Invalid JSON in GOOGLE_APPLICATION_CREDENTIALS: {e}") from e
            else:
                _db = firestore.Client(project=GCP_PROJECT_ID, database=FIRESTORE_DATABASE_ID)
                logger.info("Firestore initialized with default credentials")
                
            logger.info("Firestore client initialized (project=%s, database=%s, collection=%s)",
                GCP_PROJECT_ID, FIRESTORE_DATABASE_ID, FIRESTORE_COLLECTION)
        except Exception as e:
            logger.error("Failed to initialize Firestore client: %s", e)
            raise RuntimeError(f"Firestore initialization failed: {e}") from e
    return _db

def _collection():
    return _get_db().collection(FIRESTORE_COLLECTION)

def _find_duplicate(client_session_id: str, text_hash: str) -> Optional[Dict[str, Any]]:
    try:
        docs = (
            _collection()
            .where(filter=firestore.FieldFilter("client_session_id", "==", client_session_id))
            .where(filter=firestore.FieldFilter("sha256", "==", text_hash))
            .limit(1)
            .stream()
        )
        docs = list(docs)
        if docs:
            return docs[0].to_dict()
        return None
    except Exception as e:
        msg = str(e)
        if "The query requires an index" in msg:
            try:
                for d in _collection().where(filter=firestore.FieldFilter("sha256", "==", text_hash)).stream():
                    data = d.to_dict()
                    if data.get("client_session_id") == client_session_id:
                        return data
            except Exception as e2:
                logger.error("Duplicate-check fallback failed: %s", e2)
        else:
            logger.error("Duplicate-check failed: %s", e)
        return None

def _recent_briefs(client_session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent briefs with proper ordering and error handling"""
    try:
        # Try with ordering first (requires composite index)
        query = (
            _collection()
            .where(filter=firestore.FieldFilter("client_session_id", "==", client_session_id))
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
        )
        docs = list(query.stream())
        
    except Exception as e:
        logger.warning(f"Ordered query failed (likely missing index): {e}")
        try:
            # Fallback: simple query without ordering
            query = (
                _collection()
                .where(filter=firestore.FieldFilter("client_session_id", "==", client_session_id))
                .limit(limit * 2)  # Get extra docs for manual sorting
            )
            docs = list(query.stream())
        except Exception as e2:
            logger.error(f"Fallback query also failed: {e2}")
            return []  # Return empty array, don't crash

    # Process documents safely
    results = []
    for doc in docs:
        try:
            data = doc.to_dict()
            if not data or not data.get("created_at"):
                continue
                
            data["actions"] = _map_actions_to_ui(data.get("actions", []))
            brief = {
                "id": data.get("id", ""),
                "summary": data.get("summary", ""),
                "created_at": _to_iso(data.get("created_at")),
                **_counts(data),
            }
            results.append(brief)
        except Exception as e:
            logger.warning(f"Failed to process document: {e}")
            continue

    # Sort by datetime objects, not strings
    try:
        results.sort(key=lambda x: datetime.fromisoformat(x.get("created_at", "1970-01-01T00:00:00+00:00").replace('Z', '+00:00')), reverse=True)
    except Exception:
        # Fallback to string sorting if datetime parsing fails
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return results[:limit]

def _get_brief(brief_id: str, client_session_id: str) -> Optional[Dict[str, Any]]:
    doc = _collection().document(brief_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    if data.get("client_session_id") != client_session_id:
        return None
    data["created_at"] = _to_iso(data.get("created_at"))
    data["actions"] = _map_actions_to_ui(data.get("actions", []))
    return data

# ----------------------------------------------------------------------------
# Gemini LLM
# ----------------------------------------------------------------------------
def _gemini_generate(source_text: str) -> Dict[str, Any]:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not configured")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-pro")

    def build_prompt(strict: bool = False) -> str:
        example = (
            '{"summary":"string ≤100 words","decisions":["..."],'
            '"actions":[{"task":"...","assignee":"name or null","dueDate":"YYYY-MM-DD or null"}],'
            '"questions":["..."]}'
        )
        if not strict:
            return (
                "Return ONLY valid JSON (no markdown). Keys must be: "
                'summary, decisions, actions, questions.\n'
                "- summary: string (≤100 words)\n"
                "- decisions: array of strings\n"
                "- actions: array of {task, assignee, dueDate} (assignee/dueDate may be null)\n"
                "- questions: array of strings\n\n"
                f"Text to analyze:\n{source_text}\n\nJSON only:"
            )
        else:
            return (
                "STRICT: Return ONLY valid JSON, no markdown or extra text. Use exactly this shape:\n"
                + example + "\n\nText to analyze:\n" + source_text + "\n\nJSON:"
            )

    def call_once(prompt: str) -> Dict[str, Any]:
        resp = model.generate_content(prompt)
        text = (resp.text or "").strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        data = json.loads(text)
        for k in ("summary", "decisions", "actions", "questions"):
            if k not in data:
                raise KeyError(f"Missing key: {k}")
        data["summary"] = _trim_summary(str(data.get("summary", "")))
        data["actions"] = _map_actions_to_ui(data.get("actions", []))
        data["decisions"] = list(data.get("decisions", []) or [])
        data["questions"] = list(data.get("questions", []) or [])
        return data

    try:
        return call_once(build_prompt(False))
    except Exception as e1:
        logger.warning("Gemini parse failed, retrying strictly: %s", e1)
        return call_once(build_prompt(True))

# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------
@app.route("/")
def root():
    return jsonify({
        "service": "Brief Generator API",
        "status": "running",
        "version": "1.1.0",
        "endpoints": {
            "health": "/health",
            "create_brief": "POST /api/briefs",
            "list_briefs": "GET /api/briefs?client_session_id=<uuid>",
            "get_brief": "GET /api/briefs/<id>?client_session_id=<uuid>",
            "delete_brief": "DELETE /api/briefs/<id>?client_session_id=<uuid>"
        }
    })

@app.route("/health", methods=["GET"])
def health():
    health_status = {
        "status": "ok", 
        "time": _to_iso(_now_utc()),
        "version": "1.1.0",
        "environment": {
            "gcp_project_id": bool(GCP_PROJECT_ID),
            "gemini_api_key": bool(GEMINI_API_KEY),
            "google_application_credentials": bool(GOOGLE_APPLICATION_CREDENTIALS)
        }
    }
    
    try:
        _get_db()
        health_status["firestore"] = "connected"
    except Exception as e:
        logger.error("Firestore health check failed: %s", e)
        health_status["firestore"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    return jsonify(health_status)

@app.route("/api/briefs", methods=["POST"])
def create_brief():
    if request.method == "OPTIONS":
        return "", 200
    data = request.get_json(silent=True) or {}
    source_text = (data.get("source_text") or "").strip()
    client_session_id = (data.get("client_session_id") or "").strip()

    if not source_text:
        return jsonify({"error": "source_text is required"}), 400
    if len(source_text) > MAX_TEXT_LENGTH:
        return jsonify({"error": f"source_text exceeds {MAX_TEXT_LENGTH} characters"}), 400
    if not _is_uuid(client_session_id):
        return jsonify({"error": "client_session_id must be a valid UUID"}), 400

    text_hash = _sha256(source_text)
    existing = _find_duplicate(client_session_id, text_hash)
    if existing:
        existing["created_at"] = _to_iso(existing.get("created_at"))
        existing["actions"] = _map_actions_to_ui(existing.get("actions", []))
        return jsonify({**existing, **_counts(existing)}), 200

    try:
        llm = _gemini_generate(source_text)
    except Exception as e:
        logger.error("LLM generation failed: %s", e)
        msg = str(e)
        if "GEMINI_API_KEY not configured" in msg:
            return jsonify({"error": "Gemini not configured. Set GEMINI_API_KEY."}), 503
        return jsonify({"error": "Failed to generate brief"}), 500

    brief_id = str(uuid.uuid4())
    doc = {
        "id": brief_id,
        "client_session_id": client_session_id,
        "source_text": source_text,
        "summary": llm.get("summary", ""),
        "decisions": llm.get("decisions", []),
        "actions": _map_actions_to_ui(llm.get("actions", [])),
        "questions": llm.get("questions", []),
        "created_at": _now_utc(),
        "sha256": text_hash,
    }

    try:
        _collection().document(brief_id).set(doc)
    except Exception as e:
        logger.error("Failed to store brief: %s", e)
        return jsonify({"error": "Failed to store brief"}), 500

    resp = {**doc, "created_at": _to_iso(doc["created_at"])}
    resp.update(_counts(doc))
    return jsonify(resp), 201

@app.route("/api/briefs", methods=["GET"])
def list_briefs():
    client_session_id = (request.args.get("client_session_id") or "").strip()
    limit = request.args.get("limit", type=int) or MAX_RECENT_BRIEFS

    if not _is_uuid(client_session_id):
        return jsonify({"error": "client_session_id must be a valid UUID"}), 400
    limit = max(1, min(50, limit))

    try:
        items = _recent_briefs(client_session_id, limit)
        return jsonify(items), 200
    except Exception as e:
        logger.error("Failed to list briefs: %s", e)
        return jsonify([]), 200

@app.route("/api/briefs/<string:brief_id>", methods=["GET"])
def get_brief(brief_id: str):
    client_session_id = (request.args.get("client_session_id") or "").strip()
    if not _is_uuid(client_session_id) or not _is_uuid(brief_id):
        return jsonify({"error": "invalid id(s)"}), 400
    try:
        brief = _get_brief(brief_id, client_session_id)
        if not brief:
            return jsonify({"error": "Not found"}), 404
        brief_with_counts = {**brief, **_counts(brief)}
        return jsonify(brief_with_counts), 200
    except Exception as e:
        logger.error("Failed to get brief: %s", e)
        return jsonify({"error": "Failed to retrieve brief"}), 500

@app.route("/api/briefs/<string:brief_id>", methods=["DELETE"])
def delete_brief(brief_id: str):
    client_session_id = (request.args.get("client_session_id") or "").strip()
    if not _is_uuid(client_session_id) or not _is_uuid(brief_id):
        return jsonify({"error": "invalid id(s)"}), 400
    try:
        brief = _get_brief(brief_id, client_session_id)
        if not brief:
            return jsonify({"error": "Not found"}), 404
        _collection().document(brief_id).delete()
        return ("", 204)
    except Exception as e:
        logger.error("Failed to delete brief: %s", e)
        return jsonify({"error": "Failed to delete brief"}), 500

# @app.errorhandler(Exception)  
# def handle_all_exceptions(e):
#     logger.error(f"Unhandled exception: {e}")
    
#     response = jsonify({"error": "Internal server error"})
    
#     origin = request.headers.get('Origin', 'https://brief-me-seven.vercel.app')
#     if origin in ['http://localhost:3000', 'https://brief-me-seven.vercel.app', FRONTEND_URL]:
#         response.headers.add('Access-Control-Allow-Origin', origin)
#     else:
#         response.headers.add('Access-Control-Allow-Origin', 'https://brief-me-seven.vercel.app')
    
#     response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
#     response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
#     response.headers.add('Access-Control-Allow-Credentials', 'true')
    
#     return response, 500

# @app.route('/api/briefs', methods=['OPTIONS'])
# @app.route('/api/briefs/<string:brief_id>', methods=['OPTIONS'])  
# def handle_options(brief_id=None):
#     return '', 200  # Let CORS middleware handle headers

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = (os.getenv("FLASK_DEBUG", "false").lower() == "true")
    print(f"\nStarting Brief Generator API on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)