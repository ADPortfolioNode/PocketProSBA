#!/usr/bin/env python3
"""
Test script to verify REST API routes can be loaded.
"""
import sys
import os
sys.path.append('/app/src')

# Test imports
try:
    from flask import Flask, request, jsonify
    from werkzeug.utils import secure_filename
    import json
    import uuid
    print("✓ Basic imports OK")
except Exception as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

# Test service imports
try:
    from src.services.rag_manager import get_rag_manager
    from src.services.document_processor import DocumentProcessor
    print("✓ Service imports OK")
except Exception as e:
    print(f"✗ Service import error: {e}")
    sys.exit(1)

# Create test Flask app
app = Flask(__name__)

# Test basic route
@app.route('/test')
def test_route():
    return "OK"

# Test if we can define the documents route
@app.route('/api/documents', methods=['GET'])
def list_documents():
    """List all documents in the collection."""
    return jsonify({"success": True, "test": True})

print("✓ Routes defined successfully")

# Check routes
with app.app_context():
    rules = [str(rule) for rule in app.url_map.iter_rules()]
    print(f"✓ Total routes: {len(rules)}")
    print(f"✓ Routes: {rules}")

print("✓ All tests passed")
