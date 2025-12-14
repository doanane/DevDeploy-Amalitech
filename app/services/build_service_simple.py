# """
# Simplified build service without complex dependencies.
# """
# import logging
# from datetime import datetime
# from typing import Optional, Dict, Any, List
# from sqlalchemy.orm import Session
# from sqlalchemy import desc

# from app.models import Build, Project

# logger = logging.getLogger(__name__)

# class BuildServiceSimple:
#     """Simple build service."""
    
#     def __init__(self, db: Session):
#         self.db = db
    
#     def create_build(
#         self,
#         project_id: int,
#         trigger_type: str = "manual",
#         commit_hash: Optional[str] = None,
#         commit_message: Optional[str] = None,
#         branch: Optional[str] = None
#     ) -> Build:
#         """
#         Create a new build.
#         """
#         # Get project
#         project = self.db.query(Project).get(project_id)
#         if not project:
#             raise ValueError(f"Project {project_id} not found")
        
#         # Create build
#         build = Build(
#             project_id=project_id,
#             trigger_type=trigger_type,
#             commit_hash=commit_hash,
#             commit_message=commit_message,
#             branch=branch or project.branch,
#             status="pending",
#             build_number=self._generate_build_number(project_id)
#         )
        
#         self.db.add(build)
#         self.db.commit()
#         self.db.refresh(build)
        
#         logger.info(f"Created build {build.id} for project {project_id}")
#         return build
    
#     def _generate_build_number(self, project_id: int) -> str:
#         """Generate a simple build number."""
#         last_build = self.db.query(Build).filter(
#             Build.project_id == project_id
#         ).order_by(desc(Build.created_at)).first()
        
#         if last_build and last_build.build_number:
#             try:
#                 last_num = int(last_build.build_number.split("-")[-1])
#                 next_num = last_num + 1
#             except:
#                 next_num = 1
#         else:
#             next_num = 1
        
#         return f"BUILD-{next_num:03d}"
    
#     def get_build(self, build_id: int) -> Optional[Build]:
#         """Get a build by ID."""
#         return self.db.query(Build).get(build_id)
    
#     def update_build_status(
#         self,
#         build_id: int,
#         status: str,
#         logs: Optional[str] = None
#     ) -> Build:
#         """Update build status."""
#         build = self.db.query(Build).get(build_id)
#         if not build:
#             raise ValueError(f"Build {build_id} not found")
        
#         build.status = status
#         if status in ["success", "failed", "cancelled"]:
#             build.completed_at = datetime.utcnow()
        
#         if logs:
#             build.logs = logs
        
#         self.db.commit()
#         self.db.refresh(build)
#         return build
    
#     def get_project_builds(
#         self,
#         project_id: int,
#         limit: int = 50,
#         offset: int = 0
#     ) -> List[Build]:
#         """Get builds for a project."""
#         return self.db.query(Build).filter(
#             Build.project_id == project_id
#         ).order_by(
#             desc(Build.created_at)
#         ).offset(offset).limit(limit).all()
