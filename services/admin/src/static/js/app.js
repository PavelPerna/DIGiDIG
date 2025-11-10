// DIGiDIG Admin App JavaScript

class AdminApp {
    constructor() {
        this.currentPage = document.body.dataset.page || 'domains';
        this.init();
    }

    init() {
        // Initialize page-specific functionality
        if (this.currentPage === 'domains') {
            this.initDomainsPage();
        } else if (this.currentPage === 'services') {
            this.initServicesPage();
        }

        // Initialize common functionality
        this.initCommon();

        // Adjust layout for sticky top pane
        this.adjustLayoutForTopPane();
    }

    initCommon() {
        // Add any common initialization here
        console.log('Admin app initialized for page:', this.currentPage);
    }

    initDomainsPage() {
        // Domain management functionality
        console.log('Initializing domains page');
    }

    initServicesPage() {
        // Service management functionality
        console.log('Initializing services page');
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
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.getCookie('access_token')}`
            }
        };

        const response = await fetch(url, { ...defaultOptions, ...options });
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
}

// Global app instance
window.AdminApp = new AdminApp();