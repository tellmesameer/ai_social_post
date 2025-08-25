# frontend/api_client.py
import requests
import json
import streamlit as st
from typing import Dict, Any, Optional


class APIClient:
    """Client for communicating with the AI Social Post Generator API."""
    
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api/v1"
    
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a request to the API."""
        url = f"{self.api_base}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {e}")
            return {"error": str(e)}
        except json.JSONDecodeError as e:
            st.error(f"Failed to parse API response: {e}")
            return {"error": "Invalid JSON response"}
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            return {"error": str(e)}
    
    
    def create_post(self, url: str, opinion: str, tone: str, image_options: Dict[str, Any]) -> Optional[str]:
        """Create a new post generation job."""
        data = {
            "url": url,
            "opinion": opinion,
            "tone": tone,
            "image_options": image_options
        }
        
        response = self._make_request("POST", "/posts", data)
        
        if "error" in response:
            return None
        
        return response.get("job_id")
    
    
    def get_post_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the status and result of a post generation job."""
        response = self._make_request("GET", f"/posts/{job_id}")
        
        if "error" in response:
            return None
        
        return response
    
    
    def regenerate_content(self, job_id: str, regenerate_type: str, variant: str) -> bool:
        """Regenerate specific content for a post variant."""
        data = {
            "regenerate": regenerate_type,
            "variant": variant
        }
        
        response = self._make_request("POST", f"/posts/{job_id}/regenerate", data)
        
        return "error" not in response
    
    
    def publish_post(self, job_id: str, variant: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Publish a post variant to LinkedIn."""
        data = {
            "variant": variant,
            "user_id": user_id
        }
        
        response = self._make_request("POST", f"/posts/{job_id}/publish", data)
        
        if "error" in response:
            return None
        
        return response
    
    
    def health_check(self) -> bool:
        """Check if the API is healthy."""
        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

# Global API client instance
@st.cache_resource
def get_api_client() -> APIClient:
    """Get cached API client instance."""
    return APIClient()
