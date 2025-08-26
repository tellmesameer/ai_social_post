# frontend/api_client.py

# Third-party imports
import requests
import streamlit as st

# Typing imports
from typing import Dict, Any, Optional

# Local application imports
from config import API_BASE_URL

class APIClient:
    """Client for communicating with the AI Social Post Generator API."""
    
    @staticmethod
    def create_job(url: str, opinion: str, tone: str, image_options: Dict[str, Any]) -> Optional[str]:
        """Create a new job and return job_id."""
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/v1/posts",
                json={
                    "url": url,
                    "opinion": opinion,
                    "tone": tone,
                    "image_options": image_options
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json().get("job_id")
        except Exception as e:
            st.error(f"Error creating job: {e}")
            return None
    
    @staticmethod
    def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
        """Get the status and result of a job."""
        try:
            response = requests.get(f"{API_BASE_URL}/api/v1/posts/{job_id}", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Error getting job status: {e}")
            return None
    
    @staticmethod
    def regenerate_content(job_id: str, regenerate_type: str, variant: str) -> bool:
        """Regenerate specific content for a variant."""
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/v1/posts/{job_id}/regenerate",
                json={
                    "regenerate": regenerate_type,
                    "variant": variant
                },
                timeout=10
            )
            response.raise_for_status()
            return True
        except Exception as e:
            st.error(f"Error regenerating content: {e}")
            return False
    
    @staticmethod
    def publish_post(job_id: str, variant: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Publish a post variant to LinkedIn."""
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/v1/posts/{job_id}/publish",
                json={
                    "variant": variant,
                    "user_id": user_id
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Error publishing post: {e}")
            return None