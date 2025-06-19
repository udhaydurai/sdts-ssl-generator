from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime, timedelta
import tempfile
import os

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
    
    def __init__(self, staging: bool = True):
        self.staging = staging
        self.acme_client = None
    
    def generate_certificate(self, domains: List[str], email: str, validation_method: str) -> Dict:
        """Generate real SSL certificate with challenges"""
        try:
            from real_acme_client import RealACMEClient
            self.acme_client = RealACMEClient(staging=self.staging)
            
            challenge_result = self.acme_client.generate_certificate_with_challenges(
                domains=domains,
                email=email,
                validation_method=validation_method
            )
            
            return {
                'success': True,
                'challenge_data': challenge_result,
                'type': 'real',
                'domains': domains,
                'staging': self.staging,
                'expires': datetime.now() + timedelta(hours=1)
            }
            
        except Exception as e:
            logger.error(f"Real SSL generation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'type': 'real'
            }
    
    def verify_challenges(self, request_id: str) -> Dict:
        """Verify domain validation challenges"""
        try:
            if not self.acme_client:
                raise Exception("ACME client not initialized")
            
            verified, verification_results = self.acme_client.verify_challenges(request_id)
            
            if verified:
                cert_files = self.acme_client.complete_certificate_generation(request_id)
                return {
                    'success': True,
                    'files': cert_files,
                    'type': 'real',
                    'expires': datetime.now() + timedelta(minutes=15)
                }
            else:
                return {
                    'success': False,
                    'verification_results': verification_results,
                    'type': 'real'
                }
                
        except Exception as e:
            logger.error(f"Challenge verification failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'type': 'real'
            }
    
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
            return RealSSLService(staging=staging)
        else:
            raise ValueError(f"Unsupported certificate type: {cert_type}") 