#!/usr/bin/env python3
"""
Real ACME Client for Let's Encrypt Integration
A from-scratch implementation to bypass library bugs and generate real certificates.
"""

import os
import time
import logging
import tempfile
import json
import base64
import hashlib
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.x509.oid import NameOID
import requests
from cryptography.hazmat.primitives.serialization import load_pem_private_key

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
LETSENCRYPT_STAGING_URL = "https://acme-staging-v02.api.letsencrypt.org"
LETSENCRYPT_PROD_URL = "https://acme-v02.api.letsencrypt.org"
KEY_SIZE = 2048

class RealACMEClient:
    def __init__(self, use_staging=True):
        self.base_url = LETSENCRYPT_STAGING_URL if use_staging else LETSENCRYPT_PROD_URL
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'SDTS-SSL-Generator/1.0'})
        
        self.account_key = rsa.generate_private_key(public_exponent=65537, key_size=KEY_SIZE)
        self.domain_key = rsa.generate_private_key(public_exponent=65537, key_size=KEY_SIZE)
        
        self.directory = None
        self.account_url = None
        self.nonce = None
        self.order_data = None
        self.order_url = None

    def export_state(self):
        """Exports the client's state to a serializable dictionary."""
        return {
            'account_key_pem': self.account_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8'),
            'domain_key_pem': self.domain_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8'),
            'account_url': self.account_url,
            'order_url': self.order_url,
            'order_data': self.order_data,
            'directory': self.directory,
            'nonce': self.nonce,
            'base_url': self.base_url
        }

    @classmethod
    def from_state(cls, state):
        """Creates a client instance from a saved state."""
        is_staging = (LETSENCRYPT_STAGING_URL in state['base_url'])
        client = cls(use_staging=is_staging)
        
        client.account_key = load_pem_private_key(state['account_key_pem'].encode('utf-8'), password=None)
        client.domain_key = load_pem_private_key(state['domain_key_pem'].encode('utf-8'), password=None)
        
        client.account_url = state['account_url']
        client.order_url = state['order_url']
        client.order_data = state['order_data']
        client.directory = state['directory']
        client.nonce = state['nonce']
        
        return client

    def _get_nonce(self):
        """Gets a new nonce from the ACME server."""
        try:
            response = self.session.head(self.directory['newNonce'], timeout=10)
            response.raise_for_status()
            self.nonce = response.headers['Replay-Nonce']
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get nonce: {e}")
            raise

    def _send_signed_request(self, url, payload):
        """Sends a JWS signed request to the ACME server."""
        if self.nonce is None:
            self._get_nonce()

        protected_header = {
            "alg": "RS256",
            "nonce": self.nonce,
            "url": url
        }
        
        public_numbers = self.account_key.public_key().public_numbers()
        jwk = {
            "kty": "RSA",
            "n": base64.urlsafe_b64encode(public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, 'big')).rstrip(b'=').decode('utf-8'),
            "e": base64.urlsafe_b64encode(public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, 'big')).rstrip(b'=').decode('utf-8'),
        }

        if self.account_url:
            protected_header["kid"] = self.account_url
        else:
            protected_header["jwk"] = jwk

        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode('utf-8')).rstrip(b'=')
        protected_b64 = base64.urlsafe_b64encode(json.dumps(protected_header).encode('utf-8')).rstrip(b'=')

        signature = self.account_key.sign(
            protected_b64 + b'.' + payload_b64,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b'=')

        jws_payload = {
            "protected": protected_b64.decode('utf-8'),
            "payload": payload_b64.decode('utf-8'),
            "signature": signature_b64.decode('utf-8')
        }
        
        response = self.session.post(url, data=json.dumps(jws_payload), headers={'Content-Type': 'application/jose+json'}, timeout=15)
        self.nonce = response.headers.get('Replay-Nonce')
        
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error: {e.response.status_code} {e.response.text}")
            raise
        
        return response

    def _get_key_authorization(self, token):
        """Generates the key authorization string for a challenge."""
        public_numbers = self.account_key.public_key().public_numbers()
        jwk = {
            "e": base64.urlsafe_b64encode(public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, 'big')).rstrip(b'=').decode('utf-8'),
            "kty": "RSA",
            "n": base64.urlsafe_b64encode(public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, 'big')).rstrip(b'=').decode('utf-8'),
        }
        jwk_json = json.dumps(jwk, sort_keys=True, separators=(',', ':'))
        thumbprint = base64.urlsafe_b64encode(hashlib.sha256(jwk_json.encode('utf-8')).digest()).rstrip(b'=')
        return f"{token}.{thumbprint.decode('utf-8')}"

    def _init_client(self, email):
        """Initializes ACME client and account."""
        if self.account_url:
            return

        self.directory = self.session.get(f"{self.base_url}/directory", timeout=10).json()
        self._get_nonce()

        account_payload = {"termsOfServiceAgreed": True, "contact": [f"mailto:{email}"]}
        response = self._send_signed_request(self.directory['newAccount'], account_payload)
        self.account_url = response.headers['Location']
        logger.info(f"ACME account created successfully: {self.account_url}")

    def generate_challenges(self, domains, email, validation_method):
        """Generates challenges for the given domains."""
        self._init_client(email)
        
        identifiers = [{"type": "dns", "value": d} for d in domains]
        order_payload = {"identifiers": identifiers}
        
        response = self._send_signed_request(self.directory['newOrder'], order_payload)
        self.order_url = response.headers['Location']
        self.order_data = response.json()

        request_id = str(int(time.time()))
        challenges = []
        for auth_url in self.order_data['authorizations']:
            auth_data = self.session.get(auth_url, timeout=10).json()
            domain = auth_data['identifier']['value']
            
            for chal in auth_data['challenges']:
                if chal['type'] == 'http-01' and validation_method == 'http':
                    token = chal['token']
                    key_auth = self._get_key_authorization(token)
                    challenges.append({
                        'type': 'http-01', 'domain': domain, 'token': token, 'url': chal['url'],
                        'file_path': f"/.well-known/acme-challenge/{token}", 'file_content': key_auth
                    })
                    break
        
        return {'request_id': request_id, 'challenges': challenges}

    def verify_domain_challenges(self, challenges):
        """Verifies that challenges have been met."""
        results = []
        for chal in challenges:
            self._send_signed_request(chal['url'], {}) # Signal readiness

            # Poll for status
            start_time = time.time()
            while time.time() - start_time < 90: # 90-second timeout
                try:
                    response = self.session.get(chal['url'], timeout=10).json()
                    if response['status'] == 'valid':
                        results.append({'domain': chal['domain'], 'verified': True, 'message': 'Verified'})
                        break
                    elif response['status'] == 'invalid':
                        error_detail = response.get('error', {}).get('detail', 'No details provided')
                        results.append({'domain': chal['domain'], 'verified': False, 'message': f"Failed: {error_detail}"})
                        break
                except requests.exceptions.RequestException as e:
                    logger.error(f"Polling failed for {chal['domain']}: {e}")
                    results.append({'domain': chal['domain'], 'verified': False, 'message': f"Polling request failed: {e}"})
                    break
                time.sleep(3)
            else:
                results.append({'domain': chal['domain'], 'verified': False, 'message': 'Polling timed out.'})
        return results

    def complete_certificate_generation(self, domains):
        """Finalizes the order and retrieves the certificate."""
        csr = x509.CertificateSigningRequestBuilder().subject_name(
            x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, domains[0])])
        ).add_extension(
            x509.SubjectAlternativeName([x509.DNSName(d) for d in domains]), critical=False
        ).sign(self.domain_key, hashes.SHA256())
        csr_der = csr.public_bytes(serialization.Encoding.DER)
        
        finalize_payload = {'csr': base64.urlsafe_b64encode(csr_der).rstrip(b'=').decode('utf-8')}
        self._send_signed_request(self.order_data['finalize'], finalize_payload)
        
        # Poll for cert
        start_time = time.time()
        while time.time() - start_time < 90:
            try:
                order_status = self.session.get(self.order_url, timeout=10).json()
                if order_status['status'] == 'valid':
                    cert_url = order_status['certificate']
                    cert_pem = self.session.get(cert_url, timeout=10).text
                    key_pem = self.domain_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.TraditionalOpenSSL,
                        encryption_algorithm=serialization.NoEncryption()
                    ).decode('utf-8')

                    temp_dir = tempfile.mkdtemp()
                    cert_path = os.path.join(temp_dir, 'certificate.crt')
                    key_path = os.path.join(temp_dir, 'private.key')
                    with open(cert_path, 'w') as f: f.write(cert_pem)
                    with open(key_path, 'w') as f: f.write(key_pem)
                    return {'certificate': cert_path, 'private_key': key_path}
                elif order_status['status'] == 'invalid':
                    logger.error(f"Order failed: {order_status}")
                    raise Exception(f"Certificate order failed: {order_status.get('error', 'No details')}")
            except requests.exceptions.RequestException as e:
                 logger.error(f"Certificate polling failed: {e}")
                 raise Exception("Certificate polling request failed.")
            time.sleep(3)
        raise Exception("Certificate generation timed out.")

    def cleanup(self):
        """Cleanup method for compatibility."""
        pass
