# DIGiDIG Test Suite Service

Test suite for DIGiDIG UI components with automated testing and demonstration.

## Features

- **Component Testing**: Automated testing of all DIGiDIG UI components
- **Auto-login**: Automatically logs in with test user (admin@example.com)
- **Real-time Testing**: Live test results and component status
- **Component Showcase**: Demonstrates all available components

## Components Tested

- ✅ Language Selector
- ✅ Dark Mode Switch
- ✅ Avatar Dropdown
- ✅ Top Pane
- ✅ Preferences Manager

## Usage

### Start Service

```bash
make up components-test
```

### Access Test Suite

Open `http://localhost:8008` in your browser.

The service will automatically:
1. Log in with the test user from config
2. Load all components
3. Run automated tests
4. Display results in real-time

## API Endpoints

- `GET /` - Main test suite page
- `GET /health` - Health check

## Configuration

The service uses the same configuration as other DIGiDIG services:

- Test user: `security.admin.email` and `security.admin.password`
- Identity service URL: `services.identity.url`

## Development

### Build

```bash
docker compose build components-test
```

### Logs

```bash
docker compose logs -f components-test
```

### Restart

```bash
docker compose restart components-test
```