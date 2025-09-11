import google.generativeai as genai
import json
import logging
from typing import Dict, Any, Optional
from utils.config import Config

logger = logging.getLogger(__name__)

class GeminiService:
    """Service for interacting with Google Gemini API"""
    
    def __init__(self):
        """Initialize Gemini service"""
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-pro')
    
    def generate_brief(self, source_text: str) -> Dict[str, Any]:
        """
        Generate a structured brief from source text using Gemini
        
        Args:
            source_text (str): The input text to generate brief from
            
        Returns:
            Dict: Structured brief with summary, decisions, actions, questions
            
        Raises:
            Exception: If LLM call fails or returns invalid JSON
        """
        prompt = self._create_prompt(source_text)
        
        try:
            # First attempt
            response = self._call_gemini(prompt)
            result = self._parse_response(response)
            return result
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"First attempt failed with error: {e}. Retrying with stricter prompt.")
            
            # Retry with stricter prompt
            strict_prompt = self._create_strict_prompt(source_text)
            try:
                response = self._call_gemini(strict_prompt)
                result = self._parse_response(response)
                return result
                
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Second attempt also failed: {e}")
                raise Exception("Failed to generate valid brief after retry")
    
    def _create_prompt(self, source_text: str) -> str:
        """Create the initial prompt for Gemini"""
        return f"""
Please analyze the following text and create a structured brief. Return ONLY a valid JSON object with no additional text or markdown formatting.

The JSON must have exactly these fields:
- "summary": string (maximum 100 words)
- "decisions": array of strings
- "actions": array of objects, each with "text" (string), "owner" (string or null), "due_date" (string in YYYY-MM-DD format or null)
- "questions": array of strings

Text to analyze:
{source_text}

Return only the JSON:
"""

    def _create_strict_prompt(self, source_text: str) -> str:
        """Create a stricter prompt for retry"""
        return f"""
IMPORTANT: Return ONLY valid JSON. No markdown, no explanations, no additional text.

Analyze this text and return a JSON object with this exact structure:
{{
  "summary": "brief summary in 100 words or less",
  "decisions": ["decision 1", "decision 2"],
  "actions": [
    {{"text": "action description", "owner": "person name or null", "due_date": "YYYY-MM-DD or null"}}
  ],
  "questions": ["question 1", "question 2"]
}}

Text: {source_text}

JSON:
"""

    def _call_gemini(self, prompt: str) -> str:
        """Make API call to Gemini"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise Exception(f"Failed to call Gemini API: {str(e)}")
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse and validate Gemini response"""
        # Clean up response text
        cleaned_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if cleaned_text.startswith('```json'):
            cleaned_text = cleaned_text[7:]
        if cleaned_text.startswith('```'):
            cleaned_text = cleaned_text[3:]
        if cleaned_text.endswith('```'):
            cleaned_text = cleaned_text[:-3]
        
        cleaned_text = cleaned_text.strip()
        
        try:
            result = json.loads(cleaned_text)
            
            # Validate required fields
            required_fields = ['summary', 'decisions', 'actions', 'questions']
            for field in required_fields:
                if field not in result:
                    raise KeyError(f"Missing required field: {field}")
            
            # Validate field types
            if not isinstance(result['summary'], str):
                raise ValueError("Summary must be a string")
            if not isinstance(result['decisions'], list):
                raise ValueError("Decisions must be a list")
            if not isinstance(result['actions'], list):
                raise ValueError("Actions must be a list")
            if not isinstance(result['questions'], list):
                raise ValueError("Questions must be a list")
            
            # Validate actions structure
            for action in result['actions']:
                if not isinstance(action, dict) or 'text' not in action:
                    raise ValueError("Each action must be an object with 'text' field")
            
            # Truncate summary if too long
            if len(result['summary']) > 500:  # Allow some buffer beyond 100 words
                words = result['summary'].split()[:100]
                result['summary'] = ' '.join(words)
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}. Response text: {cleaned_text}")
            raise
        except (KeyError, ValueError) as e:
            logger.error(f"Invalid response structure: {e}")
            raise
