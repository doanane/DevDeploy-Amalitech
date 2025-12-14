import os
import sys

print("Checking database configuration...")

# Check DATABASE_URL
db_url = os.getenv("DATABASE_URL", "")
print(f"DATABASE_URL: {db_url}")

# Check if it contains asyncpg or psycopg2
if "asyncpg" in db_url:
    print("❌ ERROR: DATABASE_URL is using asyncpg (async driver)")
    print("Change to: postgresql+psycopg2://...")
elif "psycopg2" in db_url:
    print("✓ DATABASE_URL is using psycopg2 (sync driver)")
else:
    print("⚠️  DATABASE_URL driver not recognized")

# Check installed packages
print("\nChecking installed packages...")
try:
    import importlib.metadata
    packages = [dist.metadata['Name'] for dist in importlib.metadata.distributions()]
    
    if 'asyncpg' in packages:
        print("❌ asyncpg is installed. Remove it!")
    else:
        print("✓ asyncpg is NOT installed")
        
    if 'psycopg2-binary' in packages or 'psycopg2' in packages:
        print("✓ psycopg2 is installed")
    else:
        print("❌ psycopg2 is NOT installed")
        
except:
    print("Could not check packages")

# Check SQLAlchemy engine
print("\nTrying to create engine...")
try:
    from sqlalchemy import create_engine
    
    # Test with a simple URL
    test_url = "postgresql+psycopg2://test:test@localhost/test"
    engine = create_engine(test_url, echo=False)
    
    # Get the dialect
    dialect = engine.dialect.name
    print(f"SQLAlchemy dialect: {dialect}")
    
    # Get the driver
    driver = engine.dialect.driver
    print(f"SQLAlchemy driver: {driver}")
    
    if driver == "asyncpg":
        print("❌ SQLAlchemy is using asyncpg driver!")
    elif driver == "psycopg2":
        print("✓ SQLAlchemy is using psycopg2 driver")
    else:
        print(f"⚠️  Unexpected driver: {driver}")
        
except Exception as e:
    print(f"Error creating engine: {e}")