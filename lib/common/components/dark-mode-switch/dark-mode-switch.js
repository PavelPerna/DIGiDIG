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

            // Apply initial theme
            this.applyTheme();

            // Create the toggle button
            this.button = document.createElement('button');
            this.button.className = 'dark-mode-switch';
            this.button.setAttribute('aria-label', 'Toggle dark mode');
            this.button.setAttribute('title', 'Toggle dark mode');
            this.button.setAttribute('type', 'button');
            this.button.setAttribute('role', 'switch');
            this.button.setAttribute('aria-pressed', this.currentTheme === 'dark' ? 'true' : 'false');
            this.button.dataset.state = this.currentTheme;

            // Set initial state
            this.updateButtonState();

            // Add click handler
            this.button.addEventListener('click', () => this.toggleTheme());
            // Keyboard accessibility
            this.button.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.toggleTheme();
                }
            });

            this.element.appendChild(this.button);
            console.log('Dark mode switch created, initial theme:', this.currentTheme);

        } catch (error) {
            console.error('Dark mode switch initialization error:', error);
        }
    }

    async toggleTheme() {
        // Toggle theme
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';

        // Apply theme immediately for responsive UI
        this.applyTheme();

        // Update button state
        this.updateButtonState();

        // Save preference
        const darkMode = this.currentTheme === 'dark';
        await window.DigiDigPreferences.setPreference('darkMode', darkMode);

        console.log('Theme toggled to:', this.currentTheme);
    }

    applyTheme() {
        // Apply both data-theme and body class so templates that check either will work
        if (this.currentTheme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
            document.body.classList.add('dark-mode');
            document.documentElement.lang = document.documentElement.lang || 'en';
        } else {
            document.documentElement.removeAttribute('data-theme');
            document.body.classList.remove('dark-mode');
        }
    }

    updateButtonState() {
        if (!this.button) return;

        if (this.currentTheme === 'dark') {
            this.button.classList.add('active');
            this.button.setAttribute('aria-pressed', 'true');
            this.button.dataset.state = 'dark';
        } else {
            this.button.classList.remove('active');
            this.button.setAttribute('aria-pressed', 'false');
            this.button.dataset.state = 'light';
        }
    }
}

// Auto-initialize
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-component="dark-mode-switch"]').forEach(element => {
        new DarkModeSwitch(element);
    });
});