"""
Akash Institute Outreach System - Streamlit Admin Dashboard
Main application entry point with multi-page navigation
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add the parent directory to Python path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from utils.api_client import APIClient
from utils.auth_manager import AuthManager
from components.sidebar import render_sidebar
from components.header import render_header

def main():
    """Main Streamlit application"""
    
    # Page configuration
    st.set_page_config(
        page_title="Akash Institute - Outreach System",
        page_icon="📞",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "api_client" not in st.session_state:
        st.session_state.api_client = None
    
    # Authentication check
    auth_manager = AuthManager()
    
    if not st.session_state.authenticated:
        # Show login page
        show_login_page(auth_manager)
    else:
        # Show main application
        show_main_app()

def show_login_page(auth_manager):
    """Display login page"""
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 50px 0;">
            <h1>📞 Akash Institute</h1>
            <h3>Outreach System</h3>
            <p style="color: #666;">Admin Dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Login form
        with st.form("login_form"):
            st.subheader("🔐 Admin Login")
            
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col_login1, col_login2, col_login3 = st.columns([1, 2, 1])
            with col_login2:
                submit_button = st.form_submit_button("Login", use_container_width=True)
            
            if submit_button:
                if username and password:
                    success, token, user_info = auth_manager.login(username, password)
                    
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user_info = user_info
                        st.session_state.api_client = APIClient(token)
                        st.success("✅ Login successful! Redirecting...")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                else:
                    st.warning("⚠️ Please enter both username and password")

def show_main_app():
    """Display main application with navigation"""
    
    # Render header
    render_header()
    
    # Render sidebar navigation
    selected_page = render_sidebar()
    
    # Route to selected page
    if selected_page == "Dashboard":
        from pages.dashboard import show_dashboard
        show_dashboard()
    elif selected_page == "Students":
        from pages.students import show_students
        show_students()
    elif selected_page == "Campaigns":
        from pages.campaigns import show_campaigns
        show_campaigns()
    elif selected_page == "Calls":
        from pages.calls import show_calls
        show_calls()
    elif selected_page == "Fields":
        from pages.fields import show_fields
        show_fields()
    elif selected_page == "Context":
        from pages.context import show_context
        show_context()
    elif selected_page == "Analytics":
        from pages.analytics import show_analytics
        show_analytics()
    elif selected_page == "Settings":
        from pages.settings import show_settings
        show_settings()

if __name__ == "__main__":
    main()
