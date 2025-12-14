import time
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def wait_for_database(max_retries=30, delay_seconds=2):
    """
    Wait for database to be ready before creating tables
    """
    from app.database import engine
    from sqlalchemy import text  # Make sure this is imported
    
    logger.info("Waiting for database to be ready...")
    
    for attempt in range(max_retries):
        try:
            # Try to connect to database - FIXED: Use text() function
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))  # FIXED
            logger.info("Database connection successful!")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                logger.info(f"Attempt {attempt + 1}/{max_retries}: Database not ready, retrying in {delay_seconds}s...")
                time.sleep(delay_seconds)
            else:
                logger.error(f"Could not connect to database after {max_retries} attempts: {e}")
                return False
    
    return False

# Create FastAPI application instance
app = FastAPI(
    title="DevDeploy API",
    description="CI/CD Pipeline Monitoring & Automation API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("Starting application initialization...")
    
    
    try:
        # Import database and models inside startup to avoid circular imports
        from app.database import engine, Base
        from app.models.user import User
        from app.models.project import Project
        from app.models.build import Build
        from app.models.webhook import WebhookEvent
        from app.models.notification import Notification
        from app.models.build_log import BuildLog
        
        # Wait for database
        if wait_for_database():
            # Create all database tables - FIXED: Base.metadata NOT Base.build_metadata
            Base.metadata.create_all(bind=engine)
            logger.info("✓ Database tables created successfully")
        else:
            logger.error("Failed to connect to database")
            
    except Exception as e:
        logger.error(f"Error during startup: {e}")

# Import and include routers
from app.api import auth, projects, builds, monitoring, notifications

# Try to import webhooks (might have issues)
try:
    from app.api import webhooks
    app.include_router(webhooks.router, tags=["webhooks"])
except ImportError as e:
    logger.warning(f"Webhooks module not available: {e}")

app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(projects.router, tags=["projects"])
app.include_router(builds.router, tags=["builds"])
app.include_router(monitoring.router, tags=["monitoring"])
app.include_router(notifications.router, tags=["notifications"])


# In your main.py, make sure webhooks are imported:
try:
    from app.api import webhooks
    app.include_router(webhooks.router, tags=["webhooks"])
    webhooks_available = True
except ImportError as e:
    logger.warning(f"Could not import webhooks module: {e}")
    webhooks_available = False


@app.get("/")
def read_root():
    return {
        "message": "Welcome to DevDeploy API",
        "status": "running",
        "version": "1.0.0",
        "features": {
            "authentication": True,
            "projects": True,
            "builds": True,
            "webhooks": webhooks_available,
            "monitoring": True,
            "notifications": True
        },
        "documentation": "/docs",
        "health_check": "/health"
    }

@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring
    """
    try:
        from app.database import engine
        # Test database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "healthy", 
            "service": "DevDeploy API", 
            "database": "connected",
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "service": "DevDeploy API", 
            "database": "disconnected", 
            "error": str(e)
        }