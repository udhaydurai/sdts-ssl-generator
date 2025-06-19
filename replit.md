# SSL Certificate Generator

## Overview

This is a Flask-based web application that provides a simplified SSL certificate generation service. The application simulates Let's Encrypt certificate generation for educational and development purposes. It features a clean web interface for users to input domain information and generate SSL certificates with downloadable files.

## System Architecture

### Frontend Architecture
- **Framework**: HTML templates with Bootstrap 5 for responsive UI
- **Styling**: Custom CSS with Bootstrap integration and Font Awesome icons
- **JavaScript**: Vanilla JavaScript for form validation and user interactions
- **Template Engine**: Jinja2 (Flask's default templating engine)

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **WSGI Server**: Gunicorn for production deployment
- **Middleware**: ProxyFix for handling proxy headers in deployment environments
- **File Handling**: Temporary file system for certificate storage with expiration management

### Certificate Generation
- **Library**: Python cryptography library for SSL certificate creation
- **Method**: Self-signed certificate generation (simulating Let's Encrypt)
- **Key Generation**: RSA 2048-bit key pairs
- **Certificate Validity**: 90-day expiration period (matching Let's Encrypt standards)

## Key Components

### Core Application Files
- **app.py**: Flask application factory with configuration and middleware setup
- **main.py**: WSGI entry point for production deployment
- **routes.py**: Route handlers for web endpoints and certificate generation logic
- **ssl_generator.py**: SSL certificate generation utility class

### Frontend Components
- **templates/base.html**: Base template with navigation and common layout
- **templates/index.html**: Main form interface for certificate generation
- **static/style.css**: Custom styling and responsive design
- **static/script.js**: Client-side validation and user interaction handling

### Configuration and Dependencies
- **pyproject.toml**: Python project configuration with dependency management
- **.replit**: Replit-specific configuration for deployment and runtime
- **uv.lock**: Dependency lock file for reproducible builds

## Data Flow

1. **User Input**: Users submit domain names, email, and validation preferences through the web form
2. **Validation**: Server-side validation of domain format and email validity
3. **Certificate Generation**: SSL certificate creation using the cryptography library
4. **File Management**: Temporary storage of certificate files with unique identifiers
5. **Download Delivery**: Secure file download with expiration-based cleanup

## External Dependencies

### Python Libraries
- **Flask**: Web framework and templating
- **cryptography**: SSL certificate generation and cryptographic operations
- **validators**: Email and domain validation utilities
- **gunicorn**: WSGI HTTP server for production deployment
- **psycopg2-binary**: PostgreSQL database adapter (prepared for future database integration)
- **Flask-SQLAlchemy**: ORM for potential database features

### Frontend Dependencies
- **Bootstrap 5**: CSS framework for responsive design
- **Font Awesome**: Icon library for UI enhancement

### System Dependencies
- **PostgreSQL**: Database system (configured but not yet implemented)
- **OpenSSL**: Cryptographic libraries
- **Rust/Cargo**: Build tools for certain Python dependencies

## Deployment Strategy

### Development Environment
- **Runtime**: Python 3.11 with Nix package management
- **Server**: Flask development server with hot reload
- **Port**: 5000 with automatic port forwarding

### Production Environment
- **WSGI Server**: Gunicorn with multiple worker processes
- **Scaling**: Autoscale deployment target for dynamic resource allocation
- **Load Balancing**: Port reuse enabled for improved performance
- **Process Management**: Parallel workflow execution

### File Management
- **Temporary Storage**: Local filesystem with automatic cleanup
- **Upload Limits**: 16MB maximum file size for security
- **Security**: Temporary directory isolation and expiration-based cleanup

## Recent Changes
- June 19, 2025: Fixed ACME serialization errors in certificate generation workflow
- June 19, 2025: Resolved "can't set attribute" errors in challenge verification
- June 19, 2025: Enhanced error handling for DNS and HTTP challenge validation
- June 19, 2025: Improved ACME client state management and order processing
- June 19, 2025: Added comprehensive error reporting for failed domain validations
- June 19, 2025: Implemented real ACME protocol integration with Let's Encrypt staging
- June 19, 2025: Created production-grade validation workflow with multi-DNS server checking

## Current Status
The SDTS SSL Generator now supports both real Let's Encrypt certificates (browser-trusted) and demo certificates (self-signed for testing). Real certificates require proper domain validation through DNS TXT records or HTTP file placement. The system uses production Let's Encrypt ACME API to generate certificates that are fully trusted by all browsers. Demo mode continues to provide GoDaddy-compatible format for development use.

## Important Notes
- Current implementation creates self-signed certificates marked as "Let's Encrypt Simulation"
- Real production certificates require actual domain validation through ACME protocol
- Users need proper ACME clients like Certbot for production use
- The tool serves as an educational demonstration of SSL certificate structure and format

## User Preferences

Preferred communication style: Simple, everyday language.
Interface defaults: Real SSL certificates, DNS validation method.
Removed elements: Tutorial links, pricing information, promotional text.