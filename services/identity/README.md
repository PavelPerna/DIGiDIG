# Identity Service

Centralizovaná autentizační a autorizační služba pro DIGiDIG systém.

## Popis

Identity služba poskytuje:
- Registrace a správa uživatelských účtů
- Autentizace pomocí JWT tokenů
- Správa rolí a oprávnění
- Session management
- Domain management pro e-mailové domény

## Technologie

- **FastAPI** - Python async web framework
- **PostgreSQL 15** - Relační databáze pro uživatele a domény
- **asyncpg** - Async PostgreSQL driver
- **JWT (PyJWT)** - JSON Web Tokens pro autentizaci
- **bcrypt** - Password hashing

## API Endpoints

### Health & Stats
- `GET /api/health` - Health check a database status
- `GET /api/stats` - Statistiky služby (požadavky, aktivní sessions)
- `GET /api/config` - Aktuální konfigurace služby

### Authentication
- `POST /api/register` - Registrace nového uživatele
- `POST /api/login` - Přihlášení (vrací JWT token)
- `POST /api/logout` - Odhlášení (invalidace tokenu)
- `POST /api/verify` - Verifikace JWT tokenu
- `POST /api/refresh` - Obnovení JWT tokenu

### User Management
- `GET /api/users` - Seznam všech uživatelů (admin only)
- `GET /api/users/{user_id}` - Detail konkrétního uživatele
- `PUT /api/users/{user_id}` - Aktualizace uživatele
- `DELETE /api/users/{user_id}` - Smazání uživatele

### Domain Management
- `GET /api/domains` - Seznam domén
- `POST /api/domains` - Vytvoření nové domény
- `GET /api/domains/{domain_id}` - Detail domény
- `PUT /api/domains/{domain_id}` - Aktualizace domény
- `DELETE /api/domains/{domain_id}` - Smazání domény

## Environment Variables

```env
IDENTITY_PORT=8001                      # Port FastAPI aplikace
IDENTITY_HOSTNAME=0.0.0.0               # Hostname pro binding
DB_HOST=postgres                        # PostgreSQL host
DB_PORT=5432                            # PostgreSQL port
DB_NAME=strategos                       # Název databáze
DB_USER=postgres                        # PostgreSQL username
DB_PASS=securepassword                  # PostgreSQL heslo
JWT_SECRET=b8_XYZ123abc456DEF789ghiJKL0mnoPQ  # Secret pro JWT signing
TOKEN_EXPIRY=3600                       # Token expirační doba (sekundy)
IDENTITY_TIMEOUT=30                     # Request timeout (sekundy)
```

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Domains Table
```sql
CREATE TABLE domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(255) UNIQUE NOT NULL,
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    active BOOLEAN DEFAULT TRUE
);
```

### Sessions Table
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(512) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    revoked BOOLEAN DEFAULT FALSE
);
```

## Vývoj

### Inicializace databáze
```bash
# Automaticky vytvoří tabulky a admin účet při startu
make up identity

# Manuální vytvoření admin účtu
docker compose exec identity python scripts/create_admin.py
```

### Spuštění služby
```bash
# Pomocí Docker Compose
make up identity

# Full rebuild
make refresh identity

# Pouze restart
make clear-cache-view identity
```

### Testování
```bash
# Spuštění testů
make test

# Health check
curl http://localhost:8001/api/health

# Registrace
curl -X POST http://localhost:8001/api/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"secure123","role":"user"}'

# Login
curl -X POST http://localhost:8001/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin"}'

# Verify token
curl -X POST http://localhost:8001/api/verify \
  -H "Content-Type: application/json" \
  -d '{"token":"YOUR_JWT_TOKEN"}'
```

## Struktura projektu

```
identity/
├── Dockerfile              # Docker image definice
├── requirements.txt        # Python závislosti
├── scripts/
│   ├── create_admin.py    # Script pro vytvoření admin účtu
│   └── start.sh           # Startup script
├── src/
│   └── identity.py        # Hlavní aplikace
└── tests/
    ├── Dockerfile         # Test environment
    ├── requirements.txt   # Test dependencies
    ├── test_api.py        # Unit testy
    └── test_integration.py # Integration testy
```

## Security Features

### Password Hashing
- SHA-256 hashing s salt
- Hesla nejsou nikdy uložena v plain textu

### JWT Tokens
- Obsahuje: user_id, email, role, expiraci
- Podepsaný pomocí HS256 algoritmu
- Default expirační doba: 1 hodina

### Session Management
- Aktivní sessions trackované v databázi
- Možnost revokace tokenů (logout)
- Automatické čištění expirovaných sessions

### Role-Based Access Control
- **admin** - Plný přístup ke všem endpointům
- **user** - Omezený přístup (vlastní účet a e-maily)

## Monitoring

### Service State
```python
{
    "start_time": float,           # Unix timestamp služby start
    "requests_total": int,         # Celkový počet požadavků
    "requests_successful": int,    # Úspěšné požadavky
    "requests_failed": int,        # Neúspěšné požadavky
    "last_request_time": float,    # Timestamp posledního požadavku
    "active_sessions": list        # Seznam aktivních session IDs
}
```

### Health Check Response
```json
{
    "status": "healthy",
    "database_status": "connected",
    "uptime_seconds": 3600,
    "active_sessions": 5
}
```

## Závislosti

- **PostgreSQL** - Primární databáze
- Žádné závislosti na dalších mikroservicech (samostatná služba)

## Poznámky

- Default admin účet: `admin@example.com` / `admin` (vytvořen automaticky při instalaci)
- Pro produkci změň JWT_SECRET a DB_PASS!
- Sessions jsou perzistentní v databázi pro možnost multi-instance deploymentu
- Token refresh endpoint umožňuje prodloužit session bez opětovného přihlášení
