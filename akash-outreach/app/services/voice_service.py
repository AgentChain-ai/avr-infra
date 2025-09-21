"""
AVR Voice Service Integration
Handles voice calling through the existing AVR infrastructure
"""

import asyncio
import json
import logging
import os
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
    personalized_context: Optional[str] = None
    
class VoiceService:
    """
    AVR Voice Service Integration
    Manages voice calls through the existing AVR infrastructure
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        # Use environment variables from your .env configuration
        self.avr_core_url = os.getenv("AVR_CORE_URL", "http://localhost:5001")
        self.avr_ami_url = os.getenv("AVR_AMI_URL", "http://localhost:6006")
        self.webhook_url = config.get("webhook_url", f"http://akash-outreach:{os.getenv('AKASH_API_PORT', '8000')}/api/webhooks/avr-events") if config else f"http://localhost:{os.getenv('AKASH_API_PORT', '8000')}/api/webhooks/avr-events"
        
        # Base agent prompt from environment
        self.base_agent_prompt = os.getenv("AGENT_PROMPT", "You are a helpful phone assistant.")
        
        # Call settings from environment
        self.default_extension = os.getenv("DEFAULT_CALL_EXTENSION", "5001")
        self.max_concurrent_calls = int(os.getenv("MAX_CONCURRENT_CALLS", "5"))
        self.call_timeout = int(os.getenv("CALL_TIMEOUT", "300"))
        
        # HTTP client for AVR API calls
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Content-Type": "application/json"
            }
        )
        
        # Active call tracking
        self.active_calls: Dict[str, Dict] = {}
        
    async def initiate_call(self, call_request: CallRequest) -> Dict[str, Any]:
        """
        Initiate a voice call through Asterisk AMI to AVR system
        Uses direct AMI connection to place calls to SIP endpoints
        """
        try:
            print(f"🔍 VOICE SERVICE DEBUG: Starting initiate_call for {call_request.phone_number}")
            logger.info(f"🔍 VOICE SERVICE DEBUG: Starting initiate_call for {call_request.phone_number}")
            
            # Prepare personalized prompt for the call
            personalized_prompt = await self._prepare_personalized_prompt(call_request)
            
            # Generate unique call ID
            call_id = f"call_{int(datetime.utcnow().timestamp())}"
            print(f"🔍 VOICE SERVICE DEBUG: Generated call_id {call_id}")
            
            # For SIP extensions, call directly through Asterisk
            if call_request.phone_number.isdigit() and len(call_request.phone_number) <= 4:
                # This is a SIP extension (like 1000)
                print(f"🔍 VOICE SERVICE DEBUG: Calling SIP extension {call_request.phone_number}")
                success = await self._initiate_sip_call(call_request, call_id, personalized_prompt)
                print(f"🔍 VOICE SERVICE DEBUG: SIP call result: {success}")
            else:
                # This would be for external numbers (needs Twilio integration)
                print(f"🔍 VOICE SERVICE DEBUG: External number {call_request.phone_number} not supported")
                return {
                    "success": False,
                    "error": "External calls require Twilio integration",
                    "message": "Only SIP extensions supported currently"
                }
            
            if success:
                # Track the call
                self.active_calls[call_id] = {
                    "student_id": call_request.student_id,
                    "phone_number": call_request.phone_number,
                    "status": CallStatus.QUEUED,
                    "initiated_at": datetime.utcnow(),
                    "campaign_id": call_request.campaign_id,
                    "personalized_prompt": personalized_prompt
                }
                
                logger.info(f"SIP call initiated successfully: {call_id} to {call_request.phone_number}")
                return {
                    "success": True,
                    "call_id": call_id,
                    "status": CallStatus.QUEUED.value,
                    "message": "Call initiated successfully",
                    "phone_number": call_request.phone_number,
                    "student_id": call_request.student_id
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to initiate SIP call",
                    "message": "Call initiation failed"
                }
                
        except Exception as e:
            logger.error(f"Error initiating call: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Call initiation failed due to technical error"
            }
    
    async def _initiate_sip_call(self, call_request: CallRequest, call_id: str, system_message: str) -> bool:
        """
        Initiate a SIP call using Asterisk's originate functionality
        """
        try:
            import asyncio
            import json
            
            # First, prepare the complete personalized context for this call
            personalized_instructions = await self._generate_personalized_instructions(call_request, system_message)
            
            # DIRECTLY send the personalized context to the OpenAI service via API
            success = await self._send_context_to_openai_service(call_request.phone_number, personalized_instructions)
            if not success:
                logger.warning("Failed to send context to OpenAI service, proceeding with default instructions")
            
            # Use Asterisk CLI through Docker exec to initiate the call
            asterisk_cmd = [
                "docker", "exec", "avr-asterisk", "asterisk", "-x",
                f"channel originate PJSIP/{call_request.phone_number} extension 5001@demo"
            ]
            
            # Debug logging
            print(f"🔍 VOICE DEBUG: Executing command: {' '.join(asterisk_cmd)}")
            print(f"🔍 VOICE DEBUG: Calling phone number: {call_request.phone_number}")
            logger.info(f"🔍 VOICE DEBUG: Executing command: {' '.join(asterisk_cmd)}")
            logger.info(f"🔍 VOICE DEBUG: Calling phone number: {call_request.phone_number}")
            
            # Execute the command
            process = await asyncio.create_subprocess_exec(
                *asterisk_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            print(f"🔍 VOICE DEBUG: Command completed. Return code: {process.returncode}")
            print(f"🔍 VOICE DEBUG: stdout: {stdout.decode()}")
            print(f"🔍 VOICE DEBUG: stderr: {stderr.decode()}")
            
            if process.returncode == 0:
                print(f"🔍 VOICE DEBUG: Asterisk originate command successful for {call_request.phone_number}")
                logger.info(f"Asterisk originate command successful for {call_request.phone_number}")
                return True
            else:
                print(f"🔍 VOICE DEBUG: Asterisk originate failed: {stderr.decode()}")
                logger.error(f"Asterisk originate failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing Asterisk originate: {str(e)}")
            return False
    
    async def _prepare_personalized_prompt(self, call_request: CallRequest) -> str:
        """
        Prepare personalized prompt by combining base prompt with campaign context
        """
        try:
            # Start with base agent prompt from environment
            prompt = self.base_agent_prompt
            
            # Add personalized context if available
            if call_request.personalized_context:
                prompt = f"{prompt}\n\nContext for this call:\n{call_request.personalized_context}"
            else:
                # Fallback: create basic context from student data
                context_parts = []
                if call_request.student_name:
                    context_parts.append(f"Student name: {call_request.student_name}")
                if call_request.parent_name:
                    context_parts.append(f"Parent name: {call_request.parent_name}")
                if call_request.scholarship_amount:
                    context_parts.append(f"Scholarship amount: ${call_request.scholarship_amount}")
                if call_request.course:
                    context_parts.append(f"Course: {call_request.course}")
                
                if context_parts:
                    context = "\n".join(context_parts)
                    prompt = f"{prompt}\n\nContext for this call:\n{context}"
            
            return prompt
            
        except Exception as e:
            logger.error(f"Error preparing personalized prompt: {str(e)}")
            return self.base_agent_prompt  # Fallback to base prompt
    
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
    
    async def execute_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a campaign by initiating calls for all students with their personalized contexts
        """
        try:
            campaign_id = campaign_data.get("id")
            student_ids = campaign_data.get("student_ids", [])
            personalized_contexts = campaign_data.get("personalized_contexts", {})
            
            logger.info(f"Starting campaign execution: {campaign_id} with {len(student_ids)} students")
            
            call_requests = []
            
            # Create call requests for each student
            for student_id in student_ids:
                student_data = campaign_data.get("students", {}).get(str(student_id), {})
                personalized_context = personalized_contexts.get(str(student_id), {}).get("context", "")
                
                call_request = CallRequest(
                    student_id=student_id,
                    phone_number=student_data.get("phone_number", ""),
                    student_name=student_data.get("student_name", ""),
                    parent_name=student_data.get("parent_name"),
                    scholarship_amount=student_data.get("scholarship_amount"),
                    course=student_data.get("course"),
                    priority=5,  # Default priority
                    context_data=student_data,
                    campaign_id=campaign_id,
                    personalized_context=personalized_context
                )
                
                call_requests.append(call_request)
            
            # Execute bulk calls
            results = await self.bulk_initiate_calls(call_requests)
            
            logger.info(f"Campaign {campaign_id} execution completed: {results['total']} total, {len(results['successful'])} successful, {len(results['failed'])} failed")
            
            return {
                "success": True,
                "campaign_id": campaign_id,
                "results": results,
                "message": f"Campaign started with {len(results['successful'])} calls initiated"
            }
            
        except Exception as e:
            logger.error(f"Error executing campaign: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to execute campaign"
            }
    
    async def get_campaign_status(self, campaign_id: int) -> Dict[str, Any]:
        """
        Get status of all calls in a campaign
        """
        try:
            # Filter active calls for this campaign
            campaign_calls = {
                call_id: call_data 
                for call_id, call_data in self.active_calls.items() 
                if call_data.get("campaign_id") == campaign_id
            }
            
            # Aggregate status
            status_counts = {}
            for call_data in campaign_calls.values():
                status = call_data.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                "campaign_id": campaign_id,
                "total_calls": len(campaign_calls),
                "status_breakdown": status_counts,
                "active_calls": list(campaign_calls.keys())
            }
            
        except Exception as e:
            logger.error(f"Error getting campaign status: {str(e)}")
            return {
                "campaign_id": campaign_id,
                "error": str(e)
            }
    
    async def stop_campaign(self, campaign_id: int) -> Dict[str, Any]:
        """
        Stop all active calls in a campaign
        """
        try:
            # Find all active calls for this campaign
            campaign_calls = [
                call_id for call_id, call_data in self.active_calls.items() 
                if call_data.get("campaign_id") == campaign_id and 
                   call_data.get("status") in [CallStatus.QUEUED, CallStatus.INITIATING, CallStatus.RINGING, CallStatus.CONNECTED]
            ]
            
            results = {
                "cancelled": [],
                "failed_to_cancel": [],
                "total_attempted": len(campaign_calls)
            }
            
            # Cancel each active call
            for call_id in campaign_calls:
                cancel_result = await self.cancel_call(call_id)
                if cancel_result.get("success"):
                    results["cancelled"].append(call_id)
                else:
                    results["failed_to_cancel"].append({
                        "call_id": call_id,
                        "error": cancel_result.get("error")
                    })
            
            logger.info(f"Campaign {campaign_id} stop completed: {len(results['cancelled'])} calls cancelled")
            
            return {
                "success": True,
                "campaign_id": campaign_id,
                "results": results,
                "message": f"Campaign stopped, {len(results['cancelled'])} calls cancelled"
            }
            
        except Exception as e:
            logger.error(f"Error stopping campaign: {str(e)}")
            return {
                "success": False,
                "campaign_id": campaign_id,
                "error": str(e)
            }
    
    async def _generate_personalized_instructions(self, call_request: CallRequest, system_message: str) -> str:
        """
        Generate personalized OpenAI instructions for this specific call
        """
        try:
            # Extract key information from the system message
            student_name = call_request.student_name
            
            # Create specific instructions for this call
            if "Test User" in system_message:
                # Handle Test User case
                instructions = f"""You are calling from Akash Institute to congratulate a student on their excellent academic performance. 

You are calling {student_name} who has achieved 100th rank nationally and has been awarded ₹25,000 scholarship (20% fee waiver) for JEE Preparation course. 

Start with: नमस्ते! मैं अकाश इंस्टिट्यूट से बोल रहा हूं। {student_name} जी, आपको बधाई! आपने राष्ट्रीय स्तर पर 100वीं रैंक हासिल की है और ₹25,000 की छात्रवृत्ति प्राप्त की है।

Always speak in Hindi. Be warm, congratulatory, and helpful. Explain the scholarship benefits and next steps for JEE preparation."""
            else:
                # Generate instructions from the system message
                instructions = f"""You are calling from Akash Institute to congratulate a student on their excellent academic performance.

You are calling {student_name}. Use the following context for this call:

{system_message}

Always speak in Hindi. Be warm, congratulatory, and helpful. Focus on their specific achievements and scholarship details."""
            
            return instructions
            
        except Exception as e:
            logger.error(f"Error generating personalized instructions: {str(e)}")
            return f"You are calling from Akash Institute to speak with {call_request.student_name}. Always speak in Hindi. Be warm and professional."
    
    def _extract_context_variables(self, call_request: CallRequest, system_message: str) -> Dict[str, str]:
        """
        Extract key context variables for the call
        """
        variables = {
            "student_name": call_request.student_name or "Student",
            "phone_number": call_request.phone_number
        }
        
        # Try to extract key information from system message
        if "Test User" in system_message:
            variables.update({
                "student_name": "Test User",
                "rank": "100th nationally",
                "scholarship_amount": "₹25,000",
                "course": "JEE Preparation",
                "greeting": "नमस्ते! मैं अकाश इंस्टिट्यूट से बोल रहा हूं। Test User जी, आपको बधाई!"
            })
        else:
            # Try to extract from call_request data
            if hasattr(call_request, 'scholarship_amount') and call_request.scholarship_amount:
                variables["scholarship_amount"] = f"₹{call_request.scholarship_amount}"
            if hasattr(call_request, 'course') and call_request.course:
                variables["course"] = call_request.course
            if hasattr(call_request, 'parent_name') and call_request.parent_name:
                variables["parent_name"] = call_request.parent_name
                
        return variables
    
    async def _send_context_to_openai_service(self, phone_number: str, instructions: str) -> bool:
        """
        Update the OpenAI service with personalized context by updating compose file and restarting
        This ensures the dynamic context is used for the specific call
        """
        try:
            print(f"🔍 DYNAMIC CONTEXT: Updating OpenAI service for {phone_number}")
            print(f"🔍 CONTEXT PREVIEW: {instructions[:200]}...")
            
            # Store the context in our API for reference
            context_data = {
                "phone_number": phone_number,
                "instructions": instructions
            }
            
            async with httpx.AsyncClient() as client:
                await client.post(
                    "http://localhost:8000/api/v1/context/call-context/update",
                    json=context_data,
                    timeout=5.0
                )
            
            # Update the docker-compose file with personalized instructions
            compose_file = "/home/mason/Desktop/prog/agentchain/agentvoice/forked/avr-infra/docker-compose-openai-realtime.yml"
            
            success = await self._update_compose_file_with_context(compose_file, instructions)
            if not success:
                return False
            
            # Restart the OpenAI service to load new instructions
            restart_cmd = [
                "docker", "compose", "-f", compose_file,
                "restart", "avr-sts-openai"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *restart_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="/home/mason/Desktop/prog/agentchain/agentvoice/forked/avr-infra"
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                print(f"✅ DYNAMIC CONTEXT: OpenAI service restarted with personalized context")
                # Wait for service to fully start
                await asyncio.sleep(3)
                return True
            else:
                print(f"❌ DYNAMIC CONTEXT: Failed to restart service: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"❌ DYNAMIC CONTEXT: Error updating context: {str(e)}")
            logger.error(f"Error updating dynamic context: {str(e)}")
            return False
    
    async def _update_compose_file_with_context(self, compose_file: str, instructions: str) -> bool:
        """
        Update the docker-compose file with personalized OPENAI_INSTRUCTIONS
        """
        try:
            # Read current file
            with open(compose_file, 'r') as f:
                content = f.read()
            
            # Escape the instructions properly for YAML (single line)
            escaped_instructions = instructions.replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
            
            # Find and replace the OPENAI_INSTRUCTIONS section (handle multi-line)
            import re
            # Match the entire OPENAI_INSTRUCTIONS block including multi-line strings
            pattern = r'- "OPENAI_INSTRUCTIONS=.*?"(?=\s*- OPENAI_VOICE|\s*- [A-Z_]+=|\s*#|\s*networks:)'
            replacement = f'- "OPENAI_INSTRUCTIONS={escaped_instructions}"'
            
            new_content = re.sub(pattern, replacement, content, flags=re.DOTALL | re.MULTILINE)
            
            # If the pattern didn't match, try a simpler approach
            if new_content == content:
                print("🔍 COMPOSE UPDATE: Pattern didn't match, trying line-by-line replacement")
                lines = content.split('\n')
                in_openai_instructions = False
                new_lines = []
                
                for line in lines:
                    if 'OPENAI_INSTRUCTIONS=' in line:
                        # Replace with our instructions and mark that we're in the block
                        new_lines.append(f'      - "OPENAI_INSTRUCTIONS={escaped_instructions}"')
                        in_openai_instructions = True
                    elif in_openai_instructions and (line.strip().startswith('- ') or line.strip().startswith('networks:') or line.strip().startswith('#')):
                        # We've reached the next environment variable or section
                        in_openai_instructions = False
                        new_lines.append(line)
                    elif not in_openai_instructions:
                        # Normal line, keep it
                        new_lines.append(line)
                    # Skip lines that are part of the old OPENAI_INSTRUCTIONS block
                
                new_content = '\n'.join(new_lines)
            
            # Write back to file
            with open(compose_file, 'w') as f:
                f.write(new_content)
            
            print(f"✅ COMPOSE UPDATE: Updated docker-compose with personalized instructions")
            print(f"🔍 PREVIEW: {escaped_instructions[:100]}...")
            return True
            
        except Exception as e:
            print(f"❌ COMPOSE UPDATE: Error updating compose file: {str(e)}")
            logger.error(f"Error updating compose file: {str(e)}")
            return False
            
            # Write back to file
            with open(compose_file, 'w') as f:
                f.write(new_content)
            
            print(f"✅ COMPOSE UPDATE: Updated docker-compose with personalized instructions")
            return True
            
        except Exception as e:
            logger.error(f"Error updating compose file: {str(e)}")
            return False
    
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
