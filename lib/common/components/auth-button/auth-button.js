// Auth Button - jeden button LOGIN nebo LOGOUT
class AuthButton {
    constructor(element) {
        this.element = element;
        this.button = null;
        this.init();
    }

    async init() {
        try {
            // Check authentication status
            const isLoggedIn = await this.checkAuthStatus();
            
            // Create button based on auth status
            this.button = document.createElement('button');
            this.button.className = 'auth-button';
            
            if (isLoggedIn) {
                this.button.textContent = window.DIGIDIG_I18N ? window.DIGIDIG_I18N.logout : 'Logout';
                this.button.onclick = async (e) => {
                    e.preventDefault();
                    await this.logout();
                };
            } else {
                this.button.textContent = window.DIGIDIG_I18N ? window.DIGIDIG_I18N.login : 'Login';
                this.button.onclick = (e) => {
                    e.preventDefault();
                    this.login();
                };
            }

            this.element.appendChild(this.button);
        } catch (error) {
            console.error('Auth button initialization error:', error);
            // Fallback - show login button
            this.button = document.createElement('button');
            this.button.className = 'auth-button';
            this.button.textContent = window.DIGIDIG_I18N ? window.DIGIDIG_I18N.login : 'Login';
            this.button.onclick = (e) => {
                e.preventDefault();
                this.login();
            };
            this.element.appendChild(this.button);
        }
    }

    async checkAuthStatus() {
        try {
            // Check if we have user info from server-side rendering
            if (window.DIGIDIG_USER_INFO && window.DIGIDIG_USER_INFO.username) {
                return true;
            }
            
            // Fallback: check session via API
            const response = await fetch('/api/identity/session/verify', {
                credentials: 'include'
            });
            
            if (response.ok) {
                const data = await response.json();
                return data.authenticated === true;
            }
            
            return false;
        } catch (error) {
            console.error('Auth check failed:', error);
            return false;
        }
    }

    async logout() {
        try {
            console.log('Logging out...');
            
            // Call logout API via proxy
            const response = await fetch('/api/identity/logout', { 
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            console.log('Logout response:', response.status);
            
            // Always redirect to home after logout attempt
            window.location.href = '/';
        } catch (error) {
            console.error('Logout failed:', error);
            // Fallback - redirect anyway
            window.location.href = '/';
        }
    }

    login() {
        // Redirect to SSO login with return URL
        const currentUrl = encodeURIComponent(window.location.href);
        const ssoUrl = window.DIGIDIG_SERVICE_URLS && window.DIGIDIG_SERVICE_URLS.sso 
            ? `${window.DIGIDIG_SERVICE_URLS.sso}/login?return_url=${currentUrl}`
            : '/login'; // Fallback
        window.location.href = ssoUrl;
    }
}

// Auto-initialize
function initAuthButtons() {
    const elements = document.querySelectorAll('[data-component="auth-button"]');
    elements.forEach((element) => {
        if (!element._authButtonInitialized) {
            element._authButtonInitialized = true;
            new AuthButton(element);
        }
    });
}

document.addEventListener('DOMContentLoaded', initAuthButtons);

// Also try to initialize immediately if DOM is already ready
if (document.readyState === 'loading') {
    // DOM not ready yet
} else {
    // DOM is already ready
    setTimeout(initAuthButtons, 100);
}

// Fallback: try again after a short delay
setTimeout(initAuthButtons, 1000);
