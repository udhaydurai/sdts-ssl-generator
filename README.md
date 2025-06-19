# SDTS SSL Generator

A Flask-based web application that generates SSL certificates in GoDaddy-compatible format with real Let's Encrypt integration.

## Features

- **Real Let's Encrypt Certificates**: Generate browser-trusted SSL certificates using ACME protocol
- **Demo Certificates**: Create self-signed certificates for testing and development
- **GoDaddy Compatible Format**: Outputs .key, .crt, and -ca.crt files
- **DNS & HTTP Validation**: Support for both DNS-01 and HTTP-01 challenge types
- **Multi-DNS Verification**: Checks DNS propagation across multiple servers
- **Clean Web Interface**: Bootstrap-powered responsive design

## Quick Start

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

3. Run the application:
```bash
python main.py
```

4. Open your browser to `http://localhost:5000`

## Usage

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

## DNS Validation Setup

For real certificates, you'll need to add DNS TXT records:

**Standard Format:**
- Name: `_acme-challenge.yourdomain.com`
- Type: `TXT`
- Value: `[provided validation string]`

**GoDaddy Simplified Format:**
- Name: `_acme-challenge`
- Type: `TXT` 
- Value: `[provided validation string]`

## Project Structure

```
├── main.py              # WSGI entry point
├── app.py               # Flask application factory
├── routes.py            # Web routes and handlers
├── ssl_generator.py     # Demo certificate generator
├── real_acme_client.py  # Let's Encrypt ACME client
├── templates/           # HTML templates
├── static/              # CSS, JS, and assets
└── requirements.txt     # Python dependencies
```

## Technology Stack

- **Backend**: Flask, Python 3.11
- **ACME Client**: python-acme, certbot libraries
- **Cryptography**: Python cryptography library
- **Frontend**: Bootstrap 5, Font Awesome
- **DNS**: dnspython for validation
- **Deployment**: Gunicorn WSGI server

## Configuration

### Environment Variables

- `SESSION_SECRET`: Flask session secret key
- `DATABASE_URL`: PostgreSQL connection (optional)

### Development vs Production

The application defaults to Let's Encrypt staging environment for testing. For production certificates, modify the staging parameter in `routes.py`.

## Security Notes

- Demo certificates are self-signed and will show browser warnings
- Real certificates require proper domain ownership validation
- Private keys are temporarily stored and automatically cleaned up
- HTTPS deployment recommended for production use

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Check the troubleshooting section in the web interface
- Review DNS propagation with [whatsmydns.net](https://whatsmydns.net)
- Ensure proper domain ownership for real certificates

## Acknowledgments

- Let's Encrypt for free SSL certificates
- Flask community for the excellent web framework
- Bootstrap team for the responsive UI components