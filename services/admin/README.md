# DIGiDIG Admin Client App

A client-side web application for DIGiDIG system administration.

## Features

- **Domain Management**: Create, edit, and delete email domains
- **Service Monitoring**: View health status of all DIGiDIG services
- **SSO Authentication**: Secure login via SSO service
- **Multi-language Support**: English and Czech translations
- **Dark/Light Mode**: User preference for theme switching
- **Responsive Design**: Works on desktop and mobile devices

## Architecture

This is a client application that communicates directly with DIGiDIG microservices:

- **Identity Service**: User authentication and domain management
- **SSO Service**: Single sign-on authentication
- **SMTP/IMAP/Storage Services**: Service health monitoring

## API Endpoints

The app exposes only basic monitoring endpoints:

- `GET /health` - Health check
- `GET /stats` - Basic statistics
- `GET /logs` - Application logs

## Configuration

Configuration is stored in `config/config.yaml`:

```yaml
app:
  name: "DIGiDIG Admin Client"
  port: 9105

services:
  identity: "http://10.1.1.26:8001"
  sso: "http://10.1.1.26:8006"
  # ... other services
```

## Running the Application

```bash
cd services/admin-new/src
python app.py
```

The app will be available at `http://localhost:9105`

## Authentication Flow

1. User accesses admin app
2. If not authenticated, redirect to SSO service
3. SSO authenticates user and redirects back with token
4. Admin app verifies token with Identity service
5. User can access admin functions

## Development

### Project Structure

```
src/
├── app.py                 # FastAPI application
├── templates/
│   ├── layout.html       # Main layout with top/left/right panes
│   └── pages/
│       ├── domains.html  # Domain management page
│       └── services.html # Service monitoring page
└── static/
    ├── css/
    │   ├── layout.css   # Main layout styles
    │   ├── domains.css  # Domain-specific styles
    │   └── services.css # Service-specific styles
    └── js/
        ├── app.js       # Main app JavaScript
        ├── domains.js   # Domain management logic
        └── services.js  # Service monitoring logic
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
- `locales/en/admin.json` - Admin-specific English translations
- `locales/cs/admin.json` - Admin-specific Czech translations

## Security

- JWT token verification with Identity service
- HttpOnly cookies for token storage
- Direct service communication (no proxy)
- CSRF protection on forms