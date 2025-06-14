# app.py
from flask import Flask
from routes.client_routes import client_bp
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)

def create_app():
    # Set template folder relative to project root
    template_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
    
    app = Flask(__name__, template_folder=template_folder)
    app.secret_key = 'your-secret-key-here'  # Ganti dengan secret key yang aman
    
    # Register blueprints
    app.register_blueprint(client_bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Not found"}, 404
        
    @app.errorhandler(500)
    def internal_error(error):
        return {"error": "Internal server error"}, 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    print(f"Template folder: {app.template_folder}")
    # Ganti port sesuai kebutuhan, misalnya:
    app.run(debug=True, host='0.0.0.0', port=5005)