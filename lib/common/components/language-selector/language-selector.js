// Language Selector Component - Flag Icons Dropdown
class LanguageSelector {
    constructor(element) {
        this.element = element;
        this.container = null;
        this.dropdown = null;
        this.currentLanguage = 'en';
        this.isOpen = false;
        this.languages = {
            'en': {
                name: 'English',
                native: 'English',
                flag: this.createUSFlag(),
                country: 'United States'
            },
            'cs': {
                name: 'Czech',
                native: 'Čeština',
                flag: this.createCzechFlag(),
                country: 'Czech Republic'
            }
        };
        this.init();
    }

    createUSFlag() {
        return `<svg width="24" height="18" viewBox="0 0 24 18" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="24" height="18" fill="#B22234"/>
            <rect y="2" width="24" height="2" fill="#FFFFFF"/>
            <rect y="6" width="24" height="2" fill="#FFFFFF"/>
            <rect y="10" width="24" height="2" fill="#FFFFFF"/>
            <rect y="14" width="24" height="2" fill="#FFFFFF"/>
            <rect x="0" y="0" width="10" height="10" fill="#3C3B6E"/>
            <rect x="1" y="1" width="1" height="1" fill="#FFFFFF"/>
            <rect x="3" y="1" width="1" height="1" fill="#FFFFFF"/>
            <rect x="5" y="1" width="1" height="1" fill="#FFFFFF"/>
            <rect x="7" y="1" width="1" height="1" fill="#FFFFFF"/>
            <rect x="9" y="1" width="1" height="1" fill="#FFFFFF"/>
            <rect x="2" y="2" width="1" height="1" fill="#FFFFFF"/>
            <rect x="4" y="2" width="1" height="1" fill="#FFFFFF"/>
            <rect x="6" y="2" width="1" height="1" fill="#FFFFFF"/>
            <rect x="8" y="2" width="1" height="1" fill="#FFFFFF"/>
            <rect x="1" y="3" width="1" height="1" fill="#FFFFFF"/>
            <rect x="3" y="3" width="1" height="1" fill="#FFFFFF"/>
            <rect x="5" y="3" width="1" height="1" fill="#FFFFFF"/>
            <rect x="7" y="3" width="1" height="1" fill="#FFFFFF"/>
            <rect x="9" y="3" width="1" height="1" fill="#FFFFFF"/>
            <rect x="2" y="4" width="1" height="1" fill="#FFFFFF"/>
            <rect x="4" y="4" width="1" height="1" fill="#FFFFFF"/>
            <rect x="6" y="4" width="1" height="1" fill="#FFFFFF"/>
            <rect x="8" y="4" width="1" height="1" fill="#FFFFFF"/>
            <rect x="1" y="5" width="1" height="1" fill="#FFFFFF"/>
            <rect x="3" y="5" width="1" height="1" fill="#FFFFFF"/>
            <rect x="5" y="5" width="1" height="1" fill="#FFFFFF"/>
            <rect x="7" y="5" width="1" height="1" fill="#FFFFFF"/>
            <rect x="9" y="5" width="1" height="1" fill="#FFFFFF"/>
            <rect x="2" y="6" width="1" height="1" fill="#FFFFFF"/>
            <rect x="4" y="6" width="1" height="1" fill="#FFFFFF"/>
            <rect x="6" y="6" width="1" height="1" fill="#FFFFFF"/>
            <rect x="8" y="6" width="1" height="1" fill="#FFFFFF"/>
            <rect x="1" y="7" width="1" height="1" fill="#FFFFFF"/>
            <rect x="3" y="7" width="1" height="1" fill="#FFFFFF"/>
            <rect x="5" y="7" width="1" height="1" fill="#FFFFFF"/>
            <rect x="7" y="7" width="1" height="1" fill="#FFFFFF"/>
            <rect x="9" y="7" width="1" height="1" fill="#FFFFFF"/>
            <rect x="2" y="8" width="1" height="1" fill="#FFFFFF"/>
            <rect x="4" y="8" width="1" height="1" fill="#FFFFFF"/>
            <rect x="6" y="8" width="1" height="1" fill="#FFFFFF"/>
            <rect x="8" y="8" width="1" height="1" fill="#FFFFFF"/>
        </svg>`;
    }

    createCzechFlag() {
        return `<svg width="24" height="18" viewBox="0 0 24 18" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="24" height="9" fill="#FFFFFF"/>
            <rect y="9" width="24" height="9" fill="#D52B1E"/>
            <rect width="24" height="6" fill="#11457E"/>
        </svg>`;
    }

    async init() {
        try {
            // Wait for preferences to be available
            await window.DigiDigPreferences._initPromise;

            // Get current language preference
            const language = await window.DigiDigPreferences.getPreference('language');
            this.currentLanguage = language || 'en';

            // Apply initial language
            this.applyLanguage();

            // Create the dropdown
            this.createSelector();

            this.element.appendChild(this.container);
            console.log('Flag-based language selector created, initial language:', this.currentLanguage);

        } catch (error) {
            console.error('Language selector initialization error:', error);
        }
    }

    createSelector() {
        // Create main container
        this.container = document.createElement('div');
        this.container.className = 'language-selector-flags';

        // Create dropdown button
        const dropdownButton = document.createElement('button');
        dropdownButton.className = 'language-selector-button-flags';
        dropdownButton.innerHTML = `
            <div class="flag-container">
                ${this.languages[this.currentLanguage].flag}
            </div>
            <span class="language-code">${this.currentLanguage.toUpperCase()}</span>
            <svg class="dropdown-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="6,9 12,15 18,9"></polyline>
            </svg>
        `;
        dropdownButton.addEventListener('click', () => this.toggleDropdown());

        // Create dropdown menu
        this.dropdown = document.createElement('div');
        this.dropdown.className = 'language-dropdown-flags';

        // Add language options
        Object.keys(this.languages).forEach(lang => {
            const option = document.createElement('div');
            option.className = `language-option-flags ${lang === this.currentLanguage ? 'active' : ''}`;
            option.dataset.lang = lang;
            option.innerHTML = `
                <div class="option-flag">
                    ${this.languages[lang].flag}
                </div>
                <div class="option-content">
                    <div class="option-name">${this.languages[lang].name}</div>
                    <div class="option-country">${this.languages[lang].country}</div>
                </div>
                ${lang === this.currentLanguage ? '<div class="selected-indicator">✓</div>' : ''}
            `;
            option.addEventListener('click', () => this.selectLanguage(lang));
            this.dropdown.appendChild(option);
        });

        this.container.appendChild(dropdownButton);
        this.container.appendChild(this.dropdown);

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.closeDropdown();
            }
        });
    }

    toggleDropdown() {
        this.isOpen = !this.isOpen;
        if (this.isOpen) {
            this.dropdown.classList.add('open');
            this.container.classList.add('active');
        } else {
            this.dropdown.classList.remove('open');
            this.container.classList.remove('active');
        }
    }

    closeDropdown() {
        this.isOpen = false;
        this.dropdown.classList.remove('open');
        this.container.classList.remove('active');
    }

    async selectLanguage(newLanguage) {
        if (newLanguage === this.currentLanguage) {
            this.closeDropdown();
            return;
        }

        // Update current language
        this.currentLanguage = newLanguage;

        // Update UI
        this.updateUI();

        // Apply language immediately
        this.applyLanguage();

        // Save preference
        try {
            await window.DigiDigPreferences.setPreference('language', newLanguage);

            // If user is authenticated, try to update preferences on Identity service
            try {
                const accessToken = (document.cookie || '').split('; ').find(c => c.startsWith('access_token='));
                if (accessToken) {
                    const token = accessToken.split('=')[1];
                    const identityUrl = window.DIGIDIG_SERVICE_URLS && window.DIGIDIG_SERVICE_URLS.identity;
                    if (identityUrl) {
                        await fetch(identityUrl + '/api/user/preferences', {
                            method: 'PUT',
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': `Bearer ${token}`
                            },
                            body: JSON.stringify({ language: newLanguage })
                        });
                    }
                }
            } catch (err) {
                // Non-fatal - log and continue
                console.warn('Failed to update identity preferences:', err);
            }

            // Inform SSO service for immediate server-side language switch
            try {
                const formData = new FormData();
                formData.append('lang', newLanguage);
                await fetch('/api/language', {
                    method: 'POST',
                    body: formData
                });
            } catch (err) {
                console.warn('Failed to notify SSO of language change:', err);
            }

        } catch (err) {
            console.error('Failed to save language preference:', err);
        }

        // Close dropdown and reload to apply server-side translations
        this.closeDropdown();
        window.location.reload();
        console.log('Language changed to:', newLanguage, '- reloading page');
    }

    updateUI() {
        // Update button display
        const button = this.container.querySelector('.language-selector-button-flags');
        if (button) {
            button.innerHTML = `
                <div class="flag-container">
                    ${this.languages[this.currentLanguage].flag}
                </div>
                <span class="language-code">${this.currentLanguage.toUpperCase()}</span>
                <svg class="dropdown-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="6,9 12,15 18,9"></polyline>
                </svg>
            `;
        }

        // Update active states in dropdown
        const options = this.container.querySelectorAll('.language-option-flags');
        options.forEach(option => {
            const lang = option.dataset.lang;
            if (lang === this.currentLanguage) {
                option.classList.add('active');
                // Add selected indicator if not present
                if (!option.querySelector('.selected-indicator')) {
                    const indicator = document.createElement('div');
                    indicator.className = 'selected-indicator';
                    indicator.textContent = '✓';
                    option.appendChild(indicator);
                }
            } else {
                option.classList.remove('active');
                // Remove selected indicator
                const indicator = option.querySelector('.selected-indicator');
                if (indicator) {
                    indicator.remove();
                }
            }
        });
    }

    applyLanguage() {
        // Set document language attribute
        document.documentElement.lang = this.currentLanguage;
    }
}

// Auto-initialize
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-component="language-selector"]').forEach(element => {
        new LanguageSelector(element);
    });
});