"""
Students API endpoints
Comprehensive CRUD operations for student management
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import io
import pandas as pd

from ..database import get_db
from ..models import Student, CallStatus
from ..models.student import create_student, get_student_by_id, update_student, delete_student
from ..models.field_config import get_active_fields
from ..services.csv_processor import CSVProcessor
from .auth import get_current_user, UserInfo

# Pydantic models for API
class StudentCreate(BaseModel):
    phone_number: str = Field(..., description="Student's phone number", max_length=15)
    student_data: Dict[str, Any] = Field(..., description="Dynamic student data as JSON")
    priority: Optional[int] = Field(0, description="Call priority (higher = more urgent)")

class StudentUpdate(BaseModel):
    phone_number: Optional[str] = Field(None, max_length=15)
    student_data: Optional[Dict[str, Any]] = None
    call_status: Optional[CallStatus] = None
    priority: Optional[int] = None

class StudentResponse(BaseModel):
    model_config = ConfigDict(extra="allow")  # Allow additional fields from student_data
    
    id: int
    phone_number: str
    call_status: CallStatus
    call_count: int
    priority: int
    last_call_attempt: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Additional computed fields that to_dict() includes
    display_name: Optional[str] = None
    is_pending: Optional[bool] = None
    is_completed: Optional[bool] = None

class StudentListResponse(BaseModel):
    students: List[StudentResponse]
    total: int
    skip: int
    limit: int
    filters_applied: Dict[str, Any]

class BulkUploadResponse(BaseModel):
    success: bool
    message: str
    processed_count: int
    error_count: int
    warnings: List[str]
    field_mapping: Dict[str, str]
    sample_data: List[Dict[str, Any]]

# Router setup
router = APIRouter()

@router.get("/", response_model=StudentListResponse)
async def list_students(
    skip: int = 0,
    limit: int = 100,
    status: Optional[CallStatus] = None,
    search: Optional[str] = None,
    priority_min: Optional[int] = None,
    phone_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    List students with comprehensive filtering options
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **status**: Filter by call status
    - **search**: Search in student data (JSON search)
    - **priority_min**: Minimum priority level
    - **phone_filter**: Filter by phone number pattern
    """
    
    query = db.query(Student)
    filters_applied = {}
    
    # Apply filters
    if status:
        query = query.filter(Student.call_status == status)
        filters_applied["status"] = status
    
    if priority_min is not None:
        query = query.filter(Student.priority >= priority_min)
        filters_applied["priority_min"] = priority_min
    
    if phone_filter:
        query = query.filter(Student.phone_number.contains(phone_filter))
        filters_applied["phone_filter"] = phone_filter
    
    if search:
        # Search in JSON student_data (SQLite JSON support)
        query = query.filter(
            or_(
                Student.phone_number.contains(search),
                Student.student_data.op("json_extract")("$.student_name").contains(search),
                Student.student_data.op("json_extract")("$.parent_name").contains(search)
            )
        )
        filters_applied["search"] = search
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination and ordering
    students = query.order_by(Student.priority.desc(), Student.created_at.desc()).offset(skip).limit(limit).all()
    
    return StudentListResponse(
        students=[StudentResponse(**student.to_dict()) for student in students],
        total=total,
        skip=skip,
        limit=limit,
        filters_applied=filters_applied
    )

@router.post("/", response_model=StudentResponse)
async def create_new_student(
    student_data: StudentCreate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Create a new student record"""
    
    # Check if phone number already exists
    existing_student = db.query(Student).filter(Student.phone_number == student_data.phone_number).first()
    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student with phone number {student_data.phone_number} already exists"
        )
    
    # Validate student_data against field configurations
    field_configs = get_active_fields(db)
    validation_errors = []
    
    for field_config in field_configs:
        if field_config.is_required and field_config.field_name not in student_data.student_data:
            validation_errors.append(f"Required field '{field_config.field_label}' is missing")
    
    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation errors: {', '.join(validation_errors)}"
        )
    
    # Create student
    new_student = create_student(
        db=db,
        phone_number=student_data.phone_number,
        student_data=student_data.student_data,
        priority=student_data.priority
    )
    
    return StudentResponse(**new_student.to_dict())

@router.get("/search", response_model=StudentListResponse)
async def search_students(
    q: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Search students by name, phone, or other data"""
    
    # Use the same search logic as the main list endpoint
    query = db.query(Student)
    
    # Search in JSON student_data using proper SQLite JSON syntax
    search_filter = or_(
        Student.phone_number.contains(q),
        func.json_extract(Student.student_data, '$.student_name').contains(q),
        func.json_extract(Student.student_data, '$.parent_name').contains(q)
    )
    query = query.filter(search_filter)
    
    # Get results with pagination
    total = query.count()
    students = query.offset(skip).limit(limit).all()
    
    return StudentListResponse(
        students=[StudentResponse(**student.to_dict()) for student in students],
        total=total,
        skip=skip,
        limit=limit,
        filters_applied={"search": q}
    )

@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Get a specific student by ID"""
    
    student = get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found"
        )
    
    return StudentResponse(**student.to_dict())

@router.put("/{student_id}", response_model=StudentResponse)
async def update_student_record(
    student_id: int,
    update_data: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Update a student record"""
    
    student = get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found"
        )
    
    # Check for phone number conflicts if updating phone
    if update_data.phone_number and update_data.phone_number != student.phone_number:
        existing = db.query(Student).filter(
            and_(
                Student.phone_number == update_data.phone_number,
                Student.id != student_id
            )
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Phone number {update_data.phone_number} is already in use"
            )
    
    # Update student
    updated_student = update_student(
        db=db,
        student_id=student_id,
        phone_number=update_data.phone_number,
        student_data=update_data.student_data,
        call_status=update_data.call_status,
        priority=update_data.priority
    )
    
    return StudentResponse(**updated_student.to_dict())

@router.delete("/{student_id}")
async def delete_student_record(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Delete a student record"""
    
    student = get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found"
        )
    
    success = delete_student(db, student_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete student"
        )
    
    return {"message": f"Student {student_id} deleted successfully"}

@router.post("/upload", response_model=BulkUploadResponse)
async def upload_students_csv(
    file: UploadFile = File(..., description="CSV or Excel file with student data"),
    field_mapping: Optional[str] = Form(None, description="JSON field mapping override"),
    auto_map: bool = Form(True, description="Use AI to automatically map fields"),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Upload students from CSV/Excel file with AI-powered field mapping
    
    The system will automatically detect and map fields based on column headers.
    You can override the mapping by providing a field_mapping JSON.
    """
    
    # Validate file type
    if not file.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be CSV or Excel format (.csv, .xlsx, .xls)"
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Initialize CSV processor
        processor = CSVProcessor(db)
        
        # Process the file
        if auto_map:
            # Use AI to analyze and map fields
            result = await processor.process_file_with_ai(content, file.filename)
        else:
            # Use manual field mapping
            mapping_dict = json.loads(field_mapping) if field_mapping else {}
            result = await processor.process_file_manual(content, file.filename, mapping_dict)
        
        return BulkUploadResponse(
            success=result["success"],
            message=result["message"],
            processed_count=result["processed_count"],
            error_count=result["error_count"],
            warnings=result["warnings"],
            field_mapping=result["field_mapping"],
            sample_data=result["sample_data"][:5]  # Return first 5 rows as sample
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )

@router.get("/export/csv")
async def export_students_csv(
    status: Optional[CallStatus] = None,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Export students data as CSV"""
    
    from fastapi.responses import StreamingResponse
    
    # Get students data
    query = db.query(Student)
    if status:
        query = query.filter(Student.call_status == status)
    
    students = query.all()
    
    # Convert to DataFrame
    data = []
    for student in students:
        row = {
            "id": student.id,
            "phone_number": student.phone_number,
            "call_status": student.call_status,
            "call_count": student.call_count,
            "priority": student.priority,
            "created_at": student.created_at,
            **student.student_data  # Flatten JSON data
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    
    # Create CSV stream
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    # Return as streaming response
    return StreamingResponse(
        io.StringIO(output.getvalue()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=students_export.csv"}
    )

@router.get("/analytics/summary")
async def get_students_analytics(
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Get student analytics summary"""
    
    # Get counts by status
    status_counts = {}
    for call_status in CallStatus:
        count = db.query(Student).filter(Student.call_status == call_status).count()
        status_counts[call_status.value] = count
    
    # Get total counts
    total_students = db.query(Student).count()
    high_priority = db.query(Student).filter(Student.priority >= 5).count()
    
    # Get recent additions
    from datetime import datetime, timedelta
    recent_cutoff = datetime.utcnow() - timedelta(days=7)
    recent_additions = db.query(Student).filter(Student.created_at >= recent_cutoff).count()
    
    return {
        "total_students": total_students,
        "status_breakdown": status_counts,
        "high_priority_count": high_priority,
        "recent_additions_7_days": recent_additions,
        "completion_rate": round((status_counts.get("completed", 0) / total_students * 100), 2) if total_students > 0 else 0
    }
