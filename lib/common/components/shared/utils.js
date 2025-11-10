/**
 * DIGiDIG Component Utilities
 * 
 * Common helper functions for UI components
 */

/**
 * DOM utilities
 */
const DOMUtils = {
    /**
     * Create element with attributes and content
     */
    createElement(tag, attributes = {}, content = '') {
        const element = document.createElement(tag);
        
        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'dataset') {
                Object.entries(value).forEach(([dataKey, dataValue]) => {
                    element.dataset[dataKey] = dataValue;
                });
            } else {
                element.setAttribute(key, value);
            }
        });
        
        if (content) {
            if (typeof content === 'string') {
                element.innerHTML = content;
            } else {
                element.appendChild(content);
            }
        }
        
        return element;
    },

    /**
     * Add event listener with cleanup tracking
     */
    addEventListenerWithCleanup(element, event, handler, options = {}) {
        element.addEventListener(event, handler, options);
        
        // Store cleanup function for later
        if (!element._digidigCleanupFns) {
            element._digidigCleanupFns = [];
        }
        element._digidigCleanupFns.push(() => {
            element.removeEventListener(event, handler, options);
        });
    },

    /**
     * Debounce helper - returns a debounced function that delays invocation
     * of `fn` until `wait` milliseconds have elapsed since the last call.
     */
    debounce(fn, wait = 100) {
        let timeout = null;
        return function(...args) {
            const ctx = this;
            if (timeout) clearTimeout(timeout);
            timeout = setTimeout(() => {
                timeout = null;
                try { fn.apply(ctx, args); } catch (e) { console.error('debounced fn error', e); }
            }, wait);
        };
    },

    /**
     * Cleanup all event listeners for element
     */
    cleanup(element) {
        if (element._digidigCleanupFns) {
            element._digidigCleanupFns.forEach(cleanup => cleanup());
            element._digidigCleanupFns = [];
        }
    }
};

/**
 * CSS utilities
 */
const CSSUtils = {
    /**
     * Apply CSS variables to element
     */
    applyVariables(element, variables) {
        Object.entries(variables).forEach(([key, value]) => {
            element.style.setProperty(key, value);
        });
    },

    /**
     * Toggle CSS class with transition support
     */
    toggleClass(element, className, force = null) {
        if (force !== null) {
            element.classList.toggle(className, force);
        } else {
            element.classList.toggle(className);
        }
    },

    /**
     * Add CSS with scoped variables
     */
    addScopedCSS(cssText, scopeId) {
        const style = document.createElement('style');
        style.id = `digidig-component-${scopeId}`;
        style.textContent = cssText;
        
        // Only add if not already present
        if (!document.getElementById(style.id)) {
            document.head.appendChild(style);
        }
        
        return style;
    }
};

/**
 * Component lifecycle utilities
 */
const ComponentUtils = {
    /**
     * Initialize component with standard lifecycle
     */
    async initializeComponent(componentName, element, options = {}) {
        try {
            // Add component identifier
            element.setAttribute('data-digidig-component', componentName);
            
            // Initialize preferences if needed
            if (options.usePreferences) {
                await window.DigiDigPreferences.getPreferences();
            }
            
            // Add cleanup on page unload
            window.addEventListener('beforeunload', () => {
                DOMUtils.cleanup(element);
            });
            
            console.debug(`DigiDIG component ${componentName} initialized`);
            
        } catch (error) {
            console.error(`Failed to initialize component ${componentName}:`, error);
            throw error;
        }
    },

    /**
     * Create component instance with error handling
     */
    createComponent(ComponentClass, element, options = {}) {
        try {
            const instance = new ComponentClass(element, options);
            
            // Store instance on element for debugging
            element._digidigComponent = instance;
            
            return instance;
        } catch (error) {
            console.error(`Failed to create component ${ComponentClass.name}:`, error);
            throw error;
        }
    }
};

/**
 * Validation utilities
 */
const ValidationUtils = {
    /**
     * Validate language code
     */
    isValidLanguage(lang) {
        const supportedLanguages = ['en', 'cs'];
        return supportedLanguages.includes(lang);
    },

    /**
     * Validate boolean preference
     */
    isValidBoolean(value) {
        return typeof value === 'boolean' || value === 'true' || value === 'false';
    },

    /**
     * Sanitize preference value
     */
    sanitizePreference(key, value) {
        switch (key) {
            case 'language':
                return this.isValidLanguage(value) ? value : 'en';
            case 'dark_mode':
                if (typeof value === 'string') {
                    return value === 'true';
                }
                return Boolean(value);
            default:
                return value;
        }
    }
};

/**
 * Animation utilities
 */
const AnimationUtils = {
    /**
     * Smooth fade transition
     */
    fade(element, direction = 'toggle', duration = 300) {
        return new Promise(resolve => {
            const isHidden = element.style.opacity === '0' || element.classList.contains('hidden');
            
            let targetOpacity;
            if (direction === 'toggle') {
                targetOpacity = isHidden ? '1' : '0';
            } else if (direction === 'in') {
                targetOpacity = '1';
            } else {
                targetOpacity = '0';
            }
            
            element.style.transition = `opacity ${duration}ms ease`;
            element.style.opacity = targetOpacity;
            
            setTimeout(() => {
                if (targetOpacity === '0') {
                    element.classList.add('hidden');
                } else {
                    element.classList.remove('hidden');
                }
                resolve();
            }, duration);
        });
    },

    /**
     * Slide animation
     */
    slide(element, direction = 'toggle', duration = 300) {
        return new Promise(resolve => {
            const isHidden = element.classList.contains('hidden');
            
            if (direction === 'toggle') {
                direction = isHidden ? 'down' : 'up';
            }
            
            if (direction === 'down') {
                element.classList.remove('hidden');
                element.style.maxHeight = '0px';
                element.style.overflow = 'hidden';
                element.style.transition = `max-height ${duration}ms ease`;
                
                setTimeout(() => {
                    element.style.maxHeight = element.scrollHeight + 'px';
                }, 10);
                
                setTimeout(() => {
                    element.style.maxHeight = '';
                    element.style.overflow = '';
                    element.style.transition = '';
                    resolve();
                }, duration);
            } else {
                element.style.maxHeight = element.scrollHeight + 'px';
                element.style.overflow = 'hidden';
                element.style.transition = `max-height ${duration}ms ease`;
                
                setTimeout(() => {
                    element.style.maxHeight = '0px';
                }, 10);
                
                setTimeout(() => {
                    element.classList.add('hidden');
                    element.style.maxHeight = '';
                    element.style.overflow = '';
                    element.style.transition = '';
                    resolve();
                }, duration);
            }
        });
    }
};

// Export utilities
window.DigiDigUtils = {
    DOM: DOMUtils,
    CSS: CSSUtils,
    Component: ComponentUtils,
    Validation: ValidationUtils,
    Animation: AnimationUtils
};