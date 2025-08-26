# frontend/main.py
import streamlit as st
import time
from typing import Dict, Any, Optional
from api_client import APIClient
from ui_components import (
    apply_custom_styles, 
    render_form, 
    render_loading_screen, 
    render_results, 
    reset_session
)
from config import SESSION_KEYS, POLL_INTERVAL, MAX_WAIT_TIME


# Set page configuration - this must be the first Streamlit command
st.set_page_config(
    page_title="AI Social Post Generator",
    page_icon="🚀",
    layout=None,
    initial_sidebar_state="collapsed"
)

def initialize_session_state():
    """Initialize session state variables."""
    for key in SESSION_KEYS:
        if key not in st.session_state:
            st.session_state[key] = None

def main():
    """Main application logic."""
    # Apply custom styles
    apply_custom_styles()
    
    # Initialize session state
    initialize_session_state()
    
    # Check if we have an active job
    if st.session_state.job_id and not st.session_state.show_results:
        # We're in the loading phase
        job_id = st.session_state.job_id
        
        # Initialize start time if not set
        if not st.session_state.start_time:
            st.session_state.start_time = time.time()
        
        # Calculate elapsed time
        elapsed_time = int(time.time() - st.session_state.start_time)
        
        # Check if we should extend the wait time
        max_wait = MAX_WAIT_TIME + (60 if st.session_state.extended_wait else 0)
        
        if elapsed_time < max_wait and not st.session_state.job_result:
            # Still waiting, poll the job status
            status_response = APIClient.get_job_status(job_id)
            
            if status_response:
                job_status = status_response.get("status")
                st.session_state.job_status = job_status
                
                if job_status == "completed":
                    st.session_state.job_result = status_response.get("result", {})
                    st.session_state.show_results = True
                    st.rerun()
                elif job_status in ["failed", "cancelled"]:
                    st.markdown('<div class="error-message">Job failed. Please try again.</div>', unsafe_allow_html=True)
                    if st.button("Start Over"):
                        reset_session()
                        st.rerun()
                else:
                    # Still processing
                    render_loading_screen(job_status or "unknown", elapsed_time)
                    time.sleep(POLL_INTERVAL)
                    st.rerun()
            else:
                st.markdown('<div class="error-message">Failed to get job status</div>', unsafe_allow_html=True)
                if st.button("Start Over"):
                    reset_session()
                    st.rerun()
        else:
            # Either we have results or we've exceeded the wait time
            if st.session_state.job_result:
                st.session_state.show_results = True
                st.rerun()
            else:
                st.markdown('<div class="error-message">Job is taking longer than expected. Please try again later.</div>', unsafe_allow_html=True)
                if st.button("Start Over"):
                    reset_session()
                    st.rerun()
    elif st.session_state.show_results and st.session_state.job_result:
        # Show the results
        render_results(st.session_state.job_result, st.session_state.job_id)
        
        # Add a "Create New Post" button with custom styling
        st.markdown("---")
        if st.button("🆕 Create New Post", type="primary", use_container_width=True):
            reset_session()
            st.rerun()
    else:
        # Show the form
        form_data = render_form()
        
        if form_data:
            # Submit the job
            with st.spinner("Creating your job..."):
                job_id = APIClient.create_job(
                    url=form_data["url"],
                    opinion=form_data["opinion"],
                    tone=form_data["tone"],
                    image_options=form_data["image_options"]
                )
                
                if job_id:
                    st.markdown('<div class="success-message">Job created successfully!</div>', unsafe_allow_html=True)
                    st.session_state.job_id = job_id
                    st.session_state.form_data = form_data
                    st.rerun()
                else:
                    st.markdown('<div class="error-message">Failed to create job. Please try again.</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()