"""
Student model for Akash Institute Outreach System
Flexible JSON-based schema for dynamic student data
"""
from sqlalchemy import Column, Integer, Text, DateTime, JSON, Index
from sqlalchemy.sql import func
from ..database import Base
import json
from typing import Dict, Any, Optional


class Student(Base):
    """
    Student model with flexible JSON data storage
    
    Core philosophy: Only phone number is required, everything else
    is stored in flexible JSON format based on dynamic field configuration
    """
    __tablename__ = "students"
    
    # Core fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    phone_number = Column(Text, nullable=False, unique=True, index=True)
    
    # Flexible student data in JSON format
    student_data = Column(JSON, nullable=False, default=dict)
    
    # Call management
    call_status = Column(
        Text, 
        nullable=False, 
        default="pending",
        # SQLite CHECK constraint for call status
    )
    call_count = Column(Integer, default=0)
    last_call_attempt = Column(DateTime, nullable=True)
    
    # Priority for calling queue (higher number = higher priority)
    priority = Column(Integer, default=0, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Add check constraint for call_status
    __table_args__ = (
        Index('idx_call_status', 'call_status'),
        Index('idx_priority', 'priority'),
    )
    
    def __init__(self, phone_number: str, student_data: Dict[str, Any] = None, **kwargs):
        """Initialize student with phone number and optional data"""
        super().__init__(**kwargs)
        self.phone_number = phone_number
        self.student_data = student_data or {}
    
    def get_field_value(self, field_name: str, default: Any = None) -> Any:
        """Get value from student_data JSON"""
        return self.student_data.get(field_name, default)
    
    def set_field_value(self, field_name: str, value: Any) -> None:
        """Set value in student_data JSON"""
        if self.student_data is None:
            self.student_data = {}
        self.student_data[field_name] = value
    
    def update_data(self, data_updates: Dict[str, Any]) -> None:
        """Update multiple fields in student_data"""
        if self.student_data is None:
            self.student_data = {}
        
        # Create a new dict to ensure SQLAlchemy detects the change
        updated_data = dict(self.student_data)
        updated_data.update(data_updates)
        self.student_data = updated_data
        
        # Force SQLAlchemy to detect the change
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(self, 'student_data')
    
    @property
    def student_name(self) -> Optional[str]:
        """Get student name from JSON data"""
        return self.get_field_value("student_name")
    
    @property
    def parent_name(self) -> Optional[str]:
        """Get parent name from JSON data"""
        return self.get_field_value("parent_name")
    
    @property
    def scholarship_amount(self) -> Optional[float]:
        """Get scholarship amount from JSON data"""
        amount = self.get_field_value("scholarship_amount")
        try:
            return float(amount) if amount is not None else None
        except (ValueError, TypeError):
            return None
    
    @property
    def display_name(self) -> str:
        """Get display name for UI (student name or phone number)"""
        student_name = self.student_name
        return student_name if student_name else f"Student ({self.phone_number})"
    
    @property
    def is_pending(self) -> bool:
        """Check if student is pending for call"""
        return self.call_status == "pending"
    
    @property
    def is_completed(self) -> bool:
        """Check if call has been completed"""
        return self.call_status == "completed"
    
    def mark_call_attempted(self):
        """Mark that a call attempt was made"""
        self.call_status = "attempted"
        self.call_count += 1
        self.last_call_attempt = func.now()
    
    def mark_call_completed(self):
        """Mark that call was successfully completed"""
        self.call_status = "completed"
        self.call_count += 1
        self.last_call_attempt = func.now()
    
    def mark_call_failed(self):
        """Mark that call failed"""
        self.call_status = "failed"
        self.call_count += 1
        self.last_call_attempt = func.now()
    
    def request_callback(self):
        """Mark that parent requested callback"""
        self.call_status = "callback_requested"
        self.priority += 1  # Increase priority for callback
    
    def to_dict(self, include_phone: bool = True) -> Dict[str, Any]:
        """Convert student to dictionary for API responses"""
        result = {
            "id": self.id,
            "call_status": self.call_status,
            "call_count": self.call_count,
            "last_call_attempt": self.last_call_attempt.isoformat() if self.last_call_attempt else None,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_phone:
            result["phone_number"] = self.phone_number
        
        # Add all student data fields
        if self.student_data:
            result.update(self.student_data)
        
        # Add computed properties
        result["display_name"] = self.display_name
        result["is_pending"] = self.is_pending
        result["is_completed"] = self.is_completed
        
        return result
    
    def __repr__(self):
        return f"<Student(id={self.id}, phone={self.phone_number}, name='{self.student_name}', status='{self.call_status}')>"
    
    def __str__(self):
        return self.display_name


# Valid call statuses
CALL_STATUSES = [
    "pending",
    "attempted", 
    "completed",
    "failed",
    "callback_requested"
]


def validate_call_status(status: str) -> bool:
    """Validate if call status is valid"""
    return status in CALL_STATUSES


def get_students_by_status(db_session, status: str = None, limit: int = None):
    """Get students filtered by call status"""
    query = db_session.query(Student)
    
    if status:
        query = query.filter(Student.call_status == status)
    
    # Order by priority (desc), then by created_at
    query = query.order_by(Student.priority.desc(), Student.created_at)
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


def get_pending_students(db_session, limit: int = None):
    """Get students pending for calls, ordered by priority"""
    return get_students_by_status(db_session, "pending", limit)


# Additional CRUD functions for API compatibility
def create_student(db, phone_number: str, student_data: dict = None, **kwargs):
    """Create a new student"""
    if not phone_number:
        raise ValueError("phone_number is required")
    
    # Extract core fields from kwargs
    call_status = kwargs.get('call_status', 'pending')
    priority = kwargs.get('priority', 0)
    
    # Use provided student_data or empty dict
    student_data = student_data or {}
    
    # Create student instance
    student = Student(
        phone_number=phone_number,
        student_data=student_data,
        call_status=call_status,
        priority=priority
    )
    
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def get_student_by_id(db, student_id: int):
    """Get student by ID"""
    return db.query(Student).filter(Student.id == student_id).first()


def get_student_by_phone(db, phone_number: str):
    """Get student by phone number"""
    return db.query(Student).filter(Student.phone_number == phone_number).first()


def get_students(db, skip: int = 0, limit: int = 100, call_status: str = None):
    """Get list of students with optional filters"""
    query = db.query(Student)
    
    if call_status:
        query = query.filter(Student.call_status == call_status)
    
    return query.offset(skip).limit(limit).all()


def update_student(db, student_id: int, phone_number: str = None, student_data: dict = None, call_status: str = None, priority: int = None, **kwargs):
    """Update student"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return None
    
    # Handle phone number update
    if phone_number:
        student.phone_number = phone_number
    
    # Handle core fields
    if call_status:
        student.call_status = call_status
    
    if priority is not None:
        student.priority = priority
    
    # Update JSON data
    if student_data:
        student.update_data(student_data)
    
    # Handle any additional kwargs by adding them to student_data
    if kwargs:
        student.update_data(kwargs)
    
    db.commit()
    db.refresh(student)
    return student


def delete_student(db, student_id: int):
    """Delete student (hard delete)"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return False
    
    db.delete(student)
    db.commit()
    return True


def search_students(db, query: str, skip: int = 0, limit: int = 100):
    """Search students by name or phone"""
    search_term = f"%{query}%"
    return db.query(Student).filter(
        (Student.phone_number.ilike(search_term)) |
        (Student.student_data.op('->>')('student_name').ilike(search_term)) |
        (Student.student_data.op('->>')('parent_name').ilike(search_term))
    ).offset(skip).limit(limit).all()
