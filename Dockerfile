# Use a specific, stable Python version
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the file that defines our project and dependencies
COPY pyproject.toml .

# Install dependencies using the now-standard pyproject.toml
# This creates a consistent and reproducible environment
RUN pip install .

# Copy the rest of the application code into the container
COPY . .

# Set the production flag for the application
ENV FLASK_CONFIG=production

# The port will be provided by Replit via the $PORT environment variable
# The self-hosting app.py will read this variable
# No EXPOSE needed as Replit handles port mapping

# The command to run the self-hosting application
CMD ["python", "app.py"]