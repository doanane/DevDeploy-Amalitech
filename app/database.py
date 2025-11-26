# app/database.py
# Import necessary modules and classes
from sqlalchemy import create_engine  # Import create_engine function to create database engine
from sqlalchemy.ext.declarative import declarative_base  # Import declarative_base to create base class for models
from sqlalchemy.orm import sessionmaker  # Import sessionmaker to create database session factory
import os  # Import os module to access environment variables
from dotenv import load_dotenv  # Import load_dotenv to load variables from .env file

# Load environment variables from .env file into os.environ
load_dotenv()

# Get the database URL from environment variables
# This URL contains connection details: dialect+driver://username:password@host:port/database
DATABASE_URL = os.getenv("DATABASE_URL")

# Create a SQLAlchemy engine instance
# The engine is the starting point for any SQLAlchemy application
# It manages the connection pool and database communication
engine = create_engine(DATABASE_URL)

# Create a configured "Session" class
# sessionmaker is a factory for creating Session objects
# autocommit=False: Don't automatically commit after each operation
# autoflush=False: Don't automatically flush pending changes to database
# bind=engine: Connect this session factory to our database engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for our models to inherit from
# All model classes will extend this Base class
# This allows SQLAlchemy to track our models and create database tables
Base = declarative_base()

# Dependency function to get database session
def get_db():
    """
    This function creates a new database session for each request
    and ensures it's closed when the request is finished
    It's used as a dependency in FastAPI route functions
    """
    # Create a new session from our session factory
    db = SessionLocal()
    try:
        # yield provides the session to the route function
        # execution pauses here until the route function completes
        yield db
    finally:
        # This block always runs, even if there's an error
        # Close the database session to free up connections
        db.close()