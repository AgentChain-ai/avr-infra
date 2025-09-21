"""
Call Log model for tracking all voice interactions
"""
from sqlalchemy import Column, Integer, Text, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base
from typing import Dict, Any, List, Optional


class CallLog(Base):
    """
    Call log for tracking all voice interactions with students/parents
    """
    __tablename__ = "call_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Student reference (nullable in case student is deleted)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="SET NULL"), nullable=True, index=True)
    phone_number = Column(Text, nullable=False, index=True)  # Always store phone number
    
    # Call details
    call_duration = Column(Integer, default=0)  # Duration in seconds
    call_status = Column(Text, nullable=False)  # completed, no_answer, busy, failed, callback_requested, in_progress
    
    # Conversation data in flexible JSON format
    conversation_data = Column(JSON, nullable=True)
    ai_summary = Column(Text, nullable=True)  # AI-generated summary of the call
    
    # Follow-up and recordings
    follow_up_required = Column(Boolean, default=False)
    call_recording_path = Column(Text, nullable=True)  # Path to call recording file
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), index=True)
    
    def __init__(self, phone_number: str, call_status: str, **kwargs):
        """Initialize call log with phone number and status"""
        super().__init__(**kwargs)
        self.phone_number = phone_number
        self.call_status = call_status
        self.conversation_data = kwargs.get('conversation_data', {})
    
    @property
    def duration_formatted(self) -> str:
        """Get formatted call duration (MM:SS)"""
        if not self.call_duration:
            return "00:00"
        
        minutes = self.call_duration // 60
        seconds = self.call_duration % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def is_successful(self) -> bool:
        """Check if call was successful"""
        return self.call_status == "completed"
    
    @property
    def questions_asked(self) -> List[str]:
        """Get list of questions asked during the call"""
        if self.conversation_data:
            return self.conversation_data.get("questions_asked", [])
        return []
    
    @property
    def answers_provided(self) -> Dict[str, str]:
        """Get answers provided during the call"""
        if self.conversation_data:
            return self.conversation_data.get("answers_provided", {})
        return {}
    
    @property
    def parent_concerns(self) -> List[str]:
        """Get parent concerns mentioned during the call"""
        if self.conversation_data:
            return self.conversation_data.get("parent_concerns", [])
        return []
    
    @property
    def satisfaction_level(self) -> Optional[str]:
        """Get satisfaction level from conversation data"""
        if self.conversation_data:
            return self.conversation_data.get("satisfaction_level")
        return None
    
    def add_question_asked(self, question: str):
        """Add a question that was asked during the call"""
        if not self.conversation_data:
            self.conversation_data = {}
        
        if "questions_asked" not in self.conversation_data:
            self.conversation_data["questions_asked"] = []
        
        if question not in self.conversation_data["questions_asked"]:
            self.conversation_data["questions_asked"].append(question)
    
    def add_answer_provided(self, topic: str, answer: str):
        """Add an answer that was provided during the call"""
        if not self.conversation_data:
            self.conversation_data = {}
        
        if "answers_provided" not in self.conversation_data:
            self.conversation_data["answers_provided"] = {}
        
        self.conversation_data["answers_provided"][topic] = answer
    
    def add_parent_concern(self, concern: str):
        """Add a parent concern mentioned during the call"""
        if not self.conversation_data:
            self.conversation_data = {}
        
        if "parent_concerns" not in self.conversation_data:
            self.conversation_data["parent_concerns"] = []
        
        if concern not in self.conversation_data["parent_concerns"]:
            self.conversation_data["parent_concerns"].append(concern)
    
    def set_satisfaction_level(self, level: str):
        """Set the satisfaction level (high, medium, low)"""
        if not self.conversation_data:
            self.conversation_data = {}
        
        self.conversation_data["satisfaction_level"] = level
    
    def set_callback_request(self, reason: str):
        """Mark that parent requested callback with reason"""
        self.call_status = "callback_requested"
        self.follow_up_required = True
        
        if not self.conversation_data:
            self.conversation_data = {}
        
        self.conversation_data["callback_requested_for"] = reason
    
    def mark_completed(self, duration: int = 0):
        """Mark call as completed with duration"""
        self.call_status = "completed"
        self.call_duration = duration
    
    def mark_failed(self, reason: str = "unknown"):
        """Mark call as failed with reason"""
        self.call_status = "failed"
        
        if not self.conversation_data:
            self.conversation_data = {}
        
        self.conversation_data["failure_reason"] = reason
    
    def generate_ai_summary(self) -> str:
        """Generate AI summary of the call (placeholder for AI integration)"""
        if not self.conversation_data:
            return "No conversation data available"
        
        # This would be replaced with actual AI summary generation
        summary_parts = []
        
        if self.questions_asked:
            summary_parts.append(f"Parent asked {len(self.questions_asked)} questions")
        
        if self.parent_concerns:
            summary_parts.append(f"Concerns: {', '.join(self.parent_concerns)}")
        
        if self.satisfaction_level:
            summary_parts.append(f"Satisfaction: {self.satisfaction_level}")
        
        if self.call_status == "callback_requested":
            callback_reason = self.conversation_data.get("callback_requested_for", "unspecified")
            summary_parts.append(f"Callback requested for: {callback_reason}")
        
        return "; ".join(summary_parts) if summary_parts else "Call completed successfully"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert call log to dictionary for API responses"""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "phone_number": self.phone_number,
            "call_duration": self.call_duration,
            "duration_formatted": self.duration_formatted,
            "call_status": self.call_status,
            "conversation_data": self.conversation_data,
            "ai_summary": self.ai_summary or self.generate_ai_summary(),
            "follow_up_required": self.follow_up_required,
            "call_recording_path": self.call_recording_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_successful": self.is_successful,
            "questions_asked": self.questions_asked,
            "answers_provided": self.answers_provided,
            "parent_concerns": self.parent_concerns,
            "satisfaction_level": self.satisfaction_level,
        }
    
    def __repr__(self):
        return f"<CallLog(id={self.id}, phone={self.phone_number}, status='{self.call_status}', duration={self.duration_formatted})>"


# Valid call statuses
CALL_LOG_STATUSES = [
    "completed",
    "no_answer",
    "busy", 
    "failed",
    "callback_requested",
    "in_progress"
]


def validate_call_log_status(status: str) -> bool:
    """Validate if call log status is valid"""
    return status in CALL_LOG_STATUSES


def get_calls_by_status(db_session, status: str = None, limit: int = None):
    """Get call logs filtered by status"""
    query = db_session.query(CallLog)
    
    if status:
        query = query.filter(CallLog.call_status == status)
    
    # Order by created_at descending (newest first)
    query = query.order_by(CallLog.created_at.desc())
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


def get_calls_for_student(db_session, student_id: int):
    """Get all call logs for a specific student"""
    return db_session.query(CallLog).filter(
        CallLog.student_id == student_id
    ).order_by(CallLog.created_at.desc()).all()


def get_recent_calls(db_session, limit: int = 10):
    """Get recent call logs"""
    return db_session.query(CallLog).order_by(
        CallLog.created_at.desc()
    ).limit(limit).all()


def get_calls_requiring_followup(db_session):
    """Get calls that require follow-up"""
    return db_session.query(CallLog).filter(
        CallLog.follow_up_required == True
    ).order_by(CallLog.created_at.desc()).all()


# Additional CRUD functions for API compatibility
def create_call_log(db, call_data: dict):
    """Create a new call log"""
    call_log = CallLog(**call_data)
    db.add(call_log)
    db.commit()
    db.refresh(call_log)
    return call_log


def get_call_log_by_id(db, call_id: int):
    """Get call log by ID"""
    return db.query(CallLog).filter(CallLog.id == call_id).first()


def update_call_log(db, call_id: int, call_data: dict):
    """Update call log"""
    call_log = db.query(CallLog).filter(CallLog.id == call_id).first()
    if not call_log:
        return None
    
    for key, value in call_data.items():
        if hasattr(call_log, key):
            setattr(call_log, key, value)
    
    db.commit()
    db.refresh(call_log)
    return call_log


def get_calls_by_student(db, student_id: int):
    """Get all calls for a specific student (alias for get_calls_for_student)"""
    return get_calls_for_student(db, student_id)
