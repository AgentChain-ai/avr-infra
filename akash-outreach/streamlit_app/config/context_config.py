"""
Configuration file for Context Management
Database-backed dynamic categories and settings
"""

import streamlit as st
from typing import List, Dict

# Priority Levels Configuration
PRIORITY_LEVELS = {
    "Low": 1,
    "Medium": 5,
    "High": 8,
    "Critical": 10
}

# Default Settings
DEFAULT_PRIORITY = 5
DEFAULT_ACTIVE_STATUS = True

def get_context_categories() -> List[str]:
    """Get list of available context categories from database"""
    try:
        if "api_client" in st.session_state and st.session_state.api_client:
            api_client = st.session_state.api_client
            categories = api_client.get_context_categories()
            return [cat["name"] for cat in categories if cat.get("is_active", True)]
        else:
            # Fallback to basic categories if no API client
            return [
                "About Institution",
                "About ANTHE", 
                "Scholarship Information",
                "Program Details",
                "Next Steps",
                "Other"
            ]
    except Exception as e:
        # Fallback if API fails
        return [
            "About Institution",
            "About ANTHE", 
            "Scholarship Information", 
            "Program Details",
            "Next Steps",
            "Other"
        ]

def get_context_categories_with_details() -> List[Dict]:
    """Get full category details from database"""
    try:
        if "api_client" in st.session_state and st.session_state.api_client:
            api_client = st.session_state.api_client
            return api_client.get_context_categories()
        else:
            return []
    except Exception:
        return []

def get_priority_levels():
    """Get priority level mappings"""
    return PRIORITY_LEVELS

def get_category_color(category: str) -> str:
    """Get color for a specific category from database"""
    try:
        if "api_client" in st.session_state and st.session_state.api_client:
            api_client = st.session_state.api_client
            categories = api_client.get_context_categories()
            for cat in categories:
                if cat["name"] == category:
                    return cat.get("color", "#607d8b")
        return "#607d8b"
    except Exception:
        return "#607d8b"
