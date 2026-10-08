# agents/image_analysis_agent.py: describes each product image

import logging
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ProductDescription(BaseModel):
    image_url: str
    product: str  # product name associated with this image
    description: str


image_analysis_system_prompt = """You are an expert visual marketing analyst. Analyze the provided product image to extract key marketing insights useful for writing copy.

Focus on:
- Product's primary function/use clearly depicted.
- Key visual features or unique selling points visible.
- Materials, texture, or build quality suggested by the visuals.
- Overall aesthetic, style, and mood evoked (e.g., modern, playful, luxurious, rugged, minimalist).
- Implied user lifestyle, context, or environment shown (e.g., office, outdoors, home).
- Dominant colors and their potential psychological impact (e.g., blue suggests trust, red suggests urgency).

Output your analysis as a concise JSON object containing only the following keys:
- "visual_summary": (String) A brief (1-2 sentence) overall description of the image's marketing message.
- "key_features_visible": (List of strings) Bullet points of tangible features seen.
- "style_mood_aesthetics": (String) Keywords describing the look and feel.
- "implied_context_user": (String) Description of the setting or likely user profile shown/implied.
- "color_psychology_notes": (String) Brief note on dominant colors and potential feelings evoked.

Be objective and base the analysis strictly on the visual content of the image. Ensure the output is ONLY the JSON object."""


def build_image_analysis_messages(image_url: str):
    """Builds messages for the image analysis agent."""
    if not image_url or not image_url.startswith(("http://", "https://")):
        raise ValueError(f"Invalid or missing image URL: {image_url}")
    user_content: list[str | dict[Any, Any]] = [
        {
            "type": "text",
            "text": "Describe the key visual elements of this product image relevant for marketing.",
        },
        {"type": "image_url", "image_url": {"url": image_url}},
    ]
    return [
        SystemMessage(content=image_analysis_system_prompt),
        HumanMessage(content=user_content),
    ]


def analyze_image(
    llm: BaseChatModel, image_url: str, product_name: str
) -> ProductDescription:
    """Analyzes a single image; raises when the URL is invalid or the model fails."""
    response = llm.invoke(build_image_analysis_messages(image_url))
    return ProductDescription(
        image_url=image_url, product=product_name, description=str(response.content)
    )


def get_image_analysis_runnable(llm: BaseChatModel):
    """Runnable taking 'product_image_urls' and 'product_name' and returning
    {'product_image_descriptions': [one dict per image]}."""

    def analyze_images(state: dict) -> dict:
        image_urls = state["product_image_urls"]
        product_name = state.get("product_name") or "Unknown Product"
        logger.info("Analyzing %d image(s) for '%s'", len(image_urls), product_name)
        descriptions = []
        for url in image_urls:
            analysis = analyze_image(llm, url, product_name).model_dump()
            analysis["image_url_analyzed"] = url
            descriptions.append(analysis)
        return {"product_image_descriptions": descriptions}

    return RunnableLambda(analyze_images)
