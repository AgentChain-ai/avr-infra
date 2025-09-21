"""
Context Store Service
Stores personalized contexts for active calls
"""

import json
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ContextStore:
    """
    In-memory store for call contexts
    """
    
    def __init__(self):
        self._contexts: Dict[str, Dict] = {}
        self._phone_to_context: Dict[str, str] = {}  # phone -> context_id mapping
    
    def store_context(self, phone_number: str, context_data: Dict) -> str:
        """
        Store context for a phone number
        """
        context_id = f"ctx_{phone_number}_{int(datetime.utcnow().timestamp())}"
        
        self._contexts[context_id] = {
            "phone_number": phone_number,
            "context_data": context_data,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        
        # Map phone number to context for quick lookup
        self._phone_to_context[phone_number] = context_id
        
        logger.info(f"Stored context {context_id} for phone {phone_number}")
        return context_id
    
    def get_context_by_phone(self, phone_number: str) -> Optional[Dict]:
        """
        Get context for a phone number
        """
        context_id = self._phone_to_context.get(phone_number)
        if not context_id:
            return None
        
        context = self._contexts.get(context_id)
        if not context:
            return None
        
        # Check if expired
        expires_at = datetime.fromisoformat(context["expires_at"])
        if datetime.utcnow() > expires_at:
            self.cleanup_context(phone_number)
            return None
        
        return context["context_data"]
    
    def get_context(self, context_id: str) -> Optional[Dict]:
        """
        Get context by ID
        """
        return self._contexts.get(context_id, {}).get("context_data")
    
    def cleanup_context(self, phone_number: str):
        """
        Remove context for a phone number
        """
        context_id = self._phone_to_context.pop(phone_number, None)
        if context_id:
            self._contexts.pop(context_id, None)
            logger.info(f"Cleaned up context for phone {phone_number}")
    
    def cleanup_expired(self):
        """
        Clean up expired contexts
        """
        now = datetime.utcnow()
        expired_ids = []
        
        for context_id, context in self._contexts.items():
            expires_at = datetime.fromisoformat(context["expires_at"])
            if now > expires_at:
                expired_ids.append(context_id)
        
        for context_id in expired_ids:
            context = self._contexts.pop(context_id, {})
            phone_number = context.get("phone_number")
            if phone_number:
                self._phone_to_context.pop(phone_number, None)
        
        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired contexts")

# Global context store instance
context_store = ContextStore()
