// Auth Button - jeden button LOGIN nebo LOGOUT
class AuthButton {
    constructor(element) {
        this.element = element;
        this.button = null;
        this.init();
    }

    async init() {
        try {
            // Zjisti stav session - identity má endpointy bez /api/ prefixu
            const response = await fetch('/api/identity/session/verify');
            const isLoggedIn = response.ok;
            
            console.log('Auth button: logged in =', isLoggedIn);

            // Vytvoř button
            this.button = document.createElement('button');
            this.button.className = 'auth-button';
            
            if (isLoggedIn) {
                this.button.textContent = 'Logout';
                this.button.onclick = async (e) => {
                    e.preventDefault();
                    await this.logout();
                };
            } else {
                this.button.textContent = 'Login';
                this.button.onclick = (e) => {
                    e.preventDefault();
                    this.login();
                };
            }

            this.element.appendChild(this.button);
            console.log('Auth button created:', this.button);
        } catch (error) {
            console.error('Auth button error:', error);
        }
    }

    async logout() {
        try {
            console.log('Logging out...');
            // Proxy mapuje /api/identity/logout -> identity:9101/logout
            const response = await fetch('/api/identity/logout', { 
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            console.log('Logout response:', response.status);
            window.location.href = '/';
        } catch (error) {
            console.error('Logout failed:', error);
            // Fallback - zkus přesměrovat i když logout selhal
            window.location.href = '/';
        }
    }

    login() {
        window.location.href = '/login';
    }
}

// Auto-initialize
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-component="auth-button"]').forEach(element => {
        new AuthButton(element);
    });
});
