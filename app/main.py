from fastapi import FastAPI
from app.database import engine, Base
from app.models import user, project, build
from app.api import auth, projects
from app.core.config import settings

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DevDeploy API",
    description="CI/CD Pipeline Monitoring & Automation API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.include_router(auth.router)
app.include_router(projects.router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to DevDeploy API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "DevDeploy API"}