# app/services/notification.py - Notification service
import logging
import smtplib
import aiohttp
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Notification, User, Project, Build
from app.schemas.notification import NotificationCreate, SlackNotification
from app.core.config import settings
from app.core.websocket import WebSocketManager

logger = logging.getLogger(__name__)

class NotificationService:
    """Handles sending notifications through various channels."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ws_manager = WebSocketManager()
    
    async def send_build_started(
        self,
        user_id: int,
        project_id: int,
        build_id: int,
        commit_hash: Optional[str] = None
    ):
        """Send notification for build started."""
        stmt = select(Project).where(Project.id == project_id)
        result = await self.db.execute(stmt)
        project = result.scalar_one()
        
        title = f"Build started for {project.name}"
        message = f"A new build has started for project {project.name}"
        if commit_hash:
            message += f" (commit: {commit_hash})"
        
        await self.create_notification(
            NotificationCreate(
                type="build_started",
                title=title,
                message=message,
                user_id=user_id,
                project_id=project_id,
                build_id=build_id,
                channel="web"
            )
        )
        
        # Send via WebSocket
        await self.ws_manager.broadcast_to_user(
            user_id,
            {
                "type": "notification",
                "notification": {
                    "type": "build_started",
                    "title": title,
                    "message": message,
                    "project_id": project_id,
                    "build_id": build_id
                }
            }
        )
    
    async def send_build_success(
        self,
        user_id: int,
        project_id: int,
        build_id: int
    ):
        """Send notification for build success."""
        stmt = select(Project).where(Project.id == project_id)
        result = await self.db.execute(stmt)
        project = result.scalar_one()
        
        title = f"Build successful for {project.name}"
        message = f"The build for {project.name} completed successfully"
        
        notification = await self.create_notification(
            NotificationCreate(
                type="build_success",
                title=title,
                message=message,
                user_id=user_id,
                project_id=project_id,
                build_id=build_id,
                channel="web"
            )
        )
        
        # Send via WebSocket
        await self.ws_manager.broadcast_to_user(
            user_id,
            {
                "type": "notification",
                "notification": notification.to_dict()
            }
        )
        
        # Send email if configured
        if settings.SMTP_HOST:
            await self.send_email_notification(notification)
        
        # Send Slack if configured
        if settings.SLACK_WEBHOOK_URL:
            await self.send_slack_notification(notification)
    
    async def send_build_failed(
        self,
        user_id: int,
        project_id: int,
        build_id: int,
        error_message: str
    ):
        """Send notification for build failure."""
        stmt = select(Project).where(Project.id == project_id)
        result = await self.db.execute(stmt)
        project = result.scalar_one()
        
        title = f"Build failed for {project.name}"
        message = f"The build for {project.name} failed with error: {error_message}"
        
        notification = await self.create_notification(
            NotificationCreate(
                type="build_failed",
                title=title,
                message=message,
                data={"error": error_message},
                user_id=user_id,
                project_id=project_id,
                build_id=build_id,
                channel="web"
            )
        )
        
        # Send via WebSocket
        await self.ws_manager.broadcast_to_user(
            user_id,
            {
                "type": "notification",
                "notification": notification.to_dict()
            }
        )
        
        # Send email if configured
        if settings.SMTP_HOST:
            await self.send_email_notification(notification)
        
        # Send Slack if configured
        if settings.SLACK_WEBHOOK_URL:
            await self.send_slack_notification(notification, alert=True)
    
    async def create_notification(self, data: NotificationCreate) -> Notification:
        """Create a notification in the database."""
        notification = Notification(
            user_id=data.user_id,
            project_id=data.project_id,
            build_id=data.build_id,
            type=data.type.value if hasattr(data.type, 'value') else data.type,
            title=data.title,
            message=data.message,
            data=data.data,
            channel=data.channel.value if hasattr(data.channel, 'value') else data.channel,
            status="pending"
        )
        
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        
        return notification
    
    async def send_email_notification(self, notification: Notification):
        """Send notification via email."""
        try:
            # Get user email
            stmt = select(User).where(User.id == notification.user_id)
            result = await self.db.execute(stmt)
            user = result.scalar_one()
            
            if not user.email:
                return
            
            # Create email
            msg = MIMEMultipart("alternative")
            msg["Subject"] = notification.title
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = user.email
            
            # Create HTML content
            html = f"""
            <html>
            <body>
                <h2>{notification.title}</h2>
                <p>{notification.message}</p>
                <p>Time: {notification.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr>
                <p>DevDeploy - CI/CD Pipeline Monitoring</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(notification.message, "plain"))
            msg.attach(MIMEText(html, "html"))
            
            # Send email
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            # Update notification status
            notification.status = "sent"
            notification.sent_at = datetime.utcnow()
            await self.db.commit()
            
            logger.info(f"Email notification sent to {user.email}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")
            notification.status = "failed"
            await self.db.commit()
    
    async def send_slack_notification(
        self,
        notification: Notification,
        alert: bool = False
    ):
        """Send notification to Slack."""
        try:
            stmt = select(Project).where(Project.id == notification.project_id)
            result = await self.db.execute(stmt)
            project = result.scalar_one()
            
            # Create Slack message
            color = "#36a64f"  # green for success
            if notification.type == "build_failed":
                color = "#ff0000"  # red for failure
            elif alert:
                color = "#ff9900"  # orange for alerts
            
            slack_payload = {
                "text": notification.title,
                "attachments": [
                    {
                        "color": color,
                        "fields": [
                            {"title": "Project", "value": project.name, "short": True},
                            {"title": "Type", "value": notification.type.replace("_", " ").title(), "short": True},
                            {"title": "Message", "value": notification.message, "short": False}
                        ],
                        "footer": "DevDeploy",
                        "ts": int(notification.created_at.timestamp())
                    }
                ]
            }
            
            # Send to Slack webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    settings.SLACK_WEBHOOK_URL,
                    json=slack_payload
                ) as response:
                    if response.status == 200:
                        notification.status = "sent"
                        notification.sent_at = datetime.utcnow()
                        await self.db.commit()
                        logger.info("Slack notification sent successfully")
                    else:
                        raise Exception(f"Slack API returned {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {str(e)}")
            notification.status = "failed"
            await self.db.commit()
    
    async def get_user_notifications(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications for a user."""
        stmt = select(Notification).where(
            Notification.user_id == user_id
        )
        
        if unread_only:
            stmt = stmt.where(Notification.read_at.is_(None))
        
        stmt = stmt.order_by(Notification.created_at.desc())
        stmt = stmt.limit(limit).offset(offset)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def mark_as_read(self, notification_id: int, user_id: int):
        """Mark a notification as read."""
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id
        )
        result = await self.db.execute(stmt)
        notification = result.scalar_one_or_none()
        
        if notification and not notification.read_at:
            notification.read_at = datetime.utcnow()
            await self.db.commit()