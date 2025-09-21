"""
Campaign model for managing outreach campaigns
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Time
from sqlalchemy.sql import func
from ..database import Base

class Campaign(Base):
    """Campaign model for organizing and managing student outreach campaigns"""
    
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Campaign basic info
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Campaign configuration
    context_note_ids = Column(JSON, nullable=False)  # List of selected context note IDs
    student_ids = Column(JSON, nullable=False)       # List of selected student IDs
    
    # Scheduling
    call_from_time = Column(Time, nullable=False)    # Start time for calling window
    call_to_time = Column(Time, nullable=False)      # End time for calling window
    campaign_start_date = Column(DateTime)           # When campaign starts
    campaign_end_date = Column(DateTime)             # When campaign ends
    
    # Campaign status and metrics
    status = Column(String(50), default="draft")     # draft, active, paused, completed, cancelled
    total_students = Column(Integer, default=0)
    students_called = Column(Integer, default=0)
    successful_calls = Column(Integer, default=0)
    failed_calls = Column(Integer, default=0)
    
    # AI-generated contexts (stored after campaign creation)
    personalized_contexts = Column(JSON)             # student_id -> generated context mapping
    
    # Metadata
    created_by = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Campaign(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    @property
    def completion_rate(self):
        """Calculate campaign completion rate"""
        if self.total_students == 0:
            return 0
        return round((self.students_called / self.total_students) * 100, 2)
    
    @property
    def success_rate(self):
        """Calculate call success rate"""
        if self.students_called == 0:
            return 0
        return round((self.successful_calls / self.students_called) * 100, 2)
    
    def to_dict(self):
        """Convert campaign to dictionary for API responses"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "context_note_ids": self.context_note_ids,
            "student_ids": self.student_ids,
            "call_from_time": self.call_from_time.strftime("%H:%M") if self.call_from_time else None,
            "call_to_time": self.call_to_time.strftime("%H:%M") if self.call_to_time else None,
            "campaign_start_date": self.campaign_start_date.isoformat() if self.campaign_start_date else None,
            "campaign_end_date": self.campaign_end_date.isoformat() if self.campaign_end_date else None,
            "status": self.status,
            "total_students": self.total_students,
            "students_called": self.students_called,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "completion_rate": self.completion_rate,
            "success_rate": self.success_rate,
            "personalized_contexts": self.personalized_contexts,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
