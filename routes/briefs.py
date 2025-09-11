from flask import request, jsonify
from flask_restx import Resource, Namespace, fields
from marshmallow import ValidationError
import logging

from models.schemas import CreateBriefSchema, BriefResponseSchema, BriefSummarySchema
from services.firestore_service import FirestoreService
from services.gemini_service import GeminiService
from utils.helpers import generate_sha256, is_valid_uuid

logger = logging.getLogger(__name__)

# Create namespace for API documentation
api = Namespace('briefs', description='Brief generation and management operations')

# Define models for Swagger documentation
create_brief_model = api.model('CreateBrief', {
    'source_text': fields.String(required=True, description='Text to generate brief from (max 10,000 chars)'),
    'client_session_id': fields.String(required=True, description='Client session UUID')
})

action_item_model = api.model('ActionItem', {
    'text': fields.String(required=True, description='Action item description'),
    'owner': fields.String(description='Optional owner of the action item'),
    'due_date': fields.String(description='Optional due date in YYYY-MM-DD format')
})

brief_response_model = api.model('BriefResponse', {
    'id': fields.String(required=True, description='Brief ID'),
    'client_session_id': fields.String(required=True, description='Client session ID'),
    'source_text': fields.String(required=True, description='Original source text'),
    'summary': fields.String(required=True, description='Brief summary (max 100 words)'),
    'decisions': fields.List(fields.String, required=True, description='List of decisions'),
    'actions': fields.List(fields.Nested(action_item_model), required=True, description='List of action items'),
    'questions': fields.List(fields.String, required=True, description='List of open questions'),
    'created_at': fields.DateTime(required=True, description='Creation timestamp'),
    'sha256': fields.String(required=True, description='SHA256 hash of source text')
})

brief_summary_model = api.model('BriefSummary', {
    'id': fields.String(required=True, description='Brief ID'),
    'summary': fields.String(required=True, description='Brief summary'),
    'created_at': fields.DateTime(required=True, description='Creation timestamp'),
    'decisions_count': fields.Integer(required=True, description='Number of decisions'),
    'actions_count': fields.Integer(required=True, description='Number of action items'),
    'questions_count': fields.Integer(required=True, description='Number of open questions')
})

# Initialize services
firestore_service = FirestoreService()
gemini_service = GeminiService()

@api.route('')
class BriefListResource(Resource):
    
    @api.doc('create_brief')
    @api.expect(create_brief_model)
    @api.marshal_with(brief_response_model, code=201)
    @api.response(400, 'Validation error')
    @api.response(409, 'Duplicate content - existing brief returned')
    @api.response(500, 'Internal server error')
    def post(self):
        """Create a new brief from source text"""
        try:
            # Validate request data
            schema = CreateBriefSchema()
            try:
                validated_data = schema.load(request.json)
            except ValidationError as e:
                return {'error': 'Validation failed', 'details': e.messages}, 400
            
            source_text = validated_data['source_text']
            client_session_id = validated_data['client_session_id']
            
            # Validate client session ID format
            if not is_valid_uuid(client_session_id):
                return {'error': 'Invalid client session ID format'}, 400
            
            # Generate hash for duplicate detection
            text_hash = generate_sha256(source_text)
            
            # Check for existing brief with same content
            existing_brief = firestore_service.find_existing_brief(client_session_id, text_hash)
            if existing_brief:
                logger.info(f"Returning existing brief for duplicate content")
                return existing_brief, 209  # 209 = Content Already Reported (non-standard but descriptive)
            
            # Generate brief using Gemini
            try:
                llm_result = gemini_service.generate_brief(source_text)
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
                return {'error': 'Failed to generate brief', 'details': str(e)}, 500
            
            # Prepare data for storage
            brief_data = {
                'client_session_id': client_session_id,
                'source_text': source_text,
                'summary': llm_result['summary'],
                'decisions': llm_result['decisions'],
                'actions': llm_result['actions'],
                'questions': llm_result['questions'],
                'sha256': text_hash
            }
            
            # Store in Firestore
            try:
                brief_id = firestore_service.create_brief(brief_data)
                brief_data['id'] = brief_id
            except Exception as e:
                logger.error(f"Failed to store brief: {e}")
                return {'error': 'Failed to store brief', 'details': str(e)}, 500
            
            return brief_data, 201
            
        except Exception as e:
            logger.error(f"Unexpected error in create_brief: {e}")
            return {'error': 'Internal server error'}, 500
    
    @api.doc('get_recent_briefs')
    @api.param('client_session_id', 'Client session UUID', required=True)
    @api.param('limit', 'Maximum number of briefs to return (default: 10)', type=int)
    @api.marshal_list_with(brief_summary_model)
    @api.response(400, 'Validation error')
    @api.response(500, 'Internal server error')
    def get(self):
        """Get recent briefs for a client session"""
        try:
            # Get query parameters
            client_session_id = request.args.get('client_session_id')
            limit = request.args.get('limit', 10, type=int)
            
            if not client_session_id:
                return {'error': 'client_session_id parameter is required'}, 400
            
            if not is_valid_uuid(client_session_id):
                return {'error': 'Invalid client session ID format'}, 400
            
            if limit < 1 or limit > 50:
                return {'error': 'Limit must be between 1 and 50'}, 400
            
            # Get recent briefs
            try:
                briefs = firestore_service.get_recent_briefs(client_session_id, limit)
                return briefs, 200
            except Exception as e:
                logger.error(f"Failed to get recent briefs: {e}")
                return {'error': 'Failed to retrieve briefs', 'details': str(e)}, 500
                
        except Exception as e:
            logger.error(f"Unexpected error in get_recent_briefs: {e}")
            return {'error': 'Internal server error'}, 500

@api.route('/<string:brief_id>')
class BriefResource(Resource):
    
    @api.doc('get_brief')
    @api.param('client_session_id', 'Client session UUID', required=True)
    @api.marshal_with(brief_response_model)
    @api.response(400, 'Validation error')
    @api.response(404, 'Brief not found')
    @api.response(500, 'Internal server error')
    def get(self, brief_id):
        """Get a specific brief by ID"""
        try:
            # Get query parameters
            client_session_id = request.args.get('client_session_id')
            
            if not client_session_id:
                return {'error': 'client_session_id parameter is required'}, 400
            
            if not is_valid_uuid(client_session_id):
                return {'error': 'Invalid client session ID format'}, 400
            
            if not is_valid_uuid(brief_id):
                return {'error': 'Invalid brief ID format'}, 400
            
            # Get brief
            try:
                brief = firestore_service.get_brief_by_id(brief_id, client_session_id)
                if not brief:
                    return {'error': 'Brief not found or access denied'}, 404
                
                return brief, 200
            except Exception as e:
                logger.error(f"Failed to get brief {brief_id}: {e}")
                return {'error': 'Failed to retrieve brief', 'details': str(e)}, 500
                
        except Exception as e:
            logger.error(f"Unexpected error in get_brief: {e}")
            return {'error': 'Internal server error'}, 500
    
    @api.doc('delete_brief')
    @api.param('client_session_id', 'Client session UUID', required=True)
    @api.response(204, 'Brief deleted successfully')
    @api.response(400, 'Validation error')
    @api.response(404, 'Brief not found')
    @api.response(500, 'Internal server error')
    def delete(self, brief_id):
        """Delete a specific brief by ID"""
        try:
            # Get query parameters
            client_session_id = request.args.get('client_session_id')
            
            if not client_session_id:
                return {'error': 'client_session_id parameter is required'}, 400
            
            if not is_valid_uuid(client_session_id):
                return {'error': 'Invalid client session ID format'}, 400
            
            if not is_valid_uuid(brief_id):
                return {'error': 'Invalid brief ID format'}, 400
            
            # Delete brief
            try:
                success = firestore_service.delete_brief(brief_id, client_session_id)
                if not success:
                    return {'error': 'Brief not found or access denied'}, 404
                
                return '', 204
            except Exception as e:
                logger.error(f"Failed to delete brief {brief_id}: {e}")
                return {'error': 'Failed to delete brief', 'details': str(e)}, 500
                
        except Exception as e:
            logger.error(f"Unexpected error in delete_brief: {e}")
            return {'error': 'Internal server error'}, 500
