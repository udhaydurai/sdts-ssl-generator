# Use a specific, stable Python version that is common on hosting platforms
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy all application code into the container first
COPY . .

# Now, install dependencies using pyproject.toml
# This creates a consistent and reproducible environment
RUN pip install .

# Set the production flag for the application
ENV FLASK_CONFIG=production

# The PORT environment variable will be provided by the hosting platform (e.g., Cloud Run).
# Gunicorn will bind to this port.
# Exposing the port is good practice for container-based deployments.
EXPOSE 8080

# The standard, robust command to run a Flask app in production with Gunicorn.
# This will be executed by the hosting platform inside the container.
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080", "--workers", "4"]