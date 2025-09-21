"""
Dashboard page - Main overview with key metrics and charts
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, Any

def show_dashboard():
    """Display main dashboard with metrics and charts"""
    
    # Add beautiful styling
    st.markdown("""
    <style>
    /* Dashboard styling */
    .dashboard-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
    }
    
    .metric-container {
        background: white;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        margin: 10px 0;
    }
    
    .chart-container {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 15px 0;
    }
    
    .action-button {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Beautiful header
    st.markdown("""
    <div class="dashboard-header">
        <h1 style="margin: 0; font-size: 36px; font-weight: 600;">📊 Dashboard Overview</h1>
        <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Welcome to the Akash Institute Outreach System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check API client
    if not st.session_state.get("api_client"):
        st.error("❌ No API connection. Please refresh the page.")
        return
    
    api_client = st.session_state.api_client
    
    # Refresh button
    col_refresh, col_empty = st.columns([1, 4])
    with col_refresh:
        if st.button("🔄 Refresh Data", key="dashboard_refresh"):
            st.rerun()
    
    try:
        # Get dashboard metrics
        with st.spinner("📊 Loading dashboard metrics..."):
            metrics = api_client.get_dashboard_metrics()
            student_analytics = api_client.get_student_analytics()
            call_analytics = api_client.get_call_analytics()
            trends_data = api_client.get_trends_analytics()
        
        # Main metrics row
        render_main_metrics(metrics)
        
        # Charts row
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            render_call_status_chart(call_analytics)
        
        with col_chart2:
            render_daily_activity_chart(trends_data)
        
        # Additional metrics
        render_detailed_metrics(student_analytics, call_analytics)
        
        # Recent activity
        render_recent_activity(api_client)
        
    except Exception as e:
        st.error(f"❌ Error loading dashboard: {str(e)}")
        st.info("💡 Make sure the FastAPI backend is running on http://localhost:8000 (local) or http://akash-outreach-api:8000 (Docker)")

def render_main_metrics(metrics: Dict[str, Any]):
    """Render main KPI metrics"""
    
    st.markdown("### 📈 Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_students = metrics.get("total_students", 0)
        st.markdown(f"""
        <div class="metric-container">
            <h3 style="color: #667eea; margin: 0 0 10px 0;">👥 Total Students</h3>
            <h2 style="margin: 0; color: #333; font-size: 32px;">{total_students:,}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        total_calls = metrics.get("total_calls", 0)
        st.markdown(f"""
        <div class="metric-container">
            <h3 style="color: #667eea; margin: 0 0 10px 0;">📞 Total Calls</h3>
            <h2 style="margin: 0; color: #333; font-size: 32px;">{total_calls:,}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        completion_rate = metrics.get("completion_rate", 0)
        st.markdown(f"""
        <div class="metric-container">
            <h3 style="color: #667eea; margin: 0 0 10px 0;">✅ Completion Rate</h3>
            <h2 style="margin: 0; color: #333; font-size: 32px;">{completion_rate:.1f}%</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        system_health = metrics.get("system_health", "unknown")
        health_color = "#28a745" if system_health == "healthy" else "#dc3545"
        st.markdown(f"""
        <div class="metric-container">
            <h3 style="color: #667eea; margin: 0 0 10px 0;">🏥 System Health</h3>
            <h2 style="margin: 0; color: {health_color}; font-size: 24px; text-transform: capitalize;">{system_health}</h2>
        </div>
        """, unsafe_allow_html=True)

def render_call_status_chart(call_analytics: Dict[str, Any]):
    """Render call status distribution pie chart"""
    
    st.subheader("📊 Call Status Distribution")
    
    # Get status data from call analytics
    status_data = call_analytics.get("calls_by_status", {})
    
    if status_data and any(status_data.values()):
        # Create pie chart
        labels = list(status_data.keys())
        values = list(status_data.values())
        
        # Color mapping for different statuses
        colors = {
            'completed': '#28a745',
            'pending': '#ffc107', 
            'failed': '#dc3545',
            'attempted': '#17a2b8',
            'callback_requested': '#fd7e14',
            'no_answer': '#6c757d',
            'busy': '#e83e8c',
            'in_progress': '#20c997'
        }
        
        chart_colors = [colors.get(label, '#6c757d') for label in labels]
        
        fig = go.Figure(data=[go.Pie(
            labels=[label.replace('_', ' ').title() for label in labels],
            values=values,
            hole=0.4,
            marker_colors=chart_colors,
            textinfo='label+percent'
        )])
        
        fig.update_layout(
            showlegend=True,
            height=400,
            margin=dict(t=0, b=0, l=0, r=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Show clean no data message instead of sample data
        st.markdown("""
        <div class="chart-container">
            <div style="text-align: center; padding: 40px; color: #666;">
                <h3 style="color: #667eea; margin-bottom: 15px;">📊 No Call Data Available</h3>
                <p style="margin: 0;">Start making calls to see real distribution data here.</p>
                <div style="margin-top: 20px;">
                    <p style="font-size: 14px; opacity: 0.8;">• Add students and create call campaigns</p>
                    <p style="font-size: 14px; opacity: 0.8;">• Initiate calls through the Calls page</p>
                    <p style="font-size: 14px; opacity: 0.8;">• Track call status and completion rates</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_daily_activity_chart(trends_data: Dict[str, Any]):
    """Render daily activity line chart"""
    
    st.subheader("📈 Daily Activity Trend")
    
    # Get daily activity data
    daily_data = trends_data.get("daily_data", [])
    
    if daily_data:
        # Convert to DataFrame
        df = pd.DataFrame(daily_data)
        df['date'] = pd.to_datetime(df['date'])
        
        # Create line chart
        fig = px.line(
            df, 
            x='date', 
            y=['calls', 'students_added'],
            title="Daily Calls Made vs Students Added",
            labels={'value': 'Count', 'date': 'Date'},
            color_discrete_map={
                'calls': '#007bff',
                'students_added': '#28a745'
            }
        )
        
        fig.update_layout(
            height=400,
            showlegend=True,
            margin=dict(t=30, b=0, l=0, r=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Show clean no data message for daily activity
        st.markdown("""
        <div class="chart-container">
            <div style="text-align: center; padding: 40px; color: #666;">
                <h3 style="color: #667eea; margin-bottom: 15px;">📈 No Activity Data Yet</h3>
                <p style="margin: 0;">Daily activity trends will appear here as you use the system.</p>
                <div style="margin-top: 20px;">
                    <p style="font-size: 14px; opacity: 0.8;">• Track calls made each day</p>
                    <p style="font-size: 14px; opacity: 0.8;">• Monitor student additions</p>
                    <p style="font-size: 14px; opacity: 0.8;">• Analyze activity patterns</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_detailed_metrics(student_analytics: Dict[str, Any], call_analytics: Dict[str, Any]):
    """Render detailed metrics section"""
    
    st.subheader("📋 Detailed Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**👥 Student Statistics**")
        
        # Student metrics from actual API
        total_students = student_analytics.get("total_students", 0)
        students_by_status = student_analytics.get("students_by_status", {})
        
        student_metrics = [
            ("Total Students", total_students),
            ("Pending Calls", students_by_status.get("pending", 0)),
            ("Completed Calls", students_by_status.get("completed", 0)),
            ("High Priority", students_by_status.get("high_priority", 0)),
        ]
        
        for label, value in student_metrics:
            st.metric(label, f"{value:,}")
    
    with col2:
        st.markdown("**📞 Call Statistics**")
        
        # Call metrics from actual API
        total_calls = call_analytics.get("total_calls", 0)
        successful_calls = call_analytics.get("successful_calls", 0)
        completion_rate = call_analytics.get("completion_rate", 0)
        avg_duration = call_analytics.get("average_duration", 0)
        
        call_metrics = [
            ("Total Calls Made", total_calls),
            ("Successful Calls", successful_calls),
            ("Completion Rate", f"{completion_rate:.1f}%"),
            ("Avg Duration", f"{avg_duration:.1f}s"),
        ]
        
        for label, value in call_metrics:
            if isinstance(value, str):
                st.metric(label, value)
            else:
                st.metric(label, f"{value:,}")

def render_recent_activity(api_client):
    """Render recent activity feed"""
    
    st.subheader("🕐 Recent Activity")
    
    try:
        # Get recent calls
        recent_calls = api_client.get_calls(limit=5)
        
        if recent_calls and isinstance(recent_calls, list):
            for call in recent_calls:
                # Create activity item
                with st.container():
                    col_time, col_content, col_status = st.columns([1, 3, 1])
                    
                    with col_time:
                        # Format timestamp
                        created_at = call.get("created_at", "")
                        if created_at:
                            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            time_str = dt.strftime("%H:%M")
                            st.small(time_str)
                    
                    with col_content:
                        student_id = call.get("student_id", "N/A")
                        call_status = call.get("call_status", "unknown")
                        st.write(f"Call to Student #{student_id}")
                        if call.get("notes"):
                            st.caption(call["notes"][:100] + "..." if len(call["notes"]) > 100 else call["notes"])
                    
                    with col_status:
                        status_colors = {
                            "completed": "🟢",
                            "failed": "🔴", 
                            "attempted": "🟡",
                            "pending": "⚪"
                        }
                        status_icon = status_colors.get(call_status, "⚫")
                        st.write(f"{status_icon} {call_status.title()}")
                
                st.divider()
        else:
            st.info("📝 No recent activity found")
            
    except Exception as e:
        st.error(f"❌ Error loading recent activity: {str(e)}")
