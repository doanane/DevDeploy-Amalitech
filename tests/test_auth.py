#!/usr/bin/env python3
"""
Fix all known errors in the codebase.
"""
import os
import re

def fix_build_model():
    """Fix Build model metadata field conflict."""
    filepath = "app/models/build.py"
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Replace metadata with build_metadata
    content = content.replace("metadata = Column(JSON, nullable=True)", 
                              "build_metadata = Column(JSON, nullable=True)")
    
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"✓ Fixed {filepath}")

def fix_webhook_service():
    """Fix webhook service references."""
    filepath = "app/services/webhook_service.py"
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Add missing imports
    if "from typing import Dict, Any, Optional, Tuple, List" not in content:
        content = content.replace(
            "from typing import Dict, Any, Optional, Tuple",
            "from typing import Dict, Any, Optional, Tuple, List"
        )
    
    # Fix metadata references
    content = content.replace('metadata=', 'build_metadata=')
    
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"✓ Fixed {filepath}")

def fix_build_service():
    """Fix build service references."""
    filepath = "app/services/build_service.py"
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Fix metadata references
    content = content.replace('metadata: Optional[Dict[str, Any]] = None',
                             'build_metadata: Optional[Dict[str, Any]] = None')
    content = content.replace('metadata=metadata or {}',
                             'build_metadata=build_metadata or {}')
    content = content.replace('metadata:', 'build_metadata:')
    
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"✓ Fixed {filepath}")

def fix_notification_service():
    """Fix notification service missing import."""
    filepath = "app/services/notification.py"
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Add datetime import if missing
    if "from datetime import datetime" not in content:
        # Find the imports section
        lines = content.split('\n')
        import_end = 0
        for i, line in enumerate(lines):
            if line.startswith('from ') or line.startswith('import '):
                import_end = i + 1
        
        # Insert datetime import
        lines.insert(import_end, "from datetime import datetime")
        content = '\n'.join(lines)
    
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"✓ Fixed {filepath}")

def fix_project_model():
    """Add missing relationships to Project model."""
    filepath = "app/models/project.py"
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Add relationship import if missing
    if "from sqlalchemy.orm import relationship" not in content:
        # Add after sqlalchemy imports
        content = content.replace(
            "from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text",
            "from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text\nfrom sqlalchemy.orm import relationship"
        )
    
    # Add relationships at the end of class
    if 'webhook_events = relationship("WebhookEvent", back_populates="project")' not in content:
        # Find the end of the class
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip() == 'owner = relationship("User")':
                # Add other relationships
                lines.insert(i + 1, '    builds = relationship("Build", back_populates="project")')
                lines.insert(i + 2, '    webhook_events = relationship("WebhookEvent", back_populates="project")')
                break
        
        content = '\n'.join(lines)
    
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"✓ Fixed {filepath}")

def fix_user_model():
    """Add missing relationships to User model."""
    filepath = "app/models/user.py"
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Add relationship import if missing
    if "from sqlalchemy.orm import relationship" not in content:
        content = content.replace(
            "from sqlalchemy import Column, Integer, String, Boolean, DateTime",
            "from sqlalchemy import Column, Integer, String, Boolean, DateTime\nfrom sqlalchemy.orm import relationship"
        )
    
    # Add relationships
    if 'notifications = relationship("Notification", back_populates="user")' not in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip() == 'created_at = Column(DateTime(timezone=True), server_default=func.now())':
                # Add relationships after class definition
                lines.insert(i + 2, '    # Relationships')
                lines.insert(i + 3, '    projects = relationship("Project", back_populates="owner")')
                lines.insert(i + 4, '    notifications = relationship("Notification", back_populates="user")')
                break
        
        content = '\n'.join(lines)
    
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"✓ Fixed {filepath}")

def fix_requirements():
    """Ensure all required packages are in requirements.txt."""
    filepath = "requirements.txt"
    required_packages = [
        "pydantic-settings==2.1.0",
        "redis==4.6.0"
    ]
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    for package in required_packages:
        if package.split('==')[0] not in content:
            content += f"\n{package}"
    
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"✓ Fixed {filepath}")

def main():
    print("Fixing all known errors...")
    
    # Apply all fixes
    fix_build_model()
    fix_webhook_service()
    fix_build_service()
    fix_notification_service()
    fix_project_model()
    fix_user_model()
    fix_requirements()
    
    print("\n✅ All fixes applied!")
    print("\nNext steps:")
    print("1. Rebuild your Docker containers: docker-compose build")
    print("2. Start the application: docker-compose up")
    print("3. Access the API at: http://localhost:8000")
    print("4. Check documentation at: http://localhost:8000/docs")

if __name__ == "__main__":
    main()