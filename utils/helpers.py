import hashlib
import uuid
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional

def generate_sha256(text: str) -> str:
    """Generate SHA256 hash of text."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())

def is_valid_uuid(uuid_string: str) -> bool:
    """Validate UUID format."""
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(uuid_string))

def validate_text_input(text: str) -> tuple[bool, Optional[str]]:
    """Validate input text."""
    if not text or not text.strip():
        return False, "Text cannot be empty"
    
    if len(text) > 10000:
        return False, "Text cannot exceed 10,000 characters"
    
    return True, None

def format_brief_response(brief_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format brief data for API response."""
    return {
        'id': brief_data.get('id'),
        'client_session_id': brief_data.get('client_session_id'),
        'source_text': brief_data.get('source_text'),
        'summary': brief_data.get('summary'),
        'decisions': brief_data.get('decisions', []),
        'actions': brief_data.get('actions', []),
        'questions': brief_data.get('questions', []),
        'created_at': brief_data.get('created_at'),
        'sha256': brief_data.get('sha256')
    }

def get_current_timestamp():
    """Get current UTC timestamp with timezone info."""
    return datetime.now(timezone.utc)