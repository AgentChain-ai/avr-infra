"""
Header component for Streamlit application
"""

import streamlit as st
from datetime import datetime

def render_header():
    """Render the application header"""
    
    # Main header
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("""
        <div style="display: flex; align-items: center;">
            <h1 style="margin: 0; color: #1f77b4;">📞 Akash Institute</h1>
            <span style="margin-left: 20px; color: #666; font-size: 18px;">Outreach System</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.session_state.get("user_info"):
            st.markdown(f"""
            <div style="text-align: right; padding-top: 10px;">
                <small style="color: #666;">Welcome back,</small><br>
                <strong>{st.session_state.user_info.get('username', 'Admin')}</strong>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        # Logout button
        if st.button("🚪 Logout", key="header_logout"):
            from utils.auth_manager import AuthManager
            auth_manager = AuthManager()
            auth_manager.logout()
            st.rerun()
    
    # Add a divider
    st.divider()
    
    # Status bar
    col_status1, col_status2, col_status3, col_status4 = st.columns(4)
    
    with col_status1:
        # API connection status
        if st.session_state.get("api_client"):
            if st.session_state.api_client.verify_token():
                st.success("🟢 API Connected", icon="✅")
            else:
                st.error("🔴 API Disconnected", icon="❌")
        else:
            st.warning("🟡 No API Client", icon="⚠️")
    
    with col_status2:
        # Current time
        current_time = datetime.now().strftime("%H:%M:%S")
        st.info(f"🕐 {current_time}", icon="ℹ️")
    
    with col_status3:
        # System status placeholder
        st.info("🟢 System Online", icon="💻")
    
    with col_status4:
        # Auto-refresh toggle
        auto_refresh = st.checkbox("🔄 Auto Refresh", key="auto_refresh_header")
        
        if auto_refresh:
            # Auto refresh every 30 seconds
            import time
            time.sleep(30)
            st.rerun()
