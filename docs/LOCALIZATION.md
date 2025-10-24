# Localization (i18n) System

## Overview

DIGiDIG supports multiple languages through a comprehensive internationalization (i18n) system. This document describes the architecture, usage, and contribution guidelines for translations.

## Supported Languages

- **English (en)** - Default language
- **Czech (cs)** - Čeština

## Architecture

### Components

1. **common/i18n.py** - Core i18n module
2. **locales/** - Translation files directory
   ```
   locales/
   ├── en/              # English translations
   │   ├── common.json  # Common texts (buttons, errors, etc.)
   │   ├── admin.json   # Admin service
   │   ├── client.json  # Client service
   │   ├── identity.json
   │   ├── storage.json
   │   ├── smtp.json
   │   └── imap.json
   └── cs/              # Czech translations
       ├── common.json
       ├── admin.json
       └── ... (same structure)
   ```

### Translation File Format

JSON files with nested structure:

```json
{
  "section": {
    "key": "Translated text",
    "with_params": "Hello {username}!"
  }
}
```

Keys use dot notation: `section.key`

## Usage

### Backend (Python)

```python
from common.i18n import init_i18n, get_i18n, t

# Initialize i18n for a service
i18n = init_i18n(default_language='en', service_name='client')

# Get translation
text = i18n.get('login.title')  # Returns: "Login"

# With parameters
text = i18n.get('admin.welcome', username='John')  
# Returns: "Welcome, John!"

# Change language
i18n.set_language('cs')

# Shorthand function
text = t('common.save')  # Returns: "Save"
```

### Frontend (JavaScript)

Client-side translations are embedded in templates:

```javascript
const translations = {
    en: {
        loginTitle: 'Login',
        welcome: 'Welcome, {username}!'
    },
    cs: {
        loginTitle: 'Přihlášení',
        welcome: 'Vítejte, {username}!'
    }
};

// Get current language from cookie
const lang = getCookie('language') || 'en';

// Update UI
document.getElementById('title').textContent = translations[lang].loginTitle;
```

### Language Selection

Users can change language via dropdown selector in the UI:

1. **Client Service**: Language selector in header
2. **Admin Service**: Language selector in navigation
3. **Selection is persistent**: Stored in httponly cookie (1 year)

## API Endpoints

### Set Language

```http
POST /api/language
Content-Type: application/x-www-form-urlencoded

lang=cs
```

### Get Translations

```http
GET /api/translations
Cookie: language=cs
```

Response:
```json
{
  "common.save": "Uložit",
  "common.cancel": "Zrušit",
  "login.title": "Přihlášení",
  ...
}
```

## Translation Keys

### Common Keys (locales/{lang}/common.json)

```
app.name                  - Application name
app.tagline              - Application tagline
common.yes               - Yes button
common.no                - No button
common.save              - Save button
common.cancel            - Cancel button
auth.login               - Login text
auth.logout              - Logout text
auth.username            - Username label
auth.password            - Password label
errors.generic           - Generic error message
errors.network           - Network error
date.today               - Today
language.select          - Language selector label
```

### Service-Specific Keys

Each service has its own translation file (e.g., `client.json`, `admin.json`) with service-specific keys.

## Adding New Languages

1. **Create language directory**:
   ```bash
   mkdir -p locales/de  # For German
   ```

2. **Copy English templates**:
   ```bash
   cp locales/en/*.json locales/de/
   ```

3. **Translate content**:
   Edit each JSON file with translated texts.

4. **Update i18n.py**:
   Add language code to `SUPPORTED_LANGUAGES`:
   ```python
   SUPPORTED_LANGUAGES = ['cs', 'en', 'de']
   ```

5. **Add to UI selectors**:
   Update language dropdowns in templates:
   ```html
   <option value="de">Deutsch</option>
   ```

## Adding New Translation Keys

1. **Add to English file**:
   ```json
   {
     "new_section": {
       "new_key": "New text in English"
     }
   }
   ```

2. **Add to all other languages**:
   Translate the same key in all `locales/{lang}/*.json` files.

3. **Use in code**:
   ```python
   text = i18n.get('new_section.new_key')
   ```

## Best Practices

### Translation Quality

1. **Context Matters**: Provide context for translators
2. **Consistency**: Use same terms consistently
3. **Placeholders**: Use `{param}` for dynamic values
4. **Punctuation**: Include proper punctuation
5. **Cultural Adaptation**: Adapt to local conventions

### Technical Guidelines

1. **Key Naming**:
   - Use dot notation: `section.subsection.key`
   - Lowercase with underscores: `email.mark_read`
   - Descriptive names: `login.button` not `lb1`

2. **Parameters**:
   ```json
   "welcome": "Welcome, {username}!"
   ```
   Use: `i18n.get('welcome', username='John')`

3. **Fallback**:
   - Always provide English translation
   - System falls back to English if translation missing

4. **Testing**:
   - Test all supported languages
   - Verify parameter substitution
   - Check UI layout with longer texts

## Current Translation Status

| Language | Code | Status | Coverage |
|----------|------|--------|----------|
| English  | en   | ✅ Complete | 100% |
| Czech    | cs   | ✅ Complete | 100% |

## Contributing Translations

1. Fork the repository
2. Add/update translation files in `locales/{lang}/`
3. Test with `make test`
4. Submit pull request

### Translation Checklist

- [ ] All JSON files are valid
- [ ] No missing keys compared to English
- [ ] Parameters match English version
- [ ] Text tested in UI
- [ ] Cultural appropriateness verified

## Troubleshooting

### Translation Not Showing

1. Check language is supported in `i18n.SUPPORTED_LANGUAGES`
2. Verify JSON file syntax is valid
3. Ensure key exists in translation file
4. Check browser console for errors
5. Verify cookie is set correctly

### Missing Translations

System automatically falls back to English. Check logs:

```
WARNING: Translation not found for key: login.title (lang: cs)
```

## Examples

### Complete Login Page

```python
# Backend (client.py)
from common.i18n import init_i18n

i18n = init_i18n(default_language='en', service_name='client')

@app.get("/")
async def login(request: Request):
    lang = request.cookies.get("language", "en")
    i18n.set_language(lang)
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "title": i18n.get("login.title"),
        "subtitle": i18n.get("login.subtitle")
    })
```

```html
<!-- Frontend (login.html) -->
<script>
const translations = {
    en: { title: 'Login', subtitle: 'Sign in to your account' },
    cs: { title: 'Přihlášení', subtitle: 'Přihlaste se do svého účtu' }
};

function updateUI(lang) {
    const t = translations[lang];
    document.getElementById('title').textContent = t.title;
    document.getElementById('subtitle').textContent = t.subtitle;
}

// Initialize
const currentLang = getCookie('language') || 'en';
updateUI(currentLang);
</script>
```

## Future Enhancements

- [ ] Pluralization support
- [ ] Number formatting per locale
- [ ] Date/time formatting per locale
- [ ] RTL language support
- [ ] Translation management UI
- [ ] Automatic translation via API
- [ ] Translation validation tools

## References

- [Mozilla i18n Guide](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Internationalization)
- [FastAPI i18n](https://fastapi.tiangolo.com/)
- [JSON Schema](https://json-schema.org/)
