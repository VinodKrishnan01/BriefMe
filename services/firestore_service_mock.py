import logging
from typing import Dict, Any, Optional
from utils.config import Config
from utils.helpers import generate_sha256, generate_uuid, get_current_timestamp

logger = logging.getLogger(__name__)

class FirestoreService:
    """Service for interacting with Firestore - Mock version for development"""
    
    def __init__(self):
        """Initialize Firestore service with mock data storage"""
        logger.info("Initializing FirestoreService (Mock Mode)")
        # In-memory storage for development
        self.mock_briefs = {}
    
    def create_brief(self, brief_data: Dict[str, Any]) -> str:
        """Create a new brief - Mock implementation"""
        try:
            # Generate document ID
            doc_id = generate_uuid()
            
            # Add metadata
            brief_data['id'] = doc_id
            brief_data['created_at'] = get_current_timestamp()
            
            # Store in mock storage
            self.mock_briefs[doc_id] = brief_data
            
            logger.info(f"Created mock brief with ID: {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to create brief: {e}")
            raise Exception(f"Failed to store brief: {str(e)}")
    
    def get_brief_by_id(self, brief_id: str, client_session_id: str) -> Optional[Dict[str, Any]]:
        """Get a brief by ID - Mock implementation"""
        try:
            brief_data = self.mock_briefs.get(brief_id)
            
            if not brief_data:
                logger.warning(f"Brief not found: {brief_id}")
                return None
            
            # Check authorization
            if brief_data.get('client_session_id') != client_session_id:
                logger.warning(f"Unauthorized access attempt for brief {brief_id}")
                return None
            
            return brief_data
            
        except Exception as e:
            logger.error(f"Failed to get brief {brief_id}: {e}")
            raise Exception(f"Failed to retrieve brief: {str(e)}")
    
    def get_recent_briefs(self, client_session_id: str, limit: int = 10) -> list:
        """Get recent briefs - Mock implementation"""
        try:
            # Filter briefs by client session
            session_briefs = [
                brief for brief in self.mock_briefs.values()
                if brief.get('client_session_id') == client_session_id
            ]
            
            # Sort by created_at (newest first) and limit
            sorted_briefs = sorted(
                session_briefs, 
                key=lambda x: x.get('created_at', ''), 
                reverse=True
            )[:limit]
            
            # Create summary for list view
            briefs = []
            for brief_data in sorted_briefs:
                brief_summary = {
                    'id': brief_data['id'],
                    'summary': brief_data['summary'],
                    'created_at': brief_data['created_at'],
                    'decisions_count': len(brief_data.get('decisions', [])),
                    'actions_count': len(brief_data.get('actions', [])),
                    'questions_count': len(brief_data.get('questions', []))
                }
                briefs.append(brief_summary)
            
            logger.info(f"Retrieved {len(briefs)} mock briefs for session {client_session_id}")
            return briefs
            
        except Exception as e:
            logger.error(f"Failed to get recent briefs: {e}")
            raise Exception(f"Failed to retrieve recent briefs: {str(e)}")
    
    def delete_brief(self, brief_id: str, client_session_id: str) -> bool:
        """Delete a brief - Mock implementation"""
        try:
            # Check if brief exists and user owns it
            brief_data = self.get_brief_by_id(brief_id, client_session_id)
            if not brief_data:
                logger.warning(f"Cannot delete brief {brief_id}: not found or unauthorized")
                return False
            
            # Delete from mock storage
            del self.mock_briefs[brief_id]
            
            logger.info(f"Deleted mock brief: {brief_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete brief {brief_id}: {e}")
            raise Exception(f"Failed to delete brief: {str(e)}")
    
    def find_existing_brief(self, client_session_id: str, text_hash: str) -> Optional[Dict[str, Any]]:
        """Find existing brief by hash - Mock implementation"""
        try:
            for brief in self.mock_briefs.values():
                if (brief.get('client_session_id') == client_session_id and 
                    brief.get('sha256') == text_hash):
                    logger.info(f"Found existing mock brief for hash {text_hash}")
                    return brief
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to search for existing brief: {e}")
            return None
