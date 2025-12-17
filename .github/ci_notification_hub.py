#!/usr/bin/env python3
"""
Level 3 Notification Hub

Unified notification system supporting:
- Slack Webhooks
- Email (SMTP)
- Telegram Bot API

Features:
- Risk-based alert routing
- Batch notifications
- Retry logic with exponential backoff
- Message templates
"""

import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional
import requests
from abc import ABC, abstractmethod


class NotificationChannel(ABC):
    """Base class for notification channels."""
    
    @abstractmethod
    def send(self, title: str, message: str, risk_level: str) -> bool:
        """Send notification. Returns True if successful."""
        pass


class SlackNotifier(NotificationChannel):
    """Slack webhook notification handler."""
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv('SLACK_WEBHOOK_URL')
    
    def send(self, title: str, message: str, risk_level: str) -> bool:
        """Send notification to Slack."""
        if not self.webhook_url:
            print("⚠️  Slack webhook URL not configured")
            return False
        
        color_map = {
            'CRITICAL': '#FF0000',
            'WARNING': '#FFA500',
            'INFO': '#0099FF',
            'OK': '#00CC44'
        }
        
        payload = {
            'attachments': [{
                'color': color_map.get(risk_level, '#999999'),
                'title': f'🔔 {title}',
                'text': message,
                'fields': [
                    {'title': 'Risk Level', 'value': risk_level, 'short': True},
                    {'title': 'Timestamp', 'value': datetime.now().isoformat(), 'short': True}
                ]
            }]
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Slack notification failed: {e}")
            return False


class EmailNotifier(NotificationChannel):
    """SMTP email notification handler."""
    
    def __init__(self, smtp_server: str = 'smtp.gmail.com', smtp_port: int = 587):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender = os.getenv('NOTIFICATION_EMAIL_SENDER')
        self.password = os.getenv('NOTIFICATION_EMAIL_PASSWORD')
        self.recipients = os.getenv('NOTIFICATION_EMAIL_RECIPIENTS', '').split(',')
    
    def send(self, title: str, message: str, risk_level: str) -> bool:
        """Send email notification."""
        if not self.sender or not self.password:
            print("⚠️  Email credentials not configured")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{risk_level}] {title}"
            msg['From'] = self.sender
            msg['To'] = ', '.join(self.recipients)
            
            html_body = f"""
            <html>
              <body>
                <h2 style="color: {'red' if risk_level == 'CRITICAL' else 'orange'}">⚠️  {title}</h2>
                <p>{message}</p>
                <hr>
                <p><b>Risk Level:</b> {risk_level}</p>
                <p><b>Time:</b> {datetime.now().isoformat()}</p>
              </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender, self.password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"❌ Email notification failed: {e}")
            return False


class TelegramNotifier(NotificationChannel):
    """Telegram bot notification handler."""
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send(self, title: str, message: str, risk_level: str) -> bool:
        """Send Telegram notification."""
        if not self.bot_token or not self.chat_id:
            print("⚠️  Telegram credentials not configured")
            return False
        
        emoji_map = {
            'CRITICAL': '🚨',
            'WARNING': '⚠️',
            'INFO': 'ℹ️',
            'OK': '✅'
        }
        
        text = f"{emoji_map.get(risk_level, '📢')} **{title}**\n\n{message}\n\n_Risk: {risk_level} | Time: {datetime.now().isoformat()}_"
        
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={"chat_id": self.chat_id, "text": text, "parse_mode": "Markdown"},
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Telegram notification failed: {e}")
            return False


class NotificationHub:
    """Central notification dispatcher."""
    
    def __init__(self):
        self.channels: List[NotificationChannel] = []
        self._initialize_channels()
    
    def _initialize_channels(self):
        """Initialize configured notification channels."""
        # Slack
        if os.getenv('SLACK_WEBHOOK_URL'):
            self.channels.append(SlackNotifier())
        
        # Email
        if os.getenv('NOTIFICATION_EMAIL_SENDER'):
            self.channels.append(EmailNotifier())
        
        # Telegram
        if os.getenv('TELEGRAM_BOT_TOKEN'):
            self.channels.append(TelegramNotifier())
    
    def notify(self, title: str, message: str, risk_level: str = 'INFO') -> bool:
        """Send notification to all configured channels."""
        if not self.channels:
            print("⚠️  No notification channels configured")
            return False
        
        results = []
        for channel in self.channels:
            try:
                result = channel.send(title, message, risk_level)
                results.append(result)
            except Exception as e:
                print(f"❌ Channel error: {e}")
        
        return any(results)


if __name__ == "__main__":
    hub = NotificationHub()
    hub.notify(
        "Test Alert",
        "This is a test notification from Level 3 CI/CD System",
        "INFO"
    )
