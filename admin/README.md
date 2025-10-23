# Admin Service

Admin webové rozhraní pro správu DIGiDIG systému.

## Popis

Admin služba poskytuje webové rozhraní pro administrátory systému, kde mohou:
- Spravovat domény
- Monitorovat a konfigurovat mikroservisy (SMTP, IMAP, Storage, Identity)
- Zobrazovat statistiky služeb
- Restartovat SMTP server

## Technologie

- **FastAPI** - Python async web framework
- **Jinja2** - Templating engine pro HTML
- **aiohttp** - Async HTTP klient pro komunikaci s dalšími službami
- **JWT** - Autentizace pomocí tokenů z Identity služby

## API Endpoints

### Web Interface
- `GET /` - Login stránka nebo dashboard (s tokenem)
- `POST /api/login` - Přihlášení uživatele (vrací JWT token)
- `POST /logout` - Odhlášení uživatele
- `GET /services` - Správa služeb (vyžaduje token)

### Service Management API
- `GET /api/services` - Seznam všech služeb a jejich stavu
- `GET /api/services/{service_name}/stats` - Statistiky konkrétní služby
- `GET /api/services/{service_name}/config` - Konfigurace služby
- `PUT /api/services/{service_name}/config` - Aktualizace konfigurace služby
- `POST /api/services/{service_name}/restart` - Restart služby (pouze SMTP)

### Domain Management API
- `GET /api/domains` - Seznam domén
- `POST /api/domains` - Vytvoření nové domény
- `DELETE /api/domains/{domain_id}` - Smazání domény

## Environment Variables

```env
ADMIN_PORT=8005                    # Port FastAPI aplikace
IDENTITY_URL=http://identity:8001  # URL Identity služby
SMTP_URL=http://smtp:8000          # URL SMTP služby
IMAP_URL=http://imap:8003          # URL IMAP služby
STORAGE_URL=http://storage:8002    # URL Storage služby
JWT_SECRET=your_secret_key         # Sdílený secret s Identity službou
```

## Vývoj

### Spuštění služby
```bash
# Pomocí Docker Compose
make up admin

# Full rebuild (po změnách v kódu)
make refresh admin

# Restart (pro změny v templates/static)
make clear-cache-view admin
```

### Testování
```bash
# Health check
curl http://localhost:8005/api/health

# Login
curl -X POST http://localhost:8005/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin"}'

# Seznam služeb (s tokenem)
curl http://localhost:8005/api/services \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Struktura projektu

```
admin/
├── Dockerfile              # Docker image definice
├── requirements.txt        # Python závislosti
├── src/
│   ├── admin.py           # Hlavní aplikace
│   ├── static/            # CSS, JS, obrázky
│   │   ├── css/
│   │   │   ├── styles.css         # Globální styly
│   │   │   ├── datagrid.css       # Layout a komponenty
│   │   │   └── password-validation.css
│   │   └── js/
│   └── templates/         # Jinja2 templates
│       ├── login.html
│       ├── dashboard.html
│       └── services.html
└── tests/
    └── integration_test.py
```

## UI Features

### Dashboard
- Správa domén (přidání, smazání)
- Avatar dropdown s logout akcí
- Responzivní dark mode design

### Services Page
- Grid zobrazení všech služeb (SMTP, IMAP, Storage, Identity)
- Real-time status indikátory (healthy/unhealthy/unreachable)
- Uptime statistiky
- Modální dialogy pro detailní statistiky a konfiguraci
- Restart tlačítko pro SMTP server

## Security

- Všechny chráněné endpointy vyžadují JWT token
- Token validace proti Identity službě
- Session management s logout funkcionalitou
- Password hidden v konfiguračních dialozích

## Závislosti na dalších službách

- **Identity** - Pro autentizaci a autorizaci uživatelů
- **SMTP** - Pro správu SMTP serveru a konfiguraci
- **IMAP** - Pro monitoring IMAP služby
- **Storage** - Pro monitoring Storage služby

## Poznámky

- Default admin účet: `admin@example.com` / `admin`
- Token expiruje za 1 hodinu (nastavitelné přes Identity)
- Browser cache může blokovat změny v templates - použij `Ctrl+Shift+R` pro hard refresh
