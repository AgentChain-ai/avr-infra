"""
Campaign management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, time
from pydantic import BaseModel, Field

from ..database import get_db
from ..models.campaign import Campaign
from ..models.student import Student
from ..models.context_info import ContextInfo
from .auth import get_current_user, UserInfo
from ..services.context_generation import ContextGenerationService

router = APIRouter(tags=["campaigns"])

# Pydantic models for request/response
class CampaignCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    context_note_ids: List[int] = Field(..., min_items=1)
    student_ids: List[int] = Field(..., min_items=1)
    call_from_time: str = Field(..., pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")  # HH:MM format
    call_to_time: str = Field(..., pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")    # HH:MM format
    campaign_start_date: Optional[datetime] = None
    campaign_end_date: Optional[datetime] = None

class CampaignUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    context_note_ids: Optional[List[int]] = None
    student_ids: Optional[List[int]] = None
    call_from_time: Optional[str] = Field(None, pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    call_to_time: Optional[str] = Field(None, pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    campaign_start_date: Optional[datetime] = None
    campaign_end_date: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern=r"^(draft|active|paused|completed|cancelled)$")

class CampaignResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    context_note_ids: List[int]
    student_ids: List[int]
    call_from_time: str
    call_to_time: str
    campaign_start_date: Optional[datetime]
    campaign_end_date: Optional[datetime]
    status: str
    total_students: int
    students_called: int
    successful_calls: int
    failed_calls: int
    completion_rate: float
    success_rate: float
    created_by: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    personalized_contexts: Optional[dict] = None

class PersonalizedContext(BaseModel):
    student_id: int
    student_name: str
    phone_number: str
    context: str

class CampaignContexts(BaseModel):
    campaign_id: int
    campaign_name: str
    contexts: List[PersonalizedContext]

# Helper functions
def parse_time_string(time_str: str) -> time:
    """Parse HH:MM time string to time object"""
    try:
        hour, minute = map(int, time_str.split(':'))
        return time(hour=hour, minute=minute)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid time format: {time_str}. Expected HH:MM format."
        )

# API Endpoints

@router.get("/")
async def list_campaigns(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
    # current_user: UserInfo = Depends(get_current_user)  # Temporarily disabled for testing
):
    """Get list of campaigns with optional status filter"""
    
    query = db.query(Campaign)
    
    if status:
        query = query.filter(Campaign.status == status)
    
    campaigns = query.offset(skip).limit(limit).all()
    
    return [CampaignResponse(**campaign.to_dict()) for campaign in campaigns]

@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Get specific campaign details"""
    
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    return CampaignResponse(**campaign.to_dict())

@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    campaign_data: CampaignCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create new campaign and generate personalized contexts"""
    
    # Validate context note IDs exist
    existing_contexts = db.query(ContextInfo).filter(
        ContextInfo.id.in_(campaign_data.context_note_ids)
    ).all()
    
    if len(existing_contexts) != len(campaign_data.context_note_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more context note IDs are invalid"
        )
    
    # Validate student IDs exist
    existing_students = db.query(Student).filter(
        Student.id.in_(campaign_data.student_ids)
    ).all()
    
    if len(existing_students) != len(campaign_data.student_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more student IDs are invalid"
        )
    
    # Parse time strings
    call_from_time = parse_time_string(campaign_data.call_from_time)
    call_to_time = parse_time_string(campaign_data.call_to_time)
    
    # Validate time range
    if call_from_time >= call_to_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Call start time must be before end time"
        )
    
    # Create campaign
    campaign = Campaign(
        name=campaign_data.name,
        description=campaign_data.description,
        context_note_ids=campaign_data.context_note_ids,
        student_ids=campaign_data.student_ids,
        call_from_time=call_from_time,
        call_to_time=call_to_time,
        campaign_start_date=campaign_data.campaign_start_date,
        campaign_end_date=campaign_data.campaign_end_date,
        total_students=len(campaign_data.student_ids),
        created_by=current_user.username,  # Use authenticated username
        status="draft"
    )
    
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    
    print(f"🔍 DEBUG: Campaign {campaign.id} created successfully")

    # Generate personalized contexts for all students
    try:
        print(f"🔍 DEBUG: Starting context generation for campaign {campaign.id}")
        context_service = ContextGenerationService(db)
        personalized_contexts = await context_service.generate_campaign_contexts(
            campaign.id, existing_contexts, existing_students
        )
        
        print(f"🔍 DEBUG: Context generation completed. Result type: {type(personalized_contexts)}")
        print(f"🔍 DEBUG: Number of contexts generated: {len(personalized_contexts) if personalized_contexts else 0}")
        
        if personalized_contexts:
            print(f"🔍 DEBUG: Context keys: {list(personalized_contexts.keys())}")
            
        # Update campaign with generated contexts
        print(f"🔍 DEBUG: Updating campaign {campaign.id} with contexts...")
        campaign.personalized_contexts = personalized_contexts
        db.commit()
        db.refresh(campaign)
        
        print(f"🔍 DEBUG: Campaign updated. Final personalized_contexts value: {campaign.personalized_contexts}")
        
    except Exception as e:
        # If context generation fails, still create the campaign but log the error
        error_msg = f"Warning: Failed to generate contexts for campaign {campaign.id}: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
    
    return CampaignResponse(**campaign.to_dict())

@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    campaign_data: CampaignUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update campaign"""
    
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Update fields if provided
    update_data = campaign_data.dict(exclude_unset=True)
    
    # Handle time fields specially
    if "call_from_time" in update_data:
        update_data["call_from_time"] = parse_time_string(update_data["call_from_time"])
    
    if "call_to_time" in update_data:
        update_data["call_to_time"] = parse_time_string(update_data["call_to_time"])
    
    # Validate time range if both times are being updated
    if "call_from_time" in update_data and "call_to_time" in update_data:
        if update_data["call_from_time"] >= update_data["call_to_time"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Call start time must be before end time"
            )
    
    # Update student count if student_ids changed
    if "student_ids" in update_data:
        update_data["total_students"] = len(update_data["student_ids"])
    
    # Apply updates
    for field, value in update_data.items():
        setattr(campaign, field, value)
    
    campaign.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(campaign)
    
    return CampaignResponse(**campaign.to_dict())

@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete campaign"""
    
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Only allow deletion of draft campaigns
    if campaign.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft campaigns can be deleted"
        )
    
    db.delete(campaign)
    db.commit()
    
    return {"message": "Campaign deleted successfully"}

@router.get("/{campaign_id}/contexts", response_model=CampaignContexts)
async def get_campaign_contexts(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get personalized contexts for all students in campaign"""
    
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Get student data
    students = db.query(Student).filter(Student.id.in_(campaign.student_ids)).all()
    student_map = {student.id: student for student in students}
    
    contexts = []
    personalized_contexts = campaign.personalized_contexts or {}
    
    for student_id in campaign.student_ids:
        student = student_map.get(student_id)
        if student:
            context = personalized_contexts.get(str(student_id), "Context not generated")
            contexts.append(PersonalizedContext(
                student_id=student_id,
                student_name=student.get_field_value("student_name", "Unknown"),
                phone_number=student.phone_number,
                context=context
            ))
    
    return CampaignContexts(
        campaign_id=campaign.id,
        campaign_name=campaign.name,
        contexts=contexts
    )

@router.post("/{campaign_id}/regenerate-contexts")
async def regenerate_contexts(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Regenerate personalized contexts for campaign"""
    
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Get contexts and students
    contexts = db.query(ContextInfo).filter(
        ContextInfo.id.in_(campaign.context_note_ids)
    ).all()
    
    students = db.query(Student).filter(
        Student.id.in_(campaign.student_ids)
    ).all()
    
    # Regenerate contexts
    try:
        context_service = ContextGenerationService(db)
        personalized_contexts = await context_service.generate_campaign_contexts(
            campaign.id, contexts, students
        )
        
        # Update campaign
        campaign.personalized_contexts = personalized_contexts
        campaign.updated_at = datetime.utcnow()
        db.commit()
        
        return {"message": "Contexts regenerated successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate contexts: {str(e)}"
        )

@router.post("/{campaign_id}/activate")
async def activate_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Activate campaign to start calling"""
    
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    if campaign.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft campaigns can be activated"
        )
    
    campaign.status = "active"
    campaign.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Campaign activated successfully"}

@router.post("/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Pause active campaign"""
    
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    if campaign.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only active campaigns can be paused"
        )
    
    campaign.status = "paused"
    campaign.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Campaign paused successfully"}

@router.put("/{campaign_id}/contexts/{student_id}")
async def update_student_context(
    campaign_id: int,
    student_id: int,
    context_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update personalized context for a specific student in a campaign"""
    
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Update the context for the specific student
    personalized_contexts = campaign.personalized_contexts or {}
    
    if str(student_id) not in personalized_contexts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student context not found in campaign"
        )
    
    # Update the context text
    new_context = context_data.get("context", "")
    personalized_contexts[str(student_id)]["context"] = new_context
    
    # Use flag_modified to ensure SQLAlchemy knows the JSON field changed
    from sqlalchemy.orm.attributes import flag_modified
    campaign.personalized_contexts = personalized_contexts
    flag_modified(campaign, "personalized_contexts")
    campaign.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(campaign)
    
    return {
        "message": "Student context updated successfully",
        "student_id": student_id,
        "updated_context": personalized_contexts[str(student_id)]
    }
