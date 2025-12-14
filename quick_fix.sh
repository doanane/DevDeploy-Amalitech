#!/bin/bash

echo "Fixing DevDeploy startup issues..."

# Stop everything
docker-compose down

# Remove volumes to start fresh
docker-compose down -v

# Fix the init_db.py file
cat > scripts/init_db.py << 'EOF'
#!/usr/bin/env python3
"""
Database initialization script.
"""
import sys
import os
import time
from sqlalchemy import text

# Add app to path
sys.path.insert(0, '/app')

from app.database import engine, Base
from app.models.user import User
from app.models.project import Project
from app.models.build import Build
from app.models.webhook import WebhookEvent
from app.models.notification import Notification
from app.models.build_log import BuildLog

def init_database():
    """Initialize database tables."""
    print("Initializing database...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables created successfully")
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"✓ Database connection successful - Test query result: {result.scalar()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        # Wait a bit for database to be ready
        print("Waiting for database to be ready...")
        time.sleep(5)
        
        # Try multiple times
        max_retries = 5
        for attempt in range(max_retries):
            print(f"Attempt {attempt + 1}/{max_retries}...")
            success = init_database()
            
            if success:
                print("✅ Database initialization complete")
                sys.exit(0)
            else:
                if attempt < max_retries - 1:
                    print(f"Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    print("❌ Database initialization failed after all retries")
                    sys.exit(1)
                    
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
EOF

echo "✓ Fixed init_db.py"

# Build and start
echo "Building and starting containers..."
docker-compose build
docker-compose up -d

echo "Waiting for startup..."
sleep 15

echo "Checking status..."
docker-compose ps

echo "Testing API..."
curl -s http://localhost:8000/health | python -m json.tool

echo "✅ Fix complete! API should be running at http://localhost:8000"