"""
Field configuration management page
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List

def show_fields():
    """Display field configuration page"""
    
    st.title("⚙️ Field Configuration")
    st.markdown("Manage dynamic fields for student data collection and display.")
    
    # Check API connection
    if not st.session_state.get("api_client"):
        st.error("❌ No API connection. Please refresh the page.")
        return
    
    api_client = st.session_state.api_client
    
    # Check if we're in edit mode
    if st.session_state.get("editing_field_id"):
        show_edit_field_interface(api_client)
    else:
        # Main tabs
        tab1, tab2 = st.tabs(["📋 Current Fields", "➕ Add New Field"])
        
        with tab1:
            show_fields_list(api_client)
        
        with tab2:
            show_add_field_form(api_client)

def show_edit_field_interface(api_client):
    """Display the edit field interface with back button"""
    
    field_data = st.session_state.get("editing_field_data")
    if not field_data:
        st.error("❌ No field data found")
        return
    
    # Back button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← Back to Fields", type="secondary"):
            st.session_state.pop("editing_field_id", None)
            st.session_state.pop("editing_field_data", None)
            st.rerun()
    
    with col2:
        st.subheader(f"✏️ Edit Field: {field_data.get('field_label')}")
    
    # Edit form
    with st.form(f"edit_field_{field_data.get('id')}"):
        # Pre-populate with existing values
        col1, col2 = st.columns(2)
        
        with col1:
            field_label = st.text_input("Display Label", value=field_data.get('field_label', ''))
            field_type = st.selectbox(
                "Field Type",
                options=["text", "number", "select", "email", "phone", "textarea", "date"],
                index=["text", "number", "select", "email", "phone", "textarea", "date"].index(field_data.get('field_type', 'text'))
            )
        
        with col2:
            is_required = st.checkbox("Required Field", value=field_data.get('is_required', False))
            is_visible_in_list = st.checkbox("Visible in Student List", value=field_data.get('is_visible_in_list', True))
            is_active = st.checkbox("Active", value=field_data.get('is_active', True))
            display_order = st.number_input("Display Order", min_value=1, value=field_data.get('display_order', 10))
        
        # Field options for select type
        field_options = []
        if field_type == "select":
            st.markdown("**Select Options**")
            existing_options = field_data.get('field_options', [])
            options_text = st.text_area(
                "Options (one per line)",
                value='\n'.join(existing_options) if existing_options else '',
                help="Enter each option on a new line"
            )
            if options_text:
                field_options = [opt.strip() for opt in options_text.split('\n') if opt.strip()]
        
        # Validation rules
        validation_rules = st.text_input(
            "Validation Rules",
            value=field_data.get('validation_rules', '') or '',
            help="Custom validation rules for the field"
        )
        
        # Submit buttons
        col_save, col_cancel = st.columns(2)
        
        with col_save:
            submitted = st.form_submit_button("💾 Save Changes", type="primary")
        
        with col_cancel:
            if st.form_submit_button("❌ Cancel"):
                st.session_state.pop("editing_field_id", None)
                st.session_state.pop("editing_field_data", None)
                st.rerun()
        
        if submitted:
            try:
                # Prepare update data
                update_data = {
                    "field_label": field_label,
                    "field_type": field_type,
                    "is_required": is_required,
                    "is_visible_in_list": is_visible_in_list,
                    "is_active": is_active,
                    "display_order": display_order
                }
                
                if field_options:
                    update_data["field_options"] = field_options
                
                if validation_rules:
                    update_data["validation_rules"] = validation_rules
                
                # Update field
                api_client.update_field(field_data.get('id'), update_data)
                
                st.success(f"✅ Field '{field_label}' updated successfully!")
                st.session_state.pop("editing_field_id", None)
                st.session_state.pop("editing_field_data", None)
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error updating field: {str(e)}")

def show_fields_list(api_client):
    """Display list of existing fields with management options"""
    
    st.subheader("📋 Current Fields")
    
    try:
        # Get fields from API
        with st.spinner("📊 Loading field configurations..."):
            fields = api_client.get_fields()
        
        if not fields:
            st.info("📝 No fields configured yet. Use the 'Add New Field' tab to create your first field.")
            return
        
        # Convert to DataFrame for better display
        fields_df = pd.DataFrame(fields)
        
        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Fields", len(fields))
        
        with col2:
            active_fields = len([f for f in fields if f.get('is_active', True)])
            st.metric("Active Fields", active_fields)
        
        with col3:
            required_fields = len([f for f in fields if f.get('is_required', False)])
            st.metric("Required Fields", required_fields)
        
        with col4:
            visible_fields = len([f for f in fields if f.get('is_visible_in_list', False)])
            st.metric("Visible in List", visible_fields)
        
        st.markdown("---")
        
        # Display fields as cards
        for field in fields:
            render_field_card(field, api_client)
        
    except Exception as e:
        st.error(f"❌ Error loading fields: {str(e)}")

def render_field_card(field: Dict[str, Any], api_client):
    """Render a single field as a card"""
    
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Field info
            status_icon = "🟢" if field.get('is_active', True) else "🔴"
            required_icon = "⭐" if field.get('is_required', False) else ""
            visible_icon = "👁️" if field.get('is_visible_in_list', False) else ""
            
            st.markdown(f"""
            **{status_icon} {field.get('field_label', 'Unnamed Field')} {required_icon} {visible_icon}**
            
            - **Type:** {field.get('field_type', 'unknown').title()}
            - **Internal Name:** `{field.get('field_name', 'unnamed')}`
            - **Display Order:** {field.get('display_order', 0)}
            """)
            
            # Show options for select fields
            if field.get('field_type') == 'select' and field.get('field_options'):
                options = field.get('field_options', [])
                st.markdown(f"**Options:** {', '.join(options[:3])}{'...' if len(options) > 3 else ''}")
        
        with col2:
            # Action buttons
            col_edit, col_delete = st.columns(2)
            
            with col_edit:
                if st.button("✏️ Edit", key=f"edit_{field.get('id')}", use_container_width=True):
                    st.session_state["editing_field_id"] = field.get('id')
                    st.session_state["editing_field_data"] = field
                    st.rerun()
            
            with col_delete:
                if st.button("🗑️ Delete", key=f"delete_{field.get('id')}", use_container_width=True, type="secondary"):
                    if st.session_state.get(f"confirm_delete_{field.get('id')}"):
                        delete_field(field.get('id'), api_client)
                    else:
                        st.session_state[f"confirm_delete_{field.get('id')}"] = True
                        st.rerun()
            
            # Show confirmation for delete
            if st.session_state.get(f"confirm_delete_{field.get('id')}"):
                st.warning("⚠️ Click Delete again to confirm")
        
        st.markdown("---")

def show_add_field_form(api_client):
    """Display form to add a new field"""
    
    st.subheader("➕ Add New Field")
    
    with st.form("add_field", clear_on_submit=True):
        # Basic field information
        col1, col2 = st.columns(2)
        
        with col1:
            field_name = st.text_input(
                "Field Name *", 
                placeholder="e.g., student_email, course_preference",
                help="Internal name for the field (lowercase, no spaces)"
            )
            
            field_label = st.text_input(
                "Display Label *", 
                placeholder="e.g., Student Email, Course Preference",
                help="Human-readable label shown in forms"
            )
            
            field_type = st.selectbox(
                "Field Type *",
                options=["text", "number", "select", "email", "phone", "textarea", "date"],
                help="Type of input field"
            )
        
        with col2:
            is_required = st.checkbox("Required Field", help="Must be filled when creating students")
            is_visible_in_list = st.checkbox("Visible in Student List", value=True, help="Show in student table view")
            is_active = st.checkbox("Active", value=True, help="Field is available for use")
            display_order = st.number_input("Display Order", min_value=1, value=10, help="Order in forms and lists")
        
        # Field options for select type
        field_options = []
        if field_type == "select":
            st.markdown("**Select Options**")
            options_text = st.text_area(
                "Options (one per line)",
                placeholder="Option 1\nOption 2\nOption 3",
                help="Enter each option on a new line"
            )
            if options_text:
                field_options = [opt.strip() for opt in options_text.split('\n') if opt.strip()]
        
        # Validation rules
        validation_rules = st.text_input(
            "Validation Rules",
            placeholder="e.g., regex pattern or validation expression",
            help="Custom validation rules for the field (optional)"
        )
        
        # Submit button
        submitted = st.form_submit_button("🚀 Create Field", type="primary")
        
        if submitted:
            # Validation
            if not field_name or not field_label:
                st.error("❌ Field name and display label are required")
                return
            
            if field_type == "select" and not field_options:
                st.error("❌ Select fields must have at least one option")
                return
            
            try:
                # Prepare field data
                field_data = {
                    "field_name": field_name,
                    "field_label": field_label,
                    "field_type": field_type,
                    "is_required": is_required,
                    "is_visible_in_list": is_visible_in_list,
                    "is_active": is_active,
                    "display_order": display_order
                }
                
                if field_options:
                    field_data["field_options"] = field_options
                
                if validation_rules:
                    field_data["validation_rules"] = validation_rules
                
                # Create field
                new_field = api_client.create_field(field_data)
                
                st.success(f"✅ Field '{field_label}' created successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error creating field: {str(e)}")

def delete_field(field_id: int, api_client):
    """Delete a field configuration"""
    
    try:
        if api_client.delete_field(field_id):
            st.success("✅ Field deleted successfully!")
            # Clear confirmation state
            if f"confirm_delete_{field_id}" in st.session_state:
                del st.session_state[f"confirm_delete_{field_id}"]
            st.rerun()
        else:
            st.error("❌ Failed to delete field")
    except Exception as e:
        st.error(f"❌ Error deleting field: {str(e)}")
