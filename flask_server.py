"""
Flask HTTP server wrapper for the image processing API.
Run this to start an HTTP server that the frontend can connect to.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import Application


# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize the backend application
backend_app = Application()
image_controller = backend_app.container.get_controller('image')


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "4IR Backend API",
        "version": "1.0.0"
    })


@app.route('/images/extract-text', methods=['POST'])
def extract_text():
    """Extract text from uploaded image."""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "error": {"message": "No JSON data provided"}
            }), 400
        
        # Run the async controller method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(image_controller.extract_text(data))
            return jsonify(result), result.get('status_code', 200)
        finally:
            loop.close()
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": {"message": str(e)}
        }), 500


@app.route('/images/health', methods=['GET'])
def image_service_health():
    """Image service health check."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(image_controller.health_check())
            return jsonify(result), result.get('status_code', 200)
        finally:
            loop.close()
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": {"message": str(e)}
        }), 500


if __name__ == '__main__':
    print("🚀 Starting 4IR Backend API Server...")
    print("📱 Frontend can now connect to: http://localhost:5000")
    print("🖼️  Image processing endpoint: POST /images/extract-text")
    print("💚 Health check: GET /health")
    
    app.run(host='0.0.0.0', port=5000, debug=True)