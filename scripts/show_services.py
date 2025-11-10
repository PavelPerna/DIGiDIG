#!/usr/bin/env python3
"""Display DIGiDIG service URLs dynamically from config."""

import sys
sys.path.insert(0, '.')

from digidig.config import get_config, get_service_http_port, get_service_https_port

def main():
    config = get_config()
    domain = config.get('external_url', 'digidig.cz').replace('https://', '').replace('http://', '')
    
    services = [
        ('Identity', 'identity'),
        ('Storage', 'storage'),
        ('Client', 'client'),
        ('Admin', 'admin'),
        ('SSO', 'sso'),
        ('Mail', 'mail'),
        ('Test Suite', 'test-suite'),
        ('API Docs', 'apidocs'),
        ('Services', 'services')
    ]
    
    print('🌐 Available Services:\n')
    for name, svc in services:
        http_port = get_service_http_port(svc)
        https_port = get_service_https_port(svc)
        print(f'  {name:15} http://{domain}:{http_port}  https://{domain}:{https_port}')
    
    print(f'\n🔍 Health checks: curl https://{domain}:920X/health')
    print('🔒 All HTTPS endpoints use Let\'s Encrypt certificates')

if __name__ == '__main__':
    main()
