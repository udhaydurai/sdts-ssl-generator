from flask import Blueprint, render_template, request, jsonify, send_file, flash, redirect, url_for, session, current_app
from flask_limiter.util import get_remote_address
import logging
import time
from datetime import datetime, timedelta
import os
from io import BytesIO
import pickle

from services import SSLServiceFactory
from validators import DomainValidator

# Create blueprint
main_bp = Blueprint('main', __name__)

# Set up logger
logger = logging.getLogger(__name__)

# --- Persistent Session Cache using Pickle ---
SESSION_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.session_cache.pkl')

def load_sessions():
    """Loads active sessions from a pickle file."""
    if os.path.exists(SESSION_CACHE_FILE):
        try:
            with open(SESSION_CACHE_FILE, 'rb') as f:
                acme_challenges = pickle.load(f)
            # Filter out expired sessions
            current_time = datetime.now()
            return {
                k: v for k, v in acme_challenges.items() 
                if v.get('expires', current_time + timedelta(days=1)) > current_time
            }
        except (pickle.UnpicklingError, EOFError, TypeError) as e:
            logger.error(f"Could not load session cache: {e}. Starting fresh.")
            return {}
    return {}

def save_sessions(acme_challenges):
    """Saves active sessions to a pickle file."""
    with open(SESSION_CACHE_FILE, 'wb') as f:
        pickle.dump(acme_challenges, f)

# Load sessions at startup
acme_challenges = load_sessions()
save_sessions(acme_challenges) # Save back to prune expired sessions
# --- End of Cache ---

# Store for temporary file downloads with expiration
temp_files = {}

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
        validation_method = request.form.get('validation_method', 'http')
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
                
                # Prepare challenges with verification URLs for the template
                challenges_for_template = []
                for ch in result['challenge_data']['challenges']:
                    if validation_method == 'http':
                        ch['verification_url'] = f"http://{ch['domain']}{ch['file_path']}"
                    challenges_for_template.append(ch)
                
                # Export the state to a serializable dictionary
                client_state = ssl_service.acme_client.export_state()

                # Store the serializable state, not the service object
                acme_challenges[request_id] = {
                    'client_state': client_state,
                    'challenges': result['challenge_data']['challenges'],
                    'validation_method': validation_method,
                    'expires': result['expires'],
                    'domains': domain_list,
                    'cert_type': 'real',
                    'staging': staging,
                }
                save_sessions(acme_challenges)
                
                return render_template('validation.html',
                                     request_id=request_id,
                                     challenges=challenges_for_template,
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
        logger.error(f"SSL generation error: {str(e)}", exc_info=True)
        flash(f'An unexpected error occurred: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@main_bp.route('/verify_challenges/<request_id>', methods=['GET', 'POST'])
def verify_challenges(request_id):
    """Verify domain validation challenges and generate real certificate"""
    try:
        if request_id not in acme_challenges:
            flash('Invalid or expired validation request. Please start over.', 'error')
            return redirect(url_for('main.index'))
        
        challenge_session = acme_challenges[request_id]
        
        # Rehydrate the ACME client from the stored state
        from real_acme_client import RealACMEClient
        rehydrated_client = RealACMEClient.from_state(challenge_session['client_state'])
        
        # Create a new service wrapper and attach the rehydrated client
        ssl_service = SSLServiceFactory.create_service(
            challenge_session.get('cert_type', 'real'), 
            challenge_session.get('staging', True)
        )
        ssl_service.acme_client = rehydrated_client
        
        result = ssl_service.verify_challenges(challenge_session['challenges'])
        
        if not result['success']:
            # A domain failed. Let the user retry.
            # The session is preserved.
            return render_template('validation_results.html', 
                                 success=False,
                                 verification_results=result.get('verification_results', []),
                                 request_id=request_id,
                                 challenge_info=challenge_session)
        
        # Success case: Store files for download
        file_id = str(int(time.time()))
        temp_files[file_id] = {
            'files': result['files'],
            'expires': result['expires'],
            'domain': challenge_session['domains'][0]
        }
        
        cert_contents = _read_certificate_contents(result['files'])
        
        # Clean up challenge info
        del acme_challenges[request_id]
        save_sessions(acme_challenges) # Save session to disk
        
        flash('Real SSL certificate generated successfully! Download links will expire in 15 minutes.', 'success')
        return render_template('index.html', 
                             success=True, 
                             file_id=file_id,
                             domain=challenge_session['domains'][0],
                             cert_contents=cert_contents,
                             cert_type='real')

    except Exception as e:
        logger.error(f"Challenge verification process failed: {str(e)}", exc_info=True)
        
        challenge_session = acme_challenges.get(request_id)
        
        # Create a detailed error message for display
        error_result = [{
            'domain': 'Verification Error',
            'verified': False,
            'message': f"An unexpected error occurred: {str(e)}"
        }]
        
        # Do not clean up the failed session, allowing the user to retry.
        # Render the results page with the specific error instead of redirecting
        return render_template('validation_results.html', 
                             success=False,
                             verification_results=error_result,
                             request_id=request_id,
                             challenge_info=challenge_session)

@main_bp.route('/download_challenge/<request_id>/<domain>')
def download_challenge(request_id, domain):
    """Serves the ACME challenge file for download."""
    if request_id not in acme_challenges:
        flash('Invalid or expired validation request.', 'error')
        return redirect(url_for('main.index'))

    challenge_session = acme_challenges[request_id]
    
    # Find the specific challenge for the requested domain
    challenge_data = next((c for c in challenge_session['challenges'] if c['domain'] == domain), None)

    if not challenge_data or 'file_content' not in challenge_data:
        flash(f'Challenge data not found for domain {domain}.', 'error')
        return redirect(url_for('main.index'))

    # Prepare file for download
    file_content = challenge_data['file_content']
    file_name = os.path.basename(challenge_data['file_path'])
    
    buffer = BytesIO()
    buffer.write(file_content.encode('utf-8'))
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=file_name,
        mimetype='text/plain'
    )

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
