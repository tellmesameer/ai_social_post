# backend\providers.py
import os
import base64
import asyncio
import io as _io
from typing import Optional
from .config import settings
from datetime import datetime
from PIL import Image, ImageDraw
from .logger_config import logger, log_call
from langchain_google_genai import ChatGoogleGenerativeAI
# Use langchain_core.messages consistently for message classes to avoid import mismatches
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage

class AI_Response:
    def __init__(self):
        if settings.google_api_key is not None:
            os.environ["GOOGLE_API_KEY"] = settings.google_api_key

    async def get_text_google(self, prompt: str, max_tokens: Optional[int] = None, temperature: Optional[float] = None, **kwargs) -> dict:
        logger.info("Generating text for prompt:")
        llm_kwargs = {}
        if temperature is not None:
            llm_kwargs["temperature"] = float(temperature)
        if max_tokens is not None:
            llm_kwargs["max_output_tokens"] = int(max_tokens)

        def _invoke():
            chat_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", **llm_kwargs)
            new_message = chat_llm.invoke([
                SystemMessage(content="You are a helpful assistant."),
                HumanMessage(content=prompt),
            ])
            return {
                "content": new_message.content,
                "status": 200,
            }
        return await asyncio.to_thread(_invoke)

    async def generate_image(self, prompt: str) -> dict:
        logger.info("Generating image for prompt")
        def _invoke():
            image_llm = ChatGoogleGenerativeAI(model="models/gemini-2.0-flash-preview-image-generation")
            message = HumanMessage(content=prompt)
            response = image_llm.invoke(
                [message],
                generation_config=dict(response_modalities=["TEXT", "IMAGE"]),
            )
            def _get_image_base64(response: BaseMessage) -> None:
                for block in getattr(response, "content", []) or []:
                    if isinstance(block, dict) and block.get("image_url"):
                        url = block["image_url"].get("url")
                        if url and "," in url:
                            return url.split(",", 1)[-1]
                        return url
                return None
            image_base64 = _get_image_base64(response)
            if image_base64 is not None:
                return {
                    "image_base64": image_base64,
                    "alt_text": prompt,
                    "status": 200
                }
            else:
                return {
                    "image_base64": None,
                    "alt_text": prompt,
                    "status": 500,
                    "error": "No image data found"
                }
        return await asyncio.to_thread(_invoke)



    def get_image_description(self, image_path: str) -> dict:
        # Multimodal invocation with gemini-pro-vision
        logger.info(f"Getting description for image: {image_path}")
        chat_with_image_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": "What's in this image?",
                },
                {"type": "image_url", "image_url": image_path},
            ]
        )
        result = chat_with_image_llm.invoke([message])
        description=result.content
        return {
            "description": description,
            "status": 200
        }


# Adapter to expose a stable provider interface expected by the rest of the app
class ProviderAdapter:
    def __init__(self):
        self.impl = None
        self.google_available = bool(settings.google_api_key and settings.vertex_project)
        if self.google_available:
            try:
                self.impl = AI_Response()
                logger.info("ProviderAdapter: using Google AI (AI_Response)")
            except Exception as e:
                logger.warning(f"ProviderAdapter: failed to initialize AI_Response: {e}")
                self.impl = None


    async def generate_text(self, prompt: str, max_tokens: int = 512, temperature: float = 0.2) -> str:
        logger.info("ProviderAdapter.generate_text called with prompt...")
        if self.impl:
            try:
                resp = await self.impl.get_text_google(prompt)
                if isinstance(resp, dict):
                    content = resp.get("content")
                    if content:
                        return str(content)
            except Exception as e:
                logger.warning(f"ProviderAdapter.generate_text: google impl failed: {e}")

        # Dev-stub fallback
        if "summary" in prompt.lower():
            return (
                "This is a comprehensive summary of the article that provides key insights and main points. "
            )
        if "post" in prompt.lower():
            return (
                "This is a compelling LinkedIn post that engages readers with thought-provoking content. "
            )
        return "This is generated content based on your request."

    async def generate_image(self, prompt: str, negative_prompt: Optional[str] = None, size: str = "1024x576", job_id: Optional[str] = None) -> bytes:
        logger.info("ProviderAdapter.generate_image called with prompt...")
        if self.impl:
            try:
                resp = await self.impl.generate_image(prompt)
                if isinstance(resp, dict):
                    image_path = resp.get("image_path")
                    if image_path and os.path.exists(image_path):
                        with open(image_path, "rb") as f:
                            return f.read()
                    for key in ("image_base64", "base64", "b64"):
                        b64 = resp.get(key)
                        if b64:
                            try:
                                return base64.b64decode(b64)
                            except Exception:
                                pass
                if isinstance(resp, (bytes, bytearray)):
                    return bytes(resp)
            except Exception as e:
                logger.warning(f"ProviderAdapter.generate_image: google impl failed: {e}")

        try:
            
            def _placeholder():
                img = Image.new("RGB", (100, 100), color="#f0f0f0")
                draw = ImageDraw.Draw(img)
                draw.rectangle([10, 10, 90, 90], outline="#666666", width=2)
                draw.text((50, 50), "AI", fill="#666666", anchor="mm")
                buf = _io.BytesIO()
                img.save(buf, format="PNG")
                return buf.getvalue()
            return await asyncio.to_thread(_placeholder)
        except Exception:
            return b""


# Global provider instance for other modules to import
provider = ProviderAdapter()