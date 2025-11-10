# API Endpoints Documentation

**Vygenerováno:** 2025-11-09  
**Projekt:** DIGiDIG Email Platform

## Architektura

Všechny REST API endpointy jsou pod prefixem `/api/`. Client routes (HTML stránky) jsou bez tohoto prefixu.

### Proxy Mapping

ServiceClient automaticky proxuje requesty na jednotlivé služby:

```
/api/{service}/{path} → http://{service}:port/api/{path}
```

**Příklady:**
- `/api/identity/logout` → `http://identity:9101/api/logout`
- `/api/identity/session/verify` → `http://identity:9101/api/session/verify`
- `/api/identity/users/admin/preferences` → `http://identity:9101/api/users/admin/preferences`
- `/api/smtp/send` → `http://smtp:9100/api/send`
- `/api/storage/emails` → `http://storage:9102/api/emails`
- `/api/imap/emails` → `http://imap:9103/api/emails`

---

## REST API Endpointy

### Identity Service (port 9101)

#### Authentication
| Method | Endpoint | Popis |
|--------|----------|-------|
| POST | `/api/register` | Registrace nového uživatele |
| POST | `/api/login` | Přihlášení uživatele |
| POST | `/api/logout` | Odhlášení uživatele |
| GET | `/api/verify` | Verifikace tokenu (GET) |
| POST | `/api/verify` | Verifikace tokenu (POST) |
| GET | `/api/session/verify` | Verifikace session z cookie |

#### Tokens
| Method | Endpoint | Popis |
|--------|----------|-------|
| POST | `/api/tokens/refresh` | Refresh access token |
| POST | `/api/tokens/revoke` | Zneplatnění tokenu |

#### Users
| Method | Endpoint | Popis |
|--------|----------|-------|
| GET | `/api/users` | Seznam všech uživatelů |
| PUT | `/api/users` | Vytvořit/aktualizovat uživatele |
| DELETE | `/api/users/{user_id}` | Smazat uživatele |
| GET | `/api/users/{username}/preferences` | Načíst preference uživatele |
| PUT | `/api/users/{username}/preferences` | Uložit preference uživatele |

**Poznámka:** Preference endpointy vyžadují autentizaci. Uživatel může přistupovat pouze ke svým vlastním preferencím, pokud není admin.

#### Domains
| Method | Endpoint | Popis |
|--------|----------|-------|
| GET | `/api/domains` | Seznam všech domén |
| POST | `/api/domains` | Vytvořit novou doménu |
| DELETE | `/api/domains/{domain_name}` | Smazat doménu |
| POST | `/api/domains/rename` | Přejmenovat doménu |
| GET | `/api/domains/{domain}/exists` | Zkontrolovat existenci domény |

#### Metadata & Monitoring
| Method | Endpoint | Popis |
|--------|----------|-------|
| GET | `/api/config` | Konfigurace služby |
| PUT | `/api/config` | Upravit konfiguraci |
| GET | `/api/stats` | Statistiky služby |
| GET | `/api/health` | Health check |
| GET | `/api/identity/sessions` | Seznam aktivních sessions |

#### OAuth
| Method | Endpoint | Popis |
|--------|----------|-------|
| GET | `/api/oauth/{provider}/callback` | OAuth callback endpoint |

#### RSA
| Method | Endpoint | Popis |
|--------|----------|-------|
| GET | `/api/rsa/public-key/{realm}` | Získat veřejný RSA klíč pro realm |

---

### SMTP Service (port 9100)

| Method | Endpoint | Popis |
|--------|----------|-------|
| POST | `/api/send` | Odeslat email |

**Request Body:**
```json
{
  "to": "recipient@example.com",
  "subject": "Subject",
  "body": "Email content",
  "from": "sender@example.com"
}
```

---

### Storage Service (port 9102)

| Method | Endpoint | Popis |
|--------|----------|-------|
| POST | `/api/emails` | Uložit email do MongoDB |
| GET | `/api/health` | Health check |

---

### IMAP Service (port 9103)

| Method | Endpoint | Popis |
|--------|----------|-------|
| GET | `/api/emails` | Načíst seznam emailů |
| GET | `/api/config` | Konfigurace IMAP služby |
| PUT | `/api/config` | Upravit konfiguraci |
| GET | `/api/stats` | Statistiky IMAP služby |
| GET | `/api/health` | Health check |
| GET | `/api/imap/connections` | Seznam aktivních IMAP připojení |
| GET | `/api/imap/sessions` | Seznam aktivních IMAP sessions |

---

## Client Routes (HTML Pages)

### Mail Service (port 9200)

| Method | Endpoint | Popis |
|--------|----------|-------|
| GET | `/` | Redirect na /list |
| GET | `/list` | Seznam emailů (HTML stránka) |
| GET | `/compose` | Compose nového emailu (HTML stránka) |

---

### Admin Service (port 9201)

| Method | Endpoint | Popis |
|--------|----------|-------|
| GET | `/` | Admin dashboard (HTML) |
| GET | `/health` | Health check |

---

### SSO Service (port 9300)

| Method | Endpoint | Popis |
|--------|----------|-------|
| GET | `/` | Login stránka (HTML) |
| POST | `/login` | Login form submit |

---

### Client Service (port 9202)

| Method | Endpoint | Popis |
|--------|----------|-------|
| GET | `/` | Hlavní client stránka (HTML) |
| GET | `/health` | Health check |

---

## Autentizace

### Token-based Authentication

Většina REST API endpointů vyžaduje autentizaci pomocí JWT tokenu v `Authorization` headeru:

```
Authorization: Bearer <token>
```

### Session-based Authentication (Cookie)

Client services používají HttpOnly cookies pro autentizaci. Session cookie (`access_token`) je automaticky posílána s každým requestem.

Proxy v ServiceClient zajišťuje, že cookies jsou správně předávány mezi services:

```javascript
fetch('/api/identity/logout', {
    method: 'POST',
    credentials: 'include'  // Důležité pro HttpOnly cookies
})
```

---

## Chybové Kódy

| HTTP Status | Význam |
|-------------|--------|
| 200 | OK - Request úspěšný |
| 201 | Created - Resource vytvořen |
| 400 | Bad Request - Nevalidní data |
| 401 | Unauthorized - Chybí nebo neplatná autentizace |
| 403 | Forbidden - Nedostatečná oprávnění |
| 404 | Not Found - Resource nenalezen |
| 500 | Internal Server Error - Chyba serveru |
| 502 | Bad Gateway - Chyba proxy komunikace |

---

## Příklady Použití

### Login
```bash
curl -X POST http://mail.digidig.cz/api/identity/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password123"}'
```

### Get User Preferences
```bash
curl http://mail.digidig.cz/api/identity/users/admin/preferences \
  -H "Authorization: Bearer <token>"
```

### Send Email
```bash
curl -X POST http://mail.digidig.cz/api/smtp/send \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "to": "user@example.com",
    "subject": "Test",
    "body": "Hello World"
  }'
```

---

## Poznámky

1. **Všechny REST API endpointy jsou pod `/api/` prefixem**
2. **Client routes (HTML stránky) NEMAJÍ `/api/` prefix**
3. **Proxy automaticky mapuje `/api/{service}/*` na správnou službu**
4. **Preferences endpoint používá REST standard**: `/api/users/{username}/preferences` (ne `/api/user/preferences`)
5. **HttpOnly cookies vyžadují `credentials: 'include'` ve fetch() volání**
