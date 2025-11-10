# DIGiDIG Reusable Components

This directory contains reusable UI components for the DIGiDIG microservices system. These components provide consistent user interface elements with adaptive persistence based on authentication state.

## 🏗️ Architecture

The component system is hierarchical:
- **`top-pane`** - Main header component for authenticated services
- **`avatar-dropdown`** - User menu combining preferences and actions
- **`language-selector`** - Language selection component
- **`dark-mode-switch`** - Dark/light theme toggle
- **`shared/`** - Common utilities and persistence management

## 🚀 Quick Start

### Include Dependencies

Add these script tags to your HTML template:

```html
<!-- Include component CSS and JS -->
<link rel="stylesheet" href="/lib/common/components/shared/utils.css">
<link rel="stylesheet" href="/lib/common/components/language-selector/language-selector.css">
<link rel="stylesheet" href="/lib/common/components/dark-mode-switch/dark-mode-switch.css">
<link rel="stylesheet" href="/lib/common/components/avatar-dropdown/avatar-dropdown.css">
<link rel="stylesheet" href="/lib/common/components/top-pane/top-pane.css">

<script src="/lib/common/components/shared/preferences-manager.js"></script>
<script src="/lib/common/components/shared/utils.js"></script>
<script src="/lib/common/components/language-selector/language-selector.js"></script>
<script src="/lib/common/components/dark-mode-switch/dark-mode-switch.js"></script>
<script src="/lib/common/components/avatar-dropdown/avatar-dropdown.js"></script>
<script src="/lib/common/components/top-pane/top-pane.js"></script>
```

### Use Top Pane (For Client, Admin, Apidocs)

```html
<!-- Include the top-pane component HTML -->
<header class="digidig-top-pane" data-digidig-component="top-pane">
    <!-- Component content will be automatically initialized -->
</header>
```

### Use Language Selector Only (For SSO Login Pages)

```html
<div data-digidig-component="language-selector">
    <select class="digidig-language-select">
        <option value="en">English</option>
        <option value="cs">Čeština</option>
    </select>
</div>
```

## 📦 Component Reference

### Top Pane Component

Main header component for authenticated services.

**Options:**
- `title: string` - Service title
- `logoText: string` - Logo text (default: "DIGiDIG")
- `size: 'compact'|'default'|'large'` - Size variant
- `layout: 'default'|'minimal'|'no-center'|'no-nav'` - Layout variant

**Events:**
- `digidig:top-pane:ready`
- `digidig:top-pane:auth-state-change`
- `digidig:top-pane:language-change`
- `digidig:top-pane:theme-change`

### Avatar Dropdown Component

User menu with preferences and actions.

**Options:**
- `size: 'small'|'default'|'large'` - Size variant
- `compact: boolean` - Hide user name
- `responsive: boolean` - Mobile bottom sheet
- `logoutUrl: string` - Logout URL

**Events:**
- `digidig:avatar-dropdown:ready`
- `digidig:avatar-dropdown:open`
- `digidig:avatar-dropdown:close`
- `digidig:avatar-dropdown:language-change`
- `digidig:avatar-dropdown:theme-change`

### Language Selector Component

Language selection dropdown.

**Options:**
- `size: 'small'|'default'|'large'` - Size variant
- `showLabel: boolean` - Show label text
- `reloadOnChange: boolean` - Reload page on change

**Events:**
- `digidig:language-selector:ready`
- `digidig:language-selector:change`
- `digidig:language-selector:error`

### Dark Mode Switch Component

Dark/light theme toggle switch.

**Options:**
- `size: 'small'|'default'|'large'` - Size variant
- `showLabel: boolean` - Show label text
- `labelText: string` - Label text
- `applyTheme: boolean` - Apply theme to document

**Events:**
- `digidig:dark-mode-switch:ready`
- `digidig:dark-mode-switch:change`
- `digidig:dark-mode-switch:error`

## 🔧 Adaptive Persistence

Components automatically detect authentication state and use appropriate persistence:

- **Authenticated Users**: Preferences saved to Identity API (`/api/user/preferences`) with localStorage fallback
- **Anonymous Users**: Preferences saved to localStorage with cookie fallback

## 🎨 Theming

Components use CSS variables for theming:

```css
:root {
    --text-color: #374151;
    --input-border: #d1d5db;
    --input-bg: #ffffff;
    --input-focus: #3b82f6;
}

[data-theme="dark"] {
    --text-color: #f9fafb;
    --input-border: #4b5563;
    --input-bg: #374151;
}
```

## 📱 Responsive Design

All components are mobile-friendly:
- Dropdowns become bottom sheets on mobile
- Logo text hides on small screens
- Touch-friendly interaction areas

## ♿ Accessibility

Components include:
- Full ARIA support
- Keyboard navigation
- Focus management
- High contrast mode support
- Screen reader compatibility

## 🔄 Migration Guide

### From Client Service

Replace existing dropdown in `services/client/src/templates/layout.html`:

```html
<!-- Replace this -->
<div class="user-dropdown">...</div>

<!-- With this -->
<header class="digidig-top-pane" data-digidig-component="top-pane">
    <!-- Component will auto-initialize -->
</header>
```

### From Admin Service

Replace broken dropdown in `services/admin/src/templates/base.html`:

```html
<!-- Replace this -->
<div class="admin-header">...</div>

<!-- With this -->
<header class="digidig-top-pane" data-digidig-component="top-pane">
    <!-- Component will auto-initialize -->
</header>
```

### From Apidocs Service

Replace inline selectors in `services/apidocs/src/templates/index.html`:

```html
<!-- Replace this -->
<select id="language">...</select>

<!-- With this -->
<header class="digidig-top-pane" data-digidig-component="top-pane">
    <!-- Component will auto-initialize -->
</header>
```

### For SSO Service

Add to login page in `services/sso/src/templates/login.html`:

```html
<!-- Add this where current language selector is -->
<div data-digidig-component="language-selector">
    <select class="digidig-language-select">
        <option value="en">English</option>
        <option value="cs">Čeština</option>
    </select>
</div>
```

## 🧪 Testing

Components include:
- Unit tests for core functionality
- Integration tests for persistence
- Cross-browser compatibility tests
- Accessibility compliance tests

## 🐛 Troubleshooting

### Component Not Initializing

1. Check console for JavaScript errors
2. Ensure all dependencies are loaded
3. Verify HTML structure matches expected format
4. Check `data-digidig-component` attribute

### Preferences Not Persisting

1. Check authentication state detection
2. Verify Identity API endpoint is accessible
3. Check localStorage is available
4. Verify cookie settings

### Styling Issues

1. Ensure CSS is loaded after dependencies
2. Check for CSS variable conflicts
3. Verify theme attribute is set correctly
4. Check for CSS specificity issues

## 📚 API Reference

### PreferencesManager

```javascript
// Get preference
const language = await DigiDigPreferences.getPreference('language');

// Set preference
await DigiDigPreferences.setPreference('language', 'cs');

// Listen for changes
DigiDigPreferences.onPreferenceChange((preferences) => {
    console.log('Preferences changed:', preferences);
});
```

### Component Utils

```javascript
// Create component manually
const component = DigiDigUtils.Component.createComponent(
    DigiDigLanguageSelector, 
    element, 
    options
);

// Cleanup component
DigiDigUtils.DOM.cleanup(element);
```

## 🔗 Related Documentation

- [DIGiDIG Configuration System](../../_doc/CONFIGURATION.md)
- [Service Architecture](../../_doc/PROJECT-RESTRUCTURE.md)
- [Testing Guide](../../_doc/TESTING.md)