import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32)
    SESSION_SECRET = os.environ.get('SESSION_SECRET') or os.urandom(32)
    
    # File upload settings
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or os.path.join(os.getcwd(), 'temp_certs')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    
    # Certificate settings
    CERT_EXPIRY_MINUTES = int(os.environ.get('CERT_EXPIRY_MINUTES', 15))
    CHALLENGE_EXPIRY_HOURS = int(os.environ.get('CHALLENGE_EXPIRY_HOURS', 1))
    
    # ACME settings
    ACME_STAGING = os.environ.get('ACME_STAGING', 'true').lower() == 'true'
    ACME_RATE_LIMIT = int(os.environ.get('ACME_RATE_LIMIT', 5))  # requests per minute per IP
    
    # DNS validation settings
    DNS_PROPAGATION_TIMEOUT = int(os.environ.get('DNS_PROPAGATION_TIMEOUT', 300))  # 5 minutes
    DNS_CHECK_INTERVAL = int(os.environ.get('DNS_CHECK_INTERVAL', 30))  # 30 seconds
    
    # Security settings
    CSRF_ENABLED = os.environ.get('CSRF_ENABLED', 'true').lower() == 'true'
    RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    
    # Database settings (for future use)
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    ACME_STAGING = False  # Use production Let's Encrypt

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 