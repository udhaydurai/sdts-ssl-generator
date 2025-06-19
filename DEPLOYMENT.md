# Deployment Guide

## Replit Deployment

This application is optimized for Replit deployment with automatic scaling.

### Setup
1. Import this repository to Replit
2. Install dependencies automatically via `pyproject.toml`
3. Configure environment variables in Replit Secrets
4. Run with the configured workflow

### Environment Variables
- `SESSION_SECRET`: Random string for Flask sessions
- `DATABASE_URL`: PostgreSQL connection (auto-configured in Replit)

## Docker Deployment

### Build and Run
```bash
docker build -t sdts-ssl-generator .
docker run -p 5000:5000 -e SESSION_SECRET=your-secret-key sdts-ssl-generator
```

### Docker Compose
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - SESSION_SECRET=your-secret-key
      - FLASK_ENV=production
    volumes:
      - ./temp_certs:/app/temp_certs
```

## Traditional Server Deployment

### Ubuntu/Debian Setup
```bash
# Install Python and dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx

# Clone and setup
git clone https://github.com/udhaydurai/sdts-ssl-generator.git
cd sdts-ssl-generator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-github.txt

# Run with Gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 main:app
```

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Security Considerations

1. **HTTPS Required**: Always deploy behind HTTPS in production
2. **Firewall**: Restrict access to necessary ports only
3. **File Permissions**: Ensure temporary certificate files are properly secured
4. **Session Security**: Use strong SESSION_SECRET values
5. **Rate Limiting**: Consider implementing rate limiting for certificate requests

## Production Checklist

- [ ] HTTPS enabled with valid SSL certificate
- [ ] SESSION_SECRET configured
- [ ] Database connection tested (if using database features)
- [ ] Temporary file cleanup verified
- [ ] DNS validation domains tested
- [ ] Rate limiting configured
- [ ] Monitoring and logging enabled
- [ ] Backup strategy implemented

## Monitoring

### Health Check Endpoint
The application provides a basic health check at the root URL (`/`).

### Logging
Application logs include:
- Certificate generation requests
- DNS validation attempts
- ACME client operations
- Error conditions

### Metrics to Monitor
- Certificate generation success rate
- DNS validation response times
- Application response times
- Storage usage (temporary files)
- ACME API rate limits

## Troubleshooting

### Common Issues

1. **DNS Validation Failures**
   - Check DNS record propagation
   - Verify domain ownership
   - Test with multiple DNS servers

2. **ACME Rate Limits**
   - Use staging environment for testing
   - Implement proper caching
   - Monitor Let's Encrypt rate limits

3. **Certificate Storage**
   - Ensure temporary directory exists
   - Check file permissions
   - Monitor disk space

### Debug Mode
For development, enable debug mode:
```bash
export FLASK_ENV=development
python main.py
```