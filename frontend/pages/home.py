# frontend/pages/home.py
import streamlit as st
from components.post_form import render_post_form, render_form_preview
from api_client import get_api_client

def render_home_page():
    """Render the home page with post creation form."""
    
    st.set_page_config(
        page_title="AI Social Post Generator - Home",
        page_icon="🚀",
        layout="wide"
    )
    
    # Page header
    st.title("🚀 AI Social Post Generator")
    st.markdown("Transform any article into engaging LinkedIn posts with AI-generated images")
    
    # Check API health
    api_client = get_api_client()
    if not api_client.health_check():
        st.error("⚠️ Backend API is not accessible. Please ensure the backend is running.")
        st.info("Start the backend with: `uvicorn backend.main:app --reload --port 8000`")
        return
    
    # Sidebar with information
    with st.sidebar:
        st.header("ℹ️ How It Works")
        st.markdown("""
        1. **Enter Article URL** - Paste the link to any article
        2. **Share Your Opinion** - Agree, disagree, or provide custom thoughts
        3. **Choose Tone** - Professional, conversational, or other styles
        4. **Customize Images** - Select style, aspect ratio, and preferences
        5. **Generate & Preview** - Get A/B variants with AI-generated images
        6. **Edit & Publish** - Refine content and publish to LinkedIn
        """)
        
        st.header("🔧 Features")
        st.markdown("""
        • **AI-Powered Content** - Uses LangChain + Vertex AI/OpenAI
        • **Smart Summarization** - Extracts key points automatically
        • **A/B Testing** - Compare two post variants
        • **Image Generation** - AI-created visuals for each variant
        • **Content Moderation** - Safety checks before publishing
        • **LinkedIn Ready** - Optimized for professional networking
        """)
        
        st.header("⚡ Quick Start")
        st.markdown("""
        Try with a tech article URL:
        • TechCrunch
        • MIT Technology Review
        • Wired
        • Ars Technica
        """)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Render the post form
        form_data = render_post_form()
        
        if form_data:
            # Show form preview
            render_form_preview(form_data)
            
            # Process the form submission
            with st.spinner("Creating your post generation job..."):
                try:
                    # Create the job via API
                    job_id = api_client.create_post(
                        url=form_data["url"],
                        opinion=form_data["opinion"],
                        tone=form_data["tone"],
                        image_options=form_data["image_options"]
                    )
                    
                    if job_id:
                        st.success(f"✅ Job created successfully! Job ID: {job_id}")
                        
                        # Store job ID in session state for navigation
                        st.session_state["current_job_id"] = job_id
                        
                        # Show next steps
                        st.info("🎯 **Next Steps:**")
                        st.markdown("""
                        1. **Wait for Processing** - Your job is now being processed
                        2. **View Results** - Check the Preview page to see your posts
                        3. **Edit & Refine** - Make adjustments as needed
                        4. **Publish** - Share your favorite variant on LinkedIn
                        """)
                        
                        # Navigation button
                        if st.button("📊 Go to Preview Page", type="primary"):
                            st.switch_page("pages/preview.py")
                        
                        # Show job status
                        st.subheader("📊 Job Status")
                        status_response = api_client.get_post_status(job_id)
                        
                        if status_response:
                            status = status_response.get("status", "unknown")
                            st.info(f"**Current Status:** {status}")
                            
                            if status == "completed":
                                st.success("🎉 Your posts are ready! Click 'Go to Preview Page' to view them.")
                            elif status == "failed":
                                error = status_response.get("error", "Unknown error")
                                st.error(f"❌ Job failed: {error}")
                            else:
                                st.info("⏳ Job is still processing. This may take a few minutes.")
                        
                    else:
                        st.error("❌ Failed to create job. Please try again.")
                        
                except Exception as e:
                    st.error(f"❌ Error creating job: {e}")
                    st.info("Please check your input and try again.")
    
    with col2:
        # Show example posts
        st.subheader("💡 Example Output")
        st.markdown("""
        **Variant A:**
        > "Just read this fascinating article about AI in healthcare. The potential for early disease detection is incredible! What do you think about the ethical considerations? #AI #Healthcare #Innovation"
        
        **Variant B:**
        > "Healthcare AI is transforming patient care in ways we never imagined. This article highlights both the opportunities and challenges ahead. How is your industry adapting to AI integration? #DigitalHealth #AI #FutureOfMedicine"
        """)
        
        # Show image preview
        st.subheader("🎨 Generated Images")
        st.info("AI-generated images will appear here once your job is complete.")
        
        # Job queue info
        st.subheader("📋 Recent Jobs")
        st.info("Your job history will appear here.")
    
    # Footer
    st.markdown("---")
    st.caption("Built with Streamlit, FastAPI, and LangChain. Powered by Vertex AI and OpenAI.")

if __name__ == "__main__":
    render_home_page()
