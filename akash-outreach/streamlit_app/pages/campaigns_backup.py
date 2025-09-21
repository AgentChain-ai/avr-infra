"""
Campaign Management Page
Step-by-step campaign creation and management interface
"""

import streamlit as st
import pandas as pd
from datetime import datetime, time, date, timedelta
from typing import List, Dict, Any
import json

def show_campaigns():
    """Main campaigns page with creation and management"""
    
    # Check API client
    if not st.session_state.get("api_client"):
        st.error("❌ No API connection. Please refresh the page.")
        return
    
    api_client = st.session_state.api_client
    
    st.title("📢 Campaign Management")
    
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
    """Render campaigns list with management options"""
    
    st.subheader("📋 Active Campaigns")
    
    try:
        # Get campaigns data
        with st.spinner("📊 Loading campaigns..."):
            campaigns = api_client.get_campaigns()
        
        if campaigns:
            # Campaign stats
            render_campaign_stats(campaigns)
            
            # Filters
            col_filter1, col_filter2, col_filter3 = st.columns(3)
            
            with col_filter1:
                status_filter = st.selectbox(
                    "📊 Status Filter",
                    ["All", "Active", "Paused", "Completed", "Draft"],
                    key="campaign_status_filter"
                )
            
            with col_filter2:
                type_filter = st.selectbox(
                    "🎯 Type Filter",
                    ["All", "Voice Call", "SMS", "Email", "Mixed"],
                    key="campaign_type_filter"
                )
            
            with col_filter3:
                sort_by = st.selectbox(
                    "📈 Sort By",
                    ["Created (Newest)", "Created (Oldest)", "Progress", "Success Rate", "Name"],
                    key="campaign_sort"
                )
            
            # Apply filters
            filtered_campaigns = apply_campaign_filters(campaigns, status_filter, type_filter)
            
            st.subheader(f"📋 Campaigns ({len(filtered_campaigns)})")
            
            # Display campaigns
            for campaign in filtered_campaigns:
                render_campaign_card(campaign, api_client)
        
        else:
            st.info("📝 No campaigns found")
            
            # Quick start section
            st.markdown("### 🚀 Get Started")
            col_start1, col_start2 = st.columns(2)
            
            with col_start1:
                if st.button("🎯 Create Your First Campaign", key="first_campaign"):
                    st.session_state.active_tab = "create_campaign"
                    st.rerun()
            
            with col_start2:
                if st.button("📋 Use Template", key="use_template"):
                    st.session_state.active_tab = "templates"
                    st.rerun()
    
    except Exception as e:
        st.error(f"❌ Error loading campaigns: {str(e)}")

def show_campaign_creation(api_client):
    """Step-by-step campaign creation interface"""
    
    st.subheader("📝 Create New Campaign")
    st.markdown("Follow the step-by-step process to create your personalized campaign")
    
    # Initialize session state for multi-step form
    if "campaign_step" not in st.session_state:
        st.session_state.campaign_step = 1
    if "campaign_data" not in st.session_state:
        st.session_state.campaign_data = {}
    
    # Progress bar
    progress_steps = ["📋 Context Cards", "👥 Students", "⏰ Schedule", "🤖 AI Generation"]
    progress = st.session_state.campaign_step / 4
    st.progress(progress)
    
    # Step indicator
    cols = st.columns(4)
    for i, step in enumerate(progress_steps, 1):
        with cols[i-1]:
            if i == st.session_state.campaign_step:
                st.markdown(f"**🔵 {step}**")
            elif i < st.session_state.campaign_step:
                st.markdown(f"✅ {step}")
            else:
                st.markdown(f"⚪ {step}")
    
    st.markdown("---")
    
    # Step-specific content
    if st.session_state.campaign_step == 1:
        show_context_card_selection(api_client)
    elif st.session_state.campaign_step == 2:
        show_student_selection(api_client)
    elif st.session_state.campaign_step == 3:
        show_time_scheduling(api_client)
    elif st.session_state.campaign_step == 4:
        show_ai_context_generation(api_client)

def show_context_card_selection(api_client):
    """Step 1: Context Card Selection"""
    
    st.markdown("### 📋 Step 1: Select Context Cards")
    st.info("Choose the context cards that will be used to generate personalized content for each student")
    
    try:
        # Get context notes
        with st.spinner("📝 Loading context cards..."):
            context_notes = api_client.get_context_notes()
        
        if context_notes:
            # Search and filter
            search_term = st.text_input("🔍 Search context cards...", placeholder="Search by title or content")
            
            # Filter context notes
            filtered_notes = [
                note for note in context_notes 
                if not search_term or search_term.lower() in note.get('title', '').lower() 
                or search_term.lower() in note.get('content', '').lower()
            ]
            
            # Multi-select with checkboxes
            st.markdown("**Select Context Cards:**")
            selected_context_ids = []
            
            # Display context cards in a nice format
            for note in filtered_notes:
                col1, col2 = st.columns([1, 10])
                with col1:
                    if st.checkbox("", key=f"context_{note['id']}"):
                        selected_context_ids.append(note['id'])
                with col2:
                    with st.expander(f"📝 {note.get('title', 'Untitled')}"):
                        st.write(f"**Content:** {note.get('content', 'No content')[:200]}...")
                        st.write(f"**Created:** {note.get('created_at', 'Unknown')}")
            
            # Save selection and navigation
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col2:
                if st.button("➡️ Next: Select Students", type="primary", disabled=len(selected_context_ids) == 0):
                    st.session_state.campaign_data['context_note_ids'] = selected_context_ids
                    st.session_state.campaign_step = 2
                    st.rerun()
            
            if len(selected_context_ids) == 0:
                st.warning("⚠️ Please select at least one context card to continue")
            else:
                st.success(f"✅ {len(selected_context_ids)} context cards selected")
        
        else:
            st.warning("📝 No context cards found. Please create some context cards first.")
            if st.button("➕ Create Context Card"):
                st.switch_page("pages/context_notes.py")
    
    except Exception as e:
        st.error(f"❌ Error loading context cards: {str(e)}")

def show_student_selection(api_client):
    """Step 2: Student Selection"""
    
    st.markdown("### 👥 Step 2: Select Students")
    st.info("Choose which students will receive personalized calls")
    
    try:
        # Get students
        with st.spinner("👥 Loading students..."):
            students = api_client.get_students()
        
        if students:
            # Search and filter
            col1, col2 = st.columns(2)
            with col1:
                search_term = st.text_input("🔍 Search students...", placeholder="Search by name or phone")
            with col2:
                priority_filter = st.selectbox("📊 Priority Filter", ["All", "High (8+)", "Medium (4-7)", "Low (1-3)"])
            
            # Filter students
            filtered_students = students
            if search_term:
                filtered_students = [
                    student for student in filtered_students
                    if search_term.lower() in student.get('name', '').lower()
                    or search_term.lower() in student.get('phone', '').lower()
                ]
            
            if priority_filter != "All":
                if priority_filter == "High (8+)":
                    filtered_students = [s for s in filtered_students if s.get('priority', 0) >= 8]
                elif priority_filter == "Medium (4-7)":
                    filtered_students = [s for s in filtered_students if 4 <= s.get('priority', 0) <= 7]
                elif priority_filter == "Low (1-3)":
                    filtered_students = [s for s in filtered_students if s.get('priority', 0) <= 3]
            
            # Bulk selection
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ Select All"):
                    for student in filtered_students:
                        st.session_state[f"student_{student['id']}"] = True
                    st.rerun()
            with col2:
                if st.button("❌ Deselect All"):
                    for student in filtered_students:
                        st.session_state[f"student_{student['id']}"] = False
                    st.rerun()
            
            # Student selection with details
            st.markdown("**Select Students:**")
            selected_student_ids = []
            
            for student in filtered_students:
                col1, col2 = st.columns([1, 10])
                with col1:
                    if st.checkbox("", key=f"student_{student['id']}"):
                        selected_student_ids.append(student['id'])
                with col2:
                    priority_color = "🔴" if student.get('priority', 0) >= 8 else "🟡" if student.get('priority', 0) >= 4 else "🟢"
                    st.write(f"{priority_color} **{student.get('name', 'Unknown')}** - {student.get('phone', 'No phone')} (Priority: {student.get('priority', 0)})")
            
            # Navigation
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("⬅️ Back"):
                    st.session_state.campaign_step = 1
                    st.rerun()
            
            with col3:
                if st.button("➡️ Next: Schedule", type="primary", disabled=len(selected_student_ids) == 0):
                    st.session_state.campaign_data['student_ids'] = selected_student_ids
                    st.session_state.campaign_step = 3
                    st.rerun()
            
            if len(selected_student_ids) == 0:
                st.warning("⚠️ Please select at least one student to continue")
            else:
                st.success(f"✅ {len(selected_student_ids)} students selected")
        
        else:
            st.warning("👥 No students found. Please add students first.")
            if st.button("➕ Add Students"):
                st.switch_page("pages/students.py")
    
    except Exception as e:
        st.error(f"❌ Error loading students: {str(e)}")

def show_time_scheduling(api_client):
    """Step 3: Time Scheduling"""
    
    st.markdown("### ⏰ Step 3: Schedule Campaign")
    st.info("Set up when the campaign should run")
    
    # Campaign basic info
    st.markdown("**📋 Campaign Information**")
    col1, col2 = st.columns(2)
    
    with col1:
        campaign_name = st.text_input("Campaign Name *", 
            value=st.session_state.campaign_data.get('name', ''),
            placeholder="e.g., JEE 2024 Outreach")
    
    with col2:
        campaign_description = st.text_area("Description", 
            value=st.session_state.campaign_data.get('description', ''),
            placeholder="Brief campaign description...")
    
    # Time scheduling
    st.markdown("**⏰ Schedule Settings**")
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input("Start Date", 
            value=st.session_state.campaign_data.get('start_date', datetime.now().date()))
        start_time = st.time_input("Start Time", 
            value=st.session_state.campaign_data.get('start_time', datetime.strptime("09:00", "%H:%M").time()))
    
    with col2:
        end_date = st.date_input("End Date", 
            value=st.session_state.campaign_data.get('end_date', datetime.now().date()))
        end_time = st.time_input("End Time", 
            value=st.session_state.campaign_data.get('end_time', datetime.strptime("18:00", "%H:%M").time()))
    
    # Call settings
    st.markdown("**📞 Call Settings**")
    col1, col2 = st.columns(2)
    
    with col1:
        daily_limit = st.number_input("Daily Call Limit", 
            min_value=1, max_value=1000, 
            value=st.session_state.campaign_data.get('daily_limit', 50))
    
    with col2:
        retry_attempts = st.number_input("Retry Attempts", 
            min_value=0, max_value=5, 
            value=st.session_state.campaign_data.get('retry_attempts', 2))
    
    # Navigation
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("⬅️ Back"):
            st.session_state.campaign_step = 2
            st.rerun()
    
    with col3:
        if st.button("➡️ Next: Generate", type="primary", disabled=not campaign_name):
            # Save all scheduling data
            st.session_state.campaign_data.update({
                'name': campaign_name,
                'description': campaign_description,
                'start_date': start_date,
                'start_time': start_time,
                'end_date': end_date,
                'end_time': end_time,
                'daily_limit': daily_limit,
                'retry_attempts': retry_attempts
            })
            st.session_state.campaign_step = 4
            st.rerun()
    
    if not campaign_name:
        st.warning("⚠️ Please enter a campaign name to continue")

def show_ai_context_generation(api_client):
    """Step 4: AI Context Generation"""
    
    st.markdown("### 🤖 Step 4: Generate Personalized Contexts")
    st.info("AI will generate personalized calling contexts for each selected student")
    
    # Show summary
    campaign_data = st.session_state.campaign_data
    
    st.markdown("**📋 Campaign Summary**")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Name:** {campaign_data.get('name', 'N/A')}")
        st.write(f"**Context Cards:** {len(campaign_data.get('context_note_ids', []))}")
        st.write(f"**Students:** {len(campaign_data.get('student_ids', []))}")
    
    with col2:
        st.write(f"**Start:** {campaign_data.get('start_date', 'N/A')} {campaign_data.get('start_time', 'N/A')}")
        st.write(f"**End:** {campaign_data.get('end_date', 'N/A')} {campaign_data.get('end_time', 'N/A')}")
        st.write(f"**Daily Limit:** {campaign_data.get('daily_limit', 'N/A')}")
    
    st.markdown("---")
    
    # Generation controls
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🤖 Generate Contexts", type="primary"):
            st.session_state.generation_started = True
            st.rerun()
    
    with col2:
        if st.button("⬅️ Back"):
            st.session_state.campaign_step = 3
            st.rerun()
    
    # AI Generation Process
    if st.session_state.get('generation_started', False):
        
        st.markdown("**🤖 AI Context Generation in Progress...**")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Create campaign first
            status_text.text("Creating campaign...")
            progress_bar.progress(0.1)
            
            campaign_payload = {
                "name": campaign_data['name'],
                "description": campaign_data.get('description', ''),
                "context_note_ids": campaign_data['context_note_ids'],
                "student_ids": campaign_data['student_ids'],
                "start_date": campaign_data['start_date'].isoformat(),
                "start_time": campaign_data['start_time'].strftime("%H:%M"),
                "end_date": campaign_data['end_date'].isoformat(),
                "end_time": campaign_data['end_time'].strftime("%H:%M"),
                "daily_limit": campaign_data['daily_limit'],
                "retry_attempts": campaign_data['retry_attempts'],
                "status": "draft"
            }
            
            new_campaign = api_client.create_campaign(campaign_payload)
            campaign_id = new_campaign['id']
            
            status_text.text("Generating personalized contexts...")
            progress_bar.progress(0.3)
            
            # Generate contexts
            contexts = api_client.generate_campaign_contexts(campaign_id)
            
            progress_bar.progress(0.8)
            status_text.text("Activating campaign...")
            
            # Activate campaign
            api_client.activate_campaign(campaign_id)
            
            progress_bar.progress(1.0)
            status_text.text("✅ Campaign created successfully!")
            
            st.success(f"🎉 Campaign '{campaign_data['name']}' created successfully!")
            st.success(f"📞 Generated {len(contexts)} personalized contexts")
            
            # Show some example contexts
            if contexts:
                st.markdown("**📝 Sample Generated Contexts:**")
                for i, context in enumerate(contexts[:3]):  # Show first 3
                    with st.expander(f"Context {i+1}"):
                        st.write(context.get('personalized_context', 'N/A'))
            
            # Reset form
            if st.button("🔄 Create Another Campaign"):
                # Clear session state
                for key in ['campaign_step', 'campaign_data', 'generation_started']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
            
            if st.button("📊 View Campaigns"):
                st.switch_page("pages/campaigns.py")
        
        except Exception as e:
            progress_bar.progress(0)
            status_text.text("")
            st.error(f"❌ Error creating campaign: {str(e)}")
            st.session_state.generation_started = False

def render_create_campaign(api_client):
    """Legacy create campaign function - now redirects to step-by-step process"""
    show_campaign_creation(api_client)

def show_campaign_management(api_client):
    """Campaign management and list view"""
    render_campaigns_list(api_client)

def render_campaign_analytics(api_client):
    """Render campaign analytics dashboard"""
    
    st.subheader("📊 Campaign Analytics")
    
    try:
        # Get analytics data
        with st.spinner("📊 Loading analytics..."):
            analytics = api_client.get_campaign_analytics()
        
        # Time period selector
        col_period1, col_period2 = st.columns(2)
        
        with col_period1:
            time_period = st.selectbox(
                "📅 Analytics Period",
                ["Last 7 days", "Last 30 days", "This Month", "Last 3 Months", "Custom"]
            )
        
        with col_period2:
            if time_period == "Custom":
                date_range = st.date_input("Select Date Range", value=[
                    datetime.now().date() - timedelta(days=30),
                    datetime.now().date()
                ])
        
        # Overview metrics
        render_analytics_overview(analytics)
        
        # Campaign performance comparison
        st.subheader("📈 Campaign Performance Comparison")
        render_campaign_comparison_chart(analytics)
        
        # Success rate trends
        st.subheader("📊 Success Rate Trends")
        render_success_trends_chart(analytics)
        
        # Performance insights
        st.subheader("💡 Performance Insights")
        render_performance_insights(analytics)
        
    except Exception as e:
        st.error(f"❌ Error loading analytics: {str(e)}")

def render_campaign_templates(api_client):
    """Render campaign templates management"""
    
    st.subheader("⚙️ Campaign Templates")
    
    # Template categories
    col_cat1, col_cat2, col_cat3 = st.columns(3)
    
    with col_cat1:
        if st.button("📞 Call Scripts", key="call_scripts"):
            show_call_scripts_templates(api_client)
    
    with col_cat2:
        if st.button("🎯 Campaign Types", key="campaign_types"):
            show_campaign_type_templates(api_client)
    
    with col_cat3:
        if st.button("📋 Quick Setup", key="quick_setup"):
            show_quick_setup_templates(api_client)
    
    # Default templates
    st.markdown("### 📋 Available Templates")
    
    templates = [
        {
            "name": "JEE Admission Campaign",
            "type": "Voice Call",
            "description": "Outreach to JEE aspirants for admission counseling",
            "success_rate": "78%",
            "usage": "145 campaigns"
        },
        {
            "name": "NEET Counseling Drive",
            "type": "Mixed",
            "description": "Multi-channel approach for NEET students",
            "success_rate": "82%",
            "usage": "89 campaigns"
        },
        {
            "name": "Foundation Course Promo",
            "type": "Voice Call + SMS",
            "description": "Promote foundation courses to Class 9-10 students",
            "success_rate": "65%",
            "usage": "67 campaigns"
        }
    ]
    
    for template in templates:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                st.markdown(f"**{template['name']}**")
                st.text(template['description'])
                st.caption(f"Type: {template['type']}")
            
            with col2:
                st.metric("Success Rate", template['success_rate'])
            
            with col3:
                st.metric("Usage", template['usage'])
            
            with col4:
                if st.button("Use", key=f"use_template_{template['name']}"):
                    use_campaign_template(api_client, template)
            
            st.divider()

# Helper functions
def render_campaign_stats(campaigns: List[Dict]):
    """Render campaign statistics"""
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total_campaigns = len(campaigns)
    active_campaigns = len([c for c in campaigns if c.get('status') == 'active'])
    total_targets = sum(c.get('target_count', 0) for c in campaigns)
    total_completed = sum(c.get('completed_count', 0) for c in campaigns)
    avg_success_rate = sum(c.get('success_rate', 0) for c in campaigns) / total_campaigns if total_campaigns > 0 else 0
    
    with col1:
        st.metric("Total Campaigns", f"{total_campaigns:,}")
    
    with col2:
        st.metric("Active Campaigns", f"{active_campaigns:,}")
    
    with col3:
        st.metric("Total Targets", f"{total_targets:,}")
    
    with col4:
        st.metric("Completed", f"{total_completed:,}")
    
    with col5:
        st.metric("Avg Success Rate", f"{avg_success_rate:.1f}%")

def apply_campaign_filters(campaigns: List[Dict], status_filter: str, type_filter: str) -> List[Dict]:
    """Apply filters to campaigns list"""
    
    filtered = campaigns
    
    # Status filter
    if status_filter != "All":
        filtered = [c for c in filtered if c.get('status', '').title() == status_filter]
    
    # Type filter
    if type_filter != "All":
        filtered = [c for c in filtered if c.get('type', '') == type_filter]
    
    return filtered

def render_campaign_card(campaign: Dict, api_client):
    """Render individual campaign card"""
    
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        
        with col1:
            # Campaign name and status
            status_color = {
                'active': '🟢',
                'paused': '🟡', 
                'completed': '🔵',
                'draft': '⚪'
            }.get(campaign.get('status', 'draft'), '⚪')
            
            st.markdown(f"**{status_color} {campaign.get('name', 'Unnamed Campaign')}**")
            st.text(f"Type: {campaign.get('type', 'Unknown')}")
            st.caption(campaign.get('description', '')[:100] + "..." if len(campaign.get('description', '')) > 100 else campaign.get('description', ''))
        
        with col2:
            # Progress metrics
            progress = campaign.get('progress', 0)
            st.metric("Progress", f"{progress:.1f}%")
            
            target_count = campaign.get('target_count', 0)
            completed = campaign.get('completed_count', 0)
            st.text(f"{completed:,} / {target_count:,}")
        
        with col3:
            # Performance metrics
            success_rate = campaign.get('success_rate', 0)
            st.metric("Success Rate", f"{success_rate:.1f}%")
            
            created_date = campaign.get('created_at', '')
            if created_date:
                date_str = datetime.fromisoformat(created_date.replace('Z', '+00:00')).strftime('%m/%d/%Y')
                st.caption(f"Created: {date_str}")
        
        with col4:
            # Action buttons
            campaign_id = campaign.get('id')
            
            if campaign.get('status') == 'active':
                if st.button("⏸️", key=f"pause_{campaign_id}", help="Pause Campaign"):
                    pause_campaign(api_client, campaign_id)
            else:
                if st.button("▶️", key=f"resume_{campaign_id}", help="Resume Campaign"):
                    resume_campaign(api_client, campaign_id)
            
            if st.button("📊", key=f"details_{campaign_id}", help="View Details"):
                show_campaign_details(api_client, campaign_id)
        
        st.divider()

def show_quick_campaign_modal(api_client):
    """Show quick campaign creation modal"""
    st.info("🚧 Quick campaign creation - coming soon!")

def generate_campaign_report(api_client):
    """Generate comprehensive campaign report"""
    st.info("🚧 Campaign report generation - coming soon!")

def pause_all_campaigns(api_client):
    """Pause all active campaigns"""
    st.info("🚧 Pause all campaigns - coming soon!")

def pause_campaign(api_client, campaign_id: int):
    """Pause specific campaign"""
    st.info(f"🚧 Pausing campaign {campaign_id} - coming soon!")

def resume_campaign(api_client, campaign_id: int):
    """Resume specific campaign"""
    st.info(f"🚧 Resuming campaign {campaign_id} - coming soon!")

def show_campaign_details(api_client, campaign_id: int):
    """Show detailed campaign information"""
    st.info(f"🚧 Campaign {campaign_id} details - coming soon!")

def render_analytics_overview(analytics: Dict):
    """Render analytics overview metrics"""
    st.info("🚧 Analytics overview - coming soon!")

def render_campaign_comparison_chart(analytics: Dict):
    """Render campaign performance comparison chart"""
    st.info("🚧 Campaign comparison chart - coming soon!")

def render_success_trends_chart(analytics: Dict):
    """Render success rate trends chart"""
    st.info("🚧 Success trends chart - coming soon!")

def render_performance_insights(analytics: Dict):
    """Render performance insights"""
    st.info("🚧 Performance insights - coming soon!")

def show_call_scripts_templates(api_client):
    """Show call scripts templates"""
    st.info("🚧 Call scripts templates - coming soon!")

def show_campaign_type_templates(api_client):
    """Show campaign type templates"""
    st.info("🚧 Campaign type templates - coming soon!")

def show_quick_setup_templates(api_client):
    """Show quick setup templates"""
    st.info("🚧 Quick setup templates - coming soon!")

def use_campaign_template(api_client, template: Dict):
    """Use a campaign template"""
    st.info(f"🚧 Using template '{template['name']}' - coming soon!")
