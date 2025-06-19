import re
import validators
from typing import List, Dict, Tuple
import dns.resolver
import logging

logger = logging.getLogger(__name__)

class DomainValidator:
    """Comprehensive domain validation for SSL certificates"""
    
    # Domain regex patterns
    DOMAIN_PATTERN = re.compile(
        r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    )
    
    # Reserved TLDs and invalid domains
    RESERVED_TLDS = {
        'localhost', 'local', 'test', 'example', 'invalid', 'dev'
    }
    
    # Maximum domains per certificate
    MAX_DOMAINS = 100
    
    @classmethod
    def validate_domains(cls, domains: str) -> Tuple[bool, List[str], str]:
        """
        Validate domain input string
        Returns: (is_valid, domain_list, error_message)
        """
        try:
            # Split and clean domains
            domain_list = [d.strip().lower() for d in domains.split(',') if d.strip()]
            
            if not domain_list:
                return False, [], "No domains provided"
            
            if len(domain_list) > cls.MAX_DOMAINS:
                return False, [], f"Too many domains. Maximum allowed: {cls.MAX_DOMAINS}"
            
            # Validate each domain
            valid_domains = []
            for domain in domain_list:
                is_valid, error = cls.validate_single_domain(domain)
                if not is_valid:
                    return False, [], f"Invalid domain '{domain}': {error}"
                valid_domains.append(domain)
            
            return True, valid_domains, ""
            
        except Exception as e:
            logger.error(f"Domain validation error: {str(e)}")
            return False, [], f"Validation error: {str(e)}"
    
    @classmethod
    def validate_single_domain(cls, domain: str) -> Tuple[bool, str]:
        """Validate a single domain"""
        try:
            # Basic format check
            if not cls.DOMAIN_PATTERN.match(domain):
                return False, "Invalid domain format"
            
            # Check for reserved TLDs
            tld = domain.split('.')[-1]
            if tld in cls.RESERVED_TLDS:
                return False, f"Reserved TLD not allowed: {tld}"
            
            # Check for IP addresses
            if validators.ip_address.ipv4(domain) or validators.ip_address.ipv6(domain):
                return False, "IP addresses are not supported"
            
            # Check for wildcards (only allow at subdomain level)
            if '*' in domain:
                if not domain.startswith('*.'):
                    return False, "Wildcards must be at subdomain level (e.g., *.example.com)"
                if domain.count('*') > 1:
                    return False, "Multiple wildcards not allowed"
            
            # Check domain length
            if len(domain) > 253:
                return False, "Domain too long (max 253 characters)"
            
            # Check label length
            for label in domain.split('.'):
                if len(label) > 63:
                    return False, f"Domain label too long: {label}"
                if len(label) == 0:
                    return False, "Empty domain label"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Single domain validation error: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    @classmethod
    def validate_email(cls, email: str) -> Tuple[bool, str]:
        """Validate email address"""
        try:
            if not email or not email.strip():
                return False, "Email is required"
            
            email = email.strip().lower()
            
            if not validators.email(email):
                return False, "Invalid email format"
            
            # Check for disposable email providers (optional)
            disposable_domains = {
                '10minutemail.com', 'tempmail.org', 'guerrillamail.com'
            }
            email_domain = email.split('@')[-1]
            if email_domain in disposable_domains:
                return False, "Disposable email addresses are not allowed"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Email validation error: {str(e)}")
            return False, f"Email validation error: {str(e)}"
    
    @classmethod
    def check_dns_resolution(cls, domain: str) -> Tuple[bool, str]:
        """Check if domain resolves to DNS"""
        try:
            # Remove wildcard for DNS check
            check_domain = domain.replace('*.', '')
            
            # Try to resolve A record
            try:
                dns.resolver.resolve(check_domain, 'A')
                return True, ""
            except dns.resolver.NXDOMAIN:
                return False, f"Domain {domain} does not exist"
            except dns.resolver.NoAnswer:
                # Try CNAME record
                try:
                    dns.resolver.resolve(check_domain, 'CNAME')
                    return True, ""
                except dns.resolver.NXDOMAIN:
                    return False, f"Domain {domain} does not exist"
                except Exception:
                    return False, f"Domain {domain} has no A or CNAME records"
            except Exception as e:
                return False, f"DNS resolution failed: {str(e)}"
                
        except Exception as e:
            logger.error(f"DNS resolution check error: {str(e)}")
            return False, f"DNS check error: {str(e)}"
    
    @classmethod
    def validate_validation_method(cls, method: str) -> Tuple[bool, str]:
        """Validate ACME validation method"""
        valid_methods = ['dns', 'http']
        
        if not method or method not in valid_methods:
            return False, f"Invalid validation method. Must be one of: {', '.join(valid_methods)}"
        
        return True, "" 