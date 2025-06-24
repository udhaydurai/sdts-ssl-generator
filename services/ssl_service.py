from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime, timedelta
import tempfile
import os

from real_acme_client import RealACMEClient

logger = logging.getLogger(__name__)

class SSLServiceInterface(ABC):
    """Abstract interface for SSL certificate services"""
    
    @abstractmethod
    def generate_certificate(self, domains: List[str], email: str, validation_method: str) -> Dict:
        """Generate SSL certificate"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Cleanup resources"""
        pass

class DemoSSLService(SSLServiceInterface):
    """Service for generating demo/self-signed certificates"""
    
    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or tempfile.mkdtemp()
        self.ssl_generator = None
    
    def generate_certificate(self, domains: List[str], email: str, validation_method: str) -> Dict:
        """Generate demo SSL certificate"""
        try:
            from ssl_generator import SSLGenerator
            self.ssl_generator = SSLGenerator()
            
            cert_files = self.ssl_generator.generate_certificate(
                domains=domains,
                email=email,
                validation_method=validation_method
            )
            
            if not cert_files:
                raise Exception("Failed to generate certificate files")
            
            return {
                'success': True,
                'files': cert_files,
                'type': 'demo',
                'domains': domains,
                'expires': datetime.now() + timedelta(minutes=15)
            }
            
        except Exception as e:
            logger.error(f"Demo SSL generation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'type': 'demo'
            }
    
    def cleanup(self):
        """Cleanup demo certificate resources"""
        if self.ssl_generator:
            self.ssl_generator.cleanup()

class RealSSLService(SSLServiceInterface):
    """Service for generating real Let's Encrypt certificates"""
    
    def __init__(self, use_staging=True):
        self.acme_client = RealACMEClient(use_staging)

    def generate_certificate(self, domains, email, validation_method):
        """Generates a real SSL certificate."""
        try:
            challenge_data = self.acme_client.generate_challenges(domains, email, validation_method)
            return {
                'success': True,
                'challenge_data': challenge_data,
                'expires': datetime.now() + timedelta(minutes=60)
            }
        except Exception as e:
            logger.error(f"Real SSL generation failed: {e}")
            raise

    def verify_challenges(self, challenges):
        """Verifies domain challenges and completes certificate generation."""
        try:
            verification_results = self.acme_client.verify_domain_challenges(challenges)
            
            all_verified = all(r['verified'] for r in verification_results)

            if not all_verified:
                return {
                    'success': False,
                    'verification_results': verification_results,
                    'message': "Some domains failed validation."
                }
            
            # All domains are verified, now finalize the certificate
            cert_result = self.acme_client.complete_certificate_generation(
                [c['domain'] for c in challenges]
            )

            # Check if we're on Vercel and need to handle certificate data differently
            if os.environ.get('VERCEL') and 'certificate_data' in cert_result:
                # On Vercel, we need to create temporary files in memory or handle differently
                # For now, we'll return the data directly and let the routes handle it
                return {
                    'success': True, 
                    'files': cert_result,  # Contains certificate_data and private_key_data
                    'expires': datetime.now() + timedelta(minutes=15),
                    'vercel_mode': True
                }
            else:
                # Local/Docker environment - normal file handling
                return {
                    'success': True, 
                    'files': cert_result,
                    'expires': datetime.now() + timedelta(minutes=15)
                }
        except Exception as e:
            logger.error(f"Challenge verification failed: {e}")
            raise

    def cleanup(self):
        """Cleanup real certificate resources"""
        if self.acme_client:
            self.acme_client.cleanup()

class SSLServiceFactory:
    """Factory for creating SSL services"""
    
    @staticmethod
    def create_service(cert_type: str, staging: bool = True) -> SSLServiceInterface:
        """Create appropriate SSL service based on type"""
        if cert_type == 'demo':
            return DemoSSLService()
        elif cert_type == 'real':
            return RealSSLService(use_staging=staging)
        else:
            raise ValueError(f"Unsupported certificate type: {cert_type}") 