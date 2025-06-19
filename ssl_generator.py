import os
import logging
import tempfile
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
import datetime

class SSLGenerator:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def generate_certificate(self, domains, email, validation_method='http'):
        """
        Generate SSL certificate using Let's Encrypt simulation
        Note: This is a simplified implementation for demonstration.
        In production, you would use the ACME protocol with proper domain validation.
        """
        try:
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # Create certificate request
            subject = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Let's Encrypt Simulation"),
                x509.NameAttribute(NameOID.COMMON_NAME, domains[0]),
            ])
            
            # Create self-signed certificate (simulation)
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                subject  # Self-signed for simulation
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.datetime.utcnow()
            ).not_valid_after(
                datetime.datetime.utcnow() + datetime.timedelta(days=90)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName(domain) for domain in domains
                ]),
                critical=False,
            ).sign(private_key, hashes.SHA256())
            
            # Create CA certificate (simulation)
            ca_subject = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SDTS SSL Generator Demo CA"),
                x509.NameAttribute(NameOID.COMMON_NAME, "SDTS Demo Root CA"),
            ])
            
            ca_cert = x509.CertificateBuilder().subject_name(
                ca_subject
            ).issuer_name(
                ca_subject
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.datetime.utcnow()
            ).not_valid_after(
                datetime.datetime.utcnow() + datetime.timedelta(days=365)
            ).add_extension(
                x509.BasicConstraints(ca=True, path_length=None),
                critical=True,
            ).sign(private_key, hashes.SHA256())
            
            # Write files
            private_key_path = os.path.join(self.temp_dir, f'{domains[0]}.key')
            cert_path = os.path.join(self.temp_dir, f'{domains[0]}.crt')
            ca_cert_path = os.path.join(self.temp_dir, f'{domains[0]}-ca.crt')
            
            # Write private key
            with open(private_key_path, 'wb') as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # Write certificate
            with open(cert_path, 'wb') as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            # Write CA certificate
            with open(ca_cert_path, 'wb') as f:
                f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
            
            logging.info(f"SSL certificate generated for domains: {domains}")
            
            return {
                'private_key': private_key_path,
                'certificate': cert_path,
                'ca_bundle': ca_cert_path
            }
            
        except Exception as e:
            logging.error(f"SSL generation error: {str(e)}")
            raise Exception(f"Failed to generate SSL certificate: {str(e)}")
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            logging.error(f"Cleanup error: {str(e)}")
