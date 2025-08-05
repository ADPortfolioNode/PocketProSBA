 #!/usr/bin/env python3
"""
URL Verification Script for PocketPro SBA
Tests all API endpoints and routes for accessibility
"""

import os
import json
import requests
from urllib.parse import urljoin

def verify_urls():
    """Verify all URLs for app API and routes"""
    
    print('🔍 Verifying URLs for App API and Routes...')
    print('=' * 60)
    
    # Base URL configurations
    base_url = 'http://localhost:5000'
    render_url = 'https://pocketprosba-backend.onrender.com'
    
    # Check environment variables
    print('📋 Environment Variables:')
    print(f'PORT: {os.environ.get("PORT", "5000")}')
    print(f'FLASK_ENV: {os.environ.get("FLASK_ENV", "production")}')
    
    # List all API endpoints and their URLs
    endpoints = {
        'Health Check': '/health',
        'API Info': '/api/info',
        'System Info': '/api/info',
        'Models': '/api/models',
        'Documents': '/api/documents',
        'Add Document': '/api/documents/add',
        'Search': '/api/search',
        'Chat': '/api/chat',
        'Startup': '/startup',
        'SBA Content': '/api/sba-content/<content_type>',
        'SBA Content Item': '/api/sba-content/<content_type>/<item_id>',
        'SBA Content Health': '/api/sba-content/health'
    }
    
    print('\n🔗 API Endpoints and URLs:')
    for name, path in endpoints.items():
        local_url = f'{base_url}{path}'
        render_url_full = f'{render_url}{path}'
        print(f'{name}:')
        print(f'  Local: {local_url}')
        print(f'  Render: {render_url_full}')
    
    # Test connectivity to verify URLs are accessible
    print('\n🌐 Testing URL Accessibility:')
    
    test_results = []
    for name, path in endpoints.items():
        if '<' not in path:  # Skip parameterized routes
            try:
                local_url = f'{base_url}{path}'
                response = requests.get(local_url, timeout=5)
                result = {
                    'name': name,
                    'url': local_url,
                    'status': response.status_code,
                    'success': response.ok,
                    'response': response.json() if response.ok else None
                }
                test_results.append(result)
                
                if response.ok:
                    print(f'✅ {name}: {response.status_code} - {local_url}')
                else:
                    print(f'⚠️ {name}: {response.status_code} - {local_url}')
                    
            except Exception as e:
                result = {
                    'name': name,
                    'url': local_url,
                    'error': str(e),
                    'success': False
                }
                test_results.append(result)
                print(f'❌ {name}: {e} - {local_url}')
    
    # Summary
    successful = sum(1 for r in test_results if r.get('success'))
    total = len(test_results)
    
    print(f'\n📊 Summary: {successful}/{total} endpoints accessible')
    
    # Save results
    with open('url_verification_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print('🎯 URL verification complete! Results saved to url_verification_results.json')
    
    return test_results

if __name__ == '__main__':
    verify_urls()
