#!/usr/bin/env python3
"""Display DIGiDIG service URLs dynamically from config."""

import sys
sys.path.insert(0, '.')

from digidig.config import Config

def main():
    config = Config.instance()
    domain = config.get('external_url', 'digidig.cz').replace('https://', '').replace('http://', '')
    
    services = [
        ('Identity', 'identity'),
        ('Storage', 'storage'),
        ('SSO', 'sso'),
        ('Mail', 'mail'),
        ('Services', 'services')
    ]
    
    print('🌐 Available Services:\n')
    for name, svc in services:
        http_port = config.service_http_port(svc)
        https_port = config.service_https_port(svc)
        print(f'  {name:15} http://{domain}:{http_port}  https://{domain}:{https_port}')
    
    print(f'\n🔍 Health checks: curl https://{domain}:920X/health')
    print('🔒 All HTTPS endpoints use Let\'s Encrypt certificates')

if __name__ == '__main__':
    main()
