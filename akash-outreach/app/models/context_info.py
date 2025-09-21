"""
Context Information model for knowledge base management
Stores information that the voice agent can use during conversations
"""
from sqlalchemy import Column, Integer, Text, DateTime, JSON, Boolean
from sqlalchemy.sql import func
from ..database import Base
from typing import Dict, Any, List, Optional


class ContextInfo(Base):
    """
    Context information for the voice agent knowledge base
    
    Stores information about courses, fees, admission process, etc.
    that the voice agent can reference during conversations
    """
    __tablename__ = "context_info"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Content identification
    topic = Column(Text, nullable=False, index=True)  # e.g., "Admission Process", "Fee Structure"
    information = Column(Text, nullable=False)  # The actual information content
    
    # Priority and organization
    priority = Column(Integer, default=0, index=True)  # Higher number = higher priority
    tags = Column(JSON, nullable=True)  # Flexible tagging system ["admission", "fees", "courses"]
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __init__(self, topic: str, information: str, **kwargs):
        """Initialize context info with topic and information"""
        super().__init__(**kwargs)
        self.topic = topic
        self.information = information
        self.tags = kwargs.get('tags', [])
    
    @property
    def tag_list(self) -> List[str]:
        """Get tags as a list"""
        if self.tags and isinstance(self.tags, list):
            return self.tags
        return []
    
    @property
    def tag_string(self) -> str:
        """Get tags as comma-separated string"""
        return ", ".join(self.tag_list)
    
    def has_tag(self, tag: str) -> bool:
        """Check if context info has a specific tag"""
        return tag.lower() in [t.lower() for t in self.tag_list]
    
    def add_tag(self, tag: str):
        """Add a tag to this context info"""
        tags = self.tag_list
        if tag.lower() not in [t.lower() for t in tags]:
            tags.append(tag)
            self.tags = tags
    
    def remove_tag(self, tag: str):
        """Remove a tag from this context info"""
        tags = self.tag_list
        self.tags = [t for t in tags if t.lower() != tag.lower()]
    
    def set_tags(self, tags: List[str]):
        """Set tags for this context info"""
        self.tags = tags
    
    @property
    def summary(self) -> str:
        """Get a summary of the information (first 100 characters)"""
        if len(self.information) <= 100:
            return self.information
        return self.information[:97] + "..."
    
    @property
    def word_count(self) -> int:
        """Get word count of the information"""
        return len(self.information.split())
    
    def is_relevant_for_query(self, query: str) -> bool:
        """Check if this context info is relevant for a query"""
        query_lower = query.lower()
        
        # Check topic
        if query_lower in self.topic.lower():
            return True
        
        # Check information content
        if query_lower in self.information.lower():
            return True
        
        # Check tags
        for tag in self.tag_list:
            if query_lower in tag.lower() or tag.lower() in query_lower:
                return True
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context info to dictionary for API responses"""
        return {
            "id": self.id,
            "topic": self.topic,
            "information": self.information,
            "summary": self.summary,
            "priority": self.priority,
            "tags": self.tag_list,
            "tag_string": self.tag_string,
            "is_active": self.is_active,
            "word_count": self.word_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<ContextInfo(id={self.id}, topic='{self.topic}', priority={self.priority}, active={self.is_active})>"
    
    def __str__(self):
        return f"{self.topic}: {self.summary}"


def get_active_context_info(db_session, limit: int = None):
    """Get active context information ordered by priority"""
    query = db_session.query(ContextInfo).filter(ContextInfo.is_active.is_(True))
    query = query.order_by(ContextInfo.priority.desc(), ContextInfo.topic)
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


def search_context_info(db_session, query: str, limit: int = 10):
    """Search context information by query"""
    # Simple text search - can be enhanced with full-text search
    search_filter = (
        ContextInfo.topic.contains(query) |
        ContextInfo.information.contains(query)
    )
    
    return db_session.query(ContextInfo).filter(
        ContextInfo.is_active.is_(True)
    ).filter(search_filter).order_by(
        ContextInfo.priority.desc()
    ).limit(limit).all()


def get_context_by_tags(db_session, tags: List[str], limit: int = None):
    """Get context information by tags"""
    results = []
    
    for context_info in get_active_context_info(db_session):
        for tag in tags:
            if context_info.has_tag(tag):
                results.append(context_info)
                break
    
    # Sort by priority
    results.sort(key=lambda x: x.priority, reverse=True)
    
    if limit:
        results = results[:limit]
    
    return results


def get_high_priority_context(db_session, min_priority: int = 2):
    """Get high priority context information"""
    return db_session.query(ContextInfo).filter(
        ContextInfo.is_active.is_(True),
        ContextInfo.priority >= min_priority
    ).order_by(ContextInfo.priority.desc()).all()


def get_context_for_voice_agent(db_session) -> str:
    """
    Get formatted context information for voice agent
    Returns a formatted string with all high-priority context
    """
    context_items = get_high_priority_context(db_session)
    
    if not context_items:
        return "No context information available."
    
    formatted_context = []
    formatted_context.append("=== AKASH INSTITUTE INFORMATION ===")
    
    for item in context_items:
        formatted_context.append(f"\n{item.topic.upper()}:")
        formatted_context.append(item.information)
        
        if item.tag_list:
            formatted_context.append(f"[Tags: {item.tag_string}]")
    
    formatted_context.append("\n=== END INFORMATION ===")
    
    return "\n".join(formatted_context)


def update_context_priority(db_session, context_id: int, new_priority: int):
    """Update priority of a context item"""
    context_item = db_session.query(ContextInfo).filter(ContextInfo.id == context_id).first()
    
    if context_item:
        context_item.priority = new_priority
        db_session.commit()
        return True
    
    return False


def deactivate_context(db_session, context_id: int):
    """Deactivate a context item"""
    context_item = db_session.query(ContextInfo).filter(ContextInfo.id == context_id).first()
    
    if context_item:
        context_item.is_active = False
        db_session.commit()
        return True
    
    return False


# Additional CRUD functions for API compatibility
def create_context_info(db, context_data: dict):
    """Create a new context info"""
    context_info = ContextInfo(**context_data)
    db.add(context_info)
    db.commit()
    db.refresh(context_info)
    return context_info


def get_context_info_by_id(db, context_id: int):
    """Get context info by ID"""
    return db.query(ContextInfo).filter(ContextInfo.id == context_id).first()


def update_context_info(db, context_id: int, context_data: dict):
    """Update context info"""
    context_info = db.query(ContextInfo).filter(ContextInfo.id == context_id).first()
    if not context_info:
        return None
    
    for key, value in context_data.items():
        if hasattr(context_info, key):
            setattr(context_info, key, value)
    
    db.commit()
    db.refresh(context_info)
    return context_info


def delete_context_info(db, context_id: int):
    """Delete context info (soft delete by setting is_active=False)"""
    context_info = db.query(ContextInfo).filter(ContextInfo.id == context_id).first()
    if not context_info:
        return False
    
    context_info.is_active = False
    db.commit()
    return True
