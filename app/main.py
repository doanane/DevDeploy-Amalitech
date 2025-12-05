# app/main.py
import time
from fastapi import FastAPI
from sqlalchemy import text
from app.database import engine, Base, SessionLocal
from app.models import user, project, build, webhook
from app.api import auth, projects, builds, webhooks
from app.core.config import settings

def wait_for_database(max_retries=30, delay_seconds=2):
    """
    Wait for database to be ready before creating tables
    """
    print("⏳ Waiting for database to be ready...")
    
    for attempt in range(max_retries):
        try:
            # Try to connect to database
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1}/{max_retries}: Database not ready, retrying in {delay_seconds}s...")
                time.sleep(delay_seconds)
            else:
                print(f"❌ Could not connect to database after {max_retries} attempts: {e}")
                raise
    
    return False

# Wait for database before creating tables
wait_for_database()

# Create all database tables
Base.metadata.create_all(bind=engine)
print("✅ Database tables created successfully")

# Create FastAPI application instance
app = FastAPI(
    title="DevDeploy API",
    description="CI/CD Pipeline Monitoring & Automation API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include API routers
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(builds.router)
app.include_router(webhooks.router)

@app.get("/")
def read_root():
    """
    Root endpoint - API welcome and health check
    """
    return {
        "message": "Welcome to DevDeploy API",
        "status": "running",
        "version": "1.0.0",
        "features": {
            "authentication": True,
            "projects": True,
            "builds": True,
            "webhooks": True
        }
    }

@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring
    """
    try:
        # Test database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy", "service": "DevDeploy API", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "service": "DevDeploy API", "database": "disconnected", "error": str(e)}

# This block runs only if the script is executed directly (not imported)
if __name__ == "__main__":
    import uvicorn
    
    # Run the FastAPI application with uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)