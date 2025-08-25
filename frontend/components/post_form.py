# frontend/components/post_form.py
import streamlit as st
from typing import Dict, Any, Optional
from components.image_options import render_image_options

def render_post_form() -> Optional[Dict[str, Any]]:
    """Render the post creation form and return form data."""
    
    st.header("🚀 Create AI-Generated Social Post")
    st.markdown("Enter a URL and your opinion to generate LinkedIn-ready posts with AI-generated images.")
    
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
        if not custom_opinion.strip():
            st.warning("Please provide your custom opinion.")
            return None
    
    # Final opinion to use
    final_opinion = custom_opinion if opinion_choice == "Custom opinion..." else opinion_choice
    
    # Tone selection
    tone = st.selectbox(
        "🎭 Post Tone",
        options=["professional", "conversational", "enthusiastic", "thoughtful", "analytical"],
        help="Choose the tone that best fits your audience and message"
    )
    
    # Tone descriptions
    tone_descriptions = {
        "professional": "Formal, business-appropriate language",
        "conversational": "Friendly, approachable, like talking to a colleague",
        "enthusiastic": "Energetic, positive, and engaging",
        "thoughtful": "Reflective, considerate, and contemplative",
        "analytical": "Data-driven, logical, and objective"
    }
    
    if tone in tone_descriptions:
        st.info(f"**{tone.title()} Tone:** {tone_descriptions[tone]}")
    
    # A/B testing toggle
    st.subheader("🔄 A/B Testing")
    enable_ab_testing = st.checkbox(
        "Generate two post variants (A & B) for comparison",
        value=True,
        help="Create two different versions to test which performs better"
    )
    
    # Image options
    image_options = render_image_options()
    
    # Form validation
    if not url.strip():
        st.error("Please enter a valid URL.")
        return None
    
    if not final_opinion.strip():
        st.error("Please provide your opinion.")
        return None
    
    # Submit button
    if st.button("🚀 Generate Social Post", type="primary", use_container_width=True):
        if url.strip() and final_opinion.strip():
            return {
                "url": url.strip(),
                "opinion": final_opinion,
                "tone": tone,
                "image_options": image_options,
                "enable_ab_testing": enable_ab_testing
            }
        else:
            st.error("Please fill in all required fields.")
            return None
    
    return None

def render_form_preview(form_data: Dict[str, Any]):
    """Render a preview of the form data."""
    if not form_data:
        return
    
    st.subheader("📋 Form Preview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**URL:**")
        st.code(form_data["url"], language="text")
        
        st.write("**Opinion:**")
        st.info(form_data["opinion"])
    
    with col2:
        st.write("**Tone:**")
        st.success(form_data["tone"].title())
        
        st.write("**Image Style:**")
        st.info(f"{form_data['image_options']['style'].title()} - {form_data['image_options']['aspect_ratio']}")
    
    st.write("**Image Options:**")
    st.json(form_data["image_options"])

def get_default_form_data() -> Dict[str, Any]:
    """Get default form data for testing."""
    return {
        "url": "https://example.com/article",
        "opinion": "Agree — I support the main arguments",
        "tone": "professional",
        "image_options": {
            "style": "photographic",
            "aspect_ratio": "16:9",
            "negative_prompt": "no text, no logos, no watermarks, no signatures",
            "quality": 8,
            "num_images": 1
        },
        "enable_ab_testing": True
    }
