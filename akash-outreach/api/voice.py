"""
Voice Integration API Endpoints
Handles voice calling operations and webhooks
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

from services.voice_service import get_voice_service, CallRequest, CallStatus, CallOutcome
from services.database import get_db
from models.calls import Call
from models.students import Student
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["voice"])

# Request/Response Models
class InitiateCallRequest(BaseModel):
    student_id: int
    priority: Optional[int] = 5
    campaign_id: Optional[int] = None

class BulkCallRequest(BaseModel):
    student_ids: List[int]
    priority: Optional[int] = 5
    campaign_id: Optional[int] = None

class CallEventWebhook(BaseModel):
    call_id: str
    event_type: str
    status: str
    timestamp: datetime
    data: Dict[str, Any]

class CallStatusResponse(BaseModel):
    call_id: str
    student_id: int
    phone_number: str
    status: CallStatus
    initiated_at: datetime
    updated_at: Optional[datetime] = None
    duration: Optional[int] = None
    outcome: Optional[CallOutcome] = None

@router.post("/initiate-call")
async def initiate_call(
    request: InitiateCallRequest,
    db: Session = Depends(get_db)
):
    """
    Initiate a voice call for a specific student
    """
    try:
        # Get student details
        student = db.query(Student).filter(Student.id == request.student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Prepare call request
        call_request = CallRequest(
            student_id=student.id,
            phone_number=student.phone_number,
            student_name=student.student_data.get("student_name", "Student"),
            parent_name=student.student_data.get("parent_name"),
            scholarship_amount=student.student_data.get("scholarship_amount"),
            course=student.student_data.get("course"),
            priority=request.priority,
            context_data=student.student_data,
            campaign_id=request.campaign_id
        )
        
        # Initiate call through voice service
        voice_service = get_voice_service()
        result = await voice_service.initiate_call(call_request)
        
        if result.get("success"):
            # Create call record in database
            call_record = Call(
                student_id=student.id,
                campaign_id=request.campaign_id,
                call_status="queued",
                priority=request.priority,
                external_call_id=result.get("call_id"),
                initiated_at=datetime.utcnow()
            )
            db.add(call_record)
            db.commit()
            
            # Update student call count
            student.call_count = (student.call_count or 0) + 1
            student.last_call_attempt = datetime.utcnow()
            db.commit()
            
            logger.info(f"Call initiated for student {student.id}: {result.get('call_id')}")
            
            return {
                "success": True,
                "call_id": result.get("call_id"),
                "student_id": student.id,
                "status": "queued",
                "message": "Call initiated successfully"
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Call initiation failed"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating call: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk-initiate")
async def bulk_initiate_calls(
    request: BulkCallRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Initiate multiple calls in bulk
    """
    try:
        # Get students
        students = db.query(Student).filter(Student.id.in_(request.student_ids)).all()
        
        if not students:
            raise HTTPException(status_code=404, detail="No students found")
        
        # Prepare call requests
        call_requests = []
        for student in students:
            call_request = CallRequest(
                student_id=student.id,
                phone_number=student.phone_number,
                student_name=student.student_data.get("student_name", "Student"),
                parent_name=student.student_data.get("parent_name"),
                scholarship_amount=student.student_data.get("scholarship_amount"),
                course=student.student_data.get("course"),
                priority=request.priority,
                context_data=student.student_data,
                campaign_id=request.campaign_id
            )
            call_requests.append(call_request)
        
        # Add to background task for processing
        background_tasks.add_task(
            process_bulk_calls,
            call_requests,
            request.campaign_id,
            request.priority
        )
        
        return {
            "success": True,
            "message": f"Bulk call initiation started for {len(students)} students",
            "student_count": len(students),
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating bulk calls: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_bulk_calls(
    call_requests: List[CallRequest],
    campaign_id: Optional[int],
    priority: int
):
    """
    Background task to process bulk calls
    """
    try:
        voice_service = get_voice_service()
        results = await voice_service.bulk_initiate_calls(call_requests)
        
        # Log results
        logger.info(f"Bulk call processing completed: {results['success_rate']:.2%} success rate")
        
        # Here you would typically update the database with results
        # and send notifications about completion
        
    except Exception as e:
        logger.error(f"Error processing bulk calls: {str(e)}")

@router.get("/active-calls")
async def get_active_calls():
    """
    Get all currently active calls
    """
    try:
        voice_service = get_voice_service()
        active_calls = await voice_service.get_active_calls()
        
        return {
            "active_calls": active_calls,
            "count": len(active_calls)
        }
        
    except Exception as e:
        logger.error(f"Error getting active calls: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/call-status/{call_id}")
async def get_call_status(call_id: str):
    """
    Get status of a specific call
    """
    try:
        voice_service = get_voice_service()
        call_status = await voice_service.get_call_status(call_id)
        
        if call_status:
            return call_status
        else:
            raise HTTPException(status_code=404, detail="Call not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting call status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cancel-call/{call_id}")
async def cancel_call(call_id: str, db: Session = Depends(get_db)):
    """
    Cancel an active call
    """
    try:
        voice_service = get_voice_service()
        result = await voice_service.cancel_call(call_id)
        
        if result.get("success"):
            # Update database record
            call_record = db.query(Call).filter(Call.external_call_id == call_id).first()
            if call_record:
                call_record.call_status = "cancelled"
                call_record.call_outcome = "cancelled"
                call_record.ended_at = datetime.utcnow()
                db.commit()
            
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to cancel call"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling call: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhooks/call-events")
async def handle_call_events(
    webhook_data: CallEventWebhook,
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint to receive call events from AVR system
    """
    try:
        # Process event through voice service
        voice_service = get_voice_service()
        result = await voice_service.handle_call_event(
            webhook_data.call_id,
            webhook_data.dict()
        )
        
        # Update database record
        call_record = db.query(Call).filter(
            Call.external_call_id == webhook_data.call_id
        ).first()
        
        if call_record:
            # Update call status
            call_record.call_status = webhook_data.status
            
            # Handle specific events
            if webhook_data.event_type == "call_connected":
                call_record.started_at = webhook_data.timestamp
                
            elif webhook_data.event_type == "call_completed":
                call_record.ended_at = webhook_data.timestamp
                call_record.duration = webhook_data.data.get("duration")
                call_record.call_outcome = webhook_data.data.get("outcome", "completed")
                call_record.transcript = webhook_data.data.get("transcript", "")
                call_record.ai_summary = webhook_data.data.get("ai_summary", "")
                
                # Update student record
                student = db.query(Student).filter(Student.id == call_record.student_id).first()
                if student:
                    student.call_status = call_record.call_outcome
                    student.last_call_attempt = webhook_data.timestamp
                
            elif webhook_data.event_type == "call_failed":
                call_record.ended_at = webhook_data.timestamp
                call_record.call_outcome = "failed"
                call_record.failure_reason = webhook_data.data.get("error_reason", "Unknown error")
            
            db.commit()
            
            logger.info(f"Processed webhook event: {webhook_data.event_type} for call {webhook_data.call_id}")
        
        return {"status": "success", "message": "Event processed successfully"}
        
    except Exception as e:
        logger.error(f"Error handling webhook event: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics")
async def get_voice_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """
    Get voice call analytics
    """
    try:
        voice_service = get_voice_service()
        analytics = await voice_service.get_call_analytics(start_date, end_date)
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting voice analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/queue/start")
async def start_call_queue(
    limit: Optional[int] = None,
    priority_min: Optional[int] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Start processing the call queue
    """
    try:
        # Get students from queue
        query = db.query(Student).filter(
            Student.call_status.in_(["pending", "retry", "callback_requested"])
        )
        
        if priority_min:
            query = query.filter(Student.priority >= priority_min)
        
        query = query.order_by(Student.priority.desc(), Student.created_at.asc())
        
        if limit:
            query = query.limit(limit)
        
        students = query.all()
        
        if not students:
            return {
                "success": True,
                "message": "No students in queue",
                "initiated_calls": 0
            }
        
        # Prepare bulk call request
        bulk_request = BulkCallRequest(
            student_ids=[s.id for s in students],
            priority=priority_min or 5
        )
        
        # Process in background
        background_tasks.add_task(
            process_queue_calls,
            bulk_request,
            db
        )
        
        return {
            "success": True,
            "message": f"Queue processing started for {len(students)} students",
            "initiated_calls": len(students)
        }
        
    except Exception as e:
        logger.error(f"Error starting call queue: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_queue_calls(bulk_request: BulkCallRequest, db: Session):
    """
    Background task to process queue calls
    """
    try:
        # Get students
        students = db.query(Student).filter(Student.id.in_(bulk_request.student_ids)).all()
        
        # Prepare call requests
        call_requests = []
        for student in students:
            call_request = CallRequest(
                student_id=student.id,
                phone_number=student.phone_number,
                student_name=student.student_data.get("student_name", "Student"),
                parent_name=student.student_data.get("parent_name"),
                scholarship_amount=student.student_data.get("scholarship_amount"),
                course=student.student_data.get("course"),
                priority=bulk_request.priority,
                context_data=student.student_data,
                campaign_id=bulk_request.campaign_id
            )
            call_requests.append(call_request)
        
        # Process calls
        voice_service = get_voice_service()
        results = await voice_service.bulk_initiate_calls(call_requests)
        
        logger.info(f"Queue processing completed: {results['success_rate']:.2%} success rate")
        
    except Exception as e:
        logger.error(f"Error processing queue calls: {str(e)}")

# Health check endpoint
@router.get("/health")
async def voice_service_health():
    """
    Check voice service health
    """
    try:
        voice_service = get_voice_service()
        # Basic health check - you could ping AVR service here
        
        return {
            "status": "healthy",
            "service": "voice_integration",
            "timestamp": datetime.utcnow(),
            "active_calls_count": len(await voice_service.get_active_calls())
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "voice_integration",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }
