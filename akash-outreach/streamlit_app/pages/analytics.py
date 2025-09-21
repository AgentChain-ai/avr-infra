"""
Advanced Analytics and Reporting Dashboard
Comprehensive analytics with call performance, student engagement, and campaign effectiveness
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import numpy as np

def show_analytics():
    """Display comprehensive analytics dashboard"""
    
    st.title("� Advanced Analytics & Insights")
    st.markdown("Comprehensive analytics for call performance, student engagement, and campaign effectiveness.")
    
    # Check API client
    if not st.session_state.get("api_client"):
        st.error("❌ No API connection. Please refresh the page.")
        return
    
    api_client = st.session_state.api_client
    
    # Time range selector
    col_date1, col_date2, col_refresh = st.columns([2, 2, 1])
    
    with col_date1:
        date_from = st.date_input(
            "From Date", 
            value=datetime.now().date() - timedelta(days=30),
            key="analytics_date_from"
        )
    
    with col_date2:
        date_to = st.date_input(
            "To Date", 
            value=datetime.now().date(),
            key="analytics_date_to"
        )
    
    with col_refresh:
        st.write("")  # Spacer
        if st.button("🔄 Refresh Data", key="refresh_analytics"):
            st.rerun()
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Overview", 
        "📞 Call Performance", 
        "🎯 Campaign Analytics",
        "👥 Student Insights",
        "🔍 Advanced Reports"
    ])
    
    with tab1:
        render_overview_analytics(api_client, date_from, date_to)
    
    with tab2:
        render_call_performance(api_client, date_from, date_to)
    
    with tab3:
        render_campaign_analytics(api_client, date_from, date_to)
    
    with tab4:
        render_student_insights(api_client, date_from, date_to)
    
    with tab5:
        render_advanced_reports(api_client, date_from, date_to)

def render_overview_analytics(api_client, date_from, date_to):
    """Render overview analytics dashboard"""
    
    st.subheader("📈 Performance Overview")
    
    try:
        # Get overview data
        with st.spinner("📊 Loading overview data..."):
            overview_data = api_client.get_dashboard_metrics()
        
        # Key Performance Indicators
        render_kpi_metrics(overview_data)
        
        # Performance trends
        st.subheader("📈 Performance Trends")
        render_performance_trends(overview_data)
        
        # Success rate breakdown
        st.subheader("✅ Success Rate Analysis")
        render_success_breakdown(overview_data)
        
        # Daily activity heatmap
        st.subheader("🔥 Daily Activity Heatmap")
        render_activity_heatmap(overview_data)
        
    except Exception as e:
        st.error(f"❌ Error loading overview data: {str(e)}")
        render_demo_overview()

def render_call_performance(api_client, date_from, date_to):
    """Render detailed call performance analytics"""
    
    st.subheader("📞 Call Performance Analytics")
    
    try:
        # Get call analytics
        with st.spinner("📞 Loading call performance data..."):
            call_data = api_client.get_call_analytics()
        
        # Call volume metrics
        render_call_volume_metrics(call_data)
        
        # Call duration analysis
        st.subheader("⏱️ Call Duration Analysis")
        render_call_duration_analysis(call_data)
        
        # Success rate by time
        st.subheader("📈 Success Rate by Hour")
        render_hourly_success_rates(call_data)
        
        # Call outcome distribution
        st.subheader("📊 Call Outcome Distribution")
        render_call_outcomes(call_data)
        
    except Exception as e:
        st.error(f"❌ Error loading call performance: {str(e)}")
        render_demo_call_performance()

def render_campaign_analytics(api_client, date_from, date_to):
    """Render campaign analytics"""
    
    st.subheader("🎯 Campaign Performance Analytics")
    
    try:
        # Get campaign analytics
        with st.spinner("🎯 Loading campaign analytics..."):
            campaign_data = api_client.get_campaign_analytics()
        
        # Campaign comparison
        render_campaign_comparison(campaign_data)
        
        # Campaign ROI analysis
        st.subheader("💰 ROI Analysis")
        render_campaign_roi(campaign_data)
        
        # Target audience effectiveness
        st.subheader("🎯 Target Audience Effectiveness")
        render_audience_effectiveness(campaign_data)
        
    except Exception as e:
        st.error(f"❌ Error loading campaign analytics: {str(e)}")
        render_demo_campaign_analytics()

def render_student_insights(api_client, date_from, date_to):
    """Render student engagement insights"""
    
    st.subheader("👥 Student Engagement Insights")
    
    try:
        # Get student insights
        with st.spinner("� Loading student insights..."):
            student_data = api_client.get_student_analytics()
        
        # Engagement metrics
        render_engagement_metrics(student_data)
        
        # Course interest analysis
        st.subheader("📚 Course Interest Analysis")
        render_course_interest(student_data)
        
        # Scholarship impact
        st.subheader("💰 Scholarship Impact Analysis")
        render_scholarship_impact(student_data)
        
    except Exception as e:
        st.error(f"❌ Error loading student insights: {str(e)}")
        render_demo_student_insights()

def render_advanced_reports(api_client, date_from, date_to):
    """Render advanced reports and custom analytics"""
    
    st.subheader("� Advanced Reports & Custom Analytics")
    
    # Report selector
    report_type = st.selectbox(
        "Select Report Type",
        [
            "Executive Summary",
            "Call Center Performance",
            "Student Conversion Funnel",
            "Campaign ROI Analysis",
            "Custom Query Builder"
        ]
    )
    
    if report_type == "Executive Summary":
        render_executive_summary(api_client, date_from, date_to)
    elif report_type == "Call Center Performance":
        render_call_center_report(api_client, date_from, date_to)
    elif report_type == "Student Conversion Funnel":
        render_conversion_funnel(api_client, date_from, date_to)
    elif report_type == "Campaign ROI Analysis":
        render_roi_analysis(api_client, date_from, date_to)
    elif report_type == "Custom Query Builder":
        render_custom_query_builder(api_client)

# Helper functions for rendering specific visualizations
def render_kpi_metrics(data: Dict):
    """Render key performance indicators"""
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_calls = data.get("total_calls", 0)
        st.metric("Total Calls", f"{total_calls:,}")
    
    with col2:
        total_students = data.get("total_students", 0)
        st.metric("Total Students", f"{total_students:,}")
    
    with col3:
        pending_calls = data.get("pending_calls", 0)
        st.metric("Pending Calls", f"{pending_calls:,}")
    
    with col4:
        completed_calls = data.get("completed_calls", 0)
        if total_calls > 0:
            success_rate = (completed_calls / total_calls) * 100
            st.metric("Success Rate", f"{success_rate:.1f}%")
        else:
            st.metric("Success Rate", "0%")
    
    with col5:
        avg_calls_per_day = data.get("avg_calls_per_day", 0)
        st.metric("Avg Calls/Day", f"{avg_calls_per_day:.0f}")

def render_performance_trends(data: Dict):
    """Render performance trend charts"""
    
    # Generate sample trend data
    dates = [datetime.now().date() - timedelta(days=i) for i in range(30, 0, -1)]
    
    # Sample data based on API metrics
    base_calls = data.get("total_calls", 100) / 30
    call_volumes = [int(base_calls + np.random.normal(0, 5)) for _ in range(30)]
    success_rates = [60 + np.random.normal(0, 10) for _ in range(30)]
    
    trends_df = pd.DataFrame({
        'Date': dates,
        'Call Volume': call_volumes,
        'Success Rate': success_rates
    })
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Daily Call Volume', 'Success Rate Trend'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Call volume
    fig.add_trace(
        go.Scatter(x=trends_df['Date'], y=trends_df['Call Volume'], 
                  name='Call Volume', line=dict(color='blue')),
        row=1, col=1
    )
    
    # Success rate
    fig.add_trace(
        go.Scatter(x=trends_df['Date'], y=trends_df['Success Rate'], 
                  name='Success Rate', line=dict(color='green')),
        row=1, col=2
    )
    
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

def render_success_breakdown(data: Dict):
    """Render success rate breakdown"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Success by call attempt
        attempts_df = pd.DataFrame({
            "Attempt": ["1st Attempt", "2nd Attempt", "3rd Attempt", "4th+ Attempt"],
            "Success Rate": [75, 45, 25, 15]
        })
        
        fig = px.bar(attempts_df, x="Attempt", y="Success Rate", 
                   title="Success Rate by Attempt Number",
                   color="Success Rate", color_continuous_scale="viridis")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Success by time of day
        hourly_df = pd.DataFrame({
            "Hour": [f"{hour:02d}:00" for hour in range(9, 18)],
            "Success Rate": [50, 65, 70, 75, 80, 85, 75, 65, 55]
        })
        
        fig = px.line(hourly_df, x="Hour", y="Success Rate",
                    title="Success Rate by Hour of Day",
                    markers=True)
        st.plotly_chart(fig, use_container_width=True)

def render_activity_heatmap(data: Dict):
    """Render daily activity heatmap"""
    
    # Generate sample heatmap data
    hours = list(range(24))
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    # Sample activity data (higher during business hours)
    heatmap_data = []
    for day in range(7):
        day_data = []
        for hour in range(24):
            if 9 <= hour <= 17 and day < 5:  # Business hours, weekdays
                activity = np.random.randint(50, 100)
            elif 9 <= hour <= 17:  # Business hours, weekend
                activity = np.random.randint(10, 30)
            else:  # Off hours
                activity = np.random.randint(0, 10)
            day_data.append(activity)
        heatmap_data.append(day_data)
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=[f"{h:02d}:00" for h in hours],
        y=days,
        colorscale='Blues',
        colorbar=dict(title="Call Volume")
    ))
    
    fig.update_layout(
        title="Call Activity Heatmap (Calls per Hour)",
        xaxis_title="Hour of Day",
        yaxis_title="Day of Week",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Demo functions for when API data is not available
def render_demo_overview():
    """Render demo overview when API is not available"""
    
    st.info("📊 Showing demo analytics data")
    
    # Demo KPI metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Calls", "2,547")
    
    with col2:
        st.metric("Total Students", "1,834")
    
    with col3:
        st.metric("Pending Calls", "567")
    
    with col4:
        st.metric("Success Rate", "68.3%")
    
    with col5:
        st.metric("Avg Calls/Day", "85")

def render_demo_call_performance():
    """Render demo call performance"""
    
    st.info("📞 Showing demo call performance data")
    
    # Demo call outcomes pie chart
    outcomes_df = pd.DataFrame({
        'Outcome': ['Successful', 'No Answer', 'Busy', 'Failed', 'Callback'],
        'Count': [342, 156, 89, 67, 45]
    })
    
    fig = px.pie(outcomes_df, values='Count', names='Outcome', 
                title="Call Outcomes Distribution")
    st.plotly_chart(fig, use_container_width=True)

def render_demo_campaign_analytics():
    """Render demo campaign analytics"""
    
    st.info("🎯 Showing demo campaign analytics")
    
    # Demo campaign performance
    campaigns_df = pd.DataFrame({
        'Campaign': ['JEE 2024', 'NEET Prep', 'Foundation', 'Scholarship'],
        'Reach': [1200, 800, 600, 400],
        'Conversion': [240, 160, 120, 80],
        'ROI': [320, 280, 200, 150]
    })
    
    fig = px.bar(campaigns_df, x='Campaign', y=['Reach', 'Conversion'], 
                title="Campaign Performance Comparison", barmode='group')
    st.plotly_chart(fig, use_container_width=True)

def render_demo_student_insights():
    """Render demo student insights"""
    
    st.info("👥 Showing demo student insights")
    
    # Demo course interest
    courses_df = pd.DataFrame({
        'Course': ['JEE Advanced', 'JEE Main', 'NEET', 'Foundation', 'KVPY'],
        'Interest': [35, 40, 30, 25, 15],
        'Enrollment': [28, 32, 24, 20, 12]
    })
    
    fig = px.bar(courses_df, x='Course', y=['Interest', 'Enrollment'], 
                title="Course Interest vs Enrollment", barmode='group')
    st.plotly_chart(fig, use_container_width=True)

# Placeholder functions for advanced analytics
def render_call_volume_metrics(data): 
    st.info("📊 Call volume metrics - coming soon!")

def render_call_duration_analysis(data): 
    st.info("⏱️ Call duration analysis - coming soon!")

def render_hourly_success_rates(data): 
    st.info("📈 Hourly success rates - coming soon!")

def render_call_outcomes(data): 
    render_demo_call_performance()

def render_campaign_comparison(data): 
    render_demo_campaign_analytics()

def render_campaign_roi(data): 
    st.info("💰 Campaign ROI analysis - coming soon!")

def render_audience_effectiveness(data): 
    st.info("🎯 Audience effectiveness - coming soon!")

def render_engagement_metrics(data): 
    render_demo_student_insights()

def render_course_interest(data): 
    st.info("📚 Course interest analysis - coming soon!")

def render_scholarship_impact(data): 
    st.info("💰 Scholarship impact analysis - coming soon!")

def render_executive_summary(api_client, date_from, date_to): 
    st.info("📋 Executive summary report - coming soon!")

def render_call_center_report(api_client, date_from, date_to): 
    st.info("📞 Call center performance report - coming soon!")

def render_conversion_funnel(api_client, date_from, date_to): 
    st.info("🔄 Conversion funnel analysis - coming soon!")

def render_roi_analysis(api_client, date_from, date_to): 
    st.info("💰 ROI analysis report - coming soon!")

def render_custom_query_builder(api_client): 
    st.info("🔍 Custom query builder - coming soon!")
