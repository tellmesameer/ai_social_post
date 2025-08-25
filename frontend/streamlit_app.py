# frontend/streamlit_app.py
import streamlit as st
from pathlib import Path
import sys

# Add the frontend directory to Python path
frontend_dir = Path(__file__).parent
sys.path.append(str(frontend_dir))

# Import pages
from pages.home import render_home_page
from pages.preview import render_preview_page

def main():
    """Main Streamlit application."""
    
    # Page configuration
    st.set_page_config(
        page_title="AI Social Post Generator",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🚀 AI Social Post Generator")
        st.markdown("---")
        
        # Navigation
        page = st.selectbox(
            "Choose a page:",
            ["🏠 Home", "📊 Preview"],
            index=0
        )
        
        st.markdown("---")
        
        # App information
        st.header("ℹ️ About")
        st.markdown("""
        **AI Social Post Generator** is a powerful tool that:
        
        • **Scrapes articles** from any URL
        • **Generates summaries** using AI
        • **Creates post variants** with LangChain
        • **Generates images** with AI models
        • **Moderates content** for safety
        • **Publishes to LinkedIn** seamlessly
        """)
        
        st.markdown("---")
        
        # Technology stack
        st.header("🔧 Tech Stack")
        st.markdown("""
        **Frontend:** Streamlit
        **Backend:** FastAPI
        **AI:** LangChain + Vertex AI/OpenAI
        **Database:** SQLite
        **Image Gen:** Vertex Imagen/DALL-E
        """)
        
        st.markdown("---")
        
        # Quick actions
        st.header("⚡ Quick Actions")
        
        if st.button("🔄 Refresh App", use_container_width=True):
            st.rerun()
        
        if st.button("📋 View API Docs", use_container_width=True):
            st.info("API documentation available at: http://localhost:8000/docs")
        
        if st.button("🏥 Health Check", use_container_width=True):
            try:
                from api_client import get_api_client
                api_client = get_api_client()
                if api_client.health_check():
                    st.success("✅ Backend API is healthy")
                else:
                    st.error("❌ Backend API is not responding")
            except Exception as e:
                st.error(f"❌ Health check failed: {e}")
    
    # Main content area
    if page == "🏠 Home":
        render_home_page()
    elif page == "📊 Preview":
        render_preview_page()
    else:
        st.error("Invalid page selection")

if __name__ == "__main__":
    main()
