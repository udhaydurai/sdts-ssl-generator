import os
from app_factory import create_app

# Get configuration from environment
config_name = os.environ.get('FLASK_CONFIG', 'default')

# Create application instance
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

if __name__ == '__main__':
    # The port is set by the PORT environment variable, defaulting to 5001 for local development
    port = int(os.environ.get('PORT', 5001))
    # The host must be '0.0.0.0' to be accessible from outside the container
    app.run(host='0.0.0.0', port=port)
