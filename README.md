# SDTS SSL Generator

A Flask-based web application that generates SSL certificates in GoDaddy-compatible format with real Let's Encrypt integration. Designed specifically for nonprofit organizations to easily obtain free SSL certificates.

## 🚀 Quick Deploy Options

### **Option 1: Vercel (Recommended - Free & Easy)**
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/udhaydurai/sdts-ssl-generator)

1. Click the "Deploy with Vercel" button above
2. Connect your GitHub account
3. Click "Deploy" - that's it!

**✅ Perfect for:**
- Free hosting (generous limits)
- Automatic HTTPS
- Zero configuration
- Global CDN

### **Option 2: Docker (Local/Production)**
```bash
# Clone the repository
git clone https://github.com/udhaydurai/sdts-ssl-generator.git
cd sdts-ssl-generator

# Build and run with Docker
docker build -t sdts-ssl-generator .
docker run -p 5001:8080 sdts-ssl-generator

# Access at http://localhost:5001
```

### **Option 3: Local Development**
```bash
# Clone and setup
git clone https://github.com/udhaydurai/sdts-ssl-generator.git
cd sdts-ssl-generator

# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py

# Access at http://localhost:5001
```

## 🏗️ Architecture Overview

This application follows modern architectural patterns:

- **Application Factory Pattern**: Modular application creation with dependency injection
- **Service Layer Architecture**: Business logic separated from route handlers
- **Blueprint Pattern**: Modular route organization
- **Configuration Management**: Environment-based configuration with multiple profiles
- **Input Validation Layer**: Comprehensive validation with security checks
- **Rate Limiting**: Built-in protection against abuse
- **Multi-Platform Support**: Works on Vercel, Docker, and traditional hosting

## 🚀 Features

- **Real Let's Encrypt Certificates**: Generate browser-trusted SSL certificates using ACME protocol
- **Demo Certificates**: Create self-signed certificates for testing and development
- **GoDaddy Compatible Format**: Outputs .key, .crt, and -ca.crt files
- **DNS & HTTP Validation**: Support for both DNS-01 and HTTP-01 challenge types
- **Multi-DNS Verification**: Checks DNS propagation across multiple servers
- **Clean Web Interface**: Bootstrap-powered responsive design
- **Rate Limiting**: Protection against abuse and API limits
- **Comprehensive Validation**: Domain, email, and input validation
- **Health Check Endpoint**: Monitoring and deployment readiness
- **Serverless Ready**: Optimized for Vercel and other serverless platforms

## 🏛️ Project Structure

```
├── app.py                 # Application entry point
├── app_factory.py         # Application factory pattern
├── config.py              # Configuration management
├── routes.py              # Route handlers (Blueprint)
├── ssl_generator.py       # Demo certificate generator
├── real_acme_client.py    # Let's Encrypt ACME client
├── services/              # Service layer
│   ├── __init__.py
│   └── ssl_service.py     # SSL service implementation
├── validators/            # Validation layer
│   ├── __init__.py
│   └── domain_validator.py # Domain and email validation
├── templates/             # Jinja2 templates
├── static/                # Static assets (CSS, JS)
├── vercel.json           # Vercel deployment configuration
├── Dockerfile            # Docker configuration
└── requirements.txt      # Python dependencies
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_CONFIG` | `default` | Configuration profile (development/production) |
| `ACME_STAGING` | `true` | Use Let's Encrypt staging environment |
| `LOG_LEVEL` | `INFO` | Logging level |
| `UPLOAD_FOLDER` | `./temp_certs` | Temporary certificate storage |

### Let's Encrypt Settings

- **Staging Environment**: Default for testing (untrusted certificates)
- **Production Environment**: Set `ACME_STAGING=false` for trusted certificates
- **Rate Limits**: 5 requests per minute per IP (configurable)

## 🚀 Deployment Guides

### Vercel Deployment

1. **Fork this repository** to your GitHub account
2. **Go to [vercel.com](https://vercel.com)** and sign up/login
3. **Click "New Project"** → "Import Git Repository"
4. **Select your forked repository**
5. **Click "Deploy"** - Vercel will auto-detect the Python configuration

**✅ What's Included:**
- Automatic HTTPS
- Global CDN
- Zero configuration
- Automatic deployments on git push

### Docker Deployment

```bash
# Build the image
docker build -t sdts-ssl-generator .

# Run locally
docker run -p 5001:8080 sdts-ssl-generator

# Run in production (with environment variables)
docker run -d \
  -p 80:8080 \
  -e ACME_STAGING=false \
  -e LOG_LEVEL=INFO \
  --name ssl-generator \
  sdts-ssl-generator
```

### Traditional Hosting

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ACME_STAGING=false
export LOG_LEVEL=INFO

# Run with Gunicorn (production)
gunicorn app:app --bind 0.0.0.0:8080 --workers 2 --timeout 120

# Or run with Flask (development)
python app.py
```

## 🔍 Troubleshooting

### Common Issues & Solutions

#### **"Invalid or expired validation request" Error**
- **Cause**: Session data not persisting between requests
- **Solution**: ✅ **Fixed** - App now uses stateless session handling

#### **Vercel Deployment Fails**
- **Cause**: Read-only filesystem restrictions
- **Solution**: ✅ **Fixed** - App detects Vercel environment and uses in-memory storage

#### **Let's Encrypt Validation Fails**
- **HTTP-01 Challenge Issues**:
  - Ensure `/.well-known/acme-challenge/` directory exists
  - Check web server configuration (see templates for examples)
  - Verify no redirects are interfering with the path
- **DNS-01 Challenge Issues**:
  - Wait 5-10 minutes for DNS propagation
  - Use tools like [whatsmydns.net](https://whatsmydns.net) to check global propagation

#### **Certificate Generation Timeout**
- **Cause**: Let's Encrypt servers taking too long to respond
- **Solution**: The app includes retry logic and 90-second timeouts

### Server Configuration Examples

#### **Apache (.htaccess)**
```apache
RewriteEngine On
RewriteCond %{REQUEST_URI} ^/.well-known/acme-challenge/
RewriteRule ^(.*)$ $1 [L]

<Files "/.well-known/acme-challenge/*">
    ForceType text/plain
</Files>
```

#### **Nginx**
```nginx
location ^~ /.well-known/acme-challenge/ {
    default_type "text/plain";
    root /var/www/html;
}
```

#### **IIS (web.config)**
```xml
<configuration>
  <system.webServer>
    <staticContent>
      <mimeMap fileExtension="." mimeType="text/plain" />
    </staticContent>
    <handlers>
      <add name="AcmeChallenge" path=".well-known/acme-challenge/*" verb="GET" modules="StaticFileModule" resourceType="Either" />
    </handlers>
  </system.webServer>
</configuration>
```

## 🔒 Security Features

- **Input Validation**: Comprehensive domain and email validation
- **Rate Limiting**: Built-in protection against abuse
- **HTTPS Enforcement**: Automatic SSL certificate generation
- **Session Security**: Stateless session handling
- **Error Handling**: Secure error messages without information leakage

## 📊 Monitoring

### Health Check Endpoint
```bash
curl https://your-app.vercel.app/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "version": "1.0.0"
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Let's Encrypt**: For providing free SSL certificates
- **Flask**: For the excellent web framework
- **Bootstrap**: For the responsive UI components
- **Cryptography**: For the robust cryptographic operations

## 🆘 Support

If you encounter any issues:

1. **Check the troubleshooting section** above
2. **Review the deployment logs** in your hosting platform
3. **Open an issue** on GitHub with detailed error information
4. **Include your deployment platform** (Vercel, Docker, etc.) in the issue

---

**Made with ❤️ for nonprofit organizations and the open web.**