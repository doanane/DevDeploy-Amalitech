# reset_database_simple.py - No SQLAlchemy imports
import subprocess
import sys
import os
import time

def reset_with_docker():
    """Reset database using Docker commands."""
    print("Resetting database via Docker...")
    
    try:
        # Stop and remove containers
        print("Stopping containers...")
        subprocess.run(["docker-compose", "down"], capture_output=True, text=True)
        
        # Remove volume
        print("Removing database volume...")
        subprocess.run(["docker", "volume", "rm", "devdeploy_postgres_data"], 
                      capture_output=True, text=True, stderr=subprocess.DEVNULL)
        
        # Start containers
        print("Starting containers...")
        result = subprocess.run(
            ["docker-compose", "up", "-d", "--build"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Containers started successfully")
            
            # Wait for API to be ready
            print("Waiting for API to be ready...")
            time.sleep(10)
            
            # Create test user via API
            print("Creating test user via API...")
            import requests
            
            register_data = {
                "email": "test@example.com",
                "username": "testuser",
                "password": "TestPass123!"
            }
            
            try:
                response = requests.post(
                    "http://localhost:8000/auth/register",
                    json=register_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    print("✓ Test user created successfully")
                    print(f"  Email: test@example.com")
                    print(f"  Password: TestPass123!")
                else:
                    print(f"⚠️  User creation returned {response.status_code}: {response.text}")
                    
            except Exception as e:
                print(f"⚠️  Could not create user via API: {e}")
            
            return True
        else:
            print(f"✗ Failed to start containers: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def reset_with_sql():
    """Reset database using direct SQL."""
    print("Resetting database with direct SQL...")
    
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="postgres",
            database="devdeploy"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Drop all tables
        cursor.execute("""
            DO $$ DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """)
        print("✓ Dropped all tables")
        
        # Recreate via API startup
        print("✓ Database cleared. Restart API to recreate tables.")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"✗ SQL error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Database Reset Tool")
    print("=" * 60)
    
    print("\nChoose reset method:")
    print("1. Docker method (recommended)")
    print("2. Direct SQL method")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        success = reset_with_docker()
    elif choice == "2":
        success = reset_with_sql()
    else:
        print("Invalid choice")
        sys.exit(1)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Reset complete!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Reset failed!")
        print("=" * 60)
        sys.exit(1)