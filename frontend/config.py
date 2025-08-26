# frontend/config.py
from pathlib import Path

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Project Configuration
PROJECT_ROOT = Path(__file__).parent.parent
TMP_DIR = PROJECT_ROOT / "tmp"

# Timing Configuration
MAX_WAIT_TIME = 120  # 2 minutes
POLL_INTERVAL = 2    # 2 seconds

# Session State Keys
SESSION_KEYS = [
    'job_id',
    'job_status',
    'job_result',
    'start_time',
    'extended_wait',
    'form_data',
    'show_results',
    'image_status'
]

# Custom CSS for styling
CUSTOM_CSS = """
<style>
    /* Main container styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    /* Card styling */
    .post-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #e9ecef;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div > div {
        background-color: #1f77b4;
        border-radius: 10px;
    }
    
    /* Status message styling */
    .status-info {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    
    /* Image container styling */
    .image-container {
        position: relative;
        border-radius: 8px;
        overflow: hidden;
        background-color: #f5f5f5;
    }
    
    /* Loading animation */
    @keyframes pulse {
        0% { opacity: 0.6; }
        50% { opacity: 1; }
        100% { opacity: 0.6; }
    }
    
    .loading-pulse {
        animation: pulse 2s infinite;
    }
    
    /* Success message styling */
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
    }
    
    /* Error message styling */
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
    }
    
    /* Hashtag styling */
    .hashtag {
        display: inline-block;
        background-color: #e9ecef;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        margin: 0.25rem;
        font-size: 0.9rem;
        color: #495057;
    }
</style>
"""