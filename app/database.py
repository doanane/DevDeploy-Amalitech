from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# FORCE psycopg2 - NO asyncpg!
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql+psycopg2://postgres:postgres@localhost:5432/devdeploy'
)

print(f'Using database URL: {DATABASE_URL}')

if 'asyncpg' in DATABASE_URL:
    raise ValueError('ERROR: Must use psycopg2, not asyncpg!')

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True
)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
