# SDTS SSL Generator

A Flask-based web application that generates SSL certificates in GoDaddy-compatible format with real Let's Encrypt integration. Designed specifically for nonprofit organizations to easily obtain free SSL certificates.

## 🏗️ Architecture Overview

This application follows modern architectural patterns:

- **Application Factory Pattern**: Modular application creation with dependency injection
- **Service Layer Architecture**: Business logic separated from route handlers
- **Blueprint Pattern**: Modular route organization
- **Configuration Management**: Environment-based configuration with multiple profiles
- **Input Validation Layer**: Comprehensive validation with security checks
- **Rate Limiting**: Built-in protection against abuse

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
│   └── ssl_service.py     # SSL service abstraction
├── validators/            # Input validation layer
│   ├── __init__.py
│   └── domain_validator.py # Domain and email validation
├── templates/             # HTML templates
├── static/                # CSS, JS, and assets
├── requirements-github.txt # Python dependencies
├── env.example            # Environment configuration example
└── README.md              # This file
```

## 🛠️ Quick Start

### Prerequisites

- Python 3.11+
- Domain with DNS management access (for real certificates)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/udhaydurai/sdts-ssl-generator.git
cd sdts-ssl-generator
```

2. Install dependencies:
```bash
pip install -r requirements-github.txt
```

3. Configure environment (optional):
```bash
cp env.example .env
# Edit .env with your settings
```

4. Run the application:
```bash
python app.py
```

5. Open your browser to `http://localhost:5000`

## 📋 Usage

### Demo Certificates

1. Select "Demo Certificate" option
2. Enter your domain names (comma-separated)
3. Provide an email address
4. Click "Generate SSL Certificate"
5. Download the generated files

### Real Let's Encrypt Certificates

1. Select "Real SSL Certificate" option
2. Enter your domain names that you control
3. Provide a valid email address
4. Choose DNS validation method (recommended)
5. Follow the DNS record setup instructions
6. Complete domain validation
7. Download your browser-trusted certificates

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_CONFIG` | Configuration profile (development/production/testing) | `default` |
| `SECRET_KEY` | Flask secret key | Auto-generated |
| `SESSION_SECRET` | Session secret key | Auto-generated |
| `ACME_STAGING` | Use Let's Encrypt staging environment | `true` |
| `RATE_LIMIT_ENABLED` | Enable rate limiting | `true` |
| `CERT_EXPIRY_MINUTES` | Certificate download expiry (minutes) | `15` |
| `CHALLENGE_EXPIRY_HOURS` | Challenge expiry (hours) | `1` |

### Configuration Profiles

- **Development**: Debug mode, staging certificates, detailed logging
- **Production**: Production certificates, optimized performance
- **Testing**: Test configuration for automated testing

## 🔒 Security Features

- **Input Validation**: Comprehensive domain and email validation
- **Rate Limiting**: Protection against abuse (200/day, 50/hour by default)
- **Secure File Handling**: Temporary files with automatic cleanup
- **Environment-based Configuration**: No hardcoded secrets
- **CSRF Protection**: Built-in CSRF protection
- **DNS Validation**: Proper domain ownership verification

## 🧪 Testing

The application includes health check endpoints for monitoring:

```bash
curl http://localhost:5000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "version": "1.0.0"
}
```

## 🚀 Deployment

### Production Deployment

1. Set environment variables:
```bash
export FLASK_CONFIG=production
export ACME_STAGING=false
export SECRET_KEY=your-secure-secret-key
```

2. Use Gunicorn for production:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

3. Set up reverse proxy (nginx/Apache) with HTTPS

### Docker Deployment

```bash
docker build -t ssl-generator .
docker run -p 5000:5000 ssl-generator
```

## 🔍 Monitoring & Logging

- **Structured Logging**: JSON-formatted logs with configurable levels
- **Health Checks**: Built-in health check endpoint
- **Error Tracking**: Comprehensive error handling and logging
- **Performance Monitoring**: Rate limiting and request tracking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Check the troubleshooting section in the web interface
- Review DNS propagation with [whatsmydns.net](https://whatsmydns.net)
- Ensure proper domain ownership for real certificates
- Check the health endpoint for system status

## 🙏 Acknowledgments

- Let's Encrypt for free SSL certificates
- Flask community for the excellent web framework
- Bootstrap team for the responsive UI components
- Nonprofit organizations for inspiring this project