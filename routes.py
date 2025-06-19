import os
import logging
import validators
from flask import render_template, request, jsonify, send_file, flash, redirect, url_for, session
from app import app
from ssl_generator import SSLGenerator
from real_acme_client import RealACMEClient
import tempfile
import time
from datetime import datetime, timedelta

# Store for temporary file downloads with expiration
temp_files = {}

# Store for ACME validation challenges
acme_challenges = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_ssl', methods=['POST'])
def generate_ssl():
    try:
        # Get form data
        domains = request.form.get('domains', '').strip()
        email = request.form.get('email', '').strip()
        validation_method = request.form.get('validation_method', 'http')
        accept_agreement = request.form.get('accept_agreement') == 'on'
        cert_type = request.form.get('cert_type', 'demo')  # demo or real
        
        # Validate inputs
        if not domains:
            flash('Domain name(s) are required.', 'error')
            return redirect(url_for('index'))
            
        if not email:
            flash('Email address is required.', 'error')
            return redirect(url_for('index'))
            
        if not validators.email(email):
            flash('Please enter a valid email address.', 'error')
            return redirect(url_for('index'))
            
        if not accept_agreement:
            flash('You must accept the Let\'s Encrypt Subscriber Agreement.', 'error')
            return redirect(url_for('index'))
        
        # Parse domains
        domain_list = [d.strip() for d in domains.split(',') if d.strip()]
        if not domain_list:
            flash('Please enter at least one valid domain.', 'error')
            return redirect(url_for('index'))
            
        # Validate domain format
        for domain in domain_list:
            if not is_valid_domain(domain):
                flash(f'Invalid domain format: {domain}', 'error')
                return redirect(url_for('index'))
        
        # Generate SSL certificate based on type
        if cert_type == 'real':
            # Real ACME certificate with domain validation
            acme_client = RealACMEClient(staging=True)  # Use staging for testing
            try:
                challenge_result = acme_client.generate_certificate_with_challenges(
                    domains=domain_list,
                    email=email,
                    validation_method=validation_method
                )
                
                # Store challenge information for later verification
                request_id = challenge_result['request_id']
                acme_challenges[request_id] = {
                    'client': acme_client,
                    'challenges': challenge_result['challenges'],
                    'validation_method': validation_method,
                    'expires': datetime.now() + timedelta(hours=1)
                }
                
                return render_template('validation.html',
                                     request_id=request_id,
                                     challenges=challenge_result['challenges'],
                                     validation_method=validation_method,
                                     domains=domain_list)
                
            except Exception as e:
                logging.error(f"Real ACME generation error: {str(e)}")
                flash(f'Real SSL generation failed: {str(e)}', 'error')
                return redirect(url_for('index'))
        else:
            # Demo certificate generation
            ssl_generator = SSLGenerator()
            try:
                cert_files = ssl_generator.generate_certificate(
                    domains=domain_list,
                    email=email,
                    validation_method=validation_method
                )
            
                if cert_files:
                    # Store file paths with expiration time (15 minutes)
                    expiration_time = datetime.now() + timedelta(minutes=15)
                    file_id = str(int(time.time()))
                    temp_files[file_id] = {
                        'files': cert_files,
                        'expires': expiration_time,
                        'domain': domain_list[0]  # Primary domain for file naming
                    }
                    
                    # Read certificate contents for display
                    cert_contents = {}
                    try:
                        with open(cert_files['private_key'], 'r') as f:
                            cert_contents['private_key'] = f.read()
                        with open(cert_files['certificate'], 'r') as f:
                            cert_contents['certificate'] = f.read()
                        with open(cert_files['ca_bundle'], 'r') as f:
                            cert_contents['ca_bundle'] = f.read()
                    except Exception as e:
                        logging.error(f"Error reading certificate contents: {str(e)}")
                        cert_contents = None

                    flash('Demo SSL certificate generated successfully! Download links will expire in 15 minutes.', 'success')
                    return render_template('index.html', 
                                         success=True, 
                                         file_id=file_id,
                                         domain=domain_list[0],
                                         cert_contents=cert_contents,
                                         cert_type='demo')
                else:
                    flash('Failed to generate SSL certificate. Please check your domain configuration.', 'error')
                    return redirect(url_for('index'))
                    
            except Exception as e:
                logging.error(f"Demo SSL generation error: {str(e)}")
                flash(f'Demo SSL generation failed: {str(e)}', 'error')
                return redirect(url_for('index'))
            
    except Exception as e:
        logging.error(f"Route error: {str(e)}")
        flash('An unexpected error occurred. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/verify_challenges/<request_id>', methods=['POST'])
def verify_challenges(request_id):
    """Verify domain validation challenges and generate real certificate"""
    try:
        if request_id not in acme_challenges:
            flash('Invalid or expired validation request.', 'error')
            return redirect(url_for('index'))
        
        challenge_info = acme_challenges[request_id]
        acme_client = challenge_info['client']
        
        # Verify challenges
        verified, verification_results = acme_client.verify_challenges(request_id)
        
        if not verified:
            # Show detailed validation results with specific errors
            return render_template('validation_results.html', 
                                 success=False,
                                 verification_results=verification_results,
                                 request_id=request_id,
                                 challenge_info=challenge_info)
        
        if verified:
            # Complete real certificate generation
            try:
                cert_files = acme_client.complete_certificate_generation(request_id)
                
                # Store file paths with expiration time (15 minutes)
                expiration_time = datetime.now() + timedelta(minutes=15)
                file_id = str(int(time.time()))
                temp_files[file_id] = {
                    'files': cert_files,
                    'expires': expiration_time,
                    'domain': challenge_info['challenges'][0]['domain']
                }
                
                # Read certificate contents for display
                cert_contents = {}
                try:
                    with open(cert_files['private_key'], 'r') as f:
                        cert_contents['private_key'] = f.read()
                    with open(cert_files['certificate'], 'r') as f:
                        cert_contents['certificate'] = f.read()
                    with open(cert_files['ca_bundle'], 'r') as f:
                        cert_contents['ca_bundle'] = f.read()
                except Exception as e:
                    logging.error(f"Error reading certificate contents: {str(e)}")
                    cert_contents = None
                
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
                logging.error(f"Real certificate generation error: {str(e)}")
                flash(f'Certificate generation failed: {str(e)}', 'error')
                return render_template('validation.html',
                                     request_id=request_id,
                                     challenges=challenge_info['challenges'],
                                     validation_method=challenge_info['validation_method'],
                                     verification_failed=True,
                                     verification_results=verification_results)
        else:
            # Show validation errors
            return render_template('validation.html',
                                 request_id=request_id,
                                 challenges=challenge_info['challenges'],
                                 validation_method=challenge_info['validation_method'],
                                 verification_failed=True,
                                 verification_results=verification_results)
                                 
    except Exception as e:
        logging.error(f"Challenge verification error: {str(e)}")
        flash('Challenge verification failed. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/download/<file_id>/<file_type>')
def download_file(file_id, file_type):
    # Clean up expired files
    cleanup_expired_files()
    
    if file_id not in temp_files:
        flash('Download link has expired or is invalid.', 'error')
        return redirect(url_for('index'))
    
    file_info = temp_files[file_id]
    if datetime.now() > file_info['expires']:
        # Clean up expired file
        cleanup_file(file_id)
        flash('Download link has expired.', 'error')
        return redirect(url_for('index'))
    
    domain = file_info['domain']
    cert_files = file_info['files']
    
    try:
        if file_type == 'key':
            return send_file(cert_files['private_key'], 
                           as_attachment=True, 
                           download_name=f'{domain}.key',
                           mimetype='application/x-pem-file')
        elif file_type == 'crt':
            return send_file(cert_files['certificate'], 
                           as_attachment=True, 
                           download_name=f'{domain}.crt',
                           mimetype='application/x-pem-file')
        elif file_type == 'ca':
            return send_file(cert_files['ca_bundle'], 
                           as_attachment=True, 
                           download_name=f'{domain}-ca.crt',
                           mimetype='application/x-pem-file')
        else:
            flash('Invalid file type requested.', 'error')
            return redirect(url_for('index'))
            
    except Exception as e:
        logging.error(f"Download error: {str(e)}")
        flash('Error downloading file.', 'error')
        return redirect(url_for('index'))

def is_valid_domain(domain):
    """Validate domain format"""
    if not domain or len(domain) > 253:
        return False
    
    # Remove protocol if present
    if domain.startswith(('http://', 'https://')):
        return False
    
    # Basic domain validation
    import re
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
    return re.match(pattern, domain) is not None

def cleanup_expired_files():
    """Clean up expired temporary files"""
    current_time = datetime.now()
    expired_ids = [file_id for file_id, info in temp_files.items() 
                   if current_time > info['expires']]
    
    for file_id in expired_ids:
        cleanup_file(file_id)

def cleanup_file(file_id):
    """Clean up a specific temporary file"""
    if file_id in temp_files:
        file_info = temp_files[file_id]
        try:
            # Remove physical files
            for file_path in file_info['files'].values():
                if os.path.exists(file_path):
                    os.remove(file_path)
        except Exception as e:
            logging.error(f"Error cleaning up files: {str(e)}")
        
        # Remove from memory
        del temp_files[file_id]

@app.errorhandler(404)
def not_found(error):
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    flash('An internal error occurred. Please try again.', 'error')
    return render_template('index.html'), 500
