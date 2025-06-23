import os
from app_factory import create_app

# Get configuration from environment
config_name = os.environ.get('FLASK_CONFIG', 'default')

# Create application instance
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

if __name__ == '__main__':
    # The host must be '0.0.0.0' to be accessible from outside the container
    # The port is handled by Gunicorn in production, this is for local dev only
    app.run(host='0.0.0.0')
