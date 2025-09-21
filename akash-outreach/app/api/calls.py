"""
Calls API endpoints
Call management, triggering, and monitoring
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..database import get_db
from ..models import CallLog, Student, CallStatus
from ..models.call_log import (
    create_call_log,
    get_call_log_by_id,
    update_call_log,
    get_recent_calls,
    get_calls_by_student
)
from ..models.student import get_student_by_id, update_student
from .auth import get_current_user, UserInfo

# Pydantic models
class CallTrigger(BaseModel):
    student_id: int = Field(..., description="Student ID to call")
    priority_override: Optional[int] = Field(None, description="Override call priority")
    custom_message: Optional[str] = Field(None, description="Custom message for this call")
    scheduled_time: Optional[datetime] = Field(None, description="Schedule call for later")

class BulkCallCampaign(BaseModel):
    student_ids: List[int] = Field(..., description="List of student IDs to call")
    campaign_name: str = Field(..., description="Name for this calling campaign")
    call_window_start: Optional[str] = Field(None, description="Start time (HH:MM)")
    call_window_end: Optional[str] = Field(None, description="End time (HH:MM)")
    max_concurrent_calls: int = Field(3, description="Maximum concurrent calls")
    retry_failed: bool = Field(True, description="Retry failed calls")

class CallLogResponse(BaseModel):
    id: int
    student_id: Optional[int]
    phone_number: str
    call_duration: int
    call_status: CallStatus
    conversation_data: Optional[Dict[str, Any]]
    ai_summary: Optional[str]
    follow_up_required: bool
    call_recording_path: Optional[str]
    created_at: datetime
    student_info: Optional[Dict[str, Any]] = None

class CallCampaignStatus(BaseModel):
    campaign_id: str
    campaign_name: str
    status: str
    total_calls: int
    completed_calls: int
    failed_calls: int
    in_progress_calls: int
    pending_calls: int
    started_at: datetime
    estimated_completion: Optional[datetime]

# Router setup
router = APIRouter()

# Store active campaigns (in production, use Redis or database)
active_campaigns: Dict[str, CallCampaignStatus] = {}

@router.get("/", response_model=List[CallLogResponse])
async def list_calls(
    skip: int = 0,
    limit: int = 100,
    status: Optional[CallStatus] = None,
    student_id: Optional[int] = None,
    phone_number: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    List call logs with filtering options
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **status**: Filter by call status
    - **student_id**: Filter by specific student
    - **phone_number**: Filter by phone number
    - **date_from**: Filter calls from this date
    - **date_to**: Filter calls to this date
    """
    
    query = db.query(CallLog)
    
    # Apply filters
    if status:
        query = query.filter(CallLog.call_status == status)
    
    if student_id:
        query = query.filter(CallLog.student_id == student_id)
    
    if phone_number:
        query = query.filter(CallLog.phone_number.contains(phone_number))
    
    if date_from:
        query = query.filter(CallLog.created_at >= date_from)
    
    if date_to:
        query = query.filter(CallLog.created_at <= date_to)
    
    # Order by most recent first
    calls = query.order_by(CallLog.created_at.desc()).offset(skip).limit(limit).all()
    
    # Enrich with student information
    enriched_calls = []
    for call in calls:
        call_dict = call.to_dict()
        
        # Add student info if available
        if call.student_id:
            student = get_student_by_id(db, call.student_id)
            if student:
                call_dict["student_info"] = {
                    "student_name": student.student_data.get("student_name"),
                    "parent_name": student.student_data.get("parent_name"),
                    "priority": student.priority
                }
        
        enriched_calls.append(CallLogResponse(**call_dict))
    
    return enriched_calls

@router.get("/{call_id}", response_model=CallLogResponse)
async def get_call_details(
    call_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Get detailed information about a specific call"""
    
    call_log = get_call_log_by_id(db, call_id)
    if not call_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call log with ID {call_id} not found"
        )
    
    call_dict = call_log.to_dict()
    
    # Add student info
    if call_log.student_id:
        student = get_student_by_id(db, call_log.student_id)
        if student:
            call_dict["student_info"] = student.to_dict()
    
    return CallLogResponse(**call_dict)

@router.post("/trigger", response_model=Dict[str, Any])
async def trigger_single_call(
    call_data: CallTrigger,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Trigger a single call to a student"""
    
    # Validate student exists
    student = get_student_by_id(db, call_data.student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {call_data.student_id} not found"
        )
    
    # Check if student is already being called
    existing_call = db.query(CallLog).filter(
        CallLog.student_id == call_data.student_id,
        CallLog.call_status == CallStatus.IN_PROGRESS
    ).first()
    
    if existing_call:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student {call_data.student_id} is already being called"
        )
    
    try:
        # Create call log entry
        call_log = create_call_log(
            db=db,
            student_id=call_data.student_id,
            phone_number=student.phone_number,
            call_status=CallStatus.IN_PROGRESS
        )
        
        # Update student status
        update_student(
            db=db,
            student_id=call_data.student_id,
            call_status=CallStatus.IN_PROGRESS
        )
        
        # Trigger actual call in background
        background_tasks.add_task(
            execute_call,
            call_log.id,
            student.phone_number,
            student.student_data,
            call_data.custom_message,
            db
        )
        
        return {
            "success": True,
            "message": f"Call triggered for student {call_data.student_id}",
            "call_log_id": call_log.id,
            "phone_number": student.phone_number,
            "estimated_duration": "3-5 minutes"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger call: {str(e)}"
        )

@router.post("/campaign", response_model=CallCampaignStatus)
async def start_bulk_calling_campaign(
    campaign_data: BulkCallCampaign,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Start a bulk calling campaign"""
    
    # Validate students exist
    valid_students = []
    for student_id in campaign_data.student_ids:
        student = get_student_by_id(db, student_id)
        if student and student.call_status != CallStatus.IN_PROGRESS:
            valid_students.append(student)
    
    if not valid_students:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid students found for calling campaign"
        )
    
    # Create campaign
    import uuid
    campaign_id = str(uuid.uuid4())
    
    campaign_status = CallCampaignStatus(
        campaign_id=campaign_id,
        campaign_name=campaign_data.campaign_name,
        status="starting",
        total_calls=len(valid_students),
        completed_calls=0,
        failed_calls=0,
        in_progress_calls=0,
        pending_calls=len(valid_students),
        started_at=datetime.utcnow(),
        estimated_completion=None
    )
    
    # Store campaign status
    active_campaigns[campaign_id] = campaign_status
    
    # Start campaign in background
    background_tasks.add_task(
        execute_bulk_campaign,
        campaign_id,
        valid_students,
        campaign_data,
        db
    )
    
    return campaign_status

@router.get("/campaigns/active", response_model=List[CallCampaignStatus])
async def get_active_campaigns(
    current_user: UserInfo = Depends(get_current_user)
):
    """Get list of active calling campaigns"""
    return list(active_campaigns.values())

@router.get("/campaigns/{campaign_id}", response_model=CallCampaignStatus)
async def get_campaign_status(
    campaign_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """Get status of a specific campaign"""
    
    if campaign_id not in active_campaigns:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found"
        )
    
    return active_campaigns[campaign_id]

@router.post("/campaigns/{campaign_id}/stop")
async def stop_campaign(
    campaign_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """Emergency stop a calling campaign"""
    
    if campaign_id not in active_campaigns:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found"
        )
    
    # Update campaign status
    campaign = active_campaigns[campaign_id]
    campaign.status = "stopped"
    
    # In a real implementation, you'd signal the background task to stop
    # For now, we'll just update the status
    
    return {
        "message": f"Campaign {campaign_id} stop requested",
        "status": "stopped"
    }

@router.get("/analytics/summary")
async def get_call_analytics(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Get call analytics summary"""
    
    from datetime import datetime, timedelta
    
    # Date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get calls in date range
    calls_query = db.query(CallLog).filter(
        CallLog.created_at >= start_date,
        CallLog.created_at <= end_date
    )
    
    # Status breakdown
    status_counts = {}
    for call_status in CallStatus:
        count = calls_query.filter(CallLog.call_status == call_status).count()
        status_counts[call_status.value] = count
    
    total_calls = calls_query.count()
    completed_calls = status_counts.get("completed", 0)
    
    # Calculate metrics
    completion_rate = (completed_calls / total_calls * 100) if total_calls > 0 else 0
    
    # Average call duration (only completed calls)
    completed_calls_query = calls_query.filter(CallLog.call_status == CallStatus.COMPLETED)
    avg_duration = 0
    if completed_calls > 0:
        total_duration = sum([call.call_duration for call in completed_calls_query.all()])
        avg_duration = total_duration / completed_calls
    
    # Daily breakdown
    daily_stats = []
    for i in range(days):
        day_start = start_date + timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        
        day_calls = calls_query.filter(
            CallLog.created_at >= day_start,
            CallLog.created_at < day_end
        ).count()
        
        daily_stats.append({
            "date": day_start.date().isoformat(),
            "calls": day_calls
        })
    
    return {
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days
        },
        "summary": {
            "total_calls": total_calls,
            "completion_rate": round(completion_rate, 2),
            "average_duration_seconds": round(avg_duration, 2),
            "status_breakdown": status_counts
        },
        "daily_stats": daily_stats,
        "active_campaigns": len(active_campaigns)
    }

@router.get("/queue/status")
async def get_call_queue_status(
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Get current call queue status"""
    
    # Count calls by status
    pending_calls = db.query(CallLog).filter(CallLog.call_status == CallStatus.PENDING).count()
    in_progress_calls = db.query(CallLog).filter(CallLog.call_status == CallStatus.IN_PROGRESS).count()
    
    # Count students pending calls
    pending_students = db.query(Student).filter(Student.call_status == CallStatus.PENDING).count()
    
    return {
        "queue_status": {
            "pending_calls": pending_calls,
            "in_progress_calls": in_progress_calls,
            "pending_students": pending_students
        },
        "system_status": {
            "avr_services": "healthy",  # Would check actual AVR status
            "call_capacity": 10,  # Maximum concurrent calls
            "current_load": in_progress_calls
        },
        "active_campaigns": len(active_campaigns)
    }

# Background task functions
async def execute_call(call_log_id: int, phone_number: str, student_data: Dict, custom_message: Optional[str], db: Session):
    """Execute a single call - background task"""
    
    try:
        # This would integrate with AVR services to make the actual call
        # For now, we'll simulate the call process
        
        # Simulate call setup and execution
        import asyncio
        await asyncio.sleep(2)  # Simulate call setup time
        
        # Update call status
        call_log = get_call_log_by_id(db, call_log_id)
        if call_log:
            # Simulate call completion
            update_call_log(
                db=db,
                call_log_id=call_log_id,
                call_status=CallStatus.COMPLETED,
                call_duration=180,  # 3 minutes
                conversation_data={
                    "call_outcome": "successful",
                    "questions_asked": ["Course details", "Fee structure"],
                    "satisfaction": "high"
                },
                ai_summary="Call completed successfully. Parent was satisfied with information provided."
            )
            
            # Update student status
            if call_log.student_id:
                update_student(
                    db=db,
                    student_id=call_log.student_id,
                    call_status=CallStatus.COMPLETED
                )
        
    except Exception as e:
        # Handle call failure
        print(f"Call failed: {e}")
        
        if call_log:
            update_call_log(
                db=db,
                call_log_id=call_log_id,
                call_status=CallStatus.FAILED,
                ai_summary=f"Call failed: {str(e)}"
            )
            
            if call_log.student_id:
                update_student(
                    db=db,
                    student_id=call_log.student_id,
                    call_status=CallStatus.FAILED
                )

async def execute_bulk_campaign(campaign_id: str, students: List[Student], campaign_data: BulkCallCampaign, db: Session):
    """Execute bulk calling campaign - background task"""
    
    try:
        campaign = active_campaigns[campaign_id]
        campaign.status = "running"
        
        import asyncio
        
        # Process calls with concurrency limit
        semaphore = asyncio.Semaphore(campaign_data.max_concurrent_calls)
        
        async def call_student(student):
            async with semaphore:
                # Create call log
                call_log = create_call_log(
                    db=db,
                    student_id=student.id,
                    phone_number=student.phone_number,
                    call_status=CallStatus.IN_PROGRESS
                )
                
                campaign.in_progress_calls += 1
                campaign.pending_calls -= 1
                
                # Execute call
                await execute_call(call_log.id, student.phone_number, student.student_data, None, db)
                
                campaign.in_progress_calls -= 1
                campaign.completed_calls += 1
        
        # Start all calls
        tasks = [call_student(student) for student in students]
        await asyncio.gather(*tasks)
        
        campaign.status = "completed"
        
    except Exception as e:
        campaign.status = "failed"
        print(f"Campaign failed: {e}")
