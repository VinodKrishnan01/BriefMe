from google.cloud import firestore
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from utils.config import Config
from utils.helpers import generate_sha256, generate_uuid, get_current_timestamp

logger = logging.getLogger(__name__)

class FirestoreService:
    """Service for interacting with Firestore"""
    
    def __init__(self):
        """Initialize Firestore client"""
        # Use database id from configuration (defaults to "(default)" if not set)
        database_id = getattr(Config, 'FIRESTORE_DATABASE_ID', '(default)') or '(default)'
        self.db = firestore.Client(project=Config.GCP_PROJECT_ID, database=database_id)
        self.collection = self.db.collection(Config.FIRESTORE_COLLECTION)
        logger.info(
            f"Firestore initialized | project={Config.GCP_PROJECT_ID} | database={database_id} | collection={Config.FIRESTORE_COLLECTION}"
        )
    
    def create_brief(self, brief_data: Dict[str, Any]) -> str:
        """
        Create a new brief in Firestore
        
        Args:
            brief_data (Dict): Brief data to store
            
        Returns:
            str: Document ID of created brief
        """
        try:
            # Generate document ID
            doc_id = generate_uuid()
            
            # Add metadata
            brief_data['id'] = doc_id
            brief_data['created_at'] = get_current_timestamp()
            
            # Create document
            doc_ref = self.collection.document(doc_id)
            doc_ref.set(brief_data)
            
            logger.info(f"Created brief with ID: {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to create brief: {e}")
            raise Exception(f"Failed to store brief in database: {str(e)}")
    
    def get_brief_by_id(self, brief_id: str, client_session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a brief by ID, ensuring it belongs to the client session
        
        Args:
            brief_id (str): Brief document ID
            client_session_id (str): Client session ID
            
        Returns:
            Dict or None: Brief data if found and authorized
        """
        try:
            doc_ref = self.collection.document(brief_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                logger.warning(f"Brief not found: {brief_id}")
                return None
            
            brief_data = doc.to_dict()
            
            # Check authorization
            if brief_data.get('client_session_id') != client_session_id:
                logger.warning(f"Unauthorized access attempt for brief {brief_id}")
                return None
            
            return brief_data
            
        except Exception as e:
            logger.error(f"Failed to get brief {brief_id}: {e}")
            raise Exception(f"Failed to retrieve brief: {str(e)}")
    
    def get_recent_briefs(self, client_session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent briefs for a client session
        
        Args:
            client_session_id (str): Client session ID
            limit (int): Maximum number of briefs to return
            
        Returns:
            List[Dict]: List of brief summaries
        """
        try:
            query = (
                self.collection
                .where('client_session_id', '==', client_session_id)
                .order_by('created_at', direction=firestore.Query.DESCENDING)
                .limit(limit)
            )

            docs = query.stream()

            briefs: List[Dict[str, Any]] = []
            for doc in docs:
                brief_data = doc.to_dict()

                # Create summary for list view
                brief_summary = {
                    'id': brief_data['id'],
                    'summary': brief_data['summary'],
                    'created_at': brief_data['created_at'],
                    'decisions_count': len(brief_data.get('decisions', [])),
                    'actions_count': len(brief_data.get('actions', [])),
                    'questions_count': len(brief_data.get('questions', [])),
                }
                briefs.append(brief_summary)

            logger.info(f"Retrieved {len(briefs)} briefs for session {client_session_id}")
            return briefs

        except Exception as e:
            # Graceful fallback if a composite index is required
            msg = str(e)
            if 'The query requires an index' in msg:
                logger.warning(
                    "Missing composite index for (client_session_id EQ, created_at DESC). "
                    "Falling back to unindexed query + local sort. "
                    "Create the index in Firebase Console for best performance."
                )
                try:
                    # Fallback: query on client_session_id only (uses single-field index),
                    # then sort locally by created_at desc and apply limit
                    docs = (
                        self.collection
                        .where('client_session_id', '==', client_session_id)
                        .stream()
                    )
                    all_items: List[Dict[str, Any]] = [d.to_dict() for d in docs]
                    # Sort by created_at descending, missing values last
                    all_items.sort(
                        key=lambda b: b.get('created_at'),
                        reverse=True,
                    )
                    sliced = all_items[:limit]
                    briefs: List[Dict[str, Any]] = []
                    for brief_data in sliced:
                        brief_summary = {
                            'id': brief_data['id'],
                            'summary': brief_data['summary'],
                            'created_at': brief_data['created_at'],
                            'decisions_count': len(brief_data.get('decisions', [])),
                            'actions_count': len(brief_data.get('actions', [])),
                            'questions_count': len(brief_data.get('questions', [])),
                        }
                        briefs.append(brief_summary)
                    return briefs
                except Exception as inner_e:
                    logger.error(f"Fallback query failed: {inner_e}")
                    raise Exception(f"Failed to retrieve recent briefs: {str(inner_e)}")
            logger.error(f"Failed to get recent briefs: {e}")
            raise Exception(f"Failed to retrieve recent briefs: {str(e)}")
    
    def delete_brief(self, brief_id: str, client_session_id: str) -> bool:
        """
        Delete a brief, ensuring it belongs to the client session
        
        Args:
            brief_id (str): Brief document ID
            client_session_id (str): Client session ID
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            # First verify ownership
            brief_data = self.get_brief_by_id(brief_id, client_session_id)
            if not brief_data:
                logger.warning(f"Cannot delete brief {brief_id}: not found or unauthorized")
                return False
            
            # Delete the document
            doc_ref = self.collection.document(brief_id)
            doc_ref.delete()
            
            logger.info(f"Deleted brief: {brief_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete brief {brief_id}: {e}")
            raise Exception(f"Failed to delete brief: {str(e)}")
    
    def find_existing_brief(self, client_session_id: str, text_hash: str) -> Optional[Dict[str, Any]]:
        """
        Find existing brief with the same text hash to avoid duplicate processing
        
        Args:
            client_session_id (str): Client session ID
            text_hash (str): SHA256 hash of source text
            
        Returns:
            Dict or None: Existing brief data if found
        """
        try:
            query = (
                self.collection
                .where('client_session_id', '==', client_session_id)
                .where('sha256', '==', text_hash)
                .limit(1)
            )

            docs = list(query.stream())

            if docs:
                brief_data = docs[0].to_dict()
                logger.info(f"Found existing brief for hash {text_hash}")
                return brief_data

            return None

        except Exception as e:
            msg = str(e)
            if 'The query requires an index' in msg:
                logger.warning(
                    "Missing composite index for (client_session_id EQ, sha256 EQ). "
                    "Falling back to single-field query on sha256 and filtering locally."
                )
                try:
                    docs = (
                        self.collection
                        .where('sha256', '==', text_hash)
                        .stream()
                    )
                    for d in docs:
                        data = d.to_dict()
                        if data.get('client_session_id') == client_session_id:
                            logger.info(f"Found existing brief for hash {text_hash} via fallback")
                            return data
                    return None
                except Exception as inner_e:
                    logger.error(f"Fallback duplicate-check query failed: {inner_e}")
                    return None
            logger.error(f"Failed to search for existing brief: {e}")
            # Don't raise exception here, just return None to proceed with new brief
            return None
