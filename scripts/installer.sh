#!/bin/bash

set -e  # Exit on any error

echo "========================================="
echo "  DIGiDIG Installation"
echo "========================================="
echo ""

# Ask which user should own/run the services (default: current make user)
SELECTED_USER=$(id -un)
echo "Using user: $SELECTED_USER"
# Ensure required groups exist and add the selected user
echo "Ensuring groups 'docker' and 'digidig' exist..."
sudo groupadd -f docker >/dev/null 2>&1 || true
sudo groupadd -f digidig >/dev/null 2>&1 || true
echo "Adding $(id -un) to groups 'docker' and 'digidig'..."
sudo usermod -aG docker,digidig $(id -un) || echo "⚠️  Could not add $(id -un) to groups (you may need to run this manually)"
echo "If you changed group membership you may need to 'newgrp docker' or re-login for changes to take effect."
echo "Setting up Python virtual environment..."
if [ ! -d .venv ]; then
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
    echo "✅ Virtual environment created and dependencies installed"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

HOSTNAME_ARG=$(echo "$@" | grep -o 'install' | head -n1 || true)  # Not used, but for compatibility
if [ -n "$DIGIDIG_HOSTNAME" ]; then
    echo "Using hostname: $DIGIDIG_HOSTNAME"
else
    echo "Enter hostname (e.g., digidig.cz) or press Enter for default from config:"
    read -r hostname_input
    if [ -n "$hostname_input" ]; then
        export DIGIDIG_HOSTNAME=$hostname_input
        echo "Using hostname: $hostname_input"
    else
        echo "Using hostname from config.yaml"
    fi
fi
echo ""
echo "Generating .env from config..."
make gen-env
echo ""

echo "=== SSL Certificate Setup ==="
if [ -f .env ]; then
    HOSTNAME=$(grep '^HOSTNAME=' .env | cut -d'=' -f2)
else
    HOSTNAME="localhost"
fi
echo "Hostname: $HOSTNAME"
echo ""

if [ -f "ssl/$HOSTNAME.pem" ] && [ -f "ssl/$HOSTNAME-key.pem" ]; then
    echo "SSL certificates already exist for $HOSTNAME"
    echo "Skip certificate generation? [Y/n]"
    read -r skip_cert
    case $skip_cert in
        [Nn]*) GENERATE_CERT=yes ;;
        *) GENERATE_CERT=no ;;
    esac
else
    echo "No SSL certificates found for $HOSTNAME"
    echo "Generate SSL certificate? [Y/n]"
    read -r gen_cert
    case $gen_cert in
        [Nn]*) GENERATE_CERT=no ;;
        *) GENERATE_CERT=yes ;;
    esac
fi

if [ "$GENERATE_CERT" = "yes" ]; then
    if [ "$HOSTNAME" = "localhost" ] || [ "$HOSTNAME" = "127.0.0.1" ]; then
        echo "Localhost detected - generating self-signed certificate..."
        mkdir -p ssl
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ssl/$HOSTNAME-key.pem \
            -out ssl/$HOSTNAME.pem \
            -subj "/C=CZ/ST=Prague/L=Prague/O=DIGiDIG/CN=$HOSTNAME" 2>/dev/null
        echo "✅ Self-signed certificate generated: ssl/$HOSTNAME.pem"
        sudo cp ssl/$HOSTNAME.pem /etc/ssl/certs/
        sudo cp ssl/$HOSTNAME-key.pem /etc/ssl/certs/
    else
        echo ""
        echo "SSL Certificate Options:"
        echo "1. Let's Encrypt (automatic, free, trusted by browsers)"
        echo "2. Self-signed (quick, browser will show warning)"
        echo ""
        echo "Choose option [1/2] (default: 1):"
        read -r cert_choice
        case $cert_choice in
        2)
            echo "Generating self-signed certificate..."
            mkdir -p ssl
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout ssl/$HOSTNAME-key.pem \
                -out ssl/$HOSTNAME.pem \
                -subj "/C=CZ/ST=Prague/L=Prague/O=DIGiDIG/CN=$HOSTNAME" 2>/dev/null
            echo "✅ Self-signed certificate generated"
            ;;
        *)
            echo ""
            echo "Let's Encrypt Requirements:"
            echo "  ✓ Domain $HOSTNAME must point to this server"
            echo "  ✓ Port 80 must be accessible from internet"
            echo "  ✓ Email required for notifications"
            echo ""
            echo "Enter your email for Let's Encrypt:"
            read -r le_email
            if [ -z "$le_email" ]; then
                echo "❌ Email required for Let's Encrypt"
                echo "Falling back to self-signed certificate..."
                mkdir -p ssl
                openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                    -keyout ssl/$HOSTNAME-key.pem \
                    -out ssl/$HOSTNAME.pem \
                    -subj "/C=CZ/ST=Prague/L=Prague/O=DIGiDIG/CN=$HOSTNAME" 2>/dev/null
                echo "✅ Self-signed certificate generated"
                sudo cp ssl/$HOSTNAME.pem /etc/ssl/certs/
                sudo cp ssl/$HOSTNAME-key.pem /etc/ssl/certs/
            else
                echo "Attempting Let's Encrypt with Docker certbot..."
                echo "⚠️  This will temporarily bind port 80 for ACME challenge"
                mkdir -p ssl letsencrypt
                if docker run --rm \
                    -p 80:80 \
                    -v $(pwd)/letsencrypt:/etc/letsencrypt \
                    -v $(pwd)/ssl:/ssl \
                    certbot/certbot certonly --standalone \
                    -d $HOSTNAME \
                    --email $le_email \
                    --agree-tos \
                    --non-interactive; then
                    LIVE_DIR=$(sudo bash -c "ls -1d letsencrypt/live/\"$HOSTNAME\"* | tail -n 1")
                    sudo cp "$LIVE_DIR/fullchain.pem" ssl/$HOSTNAME.pem
                    sudo cp "$LIVE_DIR/privkey.pem" ssl/$HOSTNAME-key.pem
                    sudo chown $(id -un):$(id -gn) ssl/$HOSTNAME.pem ssl/$HOSTNAME-key.pem
                    sudo cp ssl/$HOSTNAME.pem /etc/ssl/certs/
                    sudo cp ssl/$HOSTNAME-key.pem /etc/ssl/certs/
                    echo "✅ Let's Encrypt certificate installed"
                    echo "💡 To renew: docker run --rm -p 80:80 -v $(pwd)/letsencrypt:/etc/letsencrypt certbot/certbot renew"
                else
                    echo "❌ Let's Encrypt failed. Possible reasons:"
                    echo "  - Domain $HOSTNAME doesn't point to this server IP"
                    echo "  - Port 80 is blocked by firewall"
                    echo "  - Port 80 is already in use (stop nginx/apache first)"
                    echo "  - DNS not propagated yet (wait 5-10 minutes)"
                    echo ""
                    echo "Falling back to self-signed certificate..."
                    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                        -keyout ssl/$HOSTNAME-key.pem \
                        -out ssl/$HOSTNAME.pem \
                        -subj "/C=CZ/ST=Prague/L=Prague/O=DIGiDIG/CN=$HOSTNAME" 2>/dev/null
                    echo "✅ Self-signed certificate generated"
                    sudo cp ssl/$HOSTNAME.pem /etc/ssl/certs/
                    sudo cp ssl/$HOSTNAME-key.pem /etc/ssl/certs/
                fi
            fi
            ;;
        esac
    fi
fi

echo ""
echo "=== Docker Images Setup ==="
echo "Options:"
echo "1. Pull pre-built images from GHCR (fast, recommended)"
echo "2. Build locally (slower, for development)"
echo ""
echo "Choose option [1/2] (default: 1):"
read -r build_choice
case $build_choice in
2)
    echo "Building all services locally..."
    BUILD_METHOD="build"
    ;;
*)
    echo "Attempting to pull images from GHCR..."
    echo ""
    if ! make pull-all; then
        echo ""
        echo "⚠️  Could not pull from GHCR, will build locally"
        BUILD_METHOD="build"
    else
        echo ""
        echo "✅ Images pulled successfully"
        BUILD_METHOD="pulled"
    fi
    ;;
esac

echo ""
if [ "$BUILD_METHOD" = "build" ]; then
    echo "This will rebuild all services. Continue? [Y/n]"
    read -r answer
    case $answer in
        [Nn]*) echo "Installation cancelled."; exit 1 ;;
    esac
    echo ""
    echo "Stopping existing services..."
    make down
    echo ""
    echo "Building services..."
    make build
else
    echo "Stopping existing services..."
    make down
fi

echo ""
echo "Starting databases..."
docker compose up -d postgres mongo
echo "Waiting for databases to be ready..."
sleep 10
echo ""
echo "Starting all services..."
docker compose up -d
echo ""
echo "========================================="
echo "✅ Installation complete!"
echo "Default admin: admin@example.com / admin"
echo "========================================="