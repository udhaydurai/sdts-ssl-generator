from flask import Blueprint, render_template, request, jsonify, send_file, flash, redirect, url_for, session, current_app
from flask_limiter.util import get_remote_address
import logging
import time
from datetime import datetime, timedelta
import os

from services import SSLServiceFactory
from validators import DomainValidator

# Create blueprint
main_bp = Blueprint('main', __name__)

# Store for temporary file downloads with expiration
temp_files = {}

# Store for ACME validation challenges
acme_challenges = {}

logger = logging.getLogger(__name__)

@main_bp.route('/')
def index():
    """Main index page"""
    return render_template('index.html')

@main_bp.route('/generate_ssl', methods=['POST'])
def generate_ssl():
    """Generate SSL certificate endpoint"""
    try:
        # Get form data
        domains = request.form.get('domains', '').strip()
        email = request.form.get('email', '').strip()
        validation_method = request.form.get('validation_method', 'dns')
        accept_agreement = request.form.get('accept_agreement') == 'on'
        cert_type = request.form.get('cert_type', 'demo')
        
        # Validate agreement
        if not accept_agreement:
            flash('You must accept the Let\'s Encrypt Subscriber Agreement.', 'error')
            return redirect(url_for('main.index'))
        
        # Validate domains
        is_valid, domain_list, domain_error = DomainValidator.validate_domains(domains)
        if not is_valid:
            flash(f'Domain validation failed: {domain_error}', 'error')
            return redirect(url_for('main.index'))
        
        # Validate email
        is_valid, email_error = DomainValidator.validate_email(email)
        if not is_valid:
            flash(f'Email validation failed: {email_error}', 'error')
            return redirect(url_for('main.index'))
        
        # Validate validation method
        is_valid, method_error = DomainValidator.validate_validation_method(validation_method)
        if not is_valid:
            flash(f'Validation method error: {method_error}', 'error')
            return redirect(url_for('main.index'))
        
        # Create SSL service
        staging = current_app.config.get('ACME_STAGING', True)
        ssl_service = SSLServiceFactory.create_service(cert_type, staging)
        
        try:
            # Generate certificate
            result = ssl_service.generate_certificate(
                domains=domain_list,
                email=email,
                validation_method=validation_method
            )
            
            if not result['success']:
                flash(f'Certificate generation failed: {result.get("error", "Unknown error")}', 'error')
                return redirect(url_for('main.index'))
            
            # Handle different certificate types
            if cert_type == 'real':
                # Store challenge information for later verification
                request_id = result['challenge_data']['request_id']
                acme_challenges[request_id] = {
                    'service': ssl_service,
                    'challenges': result['challenge_data']['challenges'],
                    'validation_method': validation_method,
                    'expires': result['expires']
                }
                
                return render_template('validation.html',
                                     request_id=request_id,
                                     challenges=result['challenge_data']['challenges'],
                                     validation_method=validation_method,
                                     domains=domain_list)
            else:
                # Demo certificate - store files for download
                file_id = str(int(time.time()))
                temp_files[file_id] = {
                    'files': result['files'],
                    'expires': result['expires'],
                    'domain': domain_list[0]
                }
                
                # Read certificate contents for display
                cert_contents = _read_certificate_contents(result['files'])
                
                flash('Demo SSL certificate generated successfully! Download links will expire in 15 minutes.', 'success')
                return render_template('index.html', 
                                     success=True, 
                                     file_id=file_id,
                                     domain=domain_list[0],
                                     cert_contents=cert_contents,
                                     cert_type='demo')
                
        finally:
            # Cleanup service resources
            ssl_service.cleanup()
            
    except Exception as e:
        logger.error(f"SSL generation error: {str(e)}")
        flash('An unexpected error occurred. Please try again.', 'error')
        return redirect(url_for('main.index'))

@main_bp.route('/verify_challenges/<request_id>', methods=['POST'])
def verify_challenges(request_id):
    """Verify domain validation challenges and generate real certificate"""
    try:
        if request_id not in acme_challenges:
            flash('Invalid or expired validation request.', 'error')
            return redirect(url_for('main.index'))
        
        challenge_info = acme_challenges[request_id]
        ssl_service = challenge_info['service']
        
        # Verify challenges
        result = ssl_service.verify_challenges(request_id)
        
        if not result['success']:
            # Show detailed validation results with specific errors
            return render_template('validation_results.html', 
                                 success=False,
                                 verification_results=result.get('verification_results', {}),
                                 request_id=request_id,
                                 challenge_info=challenge_info)
        
        # Store files for download
        file_id = str(int(time.time()))
        temp_files[file_id] = {
            'files': result['files'],
            'expires': result['expires'],
            'domain': challenge_info['challenges'][0]['domain']
        }
        
        # Read certificate contents for display
        cert_contents = _read_certificate_contents(result['files'])
        
        # Clean up challenge info
        del acme_challenges[request_id]
        
        flash('Real SSL certificate generated successfully! Download links will expire in 15 minutes.', 'success')
        return render_template('index.html', 
                             success=True, 
                             file_id=file_id,
                             domain=challenge_info['challenges'][0]['domain'],
                             cert_contents=cert_contents,
                             cert_type='real')
        
    except Exception as e:
        logger.error(f"Challenge verification error: {str(e)}")
        flash('An unexpected error occurred during verification. Please try again.', 'error')
        return redirect(url_for('main.index'))

@main_bp.route('/download/<file_id>/<file_type>')
def download_file(file_id, file_type):
    """Download certificate files"""
    try:
        # Clean up expired files
        cleanup_expired_files()
        
        if file_id not in temp_files:
            flash('File not found or expired.', 'error')
            return redirect(url_for('main.index'))
        
        file_info = temp_files[file_id]
        
        # Check if file exists
        if file_type not in file_info['files']:
            flash('Invalid file type requested.', 'error')
            return redirect(url_for('main.index'))
        
        file_path = file_info['files'][file_type]
        
        if not os.path.exists(file_path):
            flash('File not found on server.', 'error')
            return redirect(url_for('main.index'))
        
        # Generate filename
        domain = file_info['domain']
        if file_type == 'private_key':
            filename = f'{domain}.key'
        elif file_type == 'certificate':
            filename = f'{domain}.crt'
        elif file_type == 'ca_bundle':
            filename = f'{domain}-ca.crt'
        else:
            filename = f'{domain}-{file_type}'
        
        return send_file(file_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        flash('Download failed. Please try again.', 'error')
        return redirect(url_for('main.index'))

@main_bp.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

def _read_certificate_contents(files):
    """Read certificate file contents for display"""
    try:
        cert_contents = {}
        for file_type, file_path in files.items():
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    cert_contents[file_type] = f.read()
        return cert_contents
    except Exception as e:
        logger.error(f"Error reading certificate contents: {str(e)}")
        return None

def cleanup_expired_files():
    """Clean up expired temporary files"""
    current_time = datetime.now()
    
    # Clean up expired file downloads
    expired_files = []
    for file_id, file_info in temp_files.items():
        if current_time > file_info['expires']:
            expired_files.append(file_id)
    
    for file_id in expired_files:
        cleanup_file(file_id)
    
    # Clean up expired challenges
    expired_challenges = []
    for request_id, challenge_info in acme_challenges.items():
        if current_time > challenge_info['expires']:
            expired_challenges.append(request_id)
    
    for request_id in expired_challenges:
        del acme_challenges[request_id]

def cleanup_file(file_id):
    """Clean up a specific file"""
    try:
        if file_id in temp_files:
            file_info = temp_files[file_id]
            
            # Remove files from disk
            for file_path in file_info['files'].values():
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # Remove from memory
            del temp_files[file_id]
            
    except Exception as e:
        logger.error(f"File cleanup error: {str(e)}")

@main_bp.errorhandler(404)
def not_found(error):
    return render_template('index.html'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    flash('An internal error occurred. Please try again.', 'error')
    return render_template('index.html'), 500
