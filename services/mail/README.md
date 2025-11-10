# DIGiDIG Mail Client App

A client-side web application for DIGiDIG email management.

## Features

- **Email Composition**: Write and send new emails
- **Inbox Management**: View received emails
- **SSO Authentication**: Secure login via SSO service
- **Multi-language Support**: English and Czech translations
- **Dark/Light Mode**: User preference for theme switching
- **Responsive Design**: Works on desktop and mobile devices

## Architecture

This is a client application that communicates directly with DIGiDIG microservices:

- **SMTP Service**: Email sending
- **IMAP Service**: Email retrieval protocol
- **Storage Service**: Email storage and retrieval
- **Identity Service**: User authentication
- **SSO Service**: Single sign-on authentication

## API Endpoints

The app exposes only basic monitoring endpoints:

- `GET /health` - Health check
- `GET /stats` - Basic statistics
- `GET /logs` - Application logs

## Configuration

Configuration is stored in `config/config.yaml`:

```yaml
app:
  name: "DIGiDIG Mail Client"
  version: "1.0.0"
  port: 9107

services:
  smtp: "http://10.1.1.26:8000"
  imap: "http://10.1.1.26:8003"
  storage: "http://10.1.1.26:8002"
  # ... other services
```

## Running the Application

```bash
cd services/mail/src
python app.py
```

The app will be available at `http://10.1.1.26:9107`

## Authentication Flow

1. User accesses mail app
2. If not authenticated, redirect to SSO service
3. SSO authenticates user and redirects back with token
4. Mail app verifies token with Identity service
5. User can access email functions

## Development

### Project Structure

```
src/
├── app.py                 # FastAPI application
├── templates/
│   ├── layout.html       # Main layout with top/left/right panes
│   └── pages/
│       ├── compose.html  # Email composition page
│       └── list.html     # Email list/inbox page
└── static/
    ├── css/
    │   ├── layout.css   # Main layout styles
    │   ├── compose.css  # Compose-specific styles
    │   └── list.css     # List-specific styles
    └── js/
        ├── app.js       # Main app JavaScript
        ├── compose.js   # Email composition logic
        └── list.js      # Email list logic
```

### Reusable Components

The app uses shared components from `lib/common/components/`:

- **Top Pane**: Header with logo, user avatar dropdown, language/theme switchers
- **Language Selector**: Language switching functionality
- **Dark Mode Switch**: Theme switching functionality
- **Avatar Dropdown**: User menu with preferences and logout
- **Preferences Manager**: Client-side preference persistence

### Internationalization

Translations are loaded from `locales/` directory:

- `locales/en/common.json` - Common English translations
- `locales/cs/common.json` - Common Czech translations
- `locales/en/client.json` - Mail-specific English translations
- `locales/cs/client.json` - Mail-specific Czech translations

## Security

- JWT token verification with Identity service
- HttpOnly cookies for token storage
- Direct service communication (no proxy)
- CSRF protection on forms