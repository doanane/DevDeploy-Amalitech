# app/models/user.py
# Import necessary SQLAlchemy components
from sqlalchemy import Column, Integer, String  # Import column types
from sqlalchemy.orm import relationship  # Import relationship for model relationships
from app.database import Base  # Import Base class from our database setup

# Define User model class that inherits from Base
class User(Base):
    """
    User model representing a developer using the DevDeploy platform
    
    This model maps to the 'users' table in the database
    Each instance represents a row in the users table
    """
    
    # Specify the table name in the database
    __tablename__ = "users"

    # Define columns for the users table
    
    # id: Primary key column, automatically indexed
    # Integer: Stores integer values
    # primary_key=True: Uniquely identifies each row
    # index=True: Creates a database index for faster queries
    id = Column(Integer, primary_key=True, index=True)
    
    # email: User's email address
    # String(255): Stores strings up to 255 characters
    # unique=True: Ensures no duplicate emails in the database
    # index=True: Creates index for faster email-based queries
    # nullable=False: This field cannot be empty
    email = Column(String(255), unique=True, index=True, nullable=False)
    
    # hashed_password: Stores the securely hashed password
    # Never store plain text passwords!
    # String(255): Hashed passwords are fixed-length strings
    # nullable=False: Password is required
    hashed_password = Column(String(255), nullable=False)

    # Define relationship with Project model
    # relationship() creates a link between User and Project models
    # "Project": Name of the related model class
    # back_populates="owner": Creates bidirectional relationship
    # This means: a User has many Projects, and each Project has one owner (User)
    projects = relationship("Project", back_populates="owner")