# frontend/pages/preview.py
import streamlit as st
import time
from components.preview_card import (
    render_preview_card, 
    render_provenance_info, 
    render_moderation_status,
    render_job_status,
    render_provider_info
)
from api_client import get_api_client

def render_preview_page():
    """Render the preview page for viewing and editing generated posts."""
    
    st.set_page_config(
        page_title="AI Social Post Generator - Preview",
        page_icon="📊",
        layout="wide"
    )
    
    # Page header
    st.title("📊 Post Preview & Management")
    st.markdown("Review, edit, and publish your AI-generated social posts")
    
    # Get API client
    api_client = get_api_client()
    
    # Get job ID from session state or URL params
    job_id = st.session_state.get("current_job_id")
    
    if not job_id:
        st.error("❌ No job ID found. Please create a job from the Home page first.")
        if st.button("🏠 Go to Home"):
            st.switch_page("pages/home.py")
        return
    
    # Display job ID
    st.info(f"**Job ID:** {job_id}")
    
    # Job status polling
    status_response = api_client.get_post_status(job_id)
    
    if not status_response:
        st.error("❌ Failed to get job status. Please try again.")
        return
    
    job_status = status_response.get("status", "unknown")
    error = status_response.get("error")
    
    # Show job status
    render_job_status(job_status, error)
    
    # Handle different job statuses
    if job_status == "queued":
        st.info("⏳ Your job is queued and will start processing soon.")
        st.info("This page will automatically update when processing begins.")
        
        # Auto-refresh
        time.sleep(2)
        st.rerun()
        
    elif job_status == "in_progress":
        st.info("⚙️ Your job is currently being processed.")
        st.info("This may take a few minutes. The page will refresh automatically.")
        
        # Show progress
        with st.spinner("Processing your post..."):
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.1)
                progress_bar.progress(i + 1)
        
        # Auto-refresh
        time.sleep(5)
        st.rerun()
        
    elif job_status == "failed":
        st.error(f"❌ Job failed: {error}")
        st.info("Please try creating a new job or contact support if the issue persists.")
        
        if st.button("🔄 Create New Job"):
            st.switch_page("pages/home.py")
            
    elif job_status == "completed":
        # Show completed results
        result = status_response.get("result")
        if not result:
            st.error("❌ Job completed but no results found.")
            return
        
        # Display results
        st.success("🎉 Your posts are ready!")
        
        # Show provenance information
        provenance = result.get("provenance", {})
        if provenance:
            render_provenance_info(provenance)
        
        # Show provider information
        providers = result.get("providers", {})
        if providers:
            render_provider_info(providers)
        
        # Show moderation status
        moderation = result.get("moderation", {})
        if moderation:
            render_moderation_status(moderation)
        
        # Display post variants
        post_variants = result.get("post_variants", [])
        if not post_variants:
            st.warning("No post variants found in the result.")
            return
        
        st.header("📝 Generated Post Variants")
        
        # Handle regeneration callbacks
        def handle_regenerate_text(job_id: str, regenerate_type: str, variant: str):
            """Handle text regeneration request."""
            with st.spinner(f"Regenerating text for variant {variant}..."):
                success = api_client.regenerate_content(job_id, regenerate_type, variant)
                if success:
                    st.success(f"Text regeneration started for variant {variant}")
                    st.rerun()
                else:
                    st.error("Failed to start text regeneration")
        
        def handle_regenerate_image(job_id: str, regenerate_type: str, variant: str):
            """Handle image regeneration request."""
            with st.spinner(f"Regenerating image for variant {variant}..."):
                success = api_client.regenerate_content(job_id, regenerate_type, variant)
                if success:
                    st.success(f"Image regeneration started for variant {variant}")
                    st.rerun()
                else:
                    st.error("Failed to start image regeneration")
        
        def handle_publish(job_id: str, variant: str):
            """Handle publish request."""
            # Get user ID (for demo, use a default)
            user_id = "demo_user_1"
            
            with st.spinner(f"Publishing variant {variant} to LinkedIn..."):
                result = api_client.publish_post(job_id, variant, user_id)
                if result and result.get("published"):
                    linkedin_id = result.get("linkedin_post_id", "Unknown")
                    st.success(f"✅ Successfully published variant {variant} to LinkedIn!")
                    st.info(f"LinkedIn Post ID: {linkedin_id}")
                else:
                    error = result.get("error", "Unknown error") if result else "No response"
                    st.error(f"❌ Failed to publish: {error}")
        
        # Render each variant
        for variant in post_variants:
            # Create a container for each variant
            with st.container():
                st.markdown("---")
                
                # Render the preview card
                updated_variant = render_preview_card(
                    variant=variant,
                    job_id=job_id,
                    api_client=api_client,
                    on_regenerate_text=handle_regenerate_text,
                    on_regenerate_image=handle_regenerate_image,
                    on_publish=handle_publish
                )
                
                # Update the variant in the result
                for i, v in enumerate(post_variants):
                    if v["id"] == updated_variant["id"]:
                        post_variants[i] = updated_variant
                        break
        
        # Summary and next steps
        st.markdown("---")
        st.subheader("🎯 Next Steps")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **📝 Edit Your Posts:**
            • Modify text content as needed
            • Adjust hashtags and comments
            • Fine-tune image descriptions
            """)
            
            st.markdown("""
            **🔄 Regenerate Content:**
            • Create new text variations
            • Generate different images
            • Improve specific elements
            """)
        
        with col2:
            st.markdown("""
            **📤 Publish to LinkedIn:**
            • Choose your favorite variant
            • Review content moderation status
            • Share with your network
            """)
            
            st.markdown("""
            **📊 A/B Testing:**
            • Compare both variants
            • Test different approaches
            • Optimize for engagement
            """)
        
        # Action buttons
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Refresh Results", use_container_width=True):
                st.rerun()
        
        with col2:
            if st.button("🏠 Back to Home", use_container_width=True):
                st.switch_page("pages/home.py")
        
        with col3:
            if st.button("📋 View Job History", use_container_width=True):
                st.info("Job history feature coming soon!")
    
    else:
        st.warning(f"Unknown job status: {job_status}")
    
    # Footer
    st.markdown("---")
    st.caption("Built with Streamlit, FastAPI, and LangChain. Powered by Vertex AI and OpenAI.")

if __name__ == "__main__":
    render_preview_page()
