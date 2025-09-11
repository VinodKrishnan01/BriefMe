import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_restx import Api
import logging

def create_minimal_app():
    app = Flask(__name__)
    
    # Enable CORS
    CORS(app, origins=["http://localhost:3000"])
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    print("✅ Flask app created")
    
    try:
        # Initialize Flask-RESTX
        api = Api(
            app,
            version='1.0',
            title='Brief Generator API',
            description='API for generating structured briefs from text using Gemini AI',
            doc='/api/docs/',
            prefix='/api'
        )
        print("✅ Flask-RESTX initialized")
        
        # Create a simple test namespace WITHOUT importing routes
        from flask_restx import Namespace, Resource
        
        test_ns = Namespace('test', description='Test operations')
        
        @test_ns.route('/hello')
        class HelloWorld(Resource):
            def get(self):
                return {'message': 'Hello World!'}
        
        api.add_namespace(test_ns, path='/test')
        print("✅ Test namespace added")
        
    except Exception as e:
        print(f"❌ Error with Flask-RESTX: {e}")
        return None
    
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
            "message": "Minimal Debug API is running!",
            "all_routes": "http://localhost:5000/debug/routes"
        })
    
    # Root redirect
    @app.route('/')
    def root():
        return jsonify({
            "message": "Minimal Debug API",
            "health": "/health",
            "routes": "/debug/routes",
            "docs": "/api/docs/"
        })
    
    return app

def main():
    print("🔍 Starting minimal debug app...")
    
    try:
        app = create_minimal_app()
        if app is None:
            print("❌ Failed to create app")
            return
            
        port = 5000
        
        print(f"🚀 Starting Minimal Debug API on port {port}")
        print(f"🏠 Root: http://localhost:{port}/")
        print(f"🔍 All Routes: http://localhost:{port}/debug/routes")
        print(f"❤️  Health Check: http://localhost:{port}/health")
        print(f"📚 API Documentation: http://localhost:{port}/api/docs/")
        
        app.run(
            host='0.0.0.0',
            port=port,
            debug=True
        )
        
    except Exception as e:
        print(f"❌ Error starting app: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()