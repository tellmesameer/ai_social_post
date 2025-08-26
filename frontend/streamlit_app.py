# frontend/streamlit_app.py
import streamlit as st
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional
import json
from PIL import Image, ImageDraw, ImageFont
import io

# Configuration
API_BASE_URL = "http://localhost:8000"
PROJECT_ROOT = Path(__file__).parent.parent
TMP_DIR = PROJECT_ROOT / "tmp"
MAX_WAIT_TIME = 120  # 2 minutes
POLL_INTERVAL = 2    # 2 seconds

# Initialize session state
if 'job_id' not in st.session_state:
    st.session_state.job_id = None
if 'job_status' not in st.session_state:
    st.session_state.job_status = None
if 'job_result' not in st.session_state:
    st.session_state.job_result = None
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'extended_wait' not in st.session_state:
    st.session_state.extended_wait = False
if 'form_data' not in st.session_state:
    st.session_state.form_data = None
if 'show_results' not in st.session_state:
    st.session_state.show_results = False

# API Client Functions
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

def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """Get the status and result of a job."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/posts/{job_id}", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error getting job status: {e}")
        return None

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

# Image Handling Functions
def get_image_path(job_id: str, variant: str) -> Path:
    """Get the local path to an image file."""
    return TMP_DIR / job_id / "images" / f"{variant}.png"

def image_exists(job_id: str, variant: str) -> bool:
    """Check if an image file exists."""
    image_path = get_image_path(job_id, variant)
    return image_path.exists() and image_path.is_file()

def load_image(job_id: str, variant: str) -> Optional[Image.Image]:
    """Load an image from the local filesystem."""
    try:
        image_path = get_image_path(job_id, variant)
        if image_path.exists():
            return Image.open(image_path)
        return None
    except Exception as e:
        st.error(f"Error loading image: {e}")
        return None

def create_placeholder_image(variant_id: str, status: str = "Generating...") -> Image.Image:
    """Create a placeholder image with status text."""
    img = Image.new('RGB', (300, 200), color='#f0f0f0')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.load_default()
    except:
        font = None
    
    draw.rectangle([20, 20, 280, 180], outline='#666666', width=3)
    draw.text((150, 80), f"Variant {variant_id}", fill='#666666', anchor="mm", font=font)
    draw.text((150, 120), status, fill='#666666', anchor="mm", font=font)
    
    return img

# UI Components
def render_form():
    """Render the post creation form."""
    st.title("🚀 AI Social Post Generator")
    st.markdown("Transform any article into engaging LinkedIn posts with AI-generated images")
    
    with st.form("post_form"):
        # URL input
        url = st.text_input(
            "📰 Article URL",
            placeholder="https://example.com/article",
            help="Enter the URL of the article you want to create a post about"
        )
        
        # Opinion selection
        opinion_options = [
            "Agree — I support the main arguments",
            "Disagree — I have different views",
            "Neutral — Presenting balanced perspective",
            "Custom opinion..."
        ]
        
        opinion_choice = st.selectbox(
            "💭 Your Opinion",
            options=opinion_options,
            help="Choose your stance on the article content"
        )
        
        # Custom opinion input
        custom_opinion = ""
        if opinion_choice == "Custom opinion...":
            custom_opinion = st.text_area(
                "✍️ Express Your Opinion",
                placeholder="Share your thoughts on this article...",
                help="Write your personal opinion or perspective",
                max_chars=500
            )
        
        # Final opinion to use
        final_opinion = custom_opinion if opinion_choice == "Custom opinion..." else opinion_choice
        
        # Tone selection
        tone = st.selectbox(
            "🎭 Post Tone",
            options=["professional", "conversational", "enthusiastic", "thoughtful", "analytical"],
            help="Choose the tone that best fits your audience and message"
        )
        
        # Image options
        st.subheader("🎨 Image Generation Options")
        
        # Image style selection
        style = st.selectbox(
            "Image Style",
            options=["photographic", "illustrated", "flat", "abstract"],
            help="Choose the visual style for generated images"
        )
        
        # Aspect ratio selection
        aspect_ratio = st.selectbox(
            "Aspect Ratio",
            options=["16:9", "1:1", "4:3", "3:2"],
            help="Choose the aspect ratio for generated images"
        )
        
        # Negative prompt input
        negative_prompt = st.text_area(
            "Negative Prompts",
            value="no text, no logos, no watermarks, no signatures",
            help="Specify what should NOT appear in the generated images",
            max_chars=200
        )
        
        # Form submission
        submit_button = st.form_submit_button("🚀 Generate Social Post", type="primary")
        
        if submit_button:
            if not url.strip():
                st.error("Please enter a valid URL.")
                return None
            
            if not final_opinion.strip():
                st.error("Please provide your opinion.")
                return None
            
            return {
                "url": url.strip(),
                "opinion": final_opinion,
                "tone": tone,
                "image_options": {
                    "style": style,
                    "aspect_ratio": aspect_ratio,
                    "negative_prompt": negative_prompt,
                    "quality": 8,
                    "num_images": 1
                }
            }
    
    return None

def render_loading_screen(job_status: str, elapsed_time: int):
    """Render the loading screen with progress bar and status updates."""
    st.title("⏳ Generating Your Social Post")
    
    # Progress bar
    progress = min(elapsed_time / MAX_WAIT_TIME, 1.0)
    progress_bar = st.progress(progress)
    
    # Status message
    if job_status == "queued":
        status_text = "🔄 Your job is queued and will start processing soon"
    elif job_status == "in_progress":
        status_text = "⚙️ Your job is currently being processed"
    else:
        status_text = f"🔄 Processing your post (Status: {job_status})"
    
    st.info(status_text)
    
    # Time remaining
    remaining = max(MAX_WAIT_TIME - elapsed_time, 0)
    minutes, seconds = divmod(int(remaining), 60)
    st.caption(f"Time remaining: {minutes:02d}:{seconds:02d}")
    
    # Detailed status updates
    with st.expander("📊 Processing Details"):
        st.write("Current step:")
        if job_status == "queued":
            st.write("- Waiting to start processing")
        elif job_status == "in_progress":
            st.write("- Scraping article content")
            st.write("- Generating summary")
            st.write("- Creating post variants")
            st.write("- Generating images")
            st.write("- Moderating content")
        else:
            st.write(f"- Processing: {job_status}")
    
    # Extend wait button
    if elapsed_time >= MAX_WAIT_TIME and not st.session_state.extended_wait:
        st.warning("⏱️ Taking longer than expected. Images can take up to 5 minutes to generate.")
        if st.button("⏳ Wait 1 More Minute", key="extend_wait"):
            st.session_state.extended_wait = True
            st.rerun()
    
    # Cancel button
    if st.button("❌ Cancel Job", key="cancel_job"):
        st.session_state.job_id = None
        st.session_state.job_status = None
        st.session_state.job_result = None
        st.session_state.start_time = None
        st.session_state.extended_wait = False
        st.session_state.show_results = False
        st.rerun()

def render_results(job_result: Dict[str, Any], job_id: str):
    """Render the job results."""
    st.title("🎉 Your Social Posts Are Ready!")
    
    # Display provenance
    provenance = job_result.get("provenance", {})
    if provenance:
        st.subheader("📚 Source Information")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Title:** {provenance.get('title', 'No title available')}")
        with col2:
            st.write(f"**URL:** [{provenance.get('source_url', '#')}]({provenance.get('source_url', '#')})")
        st.write(f"**Excerpt:** {provenance.get('excerpt', 'No excerpt available')}")
    
    # Display post variants
    post_variants = job_result.get("post_variants", [])
    if not post_variants:
        st.warning("No post variants found")
        return
    
    st.subheader("📝 Generated Post Variants")
    
    for variant in post_variants:
        variant_id = variant.get("id", "Unknown")
        
        with st.container():
            st.markdown(f"### Variant {variant_id}")
            
            # Create columns for layout
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Post text
                st.write("**Post Text:**")
                edited_text = st.text_area(
                    f"text_{variant_id}",
                    value=variant.get("text", ""),
                    height=150,
                    key=f"text_edit_{variant_id}",
                    help="Edit the post text as needed"
                )
                
                # Hashtags
                st.write("**Hashtags:**")
                hashtags = variant.get("hashtags", [])
                hashtag_display = " ".join([f"#{tag}" for tag in hashtags]) if hashtags else "No hashtags"
                st.info(hashtag_display)
                
                # Suggested comment
                st.write("**Suggested Comment:**")
                suggested_comment = variant.get("suggested_comment", "")
                st.success(suggested_comment if suggested_comment else "No comment suggested")
            
            with col2:
                # Image display
                st.write("**Generated Image:**")
                
                # Check if image exists locally
                if image_exists(job_id, variant_id):
                    image = load_image(job_id, variant_id)
                    if image:
                        # FIXED: Replaced deprecated use_column_width with use_container_width
                        st.image(image, caption="Generated Image", use_container_width=True)
                    else:
                        st.error("Failed to load image")
                else:
                    # Show placeholder
                    placeholder = create_placeholder_image(variant_id, "Image not ready")
                    # FIXED: Replaced deprecated use_column_width with use_container_width
                    st.image(placeholder, caption="Generating Image...", use_container_width=True)
                    
                    # Retry button
                    if st.button(f"🔄 Retry Image for Variant {variant_id}", key=f"retry_{variant_id}"):
                        if regenerate_content(job_id, "image", variant_id):
                            st.success("Image regeneration started")
                            st.rerun()
            
            # Action buttons
            st.write("**Actions:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(f"🔄 Regenerate Text", key=f"regen_text_{variant_id}"):
                    if regenerate_content(job_id, "text", variant_id):
                        st.success("Text regeneration started")
                        st.rerun()
            
            with col2:
                if st.button(f"🎨 Regenerate Image", key=f"regen_image_{variant_id}"):
                    if regenerate_content(job_id, "image", variant_id):
                        st.success("Image regeneration started")
                        st.rerun()
            
            with col3:
                if st.button(f"📤 Publish to LinkedIn", key=f"publish_{variant_id}", type="primary"):
                    result = publish_post(job_id, variant_id, "demo_user")
                    if result and result.get("published"):
                        st.success("✅ Successfully published to LinkedIn!")
                    else:
                        st.error("Failed to publish to LinkedIn")
            
            st.markdown("---")

def reset_session():
    """Reset the session state."""
    for key in ['job_id', 'job_status', 'job_result', 'start_time', 'extended_wait', 'show_results']:
        if key in st.session_state:
            del st.session_state[key]

# Main App
def main():
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
            status_response = get_job_status(job_id)
            
            if status_response:
                job_status = status_response.get("status")
                st.session_state.job_status = job_status
                
                if job_status == "completed":
                    st.session_state.job_result = status_response.get("result", {})
                    st.session_state.show_results = True
                    st.rerun()
                elif job_status in ["failed", "cancelled"]:
                    st.error(f"Job {job_status}. Please try again.")
                    if st.button("Start Over"):
                        reset_session()
                        st.rerun()
                else:
                    # Still processing
                    render_loading_screen(job_status, elapsed_time)
                    time.sleep(POLL_INTERVAL)
                    st.rerun()
            else:
                st.error("Failed to get job status")
                if st.button("Start Over"):
                    reset_session()
                    st.rerun()
        else:
            # Either we have results or we've exceeded the wait time
            if st.session_state.job_result:
                st.session_state.show_results = True
                st.rerun()
            else:
                st.error("Job is taking longer than expected. Please try again later.")
                if st.button("Start Over"):
                    reset_session()
                    st.rerun()
    elif st.session_state.show_results and st.session_state.job_result:
        # Show the results
        render_results(st.session_state.job_result, st.session_state.job_id)
        
        # Add a "Create New Post" button
        if st.button("🆕 Create New Post", type="primary"):
            reset_session()
            st.rerun()
    else:
        # Show the form
        form_data = render_form()
        
        if form_data:
            # Submit the job
            with st.spinner("Creating your job..."):
                job_id = create_job(
                    url=form_data["url"],
                    opinion=form_data["opinion"],
                    tone=form_data["tone"],
                    image_options=form_data["image_options"]
                )
                
                if job_id:
                    st.success(f"Job created successfully! Job ID: {job_id}")
                    st.session_state.job_id = job_id
                    st.session_state.form_data = form_data
                    st.rerun()
                else:
                    st.error("Failed to create job. Please try again.")

if __name__ == "__main__":
    main()