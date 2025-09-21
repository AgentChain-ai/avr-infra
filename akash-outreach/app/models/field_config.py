"""
Field Configuration model for dynamic schema management
Allows admin to configure what fields are available for students
"""
from sqlalchemy import Column, Integer, Text, Boolean, JSON, DateTime
from sqlalchemy.sql import func
from ..database import Base
from typing import Dict, Any, List, Optional


class FieldConfiguration(Base):
    """
    Dynamic field configuration for student data
    
    Allows admins to define what fields are available for students
    without changing the database schema
    """
    __tablename__ = "field_configurations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Field identification
    field_name = Column(Text, nullable=False, unique=True)  # e.g., "scholarship_amount"
    field_type = Column(Text, nullable=False)  # text, number, currency, date, boolean, select
    field_label = Column(Text, nullable=False)  # "Scholarship Amount"
    
    # Field behavior
    is_required = Column(Boolean, default=False)
    is_visible_in_list = Column(Boolean, default=True)
    
    # Field options (for select fields, validation rules, etc.)
    field_options = Column(JSON, nullable=True)
    validation_rules = Column(JSON, nullable=True)
    
    # Display configuration
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    
    def __init__(self, field_name: str, field_type: str, field_label: str, **kwargs):
        """Initialize field configuration"""
        super().__init__(**kwargs)
        self.field_name = field_name
        self.field_type = field_type
        self.field_label = field_label
    
    @property
    def select_options(self) -> List[str]:
        """Get select options for select field types"""
        if self.field_type == "select" and self.field_options:
            # field_options is now a direct list, not a dict
            if isinstance(self.field_options, list):
                return self.field_options
            # Backward compatibility: if it's still a dict, extract options
            elif isinstance(self.field_options, dict):
                return self.field_options.get("options", [])
        return []
    
    @property
    def is_select_field(self) -> bool:
        """Check if this is a select field"""
        return self.field_type == "select"
    
    @property
    def is_number_field(self) -> bool:
        """Check if this is a number field"""
        return self.field_type in ["number", "currency"]
    
    @property
    def validation_pattern(self) -> Optional[str]:
        """Get validation pattern if defined"""
        if self.validation_rules:
            return self.validation_rules.get("pattern")
        return None
    
    @property
    def min_value(self) -> Optional[float]:
        """Get minimum value for number fields"""
        if self.validation_rules and self.is_number_field:
            return self.validation_rules.get("min")
        return None
    
    @property
    def max_value(self) -> Optional[float]:
        """Get maximum value for number fields"""
        if self.validation_rules and self.is_number_field:
            return self.validation_rules.get("max")
        return None
    
    def validate_value(self, value: Any) -> tuple[bool, Optional[str]]:
        """
        Validate a value against this field configuration
        Returns (is_valid, error_message)
        """
        if value is None or value == "":
            if self.is_required:
                return False, f"{self.field_label} is required"
            return True, None
        
        # Type-specific validation
        if self.field_type == "number":
            try:
                num_value = float(value)
                if self.min_value is not None and num_value < self.min_value:
                    return False, f"{self.field_label} must be at least {self.min_value}"
                if self.max_value is not None and num_value > self.max_value:
                    return False, f"{self.field_label} must be at most {self.max_value}"
            except (ValueError, TypeError):
                return False, f"{self.field_label} must be a valid number"
        
        elif self.field_type == "currency":
            try:
                num_value = float(value)
                if num_value < 0:
                    return False, f"{self.field_label} cannot be negative"
                if self.min_value is not None and num_value < self.min_value:
                    return False, f"{self.field_label} must be at least {self.min_value}"
                if self.max_value is not None and num_value > self.max_value:
                    return False, f"{self.field_label} must be at most {self.max_value}"
            except (ValueError, TypeError):
                return False, f"{self.field_label} must be a valid amount"
        
        elif self.field_type == "select":
            if str(value) not in self.select_options:
                return False, f"{self.field_label} must be one of: {', '.join(self.select_options)}"
        
        elif self.field_type == "text":
            if self.validation_rules:
                min_length = self.validation_rules.get("min_length")
                max_length = self.validation_rules.get("max_length")
                
                if min_length and len(str(value)) < min_length:
                    return False, f"{self.field_label} must be at least {min_length} characters"
                if max_length and len(str(value)) > max_length:
                    return False, f"{self.field_label} must be at most {max_length} characters"
        
        return True, None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert field configuration to dictionary"""
        return {
            "id": self.id,
            "field_name": self.field_name,
            "field_type": self.field_type,
            "field_label": self.field_label,
            "is_required": self.is_required,
            "is_visible_in_list": self.is_visible_in_list,
            "field_options": self.field_options,
            "validation_rules": self.validation_rules,
            "display_order": self.display_order,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "select_options": self.select_options,
            "is_select_field": self.is_select_field,
            "is_number_field": self.is_number_field,
        }
    
    def __repr__(self):
        return f"<FieldConfiguration(name='{self.field_name}', type='{self.field_type}', label='{self.field_label}')>"


# Valid field types
FIELD_TYPES = [
    "text",
    "number", 
    "currency",
    "date",
    "boolean",
    "select"
]


def validate_field_type(field_type: str) -> bool:
    """Validate if field type is supported"""
    return field_type in FIELD_TYPES


def get_active_fields(db_session, visible_only: bool = False):
    """Get active field configurations ordered by display_order"""
    query = db_session.query(FieldConfiguration).filter(FieldConfiguration.is_active == True)
    
    if visible_only:
        query = query.filter(FieldConfiguration.is_visible_in_list == True)
    
    return query.order_by(FieldConfiguration.display_order, FieldConfiguration.field_name).all()


def get_required_fields(db_session):
    """Get all required field configurations"""
    return db_session.query(FieldConfiguration).filter(
        FieldConfiguration.is_active == True,
        FieldConfiguration.is_required == True
    ).all()


def validate_student_data(db_session, student_data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate student data against all field configurations
    Returns (is_valid, error_messages)
    """
    field_configs = get_active_fields(db_session)
    errors = []
    
    for field_config in field_configs:
        value = student_data.get(field_config.field_name)
        is_valid, error_msg = field_config.validate_value(value)
        
        if not is_valid:
            errors.append(error_msg)
    
    return len(errors) == 0, errors


# Additional CRUD functions for API compatibility
def create_field_configuration(db, field_data: dict):
    """Create a new field configuration"""
    field_config = FieldConfiguration(**field_data)
    db.add(field_config)
    db.commit()
    db.refresh(field_config)
    return field_config


def get_field_configuration_by_id(db, field_id: int):
    """Get field configuration by ID"""
    return db.query(FieldConfiguration).filter(FieldConfiguration.id == field_id).first()


def get_field_configuration_by_name(db, field_name: str):
    """Get field configuration by name"""
    return db.query(FieldConfiguration).filter(FieldConfiguration.field_name == field_name).first()


def get_field_configurations(db, skip: int = 0, limit: int = 100, active_only: bool = None):
    """Get list of field configurations with optional filters"""
    query = db.query(FieldConfiguration)
    
    if active_only is not None:
        query = query.filter(FieldConfiguration.is_active == active_only)
    
    return query.order_by(FieldConfiguration.display_order, FieldConfiguration.field_name).offset(skip).limit(limit).all()


def update_field_configuration(db, field_id: int, field_data: dict):
    """Update field configuration"""
    field_config = db.query(FieldConfiguration).filter(FieldConfiguration.id == field_id).first()
    if not field_config:
        return None
    
    for key, value in field_data.items():
        if hasattr(field_config, key):
            setattr(field_config, key, value)
    
    db.commit()
    db.refresh(field_config)
    return field_config


def delete_field_configuration(db, field_id: int):
    """Delete field configuration (soft delete by setting is_active=False)"""
    field_config = db.query(FieldConfiguration).filter(FieldConfiguration.id == field_id).first()
    if not field_config:
        return False
    
    field_config.is_active = False
    db.commit()
    return True


def get_all_fields(db, skip: int = 0, limit: int = 100):
    """Get all field configurations (alias for get_field_configurations)"""
    return get_field_configurations(db, skip=skip, limit=limit, active_only=None)
