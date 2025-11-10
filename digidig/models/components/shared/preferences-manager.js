/**
 * DIGiDIG Preferences Manager
 * 
 * Adaptive persistence strategy:
 * - Authenticated users: Identity API + local fallback
 * - Anonymous users: Local storage + cookies
 */

class PreferencesManager {
    constructor() {
        // Start with conservative defaults; we will probe the server to confirm auth state.
        this.isAuthenticated = false;
        this.strategy = 'local';
        this.defaults = {
            language: 'en',
            darkMode: false
        };

        // Perform async initialization to detect auth state via server (identity API)
        this._initPromise = this.detectAuthStateAsync();
    }

    /**
     * Detect if user is authenticated by checking for access_token cookie
     */
    detectAuthState() {
        // Synchronous fallback used during early page load: rely on server-rendered meta tag
        try {
            const meta = document.querySelector('meta[name="digidig-authenticated"]');
            if (meta && meta.content === 'true') return true;
        } catch (e) {
            // ignore
        }

        try {
            const topPane = document.querySelector('[data-digidig-component="top-pane"]');
            if (topPane && topPane.getAttribute('data-auth-state') === 'authenticated') return true;
        } catch (e) {}

        return false;
    }

    /**
     * Async detection of auth state using server-side session endpoint.
     * Updates internal strategy to 'server' when authenticated.
     */
    async detectAuthStateAsync() {
        try {
            const resp = await fetch('/api/identity/session/verify', { credentials: 'include' });
            if (resp.ok) {
                const userInfo = await resp.json();
                if (userInfo && Object.keys(userInfo).length > 0) {
                    this.isAuthenticated = true;
                    this.strategy = 'server';
                    return true;
                }
            }
        } catch (e) {
            // ignore and keep local strategy
            console.warn('PreferencesManager: failed to probe /api/identity/session/verify', e);
        }
        this.isAuthenticated = false;
        this.strategy = 'local';
        return false;
    }

    /**
     * Get all user preferences
     */
    async getPreferences() {
        if (this.strategy === 'server') {
            try {
                const serverPrefs = await this.getFromServer();
                if (serverPrefs) {
                    // Sync to local storage for fallback
                    this.saveToLocal(serverPrefs);
                    return serverPrefs;
                }
            } catch (error) {
                console.warn('Failed to get server preferences, using local fallback:', error);
            }
        }
        
        return this.getFromLocal();
    }

    /**
     * Set user preferences
     */
    async setPreferences(preferences) {
        // Always save locally first for immediate UI response
        this.saveToLocal(preferences);

        if (this.strategy === 'server') {
            try {
                await this.saveToServer(preferences);
            } catch (error) {
                console.warn('Failed to save server preferences, keeping local only:', error);
            }
        }
    }

    /**
     * Get single preference value
     */
    async getPreference(key) {
        const prefs = await this.getPreferences();
        return prefs[key] !== undefined ? prefs[key] : this.defaults[key];
    }

    /**
     * Set single preference value
     */
    async setPreference(key, value) {
        const currentPrefs = await this.getPreferences();
        const updatedPrefs = { ...currentPrefs, [key]: value };
        await this.setPreferences(updatedPrefs);
    }

    /**
     * Get preferences from Identity server API
     */
    async getFromServer() {
        // First get current user info to know the username
        const sessionResp = await fetch('/api/identity/session/verify', {
            credentials: 'same-origin'
        });
        
        if (!sessionResp.ok) {
            throw new Error(`Not authenticated`);
        }
        
        const session = await sessionResp.json();
        const username = session.username;
        
        // Call the proxy endpoint: /api/identity/users/{username}/preferences
        const response = await fetch(`/api/identity/users/${username}/preferences`, {
            method: 'GET',
            credentials: 'same-origin',
            headers: { 'Accept': 'application/json' }
        });

        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}`);
        }

        // Map server keys (snake_case) to client-facing camelCase for consistency
        const data = await response.json();
        return {
            language: data.language,
            darkMode: data.dark_mode !== undefined ? data.dark_mode : data.darkMode
        };
    }

    /**
     * Save preferences to Identity server API
     */
    async saveToServer(preferences) {
        // First get current user info to know the username
        const sessionResp = await fetch('/api/identity/session/verify', {
            credentials: 'same-origin'
        });
        
        if (!sessionResp.ok) {
            throw new Error(`Not authenticated`);
        }
        
        const session = await sessionResp.json();
        const username = session.username;
        
        // Convert client preference keys to server expected shape (snake_case)
        const payload = {};
        if (preferences.language !== undefined) payload.language = preferences.language;
        if (preferences.darkMode !== undefined) payload.dark_mode = preferences.darkMode;

        const response = await fetch(`/api/identity/users/${username}/preferences`, {
            method: 'PUT',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}`);
        }

        const data = await response.json();
        return {
            language: data.language,
            darkMode: data.dark_mode !== undefined ? data.dark_mode : data.darkMode
        };
    }

    /**
     * Get preferences from local storage with cookie fallback
     */
    getFromLocal() {
        try {
            // Try localStorage first
            const stored = localStorage.getItem('digidig_preferences');
            if (stored) {
                return JSON.parse(stored);
            }
        } catch (error) {
            console.warn('Failed to read from localStorage:', error);
        }

        // Fallback to cookies
        const prefs = { ...this.defaults };
        
        const langCookie = this.getCookie('language');
        if (langCookie) {
            prefs.language = langCookie;
        }

        const darkModeCookie = this.getCookie('dark_mode');
        if (darkModeCookie) {
            prefs.dark_mode = darkModeCookie === 'true';
        }

        return prefs;
    }

    /**
     * Save preferences to local storage and cookies
     */
    saveToLocal(preferences) {
        // Save to localStorage
        try {
            localStorage.setItem('digidig_preferences', JSON.stringify(preferences));
        } catch (error) {
            console.warn('Failed to save to localStorage:', error);
        }

        // Also save to cookies for compatibility
        this.setCookie('language', preferences.language, 365);
        this.setCookie('dark_mode', preferences.dark_mode ? 'true' : 'false', 365);
    }

    /**
     * Cookie utility functions
     */
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    setCookie(name, value, days) {
        const d = new Date();
        d.setTime(d.getTime() + (days * 24 * 60 * 60 * 1000));
        const expires = "expires=" + d.toUTCString();
        document.cookie = name + "=" + value + ";" + expires + ";path=/;SameSite=Lax";
    }

    /**
     * Add event listener for preference changes
     */
    onPreferenceChange(callback) {
        // Listen for localStorage changes (cross-tab sync)
        window.addEventListener('storage', (e) => {
            if (e.key === 'digidig_preferences' && e.newValue) {
                try {
                    const preferences = JSON.parse(e.newValue);
                    callback(preferences);
                } catch (error) {
                    console.warn('Failed to parse preferences from storage event:', error);
                }
            }
        });
    }
}

// Global instance
window.DigiDigPreferences = new PreferencesManager();