"""
Comprehensive Settings & Configuration Management
System settings, user preferences, integrations, and security
"""

import streamlit as st
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

def show_settings():
    """Display comprehensive settings management interface"""
    
    st.title("⚙️ Settings & Configuration")
    st.markdown("Manage system settings, user preferences, and integrations.")
    
    # Check API client
    if not st.session_state.get("api_client"):
        st.error("❌ No API connection. Please refresh the page.")
        return
    
    api_client = st.session_state.api_client
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🎯 General", 
        "📞 Call Settings", 
        "👥 User Management",
        "🔗 Integrations", 
        "🔒 Security",
        "🚀 System"
    ])
    
    with tab1:
        render_general_settings(api_client)
    
    with tab2:
        render_call_settings(api_client)
    
    with tab3:
        render_user_management(api_client)
    
    with tab4:
        render_integrations(api_client)
    
    with tab5:
        render_security_settings(api_client)
    
    with tab6:
        render_system_settings(api_client)

def render_general_settings(api_client):
    """Render general system settings"""
    
    st.subheader("🎯 General Settings")
    
    try:
        # Get current settings
        with st.spinner("⚙️ Loading settings..."):
            settings = api_client.get_system_settings()
        
        with st.form("general_settings_form"):
            # Organization settings
            st.markdown("**🏢 Organization Information**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                org_name = st.text_input("Organization Name", value=settings.get("org_name", "Akash Institute"))
                org_address = st.text_area("Address", value=settings.get("org_address", ""))
            
            with col2:
                org_phone = st.text_input("Contact Phone", value=settings.get("org_phone", ""))
                org_email = st.text_input("Contact Email", value=settings.get("org_email", ""))
            
            # Time zone and locale
            st.markdown("**🌍 Locale & Time Zone**")
            
            col3, col4 = st.columns(2)
            
            with col3:
                timezone = st.selectbox(
                    "Time Zone",
                    ["Asia/Kolkata", "UTC", "Asia/Dubai", "US/Eastern", "US/Pacific"],
                    index=0
                )
            
            with col4:
                language = st.selectbox(
                    "Default Language",
                    ["English", "Hindi", "Bengali", "Tamil", "Telugu"],
                    index=0
                )
            
            # Default settings
            st.markdown("**📋 Default Settings**")
            
            col5, col6 = st.columns(2)
            
            with col5:
                default_priority = st.slider("Default Student Priority", min_value=1, max_value=10, value=5)
                max_retry_attempts = st.number_input("Max Retry Attempts", min_value=1, max_value=10, value=3)
            
            with col6:
                session_timeout = st.number_input("Session Timeout (minutes)", min_value=15, max_value=480, value=60)
                auto_save_interval = st.number_input("Auto-save Interval (seconds)", min_value=30, max_value=300, value=60)
            
            # Submit button
            if st.form_submit_button("💾 Save General Settings", type="primary"):
                general_settings = {
                    "org_name": org_name,
                    "org_address": org_address,
                    "org_phone": org_phone,
                    "org_email": org_email,
                    "timezone": timezone,
                    "language": language,
                    "default_priority": default_priority,
                    "max_retry_attempts": max_retry_attempts,
                    "session_timeout": session_timeout,
                    "auto_save_interval": auto_save_interval
                }
                
                try:
                    api_client.update_system_settings("general", general_settings)
                    st.success("✅ General settings saved successfully!")
                except Exception as e:
                    st.error(f"❌ Error saving settings: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ Error loading settings: {str(e)}")

def render_call_settings(api_client):
    """Render call management settings"""
    
    st.subheader("📞 Call Management Settings")
    
    try:
        # Get current call settings
        with st.spinner("📞 Loading call settings..."):
            call_settings = api_client.get_call_settings()
        
        with st.form("call_settings_form"):
            # Queue settings
            st.markdown("**🎯 Queue Management**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                queue_size_limit = st.number_input("Queue Size Limit", min_value=50, max_value=5000, value=1000)
                priority_boost_callbacks = st.checkbox("Priority Boost for Callbacks", value=True)
            
            with col2:
                auto_queue_refill = st.checkbox("Auto Queue Refill", value=True)
                queue_sort_method = st.selectbox("Queue Sort Method", ["Priority", "Created Date", "Last Attempt", "Random"])
            
            # Call timing
            st.markdown("**⏰ Call Timing**")
            
            col3, col4 = st.columns(2)
            
            with col3:
                call_timeout = st.number_input("Call Timeout (seconds)", min_value=30, max_value=300, value=60)
                ring_duration = st.number_input("Ring Duration (seconds)", min_value=10, max_value=60, value=30)
            
            with col4:
                retry_delay = st.number_input("Retry Delay (minutes)", min_value=5, max_value=480, value=30)
                callback_delay = st.number_input("Callback Delay (minutes)", min_value=15, max_value=1440, value=60)
            
            # Working hours
            st.markdown("**🕒 Working Hours**")
            
            col5, col6 = st.columns(2)
            
            with col5:
                working_start = st.time_input("Start Time", value=datetime.strptime("09:00", "%H:%M").time())
                working_end = st.time_input("End Time", value=datetime.strptime("18:00", "%H:%M").time())
            
            with col6:
                weekend_calls = st.checkbox("Allow Weekend Calls", value=False)
                holiday_calls = st.checkbox("Allow Holiday Calls", value=False)
            
            # Call recording and logging
            st.markdown("**📝 Recording & Logging**")
            
            col7, col8 = st.columns(2)
            
            with col7:
                enable_recording = st.checkbox("Enable Call Recording", value=True)
                auto_transcription = st.checkbox("Auto Transcription", value=True)
            
            with col8:
                detailed_logging = st.checkbox("Detailed Call Logging", value=True)
                call_analytics = st.checkbox("Real-time Call Analytics", value=True)
            
            # Submit button
            if st.form_submit_button("💾 Save Call Settings", type="primary"):
                call_config = {
                    "queue_size_limit": queue_size_limit,
                    "priority_boost_callbacks": priority_boost_callbacks,
                    "auto_queue_refill": auto_queue_refill,
                    "queue_sort_method": queue_sort_method,
                    "call_timeout": call_timeout,
                    "ring_duration": ring_duration,
                    "retry_delay": retry_delay,
                    "callback_delay": callback_delay,
                    "working_hours": {
                        "start": working_start.strftime("%H:%M"),
                        "end": working_end.strftime("%H:%M")
                    },
                    "weekend_calls": weekend_calls,
                    "holiday_calls": holiday_calls,
                    "enable_recording": enable_recording,
                    "auto_transcription": auto_transcription,
                    "detailed_logging": detailed_logging,
                    "call_analytics": call_analytics
                }
                
                try:
                    api_client.update_call_settings(call_config)
                    st.success("✅ Call settings saved successfully!")
                except Exception as e:
                    st.error(f"❌ Error saving call settings: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ Error loading call settings: {str(e)}")

def render_user_management(api_client):
    """Render user management interface"""
    
    st.subheader("👥 User Management")
    
    # User list and management
    try:
        with st.spinner("👥 Loading users..."):
            users = api_client.get_users()
        
        # Users table
        if users:
            st.subheader(f"📋 Users ({len(users)})")
            render_users_table(users, api_client)
        else:
            st.info("👥 No users found")
    
    except Exception as e:
        st.error(f"❌ Error loading users: {str(e)}")

def render_integrations(api_client):
    """Render integrations management"""
    
    st.subheader("🔗 Integrations & APIs")
    
    # Available integrations
    integrations = [
        {
            "name": "OpenAI API",
            "description": "AI-powered conversation analysis and script generation",
            "status": "active",
            "icon": "🤖"
        },
        {
            "name": "Twilio Voice",
            "description": "Voice calling infrastructure",
            "status": "configured",
            "icon": "📞"
        },
        {
            "name": "Google Sheets",
            "description": "Export data to Google Sheets",
            "status": "inactive",
            "icon": "📊"
        },
        {
            "name": "Slack Notifications",
            "description": "Real-time notifications to Slack channels",
            "status": "inactive",
            "icon": "💬"
        },
        {
            "name": "Webhook Endpoints",
            "description": "Custom webhook integrations",
            "status": "active",
            "icon": "🔗"
        }
    ]
    
    for integration in integrations:
        with st.container():
            col1, col2, col3, col4 = st.columns([1, 3, 2, 1])
            
            with col1:
                st.markdown(f"## {integration['icon']}")
            
            with col2:
                st.markdown(f"**{integration['name']}**")
                st.text(integration['description'])
            
            with col3:
                status_color = {
                    'active': '🟢 Active',
                    'configured': '🟡 Configured',
                    'inactive': '⚪ Inactive'
                }
                st.text(status_color.get(integration['status'], '❓ Unknown'))
            
            with col4:
                if st.button("⚙️ Configure", key=f"config_{integration['name']}"):
                    configure_integration(api_client, integration)
            
            st.divider()

def render_security_settings(api_client):
    """Render security settings"""
    
    st.subheader("🔒 Security Settings")
    
    try:
        with st.spinner("🔒 Loading security settings..."):
            security_settings = api_client.get_security_settings()
        
        with st.form("security_settings_form"):
            # Authentication settings
            st.markdown("**🔐 Authentication**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                password_min_length = st.number_input("Min Password Length", min_value=6, max_value=20, value=8)
                require_special_chars = st.checkbox("Require Special Characters", value=True)
            
            with col2:
                session_timeout = st.number_input("Session Timeout (minutes)", min_value=15, max_value=480, value=60)
                max_login_attempts = st.number_input("Max Login Attempts", min_value=3, max_value=10, value=5)
            
            # API security
            st.markdown("**🔑 API Security**")
            
            col3, col4 = st.columns(2)
            
            with col3:
                api_rate_limit = st.number_input("API Rate Limit (req/min)", min_value=10, max_value=1000, value=100)
                enable_cors = st.checkbox("Enable CORS", value=True)
            
            with col4:
                api_key_rotation = st.number_input("API Key Rotation (days)", min_value=30, max_value=365, value=90)
                require_https = st.checkbox("Require HTTPS", value=True)
            
            # Audit and logging
            st.markdown("**📋 Audit & Logging**")
            
            col5, col6 = st.columns(2)
            
            with col5:
                enable_audit_log = st.checkbox("Enable Audit Logging", value=True)
                log_retention_days = st.number_input("Log Retention (days)", min_value=30, max_value=365, value=90)
            
            with col6:
                enable_alerts = st.checkbox("Security Alerts", value=True)
                alert_email = st.text_input("Alert Email", value=security_settings.get("alert_email", ""))
            
            # Submit button
            if st.form_submit_button("💾 Save Security Settings", type="primary"):
                security_config = {
                    "password_min_length": password_min_length,
                    "require_special_chars": require_special_chars,
                    "session_timeout": session_timeout,
                    "max_login_attempts": max_login_attempts,
                    "api_rate_limit": api_rate_limit,
                    "enable_cors": enable_cors,
                    "api_key_rotation": api_key_rotation,
                    "require_https": require_https,
                    "enable_audit_log": enable_audit_log,
                    "log_retention_days": log_retention_days,
                    "enable_alerts": enable_alerts,
                    "alert_email": alert_email
                }
                
                try:
                    api_client.update_security_settings(security_config)
                    st.success("✅ Security settings saved successfully!")
                except Exception as e:
                    st.error(f"❌ Error saving security settings: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ Error loading security settings: {str(e)}")

def render_system_settings(api_client):
    """Render system settings and maintenance"""
    
    st.subheader("🚀 System Settings & Maintenance")
    
    # System status
    st.markdown("### 📊 System Status")
    
    try:
        with st.spinner("📊 Loading system status..."):
            system_status = api_client.get_system_status()
        
        col_status1, col_status2, col_status3, col_status4 = st.columns(4)
        
        with col_status1:
            st.metric("System Health", system_status.get("health", "Unknown"))
        
        with col_status2:
            st.metric("Uptime", system_status.get("uptime", "Unknown"))
        
        with col_status3:
            st.metric("Active Users", system_status.get("active_users", 0))
        
        with col_status4:
            st.metric("API Calls/Hour", system_status.get("api_calls_hour", 0))
        
    except Exception as e:
        st.warning(f"⚠️ Could not load system status: {str(e)}")
    
    # Maintenance actions
    st.markdown("### 🔧 Maintenance Actions")
    
    col_maint1, col_maint2, col_maint3 = st.columns(3)
    
    with col_maint1:
        if st.button("🧹 Clear Cache", key="clear_cache"):
            clear_system_cache(api_client)
    
    with col_maint2:
        if st.button("📊 Generate Report", key="system_report"):
            generate_system_report(api_client)
    
    with col_maint3:
        if st.button("💾 Backup Data", key="backup_data"):
            backup_system_data(api_client)
    
    # Database settings
    st.markdown("### 🗄️ Database Settings")
    
    with st.form("database_settings_form"):
        col_db1, col_db2 = st.columns(2)
        
        with col_db1:
            backup_frequency = st.selectbox("Backup Frequency", ["Daily", "Weekly", "Monthly"])
            auto_cleanup = st.checkbox("Auto Cleanup Old Data", value=True)
        
        with col_db2:
            retention_period = st.number_input("Data Retention (days)", min_value=30, max_value=1095, value=365)
            compression = st.checkbox("Enable Compression", value=True)
        
        if st.form_submit_button("💾 Save Database Settings"):
            db_settings = {
                "backup_frequency": backup_frequency,
                "auto_cleanup": auto_cleanup,
                "retention_period": retention_period,
                "compression": compression
            }
            
            try:
                api_client.update_database_settings(db_settings)
                st.success("✅ Database settings saved successfully!")
            except Exception as e:
                st.error(f"❌ Error saving database settings: {str(e)}")

# Helper functions
def show_add_user_form(api_client):
    """Show add new user form"""
    st.info("🚧 Add user form - coming soon!")

def show_user_analytics(api_client):
    """Show user analytics"""
    st.info("🚧 User analytics - coming soon!")

def show_bulk_user_actions(api_client):
    """Show bulk user actions"""
    st.info("🚧 Bulk user actions - coming soon!")

def render_users_table(users: List[Dict], api_client):
    """Render users management table"""
    st.info("🚧 Users table - coming soon!")

def configure_integration(api_client, integration: Dict):
    """Configure specific integration"""
    st.info(f"🚧 Configure {integration['name']} - coming soon!")

def clear_system_cache(api_client):
    """Clear system cache"""
    st.info("🚧 Clear cache - coming soon!")

def generate_system_report(api_client):
    """Generate system report"""
    st.info("🚧 Generate report - coming soon!")

def backup_system_data(api_client):
    """Backup system data"""
    st.info("🚧 Backup data - coming soon!")
