import os
from app_factory import create_app

# Get configuration from environment
config_name = os.environ.get('FLASK_CONFIG', 'default')

# Create application instance
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

if __name__ == '__main__':
    # Check if we are in a production environment (like Replit Deployments)
    is_production = os.environ.get('FLASK_CONFIG') == 'production' or not app.debug

    if is_production:
        # In production, start the Gunicorn server programmatically.
        # This is robust and avoids all PATH issues in the deployment environment.
        from gunicorn.app.base import BaseApplication

        class StandaloneApplication(BaseApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()

            def load_config(self):
                config = {key: value for key, value in self.options.items()
                          if key in self.cfg.settings and value is not None}
                for key, value in config.items():
                    self.cfg.set(key.lower(), value)

            def load(self):
                return self.application

        # Get the port from the environment, which Replit provides.
        port = int(os.environ.get('PORT', 8080))
        options = {
            'bind': f'0.0.0.0:{port}',
            'workers': 4,
        }
        StandaloneApplication(app, options).run()
    else:
        # For local development, use the simple Flask server.
        port = int(os.environ.get('PORT', 5001))
        app.run(host='0.0.0.0', port=port, debug=True)
