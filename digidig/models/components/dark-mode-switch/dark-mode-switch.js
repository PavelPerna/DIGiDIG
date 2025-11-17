// Dark Mode Switch Component
class DarkModeSwitch {
    constructor(element) {
        this.element = element;
        this.button = null;
        this.currentTheme = 'light';
        this.init();
    }

    async init() {
        try {
            // Wait for preferences to be available
            await window.DigiDigPreferences._initPromise;

            // Get current dark mode preference
            const darkMode = await window.DigiDigPreferences.getPreference('darkMode');
            this.currentTheme = darkMode ? 'dark' : 'light';

            // Theme is already applied server-side, no need to apply again

            // Create the toggle button
            this.button = document.createElement('button');
            this.button.className = 'dark-mode-switch';
            this.button.setAttribute('aria-label', 'Toggle dark mode');
            this.button.setAttribute('title', 'Toggle dark mode');

            // Set initial state
            this.updateButtonState();

            // Add click handler
            this.button.addEventListener('click', () => this.toggleTheme());

            this.element.appendChild(this.button);
            console.log('Dark mode switch created, initial theme:', this.currentTheme);

        } catch (error) {
            console.error('Dark mode switch initialization error:', error);
        }
    }

    async toggleTheme() {
        // Toggle theme
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';

        // Update button state immediately for responsive UI
        this.updateButtonState();

        // Save preference
        const darkMode = this.currentTheme === 'dark';
        await window.DigiDigPreferences.setPreference('darkMode', darkMode);

        // Reload page to apply server-side theme
        window.location.reload();

        console.log('Theme changed to:', this.currentTheme, '- reloading page');
    }

    applyTheme() {
        if (this.currentTheme === 'dark') {
            document.body.classList.add('dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
        }
    }

    updateButtonState() {
        if (!this.button) return;

        if (this.currentTheme === 'dark') {
            this.button.classList.add('active');
        } else {
            this.button.classList.remove('active');
        }
    }
}

// Auto-initialize
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-component="dark-mode-switch"]').forEach(element => {
        new DarkModeSwitch(element);
    });
});