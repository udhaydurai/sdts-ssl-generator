# 🚀 Deployment Guide

This guide covers deploying the SDTS SSL Generator on different platforms.

## 🎯 Quick Start - Vercel (Recommended)

**One-click deployment:**
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/udhaydurai/sdts-ssl-generator)

**Manual steps:**
1. Fork this repository to your GitHub account
2. Go to [vercel.com](https://vercel.com) and sign up/login
3. Click "New Project" → "Import Git Repository"
4. Select your forked repository
5. Click "Deploy"

**✅ What you get:**
- Free hosting with generous limits
- Automatic HTTPS
- Global CDN
- Zero configuration
- Automatic deployments on git push

## 🐳 Docker Deployment

### Local Development
```bash
# Clone the repository
git clone https://github.com/udhaydurai/sdts-ssl-generator.git
cd sdts-ssl-generator

# Build the Docker image
docker build -t sdts-ssl-generator .

# Run locally
docker run -p 5001:8080 sdts-ssl-generator

# Access at http://localhost:5001
```

### Production Deployment
```bash
# Build for production
docker build -t sdts-ssl-generator .

# Run with production settings
docker run -d \
  -p 80:8080 \
  -e ACME_STAGING=false \
  -e LOG_LEVEL=INFO \
  --name ssl-generator \
  --restart unless-stopped \
  sdts-ssl-generator
```

### Docker Compose (Optional)
Create a `docker-compose.yml` file:
```yaml
version: '3.8'
services:
  ssl-generator:
    build: .
    ports:
      - "80:8080"
    environment:
      - ACME_STAGING=false
      - LOG_LEVEL=INFO
    restart: unless-stopped
```

Then run:
```bash
docker-compose up -d
```

## 🖥️ Traditional Hosting

### Prerequisites
- Python 3.9+
- pip
- gunicorn (for production)

### Installation
```bash
# Clone the repository
git clone https://github.com/udhaydurai/sdts-ssl-generator.git
cd sdts-ssl-generator

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ACME_STAGING=false
export LOG_LEVEL=INFO

# Run with Flask (development)
python app.py

# Or run with Gunicorn (production)
gunicorn app:app --bind 0.0.0.0:8080 --workers 2 --timeout 120
```

### Systemd Service (Linux)
Create `/etc/systemd/system/ssl-generator.service`:
```ini
[Unit]
Description=SDTS SSL Generator
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/sdts-ssl-generator
Environment=ACME_STAGING=false
Environment=LOG_LEVEL=INFO
ExecStart=/usr/local/bin/gunicorn app:app --bind 0.0.0.0:8080 --workers 2 --timeout 120
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl enable ssl-generator
sudo systemctl start ssl-generator
```

## ☁️ Cloud Platforms

### Railway
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will auto-detect and deploy

### Render
1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Click "New" → "Web Service"
4. Connect your repository
5. Set build command: `pip install -r requirements.txt`
6. Set start command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

### Fly.io
1. Install flyctl: `curl -L https://fly.io/install.sh | sh`
2. Login: `fly auth login`
3. Deploy: `fly launch`
4. Follow the prompts

### Google Cloud Run
1. Install gcloud CLI
2. Build and push:
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT/ssl-generator
gcloud run deploy ssl-generator --image gcr.io/YOUR_PROJECT/ssl-generator --platform managed
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_CONFIG` | `default` | Configuration profile |
| `ACME_STAGING` | `true` | Use Let's Encrypt staging |
| `LOG_LEVEL` | `INFO` | Logging level |
| `UPLOAD_FOLDER` | `./temp_certs` | Temp storage (not used on Vercel) |

### Production Settings
For production deployments, set:
```bash
export ACME_STAGING=false  # Use real Let's Encrypt certificates
export LOG_LEVEL=WARNING   # Reduce log verbosity
```

## 🔍 Troubleshooting

### Common Issues

#### **"Invalid or expired validation request"**
- **Fixed**: App now uses stateless session handling
- **If still occurs**: Check if you're using the latest version

#### **Vercel deployment fails**
- **Fixed**: App detects Vercel environment automatically
- **If still occurs**: Check Vercel logs for specific errors

#### **Let's Encrypt validation fails**
- **HTTP-01**: Check web server configuration
- **DNS-01**: Wait 5-10 minutes for propagation
- **Use staging first**: Set `ACME_STAGING=true` for testing

#### **Port conflicts**
- **Docker**: Use `-p 5001:8080` (host:container)
- **Local**: Change port in `app.py` or use `PORT` environment variable

### Health Check
Test your deployment:
```bash
curl https://your-app-url/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "version": "1.0.0"
}
```

## 📊 Monitoring

### Logs
- **Vercel**: Check deployment logs in dashboard
- **Docker**: `docker logs ssl-generator`
- **Systemd**: `journalctl -u ssl-generator`

### Metrics
- Health endpoint: `/health`
- Rate limiting: Built-in protection
- Error tracking: Comprehensive logging

## 🔒 Security

### Production Checklist
- [ ] Set `ACME_STAGING=false` for real certificates
- [ ] Use HTTPS (automatic on Vercel)
- [ ] Set appropriate rate limits
- [ ] Monitor logs for abuse
- [ ] Keep dependencies updated

### Rate Limiting
Default limits (configurable):
- 200 requests per day
- 50 requests per hour
- 5 requests per minute per IP

## 🆘 Support

If you encounter issues:

1. **Check this troubleshooting guide**
2. **Review platform-specific logs**
3. **Open a GitHub issue** with:
   - Deployment platform
   - Error logs
   - Steps to reproduce

---

**Need help?** Check the main [README.md](README.md) for more details.