# SMTP Service

SMTP server a REST API pro odesílání e-mailů v DIGiDIG systému.

## Popis

SMTP služba poskytuje:
- **SMTP Server** - Přijímání e-mailů na portu 2525 (aiosmtpd)
- **REST API** - HTTP rozhraní pro odesílání e-mailů na portu 8000
- **Email Queue** - Asynchronní frontu pro zpracování e-mailů
- **Thread Pool** - Multithreading pro paralelní zpracování
- **Service Management** - Možnost restartu a konfigurace za běhu

## Technologie

- **FastAPI** - Python async web framework (REST API)
- **aiosmtpd 1.4.4** - Async SMTP server
- **ThreadPoolExecutor** - Paralelní zpracování e-mailů
- **aiohttp** - Async HTTP klient pro komunikaci se Storage službou

## Architecture

```
┌─────────────────┐
│  SMTP Client    │
│  (port 2525)    │
└────────┬────────┘
         │
         v
┌─────────────────────────┐
│  aiosmtpd Controller    │
│  (DIGiSMTPHandler)      │
└────────┬────────────────┘
         │
         v
┌─────────────────────────┐
│  Email Queue            │
│  (in-memory list)       │
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
│  (MongoDB persist)      │
└─────────────────────────┘

┌─────────────────────────┐
│  REST API               │
│  (port 8000)            │
│  - /send                │
│  - /api/health          │
│  - /api/stats           │
│  - /api/config          │
│  - /api/restart         │
└─────────────────────────┘
```

## API Endpoints

### Health & Stats
- `GET /api/health` - Health check a SMTP controller status
- `GET /api/stats` - Statistiky (počet e-mailů, uptime, queue)
- `GET /api/config` - Aktuální konfigurace služby
- `PUT /api/config` - Aktualizace konfigurace

### Email Operations
- `POST /send` - Odeslání e-mailu přes REST API
- `POST /api/restart` - Restart SMTP serveru (admin only)

## Environment Variables

```env
SMTP_PORT=8000                      # Port FastAPI REST API
SMTP_HOSTNAME=0.0.0.0               # Hostname pro binding
SMTP_SERVER_PORT=2525               # Port pro SMTP server (aiosmtpd)
SMTP_MAX_WORKERS=4                  # Počet thread pool workers
SMTP_POOL_SIZE=10                   # Max velikost connection pool
SMTP_TIMEOUT=30                     # Request timeout (sekundy)
STORAGE_URL=http://storage:8002     # URL Storage služby
```

## SMTP Protocol

### SMTP Server Configuration
- **Port**: 2525 (non-privileged)
- **Protocol**: SMTP (RFC 5321)
- **Authentication**: Momentálně zakázána (local only)
- **TLS**: Momentálně zakázána (TODO)

### Supported Commands
- `HELO` / `EHLO` - Connection establishment
- `MAIL FROM` - Sender address
- `RCPT TO` - Recipient address(es)
- `DATA` - Email content
- `QUIT` - Close connection

### Email Handler Flow
1. Client connects to port 2525
2. `handle_RCPT` validates recipient domain
3. `handle_DATA` receives email content
4. Email parsed and added to queue
5. ThreadPool worker processes email
6. Email persisted to Storage service
7. Response sent to client

## REST API

### Send Email (POST /send)
```bash
curl -X POST http://localhost:8000/send \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "from@example.com",
    "recipient": "to@example.com",
    "subject": "Test Subject",
    "body": "Email body content"
  }'
```

Response:
```json
{
  "status": "queued",
  "message": "E-mail byl úspěšně přidán do fronty",
  "email_id": "uuid-here"
}
```

### Health Check (GET /api/health)
```bash
curl http://localhost:8000/api/health
```

Response:
```json
{
  "status": "healthy",
  "controller_running": true,
  "uptime_seconds": 3600.5,
  "emails_in_queue": 3
}
```

### Stats (GET /api/stats)
```bash
curl http://localhost:8000/api/stats
```

Response:
```json
{
  "emails_sent": 150,
  "emails_received": 200,
  "emails_in_queue": 3,
  "uptime_seconds": 7200.3,
  "requests_total": 500,
  "requests_successful": 490,
  "requests_failed": 10,
  "last_request_time": 1698769303.0
}
```

### Restart SMTP Server (POST /api/restart)
```bash
curl -X POST http://localhost:8000/api/restart
```

Response:
```json
{
  "status": "restarted",
  "message": "SMTP server byl úspěšně restartován"
}
```

## Vývoj

### Spuštění služby
```bash
# Pomocí Docker Compose
make up smtp

# Full rebuild
make refresh smtp

# Pouze restart
make clear-cache-view smtp
```

### Testování

#### Test SMTP Server (port 2525)
```bash
# Pomocí telnet
telnet localhost 2525
EHLO test.example.com
MAIL FROM:<sender@example.com>
RCPT TO:<recipient@example.com>
DATA
Subject: Test Email
From: sender@example.com
To: recipient@example.com

This is a test email.
.
QUIT
```

#### Test REST API (port 8000)
```bash
# Health check
curl http://localhost:8000/api/health

# Send email via REST
curl -X POST http://localhost:8000/send \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "test@example.com",
    "recipient": "user@example.com",
    "subject": "Hello",
    "body": "Test message"
  }'
```

## Struktura projektu

```
smtp/
├── Dockerfile              # Docker image definice
├── requirements.txt        # Python závislosti
├── src/
│   └── smtp.py            # Hlavní aplikace (SMTP server + REST API)
└── README.md
```

## Email Processing Flow

1. **Reception** (SMTP or REST)
   - SMTP: Email received on port 2525 via aiosmtpd
   - REST: Email submitted via POST /send

2. **Parsing**
   - Email headers extracted (From, To, Subject)
   - Body content decoded
   - Metadata added (timestamp, ID)

3. **Queue**
   - Email added to in-memory queue
   - Queue size monitored in stats

4. **Processing** (ThreadPool)
   - Worker thread picks email from queue
   - Validates format and content
   - Sends to Storage service

5. **Storage**
   - POST to Storage API
   - Email persisted to MongoDB
   - Confirmation received

6. **Response**
   - Success/failure logged
   - Stats updated
   - Client notified

## Monitoring

### Service State
```python
{
    "start_time": float,           # Unix timestamp startup
    "requests_total": int,         # Celkový počet požadavků
    "requests_successful": int,    # Úspěšné požadavky
    "requests_failed": int,        # Neúspěšné požadavky
    "last_request_time": float,    # Timestamp posledního požadavku
    "email_queue": list,           # Aktuální fronta e-mailů
    "controller": Controller       # aiosmtpd controller instance
}
```

### Metrics Tracked
- `emails_sent` - Počet odeslaných e-mailů přes REST API
- `emails_received` - Počet přijatých e-mailů přes SMTP server
- `emails_in_queue` - Aktuální velikost fronty
- `uptime_seconds` - Doba běhu služby
- `controller_running` - Stav SMTP serveru

## Configuration Management

### Runtime Configuration
Konfigurace lze aktualizovat za běhu přes:
```bash
curl -X PUT http://localhost:8000/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "max_workers": 8,
    "pool_size": 20,
    "timeout": 60
  }'
```

### Configurable Parameters
- `max_workers` - Počet thread pool workers
- `pool_size` - Max velikost connection pool
- `timeout` - Request timeout v sekundách
- `enabled` - Enable/disable service

## Error Handling

### Common Errors
- **Connection Refused**: Storage service nedostupná
- **Queue Full**: Přílíš mnoho e-mailů ve frontě
- **Invalid Recipient**: Doména není spravována systémem
- **Parse Error**: Nevalidní email formát

### Logging
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

## Závislosti

- **Storage Service** - Pro persistenci e-mailů do MongoDB
- **Identity Service** - Pro autentizaci SMTP klientů a kontrolu lokálních domén

## Local Delivery Mechanism

SMTP služba implementuje inteligentní lokální doručování:

### Jak to funguje

1. **Domain Check**: Pro každý příchozí e-mail kontroluje, zda je doména příjemce lokální

   ```python
   # Volá Identity service
   GET http://identity:8001/api/domains/{domain}/exists
   # Response: {"exists": true, "domain": "example.com"}
   ```

2. **Local Delivery**:
   - Pokud doména existuje → lokální doručení do Storage
   - E-mail se uloží s metadata: timestamp, read=false, folder="INBOX"
   - Příjemce může okamžitě číst email přes IMAP service

3. **External Relay** (TODO):
   - Pro externí domény (gmail.com, atd.)
   - Zatím se ukládají lokálně pro vývoj
   - V budoucnu: relay na externí SMTP server

### Příklad flow

```text
1. Client odešle email na user@example.com
2. SMTP zkontroluje: Je example.com lokální?  
   → Identity: Ano, doména existuje
3. SMTP uloží email do Storage
4. User se připojí přes IMAP
5. IMAP načte email ze Storage
6. User vidí nový email ✓
```

### Testing

Kompletní integr ační test: `tests/integration/test_smtp_imap_flow.py`

```bash
# Spustit test
pytest tests/integration/test_smtp_imap_flow.py -v -s

# Test coverage:
- ✓ Local domain check
- ✓ Send email via SMTP with authentication
- ✓ Complete flow: SMTP → Storage → IMAP
- ✓ External domain handling
```

## TODO / Roadmap

- [x] Local delivery mechanism
- [x] Domain check integration with Identity
- [x] Multipart MIME message parsing
- [x] SMTP Authentication (LOGIN, PLAIN)
- [ ] TLS/SSL support (STARTTLS)
- [ ] External SMTP relay for non-local domains
- [ ] SPF/DKIM/DMARC validace
- [ ] Rate limiting per sender
- [ ] Persistent queue (Redis)
- [ ] Email retries na failure
- [ ] Virus scanning integration
- [ ] Spam filtering

## Poznámky

- SMTP server běží na **portu 2525** (non-privileged), REST API na **8000**
- Thread pool velikost je nastavitelná (default: 4 workers)
- Email queue je momentálně in-memory (při restartu se ztratí)
- **Authentication**: Aktuálně akceptuje všechny credentials (TODO: integrace s Identity service)
- **Local delivery**: Automatické - kontroluje domény v Identity service
- Pro produkci doporučeno použít Redis pro persistent queue
