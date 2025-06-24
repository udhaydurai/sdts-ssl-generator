from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix
import logging
import os
from config import config

def create_app(config_name='default'):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Ensure SESSION_SECRET is set in production
    if not app.config.get('DEBUG') and not app.config.get('TESTING'):
        if not app.config.get('SESSION_SECRET'):
            raise ValueError("SESSION_SECRET is not set. Please set it as a Replit Secret.")
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, app.config['LOG_LEVEL']),
        format=app.config['LOG_FORMAT']
    )
    
    # Security middleware
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Rate limiting
    if app.config['RATE_LIMIT_ENABLED']:
        storage_uri = app.config.get('REDIS_URL') or "memory://"
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            storage_uri=storage_uri,
            default_limits=["200 per day", "50 per hour"]
        )
        app.limiter = limiter
    
    # Create upload directory (skip on Vercel due to read-only filesystem)
    if not os.environ.get('VERCEL'):
        try:
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        except OSError as e:
            # Log the error but don't fail the app startup
            logging.warning(f"Could not create upload directory: {e}")
    else:
        # On Vercel, we don't need the upload directory since we handle files in memory
        logging.info("Running on Vercel - skipping upload directory creation")
    
    # Register blueprints
    from routes import main_bp
    app.register_blueprint(main_bp)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app

def register_error_handlers(app):
    """Register error handlers"""
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500
    
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return {'error': 'Rate limit exceeded'}, 429 