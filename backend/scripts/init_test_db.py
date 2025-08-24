#!/usr/bin/env python3
"""
Database initialization script for testing environment.

This script creates and initializes the test database with necessary tables.
Run this script before executing tests to ensure proper database setup.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path for proper imports
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

# Import after adding to path
from backend.app import create_app
from backend.config import TestConfig
from backend.models.chat import db

def init_test_database():
    """Initialize the test database with all tables"""
    print("Initializing test database...")
    
    # Create application with test configuration
    app = create_app(config_class=TestConfig)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✓ Database tables created successfully")
        
        # Verify database connection
        try:
            db.session.execute('SELECT 1')
            print("✓ Database connection verified")
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            return False
    
    print("Test database initialization completed successfully!")
    return True

def cleanup_test_database():
    """Clean up test database files"""
    print("Cleaning up test database...")
    
    app = create_app(config_class=TestConfig)
    
    with app.app_context():
        # Drop all tables
        db.drop_all()
        print("✓ Database tables dropped")
        
        # Remove SQLite database file if it exists
        if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///'):
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            if os.path.exists(db_path):
                os.remove(db_path)
                print("✓ Database file removed")
    
    print("Test database cleanup completed!")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Database Management Script')
    parser.add_argument('--cleanup', action='store_true', help='Clean up test database instead of initializing')
    
    args = parser.parse_args()
    
    if args.cleanup:
        cleanup_test_database()
    else:
        success = init_test_database()
        sys.exit(0 if success else 1)
