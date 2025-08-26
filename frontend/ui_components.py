# frontend/ui_components.py
import streamlit as st
from typing import Dict, Any
from api_client import APIClient
from image_utils import image_exists, load_image, create_animated_placeholder
from config import MAX_WAIT_TIME, CUSTOM_CSS

def apply_custom_styles():
    """Apply custom CSS styles to the app."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def render_form():
    """Render the post creation form with improved styling."""
    st.markdown('<h1 class="main-header">🚀 AI Social Post Generator</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Transform any article into engaging LinkedIn posts with AI-generated images</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    with st.form("post_form", clear_on_submit=False):
        # URL input with icon
        st.markdown("### 📰 Article URL")
        url = st.text_input(
            "",
            placeholder="https://example.com/article",
            help="Enter the URL of the article you want to create a post about",
            label_visibility="collapsed"
        )
        
        # Opinion selection with icon
        st.markdown("### 💭 Your Opinion")
        opinion_options = [
            "Agree — I support the main arguments",
            "Disagree — I have different views",
            "Neutral — Presenting balanced perspective",
            "Custom opinion..."
        ]
        
        opinion_choice = st.selectbox(
            "",
            options=opinion_options,
            help="Choose your stance on the article content",
            label_visibility="collapsed"
        )
        
        # Custom opinion input
        custom_opinion = ""
        if opinion_choice == "Custom opinion...":
            custom_opinion = st.text_area(
                "",
                placeholder="Share your thoughts on this article...",
                help="Write your personal opinion or perspective",
                max_chars=500,
                label_visibility="collapsed"
            )
        
        # Final opinion to use
        final_opinion = custom_opinion if opinion_choice == "Custom opinion..." else opinion_choice
        
        # Tone selection with icon
        st.markdown("### 🎭 Post Tone")
        tone = st.selectbox(
            "",
            options=["professional", "conversational", "enthusiastic", "thoughtful", "analytical"],
            help="Choose the tone that best fits your audience and message",
            label_visibility="collapsed"
        )
        
        # Image options with icon
        st.markdown("### 🎨 Image Generation Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            style = st.selectbox(
                "Image Style",
                options=["photographic", "illustrated", "flat", "abstract"],
                help="Choose the visual style for generated images"
            )
            
            aspect_ratio = st.selectbox(
                "Aspect Ratio",
                options=["16:9", "1:1", "4:3", "3:2"],
                help="Choose the aspect ratio for generated images"
            )
        
        with col2:
            negative_prompt = st.text_area(
                "Negative Prompts",
                value="no text, no logos, no watermarks, no signatures",
                help="Specify what should NOT appear in the generated images",
                max_chars=200,
                height=100
            )
        
        # Form submission with styling
        st.markdown("---")
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
    """Render an enhanced loading screen with animations."""
    st.markdown('<h1 class="main-header">⏳ Generating Your Social Post</h1>', unsafe_allow_html=True)
    
    # Progress bar with custom styling
    progress = min(elapsed_time / MAX_WAIT_TIME, 1.0)
    progress_bar = st.progress(progress)
    
    # Status message with custom styling
    if job_status == "queued":
        status_text = "🔄 Your job is queued and will start processing soon"
    elif job_status == "in_progress":
        status_text = "⚙️ Your job is currently being processed"
    else:
        status_text = f"🔄 Processing your post (Status: {job_status})"
    
    st.markdown(f'<div class="status-info">{status_text}</div>', unsafe_allow_html=True)
    
    # Time remaining with custom styling
    remaining = max(MAX_WAIT_TIME - elapsed_time, 0)
    minutes, seconds = divmod(int(remaining), 60)
    st.markdown(f'<p style="text-align: center; font-size: 1.1rem; color: #666;">⏱️ Time remaining: {minutes:02d}:{seconds:02d}</p>', unsafe_allow_html=True)
    
    # Animated processing steps
    st.markdown("### 📊 Processing Steps")
    
    steps = [
        ("📥 Scraping article content", job_status != "queued"),
        ("📝 Generating summary", job_status == "in_progress"),
        ("✍️ Creating post variants", job_status == "in_progress"),
        ("🎨 Generating images", job_status == "in_progress"),
        ("✅ Moderating content", job_status == "in_progress")
    ]
    
    for step_text, is_active in steps:
        if is_active:
            st.markdown(f'<div class="loading-pulse">✅ {step_text}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="color: #999;">⏳ {step_text}</div>', unsafe_allow_html=True)
    
    # Extend wait button with custom styling
    if elapsed_time >= MAX_WAIT_TIME and not st.session_state.extended_wait:
        st.markdown("---")
        st.warning("⏱️ Taking longer than expected. Images can take up to 5 minutes to generate.")
        if st.button("⏳ Wait 1 More Minute", key="extend_wait", type="secondary"):
            st.session_state.extended_wait = True
            st.rerun()
    
    # Cancel button with custom styling
    st.markdown("---")
    if st.button("❌ Cancel Job", key="cancel_job"):
        reset_session()
        st.rerun()

def render_results(job_result: Dict[str, Any], job_id: str):
    """Render enhanced results with improved card design."""
    st.markdown('<h1 class="main-header">🎉 Your Social Posts Are Ready!</h1>', unsafe_allow_html=True)
    
    # Display provenance with card styling
    provenance = job_result.get("provenance", {})
    if provenance:
        st.markdown("### 📚 Source Information")
        st.markdown('<div class="post-card">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Title:** {provenance.get('title', 'No title available')}")
        with col2:
            st.markdown(f"**URL:** [{provenance.get('source_url', '#')}]({provenance.get('source_url', '#')})")
        st.markdown(f"**Excerpt:** {provenance.get('excerpt', 'No excerpt available')}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Display post variants with enhanced cards
    post_variants = job_result.get("post_variants", [])
    if not post_variants:
        st.warning("No post variants found")
        return
    
    st.markdown("### 📝 Generated Post Variants")
    
    for variant in post_variants:
        variant_id = variant.get("id", "Unknown")
        
        st.markdown(f'<div class="post-card">', unsafe_allow_html=True)
        st.markdown(f"#### Variant {variant_id}")
        
        # Create columns for layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Post text with better styling
            st.markdown("**Post Text:**")
            edited_text = st.text_area(
                f"text_{variant_id}",
                value=variant.get("text", ""),
                height=150,
                key=f"text_edit_{variant_id}",
                help="Edit the post text as needed",
                label_visibility="collapsed"
            )
            
            # Hashtags with custom styling
            st.markdown("**Hashtags:**")
            hashtags = variant.get("hashtags", [])
            if hashtags:
                hashtag_html = " ".join([f'<span class="hashtag">#{tag}</span>' for tag in hashtags])
                st.markdown(hashtag_html, unsafe_allow_html=True)
            else:
                st.info("No hashtags")
            
            # Suggested comment with better styling
            st.markdown("**Suggested Comment:**")
            suggested_comment = variant.get("suggested_comment", "")
            if suggested_comment:
                st.markdown(f'<div class="success-message">{suggested_comment}</div>', unsafe_allow_html=True)
            else:
                st.info("No comment suggested")
        
        with col2:
            # Image display with enhanced styling
            st.markdown("**Generated Image:**")
            
            # Check if image exists locally
            if image_exists(job_id, variant_id):
                image = load_image(job_id, variant_id)
                if image:
                    st.image(image, caption="Generated Image", use_container_width=True)
                else:
                    st.error("Failed to load image")
            else:
                # Show animated placeholder
                placeholder = create_animated_placeholder(variant_id, "Generating")
                st.image(placeholder, caption="Generating Image...", use_container_width=True)
                
                # Retry button with custom styling
                if st.button(f"🔄 Retry Image", key=f"retry_{variant_id}"):
                    if APIClient.regenerate_content(job_id, "image", variant_id):
                        st.success("Image regeneration started")
                        st.rerun()
        
        # Action buttons with better layout
        st.markdown("**Actions:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(f"🔄 Regenerate Text", key=f"regen_text_{variant_id}"):
                if APIClient.regenerate_content(job_id, "text", variant_id):
                    st.success("Text regeneration started")
                    st.rerun()
        
        with col2:
            if st.button(f"🎨 Regenerate Image", key=f"regen_image_{variant_id}"):
                if APIClient.regenerate_content(job_id, "image", variant_id):
                    st.success("Image regeneration started")
                    st.rerun()
        
        with col3:
            if st.button(f"📤 Publish to LinkedIn", key=f"publish_{variant_id}", type="primary"):
                result = APIClient.publish_post(job_id, variant_id, "demo_user")
                if result and result.get("published"):
                    st.markdown('<div class="success-message">✅ Successfully published to LinkedIn!</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="error-message">Failed to publish to LinkedIn</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def reset_session():
    """Reset the session state."""
    from config import SESSION_KEYS
    
    for key in SESSION_KEYS:
        if key in st.session_state:
            del st.session_state[key]