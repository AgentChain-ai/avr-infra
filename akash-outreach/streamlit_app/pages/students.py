"""
Students management page
Complete CRUD interface with AI-powered CSV upload
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
from utils.data_helpers import (
    clean_phone_number, 
    format_datetime, 
    format_priority_badge,
    format_call_status_badge,
    suggest_field_mapping,
    validate_student_data,
    prepare_export_data,
    generate_sample_csv,
    analyze_csv_quality
)

def show_students():
    """Display students management page"""
    
    st.title("👥 Student Management")
    
    # Check API client
    if not st.session_state.get("api_client"):
        st.error("❌ No API connection. Please refresh the page.")
        return
    
    api_client = st.session_state.api_client
    
    # Display global success/error messages at the top
    if 'student_success_message' in st.session_state:
        st.success(st.session_state.student_success_message)
        # Clear the message after displaying it
        del st.session_state.student_success_message
        # Add balloons for extra celebration
        st.balloons()
    
    if 'student_error_message' in st.session_state:
        st.error(st.session_state.student_error_message)
        # Clear the message after displaying it
        del st.session_state.student_error_message
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Students List", "➕ Add Student", "📁 Upload CSV", "📊 Analytics"])
    
    with tab1:
        show_students_list(api_client)
    
    with tab2:
        show_add_student_form(api_client)
    
    with tab3:
        show_csv_upload(api_client)
    
    with tab4:
        show_student_analytics(api_client)

def show_students_list(api_client):
    """Display students list with search, filters, and editing"""
    
    st.subheader("📋 Students Database")
    
    # Search and filter controls
    col_search, col_filter1, col_filter2, col_refresh = st.columns([3, 1, 1, 1])
    
    with col_search:
        search_query = st.text_input("🔍 Search students", placeholder="Name, phone, or any field...")
    
    with col_filter1:
        call_status_filter = st.selectbox(
            "📞 Call Status",
            ["All", "pending", "completed", "failed", "attempted"]
        )
    
    with col_filter2:
        priority_filter = st.selectbox(
            "⭐ Priority",
            ["All", "High (3+)", "Medium (2)", "Low (1)"]
        )
    
    with col_refresh:
        if st.button("🔄 Refresh", key="refresh_students"):
            st.rerun()
    
    try:
        # Get students data
        with st.spinner("📊 Loading students..."):
            if search_query:
                students_data = api_client.search_students(search_query, limit=100)
            else:
                filters = {}
                if call_status_filter != "All":
                    filters["call_status"] = call_status_filter
                if priority_filter != "All":
                    if priority_filter == "High (3+)":
                        filters["min_priority"] = 3
                    elif priority_filter == "Medium (2)":
                        filters["priority"] = 2
                    elif priority_filter == "Low (1)":
                        filters["priority"] = 1
                
                students_data = api_client.get_students(limit=100, **filters)
        
        students = students_data.get("students", [])
        total_students = students_data.get("total", 0)
        
        # Display summary
        col_summary1, col_summary2, col_summary3 = st.columns(3)
        
        with col_summary1:
            st.metric("Total Students", f"{total_students:,}")
        
        with col_summary2:
            pending_count = len([s for s in students if s.get("call_status") == "pending"])
            st.metric("Pending Calls", f"{pending_count:,}")
        
        with col_summary3:
            high_priority = len([s for s in students if s.get("priority", 0) >= 3])
            st.metric("High Priority", f"{high_priority:,}")
        
        if students:
            # Convert to DataFrame for display
            df = prepare_students_dataframe(students)
            
            # Display editable data table
            st.subheader(f"📋 Students ({len(students)} shown)")
            
            # Action buttons
            col_action1, col_action2, col_action3, col_action4 = st.columns(4)
            
            with col_action1:
                if st.button("📞 Start Calls", key="start_calls"):
                    st.info("🚧 Call feature coming soon!")
            
            with col_action2:
                if st.button("✅ Mark Completed", key="bulk_complete"):
                    st.info("🚧 Bulk operations coming soon!")
            
            with col_action3:
                if st.button("📊 Export Data", key="export_data"):
                    # Export full dataset with all fields
                    export_df = prepare_export_data(students)
                    csv = export_df.to_csv(index=False)
                    
                    # Generate filename with timestamp
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"students_export_{timestamp}.csv"
                    
                    st.download_button(
                        "📥 Download Complete Data",
                        csv,
                        filename,
                        "text/csv",
                        help=f"Download {len(students)} students with all fields"
                    )
            
            with col_action4:
                if st.button("🗑️ Delete Selected", key="delete_selected"):
                    st.info("🚧 Bulk delete coming soon!")
            
            # Display the data table
            display_students_table(df, api_client)
            
        else:
            st.info("📝 No students found matching your criteria.")
            
            if st.button("➕ Add Your First Student"):
                st.session_state.active_tab = "add_student"
                st.rerun()
    
    except Exception as e:
        st.error(f"❌ Error loading students: {str(e)}")

def prepare_students_dataframe(students: List[Dict[str, Any]]) -> pd.DataFrame:
    """Convert students list to DataFrame for display with formatting"""
    
    # Flatten student data for table display
    flattened_data = []
    
    for student in students:
        # Get student_data safely
        student_data = student.get("student_data", {})
        
        row = {
            "ID": student.get("id"),
            "Phone": student.get("phone_number"),
            "Student Name": student_data.get("student_name", "N/A"),
            "Parent Name": student_data.get("parent_name", "N/A"),
            "Status": format_call_status_badge(student.get("call_status", "pending")),
            "Priority": format_priority_badge(student.get("priority", 1)),
            "Calls": student.get("call_count", 0),
            "Course": student_data.get("course", "N/A"),
            "Created": format_datetime(student.get("created_at", "")),
            "Last Updated": format_datetime(student.get("updated_at", "")),
        }
        
        # Add scholarship info if available
        if student_data.get("scholarship_amount"):
            row["Scholarship"] = f"₹{student_data['scholarship_amount']:,}"
        
        if student_data.get("scholarship_percentage"):
            row["Scholarship %"] = student_data["scholarship_percentage"]
        
        if student_data.get("rank"):
            row["Rank"] = student_data["rank"]
        
        # Add any other important fields
        for key, value in student_data.items():
            if key not in ["student_name", "parent_name", "course", "scholarship_amount", "scholarship_percentage", "rank"] and value:
                if isinstance(value, (str, int, float)):
                    display_key = key.replace("_", " ").title()
                    if display_key not in row:  # Avoid duplicates
                        row[display_key] = value
        
        flattened_data.append(row)
    
    return pd.DataFrame(flattened_data)

def display_students_table(df: pd.DataFrame, api_client):
    """Display interactive students table"""
    
    # Use st.dataframe for better interactivity
    event = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="multi-row"
    )
    
    # Handle row selection for editing
    if hasattr(event, 'selection') and event.selection.get('rows'):
        selected_rows = event.selection['rows']
        if len(selected_rows) == 1:
            selected_student_id = df.iloc[selected_rows[0]]['ID']
            
            st.subheader(f"✏️ Edit Student #{selected_student_id}")
            
            # Get full student data
            try:
                student_data = api_client.get_student(selected_student_id)
                show_edit_student_form(student_data, api_client)
            except Exception as e:
                st.error(f"❌ Error loading student details: {str(e)}")
        
        elif len(selected_rows) > 1:
            st.info(f"📋 {len(selected_rows)} students selected. Bulk operations coming soon!")

def show_edit_student_form(student_data: Dict[str, Any], api_client):
    """Show form to edit student data"""
    
    with st.form(f"edit_student_{student_data['id']}"):
        st.markdown("**📝 Student Information**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_phone = st.text_input("Phone Number", value=student_data.get("phone_number", ""))
            new_call_status = st.selectbox(
                "Call Status",
                ["pending", "attempted", "completed", "failed", "callback_requested"],
                index=["pending", "attempted", "completed", "failed", "callback_requested"].index(
                    student_data.get("call_status", "pending")
                )
            )
        
        with col2:
            new_priority = st.number_input(
                "Priority", 
                min_value=1, 
                max_value=10, 
                value=student_data.get("priority", 1)
            )
        
        # Dynamic fields based on student data
        st.markdown("**📋 Additional Information**")
        
        student_fields = {}
        existing_data = {k: v for k, v in student_data.items() 
                        if k not in ["id", "phone_number", "call_status", "priority", "call_count", "created_at", "updated_at", "last_call_attempt"]}
        
        for key, value in existing_data.items():
            if isinstance(value, str):
                student_fields[key] = st.text_input(key.replace("_", " ").title(), value=value, key=f"edit_{key}")
            elif isinstance(value, (int, float)):
                student_fields[key] = st.number_input(key.replace("_", " ").title(), value=value, key=f"edit_{key}")
            else:
                student_fields[key] = st.text_input(key.replace("_", " ").title(), value=str(value), key=f"edit_{key}")
        
        # Submit buttons
        col_submit1, col_submit2, col_submit3 = st.columns(3)
        
        with col_submit1:
            submitted = st.form_submit_button("💾 Save Changes", type="primary")
        
        with col_submit2:
            if st.form_submit_button("🗑️ Delete Student"):
                if api_client.delete_student(student_data["id"]):
                    display_name = student_data.get('display_name', f"Student #{student_data['id']}")
                    st.session_state.student_success_message = f"✅ Student '{display_name}' deleted successfully!"
                    st.rerun()
                else:
                    st.session_state.student_error_message = "❌ Failed to delete student"
                    st.rerun()
        
        with col_submit3:
            if st.form_submit_button("❌ Cancel"):
                st.rerun()
        
        if submitted:
            try:
                # Prepare update data
                update_data = {
                    "phone_number": new_phone,
                    "call_status": new_call_status,
                    "priority": new_priority,
                    "student_data": student_fields
                }
                
                # Update student
                api_client.update_student(student_data["id"], update_data)
                
                # Store success message in session state
                display_name = student_fields.get('student_name', f"Student #{student_data['id']}")
                st.session_state.student_success_message = f"✅ Student '{display_name}' updated successfully!"
                st.rerun()
                
            except Exception as e:
                st.session_state.student_error_message = f"❌ Error updating student: {str(e)}"
                st.rerun()

def show_add_student_form(api_client):
    """Display form to add new student"""
    
    st.subheader("➕ Add New Student")
    
    with st.form("add_student", clear_on_submit=True):
        # Basic Info
        col1, col2 = st.columns(2)
        
        with col1:
            phone_number = st.text_input(
                "Phone Number *", 
                placeholder="10-digit mobile number",
                help="Required field - student's contact number"
            )
            
            student_name = st.text_input("Student Name", placeholder="Full name of the student")
            
            course = st.text_input("Course", placeholder="e.g., JEE Main, NEET, Class 12")
        
        with col2:
            priority = st.number_input(
                "Priority", 
                min_value=1, 
                max_value=10, 
                value=1,
                help="1 = Highest priority, 10 = Lowest priority"
            )
            
            parent_name = st.text_input("Parent Name", placeholder="Guardian's full name")
            
            # Get scholarship_type field configuration dynamically
            try:
                fields = api_client.get_fields(include_inactive=False)
                scholarship_field = next((f for f in fields if f['field_name'] == 'scholarship_type'), None)
                
                if scholarship_field and scholarship_field.get('field_options'):
                    scholarship_options = [""] + scholarship_field['field_options']
                else:
                    # Fallback to hardcoded options if field config not found
                    scholarship_options = ["", "Full Scholarship", "Partial Scholarship", "Merit Based", "Need Based"]
            except:
                # Fallback to hardcoded options if API call fails
                scholarship_options = ["", "Full Scholarship", "Partial Scholarship", "Merit Based", "Need Based"]
            
            scholarship_type = st.selectbox(
                "Scholarship Type *",
                options=scholarship_options,
                index=0,
                help="Required field - type of scholarship offered"
            )
        
        # Additional Info
        st.markdown("**� Scholarship Details**")
        col3, col4 = st.columns(2)
        
        with col3:
            scholarship_amount = st.number_input(
                "Scholarship Amount (₹)", 
                min_value=0, 
                value=0,
                step=1000,
                help="Amount in Indian Rupees"
            )
        
        with col4:
            scholarship_percentage = st.text_input(
                "Scholarship Percentage", 
                placeholder="e.g., 25%, 50%",
                help="Percentage of total fee covered"
            )
        
        # Academic Info
        rank = st.number_input(
            "Rank/Score", 
            min_value=0, 
            value=0,
            help="Academic rank or test score"
        )
        
        # Notes
        notes = st.text_area("Notes", placeholder="Any additional information...")
        
        # Submit button
        submitted = st.form_submit_button("➕ Add Student", type="primary")
        
        if submitted:
            if not phone_number:
                st.session_state.student_error_message = "❌ Phone number is required!"
                st.rerun()
                return
            
            if not scholarship_type:
                st.session_state.student_error_message = "❌ Scholarship type is required!"
                st.rerun()
                return
            
            try:
                # Prepare student data
                student_data = {
                    "phone_number": phone_number,
                    "priority": priority,
                    "student_data": {
                        "student_name": student_name,
                        "parent_name": parent_name,
                        "scholarship_type": scholarship_type,
                        "course": course,
                        "scholarship_amount": scholarship_amount,
                        "rank": rank,
                        "scholarship_percentage": scholarship_percentage,
                        "notes": notes
                    }
                }
                
                # Remove empty fields
                student_data["student_data"] = {k: v for k, v in student_data["student_data"].items() if v}
                
                # Create student
                new_student = api_client.create_student(student_data)
                
                # Store success message in session state
                display_name = new_student.get('display_name', new_student.get('student_name', f"Student #{new_student['id']}"))
                success_msg = f"""
                🎉 **Student Added Successfully!**
                
                **Name:** {display_name}  
                **Phone:** {new_student['phone_number']}  
                **ID:** #{new_student['id']}  
                **Scholarship:** {scholarship_type}
                """
                st.session_state.student_success_message = success_msg
                
                # Clear form by rerunning
                st.rerun()
                
            except Exception as e:
                error_msg = str(e)
                if "duplicate" in error_msg.lower() or "already exists" in error_msg.lower():
                    st.session_state.student_error_message = f"⚠️ **Duplicate Student**: A student with phone number **{phone_number}** already exists in the system!"
                elif "validation" in error_msg.lower():
                    st.session_state.student_error_message = f"❌ **Validation Error**: {error_msg}"
                else:
                    st.session_state.student_error_message = f"❌ **Error Adding Student**: {error_msg}"
                st.rerun()

def show_csv_upload(api_client):
    """Display CSV upload interface with AI field mapping"""
    
    st.subheader("📁 Upload Students CSV")
    st.markdown("Upload a CSV file with student data. Our AI will help map the fields automatically.")
    
    # Sample CSV download
    col_download, col_help = st.columns([2, 3])
    
    with col_download:
        sample_csv = generate_sample_csv()
        st.download_button(
            "📥 Download Sample CSV",
            sample_csv,
            "sample_students.csv",
            "text/csv",
            help="Download a sample CSV file with the correct format"
        )
    
    with col_help:
        st.info("💡 **Tips**: Include phone_number and scholarship_type columns (required). Other common fields: student_name, parent_name, course, priority, rank, scholarship_amount")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose CSV file",
        type=['csv'],
        help="Upload a CSV file with student information"
    )
    
    if uploaded_file:
        try:
            # Read CSV with error handling
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(uploaded_file, encoding='latin-1')
                    st.warning("⚠️ File encoding detected as Latin-1. Please ensure special characters display correctly.")
                except:
                    df = pd.read_csv(uploaded_file, encoding='cp1252')
                    st.warning("⚠️ File encoding detected as Windows-1252. Please ensure special characters display correctly.")
            
            st.success(f"✅ File uploaded: {len(df)} rows, {len(df.columns)} columns")
            
            # Data quality analysis
            with st.expander("📊 Data Quality Analysis"):
                analysis = analyze_csv_quality(df)
                
                col_q1, col_q2, col_q3 = st.columns(3)
                
                with col_q1:
                    st.metric("Total Rows", f"{analysis['total_rows']:,}")
                
                with col_q2:
                    st.metric("Total Columns", analysis['total_columns'])
                
                with col_q3:
                    high_missing = sum(1 for v in analysis['missing_data'].values() if v['percentage'] > 25)
                    st.metric("Columns >25% Missing", high_missing)
                
                if analysis['potential_issues']:
                    st.warning("⚠️ **Potential Issues Found:**")
                    for issue in analysis['potential_issues']:
                        st.text(f"• {issue}")
            
            # Show preview
            st.subheader("📋 Data Preview")
            st.dataframe(df.head(10), use_container_width=True)
            
            # AI Field mapping
            st.subheader("🤖 Smart Field Mapping")
            
            csv_columns = df.columns.tolist()
            suggested_mappings = suggest_field_mapping(csv_columns)
            
            st.info("💡 Our AI has suggested field mappings below. Review and adjust as needed.")
            
            # Core field mappings with suggestions
            st.markdown("**📞 Core Fields (Required)**")
            col_map1, col_map2 = st.columns(2)
            
            with col_map1:
                # Find suggested phone column
                phone_suggestion = ""
                for col, mapping in suggested_mappings.items():
                    if mapping == "phone_number":
                        phone_suggestion = col
                        break
                
                phone_col = st.selectbox(
                    "Phone Number Column *",
                    [""] + csv_columns,
                    index=csv_columns.index(phone_suggestion) + 1 if phone_suggestion else 0,
                    help="Required field - must contain 10-digit phone numbers"
                )
                
                # Priority mapping
                priority_suggestion = ""
                for col, mapping in suggested_mappings.items():
                    if mapping == "priority":
                        priority_suggestion = col
                        break
                
                priority_col = st.selectbox(
                    "Priority Column",
                    [""] + csv_columns,
                    index=csv_columns.index(priority_suggestion) + 1 if priority_suggestion else 0,
                    help="Optional - numeric priority 1-10"
                )
            
            with col_map2:
                # Student name mapping
                student_name_suggestion = ""
                for col, mapping in suggested_mappings.items():
                    if mapping == "student_name":
                        student_name_suggestion = col
                        break
                
                student_name_col = st.selectbox(
                    "Student Name Column",
                    [""] + csv_columns,
                    index=csv_columns.index(student_name_suggestion) + 1 if student_name_suggestion else 0
                )
                
                # Scholarship type mapping (required)
                scholarship_type_suggestion = ""
                for col, mapping in suggested_mappings.items():
                    if mapping == "scholarship_type":
                        scholarship_type_suggestion = col
                        break
                
                scholarship_type_col = st.selectbox(
                    "Scholarship Type Column *",
                    [""] + csv_columns,
                    index=csv_columns.index(scholarship_type_suggestion) + 1 if scholarship_type_suggestion else 0,
                    help="Required field - must be one of: Full Scholarship, Partial Scholarship, Merit Based, Need Based"
                )
            
            # Additional field mappings with AI suggestions
            st.markdown("**📚 Additional Fields (Optional)**")
            
            # Parent name mapping as part of additional fields  
            parent_name_suggestion = ""
            for col, mapping in suggested_mappings.items():
                if mapping == "parent_name":
                    parent_name_suggestion = col
                    break
            
            parent_name_col = st.selectbox(
                "Parent Name Column",
                [""] + csv_columns,
                index=csv_columns.index(parent_name_suggestion) + 1 if parent_name_suggestion else 0
            )
            
            additional_mappings = {}
            excluded_cols = {phone_col, student_name_col, parent_name_col, priority_col, scholarship_type_col} - {""}
            
            remaining_cols = [col for col in csv_columns if col not in excluded_cols]
            
            if remaining_cols:
                st.markdown("*Review the suggested mappings below. You can modify the field names or leave blank to skip.*")
                
                cols_per_row = 2
                for i in range(0, len(remaining_cols), cols_per_row):
                    cols = st.columns(cols_per_row)
                    
                    for j, col in enumerate(remaining_cols[i:i+cols_per_row]):
                        with cols[j]:
                            suggested_name = suggested_mappings.get(col, col.lower().replace(" ", "_"))
                            field_name = st.text_input(
                                f"Map '{col}' to:",
                                value=suggested_name,
                                key=f"map_{col}",
                                help=f"Field name for '{col}' column"
                            )
                            if field_name.strip():
                                additional_mappings[col] = field_name.strip()
            
            # Validation preview
            if phone_col:
                st.subheader("✅ Validation Preview")
                
                # Sample validation on first few rows
                sample_size = min(5, len(df))
                validation_results = []
                
                for idx in range(sample_size):
                    row = df.iloc[idx]
                    
                    # Build sample student data
                    sample_data = {
                        "phone_number": clean_phone_number(str(row[phone_col])) if pd.notna(row[phone_col]) else "",
                        "priority": int(row[priority_col]) if priority_col and pd.notna(row[priority_col]) else 1,
                        "student_data": {}
                    }
                    
                    # Add scholarship_type to sample data
                    if scholarship_type_col and pd.notna(row[scholarship_type_col]):
                        sample_data["student_data"]["scholarship_type"] = str(row[scholarship_type_col]).strip()
                    
                    # Validate
                    errors = validate_student_data(sample_data)
                    validation_results.append({
                        "Row": idx + 1,
                        "Phone": sample_data["phone_number"],
                        "Scholarship Type": sample_data["student_data"].get("scholarship_type", "Missing"),
                        "Valid": "✅" if not errors else "❌",
                        "Issues": "; ".join(errors) if errors else "None"
                    })
                
                validation_df = pd.DataFrame(validation_results)
                st.dataframe(validation_df, use_container_width=True)
                
                # Show validation summary
                valid_count = len([r for r in validation_results if not r["Issues"] or r["Issues"] == "None"])
                error_count = sample_size - valid_count
                
                col_val1, col_val2 = st.columns(2)
                
                with col_val1:
                    st.metric("Valid Rows (Sample)", f"{valid_count}/{sample_size}")
                
                with col_val2:
                    if error_count > 0:
                        st.metric("Rows with Issues", error_count, delta=f"{(error_count/sample_size)*100:.1f}%")
                    else:
                        st.metric("Rows with Issues", "0 🎉")
            
            # Upload button
            upload_col1, upload_col2 = st.columns([3, 1])
            
            with upload_col1:
                if st.button("🚀 Process Upload", type="primary", disabled=not phone_col or not scholarship_type_col):
                    process_csv_upload(df, phone_col, student_name_col, parent_name_col, priority_col, scholarship_type_col, additional_mappings, api_client)
            
            with upload_col2:
                if st.button("❌ Cancel"):
                    st.rerun()
        
        except Exception as e:
            st.error(f"❌ Error reading CSV file: {str(e)}")
            st.info("💡 Try saving your file as UTF-8 CSV or check for formatting issues.")

def process_csv_upload(df: pd.DataFrame, phone_col: str, student_name_col: str, parent_name_col: str, priority_col: str, scholarship_type_col: str, additional_mappings: dict, api_client):
    """Process the CSV upload with validation and progress tracking"""
    
    if not phone_col:
        st.error("❌ Phone number column is required!")
        return
    
    if not scholarship_type_col:
        st.error("❌ Scholarship Type column is required!")
        return
    
    try:
        with st.spinner("📤 Processing upload..."):
            # Process each row
            success_count = 0
            error_count = 0
            errors = []
            duplicates = 0
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, row in df.iterrows():
                try:
                    status_text.text(f"Processing row {idx + 1}/{len(df)}: {row[phone_col] if pd.notna(row[phone_col]) else 'Unknown'}")
                    
                    # Build student data
                    phone_clean = clean_phone_number(str(row[phone_col])) if pd.notna(row[phone_col]) else ""
                    
                    if not phone_clean:
                        errors.append(f"Row {idx + 1}: Missing or invalid phone number")
                        error_count += 1
                        continue
                    
                    student_data = {
                        "phone_number": phone_clean,
                        "priority": int(row[priority_col]) if priority_col and pd.notna(row[priority_col]) else 1,
                        "student_data": {}
                    }
                    
                    # Add core fields
                    if student_name_col and pd.notna(row[student_name_col]):
                        student_data["student_data"]["student_name"] = str(row[student_name_col]).strip()
                    
                    if parent_name_col and pd.notna(row[parent_name_col]):
                        student_data["student_data"]["parent_name"] = str(row[parent_name_col]).strip()
                    
                    # Add required scholarship_type field
                    if scholarship_type_col and pd.notna(row[scholarship_type_col]):
                        student_data["student_data"]["scholarship_type"] = str(row[scholarship_type_col]).strip()
                    
                    # Add additional fields
                    for csv_col, field_name in additional_mappings.items():
                        if pd.notna(row[csv_col]):
                            value = str(row[csv_col]).strip()
                            if value:  # Only add non-empty values
                                student_data["student_data"][field_name] = value
                    
                    # Validate data
                    validation_errors = validate_student_data(student_data)
                    if validation_errors:
                        errors.append(f"Row {idx + 1}: {'; '.join(validation_errors)}")
                        error_count += 1
                        continue
                    
                    # Create student
                    api_client.create_student(student_data)
                    success_count += 1
                    
                except Exception as e:
                    error_str = str(e)
                    if "duplicate" in error_str.lower() or "already exists" in error_str.lower():
                        duplicates += 1
                        errors.append(f"Row {idx + 1}: Phone number already exists")
                    else:
                        error_count += 1
                        errors.append(f"Row {idx + 1}: {error_str}")
                
                # Update progress
                progress = (idx + 1) / len(df)
                progress_bar.progress(progress)
            
            # Clear status
            status_text.empty()
            
            # Show results
            st.balloons()
            
            col_result1, col_result2, col_result3 = st.columns(3)
            
            with col_result1:
                st.metric("✅ Successfully Added", success_count)
            
            with col_result2:
                st.metric("❌ Errors", error_count)
            
            with col_result3:
                st.metric("🔄 Duplicates Skipped", duplicates)
            
            if success_count > 0:
                st.success(f"🎉 Upload completed! {success_count} students added successfully.")
            
            if error_count > 0 or duplicates > 0:
                with st.expander(f"📋 View Issues ({error_count + duplicates} total)"):
                    for error in errors[:50]:  # Show first 50 errors
                        st.text(f"• {error}")
                    
                    if len(errors) > 50:
                        st.text(f"... and {len(errors) - 50} more issues")
            
            # Refresh students list
            if success_count > 0:
                st.session_state.refresh_students = True
    
    except Exception as e:
        st.error(f"❌ Upload failed: {str(e)}")
        st.info("💡 Please check your data format and try again.")

def show_student_analytics(api_client):
    """Display student analytics and insights"""
    
    st.subheader("📊 Student Analytics")
    
    try:
        # Get analytics data
        with st.spinner("📊 Loading analytics..."):
            analytics = api_client.get_student_analytics()
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total = analytics.get("total_students", 0)
            st.metric("Total Students", f"{total:,}")
        
        with col2:
            by_status = analytics.get("students_by_status", {})
            pending = by_status.get("pending", 0)
            st.metric("Pending Calls", f"{pending:,}")
        
        with col3:
            completed = by_status.get("completed", 0)
            st.metric("Completed", f"{completed:,}")
        
        with col4:
            if total > 0:
                completion_rate = (completed / total) * 100
                st.metric("Completion Rate", f"{completion_rate:.1f}%")
            else:
                st.metric("Completion Rate", "0%")
        
        # Status distribution chart
        if by_status:
            st.subheader("📊 Status Distribution")
            
            import plotly.express as px
            
            status_df = pd.DataFrame([
                {"Status": k.replace("_", " ").title(), "Count": v}
                for k, v in by_status.items() if v > 0
            ])
            
            if not status_df.empty:
                fig = px.pie(status_df, values="Count", names="Status", title="Student Status Distribution")
                st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error loading analytics: {str(e)}")
        
        # Show placeholder analytics
        st.info("📊 Showing sample analytics data")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Students", "1,234")
        
        with col2:
            st.metric("Pending Calls", "567")
        
        with col3:
            st.metric("Completed", "667")
        
        with col4:
            st.metric("Completion Rate", "54.1%")
