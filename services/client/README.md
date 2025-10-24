# Client Service

Klientské webové rozhraní pro koncové uživatele DIGiDIG emailového systému.

## Popis

Client služba poskytuje webové rozhraní pro běžné uživatele, kde mohou:
- Přihlásit se do svého účtu
- Zobrazit přijaté e-maily
- Odesílat nové e-maily
- Spravovat svou schránku

## Technologie

- **FastAPI** - Python async web framework
- **Jinja2** - Templating engine pro HTML
- **aiohttp** - Async HTTP klient pro komunikaci s backendem
- **JWT** - Autentizace pomocí tokenů z Identity služby

## API Endpoints

### Web Interface
- `GET /` - Login stránka
- `POST /login` - Přihlášení uživatele
- `GET /dashboard` - Hlavní dashboard s přehledem e-mailů
- `POST /send` - Odeslání nového e-mailu

## Environment Variables

```env
CLIENT_PORT=8004                   # Port FastAPI aplikace
IDENTITY_URL=http://identity:8001  # URL Identity služby pro autentizaci
SMTP_URL=http://smtp:8000          # URL SMTP služby pro odesílání
STORAGE_URL=http://storage:8002    # URL Storage služby pro načítání e-mailů
JWT_SECRET=your_secret_key         # Sdílený secret s Identity službou
```

## Vývoj

### Spuštění služby
```bash
# Pomocí Docker Compose
make up client

# Full rebuild (po změnách v kódu)
make refresh client

# Restart (pro změny v templates/static)
make clear-cache-view client
```

### Testování
```bash
# Health check
curl http://localhost:8004/

# Login (simulace)
curl -X POST http://localhost:8004/login \
  -d "email=user@example.com&password=password"

# Odeslání e-mailu
curl -X POST http://localhost:8004/send \
  -d "recipient=test@example.com&subject=Hello&body=Test message"
```

## Struktura projektu

```
client/
├── Dockerfile              # Docker image definice
├── requirements.txt        # Python závislosti
├── src/
│   ├── client.py          # Hlavní aplikace
│   ├── static/            # CSS, JS, obrázky
│   │   ├── css/
│   │   │   └── styles.css
│   │   └── js/
│   │       └── scripts.js
│   └── templates/         # Jinja2 templates
│       ├── login.html     # Přihlašovací stránka
│       └── index.html     # Dashboard s e-maily
└── README.md
```

## UI Features

### Login Page
- Email a heslo autentizace
- Redirect na dashboard po úspěšném přihlášení
- Error handling pro neplatné přihlašovací údaje

### Dashboard
- Seznam přijatých e-mailů
- Formulář pro odeslání nového e-mailu
- Responzivní design
- Session management

## Security

- Session-based autentizace
- Integrace s Identity službou pro validaci credentials
- Protected routes vyžadují aktivní session

## Závislosti na dalších službách

- **Identity** - Pro autentizaci uživatelů
- **SMTP** - Pro odesílání e-mailů
- **Storage** - Pro načítání přijatých e-mailů
- **IMAP** - Pro synchronizaci mailboxu (budoucí integrace)

## Poznámky

- Aktuálně používá simulovanou autentizaci (admin@example.com/admin)
- Pro produkční použití je potřeba implementovat plnou integraci s Identity službou
- E-maily se zatím načítají simulovaně - je potřeba implementovat fetch ze Storage API
- Browser cache může blokovat změny v templates - použij `Ctrl+Shift+R` pro hard refresh
