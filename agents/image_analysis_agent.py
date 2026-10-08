# agents/image_analysis_agent.py (Refactored for LangGraph)

import os
import json
from dotenv import load_dotenv
from typing import Dict, Optional
from pydantic import BaseModel  # Keep Pydantic for structure

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableLambda


# Keep Pydantic model for structured description output
class ProductDescription(BaseModel):
    image_url: str
    product: str  # Product name associated with this image
    description: str  # Generated description


# --- Core Logic ---
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
    # Ensure the image URL is valid before proceeding
    if not image_url or not image_url.startswith(("http://", "https://")):
        # Or handle file paths if needed, but URLs are more common for agents
        raise ValueError(f"Invalid or missing image URL: {image_url}")

    user_content = [
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


def invoke_single_image_analysis(
    llm: ChatOpenAI, image_url: str, product_name: str
) -> Optional[ProductDescription]:
    """Analyzes a single image using the provided LLM."""
    try:
        messages = build_image_analysis_messages(image_url)
        response = llm.invoke(messages)
        description_text = response.content

        # Create the structured output object
        product_desc = ProductDescription(
            image_url=image_url, product=product_name, description=description_text
        )
        # --- Removed file writing side effect ---
        return product_desc
    except ValueError as ve:
        print(f"Skipping image analysis due to invalid URL: {ve}")
        return None  # Return None or raise error if URL is invalid
    except Exception as e:
        print(f"Error analyzing image {image_url}: {e}")
        # Optionally return an error structure or raise exception
        return ProductDescription(
            image_url=image_url,
            product=product_name,
            description=f"Error analyzing image: {e}",
        )


# --- Runnable Creation Function ---
def get_image_analysis_runnable(llm: ChatOpenAI):
    """
    Creates a runnable that takes a state dict and performs image analysis.
    Expects 'product_image_urls' (list of strings) and 'product_name' in the input dict.
    Returns a dictionary containing 'product_image_descriptions' (list of dicts).
    """

    def _wrapped_invoke(state_dict: Dict) -> Dict:
        # --- Start Additions/Modifications ---
        if not isinstance(state_dict, dict):
            print("Error: Image Analysis node received non-dict input.")
            return {
                "product_image_descriptions": [{"error": "Invalid node input type"}]
            }

        image_urls = state_dict.get("product_image_urls")  # Use .get() for safety
        product_name = state_dict.get("product_name", "Unknown Product")

        if not image_urls or not isinstance(image_urls, list):
            print(
                f"Warning: 'product_image_urls' missing or not a list in state: {image_urls}"
            )
            # Return empty list but don't set error_message in state here, let node handle state
            return {"product_image_descriptions": []}
        # --- End Additions/Modifications ---

        descriptions_list = []  # List to hold analysis dictionaries
        print(f"--- Analyzing {len(image_urls)} image(s) for '{product_name}' ---")
        for url in image_urls:
            # Call the core logic for each image
            analysis_obj = invoke_single_image_analysis(llm, url, product_name)

            if (
                analysis_obj
            ):  # Check if analysis returned something (could be None on error)
                # Convert the Pydantic object to a dictionary
                analysis_dict = analysis_obj.model_dump()

                # Now add the extra key to the dictionary
                analysis_dict["image_url_analyzed"] = url

                # Append the complete dictionary to the list
                descriptions_list.append(analysis_dict)
            else:
                # Handle case where analysis failed for a specific URL if needed
                print(f"Warning: Analysis failed or returned None for URL: {url}")
                # Optionally append an error dict:
                # descriptions_list.append({"error": "Analysis failed", "image_url_analyzed": url})

        return {"product_image_descriptions": descriptions_list}

    return RunnableLambda(_wrapped_invoke)


# --- Testing Block ---
if __name__ == "__main__":
    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found.")
    else:
        # Ensure you use a model capable of vision (like gpt-4o)
        test_llm = ChatOpenAI(model="gpt-4o", max_tokens=300)
        image_analyzer_runnable = get_image_analysis_runnable(test_llm)

        # Test with one or more image URLs
        test_image_urls = [
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSlqv-_EDT0T3rwudmcvzDrJ5ihchnZWrie_w&s",
            # Add another image URL here if you have one for testing
            # "https://example.com/another_image.jpg"
        ]
        test_product_name = "Smart Coffee Mug"
        test_input_state = {
            "product_image_urls": test_image_urls,
            "product_name": test_product_name,
        }

        print("--- Testing Image Analysis Runnable ---")
        print(f"Input: {test_input_state}")
        try:
            analysis_result = image_analyzer_runnable.invoke(test_input_state)
            print("\nOutput (List of Product Descriptions):")
            print(json.dumps(analysis_result, indent=2))
        except Exception as e:
            print(f"An error occurred during test: {e}")
            import traceback

            traceback.print_exc()
