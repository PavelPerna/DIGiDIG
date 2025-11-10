/**
 * DIGiDIG Main Namespace and Component Registry
 *
 * This file defines the global DigiDig namespace and provides
 * initialization methods for all components.
 */

// Initialize DigiDig namespace
window.DigiDig = window.DigiDig || {};

// Component registry - components register themselves here
DigiDig.components = DigiDig.components || {};

// Utility function to register components
DigiDig.registerComponent = function(name, componentClass, initFunction) {
    DigiDig.components[name] = {
        class: componentClass,
        init: initFunction
    };
};

// Global initialization functions
DigiDig.init = function() {
    console.log('DIGiDIG: Initializing all components');

    // Initialize in dependency order
    if (DigiDig.TopPane && DigiDig.TopPane.init) {
        DigiDig.TopPane.init();
    }

    if (DigiDig.LanguageSelector && DigiDig.LanguageSelector.init) {
        DigiDig.LanguageSelector.init();
    }

    if (DigiDig.DarkModeSwitch && DigiDig.DarkModeSwitch.init) {
        DigiDig.DarkModeSwitch.init();
    }

    if (DigiDig.AvatarDropdown && DigiDig.AvatarDropdown.init) {
        DigiDig.AvatarDropdown.init();
    }
};

// Auto-initialize on DOM ready if DigiDig.init is called
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        // Only auto-init if not manually initialized
        if (!window.DigiDig._initialized) {
            DigiDig.init();
            window.DigiDig._initialized = true;
        }
    });
} else if (!window.DigiDig._initialized) {
    DigiDig.init();
    window.DigiDig._initialized = true;
}

console.log('DIGiDIG: Main namespace initialized');