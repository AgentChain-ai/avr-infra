"""
API Client for communicating with FastAPI backend
"""

import requests
import streamlit as st
import os
from typing import Dict, Any, Optional, List
import json

class APIClient:
    """Client for making authenticated requests to the FastAPI backend"""
    
    def __init__(self, token: str, base_url: str = None):
        if base_url is None:
            # Use environment variable or default to localhost for local development
            base_url = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
        self.token = token
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        # Create a session for persistent connections
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            if response.status_code == 401:
                st.error("❌ Session expired. Please login again.")
                st.session_state.authenticated = False
                st.rerun()
            
            if response.status_code >= 400:
                try:
                    error_detail = response.json().get("detail", "Unknown error")
                except Exception:
                    error_detail = response.text or f"HTTP {response.status_code} error"
                
                # Enhance error message for better debugging
                if response.status_code == 400:
                    error_msg = f"Bad Request: {error_detail}"
                elif response.status_code == 422:
                    error_msg = f"Validation Error: {error_detail}"
                else:
                    error_msg = f"HTTP {response.status_code}: {error_detail}"
                
                raise Exception(error_msg)
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Network error: {str(e)}")
            raise e
    
    # Authentication
    def verify_token(self) -> bool:
        """Verify if token is still valid"""
        try:
            self._make_request("GET", "/auth/me")
            return True
        except Exception:
            return False
    
    # Student methods
    def get_students(self, limit: int = 100, **filters) -> dict:
        """Get paginated list of students with optional filters"""
        params = {"limit": limit}
        params.update(filters)
        response = self.session.get(f"{self.base_url}/students", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_student(self, student_id: int) -> dict:
        """Get specific student by ID"""
        response = self.session.get(f"{self.base_url}/students/{student_id}")
        response.raise_for_status()
        return response.json()
    
    def create_student(self, student_data: dict) -> dict:
        """Create new student"""
        return self._make_request("POST", "/students/", json=student_data)
    
    def update_student(self, student_id: int, student_data: dict) -> dict:
        """Update existing student"""
        return self._make_request("PUT", f"/students/{student_id}", json=student_data)
    
    def delete_student(self, student_id: int) -> bool:
        """Delete student"""
        self._make_request("DELETE", f"/students/{student_id}")
        return True
    
    def search_students(self, query: str, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Search students"""
        params = {"q": query, "skip": skip, "limit": limit}
        return self._make_request("GET", "/students/search", params=params)
    
    def get_student_analytics(self) -> dict:
        """Get student analytics and statistics"""
        try:
            response = self.session.get(f"{self.base_url}/students/analytics")
            response.raise_for_status()
            return response.json()
        except Exception:
            # Fallback to getting basic stats from students list
            students = self.get_students(limit=1000)
            students_list = students.get("students", [])
            
            # Calculate basic analytics
            total = len(students_list)
            by_status = {}
            
            for student in students_list:
                status = student.get("call_status", "pending")
                by_status[status] = by_status.get(status, 0) + 1
            
            return {
                "total_students": total,
                "students_by_status": by_status
            }
    
    def bulk_update_students(self, student_ids: list, update_data: dict) -> dict:
        """Bulk update multiple students"""
        response = self.session.patch(
            f"{self.base_url}/students/bulk", 
            json={"student_ids": student_ids, "update_data": update_data}
        )
        response.raise_for_status()
        return response.json()
    
    def bulk_delete_students(self, student_ids: list) -> dict:
        """Bulk delete multiple students"""
        response = self.session.delete(
            f"{self.base_url}/students/bulk", 
            json={"student_ids": student_ids}
        )
        response.raise_for_status()
        return response.json()
    
    def upload_students_csv(self, file_content: bytes, field_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Upload students CSV with field mapping"""
        files = {"file": file_content}
        data = {"field_mapping": json.dumps(field_mapping)}
        # Remove Content-Type header for file upload
        headers = {"Authorization": f"Bearer {self.token}"}
        
        url = f"{self.base_url}/students/upload-csv"
        response = requests.post(url, headers=headers, files=files, data=data)
        
        if response.status_code >= 400:
            error_detail = response.json().get("detail", "Unknown error")
            raise Exception(f"Upload Error ({response.status_code}): {error_detail}")
        
        return response.json()
    
    # Fields API
    def get_fields(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Get field configurations"""
        params = {"include_inactive": include_inactive}
        return self._make_request("GET", "/fields", params=params)
    
    def create_field(self, field_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create field configuration"""
        return self._make_request("POST", "/fields", json=field_data)
    
    def update_field(self, field_id: int, field_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update field configuration"""
        return self._make_request("PUT", f"/fields/{field_id}", json=field_data)
    
    def delete_field(self, field_id: int) -> bool:
        """Delete field configuration"""
        try:
            self._make_request("DELETE", f"/fields/{field_id}")
            return True
        except Exception:
            return False
    
    def get_field_types(self) -> List[str]:
        """Get available field types"""
        return self._make_request("GET", "/fields/types/available")
    
    # Context Notes API
    def get_context_notes(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Get context notes"""
        params = {"include_inactive": include_inactive}
        return self._make_request("GET", "/context/context-notes", params=params)
    
    def create_context_note(self, note_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create context note"""
        return self._make_request("POST", "/context/context-notes", json=note_data)
    
    def update_context_note(self, note_id: int, note_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update context note"""
        return self._make_request("PUT", f"/context/context-notes/{note_id}", json=note_data)
    
    def delete_context_note(self, note_id: int) -> bool:
        """Delete context note"""
        try:
            self._make_request("DELETE", f"/context/context-notes/{note_id}")
            return True
        except Exception:
            return False
    
    def construct_context(self, student_id: int, campaign_id: int) -> Dict[str, Any]:
        """Construct natural language context for student and campaign"""
        return self._make_request("POST", "/context/construct", json={
            "student_id": student_id,
            "campaign_id": campaign_id
        })
    
    def preview_context(self, student_data: Dict[str, Any], context_note_ids: List[int]) -> Dict[str, Any]:
        """Preview context construction"""
        return self._make_request("POST", "/context/preview", json={
            "student_data": student_data,
            "context_note_ids": context_note_ids
        })
    
    # Context Category API
    def get_context_categories(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Get context categories"""
        params = {"include_inactive": include_inactive}
        return self._make_request("GET", "/context/categories", params=params)
    
    def create_context_category(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create context category"""
        return self._make_request("POST", "/context/categories", json=category_data)
    
    def update_context_category(self, category_id: int, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update context category"""
        return self._make_request("PUT", f"/context/categories/{category_id}", json=category_data)
    
    def delete_context_category(self, category_id: int) -> bool:
        """Delete context category"""
        try:
            self._make_request("DELETE", f"/context/categories/{category_id}")
            return True
        except Exception:
            return False

    # Calls API
    def get_calls(self, skip: int = 0, limit: int = 100, **filters) -> Dict[str, Any]:
        """Get call logs with pagination and filters"""
        params = {"skip": skip, "limit": limit, **filters}
        return self._make_request("GET", "/calls", params=params)
    
    def create_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create call log"""
        return self._make_request("POST", "/calls", json=call_data)
    
    def update_call(self, call_id: int, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update call log"""
        return self._make_request("PUT", f"/calls/{call_id}", json=call_data)
    
    # Call Management API
    def get_call_queue(self, priority_min: Optional[int] = None) -> Dict[str, Any]:
        """Get call queue with students ready to be called"""
        params = {}
        if priority_min:
            params["priority_min"] = priority_min
        return self._make_request("GET", "/calls/queue", params=params)
    
    def get_active_calls(self) -> List[Dict[str, Any]]:
        """Get currently active calls"""
        return self._make_request("GET", "/calls/active")
    
    def start_calling_queue(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Start calling from queue"""
        params = {"limit": limit} if limit else {}
        return self._make_request("POST", "/calls/queue/start", params=params)
    
    def get_call_history(self, date_from: Optional[str] = None, date_to: Optional[str] = None, 
                        status: Optional[str] = None, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get call history with filters"""
        params = {"skip": skip, "limit": limit}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if status:
            params["status"] = status
        return self._make_request("GET", "/calls/history", params=params)
    
    def end_call(self, call_id: int, outcome: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """End an active call"""
        data = {"outcome": outcome}
        if notes:
            data["notes"] = notes
        return self._make_request("POST", f"/calls/{call_id}/end", json=data)
    
    def update_call_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update call management settings"""
        return self._make_request("PUT", "/calls/settings", json=settings)
    
    def get_call_settings(self) -> Dict[str, Any]:
        """Get call management settings"""
        return self._make_request("GET", "/calls/settings")
    
    # Campaign Management API
    def get_campaigns(self, status: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get campaigns with optional status filter"""
        params = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status
        return self._make_request("GET", "/campaigns", params=params)
    
    def get_campaign(self, campaign_id: int) -> Dict[str, Any]:
        """Get specific campaign details"""
        return self._make_request("GET", f"/campaigns/{campaign_id}")
    
    def create_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new campaign"""
        return self._make_request("POST", "/campaigns", json=campaign_data)
    
    def update_campaign(self, campaign_id: int, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update campaign"""
        return self._make_request("PUT", f"/campaigns/{campaign_id}", json=campaign_data)
    
    def delete_campaign(self, campaign_id: int) -> bool:
        """Delete campaign"""
        try:
            self._make_request("DELETE", f"/campaigns/{campaign_id}")
            return True
        except Exception:
            return False
    
    def pause_campaign(self, campaign_id: int) -> Dict[str, Any]:
        """Pause campaign"""
        return self._make_request("POST", f"/campaigns/{campaign_id}/pause")
    
    def resume_campaign(self, campaign_id: int) -> Dict[str, Any]:
        """Resume campaign"""
        return self._make_request("POST", f"/campaigns/{campaign_id}/resume")
    
    def get_campaign_analytics(self, campaign_id: Optional[int] = None) -> Dict[str, Any]:
        """Get campaign analytics"""
        if campaign_id:
            return self._make_request("GET", f"/campaigns/{campaign_id}/analytics")
        else:
            return self._make_request("GET", "/campaigns/analytics/summary")
    
    def get_campaign_contexts(self, campaign_id: int) -> Dict[str, Any]:
        """Get personalized contexts for campaign"""
        return self._make_request("GET", f"/campaigns/{campaign_id}/contexts")
    
    def regenerate_contexts(self, campaign_id: int) -> Dict[str, Any]:
        """Regenerate personalized contexts for campaign"""
        return self._make_request("POST", f"/campaigns/{campaign_id}/regenerate-contexts")
    
    def activate_campaign(self, campaign_id: int) -> Dict[str, Any]:
        """Activate campaign to start calling"""
        return self._make_request("POST", f"/campaigns/{campaign_id}/activate")
    
    def update_student_context(self, campaign_id: int, student_id: int, context: str) -> Dict[str, Any]:
        """Update personalized context for a specific student in a campaign"""
        context_data = {"context": context}
        return self._make_request("PUT", f"/campaigns/{campaign_id}/contexts/{student_id}", json=context_data)
    
    # Settings & Configuration API
    def get_system_settings(self) -> Dict[str, Any]:
        """Get system settings"""
        return self._make_request("GET", "/settings/system")
    
    def update_system_settings(self, category: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update system settings by category"""
        return self._make_request("PUT", f"/settings/system/{category}", json=settings)
    
    def get_security_settings(self) -> Dict[str, Any]:
        """Get security settings"""
        return self._make_request("GET", "/settings/security")
    
    def update_security_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update security settings"""
        return self._make_request("PUT", "/settings/security", json=settings)
    
    def get_users(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get users list"""
        params = {"skip": skip, "limit": limit}
        return self._make_request("GET", "/users", params=params)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status and health"""
        return self._make_request("GET", "/system/status")
    
    def update_database_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update database settings"""
        return self._make_request("PUT", "/settings/database", json=settings)
    
    # Context API
    def get_context_info(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get context information"""
        params = {"category": category} if category else {}
        return self._make_request("GET", "/context", params=params)
    
    def create_context(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create context information"""
        return self._make_request("POST", "/context", json=context_data)
    
    def update_context(self, context_id: int, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update context information"""
        return self._make_request("PUT", f"/context/{context_id}", json=context_data)
    
    def chat_with_ai(self, message: str) -> Dict[str, Any]:
        """Chat with AI context agent"""
        return self._make_request("POST", "/context/chat", json={"message": message})
    
    # Analytics API
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get dashboard analytics"""
        return self._make_request("GET", "/analytics/summary")
    
    def get_call_analytics(self) -> Dict[str, Any]:
        """Get call analytics"""
        return self._make_request("GET", "/analytics/calls/metrics")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self._make_request("GET", "/analytics/performance/hourly")
    
    def get_trends_analytics(self) -> Dict[str, Any]:
        """Get trends and daily activity analytics"""
        return self._make_request("GET", "/analytics/trends")
