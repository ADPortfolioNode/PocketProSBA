#!/usr/bin/env python3
"""
Script to generate missing environment configuration for PocketProSBA
"""
import os
import secrets
import sys

def generate_secret_key():
    """Generate a secure random secret key"""
    return secrets.token_urlsafe(50)

def update_backend_env():
    """Update backend environment configuration"""
    env_file = os.path.join('backend', '.env')
    
    # Read existing content if file exists
    existing_content = {}
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    existing_content[key] = value
    
    # Set default values for missing configurations
    default_config = {
        'SECRET_KEY': generate_secret_key(),
        'GOOGLE_CSE_ID': existing_content.get('GOOGLE_CSE_ID', 'your_google_custom_search_engine_id_here'),
        'CHROMADB_HOST': existing_content.get('CHROMADB_HOST', 'localhost'),
        'CHROMADB_PORT': existing_content.get('CHROMADB_PORT', '8000'),
        'PORT': existing_content.get('PORT', '5000'),
        'FLASK_ENV': existing_content.get('FLASK_ENV', 'production'),
        'DEBUG': existing_content.get('DEBUG', 'False'),
        'DATABASE_URL': existing_content.get('DATABASE_URL', 'sqlite:///app.db'),
        'FRONTEND_URL': existing_content.get('FRONTEND_URL', 'http://localhost:3000'),
        'PYTHONUNBUFFERED': existing_content.get('PYTHONUNBUFFERED', '1')
    }
    
    # Preserve existing API keys if they exist
    for key in ['GEMINI_API_KEY', 'GOOGLE_API_KEY']:
        if key in existing_content:
            default_config[key] = existing_content[key]
    
    # Write updated configuration
    with open(env_file, 'w') as f:
        f.write("# PocketProSBA Backend Environment Configuration\n")
        f.write("# Generated automatically - update with your actual values\n\n")
        
        for key, value in default_config.items():
            f.write(f"{key}={value}\n")
    
    print(f"✅ Updated {env_file}")
    print("🔑 Generated secure SECRET_KEY")
    print("📋 Missing configurations have been set with default values")
    
    return default_config

if __name__ == "__main__":
    config = update_backend_env()
    print("\nGenerated Configuration:")
    for key, value in config.items():
        if key in ['SECRET_KEY', 'GEMINI_API_KEY', 'GOOGLE_API_KEY', 'GOOGLE_CSE_ID']:
            print(f"  {key}: {'*' * min(20, len(value))} (length: {len(value)})")
        else:
            print(f"  {key}: {value}")
