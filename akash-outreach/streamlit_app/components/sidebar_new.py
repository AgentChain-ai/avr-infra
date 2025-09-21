"""
Modern Sidebar navigation component for Streamlit application
"""

import streamlit as st

def render_sidebar() -> str:
    """
    Render beautiful sidebar navigation and return selected page
    """
    
    with st.sidebar:
        # Hide Streamlit's default navigation and add modern styling
        st.markdown("""
        <style>
        /* Hide default Streamlit navigation */
        .css-1d391kg, .css-1v3fvcr, .css-1vq4p4l {
            display: none !important;
        }
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
        .css-17lntkn {
            display: none !important;
        }
        
        /* Modern sidebar styling */
        .sidebar-header {
            text-align: center;
            padding: 25px 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: -1rem -1rem 2rem -1rem;
            border-radius: 0 0 20px 20px;
            color: white;
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
        }
        
        .sidebar-section {
            margin: 25px 0;
            padding: 20px 15px;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 12px;
            border-left: 4px solid #667eea;
            backdrop-filter: blur(10px);
        }
        
        /* Custom metric styling */
        .metric-card {
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            border: 1px solid rgba(102, 126, 234, 0.2);
        }
        
        .metric-title {
            font-size: 12px;
            color: #666;
            margin: 0;
        }
        
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #333;
            margin: 5px 0 0 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Beautiful header
        st.markdown("""
        <div class="sidebar-header">
            <h2 style="margin: 0; font-size: 28px; font-weight: 600;">📞 Akash Outreach</h2>
            <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 14px; font-weight: 300;">Admin Dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Modern Navigation
        st.markdown("### 🧭 Navigation")
        
        # Define pages
        pages = [
            ("📊", "Dashboard", "Dashboard"),
            ("👥", "Students", "Students"), 
            ("📞", "Calls", "Calls"),
            ("🎯", "Campaigns", "Campaigns"),
            ("📈", "Analytics", "Analytics"),
            ("⚙️", "Fields", "Fields"),
            ("🤖", "AI Context", "Context"),
            ("⚙️", "Settings", "Settings")
        ]
        
        # Initialize selected page
        if "selected_page" not in st.session_state:
            st.session_state.selected_page = "Dashboard"
        
        # Create beautiful navigation buttons
        for icon, label, page_value in pages:
            # Create button with custom styling
            button_style = """
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 16px;
            border-radius: 10px;
            font-weight: 500;
            margin: 5px 0;
            transition: all 0.3s ease;
            box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
            """
            
            if st.session_state.selected_page == page_value:
                button_style = """
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                color: white;
                border: none;
                padding: 12px 16px;
                border-radius: 10px;
                font-weight: 600;
                margin: 5px 0;
                box-shadow: 0 4px 16px rgba(79, 172, 254, 0.4);
                """
            
            if st.button(f"{icon} {label}", key=f"nav_{page_value}", use_container_width=True, help=f"Navigate to {label}"):
                st.session_state.selected_page = page_value
                st.rerun()
        
        st.divider()
        
        # Quick Actions Section
        st.markdown("### ⚡ Quick Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("➕ Add Student", use_container_width=True, key="quick_add_student", type="secondary"):
                st.session_state.show_add_student_modal = True
        
        with col2:
            if st.button("📁 Upload CSV", use_container_width=True, key="quick_upload_csv", type="secondary"):
                st.session_state.show_upload_modal = True
        
        # System Stats Section
        st.divider()
        st.markdown("### 📊 System Stats")
        
        # Get stats if API client available
        if st.session_state.get("api_client"):
            try:
                metrics = st.session_state.api_client.get_dashboard_metrics()
                
                # Display metrics with beautiful cards
                st.markdown(f"""
                <div class="metric-card">
                    <p class="metric-title">Total Students</p>
                    <p class="metric-value">{metrics.get("total_students", "N/A")}</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="metric-card">
                    <p class="metric-title">Total Calls</p>
                    <p class="metric-value">{metrics.get("total_calls", "N/A")}</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="metric-card">
                    <p class="metric-title">Completion Rate</p>
                    <p class="metric-value">{metrics.get("completion_rate", 0):.1f}%</p>
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"⚠️ API Error: {str(e)[:30]}...")
        else:
            st.info("🔌 Connect to view stats")
        
        # Footer
        st.divider()
        st.markdown("""
        <div style="text-align: center; font-size: 12px; color: #666; padding: 15px 0;">
            <p style="margin: 0;"><strong>Akash Institute</strong></p>
            <p style="margin: 0; opacity: 0.7;">Outreach System v2.0</p>
        </div>
        """, unsafe_allow_html=True)
    
    return st.session_state.selected_page
