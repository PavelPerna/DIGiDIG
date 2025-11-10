// DIGiDIG Mail App JavaScript

class MailApp {
    constructor() {
        this.currentPage = document.body.dataset.page || 'list';
        this.init();
    }

    init() {
        // Initialize page-specific functionality
        if (this.currentPage === 'compose') {
            this.initComposePage();
        } else if (this.currentPage === 'list') {
            this.initListPage();
        }

        // Initialize common functionality
        this.initCommon();

        // Adjust layout for sticky top pane
        this.adjustLayoutForTopPane();
    }

    initCommon() {
        // Add any common initialization here
        console.log('Mail app initialized for page:', this.currentPage);
    }

    initComposePage() {
        // Email composition functionality
        console.log('Initializing compose page');
    }

    initListPage() {
        // Email list functionality
        console.log('Initializing list page');
    }

    // Utility methods
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
        }
    }

    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    }

    async makeRequest(url, options = {}) {
        const defaultOptions = {
            credentials: 'include',  // Include cookies
            headers: {
                'Content-Type': 'application/json',
            }
        };

        // Merge headers properly
        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...(options.headers || {})
            }
        };

        const response = await fetch(url, mergedOptions);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    }

    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    adjustLayoutForTopPane() {
        const topPane = document.querySelector('.digidig-top-pane');
        const mainLayout = document.querySelector('.main-layout');

        if (topPane && mainLayout) {
            const topPaneHeight = topPane.offsetHeight;
            mainLayout.style.paddingTop = `${topPaneHeight}px`;

            // Update CSS custom property for consistency
            document.documentElement.style.setProperty('--top-pane-height', `${topPaneHeight}px`);

            // Re-adjust on window resize
            window.addEventListener('resize', () => {
                const newHeight = topPane.offsetHeight;
                mainLayout.style.paddingTop = `${newHeight}px`;
                document.documentElement.style.setProperty('--top-pane-height', `${newHeight}px`);
            });
        }
    }

    showMessage(message, type = 'success') {
        const messageEl = document.getElementById('message');
        if (messageEl) {
            messageEl.textContent = message;
            messageEl.className = `message ${type}`;
            messageEl.style.display = 'block';
            setTimeout(() => {
                messageEl.style.display = 'none';
            }, 5000);
        }
    }
}

// Global app instance
window.MailApp = new MailApp();