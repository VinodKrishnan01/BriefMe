import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_restx import Api
from utils.config import Config
import logging

def create_debug_app():
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Enable CORS
    CORS(app, origins=["http://localhost:3000"])
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize Flask-RESTX
    api = Api(
        app,
        version='1.0',
        title='Brief Generator API',
        description='API for generating structured briefs from text using Gemini AI',
        doc='/api/docs/',  # This should create the docs route
        prefix='/api'
    )
    
    # Register namespaces
    from routes.briefs import api as briefs_ns
    api.add_namespace(briefs_ns, path='/briefs')
    
    # Debug route to show all available routes
    @app.route('/debug/routes')
    def show_routes():
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'rule': str(rule)
            })
        return jsonify(routes)
    
    # Health endpoint
    @app.route('/health')
    def health():
        return jsonify({
            "status": "healthy",
            "message": "Brief Generator API is running!",
            "all_routes": "http://localhost:5000/debug/routes"
        })
    
    return app

def main():
    app = create_debug_app()
    
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Starting DEBUG Brief Generator API on port {port}")
    print(f"🔍 All Routes: http://localhost:{port}/debug/routes")
    print(f"❤️  Health Check: http://localhost:{port}/health")
    print(f"📚 API Documentation SHOULD BE: http://localhost:{port}/api/docs/")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )

if __name__ == '__main__':
    main()