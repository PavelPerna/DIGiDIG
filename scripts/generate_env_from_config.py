#!/usr/bin/env python3
"""
Generate .env file from config.yaml

Reads config/config.yaml and outputs environment variables suitable for docker-compose.
"""
import sys
import os
import socket
import re
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from digidig.config import Config

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "config.yaml"
if not CONFIG_PATH.exists():
    print(f"# config file not found at {CONFIG_PATH}", file=sys.stderr)
    sys.exit(1)

text = CONFIG_PATH.read_text()

# Load config using singleton
config = Config(config_path=str(CONFIG_PATH))

# Simple helper to find a value under a service block. This is not a full YAML parser.
# We search for the service name and then look for common keys beneath it.

def find_service_val(service_name, key_names):
    # pattern finds the service section: e.g. "  identity:" (must be indented, not top-level)
    # This ensures we match services under "services:" section, not the section itself
    m = re.search(rf"^\s\s+{re.escape(service_name)}:\s*$", text, flags=re.M)
    if not m:
        return None
    start = m.end()
    # capture the indented block after the service line
    block_match = re.search(r"(^\s*[^\s].*$)|\Z", text[start:], flags=re.M)
    # we will instead scan line by line from start until we hit another service at same indentation level
    lines = text[start:].splitlines()
    val = None
    for ln in lines:
        # Stop if we hit another top-level key or another service at same level (2-space indent)
        if re.match(r"^\S", ln) or re.match(r"^\s\s\w+:", ln):
            break
        # look for 'key: value'
        for key in key_names:
            # match like '    port: 8001' or '    rest_port: 8003'
            m2 = re.match(rf"^\s*{re.escape(key)}:\s*(.+)\s*$", ln)
            if m2:
                return m2.group(1).strip().strip('"').strip("'")
    return None

# Map config to env variables used in docker-compose.yml
out = {}
# DB ports and credentials
out['POSTGRES_PORT'] = find_service_val('postgres', ['port']) or re.search(r"postgres:\s*\n.*port:\s*(\d+)", text) and re.search(r"postgres:\s*\n.*port:\s*(\d+)", text).group(1) or '9301'
# fallback for older format: database.postgres
if out['POSTGRES_PORT'] is None:
    m = re.search(r"database:\s*\n\s*postgres:\s*\n\s*port:\s*(\d+)", text)
    if m:
        out['POSTGRES_PORT'] = m.group(1)

out['MONGO_PORT'] = find_service_val('mongo', ['port']) or '9302'

# Services - HTTP and HTTPS ports
out['IDENTITY_HTTP_PORT'] = find_service_val('identity', ['http_port']) or '9101'
out['IDENTITY_HTTPS_PORT'] = find_service_val('identity', ['http_sslport']) or '9201'
out['STORAGE_HTTP_PORT'] = find_service_val('storage', ['http_port']) or '9102'
out['STORAGE_HTTPS_PORT'] = find_service_val('storage', ['http_sslport']) or '9202'
# smtp may use different keys
out['SMTP_REST_HTTP_PORT'] = find_service_val('smtp', ['rest_port']) or '9100'
out['SMTP_REST_HTTPS_PORT'] = find_service_val('smtp', ['rest_sslport']) or '9200'
out['SMTP_SMTP_PORT'] = find_service_val('smtp', ['smtp_port']) or '25'
out['SMTP_SMTPS_PORT'] = find_service_val('smtp', ['smtp_sslport']) or '465'
# IMAP ports
out['IMAP_REST_HTTP_PORT'] = find_service_val('imap', ['rest_port']) or '9103'
out['IMAP_REST_HTTPS_PORT'] = find_service_val('imap', ['rest_sslport']) or '9203'
out['IMAP_PROTOCOL_PORT'] = find_service_val('imap', ['imap_port']) or '143'
out['IMAP_PROTOCOLS_PORT'] = find_service_val('imap', ['imap_sslport']) or '993'
out['SSO_HTTP_PORT'] = find_service_val('sso', ['http_port']) or '9106'
out['SSO_HTTPS_PORT'] = find_service_val('sso', ['http_sslport']) or '9206'
out['MAIL_HTTP_PORT'] = find_service_val('mail', ['http_port']) or '9107'
out['MAIL_HTTPS_PORT'] = find_service_val('mail', ['http_sslport']) or '9207'
out['SERVICES_HTTP_PORT'] = find_service_val('services', ['http_port']) or '9120'
out['SERVICES_HTTPS_PORT'] = find_service_val('services', ['http_sslport']) or '9220'

# Database connection details from top-level database section
m = re.search(r"database:\s*\n\s*postgres:\s*\n(\s+.+\n)+", text)
if m:
    block = m.group(0)
    mm = re.search(r"\s*user:\s*(\S+)", block)
    if mm:
        out['DB_USER'] = mm.group(1)
    mm = re.search(r"\s*password:\s*(\S+)", block)
    if mm:
        out['DB_PASS'] = mm.group(1)
    out['DB_NAME'] = 'strategos'
    mm = re.search(r"\s*host:\s*(\S+)", block)
    if mm:
        out['DB_HOST'] = mm.group(1)
    mm = re.search(r"\s*port:\s*(\d+)", block)
    if mm:
        out['DB_PORT'] = mm.group(1)

# DIGIDIG_ENV default
out['DIGIDIG_ENV'] = 'dev'

# Read hostname/domain from config.yaml external_url (this is the single source of truth)
# Do NOT use shell HOSTNAME env var as it's the machine hostname, not the service domain
try:
    # Look for external_url in any service config
    external_url_match = re.search(r'^\s*external_url:\s*(.+)\s*$', text, flags=re.M)
    if external_url_match:
        resolved_hostname = external_url_match.group(1).strip()
    else:
        # Fallback: try to use DIGIDIG_HOSTNAME env var if explicitly set (for installer override)
        installer_hostname = os.environ.get('DIGIDIG_HOSTNAME')
        if installer_hostname:
            resolved_hostname = installer_hostname
        else:
            raise ValueError("No external_url found in config and DIGIDIG_HOSTNAME not set")
except Exception as e:
    # Final fallback to get local IP address
    try:
        # Create a socket to determine the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Doesn't actually connect, just determines route
        resolved_hostname = s.getsockname()[0]
        s.close()
    except Exception:
        resolved_hostname = '127.0.0.1'  # Absolute final fallback to localhost IP

# Update to include hostname in environment variables
out['HOSTNAME'] = resolved_hostname

# Print env lines (skip *_EXTERNAL_URL)
for k in sorted(out.keys()):
    if k.endswith('_EXTERNAL_URL'):
        continue
    v = out[k]
    if v is None:
        continue
    print(f"{k}={v}")
