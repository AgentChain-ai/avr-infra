"""
Context API endpoints
Knowledge base and context information management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from ..database import get_db
from ..models import ContextInfo, ContextCategory
from ..models.context_info import (
    create_context_info,
    get_context_info_by_id,
    update_context_info,
    delete_context_info,
    get_active_context_info,
    search_context_info
)
from .auth import get_current_user, UserInfo

# Set up logger
logger = logging.getLogger(__name__)

# Pydantic models
class ContextNoteCreate(BaseModel):
    title: str = Field(..., description="Title of the context note")
    content: str = Field(..., description="Content of the context note")
    category: str = Field(..., description="Category of the context note")
    priority: int = Field(5, description="Priority level (1-10)")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")
    is_active: bool = Field(True, description="Whether the note is active")

class ContextNoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[int] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None

class ContextNoteResponse(BaseModel):
    id: int
    title: str
    content: str
    category: str
    priority: int
    tags: Optional[List[str]]
    is_active: bool
    created_at: datetime
    updated_at: datetime

# Context Category Models
class ContextCategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, max_length=500, description="Category description")
    color: str = Field("#607d8b", description="Hex color code for the category")
    sort_order: int = Field(0, description="Sort order for display")

class ContextCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

class ContextCategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    color: str
    is_active: bool
    is_system: bool
    sort_order: int
    created_at: datetime
    updated_at: Optional[datetime]

class ContextInfoCreate(BaseModel):
    topic: str = Field(..., description="Topic or title of the information")
    information: str = Field(..., description="Detailed information content")
    priority: int = Field(0, description="Priority level (higher = more important)")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")

class ContextInfoUpdate(BaseModel):
    topic: Optional[str] = None
    information: Optional[str] = None
    priority: Optional[int] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None

class ContextInfoResponse(BaseModel):
    id: int
    topic: str
    information: str
    priority: int
    tags: Optional[List[str]]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class ChatMessage(BaseModel):
    message: str = Field(..., description="User message to the context agent")
    context: Optional[str] = Field(None, description="Additional context for the query")

class ChatResponse(BaseModel):
    response: str
    suggested_actions: List[str]
    extracted_info: Optional[Dict[str, Any]]
    confidence: float

# Router setup
router = APIRouter()

@router.get("/", response_model=List[ContextInfoResponse])
async def list_context_info(
    skip: int = 0,
    limit: int = 100,
    priority_min: Optional[int] = None,
    tags: Optional[str] = None,
    search: Optional[str] = None,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    List context information with filtering options
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **priority_min**: Minimum priority level
    - **tags**: Comma-separated list of tags to filter by
    - **search**: Search in topic and information content
    - **include_inactive**: Include inactive context items
    """
    
    if search:
        context_items = search_context_info(db, search, include_inactive)
    else:
        if include_inactive:
            context_items = db.query(ContextInfo).all()
        else:
            context_items = get_active_context_info(db)
    
    # Apply additional filters
    if priority_min is not None:
        context_items = [item for item in context_items if item.priority >= priority_min]
    
    if tags:
        tag_list = [tag.strip() for tag in tags.split(',')]
        context_items = [
            item for item in context_items 
            if item.tags and any(tag in item.tags for tag in tag_list)
        ]
    
    # Apply pagination
    total = len(context_items)
    context_items = context_items[skip:skip + limit]
    
    return [ContextInfoResponse(**item.to_dict()) for item in context_items]

@router.post("/", response_model=ContextInfoResponse)
async def create_context_info_endpoint(
    context_data: ContextInfoCreate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Create new context information"""
    
    new_context = create_context_info(
        db=db,
        topic=context_data.topic,
        information=context_data.information,
        priority=context_data.priority,
        tags=context_data.tags
    )
    
    return ContextInfoResponse(**new_context.to_dict())

# Context Notes Endpoints (Specific routes must come BEFORE generic /{context_id})

@router.get("/context-notes", response_model=List[ContextNoteResponse])
async def list_context_notes(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """List context notes with filtering options"""
    
    query = db.query(ContextInfo)
    
    if not include_inactive:
        query = query.filter(ContextInfo.is_active == True)
    
    if category:
        query = query.filter(ContextInfo.tags.contains([category]))
    
    context_notes = query.order_by(ContextInfo.priority.desc(), ContextInfo.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        ContextNoteResponse(
            id=note.id,
            title=note.topic,
            content=note.information,
            category=note.tags[0] if note.tags else "Other",
            priority=note.priority,
            tags=note.tags,
            is_active=note.is_active,
            created_at=note.created_at,
            updated_at=note.updated_at
        )
        for note in context_notes
    ]

@router.post("/context-notes", response_model=ContextNoteResponse)
async def create_context_note(
    note_data: ContextNoteCreate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Create a new context note"""
    
    # Prepare data for ContextInfo model
    context_data = {
        "topic": note_data.title,
        "information": note_data.content,
        "priority": note_data.priority,
        "tags": [note_data.category] + (note_data.tags or []),
        "is_active": note_data.is_active
    }
    
    new_note = create_context_info(db, context_data)
    
    return ContextNoteResponse(
        id=new_note.id,
        title=new_note.topic,
        content=new_note.information,
        category=new_note.tags[0] if new_note.tags else "Other",
        priority=new_note.priority,
        tags=new_note.tags,
        is_active=new_note.is_active,
        created_at=new_note.created_at,
        updated_at=new_note.updated_at
    )

@router.put("/context-notes/{note_id}", response_model=ContextNoteResponse)
async def update_context_note(
    note_id: int,
    note_data: ContextNoteUpdate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Update a context note"""
    
    note = get_context_info_by_id(db, note_id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Context note with ID {note_id} not found"
        )
    
    # Prepare update data
    update_data = {}
    if note_data.title is not None:
        update_data["topic"] = note_data.title
    if note_data.content is not None:
        update_data["information"] = note_data.content
    if note_data.priority is not None:
        update_data["priority"] = note_data.priority
    if note_data.category is not None or note_data.tags is not None:
        tags = []
        if note_data.category:
            tags.append(note_data.category)
        if note_data.tags:
            tags.extend(note_data.tags)
        update_data["tags"] = tags
    if note_data.is_active is not None:
        update_data["is_active"] = note_data.is_active
    
    updated_note = update_context_info(db, note_id, update_data)
    
    return ContextNoteResponse(
        id=updated_note.id,
        title=updated_note.topic,
        content=updated_note.information,
        category=updated_note.tags[0] if updated_note.tags else "Other",
        priority=updated_note.priority,
        tags=updated_note.tags,
        is_active=updated_note.is_active,
        created_at=updated_note.created_at,
        updated_at=updated_note.updated_at
    )

@router.delete("/context-notes/{note_id}")
async def delete_context_note(
    note_id: int,
    hard_delete: bool = False,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Delete a context note"""
    
    note = get_context_info_by_id(db, note_id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Context note with ID {note_id} not found"
        )
    
    if hard_delete:
        # Permanently delete
        success = delete_context_info(db, note_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete context note"
            )
    else:
        # Soft delete by setting is_active to False
        update_context_info(db, note_id, {"is_active": False})
    
    return {"message": "Context note deleted successfully"}

# Context Category Endpoints (Must come BEFORE generic /{context_id} route)

@router.get("/categories", response_model=List[ContextCategoryResponse])
async def list_context_categories(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """List all context categories"""
    
    query = db.query(ContextCategory)
    
    if not include_inactive:
        query = query.filter(ContextCategory.is_active == True)
    
    categories = query.order_by(ContextCategory.sort_order, ContextCategory.name).all()
    
    return [
        ContextCategoryResponse(
            id=cat.id,
            name=cat.name,
            description=cat.description,
            color=cat.color,
            is_active=cat.is_active,
            is_system=cat.is_system,
            sort_order=cat.sort_order,
            created_at=cat.created_at,
            updated_at=cat.updated_at
        )
        for cat in categories
    ]

@router.post("/categories", response_model=ContextCategoryResponse)
async def create_context_category(
    category_data: ContextCategoryCreate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Create a new context category"""
    
    # Check if category name already exists
    existing = db.query(ContextCategory).filter(ContextCategory.name == category_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{category_data.name}' already exists"
        )
    
    new_category = ContextCategory(
        name=category_data.name,
        description=category_data.description,
        color=category_data.color,
        sort_order=category_data.sort_order
    )
    
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    
    return ContextCategoryResponse(
        id=new_category.id,
        name=new_category.name,
        description=new_category.description,
        color=new_category.color,
        is_active=new_category.is_active,
        is_system=new_category.is_system,
        sort_order=new_category.sort_order,
        created_at=new_category.created_at,
        updated_at=new_category.updated_at
    )

@router.put("/categories/{category_id}", response_model=ContextCategoryResponse)
async def update_context_category(
    category_id: int,
    category_data: ContextCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Update a context category"""
    
    category = db.query(ContextCategory).filter(ContextCategory.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found"
        )
    
    # Check if trying to update a system category's critical fields
    if category.is_system and category_data.name is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify name of system categories"
        )
    
    # Update fields
    if category_data.name is not None:
        # Check for duplicate name
        existing = db.query(ContextCategory).filter(
            ContextCategory.name == category_data.name,
            ContextCategory.id != category_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{category_data.name}' already exists"
            )
        category.name = category_data.name
    
    if category_data.description is not None:
        category.description = category_data.description
    if category_data.color is not None:
        category.color = category_data.color
    if category_data.sort_order is not None:
        category.sort_order = category_data.sort_order
    if category_data.is_active is not None:
        category.is_active = category_data.is_active
    
    db.commit()
    db.refresh(category)
    
    return ContextCategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        color=category.color,
        is_active=category.is_active,
        is_system=category.is_system,
        sort_order=category.sort_order,
        created_at=category.created_at,
        updated_at=category.updated_at
    )

@router.delete("/categories/{category_id}")
async def delete_context_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Delete a context category"""
    
    category = db.query(ContextCategory).filter(ContextCategory.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found"
        )
    
    # Prevent deletion of system categories
    if category.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete system categories"
        )
    
    # Check if category is being used by any context notes
    notes_using_category = db.query(ContextInfo).filter(
        ContextInfo.tags.contains([category.name])
    ).count()
    
    if notes_using_category > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category '{category.name}' - it's being used by {notes_using_category} context note(s)"
        )
    
    db.delete(category)
    db.commit()
    
    return {"message": f"Category '{category.name}' deleted successfully"}

@router.get("/{context_id}", response_model=ContextInfoResponse)
async def get_context_info(
    context_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Get specific context information by ID"""
    
    context_info = get_context_info_by_id(db, context_id)
    if not context_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Context information with ID {context_id} not found"
        )
    
    return ContextInfoResponse(**context_info.to_dict())

@router.put("/{context_id}", response_model=ContextInfoResponse)
async def update_context_info_endpoint(
    context_id: int,
    update_data: ContextInfoUpdate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Update context information"""
    
    context_info = get_context_info_by_id(db, context_id)
    if not context_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Context information with ID {context_id} not found"
        )
    
    updated_context = update_context_info(
        db=db,
        context_id=context_id,
        topic=update_data.topic,
        information=update_data.information,
        priority=update_data.priority,
        tags=update_data.tags,
        is_active=update_data.is_active
    )
    
    return ContextInfoResponse(**updated_context.to_dict())

@router.delete("/{context_id}")
async def delete_context_info_endpoint(
    context_id: int,
    hard_delete: bool = False,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Delete context information
    
    - **hard_delete**: Permanently delete (default: soft delete)
    """
    
    context_info = get_context_info_by_id(db, context_id)
    if not context_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Context information with ID {context_id} not found"
        )
    
    if hard_delete:
        success = delete_context_info(db, context_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete context information"
            )
        return {"message": f"Context information {context_id} permanently deleted"}
    else:
        # Soft delete
        update_context_info(db=db, context_id=context_id, is_active=False)
        return {"message": f"Context information {context_id} deactivated"}

@router.post("/chat", response_model=ChatResponse)
async def chat_with_context_agent(
    chat_data: ChatMessage,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Chat with AI context management agent
    The agent can help extract, organize, and update context information
    """
    
    try:
        # Import AI service
        from ..services.context_agent import ContextAgent
        
        # Initialize context agent
        agent = ContextAgent(db)
        
        # Process the message
        response = await agent.process_admin_message(
            message=chat_data.message,
            context=chat_data.context,
            user=current_user.username
        )
        
        return ChatResponse(
            response=response["message"],
            suggested_actions=response.get("suggested_actions", []),
            extracted_info=response.get("extracted_info"),
            confidence=response.get("confidence", 0.8)
        )
        
    except Exception as e:
        # Fallback response if AI service fails
        return ChatResponse(
            response=f"I'm sorry, I'm having trouble processing your request right now. Error: {str(e)}",
            suggested_actions=["Try rephrasing your message", "Contact technical support"],
            extracted_info=None,
            confidence=0.0
        )

@router.get("/search/smart")
async def smart_context_search(
    query: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Smart search using AI to find relevant context information
    """
    
    try:
        # Use AI for semantic search
        from ..services.context_agent import ContextAgent
        
        agent = ContextAgent(db)
        results = await agent.semantic_search(query, limit)
        
        return {
            "query": query,
            "results": results,
            "search_type": "semantic"
        }
        
    except Exception:
        # Fallback to simple text search
        context_items = search_context_info(db, query, include_inactive=False)
        
        return {
            "query": query,
            "results": [ContextInfoResponse(**item.to_dict()) for item in context_items[:limit]],
            "search_type": "text_fallback"
        }

@router.get("/analytics/summary")
async def get_context_analytics(
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Get context information analytics"""
    
    # Get total counts
    total_context = db.query(ContextInfo).count()
    active_context = db.query(ContextInfo).filter(ContextInfo.is_active == True).count()
    high_priority = db.query(ContextInfo).filter(
        ContextInfo.priority >= 5,
        ContextInfo.is_active == True
    ).count()
    
    # Get recent additions
    from datetime import datetime, timedelta
    recent_cutoff = datetime.utcnow() - timedelta(days=7)
    recent_additions = db.query(ContextInfo).filter(
        ContextInfo.created_at >= recent_cutoff
    ).count()
    
    # Get tag statistics
    all_context = db.query(ContextInfo).filter(ContextInfo.is_active == True).all()
    tag_counts = {}
    for item in all_context:
        if item.tags:
            for tag in item.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    # Top tags
    top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "total_context_items": total_context,
        "active_items": active_context,
        "inactive_items": total_context - active_context,
        "high_priority_items": high_priority,
        "recent_additions_7_days": recent_additions,
        "top_tags": [{"tag": tag, "count": count} for tag, count in top_tags],
        "tag_distribution": tag_counts
    }

@router.get("/export/knowledge-base")
async def export_knowledge_base(
    format: str = "json",
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Export complete knowledge base
    
    - **format**: Export format (json, csv)
    - **include_inactive**: Include inactive context items
    """
    
    if include_inactive:
        context_items = db.query(ContextInfo).all()
    else:
        context_items = get_active_context_info(db)
    
    # Sort by priority and topic
    context_items = sorted(context_items, key=lambda x: (-x.priority, x.topic))
    
    if format.lower() == "json":
        export_data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "total_items": len(context_items),
            "knowledge_base": [item.to_dict() for item in context_items]
        }
        return export_data
    
    elif format.lower() == "csv":
        from fastapi.responses import StreamingResponse
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['id', 'topic', 'information', 'priority', 'tags', 'is_active', 'created_at'])
        
        # Write data
        for item in context_items:
            writer.writerow([
                item.id,
                item.topic,
                item.information,
                item.priority,
                ','.join(item.tags) if item.tags else '',
                item.is_active,
                item.created_at
            ])
        
        output.seek(0)
        
        return StreamingResponse(
            io.StringIO(output.getvalue()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=knowledge_base_export.csv"}
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported format. Use 'json' or 'csv'"
        )


# Call Context Storage Endpoints
from ..services.context_store import context_store

class CallContextRequest(BaseModel):
    phone_number: str
    context_data: Dict[str, Any]

class CallContextResponse(BaseModel):
    context_id: str
    phone_number: str
    message: str

@router.post("/call-context/store", response_model=CallContextResponse)
async def store_call_context(request: CallContextRequest):
    """
    Store personalized context for a call
    """
    try:
        context_id = context_store.store_context(
            phone_number=request.phone_number,
            context_data=request.context_data
        )
        
        return CallContextResponse(
            context_id=context_id,
            phone_number=request.phone_number,
            message="Context stored successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store context: {str(e)}")

@router.get("/call-context/{phone_number}")
async def get_call_context(phone_number: str):
    """
    Get personalized context for a phone number - used by LLM service
    """
    try:
        context_data = context_store.get_context_by_phone(phone_number)
        
        if not context_data:
            return {
                "phone_number": phone_number,
                "context_data": None,
                "found": False,
                "message": "No context found for this phone number"
            }
        
        return {
            "phone_number": phone_number,
            "context_data": context_data,
            "found": True,
            "message": "Context found"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get context: {str(e)}")

@router.get("/call-context")
async def get_call_context_by_param(phone_number: str = None, call_id: str = None):
    """
    Get personalized context for a call - flexible endpoint for LLM service
    This endpoint can be called with either phone_number or call_id
    """
    try:
        if phone_number:
            # Look up by phone number first
            context_data = context_store.get_context_by_phone(phone_number)
        elif call_id:
            # Look up by call ID 
            context_data = context_store.get_context_by_id(call_id)
        else:
            return {
                "error": "Either phone_number or call_id parameter is required",
                "found": False
            }
        
        if not context_data:
            return {
                "phone_number": phone_number,
                "call_id": call_id,
                "context_data": None,
                "found": False,
                "message": "No context found"
            }
        
        # Return the personalized context that can be used by the LLM
        return {
            "phone_number": phone_number,
            "call_id": call_id,
            "context_data": context_data,
            "found": True,
            "personalized_prompt": context_data.get("personalized_context", ""),
            "student_info": {
                "student_id": context_data.get("student_id"),
                "student_name": context_data.get("student_name"),
                "call_id": context_data.get("call_id")
            },
            "message": "Context found successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get context: {str(e)}")

@router.delete("/call-context/{phone_number}")
async def cleanup_call_context(phone_number: str):
    """
    Clean up context for a phone number after call completion
    """
    try:
        context_store.cleanup_context(phone_number)
        return {
            "phone_number": phone_number,
            "message": "Context cleaned up successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup context: {str(e)}")

@router.post("/call-context/update")
async def update_call_context_for_phone(request: dict):
    """
    Update/set personalized context for a phone number - for dynamic context passing
    This endpoint allows the voice service to send context directly before making calls
    """
    try:
        phone_number = request.get("phone_number")
        instructions = request.get("instructions")
        
        if not phone_number or not instructions:
            raise HTTPException(status_code=400, detail="phone_number and instructions are required")
        
        # Store the dynamic context
        context_data = {
            "phone_number": phone_number,
            "personalized_instructions": instructions,
            "dynamic_context": True,
            "timestamp": datetime.now().isoformat()
        }
        
        context_id = context_store.store_context(
            phone_number=phone_number,
            context_data=context_data
        )
        
        return {
            "success": True,
            "phone_number": phone_number,
            "context_id": context_id,
            "message": "Dynamic context updated successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update context: {str(e)}")

@router.get("/openai-instructions/{phone_number}")
async def get_openai_instructions_for_call(phone_number: str):
    """
    Get personalized OpenAI instructions for a specific phone number
    This endpoint is called by the OpenAI Realtime service to get dynamic context
    """
    try:
        context_data = context_store.get_context_by_phone(phone_number)
        
        if not context_data:
            return {
                "phone_number": phone_number,
                "instructions": "You are calling from Akash Institute. Always speak in Hindi. Be warm and professional.",
                "found": False,
                "message": "No personalized context found, using default instructions"
            }
        
        # Return the personalized instructions
        instructions = context_data.get("personalized_instructions", 
                                       "You are calling from Akash Institute. Always speak in Hindi. Be warm and professional.")
        
        return {
            "phone_number": phone_number,
            "instructions": instructions,
            "found": True,
            "message": "Personalized instructions retrieved successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get instructions: {str(e)}")


@router.get("/openai-system-instructions")
async def get_openai_system_instructions(
    request: Request
):
    """
    Get system instructions for OpenAI AVR service in the format it expects.
    This endpoint is called by the AVR OpenAI service when OPENAI_URL_INSTRUCTIONS is set.
    
    Returns instructions in the format: {"system": "instructions_text"}
    The AVR service includes X-AVR-UUID header with session UUID.
    This endpoint is public (no auth required) as it's called by the AVR service.
    """
    try:
        # Get session UUID from header (sent by AVR service)
        session_uuid = request.headers.get("X-AVR-UUID")
        logger.info(f"AVR OpenAI service requesting instructions for session: {session_uuid}")
        
        # For now, we'll use a default phone number until we can map session to phone
        # In a real implementation, you'd need to track session->phone mapping
        default_phone = "1000"  # Our test phone number
        
        # Try to get personalized context from our store
        context_data = context_store.get_context_by_phone(default_phone)
        
        if context_data and context_data.get("personalized_instructions"):
            instructions = context_data["personalized_instructions"]
            logger.info(f"Returning personalized instructions for phone {default_phone}")
        else:
            # Fallback to default instructions
            instructions = "You are calling from Akash Institute. Always speak in Hindi. Be warm and professional. आप अकाश इंस्टिट्यूट से कॉल कर रहे हैं। हमेशा हिंदी में बोलें। गर्मजोशी से और पेशेवर तरीके से बात करें।"
            logger.info("Using default instructions - no personalized context found")
        
        # Return in the format expected by AVR service
        return {
            "system": instructions
        }
        
    except Exception as e:
        logger.error(f"Error getting OpenAI system instructions: {str(e)}")
        # Return default instructions on error
        return {
            "system": "You are calling from Akash Institute. Always speak in Hindi. Be warm and professional."
        }