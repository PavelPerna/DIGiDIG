# Unified Docker Testing System

DIGiDIG má nyní jednotný testovacie mechanizmus založený na Docker. Všetky testy sa spúšťajú konzistentne cez jediný Python skript.

## Ako to funguje

Všetky test mechanizmy boli skonsolidované do jedného `unified_test_runner.py` ktorý:

1. **Automaticky spustí DIGiDIG služby** ak nebeží
2. **Zostaví test container** s aktuálnym kódom  
3. **Napojí sa na Docker network** pre komunikáciu medzi službami
4. **Nastaví správne environment variables** pre služby
5. **Spustí konkrétnu kategoriu testov** podľa požiadavky

## Dostupné testovacie kategórie

### Základné použitie

```bash
# Kompletná sada testov  
make test

# Rýchly health check
make test-quick

# Konfiguračné testy
make test-config

# Unit testy
make test-unit       # Core unit testy (config, i18n, models)
make test-unit-safe  # Bezpečné unit testy (bez service deps)
make test-unit-core  # Core unit testy (alias)

# Integračné testy  
make test-integration

# Špecifické kategórie
make test-persistence  # Persistence testy
make test-admin       # Admin service testy
make test-identity    # Identity service testy
make test-flow        # Email flow testy

# Iba spusti služby bez testov
make test-services
```

### Priame použitie Python skriptu

```bash
# Rôzne kategórie testov
python3 unified_test_runner.py quick
python3 unified_test_runner.py config  
python3 unified_test_runner.py unit-core     # Core unit testy
python3 unified_test_runner.py unit-safe     # Bezpečné unit testy
python3 unified_test_runner.py integration
python3 unified_test_runner.py persistence
python3 unified_test_runner.py admin
python3 unified_test_runner.py identity
python3 unified_test_runner.py flow
python3 unified_test_runner.py all

# Iba spusti služby
python3 unified_test_runner.py services
```

## Výhody jednotného systému

### ✅ Konzistentnosť
- Jeden spôsob spúšťania všetkých testov
- Rovnaké environment variables pre všetky testy
- Automatické Docker network detection
- Jednotné logovanie a error handling

### ✅ Jednoduchost  
- Jeden Makefile target pre každý typ testu
- Žiadne zmätočné duplicity v Makefile
- Jasné kategorizovanie testov
- Automatické spúšťanie služieb

### ✅ Robustnosť
- Automatické detection Docker network
- Fallback na default network  
- Proper error handling a logging
- Konzistentné environment setup

## Test infraštruktúra

### Docker kontainer
- **Build**: `_test/Dockerfile` - aktuálny, funkčný Dockerfile
- **Image**: `digidig-tests` - obsahuje všetky test dependencies
- **Network**: Automaticky detekuje DIGiDIG Docker network

### Test súbory
- **Integration**: `_test/integration/` - testy medzi službami
- **Unit**: `_test/unit/` - izolované unit testy  
- **Config**: `_test/conftest.py` - pytest konfigurácia

### Environment variables
Automaticky nastavené pre komunikáciu medzi službami:
```
IDENTITY_URL=http://identity:8001
SMTP_URL=http://smtp:8000  
IMAP_URL=http://imap:8003
STORAGE_URL=http://storage:8002
CLIENT_URL=http://client:8004
ADMIN_URL=http://admin:8005
APIDOCS_URL=http://apidocs:8010
```

## Migrácia z starého systému

### Staré targety (odstránené)
- `test-docker` → `make test-integration`
- `test-docker-quick` → `make test-quick`  
- `test-build-docker` → automatické v novom systéme
- `test-deps` → zabudované v Docker image
- `test-ci-*` → nahradené jednotnými targetmi

### Nové targety (odporúčané)
- `make test` - kompletné testovanie
- `make test-quick` - rýchly health check
- `make test-integration` - integračné testy  
- `make test-unit` - unit testy

## Troubleshooting

### Testy zlyhávajú na networking
```bash
# Skontroluj Docker network
docker network ls | grep digidig

# Reštartuj služby  
make down && make up

# Spusti testy znova
make test-quick
```

### Services neodpovedajú
```bash
# Spusti iba služby a počkaj
make test-services

# Skontroluj status
docker compose ps

# Logs konkrétnej služby
docker compose logs identity
```

### Test container sa nezostaví
```bash
# Clean build cache
docker system prune -f

# Force rebuild
docker build -f _test/Dockerfile -t digidig-tests . --no-cache

# Spusti test znova
make test-quick
```

## Príklady použitia

### Development workflow
```bash
# 1. Spusti rýchly check
make test-quick

# 2. Zmeny v kóde...

# 3. Test konkrétnej služby  
make test-identity

# 4. Kompletné testovanie pred commitom
make test
```

### CI/CD pipeline
```bash
# Pre CI - najrýchlejšie essential testy
make test-quick

# Pre staging - kompletné testovanie
make test

# Pre production - integračné testy
make test-integration
```

### Debugging konkrétnych problémov
```bash
# Email flow problémy
make test-flow

# Konfiguračné problémy  
make test-config

# Persistence problémy
make test-persistence

# Admin interface problémy
make test-admin
```