"""
Comprehensive Call Management System
Queue management, call history, real-time tracking, and analytics
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import time
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def show_calls():
    """Display comprehensive call management interface"""
    
    st.title("📞 Call Management Center")
    st.markdown("Manage call queue, track progress, and monitor performance in real-time.")
    
    # Check API client
    if not st.session_state.get("api_client"):
        st.error("❌ No API connection. Please refresh the page.")
        return
    
    api_client = st.session_state.api_client
    
    # Initialize session state for call management
    if "call_queue_auto_refresh" not in st.session_state:
        st.session_state.call_queue_auto_refresh = True
    if "selected_call_id" not in st.session_state:
        st.session_state.selected_call_id = None
    if "call_filter_status" not in st.session_state:
        st.session_state.call_filter_status = "All"
    
    # Auto-refresh toggle
    col_refresh1, col_refresh2, col_refresh3 = st.columns([2, 1, 1])
    
    with col_refresh1:
        auto_refresh = st.toggle("🔄 Auto-refresh (30s)", value=st.session_state.call_queue_auto_refresh)
        st.session_state.call_queue_auto_refresh = auto_refresh
    
    with col_refresh2:
        if st.button("🔄 Refresh Now", key="manual_refresh"):
            st.rerun()
    
    with col_refresh3:
        last_updated = datetime.now().strftime("%H:%M:%S")
        st.caption(f"Last updated: {last_updated}")
    
    # Auto-refresh logic
    if auto_refresh:
        time.sleep(30)
        st.rerun()
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Call Queue", 
        "� Active Calls", 
        "📝 Call History", 
        "📊 Analytics", 
        "⚙️ Settings"
    ])
    
    with tab1:
        render_call_queue(api_client)
    
    with tab2:
        render_active_calls(api_client)
    
    with tab3:
        render_call_history(api_client)
    
    with tab4:
        render_call_analytics(api_client)
    
    with tab5:
        render_call_settings(api_client)

def render_call_queue(api_client):
    """Render call queue management interface"""
    
    st.subheader("🎯 Call Queue Management")
    
    try:
        # Get queue data
        with st.spinner("📊 Loading call queue..."):
            queue_data = api_client.get_call_queue()
        
        # Queue stats
        display_queue_metrics(queue_data)
        
        # Filters
        col_filter1, col_filter2, col_filter3 = st.columns(3)
        
        with col_filter1:
            priority_filter = st.selectbox(
                "⭐ Priority Filter",
                ["All", "High (8+)", "Medium (4-7)", "Low (1-3)"],
                key="queue_priority_filter"
            )
        
        with col_filter2:
            status_filter = st.selectbox(
                "📞 Status Filter", 
                ["All", "pending", "retry", "callback_requested"],
                key="queue_status_filter"
            )
        
        with col_filter3:
            sort_by = st.selectbox(
                "📈 Sort By",
                ["Priority (High→Low)", "Created (Old→New)", "Last Attempt", "Student Name"],
                key="queue_sort"
            )
        
        # Display queue
        queue_students = queue_data.get("students", [])
        
        if queue_students:
            # Apply filters
            filtered_students = apply_queue_filters(queue_students, priority_filter, status_filter)
            
            st.subheader(f"📋 Queue ({len(filtered_students)}/{len(queue_students)} students)")
            
            # Queue table
            render_queue_table(filtered_students, api_client)
            
        else:
            st.info("📝 No students in call queue")
            
            if st.button("➕ Add Students to Queue"):
                st.session_state.active_tab = "students"
                st.rerun()
    
    except Exception as e:
        st.error(f"❌ Error loading call queue: {str(e)}")

def render_active_calls(api_client):
    """Render active calls monitoring"""
    
    st.subheader("📞 Active Calls Monitor")
    
    try:
        # Get active calls
        with st.spinner("📊 Loading active calls..."):
            active_calls = api_client.get_active_calls()
        
        if active_calls:
            st.success(f"📞 {len(active_calls)} active calls")
            
            # Active calls grid
            for i, call in enumerate(active_calls):
                render_active_call_card(call, api_client, i)
        
        else:
            st.info("📝 No active calls")
            
            # Quick start section
            col_start1, col_start2 = st.columns(2)
            
            with col_start1:
                if st.button("🎯 Start from Queue", key="start_from_queue"):
                    start_calling_queue(api_client)
            
            with col_start2:
                if st.button("📞 Manual Call", key="manual_call"):
                    show_manual_call_form(api_client)
    
    except Exception as e:
        st.error(f"❌ Error loading active calls: {str(e)}")

def render_call_history(api_client):
    """Render call history and logs"""
    
    st.subheader("📝 Call History & Logs")
    
    # Date range filter
    col_date1, col_date2, col_date3 = st.columns(3)
    
    with col_date1:
        date_from = st.date_input("From Date", value=datetime.now().date() - timedelta(days=7))
    
    with col_date2:
        date_to = st.date_input("To Date", value=datetime.now().date())
    
    with col_date3:
        call_status = st.selectbox(
            "Call Status",
            ["All", "completed", "failed", "no_answer", "busy", "callback_requested"]
        )
    
    try:
        # Get call history
        with st.spinner("📊 Loading call history..."):
            history_data = api_client.get_call_history(
                date_from=date_from.isoformat(),
                date_to=date_to.isoformat(),
                status=call_status if call_status != "All" else None
            )
        
        calls = history_data.get("calls", [])
        
        if calls:
            st.info(f"📊 Found {len(calls)} calls")
            
            # History stats
            render_history_stats(calls)
            
            # History table
            render_history_table(calls, api_client)
        
        else:
            st.info("📝 No calls found for the selected criteria")
    
    except Exception as e:
        st.error(f"❌ Error loading call history: {str(e)}")

def render_call_analytics(api_client):
    """Render call analytics and performance metrics"""
    
    st.subheader("📊 Call Analytics & Performance")
    
    try:
        # Get analytics data
        with st.spinner("📊 Loading analytics..."):
            analytics = api_client.get_call_analytics()
        
        # Time period selector
        col_period1, col_period2 = st.columns(2)
        
        with col_period1:
            time_period = st.selectbox(
                "📅 Time Period",
                ["Today", "Last 7 days", "Last 30 days", "This Month", "Custom"]
            )
        
        with col_period2:
            if time_period == "Custom":
                custom_date = st.date_input("Select Date Range", value=[
                    datetime.now().date() - timedelta(days=30),
                    datetime.now().date()
                ])
        
        # Key metrics
        render_analytics_metrics(analytics)
        
        # Charts
        render_analytics_charts(analytics)
        
        # Performance insights
        render_performance_insights(analytics)
        
    except Exception as e:
        st.error(f"❌ Error loading analytics: {str(e)}")

def render_call_settings(api_client):
    """Render call settings and configuration"""
    
    st.subheader("⚙️ Call Settings & Configuration")
    
    # Queue settings
    st.markdown("**🎯 Queue Settings**")
    
    col_set1, col_set2 = st.columns(2)
    
    with col_set1:
        max_retries = st.number_input("Max Retry Attempts", min_value=1, max_value=10, value=3)
        retry_delay = st.number_input("Retry Delay (minutes)", min_value=5, max_value=120, value=30)
    
    with col_set2:
        priority_boost = st.checkbox("Priority Boost for Callbacks", value=True)
        auto_redial = st.checkbox("Auto Redial Failed Calls", value=False)
    
    # Call timing settings
    st.markdown("**⏰ Call Timing**")
    
    col_time1, col_time2 = st.columns(2)
    
    with col_time1:
        call_timeout = st.number_input("Call Timeout (seconds)", min_value=30, max_value=300, value=60)
        ring_duration = st.number_input("Ring Duration (seconds)", min_value=10, max_value=60, value=30)
    
    with col_time2:
        working_hours_start = st.time_input("Working Hours Start", value=datetime.strptime("09:00", "%H:%M").time())
        working_hours_end = st.time_input("Working Hours End", value=datetime.strptime("18:00", "%H:%M").time())
    
    # Save settings
    if st.button("💾 Save Settings", type="primary"):
        settings_data = {
            "max_retries": max_retries,
            "retry_delay": retry_delay,
            "priority_boost": priority_boost,
            "auto_redial": auto_redial,
            "call_timeout": call_timeout,
            "ring_duration": ring_duration,
            "working_hours_start": working_hours_start.strftime("%H:%M"),
            "working_hours_end": working_hours_end.strftime("%H:%M")
        }
        
        try:
            api_client.update_call_settings(settings_data)
            st.success("✅ Settings saved successfully!")
        except Exception as e:
            st.error(f"❌ Error saving settings: {str(e)}")

# Helper functions
def display_queue_metrics(queue_data: Dict[str, Any]):
    """Display queue metrics"""
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_queue = queue_data.get("total_students", 0)
        st.metric("Total Queue", f"{total_queue:,}")
    
    with col2:
        high_priority = queue_data.get("high_priority_count", 0)
        st.metric("High Priority", f"{high_priority:,}")
    
    with col3:
        retries = queue_data.get("retry_count", 0)
        st.metric("Retries", f"{retries:,}")
    
    with col4:
        callbacks = queue_data.get("callback_count", 0)
        st.metric("Callbacks", f"{callbacks:,}")
    
    with col5:
        avg_wait = queue_data.get("avg_wait_time", 0)
        st.metric("Avg Wait", f"{avg_wait:.1f}m")

def apply_queue_filters(students: List[Dict], priority_filter: str, status_filter: str) -> List[Dict]:
    """Apply filters to queue students"""
    
    filtered = students
    
    # Priority filter
    if priority_filter != "All":
        if "High" in priority_filter:
            filtered = [s for s in filtered if s.get("priority", 1) >= 8]
        elif "Medium" in priority_filter:
            filtered = [s for s in filtered if 4 <= s.get("priority", 1) <= 7]
        elif "Low" in priority_filter:
            filtered = [s for s in filtered if s.get("priority", 1) <= 3]
    
    # Status filter
    if status_filter != "All":
        filtered = [s for s in filtered if s.get("call_status") == status_filter]
    
    return filtered

def render_queue_table(students: List[Dict], api_client):
    """Render queue table with actions"""
    
    # Prepare data for display
    df_data = []
    for student in students[:50]:  # Limit to 50 for performance
        student_data = student.get("student_data", {})
        
        row = {
            "ID": student.get("id"),
            "Priority": f"⭐ {student.get('priority', 1)}",
            "Student": student_data.get("student_name", "N/A"),
            "Phone": student.get("phone_number", "N/A"),
            "Status": student.get("call_status", "pending").title(),
            "Attempts": student.get("call_count", 0),
            "Last Attempt": format_datetime_short(student.get("last_call_attempt")),
            "Course": student_data.get("course", "N/A"),
            "Created": format_datetime_short(student.get("created_at"))
        }
        df_data.append(row)
    
    df = pd.DataFrame(df_data)
    
    # Display table with selection
    selected_rows = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="multi-row"
    )

def render_active_call_card(call: Dict[str, Any], api_client, index: int):
    """Render card for active call"""
    
    with st.container():
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        
        with col1:
            st.markdown(f"**📞 Call #{call.get('id')}**")
            st.text(f"Student: {call.get('student_name', 'N/A')}")
            st.text(f"Phone: {call.get('phone_number', 'N/A')}")
        
        with col2:
            duration = call.get('duration', 0)
            st.text(f"Duration: {format_duration(duration)}")
            st.text(f"Status: {call.get('status', 'unknown').title()}")
        
        with col3:
            started_at = call.get('started_at', '')
            st.text(f"Started: {format_datetime_short(started_at)}")
            agent = call.get('agent_name', 'System')
            st.text(f"Agent: {agent}")
        
        with col4:
            if st.button("🔴 End", key=f"end_call_{index}"):
                end_call(api_client, call.get('id'))
        
        st.divider()

def start_calling_queue(api_client):
    """Start calling from queue"""
    try:
        result = api_client.start_calling_queue()
        st.success(f"✅ Started calling! {result.get('initiated_calls', 0)} calls initiated.")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error starting calls: {str(e)}")

def export_call_queue(api_client):
    """Export call queue data"""
    try:
        queue_data = api_client.get_call_queue()
        students = queue_data.get("students", [])
        
        if students:
            df = pd.DataFrame(students)
            csv = df.to_csv(index=False)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"call_queue_{timestamp}.csv"
            
            st.download_button(
                "📥 Download Queue",
                csv,
                filename,
                "text/csv"
            )
        else:
            st.warning("⚠️ No students in queue to export")
    
    except Exception as e:
        st.error(f"❌ Export failed: {str(e)}")

def format_datetime_short(dt_str: str) -> str:
    """Format datetime for short display"""
    if not dt_str:
        return "Never"
    
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%m/%d %H:%M")
    except:
        return dt_str[:10] if len(dt_str) >= 10 else dt_str

def format_duration(seconds: int) -> str:
    """Format duration in seconds to readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

# Placeholder functions for functionality that requires backend implementation
def show_manual_call_form(api_client):
    """Show manual call form"""
    st.info("🚧 Manual call form coming soon!")

def initiate_calls(api_client, student_ids: List[int]):
    """Initiate calls for selected students"""
    st.info(f"🚧 Initiating calls for {len(student_ids)} students - coming soon!")

def skip_calls(api_client, student_ids: List[int]):
    """Skip selected students in queue"""
    st.info(f"🚧 Skipping {len(student_ids)} students - coming soon!")

def remove_from_queue(api_client, student_ids: List[int]):
    """Remove students from queue"""
    st.info(f"🚧 Removing {len(student_ids)} students from queue - coming soon!")

def end_call(api_client, call_id: int):
    """End active call"""
    st.info(f"🚧 Ending call #{call_id} - coming soon!")

def render_history_stats(calls: List[Dict]):
    """Render call history statistics"""
    st.info("🚧 Call history statistics - coming soon!")

def render_history_table(calls: List[Dict], api_client):
    """Render call history table"""
    st.info("🚧 Call history table - coming soon!")

def render_analytics_metrics(analytics: Dict):
    """Render analytics metrics"""
    st.info("🚧 Analytics metrics - coming soon!")

def render_analytics_charts(analytics: Dict):
    """Render analytics charts"""
    st.info("🚧 Analytics charts - coming soon!")

def render_performance_insights(analytics: Dict):
    """Render performance insights"""
    st.info("🚧 Performance insights - coming soon!")
