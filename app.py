import os
from app_factory import create_app

# Get configuration from environment
config_name = os.environ.get('FLASK_CONFIG', 'default')

# Create application instance
app = create_app(config_name)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=app.config.get('DEBUG', False))
