import json
import logging
from typing import Dict, Any, Optional
from utils.config import Config

logger = logging.getLogger(__name__)

class GeminiService:
    """Service for interacting with Google Gemini API - Mock version for development"""
    
    def __init__(self):
        """Initialize Gemini service"""
        logger.info("Initializing GeminiService (Mock Mode)")
        # For now, use mock responses
        self.mock_mode = True
    
    def generate_brief(self, source_text: str) -> Dict[str, Any]:
        """
        Generate a structured brief from source text - Mock implementation
        
        Args:
            source_text (str): The input text to generate brief from
            
        Returns:
            Dict: Structured brief with summary, decisions, actions, questions
        """
        logger.info(f"Generating mock brief for text of length: {len(source_text)}")
        
        try:
            # Mock response based on input text
            word_count = len(source_text.split())
            
            # Generate mock content based on input
            mock_response = {
                "summary": f"This is a mock summary of the provided text ({word_count} words). The content appears to discuss various topics that would benefit from structured analysis and action planning.",
                "decisions": [
                    "Mock Decision: Proceed with the outlined approach",
                    "Mock Decision: Allocate necessary resources",
                    "Mock Decision: Set timeline for implementation"
                ],
                "actions": [
                    {
                        "text": "Review and validate the mock analysis results",
                        "owner": "Project Manager",
                        "due_date": "2024-01-15"
                    },
                    {
                        "text": "Implement the recommended changes",
                        "owner": None,
                        "due_date": None
                    },
                    {
                        "text": "Schedule follow-up meeting",
                        "owner": "Team Lead",
                        "due_date": "2024-01-20"
                    }
                ],
                "questions": [
                    "What are the key success metrics for this initiative?",
                    "Who will be responsible for ongoing monitoring?",
                    "What is the expected timeline for completion?",
                    "Are there any potential risks we should consider?"
                ]
            }
            
            # Validate the response structure
            self._validate_response(mock_response)
            
            logger.info("Successfully generated mock brief")
            return mock_response
            
        except Exception as e:
            logger.error(f"Failed to generate mock brief: {e}")
            raise Exception(f"Failed to generate brief: {str(e)}")
    
    def _validate_response(self, response: Dict[str, Any]) -> None:
        """Validate the response structure"""
        required_fields = ['summary', 'decisions', 'actions', 'questions']
        
        for field in required_fields:
            if field not in response:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate field types
        if not isinstance(response['summary'], str):
            raise ValueError("Summary must be a string")
        if not isinstance(response['decisions'], list):
            raise ValueError("Decisions must be a list")
        if not isinstance(response['actions'], list):
            raise ValueError("Actions must be a list")
        if not isinstance(response['questions'], list):
            raise ValueError("Questions must be a list")
        
        # Validate actions structure
        for action in response['actions']:
            if not isinstance(action, dict) or 'text' not in action:
                raise ValueError("Each action must be an object with 'text' field")
        
        # Truncate summary if too long (100 words max)
        words = response['summary'].split()
        if len(words) > 100:
            response['summary'] = ' '.join(words[:100]) + "..."
            
        logger.debug("Response validation passed")
