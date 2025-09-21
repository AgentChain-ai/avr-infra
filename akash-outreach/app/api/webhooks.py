"""
Webhook endpoints for receiving events from AVR system
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.campaign import Campaign
from ..models.call_log import CallLog
from ..models.student import Student
from ..services.voice_service import get_voice_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

class AVRCallEvent(BaseModel):
    """AVR call event webhook payload"""
    call_id: str
    event_type: str  # call_started, call_connected, call_completed, call_failed
    status: str
    timestamp: datetime
    metadata: Dict[str, Any]
    data: Optional[Dict[str, Any]] = None

@router.post("/avr-events")
async def handle_avr_call_events(
    event: AVRCallEvent,
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint to receive call events from AVR system
    """
    try:
        logger.info(f"Received AVR event: {event.event_type} for call {event.call_id}")
        
        # Extract metadata
        student_id = event.metadata.get("student_id")
        campaign_id = event.metadata.get("campaign_id")
        
        # Process event through voice service
        try:
            voice_service = get_voice_service()
            await voice_service.handle_call_event(event.call_id, event.dict())
        except RuntimeError:
            # Voice service not initialized - log but continue
            logger.warning("Voice service not initialized for webhook processing")
        
        # Update campaign if campaign_id is present
        if campaign_id:
            await _update_campaign_progress(db, campaign_id, event)
        
        # Update or create call log
        await _update_call_log(db, event, student_id, campaign_id)
        
        # Update student record
        if student_id:
            await _update_student_record(db, student_id, event)
        
        db.commit()
        
        return {
            "status": "success", 
            "message": f"Event {event.event_type} processed successfully",
            "call_id": event.call_id
        }
        
    except Exception as e:
        logger.error(f"Error handling AVR webhook event: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process webhook: {str(e)}")

async def _update_campaign_progress(db: Session, campaign_id: int, event: AVRCallEvent):
    """Update campaign progress based on call events"""
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            logger.warning(f"Campaign {campaign_id} not found for call event")
            return
        
        # Update campaign statistics based on event type
        if event.event_type == "call_completed":
            # Could track completion rates, success metrics, etc.
            logger.info(f"Call completed for campaign {campaign_id}")
            
        elif event.event_type == "call_failed":
            # Track failed calls
            logger.info(f"Call failed for campaign {campaign_id}")
            
        # Check if campaign is complete (all calls finished)
        # This is a simplified check - in production you might want more sophisticated logic
        if event.event_type in ["call_completed", "call_failed"]:
            await _check_campaign_completion(db, campaign)
            
    except Exception as e:
        logger.error(f"Error updating campaign progress: {str(e)}")

async def _update_call_log(db: Session, event: AVRCallEvent, student_id: Optional[int], campaign_id: Optional[int]):
    """Update or create call log entry"""
    try:
        # Find existing call log by external_call_id or create new one
        call_log = db.query(CallLog).filter(
            CallLog.conversation_data.contains({"external_call_id": event.call_id})
        ).first()
        
        if not call_log and student_id:
            # Create new call log
            call_log = CallLog(
                student_id=student_id,
                phone_number=event.metadata.get("phone_number", ""),
                call_status=event.status,
                conversation_data={
                    "external_call_id": event.call_id,
                    "campaign_id": campaign_id,
                    "events": []
                },
                created_at=event.timestamp
            )
            db.add(call_log)
        
        if call_log:
            # Update status
            call_log.call_status = event.status
            
            # Add event to conversation data
            conversation_data = call_log.conversation_data or {}
            events = conversation_data.get("events", [])
            events.append({
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "data": event.data
            })
            conversation_data["events"] = events
            
            # Handle specific event types
            if event.event_type == "call_connected":
                conversation_data["started_at"] = event.timestamp.isoformat()
                
            elif event.event_type == "call_completed":
                conversation_data["ended_at"] = event.timestamp.isoformat()
                if event.data:
                    call_log.call_duration = event.data.get("duration", 0)
                    call_log.ai_summary = event.data.get("transcript", "")
                    conversation_data["outcome"] = event.data.get("outcome", "completed")
                    
            elif event.event_type == "call_failed":
                conversation_data["ended_at"] = event.timestamp.isoformat()
                conversation_data["outcome"] = "failed"
                if event.data:
                    conversation_data["failure_reason"] = event.data.get("error_reason", "Unknown error")
            
            call_log.conversation_data = conversation_data
            
    except Exception as e:
        logger.error(f"Error updating call log: {str(e)}")

async def _update_student_record(db: Session, student_id: int, event: AVRCallEvent):
    """Update student record with call information"""
    try:
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            logger.warning(f"Student {student_id} not found for call event")
            return
        
        # Update last call date
        student.last_call_attempt = event.timestamp
        
        # Update call status for completed/failed calls
        if event.event_type == "call_completed":
            student.call_status = event.data.get("outcome", "completed") if event.data else "completed"
            student.last_call_date = event.timestamp
            
        elif event.event_type == "call_failed":
            student.call_status = "failed"
            
    except Exception as e:
        logger.error(f"Error updating student record: {str(e)}")

async def _check_campaign_completion(db: Session, campaign: Campaign):
    """Check if campaign is complete and update status accordingly"""
    try:
        # Simple completion check - in production you might want more sophisticated logic
        # For now, we'll just log that a call finished
        logger.info(f"Call finished for campaign {campaign.id}")
        
        # You could add logic here to:
        # - Count completed vs pending calls
        # - Update campaign status to 'completed' when all calls are done
        # - Send notifications, generate reports, etc.
        
    except Exception as e:
        logger.error(f"Error checking campaign completion: {str(e)}")

@router.get("/health")
async def webhook_health():
    """Health check for webhook service"""
    return {
        "status": "healthy",
        "service": "avr_webhooks",
        "timestamp": datetime.utcnow()
    }
