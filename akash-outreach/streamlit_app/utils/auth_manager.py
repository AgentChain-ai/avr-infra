"""
Authentication Manager for Streamlit application
"""

import requests
import streamlit as st
from typing import Tuple, Optional, Dict, Any

class AuthManager:
    """Handle authentication with FastAPI backend"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
    
    def login(self, username: str, password: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Attempt login with username and password
        Returns: (success, token, user_info)
        """
        try:
            # Make login request
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                user_info = {
                    "username": username,
                    "role": "admin"  # For now, all users are admin
                }
                return True, token, user_info
            elif response.status_code == 401:
                return False, None, None
            else:
                st.error(f"Login error: {response.status_code}")
                return False, None, None
                
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {str(e)}")
            return False, None, None
    
    def logout(self):
        """Clear session state and logout"""
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.session_state.api_client = None
        
        # Clear all session state
        for key in list(st.session_state.keys()):
            if key.startswith("page_"):
                del st.session_state[key]
    
    def verify_token(self, token: str) -> bool:
        """Verify if token is still valid"""
        try:
            response = requests.get(
                f"{self.base_url}/auth/verify",
                headers={"Authorization": f"Bearer {token}"}
            )
            return response.status_code == 200
        except:
            return False
