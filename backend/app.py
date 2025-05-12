# backend/app.py
import os
from flask import Flask, send_from_directory
from dotenv import load_dotenv

# Load environment variables from .env file at the project root
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Import logger after loading .env
from backend.utils.logger import logger

# Import blueprints after logger and env vars are set up
from backend.api.candidates import candidates_bp
from backend.api.chat import chat_bp

def create_app():
    """Creates and configures the Flask application."""
    # __name__ is 'backend' because of the directory structure
    # static_folder points to 'static' inside 'backend'
    # template_folder points to 'templates' inside 'backend'
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-fallback-secret-key')

    logger.info("Flask app created.")
    logger.info(f"Flask environment: {os.getenv('FLASK_ENV', 'production')}") # Default to production if not set

    # Register Blueprints
    app.register_blueprint(candidates_bp)
    app.register_blueprint(chat_bp)
    logger.info("API Blueprints registered.")

    # Serve the main HTML file for the root URL
    @app.route('/')
    def index():
        logger.debug("Serving index.html")
        # Assumes index.html is in the 'templates' folder adjacent to this file
        return send_from_directory(app.template_folder, 'index.html')

    # Route to serve static files (CSS, JS) - Flask does this automatically if static_folder is set
    # But defining it explicitly can sometimes help with debugging or specific configurations.
    # @app.route('/static/<path:filename>')
    # def static_files(filename):
    #    return send_from_directory(app.static_folder, filename)

    # Optional: Add a health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({"status": "ok"}), 200

    return app

# Create the app instance for Gunicorn or direct execution
app = create_app()

if __name__ == '__main__':
    # Run in debug mode if FLASK_ENV is development
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    logger.info(f"Starting Flask development server (Debug Mode: {debug_mode})...")
    # Host 0.0.0.0 makes it accessible externally, e.g., from Docker host
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)