import httpx
import logging
import json
from typing import Dict, Any, Optional
from ..config import Config

logger = logging.getLogger(__name__)

class WebhookService:
    """Service for sending task status updates and notifications to external URLs (e.g. n8n)."""
    
    def __init__(self):
        self.config = Config()
        self.webhook_url = getattr(self.config, "webhook_url", None)

    async def send_notification(self, task_id: str, status: str, payload: Dict[str, Any]):
        """Send a webhook notification about a task status change."""
        if not self.webhook_url:
            logger.debug(f"Webhook URL not configured, skipping notification for task {task_id}")
            return

        try:
            notification = {
                "task_id": task_id,
                "status": status,
                "timestamp": json.dumps(payload, default=str), # Basic serialization
                "metadata": {
                    "app": "SupoClip",
                    "version": "0.2.0"
                }
            }
            
            # Add results if completed
            if status == "completed":
                notification["result"] = payload
            elif status == "error":
                notification["error"] = payload.get("error")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=notification,
                    timeout=10.0
                )
                response.raise_for_status()
                logger.info(f"Webhook notification sent to {self.webhook_url} for task {task_id}")
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
