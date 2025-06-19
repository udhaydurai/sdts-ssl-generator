#!/usr/bin/env python3
"""
Real ACME Client for Let's Encrypt Integration
Implements proper ACME protocol for browser-trusted certificates
"""

import os
import time
import logging
import tempfile
import dns.resolver
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

# ACME protocol imports
from acme import challenges, client, crypto_util, errors, messages
from acme.client import ClientV2
import josepy as jose
from josepy.jwk import JWKRSA
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealACMEClient:
    """Production ACME client for Let's Encrypt certificates"""
    
    def __init__(self, staging=True):
        self.staging = staging
        self.directory_url = (
            'https://acme-staging-v02.api.letsencrypt.org/directory' if staging 
            else 'https://acme-v02.api.letsencrypt.org/directory'
        )
        self.account_key = None
        self.acme_client = None
        self.temp_dir = tempfile.mkdtemp(prefix='acme_')
        
    def generate_account_key(self):
        """Generate RSA account key for ACME"""
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        return JWKRSA(key=key)
    
    def create_acme_client(self, email):
        """Create and register ACME client with Let's Encrypt"""
        try:
            # Generate account key
            self.account_key = self.generate_account_key()
            
            # Create network client
            net = client.ClientNetwork(self.account_key, user_agent="SDTS-SSL-Generator/1.0")
            
            # Get directory and create ACME client
            directory = messages.Directory.from_json(net.get(self.directory_url).json())
            self.acme_client = ClientV2(directory, net=net)
            
            # Register account
            regr = messages.NewRegistration.from_data(
                email=email,
                terms_of_service_agreed=True
            )
            
            account = self.acme_client.new_account(regr)
            logger.info(f"ACME account registered successfully for {email}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create ACME client: {str(e)}")
            return False
    
    def generate_certificate_with_challenges(self, domains, email, validation_method='dns'):
        """
        Start certificate generation process and return validation challenges
        """
        try:
            # Create ACME client
            if not self.create_acme_client(email):
                raise Exception("Failed to create ACME client")
            
            # Generate domain private key
            domain_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # Create Certificate Signing Request (CSR)
            # Serialize private key for CSR generation
            domain_key_pem = domain_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            csr_pem = crypto_util.make_csr(
                domain_key_pem, 
                domains,
                must_staple=False
            )
            
            # Create new order
            order = self.acme_client.new_order(csr_pem)
            
            # Process challenges for each domain
            challenges_data = []
            # Process challenges for each authorization
            for auth in order.authorizations:
                domain = auth.body.identifier.value
                
                if validation_method == 'dns':
                    challenge = self._get_dns_challenge(auth)
                    if challenge:
                        validation_data = self._prepare_dns_challenge(challenge, domain)
                        challenges_data.append(validation_data)
                elif validation_method == 'http':
                    challenge = self._get_http_challenge(auth)
                    if challenge:
                        validation_data = self._prepare_http_challenge(challenge, domain)
                        challenges_data.append(validation_data)
                else:
                    raise Exception(f"Unsupported validation method: {validation_method}")
            
            if not challenges_data:
                raise Exception("No challenges could be prepared")
            
            # Store order data for completion
            request_id = str(int(time.time()))
            
            # Serialize the private key to PEM format for storage
            domain_key_pem = domain_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            # Store simplified order data (order object itself is not serializable)
            order_data = {
                'order_uri': order.uri,  # Store order URI instead of full object
                'domain_key_pem': domain_key_pem,
                'challenges': challenges_data,
                'domains': domains,
                'email': email,
                'validation_method': validation_method,
                'created': datetime.now()
            }
            
            # Save order data to temp file
            import pickle
            order_file = os.path.join(self.temp_dir, f"order_{request_id}.pkl")
            with open(order_file, 'wb') as f:
                pickle.dump(order_data, f)
            
            return {
                'request_id': request_id,
                'challenges': challenges_data,
                'validation_method': validation_method,
                'staging': self.staging
            }
            
        except Exception as e:
            logger.error(f"Challenge generation failed: {str(e)}")
            raise
    
    def _get_dns_challenge(self, authorization):
        """Extract DNS-01 challenge from authorization"""
        for challenge in authorization.body.challenges:
            if isinstance(challenge.chall, challenges.DNS01):
                return challenge
        return None
    
    def _get_http_challenge(self, authorization):
        """Extract HTTP-01 challenge from authorization"""
        for challenge in authorization.body.challenges:
            if isinstance(challenge.chall, challenges.HTTP01):
                return challenge
        return None
    
    def _prepare_dns_challenge(self, challenge, domain):
        """Prepare DNS-01 challenge data"""
        validation_content = challenge.validation(self.account_key)
        record_name = f"_acme-challenge.{domain}"
        
        return {
            'domain': domain,
            'type': 'dns',
            'record_name': record_name,
            'record_value': validation_content,
            'challenge': challenge,
            'instructions': f"Create DNS TXT record: {record_name} = {validation_content}"
        }
    
    def _prepare_http_challenge(self, challenge, domain):
        """Prepare HTTP-01 challenge data"""
        validation_content = challenge.validation(self.account_key)
        file_path = f"/.well-known/acme-challenge/{challenge.chall.token}"
        
        return {
            'domain': domain,
            'type': 'http',
            'file_path': file_path,
            'file_content': validation_content,
            'challenge': challenge,
            'instructions': f"Place file at http://{domain}{file_path} with content: {validation_content}"
        }
    
    def verify_challenges(self, request_id):
        """Verify that domain validation challenges have been completed"""
        try:
            # Load order data
            import pickle
            order_file = os.path.join(self.temp_dir, f"order_{request_id}.pkl")
            
            if not os.path.exists(order_file):
                return False, [{'domain': 'unknown', 'verified': False, 'message': 'Order not found'}]
            
            with open(order_file, 'rb') as f:
                order_data = pickle.load(f)
            
            verification_results = []
            all_verified = True
            
            for challenge_data in order_data['challenges']:
                try:
                    domain = challenge_data['domain']
                    
                    if challenge_data['type'] == 'dns':
                        verified, message = self._verify_dns_challenge(challenge_data)
                    elif challenge_data['type'] == 'http':
                        verified, message = self._verify_http_challenge(challenge_data)
                    else:
                        verified, message = False, "Unknown challenge type"
                    
                    verification_results.append({
                        'domain': domain,
                        'verified': verified,
                        'message': message,
                        'challenge_info': challenge_data
                    })
                    
                    if not verified:
                        all_verified = False
                        
                except Exception as e:
                    logger.error(f"Challenge verification error for {challenge_data.get('domain', 'unknown')}: {str(e)}")
                    verification_results.append({
                        'domain': challenge_data.get('domain', 'unknown'),
                        'verified': False,
                        'message': f"Verification error: {str(e)}",
                        'challenge_info': challenge_data
                    })
                    all_verified = False
            
            return all_verified, verification_results
            
        except Exception as e:
            logger.error(f"Challenge verification error: {str(e)}")
            return False, [{'domain': 'error', 'verified': False, 'message': f'Verification failed: {str(e)}'}]
    
    def _verify_dns_challenge(self, challenge_data):
        """Verify DNS-01 challenge"""
        try:
            record_name = challenge_data.get('record_name', '')
            expected_value = challenge_data.get('record_value', '')
            
            if not record_name or not expected_value:
                return False, "Missing DNS challenge data"
            
            # Query multiple DNS servers for better reliability
            dns_servers = ['8.8.8.8', '1.1.1.1', '9.9.9.9']
            
            for dns_server in dns_servers:
                try:
                    resolver = dns.resolver.Resolver()
                    resolver.nameservers = [dns_server]
                    resolver.timeout = 10
                    
                    answers = resolver.resolve(record_name, 'TXT')
                    
                    for rdata in answers:
                        txt_value = rdata.to_text().strip('"')
                        if txt_value == expected_value:
                            return True, f"DNS record verified successfully on {dns_server}"
                    
                except dns.resolver.NXDOMAIN:
                    continue
                except Exception as e:
                    logger.warning(f"DNS query failed on {dns_server}: {str(e)}")
                    continue
            
            return False, f"DNS TXT record not found or not propagated yet. Required DNS record: Name: {record_name}, Type: TXT, Value: {expected_value}"
            
        except Exception as e:
            logger.error(f"DNS verification error: {str(e)}")
            return False, f"DNS verification error: {str(e)}"
    
    def _verify_http_challenge(self, challenge_data):
        """Verify HTTP-01 challenge"""
        try:
            domain = challenge_data.get('domain', '')
            file_path = challenge_data.get('file_path', '')
            expected_content = challenge_data.get('file_content', '')
            
            if not domain or not file_path or not expected_content:
                return False, "Missing HTTP challenge data"
            
            url = f"http://{domain}{file_path}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                if response.text.strip() == expected_content:
                    return True, "HTTP challenge verified successfully"
                else:
                    return False, f"HTTP file content mismatch. Expected: {expected_content}"
            else:
                return False, f"HTTP challenge file not accessible (status: {response.status_code})"
                
        except Exception as e:
            logger.error(f"HTTP verification error: {str(e)}")
            return False, f"HTTP verification error: {str(e)}"
    
    def complete_certificate_generation(self, request_id):
        """Complete certificate generation after domain validation"""
        try:
            # Load order data
            import pickle
            order_file = os.path.join(self.temp_dir, f"order_{request_id}.pkl")
            
            with open(order_file, 'rb') as f:
                order_data = pickle.load(f)
            
            # Restore ACME client state
            if not self.create_acme_client(order_data['email']):
                raise Exception("Failed to restore ACME client")
            
            # Re-create order (simplified for demo - in production you'd poll the existing order)
            # For now, create a new CSR and order since stored order URI may not be accessible
            domains = order_data['domains']
            
            # Recreate CSR
            domain_key_pem = order_data['domain_key_pem']
            csr_pem = crypto_util.make_csr(
                domain_key_pem, 
                domains,
                must_staple=False
            )
            
            # Create new order
            order = self.acme_client.new_order(csr_pem)
            
            # Deserialize the private key from PEM format
            domain_key = serialization.load_pem_private_key(
                order_data['domain_key_pem'],
                password=None,
            )
            
            challenges_data = order_data['challenges']
            
            # Answer challenges by submitting response
            challenge_responses = []
            for challenge_data in challenges_data:
                try:
                    challenge = challenge_data['challenge']
                    response = challenge.response(self.account_key)
                    self.acme_client.answer_challenge(challenge, response)
                    challenge_responses.append((challenge, response))
                except Exception as e:
                    logger.error(f"Error submitting challenge response: {str(e)}")
                    raise Exception(f"Failed to submit challenge: {str(e)}")
            
            # Wait for challenge verification
            logger.info("Waiting for Let's Encrypt to verify challenges...")
            time.sleep(5)  # Give Let's Encrypt time to verify
            
            # Poll for order completion
            order = self.acme_client.poll_and_finalize(order)
            
            # Get certificate
            fullchain_pem = order.fullchain_pem
            
            # Write certificate files
            primary_domain = order_data['domains'][0]
            cert_files = self._write_certificate_files(domain_key, fullchain_pem, primary_domain)
            
            # Cleanup order file
            os.remove(order_file)
            
            logger.info(f"Real Let's Encrypt certificate generated for domains: {order_data['domains']}")
            return cert_files
            
        except Exception as e:
            logger.error(f"Certificate completion failed: {str(e)}")
            raise
    
    def _write_certificate_files(self, domain_key, fullchain_pem, primary_domain):
        """Write certificate files in GoDaddy-compatible format"""
        try:
            # Parse the fullchain to separate cert and chain
            certs = fullchain_pem.split('-----END CERTIFICATE-----\n')
            cert_pem = certs[0] + '-----END CERTIFICATE-----\n'
            
            # Handle CA bundle (intermediate + root certificates)
            ca_bundle_pem = ""
            if len(certs) > 1:
                for i in range(1, len(certs)):
                    if certs[i].strip():
                        ca_bundle_pem += certs[i] + '-----END CERTIFICATE-----\n'
            
            # Serialize private key
            private_key_pem = domain_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')
            
            # Create certificate files in temp directory
            cert_dir = os.path.join(self.temp_dir, 'certificates')
            os.makedirs(cert_dir, exist_ok=True)
            
            # Write files in GoDaddy format
            private_key_path = os.path.join(cert_dir, f'{primary_domain}.key')
            cert_path = os.path.join(cert_dir, f'{primary_domain}.crt')
            ca_cert_path = os.path.join(cert_dir, f'{primary_domain}-ca.crt')
            
            with open(private_key_path, 'w') as f:
                f.write(private_key_pem)
            
            with open(cert_path, 'w') as f:
                f.write(cert_pem)
            
            with open(ca_cert_path, 'w') as f:
                f.write(ca_bundle_pem)
            
            return {
                'private_key': private_key_path,
                'certificate': cert_path,
                'ca_bundle': ca_cert_path
            }
            
        except Exception as e:
            logger.error(f"Error writing certificate files: {str(e)}")
            raise
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")