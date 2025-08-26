# backend\prompts.py

# Third-party imports
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, SystemMessage

# Local application imports
from .logger_config import logger

# System messages for different roles
SYSTEM_MESSAGES = {
    "summarizer": SystemMessage(content="""You are an expert content summarizer. Your task is to create concise, accurate summaries of articles and content. 
    Focus on the main points, key insights, and actionable takeaways. Be professional and objective in your summaries."""),
    
    "linkedin_writer": SystemMessage(content="""You are a professional LinkedIn content writer with expertise in creating engaging, thought-provoking posts. 
    Your posts should be informative, shareable, and encourage meaningful discussion. Use appropriate hashtags and maintain a professional tone."""),
    
    "image_prompt_generator": SystemMessage(content="""You are an expert at creating detailed, descriptive prompts for AI image generation. 
    Your prompts should be clear, specific, and result in professional, high-quality images suitable for LinkedIn posts."""),
    
    "moderator": SystemMessage(content="""You are a content moderator ensuring all generated content meets professional standards. 
    Check for appropriate tone, factual accuracy, and compliance with LinkedIn's content policies.""")
}

# Prompt templates
SUMMARY_PROMPT = PromptTemplate(
    input_variables=["article_text"],
    template="""Summarize the following article into a 3-4 sentence summary and 3 concise bullet points.

Article:
{article_text}

Please return your response in the following JSON format:
{{
    "summary": "Your 3-4 sentence summary here",
    "bullets": [
        "First key point",
        "Second key point", 
        "Third key point"
    ]
}}"""
)

POST_VARIANTS_PROMPT = PromptTemplate(
    input_variables=["summary", "bullets_joined", "opinion", "tone"],
    template="""You are a LinkedIn content writer. Use the summary and bullet points to create two post variants A and B.

Context:
- Summary: {summary}
- Key Points: {bullets_joined}
- User Opinion: {opinion}
- Tone: {tone}

Requirements for each variant:
- Text: Maximum 1300 characters, engaging and thought-provoking
- Hashtags: Exactly 3 relevant hashtags
- Suggested Comment: One line to encourage engagement
- Alt Text: Maximum 125 characters describing the image

Return your response in this exact JSON format:
{{
    "A": {{
        "text": "Post text for variant A",
        "hashtags": ["#tag1", "#tag2", "#tag3"],
        "suggested_comment": "Suggested comment for variant A",
        "alt_text": "Alt text for variant A image"
    }},
    "B": {{
        "text": "Post text for variant B", 
        "hashtags": ["#tag1", "#tag2", "#tag3"],
        "suggested_comment": "Suggested comment for variant B",
        "alt_text": "Alt text for variant B image"
    }}
}}"""
)

IMAGE_PROMPT_PROMPT = PromptTemplate(
    input_variables=["post_text", "style", "negative_prompt"],
    template="""Create a detailed, professional image prompt for an AI image generator that will create a LinkedIn post image.

Post Content: {post_text}
Style: {style}
Negative Prompts: {negative_prompt}

Your prompt should:
- Be descriptive and specific
- Match the professional tone of LinkedIn
- Include visual elements that complement the post content
- Specify the style (photographic, illustrated, flat, abstract)
- Avoid any text, logos, or watermarks
- Be suitable for business/professional audiences

Return only the image prompt text, no additional formatting."""
)

MODERATION_PROMPT = PromptTemplate(
    input_variables=["post_text", "hashtags_joined", "suggested_comment"],
    template="""Review the following LinkedIn post content for appropriateness and compliance:

Post Text: {post_text}
Hashtags: {hashtags_joined}
Suggested Comment: {suggested_comment}

Check for:
1. Professional tone and language
2. Factual accuracy
3. Compliance with LinkedIn policies
4. Appropriate hashtag usage
5. Engagement without controversy

Return your assessment in this JSON format:
{{
    "status": "pass|review|reject",
    "notes": ["List any concerns or recommendations"],
    "confidence": "high|medium|low"
}}"""
)

# Function to create message chains
def create_summary_messages(article_text: str):
    """Create messages for summary generation."""
    logger.info("Creating summary messages")
    return [
        SYSTEM_MESSAGES["summarizer"],
        HumanMessage(content=SUMMARY_PROMPT.format(article_text=article_text))
    ]

def create_post_variants_messages(summary: str, bullets: list, opinion: str, tone: str):
    """Create messages for post variant generation."""
    logger.info("Creating post variants messages")
    bullets_joined = ', '.join(bullets) if bullets else ''
    return [
        SYSTEM_MESSAGES["linkedin_writer"],
        HumanMessage(content=POST_VARIANTS_PROMPT.format(
            summary=summary,
            bullets_joined=bullets_joined,
            opinion=opinion,
            tone=tone
        ))
    ]

def create_image_prompt_messages(post_text: str, style: str, negative_prompt: str):
    """Create messages for image prompt generation."""
    logger.info("Creating image prompt messages")
    return [
        SYSTEM_MESSAGES["image_prompt_generator"],
        HumanMessage(content=IMAGE_PROMPT_PROMPT.format(
            post_text=post_text,
            style=style,
            negative_prompt=negative_prompt
        ))
    ]

def create_moderation_messages(post_text: str, hashtags: list, suggested_comment: str):
    """Create messages for content moderation."""
    logger.info("Creating moderation messages")
    hashtags_joined = ', '.join(hashtags) if hashtags else ''
    return [
        SYSTEM_MESSAGES["moderator"],
        HumanMessage(content=MODERATION_PROMPT.format(
            post_text=post_text,
            hashtags_joined=hashtags_joined,
            suggested_comment=suggested_comment
        ))
    ]
