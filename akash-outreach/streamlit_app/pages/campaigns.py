"""
Campaign Management Page
Step-by-step campaign creation and management interface
"""

import streamlit as st
from datetime import datetime, timedelta

def show_campaigns():
    """Main campaigns page with creation and management"""
    
    # Check API client
    if not st.session_state.get("api_client"):
        st.error("❌ No API connection. Please refresh the page.")
        return
    
    api_client = st.session_state.api_client
    
    # Check if we should show campaign details
    if st.session_state.get("show_campaign_details"):
        show_campaign_details(api_client, st.session_state.show_campaign_details)
        return
    
    # Call the main campaigns page function
    campaigns_page()


def activate_campaign_action(api_client, campaign_id):
    """Activate a campaign and start calling"""
    try:
        # Get campaign details first
        campaign_details = api_client.get_campaign(campaign_id)
        
        # Check if current time is within call window
        from datetime import datetime, time
        current_time = datetime.now().time()
        
        if campaign_details:
            call_from_str = campaign_details.get('call_from_time', '09:00')
            call_to_str = campaign_details.get('call_to_time', '23:59')
            
            call_from = datetime.strptime(call_from_str, '%H:%M').time()
            call_to = datetime.strptime(call_to_str, '%H:%M').time()
            
            if current_time < call_from or current_time > call_to:
                st.warning(f"⚠️ Current time ({current_time.strftime('%H:%M')}) is outside the campaign call window ({call_from_str} - {call_to_str}). Calls may not be initiated immediately.")
        
        with st.spinner("� Activating campaign..."):
            result = api_client.activate_campaign(campaign_id)
        
        # The API returns a message directly on success, not a success field
        if result and result.get('message'):
            st.session_state.campaign_success_message = f"✅ {result.get('message')}"
            st.rerun()
        else:
            st.error("❌ Failed to activate campaign: No response from server")
    
    except Exception as e:
        st.error(f"❌ Error activating campaign: {str(e)}")


def campaigns_page():
    """Campaign Management"""
    
    st.title("📞 Campaign Management")
    
    # Check authentication
    if not st.session_state.get("authenticated"):
        st.warning("⚠️ Please login first")
        return
    
    api_client = st.session_state.api_client
    
    # Check if we should show campaign details
    if st.session_state.get("show_campaign_details"):
        show_campaign_details(api_client, st.session_state.show_campaign_details)
        return
    
    # Handle session state messages
    if "campaign_success_message" in st.session_state:
        st.success(st.session_state.campaign_success_message)
        del st.session_state.campaign_success_message
    
    if "campaign_error_message" in st.session_state:
        st.error(st.session_state.campaign_error_message)
        del st.session_state.campaign_error_message
    
    # Main tabs
    tab1, tab2 = st.tabs(["📝 Create Campaign", "📊 Manage Campaigns"])
    
    with tab1:
        show_campaign_creation(api_client)
    
    with tab2:
        show_campaign_management(api_client)

def show_campaign_management(api_client):
    """Campaign management and list view"""
    
    st.subheader("📋 Active Campaigns")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Status Filter",
            ["All", "Draft", "Active", "Paused", "Completed", "Cancelled"],
            key="campaign_status_filter_unique"
        )
    
    with col2:
        campaign_type = st.selectbox(
            "Campaign Type",
            ["All", "Scholarship", "General", "Follow-up"],
            key="campaign_type_filter_unique"
        )
    
    with col3:
        sort_by = st.selectbox(
            "Sort by",
            ["Created Date", "Status", "Name", "Progress"],
            key="campaign_sort_unique"
        )
    
    # Load campaigns
    try:
        with st.spinner("🔄 Loading campaigns..."):
            status = None if status_filter == "All" else status_filter.lower()
            campaigns = api_client.get_campaigns(status=status)
        
        if not campaigns:
            st.info("📝 No campaigns found")
            
            # Quick start section
            st.markdown("### 🚀 Get Started")
            col_start1, col_start2 = st.columns(2)
            
            with col_start1:
                if st.button("🎯 Create Your First Campaign", key="first_campaign_unique"):
                    st.session_state.active_tab = "create_campaign"
                    st.rerun()
            
            with col_start2:
                if st.button("📋 Use Template", key="use_template_unique"):
                    st.session_state.active_tab = "templates"
                    st.rerun()
        else:
            # Display campaigns
            st.success(f"📊 Found {len(campaigns)} campaign(s)")
            
            for campaign in campaigns:
                with st.expander(f"🎯 {campaign.get('name', 'Unnamed Campaign')}", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("**📋 Campaign Details**")
                        st.write(f"**Status:** {campaign.get('status', 'unknown').title()}")
                        st.write(f"**Created:** {campaign.get('created_at', 'N/A')}")
                        if campaign.get('description'):
                            st.write(f"**Description:** {campaign.get('description')}")
                    
                    with col2:
                        st.markdown("**👥 Target Info**")
                        st.write(f"**Students:** {campaign.get('total_students', 0)}")
                        st.write(f"**Contexts:** {len(campaign.get('context_note_ids', []))}")
                        if campaign.get('call_from_time') and campaign.get('call_to_time'):
                            st.write(f"**Call Window:** {campaign.get('call_from_time')} - {campaign.get('call_to_time')}")
                    
                    with col3:
                        st.markdown("**⚡ Actions**")
                        
                        col_btn1, col_btn2 = st.columns(2)
                        
                        with col_btn1:
                            if campaign.get('status') == 'draft':
                                if st.button("🚀 Activate", key=f"activate_{campaign.get('id')}"):
                                    activate_campaign_action(api_client, campaign.get('id'))
                            elif campaign.get('status') == 'active':
                                if st.button("⏸️ Pause", key=f"pause_{campaign.get('id')}"):
                                    pause_campaign_action(api_client, campaign.get('id'))
                            elif campaign.get('status') == 'paused':
                                if st.button("▶️ Resume", key=f"resume_{campaign.get('id')}"):
                                    resume_campaign_action(api_client, campaign.get('id'))
                        
                        with col_btn2:
                            if st.button("📊 Details", key=f"details_{campaign.get('id')}"):
                                st.session_state.show_campaign_details = campaign.get('id')
                                st.rerun()
                    
                    # Show personalized contexts if available
                    if campaign.get('personalized_contexts'):
                        st.markdown("**🤖 AI-Generated Personalized Contexts**")
                        contexts = campaign.get('personalized_contexts', {})
                        
                        if contexts:
                            for student_id, context_data in contexts.items():
                                student_name = context_data.get('student_name', f'Student {student_id}')
                                context_text = context_data.get('context', 'No context generated')
                                
                                with st.expander(f"👤 {student_name}", expanded=False):
                                    # Display context with edit capability
                                    edited_context = st.text_area(
                                        f"Personalized context for {student_name}:",
                                        value=context_text,
                                        height=100,
                                        key=f"context_edit_{campaign.get('id')}_{student_id}"
                                    )
                        else:
                            st.info("🔄 Personalized contexts are being generated...")
                    else:
                        st.info("⚡ AI context generation will create personalized messages for each student when this campaign is created.")
                    
                    # Progress bar for active campaigns
                    if campaign.get('status') == 'active':
                        progress = campaign.get('progress', 0)
                        st.progress(progress / 100 if progress > 1 else progress)
                        st.caption(f"Progress: {progress:.1f}%")
    
    except Exception as e:
        st.error(f"❌ Error loading campaigns: {str(e)}")

def show_campaign_creation(api_client):
    """Step-by-step campaign creation interface"""
    
    st.subheader("📝 Create New Campaign")
    st.markdown("Follow these steps to create a personalized campaign:")
    
    # Initialize session state for campaign creation
    if "campaign_step" not in st.session_state:
        st.session_state.campaign_step = 1
    
    if "selected_contexts" not in st.session_state:
        st.session_state.selected_contexts = []
    
    if "selected_students" not in st.session_state:
        st.session_state.selected_students = []
    
    # Progress indicator
    progress_steps = ["📋 Context Cards", "👥 Students", "⏰ Schedule", "🚀 Review & Create"]
    current_step = st.session_state.campaign_step
    
    # Create progress bar
    progress_cols = st.columns(4)
    for i, step in enumerate(progress_steps, 1):
        with progress_cols[i-1]:
            if i == current_step:
                st.markdown(f"**🔵 {step}**")
            elif i < current_step:
                st.markdown(f"✅ {step}")
            else:
                st.markdown(f"⚪ {step}")
    
    st.markdown("---")
    
    # Step content
    if current_step == 1:
        show_context_selection_step(api_client)
    elif current_step == 2:
        show_student_selection_step(api_client)
    elif current_step == 3:
        show_schedule_step(api_client)
    elif current_step == 4:
        show_review_step(api_client)

def show_context_selection_step(api_client):
    """Step 1: Context card selection"""
    
    st.markdown("### 📋 Step 1: Select AI Context Cards")
    st.info("Choose the context cards that will be used to create personalized messages for each student.")
    
    try:
        with st.spinner("🔄 Loading context cards..."):
            context_notes = api_client.get_context_notes(include_inactive=False)
        
        if not context_notes:
            st.warning("⚠️ No context cards found. Please create some context cards first.")
            if st.button("➕ Create Context Cards"):
                st.switch_page("pages/context.py")
            return
        
        st.markdown(f"**Available Context Cards ({len(context_notes)}):**")
        
        # Group by category
        categories = {}
        for note in context_notes:
            category = note.get('category', 'General')
            if category not in categories:
                categories[category] = []
            categories[category].append(note)
        
        selected_count = 0
        for category, notes in categories.items():
            with st.expander(f"📁 {category} ({len(notes)} cards)", expanded=True):
                for note in notes:
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        is_selected = st.checkbox(
                            f"Select {note['title']}", 
                            key=f"context_{note['id']}_unique",
                            label_visibility="collapsed"
                        )
                        if is_selected:
                            if note['id'] not in st.session_state.selected_contexts:
                                st.session_state.selected_contexts.append(note['id'])
                            selected_count += 1
                        else:
                            if note['id'] in st.session_state.selected_contexts:
                                st.session_state.selected_contexts.remove(note['id'])
                    
                    with col2:
                        st.markdown(f"**{note['title']}**")
                        st.markdown(f"*{note['content'][:100]}...*" if len(note['content']) > 100 else note['content'])
        
        # Navigation
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.info(f"✅ Selected: {len(st.session_state.selected_contexts)} context cards")
        
        with col3:
            if st.button("Next: Select Students ➡️", disabled=len(st.session_state.selected_contexts) == 0):
                st.session_state.campaign_step = 2
                st.rerun()
        
        if len(st.session_state.selected_contexts) == 0:
            st.warning("⚠️ Please select at least one context card to continue.")
    
    except Exception as e:
        st.error(f"❌ Error loading context cards: {str(e)}")

def show_student_selection_step(api_client):
    """Step 2: Student selection"""
    
    st.markdown("### 👥 Step 2: Select Target Students")
    st.info("Choose the students who will receive the campaign calls.")
    
    try:
        with st.spinner("🔄 Loading students..."):
            students_response = api_client.get_students(limit=1000)
            students = students_response.get("students", [])
        
        if not students:
            st.warning("⚠️ No students found. Please add some students first.")
            if st.button("➕ Add Students"):
                st.switch_page("pages/students.py")
            return
        
        # Search and filter
        col1, col2 = st.columns([2, 1])
        
        with col1:
            search_query = st.text_input("🔍 Search students...", placeholder="Search by name or phone")
        
        with col2:
            select_all = st.checkbox("Select All Visible", key="select_all_students")
        
        # Filter students based on search
        filtered_students = students
        if search_query:
            filtered_students = [
                s for s in students 
                if search_query.lower() in s.get('student_name', '').lower() 
                or search_query.lower() in s.get('phone_number', '').lower()
            ]
        
        st.markdown(f"**Available Students ({len(filtered_students)}):**")
        
        # Student selection
        for student in filtered_students:
            col1, col2, col3 = st.columns([1, 3, 2])
            
            with col1:
                student_name = student.get('student_name', f"Student {student['id']}")
                is_selected = st.checkbox(
                    f"Select {student_name}",
                    key=f"student_{student['id']}_unique",
                    label_visibility="collapsed"
                )
                if is_selected:
                    if student['id'] not in st.session_state.selected_students:
                        st.session_state.selected_students.append(student['id'])
                else:
                    if student['id'] in st.session_state.selected_students:
                        st.session_state.selected_students.remove(student['id'])
            
            with col2:
                st.markdown(f"**{student.get('student_name', 'N/A')}**")
                st.markdown(f"📞 {student.get('phone_number', 'N/A')}")
            
            with col3:
                st.markdown(f"Status: {student.get('call_status', 'pending')}")
        
        # Navigation
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            if st.button("⬅️ Back"):
                st.session_state.campaign_step = 1
                st.rerun()
        
        with col2:
            st.info(f"✅ Selected: {len(st.session_state.selected_students)}")
        
        with col4:
            if st.button("Next: Schedule ➡️", disabled=len(st.session_state.selected_students) == 0):
                st.session_state.campaign_step = 3
                st.rerun()
        
        if len(st.session_state.selected_students) == 0:
            st.warning("⚠️ Please select at least one student to continue.")
    
    except Exception as e:
        st.error(f"❌ Error loading students: {str(e)}")

def show_schedule_step(api_client):
    """Step 3: Schedule configuration"""
    
    st.markdown("### ⏰ Step 3: Set Call Schedule")
    st.info("Configure when the campaign calls should be made.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📅 Campaign Dates**")
        start_date = st.date_input(
            "Start Date",
            value=datetime.now().date(),
            min_value=datetime.now().date()
        )
        
        end_date = st.date_input(
            "End Date",
            value=(datetime.now() + timedelta(days=7)).date(),
            min_value=start_date
        )
    
    with col2:
        st.markdown("**🕐 Call Time Window**")
        from_time = st.time_input(
            "Call From",
            value=datetime.strptime("09:00", "%H:%M").time()
        )
        
        to_time = st.time_input(
            "Call To",
            value=datetime.strptime("23:59", "%H:%M").time()
        )
    
    # Validate time window
    if from_time >= to_time:
        st.error("❌ Call start time must be before call end time")
        return
    
    # Store schedule in session state
    st.session_state.campaign_schedule = {
        "start_date": start_date,
        "end_date": end_date,
        "from_time": from_time,
        "to_time": to_time
    }
    
    # Navigation
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        if st.button("⬅️ Back"):
            st.session_state.campaign_step = 2
            st.rerun()
    
    with col4:
        if st.button("Next: Review ➡️"):
            st.session_state.campaign_step = 4
            st.rerun()

def show_review_step(api_client):
    """Step 4: Review and create campaign"""
    
    st.markdown("### 🚀 Step 4: Review & Create Campaign")
    st.info("Review your campaign settings and create the campaign.")
    
    # Campaign basic info
    st.markdown("**📝 Campaign Details**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        campaign_name = st.text_input(
            "Campaign Name *",
            placeholder="Enter campaign name...",
            key="campaign_name_input"
        )
    
    with col2:
        campaign_description = st.text_area(
            "Description",
            placeholder="Optional description...",
            key="campaign_description_input"
        )
    
    # Review selections
    st.markdown("**📋 Review Selections**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Context Cards", len(st.session_state.selected_contexts))
    
    with col2:
        st.metric("Target Students", len(st.session_state.selected_students))
    
    with col3:
        schedule = st.session_state.get("campaign_schedule", {})
        if schedule:
            duration = (schedule["end_date"] - schedule["start_date"]).days + 1
            st.metric("Campaign Duration", f"{duration} days")
    
    # Navigation
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        if st.button("⬅️ Back"):
            st.session_state.campaign_step = 3
            st.rerun()
    
    with col4:
        if st.button("🚀 Create Campaign", disabled=not campaign_name):
            create_campaign(api_client, campaign_name, campaign_description)
    
    if not campaign_name:
        st.warning("⚠️ Please enter a campaign name to continue.")

def create_campaign(api_client, name, description):
    """Create the campaign with all selected parameters"""
    
    try:
        schedule = st.session_state.get("campaign_schedule", {})
        
        campaign_data = {
            "name": name,
            "description": description or "",
            "context_note_ids": st.session_state.selected_contexts,
            "student_ids": st.session_state.selected_students,
            "call_from_time": schedule["from_time"].strftime("%H:%M"),
            "call_to_time": schedule["to_time"].strftime("%H:%M"),
            "campaign_start_date": schedule["start_date"].isoformat(),
            "campaign_end_date": schedule["end_date"].isoformat()
        }
        
        with st.spinner("🚀 Creating campaign and generating personalized contexts..."):
            campaign = api_client.create_campaign(campaign_data)
        
        # Clear session state
        for key in ["campaign_step", "selected_contexts", "selected_students", "campaign_schedule"]:
            if key in st.session_state:
                del st.session_state[key]
        
        st.session_state.campaign_success_message = f"✅ Campaign '{name}' created successfully! 🎉"
        st.rerun()
    
    except Exception as e:
        st.error(f"❌ Error creating campaign: {str(e)}")


def show_campaign_details(api_client, campaign_id):
    """Detailed view of a specific campaign with editable personalized contexts"""
    
    # Back button
    col_back, col_title = st.columns([1, 4])
    with col_back:
        if st.button("← Back to Campaigns"):
            del st.session_state.show_campaign_details
            st.rerun()
    
    with col_title:
        st.title("📊 Campaign Details")
    
    try:
        # Load campaign details
        with st.spinner("🔄 Loading campaign details..."):
            campaign = api_client.get_campaign(campaign_id)
        
        if not campaign:
            st.error("❌ Campaign not found")
            return
        
        # Campaign header
        st.markdown(f"## 🎯 {campaign.get('name', 'Unnamed Campaign')}")
        
        if campaign.get('description'):
            st.markdown(f"**Description:** {campaign.get('description')}")
        
        # Campaign metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Status", campaign.get('status', 'Unknown').title())
        
        with col2:
            st.metric("Total Students", campaign.get('total_students', 0))
        
        with col3:
            st.metric("Completion Rate", f"{campaign.get('completion_rate', 0):.1f}%")
        
        with col4:
            st.metric("Success Rate", f"{campaign.get('success_rate', 0):.1f}%")
        
        st.markdown("---")
        
        # Campaign settings
        st.subheader("⚙️ Campaign Settings")
        
        col_settings1, col_settings2 = st.columns(2)
        
        with col_settings1:
            st.write(f"**Call Window:** {campaign.get('call_from_time', 'N/A')} - {campaign.get('call_to_time', 'N/A')}")
            st.write(f"**Created By:** {campaign.get('created_by', 'Unknown')}")
            st.write(f"**Created:** {campaign.get('created_at', 'N/A')}")
        
        with col_settings2:
            st.write(f"**Context Cards:** {len(campaign.get('context_note_ids', []))}")
            st.write(f"**Students Called:** {campaign.get('students_called', 0)}")
            st.write(f"**Last Updated:** {campaign.get('updated_at', 'N/A')}")
        
        # Personalized Contexts Section
        st.markdown("---")
        st.subheader("🤖 AI-Generated Personalized Contexts")
        
        personalized_contexts = campaign.get('personalized_contexts')
        
        if personalized_contexts:
            st.success(f"✅ Found personalized contexts for {len(personalized_contexts)} students")
            
            # Filter and search
            col_search, col_filter = st.columns(2)
            
            with col_search:
                search_term = st.text_input("🔍 Search contexts:", placeholder="Search by student name or context content...")
            
            with col_filter:
                context_filter = st.selectbox("Filter by:", ["All Students", "Long Contexts", "Short Contexts"])
            
            # Display each student's context
            for student_id, context_data in personalized_contexts.items():
                student_name = context_data.get('student_name', f'Student {student_id}')
                context_text = context_data.get('context', 'No context generated')
                phone_number = context_data.get('phone_number', 'N/A')
                
                # Apply search filter
                if search_term and search_term.lower() not in student_name.lower() and search_term.lower() not in context_text.lower():
                    continue
                
                # Apply length filter
                if context_filter == "Long Contexts" and len(context_text) < 200:
                    continue
                elif context_filter == "Short Contexts" and len(context_text) >= 200:
                    continue
                
                with st.expander(f"👤 {student_name} ({phone_number})", expanded=False):
                    # Context display and editing
                    st.markdown("**Generated Context:**")
                    
                    # Edit mode toggle
                    edit_mode = st.checkbox("✏️ Edit mode", key=f"edit_mode_{campaign_id}_{student_id}")
                    
                    if edit_mode:
                        # Editable text area
                        edited_context = st.text_area(
                            f"Edit context for {student_name}:",
                            value=context_text,
                            height=150,
                            key=f"context_edit_{campaign_id}_{student_id}"
                        )
                        
                        # Auto-save when content changes
                        if edited_context != context_text:
                            try:
                                # Call API to update context
                                api_client.update_student_context(campaign_id, student_id, edited_context)
                                st.success("✅ Context updated successfully!")
                                
                            except Exception as e:
                                st.error(f"❌ Failed to save context: {str(e)}")
                    else:
                        # Read-only display with nice formatting
                        st.markdown(f"```\n{context_text}\n```")
                        
                        # Context metadata
                        col_meta1, col_meta2 = st.columns(2)
                        with col_meta1:
                            st.caption(f"📏 Length: {len(context_text)} characters")
                        with col_meta2:
                            st.caption(f"📊 Words: {len(context_text.split())} words")
        else:
            st.warning("⚠️ No personalized contexts found for this campaign.")
            
            if st.button("🤖 Generate Contexts Now"):
                generate_contexts_action(api_client, campaign_id)
    
    except Exception as e:
        st.error(f"❌ Error loading campaign details: {str(e)}")


def activate_campaign_action(api_client, campaign_id):
    """Activate a campaign and start calling"""
    try:
        with st.spinner("🚀 Activating campaign..."):
            result = api_client.activate_campaign(campaign_id)
        
        # The API returns a message directly on success, not a success field
        if result and result.get('message'):
            st.session_state.campaign_success_message = f"✅ {result.get('message')}"
            st.rerun()
        else:
            st.error(f"❌ Failed to activate campaign: No response from server")
    
    except Exception as e:
        st.error(f"❌ Error activating campaign: {str(e)}")


def pause_campaign_action(api_client, campaign_id):
    """Pause an active campaign"""
    try:
        with st.spinner("⏸️ Pausing campaign..."):
            # Using generic update endpoint since pause might not be implemented yet
            result = api_client._make_request("POST", f"/campaigns/{campaign_id}/pause")
        
        if result.get('success'):
            st.session_state.campaign_success_message = "⏸️ Campaign paused successfully!"
            st.rerun()
        else:
            st.error(f"❌ Failed to pause campaign: {result.get('message', 'Unknown error')}")
    
    except Exception as e:
        st.error(f"❌ Error pausing campaign: {str(e)}")


def resume_campaign_action(api_client, campaign_id):
    """Resume a paused campaign"""
    try:
        with st.spinner("▶️ Resuming campaign..."):
            # Using generic update endpoint since resume might not be implemented yet
            result = api_client._make_request("POST", f"/campaigns/{campaign_id}/resume")
        
        if result.get('success'):
            st.session_state.campaign_success_message = "▶️ Campaign resumed successfully!"
            st.rerun()
        else:
            st.error(f"❌ Failed to resume campaign: {result.get('message', 'Unknown error')}")
    
    except Exception as e:
        st.error(f"❌ Error resuming campaign: {str(e)}")


def generate_contexts_action(api_client, campaign_id):
    """Generate personalized contexts for campaign"""
    try:
        with st.spinner("🤖 Generating personalized contexts..."):
            result = api_client.regenerate_contexts(campaign_id)
        
        if result.get('success'):
            st.session_state.campaign_success_message = "🤖 Personalized contexts generated successfully!"
            st.rerun()
        else:
            st.error(f"❌ Failed to generate contexts: {result.get('message', 'Unknown error')}")
    
    except Exception as e:
        st.error(f"❌ Error generating contexts: {str(e)}")


if __name__ == "__main__":
    show_campaigns()