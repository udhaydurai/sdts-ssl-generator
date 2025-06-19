// SSL Certificate Generator JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('sslForm');
    const generateBtn = document.getElementById('generateBtn');
    
    if (form && generateBtn) {
        // Form validation
        form.addEventListener('submit', function(e) {
            if (!validateForm()) {
                e.preventDefault();
                return false;
            }
            
            // Show loading state
            showLoadingState();
        });
        
        // Real-time validation
        const domainsInput = document.getElementById('domains');
        const emailInput = document.getElementById('email');
        
        if (domainsInput) {
            domainsInput.addEventListener('blur', validateDomains);
            domainsInput.addEventListener('input', clearValidationState);
        }
        
        if (emailInput) {
            emailInput.addEventListener('blur', validateEmail);
            emailInput.addEventListener('input', clearValidationState);
        }
    }
    
    // Auto-dismiss alerts after 5 seconds (except sticky warnings)
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        if (!alert.classList.contains('alert-info') && !alert.classList.contains('sticky-warning')) {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        }
    });
});

function validateForm() {
    let isValid = true;
    
    // Validate domains
    if (!validateDomains()) {
        isValid = false;
    }
    
    // Validate email
    if (!validateEmail()) {
        isValid = false;
    }
    
    // Validate agreement checkbox
    const agreementCheckbox = document.getElementById('accept_agreement');
    if (!agreementCheckbox.checked) {
        showError(agreementCheckbox, 'You must accept the Let\'s Encrypt Subscriber Agreement.');
        isValid = false;
    }
    
    return isValid;
}

function validateDomains() {
    const domainsInput = document.getElementById('domains');
    const domains = domainsInput.value.trim();
    
    if (!domains) {
        showError(domainsInput, 'Domain name(s) are required.');
        return false;
    }
    
    const domainList = domains.split(',').map(d => d.trim()).filter(d => d);
    
    if (domainList.length === 0) {
        showError(domainsInput, 'Please enter at least one valid domain.');
        return false;
    }
    
    // Validate each domain
    for (let domain of domainList) {
        if (!isValidDomain(domain)) {
            showError(domainsInput, `Invalid domain format: ${domain}`);
            return false;
        }
    }
    
    showValid(domainsInput, `${domainList.length} domain(s) validated successfully.`);
    return true;
}

function validateEmail() {
    const emailInput = document.getElementById('email');
    const email = emailInput.value.trim();
    
    if (!email) {
        showError(emailInput, 'Email address is required.');
        return false;
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showError(emailInput, 'Please enter a valid email address.');
        return false;
    }
    
    showValid(emailInput, 'Email address is valid.');
    return true;
}

function isValidDomain(domain) {
    // Remove protocol if present
    if (domain.startsWith('http://') || domain.startsWith('https://')) {
        return false;
    }
    
    // Basic domain validation regex
    const domainRegex = /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
    
    return domainRegex.test(domain) && domain.length <= 253;
}

function showError(input, message) {
    input.classList.remove('is-valid');
    input.classList.add('is-invalid');
    
    // Remove existing feedback
    const existingFeedback = input.parentNode.querySelector('.invalid-feedback');
    if (existingFeedback) {
        existingFeedback.remove();
    }
    
    // Add error message
    const feedback = document.createElement('div');
    feedback.className = 'invalid-feedback';
    feedback.textContent = message;
    input.parentNode.appendChild(feedback);
}

function showValid(input, message) {
    input.classList.remove('is-invalid');
    input.classList.add('is-valid');
    
    // Remove existing feedback
    const existingFeedback = input.parentNode.querySelector('.valid-feedback, .invalid-feedback');
    if (existingFeedback) {
        existingFeedback.remove();
    }
    
    // Add success message
    const feedback = document.createElement('div');
    feedback.className = 'valid-feedback';
    feedback.textContent = message;
    input.parentNode.appendChild(feedback);
}

function clearValidationState(event) {
    const input = event.target;
    input.classList.remove('is-valid', 'is-invalid');
    
    // Remove feedback messages
    const feedback = input.parentNode.querySelector('.valid-feedback, .invalid-feedback');
    if (feedback) {
        feedback.remove();
    }
}

function showLoadingState() {
    const generateBtn = document.getElementById('generateBtn');
    const btnText = generateBtn.querySelector('.btn-text');
    const btnLoading = generateBtn.querySelector('.btn-loading');
    
    generateBtn.disabled = true;
    btnText.classList.add('d-none');
    btnLoading.classList.remove('d-none');
    
    // Prevent double submission
    generateBtn.form.addEventListener('submit', function(e) {
        e.preventDefault();
    });
}

// Domain input formatting
function formatDomainInput(event) {
    const input = event.target;
    let value = input.value;
    
    // Remove extra spaces around commas
    value = value.replace(/\s*,\s*/g, ', ');
    
    input.value = value;
}

// Add domain input formatting
document.addEventListener('DOMContentLoaded', function() {
    const domainsInput = document.getElementById('domains');
    if (domainsInput) {
        domainsInput.addEventListener('input', formatDomainInput);
    }
});

// Countdown timer for download links
function startCountdown() {
    const downloadSection = document.querySelector('.download-section');
    if (!downloadSection) return;
    
    let timeLeft = 15 * 60; // 15 minutes in seconds
    
    const timerElement = document.createElement('div');
    timerElement.className = 'text-muted text-center mt-2';
    timerElement.innerHTML = '<small><i class="fas fa-clock me-1"></i>Download links expire in <span id="countdown">15:00</span></small>';
    
    downloadSection.appendChild(timerElement);
    
    const countdownElement = document.getElementById('countdown');
    
    const timer = setInterval(() => {
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        
        countdownElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        if (timeLeft <= 0) {
            clearInterval(timer);
            location.reload(); // Refresh page when timer expires
        }
        
        timeLeft--;
    }, 1000);
}

// Start countdown if download section exists
document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('.download-section')) {
        startCountdown();
    }
    
    // Add copy functionality for certificate contents
    const copyButtons = document.querySelectorAll('.copy-btn');
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const textarea = document.getElementById(targetId);
            
            if (textarea) {
                // Select and copy the text
                textarea.select();
                textarea.setSelectionRange(0, 99999); // For mobile devices
                
                try {
                    document.execCommand('copy');
                    
                    // Update button to show success
                    const originalIcon = this.querySelector('i');
                    const originalText = this.innerHTML;
                    
                    this.classList.add('copied');
                    this.innerHTML = '<i class="fas fa-check me-1"></i>Copied!';
                    
                    // Reset button after 2 seconds
                    setTimeout(() => {
                        this.classList.remove('copied');
                        this.innerHTML = originalText;
                    }, 2000);
                    
                } catch (err) {
                    console.error('Failed to copy text: ', err);
                    
                    // Fallback: show manual copy instruction
                    this.innerHTML = '<i class="fas fa-exclamation me-1"></i>Select All';
                    setTimeout(() => {
                        this.innerHTML = originalText;
                    }, 2000);
                }
                
                // Deselect the text
                if (window.getSelection) {
                    window.getSelection().removeAllRanges();
                }
            }
        });
    });
});
