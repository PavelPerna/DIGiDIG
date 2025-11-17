# IMAP Service

IMAP server a REST API pro příjem a správu e-mailů v DIGiDIG systému.

## Popis

IMAP služba poskytuje:
- **REST API** - HTTP rozhraní pro načítání e-mailů
- **Email Retrieval** - Stahování e-mailů ze Storage služby
- **Folder Management** - Správa mailboxů a složek
- **Thread Pool** - Paralelní zpracování požadavků
- **Connection Pool** - Efektivní správa připojení

## Technologie

- **FastAPI** - Python async web framework
- **ThreadPoolExecutor** - Paralelní zpracování požadavků
- **aiohttp** - Async HTTP klient pro komunikaci se Storage
- **asyncio** - Asynchronní I/O operace

## Architecture

```
┌─────────────────┐
│  IMAP Client    │
│  (REST API)     │
└────────┬────────┘
         │
         v
┌─────────────────────────┐
│  FastAPI Application    │
│  (port 8003)            │
└────────┬────────────────┘
         │
         v
┌─────────────────────────┐
│  ThreadPoolExecutor     │
│  (4 workers)            │
└────────┬────────────────┘
         │
         v
┌─────────────────────────┐
│  Storage Service        │
│  (MongoDB)              │
└─────────────────────────┘
```

## API Endpoints

### Health & Stats
- `GET /api/health` - Health check
- `GET /api/stats` - Statistiky služby
- `GET /api/config` - Aktuální konfigurace
- `PUT /api/config` - Aktualizace konfigurace

### Email Operations
- `GET /emails` - Seznam všech e-mailů
- `GET /emails/{email_id}` - Detail konkrétního e-mailu
- `POST /fetch` - Manuální fetch e-mailů ze Storage

## Environment Variables

```env
IMAP_PORT=8003                      # Port FastAPI aplikace
IMAP_HOSTNAME=0.0.0.0               # Hostname pro binding
IMAP_MAX_WORKERS=4                  # Počet thread pool workers
IMAP_POOL_SIZE=10                   # Max velikost connection pool
IMAP_TIMEOUT=30                     # Request timeout (sekundy)
IMAP_MAX_CONNECTIONS=50             # Max počet současných připojení
IMAP_IDLE_TIMEOUT=300               # IDLE timeout (sekundy)
STORAGE_URL=http://storage:8002     # URL Storage služby
```

## REST API

### Health Check (GET /api/health)
```bash
curl http://localhost:8003/api/health
```

Response:
```json
{
  "status": "healthy",
  "uptime_seconds": 3600.5,
  "active_connections": 5
}
```

### Get Emails (GET /emails)
```bash
curl http://localhost:8003/emails
```

Response:
```json
{
  "emails": [
    {
      "id": "uuid-here",
      "sender": "from@example.com",
      "recipient": "to@example.com",
      "subject": "Test Subject",
      "body": "Email content",
      "received_at": "2025-10-23T10:30:00Z"
    }
  ],
  "count": 1
}
```

### Get Email by ID (GET /emails/{email_id})
```bash
curl http://localhost:8003/emails/uuid-here
```

Response:
```json
{
  "id": "uuid-here",
  "sender": "from@example.com",
  "recipient": "to@example.com",
  "subject": "Test Subject",
  "body": "Email content",
  "headers": {},
  "received_at": "2025-10-23T10:30:00Z"
}
```

### Fetch Emails (POST /fetch)
```bash
curl -X POST http://localhost:8003/fetch \
  -H "Content-Type: application/json" \
  -d '{"user_id": "uuid-here"}'
```

Response:
```json
{
  "status": "success",
  "emails_fetched": 15,
  "message": "E-maily úspěšně staženy"
}
```

### Stats (GET /api/stats)
```bash
curl http://localhost:8003/api/stats
```

Response:
```json
{
  "emails_fetched": 150,
  "active_connections": 5,
  "uptime_seconds": 7200.3,
  "requests_total": 500,
  "requests_successful": 490,
  "requests_failed": 10,
  "last_request_time": 1698769301.0,
  "active_sessions": 3
}
```

## Vývoj

### Spuštění služby
```bash
# Pomocí Docker Compose
make up imap

# Full rebuild
make refresh imap

# Pouze restart
make clear-cache-view imap
```

### Testování
```bash
# Health check
curl http://localhost:8003/api/health

# Načíst všechny e-maily
curl http://localhost:8003/emails

# Načíst konkrétní e-mail
curl http://localhost:8003/emails/EMAIL_ID

# Fetch nové e-maily
curl -X POST http://localhost:8003/fetch
```

## Struktura projektu

```
imap/
├── Dockerfile              # Docker image definice
├── requirements.txt        # Python závislosti
├── src/
│   └── imap.py            # Hlavní aplikace
└── README.md
```

## Email Retrieval Flow

1. **Request** - Client požádá o e-maily
2. **Validation** - Ověření oprávnění a parametrů
3. **Storage Query** - Dotaz do Storage služby
4. **Processing** - Zpracování a formátování e-mailů
5. **Response** - Vrácení dat klientovi

## Monitoring

### Service State
```python
{
    "start_time": float,           # Unix timestamp startup
    "requests_total": int,         # Celkový počet požadavků
    "requests_successful": int,    # Úspěšné požadavky
    "requests_failed": int,        # Neúspěšné požadavky
    "last_request_time": float,    # Timestamp posledního požadavku
    "active_connections": list,    # Seznam aktivních připojení
    "active_sessions": list        # Seznam aktivních sessions
}
```

### Metrics Tracked
- `emails_fetched` - Počet načtených e-mailů
- `active_connections` - Počet aktivních připojení
- `active_sessions` - Počet aktivních sessions
- `uptime_seconds` - Doba běhu služby
- `requests_total/successful/failed` - Request statistiky

## Configuration Management

### Runtime Configuration
```bash
curl -X PUT http://localhost:8003/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "max_workers": 8,
    "pool_size": 20,
    "timeout": 60,
    "max_connections": 100
  }'
```

### Configurable Parameters
- `max_workers` - Počet thread pool workers
- `pool_size` - Max velikost connection pool
- `timeout` - Request timeout v sekundách
- `max_connections` - Max počet současných připojení
- `idle_timeout` - IDLE connection timeout
- `enabled` - Enable/disable service

## Connection Management

### Connection Pool
- Max connections nastavitelné přes config
- Automatické uzavření neaktivních připojení
- Connection pooling pro Storage API

### Active Connections Tracking
- Real-time monitoring aktivních připojení
- Connection timeout management
- Graceful shutdown s uzavřením všech připojení

## Error Handling

### Common Errors
- **Storage Unavailable**: Storage service nedostupná
- **Email Not Found**: E-mail s daným ID neexistuje
- **Connection Limit**: Překročen max počet připojení
- **Timeout**: Request timeout expired

### Logging
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

## Závislosti

- **Storage Service** - Pro načítání e-mailů z MongoDB
- **Identity Service** - (Budoucí) Pro autentizaci IMAP klientů

## TODO / Roadmap

- [ ] Full IMAP protocol support (port 143/993)
- [ ] IMAP Authentication
- [ ] TLS/SSL support (IMAPS)
- [ ] Folder/Mailbox management (INBOX, Sent, Trash, etc.)
- [ ] Email flags (Read, Unread, Starred, etc.)
- [ ] Search and filtering
- [ ] IDLE command support (push notifications)
- [ ] Quota management
- [ ] Message threading
- [ ] Email attachment handling

## IMAP Protocol Notes

### Planned IMAP Commands
- `LOGIN` - Authenticate user
- `SELECT` - Select mailbox
- `FETCH` - Retrieve email(s)
- `SEARCH` - Search emails
- `STORE` - Update flags
- `DELETE` - Mark for deletion
- `EXPUNGE` - Permanently remove deleted
- `IDLE` - Wait for new emails
- `LOGOUT` - Close connection

### Folder Structure
```
INBOX/
├── Sent/
├── Drafts/
├── Trash/
└── Custom Folders/
```

## Poznámky

- Momentálně poskytuje pouze REST API, full IMAP protocol v plánu
- Thread pool velikost je nastavitelná (default: 4 workers)
- Pro produkci doporučeno zvýšit `max_connections` podle zátěže
- Email cache momentálně není implementován (každý request jde do Storage)
- Pro lepší performance zvážit Redis cache vrstvu
