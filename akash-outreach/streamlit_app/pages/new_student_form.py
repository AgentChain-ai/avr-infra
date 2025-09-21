import streamlit as st
from typing import Dict, Any

def show_add_student_form(api_client):
    """Display dynamic form to add new student based on field configurations"""
    
    st.subheader("➕ Add New Student")
    
    # Load field configurations
    try:
        with st.spinner("🔄 Loading form fields..."):
            fields = api_client.get_fields(include_inactive=False)
        
        if not fields:
            st.warning("⚠️ No field configurations found. Please configure fields first in the Field Configuration page.")
            return
            
    except Exception as e:
        st.error(f"❌ Error loading field configurations: {str(e)}")
        return
    
    with st.form("add_student", clear_on_submit=True):
        # Add standard required fields first (phone_number is always required)
        st.markdown("**📱 Required Information**")
        col1, col2 = st.columns(2)
        
        with col1:
            phone_number = st.text_input(
                "Phone Number *", 
                placeholder="10-digit mobile number",
                help="Required field - student's contact number"
            )
        
        with col2:
            student_name = st.text_input("Student Name", placeholder="Full name of the student")
        
        # Dynamically generate form fields based on configuration
        st.markdown("**📋 Additional Information**")
        
        # Group fields by pairs for better layout
        active_fields = [f for f in fields if f.get('is_active', True)]
        student_data = {}
        
        # Process fields in pairs for column layout
        for i in range(0, len(active_fields), 2):
            col1, col2 = st.columns(2)
            
            # First field in the pair
            field = active_fields[i]
            with col1:
                value = render_dynamic_field(field)
                if value is not None:
                    student_data[field['field_name']] = value
            
            # Second field in the pair (if exists)
            if i + 1 < len(active_fields):
                field = active_fields[i + 1]
                with col2:
                    value = render_dynamic_field(field)
                    if value is not None:
                        student_data[field['field_name']] = value
        
        # Submit button
        submitted = st.form_submit_button("🚀 Add Student", type="primary")
        
        if submitted:
            # Validate required fields
            if not phone_number:
                st.error("❌ Phone number is required")
                return
            
            # Validate dynamic required fields
            validation_errors = []
            for field in active_fields:
                if field.get('is_required', False):
                    field_value = student_data.get(field['field_name'])
                    if not field_value:
                        validation_errors.append(f"• {field['field_label']} is required")
            
            if validation_errors:
                st.error("❌ Please fill in the following required fields:\n" + "\n".join(validation_errors))
                return
            
            try:
                # Prepare student data
                final_student_data = {
                    "phone_number": phone_number,
                    "student_name": student_name,
                    **student_data  # Include all dynamic field data
                }
                
                # Create student
                api_client.create_student(final_student_data)
                
                # Store success message in session state
                st.session_state.student_success_message = f"✅ Student '{student_name or phone_number}' added successfully! 🎉"
                st.rerun()
                
            except Exception as e:
                error_msg = str(e)
                # Store error message in session state
                st.session_state.student_error_message = f"❌ Error adding student: {error_msg}"
                st.rerun()


def render_dynamic_field(field: Dict[str, Any]) -> Any:
    """Render a dynamic form field based on field configuration"""
    
    field_name = field['field_name']
    field_label = field['field_label']
    field_type = field['field_type']
    is_required = field.get('is_required', False)
    field_options = field.get('field_options', [])
    
    # Add required indicator
    label = f"{field_label} {'*' if is_required else ''}"
    
    try:
        if field_type == "text":
            return st.text_input(
                label,
                key=f"field_{field_name}",
                help=f"Text field: {field_label}"
            )
        
        elif field_type == "number":
            return st.number_input(
                label,
                key=f"field_{field_name}",
                min_value=0,
                help=f"Numeric field: {field_label}"
            )
        
        elif field_type == "select":
            if not field_options:
                st.warning(f"⚠️ Select field '{field_label}' has no options configured")
                return None
            
            # Add empty option for non-required fields
            options = [""] + field_options if not is_required else field_options
            return st.selectbox(
                label,
                options=options,
                key=f"field_{field_name}",
                help=f"Select from options: {', '.join(field_options)}"
            )
        
        elif field_type == "email":
            return st.text_input(
                label,
                key=f"field_{field_name}",
                placeholder="example@email.com",
                help=f"Email field: {field_label}"
            )
        
        elif field_type == "phone":
            return st.text_input(
                label,
                key=f"field_{field_name}",
                placeholder="10-digit number",
                help=f"Phone field: {field_label}"
            )
        
        elif field_type == "textarea":
            return st.text_area(
                label,
                key=f"field_{field_name}",
                help=f"Text area: {field_label}"
            )
        
        elif field_type == "date":
            return st.date_input(
                label,
                key=f"field_{field_name}",
                help=f"Date field: {field_label}"
            )
        
        else:
            # Fallback to text input for unknown types
            return st.text_input(
                label,
                key=f"field_{field_name}",
                help=f"Unknown field type '{field_type}': {field_label}"
            )
    
    except Exception as e:
        st.error(f"❌ Error rendering field '{field_label}': {str(e)}")
        return None

