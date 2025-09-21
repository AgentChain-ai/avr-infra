"""
Sidebar navigation component for Streamlit application
"""

import streamlit as st

def render_sidebar() -> str:
    """
    Render sidebar navigation and return selected page
    """
    
    with st.sidebar:
        # Hide Streamlit's default navigation and add custom styling
        st.markdown("""
        <style>
        .css-1d391kg, .css-1v3fvcr, .css-1vq4p4l {
            display: none !important;
        }
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
        .css-17lntkn {
            display: none !important;
        }
        
        /* Custom navigation button styling */
        .nav-button {
            display: block;
            width: 100%;
            padding: 12px 16px;
            margin: 4px 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            border: none;
            font-weight: 500;
            text-align: left;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .nav-button:hover {
            transform: translateX(4px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        
        .nav-button.active {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            box-shadow: 0 4px 16px rgba(79, 172, 254, 0.4);
        }
        
        /* Sidebar styling */
        .sidebar-header {
            text-align: center;
            padding: 20px 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: -1rem -1rem 2rem -1rem;
            border-radius: 0 0 15px 15px;
            color: white;
        }
        
        .sidebar-section {
            margin: 20px 0;
            padding: 15px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Logo and title with better styling
        st.markdown("""
        <div class="sidebar-header">
            <h2 style="margin: 0; font-size: 24px;">📞 Akash Outreach</h2>
            <p style="margin: 5px 0 0 0; opacity: 0.9; font-size: 14px;">Admin Dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Navigation menu
        st.markdown("### 📋 Navigation")
        
        # Main pages with better organization
        pages = {
            "📊 Dashboard": "Dashboard",
            "👥 Students": "Students", 
            "📞 Calls": "Calls",
            "🎯 Campaigns": "Campaigns",
            "� Analytics": "Analytics",
            "⚙️ Fields": "Fields",
            "🤖 AI Context": "Context",
            "⚙️ Settings": "Settings"
        }
        
        # Use radio buttons for navigation with better styling
        selected_display = st.radio(
            "Navigate to:",
            options=list(pages.keys()),
            key="navigation_radio",
            label_visibility="collapsed"
        )
        
        selected_page = pages[selected_display]
        
        st.divider()
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("➕ Add Student", use_container_width=True, key="quick_add_student"):
                st.session_state.show_add_student_modal = True
        
        with col2:
            if st.button("📁 Upload CSV", use_container_width=True, key="quick_upload_csv"):
                st.session_state.show_upload_modal = True
        
        # System information
        st.divider()
        st.subheader("💾 System Info")
        
        # Get basic stats if API client available
        if st.session_state.get("api_client"):
            try:
                metrics = st.session_state.api_client.get_dashboard_metrics()
                
                st.metric(
                    "Total Students", 
                    metrics.get("total_students", "N/A")
                )
                st.metric(
                    "Pending Calls", 
                    metrics.get("pending_calls", "N/A")
                )
                st.metric(
                    "Calls Today", 
                    metrics.get("calls_today", "N/A")
                )
                
            except Exception as e:
                st.error(f"⚠️ API Error: {str(e)[:50]}...")
        else:
            st.info("🔌 Connect to view stats")
        
        # Footer
        st.divider()
        st.markdown("""
        <div style="text-align: center; font-size: 12px; color: #666;">
            <p>Akash Institute<br>Outreach System v1.0</p>
        </div>
        """, unsafe_allow_html=True)
    
    return selected_page
