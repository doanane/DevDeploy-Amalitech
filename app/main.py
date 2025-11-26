# app/main.py
# Import necessary components
from fastapi import FastAPI  # Import FastAPI class
from app.database import engine, Base  # Import database engine and Base
from app.models import user, project, build  # Import models to create tables
from app.api import auth, projects, builds  # Import API routers
from app.core.config import settings  # Import settings

# Create all database tables
# Base.metadata.create_all() creates tables for all models that inherit from Base
# bind=engine: Use our database engine to create tables
# In production, use Alembic migrations instead of this approach
Base.metadata.create_all(bind=engine)

# Create FastAPI application instance
app = FastAPI(
    title="DevDeploy API",  # API title for documentation
    description="CI/CD Pipeline Monitoring & Automation API",  # API description
    version="1.0.0",  # API version
    docs_url="/docs",  # URL for Swagger UI documentation
    redoc_url="/redoc"  # URL for ReDoc documentation
)

# Include API routers
# app.include_router() adds all routes from a router to the main application
app.include_router(auth.router)  # Include authentication routes
app.include_router(projects.router)  # Include project routes
app.include_router(builds.router)

@app.get("/")
def read_root():
    """
    Root endpoint - API welcome and health check
    
    Returns:
        dict: Welcome message and API information
    """
    return {
        "message": "Welcome to DevDeploy API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring
    
    Returns:
        dict: Service health status
    """
    return {"status": "healthy", "service": "DevDeploy API"}

# This block runs only if the script is executed directly (not imported)
if __name__ == "__main__":
    import uvicorn  # Import uvicorn to run the server
    
    # Run the FastAPI application with uvicorn
    # "app.main:app": Import path to the FastAPI app (module:app_instance)
    # host="0.0.0.0": Listen on all network interfaces
    # port=8000: Listen on port 8000
    # reload=True: Enable auto-reload during development
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)