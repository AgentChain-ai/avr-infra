"""
Fields API endpoints
Dynamic field configuration management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..database import get_db
from ..models import FieldConfiguration, FieldType
from ..models.field_config import (
    create_field_configuration,
    get_field_configuration_by_id,
    update_field_configuration,
    delete_field_configuration,
    get_active_fields,
    get_all_fields
)
from .auth import get_current_user, UserInfo

# Pydantic models
class FieldConfigurationCreate(BaseModel):
    field_name: str = Field(..., description="Internal field name (snake_case)")
    field_type: FieldType = Field(..., description="Type of field (text, number, etc.)")
    field_label: str = Field(..., description="Display label for the field")
    is_required: bool = Field(False, description="Whether field is required")
    is_visible_in_list: bool = Field(True, description="Show in student list view")
    field_options: Optional[List[str]] = Field(None, description="Options for select fields")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Custom validation rules")
    display_order: int = Field(0, description="Display order (lower = first)")

class FieldConfigurationUpdate(BaseModel):
    field_name: Optional[str] = None
    field_type: Optional[FieldType] = None
    field_label: Optional[str] = None
    is_required: Optional[bool] = None
    is_visible_in_list: Optional[bool] = None
    field_options: Optional[List[str]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None

class FieldConfigurationResponse(BaseModel):
    id: int
    field_name: str
    field_type: FieldType
    field_label: str
    is_required: bool
    is_visible_in_list: bool
    field_options: Optional[List[str]]
    validation_rules: Optional[Dict[str, Any]]
    display_order: int
    is_active: bool
    created_at: datetime

class DynamicFormSchema(BaseModel):
    fields: List[FieldConfigurationResponse]
    schema_version: str
    last_updated: datetime

# Router setup
router = APIRouter()

@router.get("/", response_model=List[FieldConfigurationResponse])
async def list_field_configurations(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    List all field configurations
    
    - **include_inactive**: Include inactive/disabled fields
    """
    
    if include_inactive:
        fields = get_all_fields(db)
    else:
        fields = get_active_fields(db)
    
    return [FieldConfigurationResponse(**field.to_dict()) for field in fields]

@router.post("/", response_model=FieldConfigurationResponse)
async def create_field_configuration_endpoint(
    field_data: FieldConfigurationCreate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Create a new field configuration"""
    
    # Check if field name already exists
    existing_field = db.query(FieldConfiguration).filter(
        FieldConfiguration.field_name == field_data.field_name
    ).first()
    
    if existing_field:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Field with name '{field_data.field_name}' already exists"
        )
    
    # Validate field options for select fields
    if field_data.field_type == FieldType.SELECT and not field_data.field_options:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Select fields must have field_options defined"
        )
    
    # Create field configuration
    new_field = create_field_configuration(
        db=db,
        field_data=field_data.model_dump()
    )
    
    return FieldConfigurationResponse(**new_field.to_dict())

@router.get("/{field_id}", response_model=FieldConfigurationResponse)
async def get_field_configuration(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Get a specific field configuration by ID"""
    
    field_config = get_field_configuration_by_id(db, field_id)
    if not field_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field configuration with ID {field_id} not found"
        )
    
    return FieldConfigurationResponse(**field_config.to_dict())

@router.put("/{field_id}", response_model=FieldConfigurationResponse)
async def update_field_configuration_endpoint(
    field_id: int,
    update_data: FieldConfigurationUpdate,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """Update a field configuration"""
    
    field_config = get_field_configuration_by_id(db, field_id)
    if not field_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field configuration with ID {field_id} not found"
        )
    
    # Check for field name conflicts if updating field_name
    if update_data.field_name and update_data.field_name != field_config.field_name:
        existing_field = db.query(FieldConfiguration).filter(
            FieldConfiguration.field_name == update_data.field_name,
            FieldConfiguration.id != field_id
        ).first()
        if existing_field:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Field with name '{update_data.field_name}' already exists"
            )
    
    # Validate select field options
    if update_data.field_type == FieldType.SELECT and not update_data.field_options:
        if field_config.field_type != FieldType.SELECT or not field_config.field_options:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Select fields must have field_options defined"
            )
    
    # Update field configuration
    field_data = {
        "field_name": update_data.field_name,
        "field_type": update_data.field_type,
        "field_label": update_data.field_label,
        "is_required": update_data.is_required,
        "is_visible_in_list": update_data.is_visible_in_list,
        "field_options": update_data.field_options,
        "validation_rules": update_data.validation_rules,
        "display_order": update_data.display_order,
        "is_active": update_data.is_active
    }
    
    updated_field = update_field_configuration(
        db=db,
        field_id=field_id,
        field_data=field_data
    )
    
    return FieldConfigurationResponse(**updated_field.to_dict())

@router.delete("/{field_id}")
async def delete_field_configuration_endpoint(
    field_id: int,
    hard_delete: bool = False,
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Delete a field configuration
    
    - **hard_delete**: Permanently delete (default: soft delete by setting is_active=False)
    """
    
    field_config = get_field_configuration_by_id(db, field_id)
    if not field_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field configuration with ID {field_id} not found"
        )
    
    if hard_delete:
        success = delete_field_configuration(db, field_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete field configuration"
            )
        return {"message": f"Field configuration {field_id} permanently deleted"}
    else:
        # Soft delete by setting is_active=False
        updated_field = update_field_configuration(
            db=db,
            field_id=field_id,
            is_active=False
        )
        return {"message": f"Field configuration {field_id} deactivated"}

@router.get("/schema/dynamic-form", response_model=DynamicFormSchema)
async def get_dynamic_form_schema(
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Get the current dynamic form schema for frontend rendering
    Returns active fields ordered by display_order
    """
    
    fields = get_active_fields(db)
    
    # Sort by display_order
    sorted_fields = sorted(fields, key=lambda x: x.display_order)
    
    return DynamicFormSchema(
        fields=[FieldConfigurationResponse(**field.to_dict()) for field in sorted_fields],
        schema_version="1.0",
        last_updated=max([field.created_at for field in fields]) if fields else datetime.utcnow()
    )

@router.post("/reorder")
async def reorder_fields(
    field_order: List[Dict[str, int]],  # [{"field_id": 1, "display_order": 0}, ...]
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Reorder fields by updating display_order values
    
    Expects: [{"field_id": 1, "display_order": 0}, {"field_id": 2, "display_order": 1}, ...]
    """
    
    updated_count = 0
    
    for item in field_order:
        field_id = item.get("field_id")
        display_order = item.get("display_order")
        
        if field_id is None or display_order is None:
            continue
        
        field_config = get_field_configuration_by_id(db, field_id)
        if field_config:
            update_field_configuration(
                db=db,
                field_id=field_id,
                display_order=display_order
            )
            updated_count += 1
    
    return {
        "message": f"Updated display order for {updated_count} fields",
        "updated_count": updated_count
    }

@router.get("/types/available")
async def get_available_field_types(
    current_user: UserInfo = Depends(get_current_user)
):
    """Get list of available field types and their descriptions"""
    
    field_type_info = {
        "text": {
            "description": "Single line text input",
            "validation_options": ["min_length", "max_length", "pattern"]
        },
        "number": {
            "description": "Numeric input (integers)",
            "validation_options": ["min_value", "max_value"]
        },
        "currency": {
            "description": "Currency/decimal input",
            "validation_options": ["min_value", "max_value", "decimal_places"]
        },
        "date": {
            "description": "Date picker input",
            "validation_options": ["min_date", "max_date"]
        },
        "boolean": {
            "description": "Checkbox (true/false)",
            "validation_options": []
        },
        "select": {
            "description": "Dropdown selection",
            "validation_options": [],
            "required_options": ["field_options"]
        }
    }
    
    return {
        "field_types": field_type_info,
        "total_types": len(field_type_info)
    }
