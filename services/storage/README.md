# DIGiDIG Storage Service

Storage microservice for the DIGiDIG platform that handles email data persistence using MongoDB.

## Installation

### As a Python Package
```bash
pip install -e .
```

### Dependencies
- `digidig-core>=1.0.0` - Shared DIGiDIG infrastructure
- `fastapi>=0.104.0` - Web framework
- `uvicorn[standard]>=0.24.0` - ASGI server
- `pymongo>=4.6.0` - MongoDB driver
- `pydantic>=2.5.0` - Data validation

## Usage

### As a package
```bash
digidig-storage
```

### As a module
```python
from storage.src.storage import main
main()
```

### Configuration
The service uses the DIGiDIG configuration system. Key settings:
- `services.storage.port` - Service port (default: 9102)
- MongoDB connection settings via environment variables:
  - `MONGO_URI` - MongoDB connection string
  - `DB_NAME` - Database name
  - `STORAGE_MAX_DOC_SIZE` - Maximum document size

---

# Storage Service

Centralizovaná úložná služba pro persistenci e-mailů v DIGiDIG systému.

## Popis

Storage služba poskytuje:
- **Email Persistence** - Uložení e-mailů do MongoDB
- **REST API** - HTTP rozhraní pro CRUD operace
- **Query Interface** - Vyhledávání a filtrování e-mailů
- **Stats & Monitoring** - Statistiky úložiště

## Technologie

- **FastAPI** - Python async web framework
- **MongoDB 6** - NoSQL databáze pro e-maily
- **pymongo** - MongoDB driver pro Python
- **Motor** - (Budoucí) Async MongoDB driver

## Architecture

```
┌─────────────────────────┐
│  SMTP Service           │
│  POST /store            │
└────────┬────────────────┘
         │
         v
┌─────────────────────────┐
│  FastAPI Application    │
│  (port 8002)            │
└────────┬────────────────┘
         │
         v
┌─────────────────────────┐
│  MongoDB                │
│  Collection: emails     │
└─────────────────────────┘
         ^
         │
┌────────┴────────────────┐
│  IMAP Service           │
│  GET /emails            │
└─────────────────────────┘
```

## API Endpoints

### Health & Stats
- `GET /api/health` - Health check a MongoDB connection status
- `GET /api/stats` - Statistiky úložiště (počet e-mailů, velikost)
- `GET /api/config` - Aktuální konfigurace služby

### Email Operations
- `GET /emails` - Seznam všech e-mailů (s pagination)
- `GET /emails/{email_id}` - Detail konkrétního e-mailu
- `POST /store` - Uložení nového e-mailu
- `DELETE /emails/{email_id}` - Smazání e-mailu
- `POST /search` - Vyhledávání e-mailů

## Environment Variables

```env
STORAGE_PORT=8002                       # Port FastAPI aplikace
STORAGE_HOSTNAME=0.0.0.0                # Hostname pro binding
STORAGE_TIMEOUT=30                      # Request timeout (sekundy)
MONGO_URI=mongodb://mongo:27017         # MongoDB connection string
DB_NAME=strategos                       # Název databáze
STORAGE_MAX_DOC_SIZE=16777216          # Max velikost dokumentu (16MB)
```

## MongoDB Schema

### Emails Collection
```javascript
{
  "_id": ObjectId("..."),
  "email_id": "uuid-string",           // Unikátní ID e-mailu
  "sender": "from@example.com",         // Email odesílatele
  "recipient": "to@example.com",        // Email příjemce
  "subject": "Email Subject",           // Předmět e-mailu
  "body": "Email content...",           // Tělo e-mailu
  "headers": {},                        // Email hlavičky (optional)
  "received_at": ISODate("..."),       // Timestamp přijetí
  "size_bytes": 1234,                  // Velikost e-mailu
  "status": "delivered"                // Status (delivered, read, etc.)
}
```

### Indexes
```javascript
// Optimalizace vyhledávání
db.emails.createIndex({ "email_id": 1 }, { unique: true });
db.emails.createIndex({ "recipient": 1 });
db.emails.createIndex({ "sender": 1 });
db.emails.createIndex({ "received_at": -1 });
db.emails.createIndex({ "subject": "text", "body": "text" });
```

## REST API

### Health Check (GET /api/health)
```bash
curl http://localhost:8002/api/health
```

Response:
```json
{
  "status": "healthy",
  "database_status": "connected",
  "database_name": "strategos",
  "collection": "emails",
  "uptime_seconds": 3600.5
}
```

### Store Email (POST /store)
```bash
curl -X POST http://localhost:8002/store \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "from@example.com",
    "recipient": "to@example.com",
    "subject": "Test Email",
    "body": "This is a test email content."
  }'
```

Response:
```json
{
  "status": "stored",
  "email_id": "uuid-here",
  "message": "E-mail byl úspěšně uložen"
}
```

### Get All Emails (GET /emails)
```bash
# Všechny e-maily
curl http://localhost:8002/emails

# S pagination
curl "http://localhost:8002/emails?limit=10&offset=0"

# Pro konkrétního příjemce
curl "http://localhost:8002/emails?recipient=user@example.com"
```

Response:
```json
{
  "emails": [
    {
      "email_id": "uuid-1",
      "sender": "from@example.com",
      "recipient": "to@example.com",
      "subject": "Test",
      "received_at": "2025-10-23T10:30:00Z",
      "size_bytes": 1234
    }
  ],
  "total": 100,
  "limit": 10,
  "offset": 0
}
```

### Get Email by ID (GET /emails/{email_id})
```bash
curl http://localhost:8002/emails/uuid-here
```

Response:
```json
{
  "email_id": "uuid-here",
  "sender": "from@example.com",
  "recipient": "to@example.com",
  "subject": "Test Email",
  "body": "Full email content here...",
  "headers": {},
  "received_at": "2025-10-23T10:30:00Z",
  "size_bytes": 1234,
  "status": "delivered"
}
```

### Delete Email (DELETE /emails/{email_id})
```bash
curl -X DELETE http://localhost:8002/emails/uuid-here
```

Response:
```json
{
  "status": "deleted",
  "email_id": "uuid-here",
  "message": "E-mail byl úspěšně smazán"
}
```

### Search Emails (POST /search)
```bash
curl -X POST http://localhost:8002/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "important meeting",
    "sender": "boss@example.com",
    "date_from": "2025-10-01",
    "date_to": "2025-10-31"
  }'
```

Response:
```json
{
  "results": [
    {
      "email_id": "uuid",
      "sender": "boss@example.com",
      "subject": "Important meeting tomorrow",
      "received_at": "2025-10-22T14:30:00Z",
      "relevance_score": 0.95
    }
  ],
  "count": 1,
  "query_time_ms": 45
}
```

### Stats (GET /api/stats)
```bash
curl http://localhost:8002/api/stats
```

Response:
```json
{
  "total_emails": 1500,
  "total_size_bytes": 52428800,
  "total_size_mb": 50.0,
  "emails_today": 45,
  "uptime_seconds": 7200.3,
  "requests_total": 3500,
  "requests_successful": 3480,
  "requests_failed": 20,
  "last_request_time": 1698765432.0,
  "database_stats": {
    "collections": 1,
    "indexes": 5,
    "data_size": 52428800
  }
}
```

## Vývoj

### Spuštění služby
```bash
# Pomocí Docker Compose
make up storage

# Full rebuild
make refresh storage

# Pouze restart
make clear-cache-view storage
```

### Testování
```bash
# Health check
curl http://localhost:8002/api/health

# Uložit e-mail
curl -X POST http://localhost:8002/store \
  -H "Content-Type: application/json" \
  -d '{"sender":"test@example.com","recipient":"user@example.com","subject":"Test","body":"Hello"}'

# Načíst všechny e-maily
curl http://localhost:8002/emails

# Vyhledat e-maily
curl -X POST http://localhost:8002/search \
  -H "Content-Type: application/json" \
  -d '{"query":"test"}'
```

## Struktura projektu

```
storage/
├── Dockerfile              # Docker image definice
├── requirements.txt        # Python závislosti
├── src/
│   └── storage.py         # Hlavní aplikace
└── README.md
```

## Email Storage Flow

1. **Reception** - E-mail přijat od SMTP služby
2. **Validation** - Kontrola povinných polí a formátu
3. **ID Generation** - Vygenerování unikátního email_id
4. **Metadata** - Přidání timestamp, velikosti, atd.
5. **Persistence** - Uložení do MongoDB
6. **Indexing** - Automatické indexování pro rychlé vyhledávání
7. **Response** - Potvrzení uložení

## Monitoring

### Service State
```python
{
    "start_time": float,           # Unix timestamp startup
    "requests_total": int,         # Celkový počet požadavků
    "requests_successful": int,    # Úspěšné požadavky
    "requests_failed": int,        # Neúspěšné požadavky
    "last_request_time": float,    # Timestamp posledního požadavku
    "config": dict                 # Aktuální konfigurace
}
```

### Metrics Tracked
- `total_emails` - Celkový počet uložených e-mailů
- `total_size_bytes` - Celková velikost úložiště
- `emails_today` - Počet dnešních e-mailů
- `database_stats` - MongoDB statistiky
- `uptime_seconds` - Doba běhu služby

## Performance Optimization

### Indexing Strategy
- **email_id** - Unique index pro rychlé lookup
- **recipient** - Index pro filtrování po příjemci
- **sender** - Index pro filtrování po odesílateli
- **received_at** - Index pro časové řazení
- **Text index** - Full-text search v subject a body

### Query Optimization
- Použití projection pro redukci dat
- Pagination pro velké result sets
- Caching často používaných queries (budoucí)

### Connection Pooling
```python
MongoClient(
    mongo_uri,
    maxPoolSize=50,
    minPoolSize=10,
    serverSelectionTimeoutMS=10000
)
```

## Error Handling

### Common Errors
- **Connection Failed**: MongoDB nedostupná
- **Duplicate Key**: E-mail s daným ID již existuje
- **Document Too Large**: E-mail překračuje max velikost (16MB)
- **Invalid Format**: Chybějící povinná pole

### Logging
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

## Backup & Recovery

### Backup Strategy
```bash
# Manuální backup
docker compose exec mongo mongodump --db strategos --out /backup

# Restore
docker compose exec mongo mongorestore --db strategos /backup/strategos
```

### Automated Backups
- TODO: Implementovat scheduled backups
- TODO: Retention policy (7 days, 4 weeks, 12 months)

## Závislosti

- **MongoDB 6** - Primární databáze
- Žádné závislosti na dalších mikroservicech (standalone)

## TODO / Roadmap

- [ ] Migrace na Motor (async MongoDB driver)
- [ ] Redis cache pro často čtené e-maily
- [ ] Full-text search vylepšení (Elasticsearch?)
- [ ] Email attachments support (GridFS)
- [ ] Compression pro starší e-maily
- [ ] Automated backups
- [ ] Data retention policies
- [ ] Email archivace (cold storage)
- [ ] Query result caching
- [ ] Bulk operations API

## Poznámky

- Max velikost e-mailu: 16MB (MongoDB document limit)
- Pro větší attachments použít GridFS
- Text search podporuje pouze základní fulltexty
- Pro produkci zvážit sharding pro horizontální škálovatelnost
- Indexy automaticky vytvořeny při prvním startu
