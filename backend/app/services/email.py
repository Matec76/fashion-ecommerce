import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import List, Optional, Any
import logging

from jinja2 import Environment, FileSystemLoader
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = int(settings.SMTP_PORT) if settings.SMTP_PORT else 587
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.EMAILS_FROM_EMAIL
        self.from_name = settings.EMAILS_FROM_NAME
        
        template_dir = Path(__file__).resolve().parent.parent / "templates" / "emails"
        
        if not template_dir.exists():
            logger.warning(f"Email template directory not found at: {template_dir}")
        
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))
    
    
    def send_email(
        self,
        *,
        email_to: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = email_to
            
            if text_content:
                part1 = MIMEText(text_content, "plain")
                msg.attach(part1)
            
            part2 = MIMEText(html_content, "html")
            msg.attach(part2)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {email_to}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Email send failed to {email_to}: {e}")
            return False
    
    
    def send_welcome_email(self, *, email_to: str, username: str) -> bool:
        subject = f"Welcome to {settings.PROJECT_NAME}!"
        
        template = self.jinja_env.get_template("welcome.html")
        html_content = template.render(
            project_name=settings.PROJECT_NAME,
            username=username,
            login_url=f"{settings.FRONTEND_HOST}/login",
        )
        
        text_content = f"Welcome to {settings.PROJECT_NAME}, {username}! Get started: {settings.FRONTEND_HOST}/login"
        
        return self.send_email(
            email_to=email_to,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )
    
    
    def send_verification_email(self, *, email_to: str, username: str, token: str) -> bool:
        verification_url = f"{settings.FRONTEND_HOST}/verify-email?token={token}"
        subject = f"Verify your email for {settings.PROJECT_NAME}"
        
        template = self.jinja_env.get_template("verify_email.html")
        html_content = template.render(
            project_name=settings.PROJECT_NAME,
            username=username,
            verification_url=verification_url,
            expiry_hours=24,
        )
        
        text_content = f"Verify email: {verification_url}"
        
        return self.send_email(
            email_to=email_to,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )
    
    
    def send_password_reset_email(self, *, email_to: str, username: str, token: str) -> bool:
        reset_url = f"{settings.FRONTEND_HOST}/reset-password?token={token}"
        subject = f"Password Reset Request - {settings.PROJECT_NAME}"
        
        template = self.jinja_env.get_template("reset_password.html")
        html_content = template.render(
            project_name=settings.PROJECT_NAME,
            username=username,
            reset_url=reset_url,
            expiry_hours=1,
        )
        
        text_content = f"Reset password: {reset_url}"
        
        return self.send_email(
            email_to=email_to,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )
    
    
    def send_password_changed_email(self, *, email_to: str, username: str) -> bool:
        subject = f"Password Changed - {settings.PROJECT_NAME}"
        
        template = self.jinja_env.get_template("password_changed.html")
        html_content = template.render(
            project_name=settings.PROJECT_NAME,
            username=username,
            support_email=settings.EMAILS_FROM_EMAIL,
        )
        
        text_content = f"Your password for {settings.PROJECT_NAME} was successfully changed."
        
        return self.send_email(
            email_to=email_to,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )

email_service = EmailService()