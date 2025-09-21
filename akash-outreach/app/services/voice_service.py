"""
AVR Voice Service Integration
Handles voice calling through the existing AVR infrastructure
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

import httpx
import websockets
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class CallStatus(str, Enum):
    """Call status enumeration"""
    QUEUED = "queued"
    INITIATING = "initiating"
    RINGING = "ringing"
    CONNECTED = "connected"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    CANCELLED = "cancelled"

class CallOutcome(str, Enum):
    """Call outcome enumeration"""
    SUCCESS = "success"
    CALLBACK_REQUESTED = "callback_requested"
    NOT_INTERESTED = "not_interested"
    WRONG_NUMBER = "wrong_number"
    TECHNICAL_ISSUE = "technical_issue"
    NO_RESPONSE = "no_response"

@dataclass
class CallRequest:
    """Call request data structure"""
    student_id: int
    phone_number: str
    student_name: str
    parent_name: Optional[str]
    scholarship_amount: Optional[float]
    course: Optional[str]
    priority: int
    context_data: Dict[str, Any]
    campaign_id: Optional[int] = None
    
class VoiceService:
    """
    AVR Voice Service Integration
    Manages voice calls through the existing AVR infrastructure
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.avr_base_url = config.get("avr_base_url", "http://localhost:8000")
        self.api_key = config.get("avr_api_key")
        self.webhook_url = config.get("webhook_url", "http://localhost:9000/webhooks/call-events")
        self.default_script_id = config.get("default_script_id", "scholarship_notification")
        
        # HTTP client for AVR API calls
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        
        # Active call tracking
        self.active_calls: Dict[str, Dict] = {}
        
    async def initiate_call(self, call_request: CallRequest) -> Dict[str, Any]:
        """
        Initiate a voice call through AVR system
        """
        try:
            # Prepare call context
            call_context = await self._prepare_call_context(call_request)
            
            # Make API call to AVR
            avr_payload = {
                "phone_number": call_request.phone_number,
                "script_id": self.default_script_id,
                "context": call_context,
                "webhook_url": self.webhook_url,
                "priority": call_request.priority,
                "metadata": {
                    "student_id": call_request.student_id,
                    "campaign_id": call_request.campaign_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            response = await self.http_client.post(
                f"{self.avr_base_url}/api/voice/initiate-call",
                json=avr_payload
            )
            
            if response.status_code == 200:
                call_data = response.json()
                call_id = call_data.get("call_id")
                
                # Track the call
                self.active_calls[call_id] = {
                    "student_id": call_request.student_id,
                    "phone_number": call_request.phone_number,
                    "status": CallStatus.QUEUED,
                    "initiated_at": datetime.utcnow(),
                    "context": call_context
                }
                
                logger.info(f"Call initiated successfully: {call_id}")
                return {
                    "success": True,
                    "call_id": call_id,
                    "status": CallStatus.QUEUED,
                    "message": "Call initiated successfully"
                }
            else:
                logger.error(f"AVR call initiation failed: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail="Call initiation failed")
                
        except Exception as e:
            logger.error(f"Error initiating call: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to initiate call"
            }
    
    async def _prepare_call_context(self, call_request: CallRequest) -> Dict[str, Any]:
        """
        Prepare context data for the voice call
        """
        context = {
            "student_name": call_request.student_name,
            "parent_name": call_request.parent_name or "Parent",
            "scholarship_amount": call_request.scholarship_amount,
            "course": call_request.course,
            "institute_name": "Akash Institute",
            "call_purpose": "scholarship_notification",
            "custom_fields": call_request.context_data
        }
        
        # Add personalized script variables
        context["greeting"] = f"Hello, this is calling from Akash Institute regarding {call_request.student_name}'s scholarship results."
        
        if call_request.scholarship_amount:
            context["scholarship_message"] = f"I'm pleased to inform you that {call_request.student_name} has been awarded a scholarship of ₹{call_request.scholarship_amount:,.0f}."
        else:
            context["scholarship_message"] = f"I'm calling to discuss {call_request.student_name}'s test results and available opportunities."
        
        # Add next steps information
        context["next_steps"] = [
            "Complete the admission process within the next 7 days",
            "Submit required documents for verification",
            "Attend the orientation session",
            "Contact our admissions team for any queries"
        ]
        
        context["contact_info"] = {
            "admissions_phone": "1800-XXX-XXXX",
            "email": "admissions@akash.ac.in",
            "website": "www.akash.ac.in"
        }
        
        return context
    
    async def handle_call_event(self, call_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle call events from AVR system
        """
        try:
            event_type = event_data.get("event_type")
            status = event_data.get("status")
            
            # Update call tracking
            if call_id in self.active_calls:
                self.active_calls[call_id]["status"] = status
                self.active_calls[call_id]["last_event"] = event_data
                self.active_calls[call_id]["updated_at"] = datetime.utcnow()
            
            # Handle specific events
            if event_type == "call_started":
                await self._handle_call_started(call_id, event_data)
            elif event_type == "call_connected":
                await self._handle_call_connected(call_id, event_data)
            elif event_type == "call_completed":
                await self._handle_call_completed(call_id, event_data)
            elif event_type == "call_failed":
                await self._handle_call_failed(call_id, event_data)
            
            logger.info(f"Processed call event: {call_id} - {event_type}")
            
            return {
                "success": True,
                "message": "Event processed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error handling call event: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_call_started(self, call_id: str, event_data: Dict[str, Any]):
        """Handle call started event"""
        logger.info(f"Call started: {call_id}")
        # Notify dashboard of call start
        await self._notify_dashboard("call_started", call_id, event_data)
    
    async def _handle_call_connected(self, call_id: str, event_data: Dict[str, Any]):
        """Handle call connected event"""
        logger.info(f"Call connected: {call_id}")
        # Notify dashboard of successful connection
        await self._notify_dashboard("call_connected", call_id, event_data)
    
    async def _handle_call_completed(self, call_id: str, event_data: Dict[str, Any]):
        """Handle call completed event"""
        logger.info(f"Call completed: {call_id}")
        
        # Extract call outcome
        outcome = event_data.get("outcome", CallOutcome.SUCCESS)
        duration = event_data.get("duration", 0)
        transcript = event_data.get("transcript", "")
        
        # Update call record
        if call_id in self.active_calls:
            call_info = self.active_calls[call_id]
            call_info.update({
                "status": CallStatus.COMPLETED,
                "outcome": outcome,
                "duration": duration,
                "transcript": transcript,
                "completed_at": datetime.utcnow()
            })
            
            # Move to completed calls
            del self.active_calls[call_id]
        
        # Notify dashboard
        await self._notify_dashboard("call_completed", call_id, event_data)
    
    async def _handle_call_failed(self, call_id: str, event_data: Dict[str, Any]):
        """Handle call failed event"""
        logger.error(f"Call failed: {call_id}")
        
        # Extract failure reason
        error_reason = event_data.get("error_reason", "Unknown error")
        
        # Update call record
        if call_id in self.active_calls:
            call_info = self.active_calls[call_id]
            call_info.update({
                "status": CallStatus.FAILED,
                "error_reason": error_reason,
                "failed_at": datetime.utcnow()
            })
            
            # Move to completed calls
            del self.active_calls[call_id]
        
        # Notify dashboard
        await self._notify_dashboard("call_failed", call_id, event_data)
    
    async def _notify_dashboard(self, event_type: str, call_id: str, event_data: Dict[str, Any]):
        """
        Notify dashboard of call events via WebSocket
        This will be implemented with WebSocket support
        """
        # Placeholder for WebSocket notification
        logger.info(f"Dashboard notification: {event_type} for call {call_id}")
        pass
    
    async def get_active_calls(self) -> List[Dict[str, Any]]:
        """Get list of currently active calls"""
        return [
            {
                "call_id": call_id,
                **call_data
            }
            for call_id, call_data in self.active_calls.items()
        ]
    
    async def get_call_status(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific call"""
        if call_id in self.active_calls:
            return {
                "call_id": call_id,
                **self.active_calls[call_id]
            }
        
        # Try to get from AVR system
        try:
            response = await self.http_client.get(
                f"{self.avr_base_url}/api/voice/call-status/{call_id}"
            )
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Error getting call status: {str(e)}")
        
        return None
    
    async def cancel_call(self, call_id: str) -> Dict[str, Any]:
        """Cancel an active call"""
        try:
            response = await self.http_client.post(
                f"{self.avr_base_url}/api/voice/cancel-call/{call_id}"
            )
            
            if response.status_code == 200:
                # Update local tracking
                if call_id in self.active_calls:
                    self.active_calls[call_id]["status"] = CallStatus.CANCELLED
                    del self.active_calls[call_id]
                
                return {
                    "success": True,
                    "message": "Call cancelled successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to cancel call"
                }
                
        except Exception as e:
            logger.error(f"Error cancelling call: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def bulk_initiate_calls(self, call_requests: List[CallRequest]) -> Dict[str, Any]:
        """
        Initiate multiple calls in bulk
        """
        results = {
            "successful": [],
            "failed": [],
            "total": len(call_requests)
        }
        
        # Process calls with concurrency limit
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent initiations
        
        async def initiate_single_call(call_request):
            async with semaphore:
                result = await self.initiate_call(call_request)
                if result.get("success"):
                    results["successful"].append({
                        "student_id": call_request.student_id,
                        "call_id": result.get("call_id"),
                        "phone_number": call_request.phone_number
                    })
                else:
                    results["failed"].append({
                        "student_id": call_request.student_id,
                        "phone_number": call_request.phone_number,
                        "error": result.get("error", "Unknown error")
                    })
        
        # Execute all calls
        await asyncio.gather(*[initiate_single_call(req) for req in call_requests])
        
        results["success_rate"] = len(results["successful"]) / results["total"] if results["total"] > 0 else 0
        
        logger.info(f"Bulk call initiation completed: {len(results['successful'])}/{results['total']} successful")
        
        return results
    
    async def get_call_analytics(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get call analytics from AVR system
        """
        try:
            params = {}
            if start_date:
                params["start_date"] = start_date.isoformat()
            if end_date:
                params["end_date"] = end_date.isoformat()
            
            response = await self.http_client.get(
                f"{self.avr_base_url}/api/voice/analytics",
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get call analytics: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting call analytics: {str(e)}")
            return {}
    
    async def close(self):
        """Clean up resources"""
        await self.http_client.aclose()


# Global voice service instance
voice_service: Optional[VoiceService] = None

def init_voice_service(config: Dict[str, Any]) -> VoiceService:
    """Initialize the global voice service instance"""
    global voice_service
    voice_service = VoiceService(config)
    return voice_service

def get_voice_service() -> VoiceService:
    """Get the global voice service instance"""
    if voice_service is None:
        raise RuntimeError("Voice service not initialized. Call init_voice_service first.")
    return voice_service
