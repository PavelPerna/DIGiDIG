# Load-Balanced Reverse Proxy Architecture

## Overview

DIGiDIG now uses a **load-balanced reverse proxy architecture** to distribute connection load across multiple Nginx instances, each running on different ports while sharing the same SSL certificate.

## Architecture

```
Internet Traffic
├── Core Services (Port 443) → nginx-core → admin, sso, identity
├── Comm Services (Port 444) → nginx-comm → smtp, imap, mail
└── Data Services (Port 445) → nginx-data → storage, api, client, docs, test
```

## Benefits

### Scalability
- **Distributed Load**: Each proxy handles different service categories
- **Connection Isolation**: Service groups don't compete for connections
- **Horizontal Scaling**: Can add more proxy instances as needed

### Performance
- **Reduced Contention**: Lower connection counts per proxy instance
- **Specialized Tuning**: Each proxy optimized for its service type
- **Better Caching**: Separate cache spaces for different workloads

### Reliability
- **Fault Isolation**: Issues in one service group don't affect others
- **Independent Scaling**: Can restart/redeploy proxies independently
- **Load Distribution**: Automatic traffic distribution by service type

## Configuration

### SSL Certificate
- **Single Certificate**: All proxies use the same `digidig.cz` certificate
- **Central Management**: Certificate stored in `./ssl/` directory
- **Automatic Renewal**: Let's Encrypt integration works for all proxies

### Port Mapping
```
nginx-core: 80/443   (Core services)
nginx-comm: 81/444   (Communication services)
nginx-data: 82/445   (Data/API services)
```

### Service Distribution

#### Core Services (Port 443)
- `digidig.cz` - Main site redirect
- `admin.digidig.cz` - Admin panel
- `sso.digidig.cz` - Authentication
- `identity.digidig.cz` - Identity management

#### Communication Services (Port 444)
- `smtp.digidig.cz:444` - SMTP service
- `imap.digidig.cz:444` - IMAP service
- `mail.digidig.cz:444` - Mail service

#### Data & API Services (Port 445)
- `storage.digidig.cz:445` - File storage
- `client.digidig.cz:445` - Client application
- `apidocs.digidig.cz:445` - API documentation
- `test-suite.digidig.cz:445` - Testing suite
- `services.digidig.cz:445` - Service API
- `api.digidig.cz:445` - API gateway

## Directory Structure

```
nginx/
├── core/           # Core services proxy
│   ├── nginx.conf
│   └── conf.d/
├── comm/           # Communication services proxy
│   ├── nginx.conf
│   └── conf.d/
└── data/           # Data/API services proxy
    ├── nginx.conf
    └── conf.d/
```

## Rate Limiting

Each proxy has specialized rate limiting:

- **Core**: Auth (10r/s), Admin (5r/s)
- **Comm**: Mail (20r/s), SMTP (15r/s)
- **Data**: API (30r/s), Storage (20r/s)

## Monitoring

### Health Checks
- Core: `https://admin.digidig.cz/health`
- Comm: `https://smtp.digidig.cz:444/health`
- Data: `https://api.digidig.cz:445/health`

### Logs
Separate log volumes for each proxy:
- `nginx_core_logs`
- `nginx_comm_logs`
- `nginx_data_logs`

## Deployment

### Prerequisites
- Ports 80, 443, 444, 445 open in firewall
- DNS wildcard `*.digidig.cz` configured
- SSL certificate for `digidig.cz`

### Commands
```bash
# Setup production with load balancing
make setup-production

# Start all services
make up

# Monitor logs
make logs nginx-core
make logs nginx-comm
make logs nginx-data
```

## Future Scaling

### Adding More Proxies
1. Create new nginx directory structure
2. Add docker-compose service
3. Configure new port mapping
4. Distribute services across proxies

### Load Balancer (Optional)
For even higher scalability, add an external load balancer:
```
Load Balancer → nginx-core, nginx-comm, nginx-data
```

### Service Mesh (Advanced)
Consider Istio or Linkerd for advanced traffic management and observability.</content>
</xai:function_call">Load-Balanced Reverse Proxy Architecture

## Overview

DIGiDIG now uses a **load-balanced reverse proxy architecture** to distribute connection load across multiple Nginx instances, each running on different ports while sharing the same SSL certificate.

## Architecture

```
Internet Traffic
├── Core Services (Port 443) → nginx-core → admin, sso, identity
├── Comm Services (Port 444) → nginx-comm → smtp, imap, mail
└── Data Services (Port 445) → nginx-data → storage, api, client, docs, test
```

## Benefits

### Scalability
- **Distributed Load**: Each proxy handles different service categories
- **Connection Isolation**: Service groups don't compete for connections
- **Horizontal Scaling**: Can add more proxy instances as needed

### Performance
- **Reduced Contention**: Lower connection counts per proxy instance
- **Specialized Tuning**: Each proxy optimized for its service type
- **Better Caching**: Separate cache spaces for different workloads

### Reliability
- **Fault Isolation**: Issues in one service group don't affect others
- **Independent Scaling**: Can restart/redeploy proxies independently
- **Load Distribution**: Automatic traffic distribution by service type

## Configuration

### SSL Certificate
- **Single Certificate**: All proxies use the same `digidig.cz` certificate
- **Central Management**: Certificate stored in `./ssl/` directory
- **Automatic Renewal**: Let's Encrypt integration works for all proxies

### Port Mapping
```
nginx-core: 80/443   (Core services)
nginx-comm: 81/444   (Communication services)
nginx-data: 82/445   (Data/API services)
```

### Service Distribution

#### Core Services (Port 443)
- `digidig.cz` - Main site redirect
- `admin.digidig.cz` - Admin panel
- `sso.digidig.cz` - Authentication
- `identity.digidig.cz` - Identity management

#### Communication Services (Port 444)
- `smtp.digidig.cz:444` - SMTP service
- `imap.digidig.cz:444` - IMAP service
- `mail.digidig.cz:444` - Mail service

#### Data & API Services (Port 445)
- `storage.digidig.cz:445` - File storage
- `client.digidig.cz:445` - Client application
- `apidocs.digidig.cz:445` - API documentation
- `test-suite.digidig.cz:445` - Testing suite
- `services.digidig.cz:445` - Service API
- `api.digidig.cz:445` - API gateway

## Directory Structure

```
nginx/
├── core/           # Core services proxy
│   ├── nginx.conf
│   └── conf.d/
├── comm/           # Communication services proxy
│   ├── nginx.conf
│   └── conf.d/
└── data/           # Data/API services proxy
    ├── nginx.conf
    └── conf.d/
```

## Rate Limiting

Each proxy has specialized rate limiting:

- **Core**: Auth (10r/s), Admin (5r/s)
- **Comm**: Mail (20r/s), SMTP (15r/s)
- **Data**: API (30r/s), Storage (20r/s)

## Monitoring

### Health Checks
- Core: `https://admin.digidig.cz/health`
- Comm: `https://smtp.digidig.cz:444/health`
- Data: `https://api.digidig.cz:445/health`

### Logs
Separate log volumes for each proxy:
- `nginx_core_logs`
- `nginx_comm_logs`
- `nginx_data_logs`

## Deployment

### Prerequisites
- Ports 80, 443, 444, 445 open in firewall
- DNS wildcard `*.digidig.cz` configured
- SSL certificate for `digidig.cz`

### Commands
```bash
# Setup production with load balancing
make setup-production

# Start all services
make up

# Monitor logs
make logs nginx-core
make logs nginx-comm
make logs nginx-data
```

## Future Scaling

### Adding More Proxies
1. Create new nginx directory structure
2. Add docker-compose service
3. Configure new port mapping
4. Distribute services across proxies

### Load Balancer (Optional)
For even higher scalability, add an external load balancer:
```
Load Balancer → nginx-core, nginx-comm, nginx-data
```

### Service Mesh (Advanced)
Consider Istio or Linkerd for advanced traffic management and observability.