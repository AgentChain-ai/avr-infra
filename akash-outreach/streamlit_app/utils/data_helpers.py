"""
Data helpers for processing and formatting data in Streamlit app
"""

import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

def clean_phone_number(phone: str) -> str:
    """Clean and format phone number"""
    if not phone:
        return ""
    
    # Remove all non-digits
    digits = re.sub(r'\D', '', str(phone))
    
    # Handle Indian phone numbers
    if len(digits) == 10:
        return digits
    elif len(digits) == 11 and digits.startswith('0'):
        return digits[1:]
    elif len(digits) == 12 and digits.startswith('91'):
        return digits[2:]
    elif len(digits) == 13 and digits.startswith('+91'):
        return digits[3:]
    
    return digits

def format_datetime(dt_str: str) -> str:
    """Format datetime string for display"""
    if not dt_str:
        return ""
    
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return dt_str[:16] if len(dt_str) > 16 else dt_str

def format_priority_badge(priority: int) -> str:
    """Format priority as colored badge"""
    if priority >= 8:
        return f"🔴 {priority} (Critical)"
    elif priority >= 5:
        return f"🟡 {priority} (High)"
    elif priority >= 3:
        return f"🟢 {priority} (Medium)"
    else:
        return f"⚪ {priority} (Low)"

def format_call_status_badge(status: str) -> str:
    """Format call status as colored badge"""
    status_map = {
        "pending": "⏳ Pending",
        "attempted": "📞 Attempted", 
        "completed": "✅ Completed",
        "failed": "❌ Failed",
        "callback_requested": "🔄 Callback",
        "in_progress": "⏰ In Progress",
        "no_answer": "📵 No Answer",
        "busy": "📞 Busy"
    }
    return status_map.get(status, f"❓ {status.title()}")

def detect_csv_encoding(file_bytes: bytes) -> str:
    """Detect CSV file encoding"""
    try:
        import chardet
        result = chardet.detect(file_bytes)
        return result.get('encoding', 'utf-8')
    except:
        return 'utf-8'

def suggest_field_mapping(csv_columns: List[str]) -> Dict[str, str]:
    """Suggest field mappings for CSV columns using AI/heuristics"""
    
    mapping_rules = {
        # Phone number patterns
        r'phone|mobile|contact|number': 'phone_number',
        
        # Student name patterns  
        r'student.*name|name.*student|student': 'student_name',
        
        # Parent name patterns
        r'parent.*name|father.*name|mother.*name|guardian': 'parent_name',
        
        # Priority patterns
        r'priority|importance|urgent': 'priority',
        
        # Course patterns
        r'course|class|program|batch': 'course',
        
        # Scholarship patterns
        r'scholarship.*amount|amount.*scholarship': 'scholarship_amount',
        r'scholarship.*percent|percent.*scholarship': 'scholarship_percentage',
        
        # Rank patterns
        r'rank|position|score': 'rank',
        
        # Address patterns
        r'address|location|city|state': 'address',
        
        # Email patterns
        r'email|mail': 'email',
        
        # Notes patterns
        r'note|comment|remark|detail': 'notes'
    }
    
    suggestions = {}
    
    for col in csv_columns:
        col_lower = col.lower().strip()
        
        for pattern, field_name in mapping_rules.items():
            if re.search(pattern, col_lower):
                suggestions[col] = field_name
                break
        
        # If no match found, suggest a cleaned version
        if col not in suggestions:
            suggestions[col] = col_lower.replace(' ', '_').replace('-', '_')
    
    return suggestions

def validate_student_data(data: Dict[str, Any]) -> List[str]:
    """Validate student data and return list of errors"""
    errors = []
    
    # Required fields
    if not data.get('phone_number'):
        errors.append("Phone number is required")
    
    # Phone number format
    phone = data.get('phone_number', '')
    if phone and not re.match(r'^\d{10}$', clean_phone_number(phone)):
        errors.append("Phone number must be 10 digits")
    
    # Priority range
    priority = data.get('priority', 1)
    if not isinstance(priority, int) or priority < 1 or priority > 10:
        errors.append("Priority must be between 1 and 10")
    
    # Call status values
    valid_statuses = ["pending", "attempted", "completed", "failed", "callback_requested", "in_progress", "no_answer", "busy"]
    status = data.get('call_status', 'pending')
    if status not in valid_statuses:
        errors.append(f"Invalid call status: {status}")
    
    # Check for required scholarship_type field
    student_data = data.get('student_data', {})
    if not student_data.get('scholarship_type'):
        errors.append("Scholarship Type is required")
    
    # Validate scholarship_type values
    valid_scholarship_types = ["Full Scholarship", "Partial Scholarship", "Merit Based", "Need Based"]
    scholarship_type = student_data.get('scholarship_type')
    if scholarship_type and scholarship_type not in valid_scholarship_types:
        errors.append(f"Invalid scholarship type: {scholarship_type}. Must be one of: {', '.join(valid_scholarship_types)}")
    
    return errors

def prepare_export_data(students: List[Dict[str, Any]]) -> pd.DataFrame:
    """Prepare student data for CSV export"""
    
    export_data = []
    
    for student in students:
        # Flatten student data
        row = {
            'id': student.get('id'),
            'phone_number': student.get('phone_number'),
            'call_status': student.get('call_status'),
            'priority': student.get('priority'),
            'call_count': student.get('call_count', 0),
            'created_at': format_datetime(student.get('created_at', '')),
            'updated_at': format_datetime(student.get('updated_at', '')),
            'last_call_attempt': format_datetime(student.get('last_call_attempt', ''))
        }
        
        # Add student_data fields
        student_data = student.get('student_data', {})
        for key, value in student_data.items():
            row[key] = value
        
        export_data.append(row)
    
    return pd.DataFrame(export_data)

def generate_sample_csv() -> str:
    """Generate sample CSV data for download"""
    
    sample_data = [
        {
            "phone_number": "9876543210",
            "student_name": "Raj Kumar",
            "parent_name": "Mr. Suresh Kumar", 
            "course": "JEE Starter",
            "priority": 3,
            "scholarship_amount": 5000,
            "scholarship_percentage": "25%",
            "scholarship_type": "Merit Based",
            "rank": 127,
            "city": "Delhi",
            "notes": "Interested in advanced math course"
        },
        {
            "phone_number": "9876543211",
            "student_name": "Priya Sharma",
            "parent_name": "Mrs. Meera Sharma",
            "course": "NEET Foundation", 
            "priority": 2,
            "scholarship_amount": 7500,
            "scholarship_percentage": "30%",
            "scholarship_type": "Need Based",
            "rank": 89,
            "city": "Mumbai",
            "notes": "Strong in biology, needs chemistry help"
        },
        {
            "phone_number": "9876543212",
            "student_name": "Amit Patel",
            "parent_name": "Dr. Rakesh Patel",
            "course": "JEE Advanced",
            "priority": 5,
            "scholarship_amount": 10000,
            "scholarship_percentage": "50%",
            "scholarship_type": "Full Scholarship", 
            "rank": 45,
            "city": "Ahmedabad",
            "notes": "Top performer, considering multiple institutes"
        }
    ]
    
    df = pd.DataFrame(sample_data)
    return df.to_csv(index=False)

def analyze_csv_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze CSV data quality and provide insights"""
    
    analysis = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "missing_data": {},
        "data_types": {},
        "potential_issues": []
    }
    
    for col in df.columns:
        # Missing data
        missing_count = df[col].isna().sum()
        missing_percent = (missing_count / len(df)) * 100
        analysis["missing_data"][col] = {
            "count": missing_count,
            "percentage": missing_percent
        }
        
        # Data types
        analysis["data_types"][col] = str(df[col].dtype)
        
        # Potential issues
        if missing_percent > 50:
            analysis["potential_issues"].append(f"Column '{col}' has {missing_percent:.1f}% missing data")
        
        # Check for phone number patterns
        if 'phone' in col.lower() or 'mobile' in col.lower():
            non_numeric = df[col].dropna().astype(str).str.contains(r'[^\d+\-\(\)\s]').sum()
            if non_numeric > 0:
                analysis["potential_issues"].append(f"Column '{col}' contains non-phone number formats")
    
    return analysis
