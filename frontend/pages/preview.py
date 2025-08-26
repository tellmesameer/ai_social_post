# frontend/pages/preview.py
import streamlit as st
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional, Callable, Tuple, Union
import logging

# Import components
# Assuming these functions are defined in components.preview_card or similar
# If they are defined elsewhere or in this file, adjust imports accordingly.
# For this complete file, we'll assume they are imported.
try:
    from components.preview_card import (
        render_provenance_info,
        render_moderation_status,
        render_job_status,
        render_provider_info
    )
except ImportError as e:
    st.error(f"Error importing components: {e}")
    # Define minimal placeholders or handle the error as appropriate
    def render_provenance_info(*args, **kwargs): st.write("Provenance Info Placeholder")
    def render_moderation_status(*args, **kwargs): st.write("Moderation Status Placeholder")
    def render_job_status(status, error): st.write(f"Job Status: {status}, Error: {error}")
    def render_provider_info(*args, **kwargs): st.write("Provider Info Placeholder")

# Import API client
from api_client import get_api_client

BASE_API_URL = "http://localhost:8000" # Common alternative: "http://127.0.0.1:8000"
logger = logging.getLogger(__name__)

try:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    logger.info(f"**DEBUG:** Calculated BASE_DIR in frontend: `{BASE_DIR}`")
    if not (BASE_DIR / "tmp").exists():
        raise FileNotFoundError("tmp directory not found relative to assumed project root.")
except Exception as e:
    # Fallback to a common absolute path - UPDATE THIS TO YOUR ACTUAL PATH
    st.warning(f"Could not determine project BASE_DIR automatically: {e}. Using fallback.")
    BASE_DIR = Path(r"D:\AI_Project\ai_social_post") # <-- Update this path!

# Retry settings for local file check
MAX_RETRY_DURATION_SECONDS = 90  # Total time to wait
RETRY_INTERVAL_SECONDS = 2       # Time between checks

# --- Logger Setup ---
# Ensure logger is configured. If frontend/logger.py exists and configures the root logger, this should work.
# Otherwise, basicConfig might be needed.
# If logging isn't working, uncomment the next line:
# logging.basicConfig(level=logging.INFO)

LOG_PREFIX = "[preview.py]"

# --- Helper Functions ---

def load_image_for_variant(
    variant: Dict[str, Any],
    job_id: str,
    variant_id: str,
    base_dir: Path,
    base_api_url: str,
    max_retry_duration: int = MAX_RETRY_DURATION_SECONDS,
    retry_interval: int = RETRY_INTERVAL_SECONDS
) -> Tuple[bool, Union[bytes, str, None], str]:
    """
    Attempts to load image data for a variant, prioritizing local file system check
    with retry, then falling back to the API URL.

    Args:
        variant: The variant dictionary containing potential 'image_path'.
        job_id: The ID of the job.
        variant_id: The ID of the variant (e.g., 'A', 'B').
        base_dir: The base project directory (e.g., D:\AI_Project\ai_social_post).
        base_api_url: The base URL of the backend API (e.g., http://localhost:8000).
        max_retry_duration: Maximum time (seconds) to retry checking the local file.
        retry_interval: Interval (seconds) between local file checks.

    Returns:
        A tuple: (success: bool, image_data_or_url: bytes/str/None, source: str)
        - success: True if image data was obtained, False otherwise.
        - image_data_or_url: Raw bytes if from local file, full API URL string if from API, None on failure.
        - source: A string indicating the source ("local_file", "api_url", "failed").
    """
    logger.info(f"{LOG_PREFIX} Starting image load process for variant {variant_id} (Job: {job_id})")

    # 1. Determine the potential API URL
    image_path_or_url = variant.get("image_path", "")
    api_url = None
    if image_path_or_url.startswith(("http://", "https://")):
        api_url = image_path_or_url
        logger.debug(f"Using full URL from variant: {api_url}")
    elif image_path_or_url.startswith("/api/v1/images/"):
        api_url = f"{base_api_url}{image_path_or_url}"
        logger.debug(f"Constructed API URL from relative path: {api_url}")
    else:
        # Fallback construction based on standard path
        api_url = f"{base_api_url}/api/v1/images/{job_id}/{variant_id}.png"
        logger.debug(f"Constructed fallback API URL: {api_url}")

    if not api_url:
        logger.warning(f"No valid API URL could be constructed for variant {variant_id}")
        return False, None, "failed"

    # 2. Prioritize Local File System Check with Retry
    # Construct the expected local path based on project structure
    local_file_path = base_dir / "tmp" / job_id / "images" / f"{variant_id}.png"
    logger.debug(f"Checking for local image file: {local_file_path}")

    start_time = time.time()
    while time.time() - start_time < max_retry_duration:
        if local_file_path.exists() and local_file_path.is_file():
            try:
                with open(local_file_path, "rb") as f:
                    image_data = f.read()
                if image_data: # Check if data was actually read
                    logger.info(f"Successfully loaded image from local file: {local_file_path}")
                    return True, image_data, "local_file"
                else:
                    logger.warning(f"Local file {local_file_path} is empty.")
            except Exception as e:
                logger.error(f"Error reading local image file {local_file_path}: {e}")

        # If file not found, not readable, or empty, wait and retry
        elapsed = time.time() - start_time
        logger.debug(f"Local file {local_file_path} not found/readable/empty. Retrying in {retry_interval}s... (Elapsed: {elapsed:.1f}s)")
        time.sleep(retry_interval)

    logger.info(f"Local file check timed out after {max_retry_duration}s for {local_file_path}")

    # 3. Fallback to API URL (if local check failed/timed out)
    # Streamlit's st.image can handle full URLs directly.
    logger.info(f"Falling back to API URL for image: {api_url}")
    return True, api_url, "api_url" # Indicate success, but source is API


# Placeholder function for image if loading fails
def create_placeholder_image(variant_id: str):
    """Creates or returns a placeholder image."""
    # A simple text placeholder. You can generate a PIL image or use a static file.
    return "🖼️ Placeholder Image"


# --- Main Rendering Functions ---

def render_preview_card(
    variant: Dict[str, Any],
    job_id: str,
    api_client,
    on_regenerate_text: Optional[Callable] = None,
    on_regenerate_image: Optional[Callable] = None,
    on_publish: Optional[Callable] = None,
):
    """Render a preview card for a post variant."""
    logger.debug(f"Rendering preview card for variant: {variant}")

    variant_id = variant.get("id", "Unknown")
    st.subheader(f"📝 Variant {variant_id}")

    # Create columns for layout
    col1, col2 = st.columns([2, 1])
    logger.info(f"**DEBUG:** Calculated BASE_DIR in frontend: `{BASE_DIR}`")

    with col1:
        # Post text (editable)
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
        
        # Alt text
        st.write("**Image Alt Text:**")
        alt_text = variant.get("alt_text", "")
        st.caption(alt_text if alt_text else "No alt text provided")

    with col2:
        # Image display
        st.write("**Generated Image:**")

        # Use the modular helper function
        success, image_data_or_url, source = load_image_for_variant(
            variant=variant,
            job_id=job_id,
            variant_id=variant_id,
            base_dir=BASE_DIR, # Pass configured base directory
            base_api_url=BASE_API_URL # Pass configured API base URL
            # max_retry_duration and retry_interval use defaults from config
        )

        if success and image_data_or_url is not None:
            try:
                if source == "local_file":
                    # Display raw bytes from local file
                    st.image(image_data_or_url, caption="Generated Image (Local)", use_column_width=True)
                    st.info("Loaded from local file system.")
                elif source == "api_url":
                    # Display using the full API URL (Streamlit handles the HTTP request)
                    st.image(image_data_or_url, caption="Generated Image", use_column_width=True)
                    # Optional info
                    # st.info("Loaded via API request.")
            except Exception as e:
                st.error(f"Error displaying image: {e}")
                logger.error(f"Failed to display image for variant {variant_id} (Source: {source}): {e}", exc_info=True)
                placeholder_img = create_placeholder_image(variant_id)
                st.image(placeholder_img, caption="Image Placeholder", use_column_width=True)
        else:
            # Loading failed or timed out
            st.warning("Image could not be loaded within the timeout period.")
            placeholder_img = create_placeholder_image(variant_id)
            st.image(placeholder_img, caption="Image Placeholder", use_column_width=True)
            st.info("Image might still be generating. You can refresh the page.")

    # Action buttons
    st.write("**Actions:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(f"🔄 Regenerate Text", key=f"regen_text_{variant_id}"):
            if on_regenerate_text:
                # Assuming callback signature: on_regenerate_text(job_id, type, variant_id)
                on_regenerate_text(job_id, "text", variant_id)
            else:
                st.info("Text regeneration requested (callback not provided)")
    with col2:
        if st.button(f"🎨 Regenerate Image", key=f"regen_image_{variant_id}"):
            if on_regenerate_image:
                 # Assuming callback signature: on_regenerate_image(job_id, type, variant_id)
                on_regenerate_image(job_id, "image", variant_id)
            else:
                st.info("Image regeneration requested (callback not provided)")
    with col3:
        if st.button(f"📤 Publish to LinkedIn", key=f"publish_{variant_id}", type="primary"):
            if on_publish:
                # Assuming callback signature: on_publish(job_id, variant_id)
                on_publish(job_id, variant_id)
            else:
                st.info("Publish requested (callback not provided)")

    # Important: Update the variant dictionary with the edited text before returning
    variant["text"] = edited_text
    return variant # Return the (potentially modified) variant dict


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
            # Adjust path based on your Streamlit navigation setup (e.g., "Home" or "pages/home.py")
            st.switch_page("pages/home.py")
        return

    # Display job ID
    st.info(f"**Job ID:** {job_id}")

    # --- Job Status Polling and Display ---
    # Fetch job status AND result (if completed) in one call
    status_response = api_client.get_post_status(job_id)

    if not status_response:
        st.error("❌ Failed to get job status. Please try again.")
        return

    job_status = status_response.get("status", "unknown")
    error = status_response.get("error")

    # --- Display Job Status ---
    # Assuming render_job_status is imported or defined
    render_job_status(job_status, error)


    # --- Handle Different Job Statuses ---

    if job_status == "queued":
        st.info("⏳ Your job is queued and will start processing soon.")
        st.info("This page will automatically update when processing begins.")
        # Auto-refresh
        time.sleep(2)
        st.rerun()

    elif job_status == "in_progress":
        st.info("⚙️ Your job is currently being processed.")
        st.info("This may take a few minutes. The page will refresh automatically.")
        # Show progress (this is static, backend should ideally provide progress updates)
        with st.spinner("Processing your post..."):
            # Simulate progress or fetch real progress if backend provides it
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.05) # Adjust sleep time as needed
                progress_bar.progress(min(i + 1, 100)) # Ensure it doesn't exceed 100
        # Auto-refresh
        time.sleep(2) # Short delay before refresh
        st.rerun()

    elif job_status == "failed":
        st.error(f"❌ Job failed: {error}")
        st.info("Please try creating a new job or contact support if the issue persists.")

        if st.button("🔄 Create New Job"):
            st.switch_page("pages/home.py") # Adjust path as needed
            
    elif job_status == "cancelled":
         st.warning("⚠️ Job was cancelled.")
         if st.button("🔄 Create New Job"):
            st.switch_page("pages/home.py") # Adjust path as needed

    elif job_status == "completed":
        # --- Display Completed Results ---
        result_data = status_response.get("result") # Get result data from the status response
        if not result_data:
            st.error("❌ Job completed but no results found in the response.")
            return

        st.success("🎉 Your posts are ready!")

        # --- Extract Data from result_data ---
        provenance = result_data.get("provenance", {})
        providers = result_data.get("providers", {}) # Might be 'provider_info' depending on backend
        moderation = result_data.get("moderation", {})
        post_variants = result_data.get("post_variants", [])

        # --- Display Additional Information ---
        # Provenance
        if provenance:
            st.subheader("🔍 Provenance")
            render_provenance_info(provenance) # Assuming function exists

        # Providers (check key name)
        if providers:
            st.subheader("🤖 AI Providers Used")
            render_provider_info(providers) # Assuming function exists

        # Moderation
        if moderation:
            st.subheader("🛡️ Content Moderation")
            render_moderation_status(moderation) # Assuming function exists

        # --- Display Post Variants ---
        if not post_variants:
            st.warning("No post variants found in the result.")
            return

        st.header("📝 Generated Post Variants")

        # --- Define Callback Handlers ---
        # These functions interact with the api_client to trigger backend actions
        def handle_regenerate_text(job_id: str, regenerate_type: str, variant_id: str):
            """Handle text regeneration request."""
            with st.spinner(f"Regenerating text for variant {variant_id}..."):
                # Ensure api_client method signature matches (job_id, type, variant_id)
                success = api_client.regenerate_content(job_id, regenerate_type, variant_id)
                if success:
                    st.success(f"Text regeneration started for variant {variant_id}")
                    st.rerun()
                else:
                    st.error("Failed to start text regeneration")

        def handle_regenerate_image(job_id: str, regenerate_type: str, variant_id: str):
            """Handle image regeneration request."""
            with st.spinner(f"Regenerating image for variant {variant_id}..."):
                 # Ensure api_client method signature matches (job_id, type, variant_id)
                success = api_client.regenerate_content(job_id, regenerate_type, variant_id)
                if success:
                    st.success(f"Image regeneration started for variant {variant_id}")
                    st.rerun()
                else:
                    st.error("Failed to start image regeneration")

        def handle_publish(job_id: str, variant_id: str):
            """Handle publish request."""
            # Get user ID (for demo, use a default or prompt)
            # Consider using st.session_state.get("user_id", "demo_user_1")
            user_id = st.session_state.get("user_id", "demo_user_1") # Example

            with st.spinner(f"Publishing variant {variant_id} to LinkedIn..."):
                # Ensure api_client method signature matches (job_id, variant_id, user_id)
                result = api_client.publish_post(job_id, variant_id, user_id)
                if result and result.get("published"):
                    linkedin_id = result.get("linkedin_post_id", "Unknown")
                    st.success(f"✅ Successfully published variant {variant_id} to LinkedIn!")
                    st.info(f"LinkedIn Post ID: {linkedin_id}")
                elif result and "error" in result:
                     st.error(f"❌ Failed to publish: {result['error']}")
                else:
                    st.error("❌ Failed to publish: Unknown error or no response")


        # --- Render Each Variant Card ---
        for i, variant in enumerate(post_variants):
            variant_id = variant.get("id", f"Variant {i+1}")
            with st.container():
                st.markdown("---")
                # Pass the variant dict, job_id, api_client, and callbacks
                # The render_preview_card function now handles image loading internally
                updated_variant = render_preview_card(
                    variant=variant,
                    job_id=job_id,
                    api_client=api_client,
                    on_regenerate_text=handle_regenerate_text,
                    on_regenerate_image=handle_regenerate_image,
                    on_publish=handle_publish
                )
                # If you need to update the post_variants list with edits, you can do so here
                # post_variants[i] = updated_variant

        # --- Summary and Next Steps ---
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

        # --- Action Buttons ---
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔄 Refresh Results", use_container_width=True):
                st.rerun()

        with col2:
            if st.button("🏠 Back to Home", use_container_width=True):
                # Adjust path based on your Streamlit navigation setup
                st.switch_page("pages/home.py")

        with col3:
            # Placeholder for future feature
            if st.button("📋 View Job History", use_container_width=True):
                st.info("Job history feature coming soon!")

    else:
        st.warning(f"Unknown or unhandled job status: {job_status}")

    # --- Footer ---
    st.markdown("---")
    st.caption("Built with Streamlit, FastAPI, and LangChain. Powered by Vertex AI and OpenAI.")


if __name__ == "__main__":
    render_preview_page()