import os
import re
import json
import uuid
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, request
from flask_cors import CORS
from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter
import google.generativeai as genai

# ----------------------------------------------------------------------------
# Minimal, single-file API for "Brief Generator"
# ----------------------------------------------------------------------------

app = Flask(__name__)
# Allow CORS for both local development and production
CORS(app, 
     origins=[
         "http://localhost:3000", 
         "https://brief-me-seven.vercel.app"
     ],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("brief-api")


# ----------------------------------------------------------------------------
# Inline configuration (no .env). You can edit these defaults directly.
# ----------------------------------------------------------------------------

# Defaults (can still be overridden by environment, but not required)
GCP_PROJECT_ID: Optional[str] = os.getenv("GCP_PROJECT_ID") or None
GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or None
GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY") or None
FIRESTORE_COLLECTION = os.getenv("FIRESTORE_COLLECTION", "briefs")
FIRESTORE_DATABASE_ID = os.getenv("FIRESTORE_DATABASE_ID", "briefmedatabase")
MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "10000"))
MAX_RECENT_BRIEFS = int(os.getenv("MAX_RECENT_BRIEFS", "10"))

# Try to set GOOGLE_APPLICATION_CREDENTIALS to a local service account JSON if not provided
if not GOOGLE_APPLICATION_CREDENTIALS:
    server_dir = os.path.dirname(__file__)
    sa_in_server = os.path.join(server_dir, "briefme-469208-947c360f429f.json")
    if os.path.exists(sa_in_server):
        GOOGLE_APPLICATION_CREDENTIALS = sa_in_server
    else:
        # Check parent folder "Service account key"
        repo_root = os.path.abspath(os.path.join(server_dir, ".."))
        sa_in_root = os.path.join(repo_root, "Service account key", "briefme-469208-947c360f429f.json")
        if os.path.exists(sa_in_root):
            GOOGLE_APPLICATION_CREDENTIALS = sa_in_root

# If we found credentials, expose them for Google SDK
if GOOGLE_APPLICATION_CREDENTIALS:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS

# Derive project id from service account if not set
if not GCP_PROJECT_ID and GOOGLE_APPLICATION_CREDENTIALS and os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
    try:
        with open(GOOGLE_APPLICATION_CREDENTIALS, "r", encoding="utf-8") as f:
            sa = json.load(f)
            GCP_PROJECT_ID = sa.get("project_id") or sa.get("projectId") or GCP_PROJECT_ID
    except Exception:
        pass

# Load Gemini API key from repo file if not provided
if not GEMINI_API_KEY:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    gemini_key_path = os.path.join(repo_root, "Service account key", "gemini api key.txt")
    try:
        if os.path.exists(gemini_key_path):
            with open(gemini_key_path, "r", encoding="utf-8") as f:
                key = f.read().strip()
                GEMINI_API_KEY = key or None
    except Exception:
        GEMINI_API_KEY = None

if not GCP_PROJECT_ID:
    logger.warning("GCP_PROJECT_ID is not set (and could not be derived). Firestore may fail to initialize.")
if not GOOGLE_APPLICATION_CREDENTIALS or not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
    logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set or file missing. Ensure credentials are configured.")
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY is not set. Gemini calls will fail.")
logger.info("Firestore target database id: %s", FIRESTORE_DATABASE_ID)


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
    """Normalize various action key shapes to UI shape: task, assignee, dueDate."""
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
        _db = firestore.Client(project=GCP_PROJECT_ID, database=FIRESTORE_DATABASE_ID)
        logger.info(
            "Firestore client initialized (project=%s, database=%s, collection=%s)",
            GCP_PROJECT_ID,
            FIRESTORE_DATABASE_ID,
            FIRESTORE_COLLECTION,
        )
    return _db


def _collection():
    return _get_db().collection(FIRESTORE_COLLECTION)


def _find_duplicate(client_session_id: str, text_hash: str) -> Optional[Dict[str, Any]]:
    try:
        docs = (
            _collection()
            .where(filter=FieldFilter("client_session_id", "==", client_session_id))
            .where(filter=FieldFilter("sha256", "==", text_hash))
            .limit(1)
            .stream()
        )
        docs = list(docs)
        if docs:
            return docs[0].to_dict()
        return None
    except Exception as e:
        # Fallback if composite index missing: query by sha256 and filter locally
        msg = str(e)
        if "The query requires an index" in msg:
            try:
                for d in _collection().where(filter=FieldFilter("sha256", "==", text_hash)).stream():
                    data = d.to_dict()
                    if data.get("client_session_id") == client_session_id:
                        return data
            except Exception as e2:
                logger.error("Duplicate-check fallback failed: %s", e2)
        else:
            logger.error("Duplicate-check failed: %s", e)
        return None


def _recent_briefs(client_session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    try:
        query = (
            _collection()
            .where(filter=FieldFilter("client_session_id", "==", client_session_id))
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
        )
        docs = list(query.stream())
    except Exception as e:
        # Fallback if missing index: query by session and sort locally
        if "The query requires an index" in str(e):
            docs = list(_collection().where(filter=FieldFilter("client_session_id", "==", client_session_id)).stream())
            items = [d.to_dict() for d in docs]
            items.sort(key=lambda b: b.get("created_at"), reverse=True)
            docs = []
            # Re-wrap into dict-like objects
            for it in items[:limit]:
                docs.append(type("_Doc", (), {"to_dict": lambda self, _it=it: _it})())
        else:
            raise

    results: List[Dict[str, Any]] = []
    for d in docs:
        data = d.to_dict()
        # Ensure UI action keys for consistency even in list (not strictly needed)
        data["actions"] = _map_actions_to_ui(data.get("actions", []))
        brief = {
            "id": data.get("id"),
            "summary": data.get("summary"),
            "created_at": _to_iso(data.get("created_at")),
            **_counts(data),
        }
        results.append(brief)
    return results


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
    """Call Gemini once; return dict with keys: summary, decisions, actions, questions.
    Actions must use UI keys (task, assignee, dueDate)."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not configured")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-pro")

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
        # Remove optional code fences if present
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        data = json.loads(text)
        # Validate minimal structure
        for k in ("summary", "decisions", "actions", "questions"):
            if k not in data:
                raise KeyError(f"Missing key: {k}")
        data["summary"] = _trim_summary(str(data.get("summary", "")))
        # Normalize actions to UI keys
        data["actions"] = _map_actions_to_ui(data.get("actions", []))
        # Ensure arrays
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

@app.get("/health")
def health():
    return jsonify({"status": "ok", "time": _to_iso(_now_utc())})


@app.post("/api/briefs")
def create_brief():
    """Create a new brief: body { source_text, client_session_id }"""
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
    # Duplicate check
    existing = _find_duplicate(client_session_id, text_hash)
    if existing:
        # Normalize for response
        existing["created_at"] = _to_iso(existing.get("created_at"))
        existing["actions"] = _map_actions_to_ui(existing.get("actions", []))
        return jsonify({**existing, **_counts(existing)}), 200

    # Generate with Gemini
    try:
        llm = _gemini_generate(source_text)
    except Exception as e:
        logger.error("LLM generation failed: %s", e)
        msg = str(e)
        if "GEMINI_API_KEY not configured" in msg:
            return jsonify({"error": "Gemini not configured. Set GEMINI_API_KEY."}), 503
        return jsonify({"error": "Failed to generate brief"}), 500

    # Build document
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

    # Response (serialize created_at to ISO)
    resp = {**doc, "created_at": _to_iso(doc["created_at"])}
    resp.update(_counts(doc))
    return jsonify(resp), 201


@app.get("/api/briefs")
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
        return jsonify({"error": "Failed to retrieve briefs"}), 500


@app.get("/api/briefs/<string:brief_id>")
def get_brief(brief_id: str):
    client_session_id = (request.args.get("client_session_id") or "").strip()
    if not _is_uuid(client_session_id) or not _is_uuid(brief_id):
        return jsonify({"error": "invalid id(s)"}), 400
    try:
        brief = _get_brief(brief_id, client_session_id)
        if not brief:
            return jsonify({"error": "Not found"}), 404
        # Add counts for convenience
        brief_with_counts = {**brief, **_counts(brief)}
        return jsonify(brief_with_counts), 200
    except Exception as e:
        logger.error("Failed to get brief: %s", e)
        return jsonify({"error": "Failed to retrieve brief"}), 500


@app.delete("/api/briefs/<string:brief_id>")
def delete_brief(brief_id: str):
    client_session_id = (request.args.get("client_session_id") or "").strip()
    if not _is_uuid(client_session_id) or not _is_uuid(brief_id):
        return jsonify({"error": "invalid id(s)"}), 400
    try:
        # Verify ownership
        brief = _get_brief(brief_id, client_session_id)
        if not brief:
            return jsonify({"error": "Not found"}), 404
        _collection().document(brief_id).delete()
        return ("", 204)
    except Exception as e:
        logger.error("Failed to delete brief: %s", e)
        return jsonify({"error": "Failed to delete brief"}), 500


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = (os.getenv("FLASK_DEBUG", "false").lower() == "true")
    print(f"\nStarting Brief Generator API on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)