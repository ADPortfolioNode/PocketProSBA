#!/usr/bin/env python3
"""
Test script to verify the PocketPro SBA application setup
"""
import sys
from pathlib import Path

# Set up the Python path
project_root = Path(__file__).parent.absolute()
backend_path = project_root / "backend"
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(src_path))

print("Testing application setup...")
print(f"Project root: {project_root}")
print(f"Backend path: {backend_path}")
print(f"Source path: {src_path}")

try:
    print("\n1. Testing config import...")
    from backend.config import Config
    config = Config()
    print(f"✅ Config loaded successfully")
    print(f"   Database URI: {config.SQLALCHEMY_DATABASE_URI}")
    
except ImportError as e:
    print(f"❌ Config import failed: {e}")
    sys.exit(1)

try:
    print("\n2. Testing models import...")
    from backend.models.chat import db, ChatMessage
    print("✅ Models imported successfully")
    
except ImportError as e:
    print(f"❌ Models import failed: {e}")
    sys.exit(1)

try:
    print("\n3. Testing services import...")
    from backend.services.chat_service import create_chat_message, get_all_chat_messages
    print("✅ Services imported successfully")
    
except ImportError as e:
    print(f"❌ Services import failed: {e}")
    sys.exit(1)

try:
    print("\n4. Testing routes import...")
    from backend.routes.chat import chat_bp
    print("✅ Routes imported successfully")
    
except ImportError as e:
    print(f"❌ Routes import failed: {e}")
    sys.exit(1)

try:
    print("\n5. Testing app creation...")
    from backend.app import create_app
    app = create_app()
    print("✅ App created successfully")
    
    # Test if chat blueprint is registered
    with app.app_context():
        rules = [str(rule) for rule in app.url_map.iter_rules()]
        chat_rules = [rule for rule in rules if '/api/chat' in rule]
        print(f"   Chat endpoints registered: {len(chat_rules)}")
        for rule in chat_rules:
            print(f"   - {rule}")
            
except ImportError as e:
    print(f"❌ App creation failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ App setup error: {e}")
    sys.exit(1)

print("\n✅ All tests passed! Application setup is correct.")
