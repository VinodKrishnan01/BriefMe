import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_restx import Api, Resource, fields
import logging

def create_app():
    app = Flask(__name__)
    
    # Enable CORS
    CORS(app, origins=["http://localhost:3000"])
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Health endpoint
    @app.route('/health')
    def health():
        return jsonify({
            "status": "healthy",
            "message": "Brief Generator API is running!",
            "docs": "/api/docs/"
        })
    
    # Initialize Flask-RESTX
    api = Api(
        app,
        version='1.0',
        title='Brief Generator API',
        description='API for generating structured briefs from text using Gemini AI',
        doc='/api/docs/',
        prefix='/api'
    )
    
    # Create namespace
    brief_ns = api.namespace('briefs', description='Brief operations')
    
    # Define models for Swagger
    create_brief_model = api.model('CreateBrief', {
        'source_text': fields.String(required=True, description='Text to analyze'),
        'client_session_id': fields.String(required=True, description='Client session UUID')
    })
    
    brief_response_model = api.model('BriefResponse', {
        'id': fields.String(description='Brief ID'),
        'summary': fields.String(description='Brief summary'),
        'decisions': fields.List(fields.String, description='Decisions'),
        'actions': fields.List(fields.Raw, description='Action items'),
        'questions': fields.List(fields.String, description='Questions'),
        'created_at': fields.String(description='Creation timestamp')
    })
    
    # API Routes
    @brief_ns.route('')
    class BriefList(Resource):
        @brief_ns.expect(create_brief_model)
        @brief_ns.marshal_with(brief_response_model, code=201)
        def post(self):
            """Create a new brief"""
            data = request.json
            
            # Basic validation
            if not data or 'source_text' not in data or 'client_session_id' not in data:
                return {'error': 'Missing required fields'}, 400
            
            # Mock response for now
            return {
                'id': 'mock-brief-id-123',
                'summary': 'This is a mock brief summary',
                'decisions': ['Mock decision 1', 'Mock decision 2'],
                'actions': [{'text': 'Mock action', 'owner': None, 'due_date': None}],
                'questions': ['Mock question 1'],
                'created_at': '2024-01-01T00:00:00Z'
            }, 201
        
        def get(self):
            """Get recent briefs"""
            client_session_id = request.args.get('client_session_id')
            if not client_session_id:
                return {'error': 'client_session_id parameter required'}, 400
                
            # Mock response
            return [{
                'id': 'mock-brief-1',
                'summary': 'Mock brief summary',
                'created_at': '2024-01-01T00:00:00Z'
            }], 200
    
    @brief_ns.route('/<string:brief_id>')
    class Brief(Resource):
        @brief_ns.marshal_with(brief_response_model)
        def get(self, brief_id):
            """Get a specific brief"""
            client_session_id = request.args.get('client_session_id')
            if not client_session_id:
                return {'error': 'client_session_id parameter required'}, 400
                
            # Mock response
            return {
                'id': brief_id,
                'summary': 'Detailed mock brief summary',
                'decisions': ['Decision 1', 'Decision 2'],
                'actions': [{'text': 'Action item', 'owner': 'John', 'due_date': '2024-01-15'}],
                'questions': ['What is the timeline?'],
                'created_at': '2024-01-01T00:00:00Z'
            }, 200
        
        def delete(self, brief_id):
            """Delete a specific brief"""
            client_session_id = request.args.get('client_session_id')
            if not client_session_id:
                return {'error': 'client_session_id parameter required'}, 400
                
            return '', 204
    
    return app

def main():
    app = create_app()
    
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Starting Brief Generator API on port {port}")
    print(f"📚 API Documentation: http://localhost:{port}/api/docs/")
    print(f"🏥 Health Check: http://localhost:{port}/health")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )

if __name__ == '__main__':
    main()
