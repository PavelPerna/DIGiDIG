#!/bin/bash
# Production setup script for DIGiDIG with reverse proxy

set -e

echo "🚀 DIGiDIG Production Setup with Reverse Proxy"
echo "=============================================="
echo ""

# Check if running as root for port 80/443 access
if [[ $EUID -eq 0 ]]; then
    echo "⚠️  Running as root - this is fine for setup"
else
    echo "ℹ️  Not running as root - some operations may require sudo"
fi

echo ""
echo "📋 Prerequisites Check:"
echo "1. Domain: digidig.cz should point to this server"
echo "2. DNS: Create wildcard record *.digidig.cz → $(curl -s ifconfig.me || hostname -I | awk '{print $1}')"
echo "   Required subdomains: sso, identity, storage, smtp, imap,"
echo "                        mail, services"
echo "3. Firewall: Ports 25, 80, 143, 443, 465, 587, 993 and 8080-8120, 8440-8460 should be open"
echo ""

read -p "Have you configured DNS and firewall? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please configure DNS and firewall first, then re-run this script."
    exit 1
fi

echo ""
echo "🔒 SSL Certificate Setup:"
echo "We'll generate Let's Encrypt certificates for digidig.cz"

# Check port availability for standard service ports
STANDARD_PORTS=(25 80 143 443 465 587 993 8081 8082 8084 8086 8087 8088 8090 8120 8444 8445 8446 8447 8448 8449 8450 8451)
for port in "${STANDARD_PORTS[@]}"; do
    if lsof -i :$port >/dev/null 2>&1; then
        echo "❌ Port $port is occupied. Attempting to free it..."
        PID=$(lsof -t -i :$port | head -1)
        if [ -n "$PID" ]; then
            echo "Stopping process $PID on port $port..."
            kill $PID 2>/dev/null || true
            sleep 2
        fi
    fi
done

# Generate SSL certificates
echo "Generating SSL certificates..."
make generate-ssl HOSTNAME=digidig.cz

echo ""
echo "🌐 Starting Services with Load-Balanced Reverse Proxies..."
make up

echo ""
echo "✅ Production Setup Complete!"
echo ""
echo "🎯 Access your DIGiDIG installation at:"
echo ""
echo "🔧 Core Services (Port 443):"
echo "   📊 Main Site:     https://digidig.cz"
echo "    SSO/Login:     https://sso.digidig.cz"
echo "   🔑 Identity:      https://identity.digidig.cz"
echo ""
echo "� Communication Services (Port 444):"
echo "   📧 SMTP:          https://smtp.digidig.cz:444"
echo "   � IMAP:          https://imap.digidig.cz:444"
echo "   � Mail:          https://mail.digidig.cz:444"
echo ""
echo "💾 Data & API Services (Port 445):"
echo "   💾 Storage:       https://storage.digidig.cz:445"
echo "   ⚙️  Services API:  https://services.digidig.cz:445"
echo "   🌐 API Gateway:   https://api.digidig.cz:445"
echo ""
echo "🔧 Management Commands:"
echo "   • View logs: make logs"
echo "   • Restart: make restart"
echo "   • Stop: make down"
echo ""
echo "📊 Monitoring:"
echo "   • Nginx status: curl http://localhost/health"
echo "   • Service health: Check individual subdomains"
echo ""
echo "Happy deploying! 🎉"