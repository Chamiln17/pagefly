# agents/coder_agent.py (Revised for Robustness with Fixed Layout + Generated Copy)

import json
import logging
from typing import Dict, List

from langchain_core.language_models import BaseChatModel

# Using PromptTemplate is less direct here since we build messages manually
# from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import HumanMessage, SystemMessage

from agents.copywriting_agent import format_price

logger = logging.getLogger(__name__)

# --- System Prompt ---
# Defines the core role and requirements

# --- Simplified System Prompt (Use this one) ---
codegen_system_prompt = """You are an expert frontend developer. Your task is to generate a complete, single-file HTML page based on a structural definition and provided text content (copy). An optional inspiration image URL may provide styling guidance.

**Inputs (Provided in User Message):**
- {LANGUAGE}: Determines document language attribute ('en', 'fr', etc.).
- {COLOR_PRIMARY}, {COLOR_SECONDARY}, {COLOR_BACKGROUND}: Use as CSS variables (--clr-primary, etc.).
- {COPY_JSON}: JSON object with nested sections containing the text copy for each element. Contains image placeholders like `[IMAGE: Description...]`.
- {DIRECTION}: 'ltr' or 'rtl', derived from language.

**Core Task:**
- Generate full HTML code, including CSS in `<style>` tags in the `<head>`.
- Implement the structure defined in the 'Page Structure Definition' (provided in user message). Use semantic HTML tags.
- Populate HTML elements precisely with text from the 'Generated Copy Content' JSON (provided in user message), mapping keys correctly. Handle sections with list items.
- **Styling:**
    - If an 'Inspiration Image' URL is provided, use it as a strong reference for visual style (colors, fonts, general feel).
    - If no image is provided, use the specified CSS color variables (--clr-primary, --clr-secondary, --clr-background) to create a clean, modern, professional default style.
    - Ensure the page is reasonably responsive using standard CSS (e.g., flexbox/grid, max-width containers, relative units like rem/%). Avoid fixed pixel widths for layout.
- **Image Placeholders:** Leave image placeholders like `[IMAGE: Description...]` exactly as they appear in the COPY_JSON within the generated HTML. DO NOT create `<img>` tags for them.
- **Output Format:** Output *only* the raw HTML code, starting *exactly* with `<!DOCTYPE html>` and ending with `</html>` no "```" and not "html". No explanations, comments outside code, or markdown.
"""
# # --- Helper to build messages ---


def build_coder_messages(
    fixed_layout: Dict,
    generated_copy: Dict,
    inspiration_image_url: str = None,
    price: str = "not provided",
) -> List:
    """Builds the message list for the coder agent LLM."""

    # Prepare the data payloads as JSON strings for the prompt
    fixed_layout_str = json.dumps(fixed_layout, indent=2)
    generated_copy_str = json.dumps(generated_copy, indent=2)

    # Construct the user message content parts
    user_content_parts = [
        {
            "type": "text",
            "text": "**Page Structure Definition:**\n```json\n"
            + fixed_layout_str
            + "\n```",
        },
        {
            "type": "text",
            "text": "**Generated Copy Content:**\n```json\n"
            + generated_copy_str
            + "\n```",
        },
        {
            "type": "text",
            "text": f"**Product Price:** {price} (show this exact price and currency on the page)",
        },
        {
            "type": "text",
            "text": "Generate the HTML code following all instructions in the system prompt, using the structure and copy provided above.",
        },
    ]

    # Add image if provided
    if inspiration_image_url:
        try:
            # Basic check if URL seems valid before adding
            if inspiration_image_url.startswith(("http://", "https://")):
                user_content_parts.append(
                    {"type": "text", "text": "**Inspiration Image:**"}
                )
                user_content_parts.append(
                    {"type": "image_url", "image_url": {"url": inspiration_image_url}}
                )
                user_content_parts.append(
                    {
                        "type": "text",
                        "text": "Use the image above for visual style guidance.",
                    }
                )
            else:
                logger.warning(
                    f"Warning: Invalid inspiration image URL format provided to coder: {inspiration_image_url}"
                )
                user_content_parts.append(
                    {
                        "type": "text",
                        "text": "**Inspiration Image:** (URL not provided or invalid format - use default style)",
                    }
                )
        except Exception as img_err:
            logger.error(
                f"Warning: Error processing inspiration image URL {inspiration_image_url}: {img_err}"
            )
            user_content_parts.append(
                {
                    "type": "text",
                    "text": "**Inspiration Image:** (Error processing URL - use default style)",
                }
            )

    else:
        user_content_parts.append(
            {
                "type": "text",
                "text": "**Inspiration Image:** None provided - use default clean, modern style.",
            }
        )

    return [
        SystemMessage(content=codegen_system_prompt),
        HumanMessage(content=user_content_parts),
    ]


# --- Core Logic Function ---


def invoke_coder_logic(llm: BaseChatModel, inputs: Dict) -> str:
    """Prepares inputs and invokes the coder LLM chain."""

    fixed_layout = inputs.get("fixed_layout_input")
    generated_copy = inputs.get("generated_copy")
    # Try to get image URL from fixed_layout first, then top-level state
    inspiration_image_url = inputs.get("fixed_layout_input", {}).get(
        "inspiration_image"
    ) or inputs.get("product_image_url")  # Assumes state might have product_image_url

    # Basic validation
    if not fixed_layout or not generated_copy:
        logger.error("Error: Coder agent missing fixed_layout_input or generated_copy.")
        return "<!-- Error: Missing required layout or copy input. -->"
    # Add more specific validation if needed (e.g., check if 'sections' key exists)
    if not isinstance(fixed_layout, dict) or not isinstance(generated_copy, dict):
        logger.error(
            "Error: Coder agent received invalid input types for layout or copy."
        )
        return "<!-- Error: Invalid input type for layout or copy. -->"
    if "sections" not in fixed_layout or "sections" not in generated_copy:
        logger.error(
            "Error: Coder input 'sections' key missing in fixed_layout or generated_copy."
        )
        return "<!-- Error: Missing 'sections' key in layout or copy input. -->"

    # Build the messages for the LLM call
    messages = build_coder_messages(
        fixed_layout, generated_copy, inspiration_image_url, format_price(inputs)
    )

    try:
        response = llm.invoke(messages)
        generated_html = response.content
        # Basic check if output looks like HTML
        if not generated_html or not generated_html.strip().lower().startswith(
            "<!doctype html>"
        ):
            logger.warning(
                f"Warning: Coder output doesn't start with <!DOCTYPE html>:\n{generated_html[:200]}..."
            )
            # Return the potentially flawed output anyway, or an error comment
            # return f"<!-- Error: Generated output may not be valid HTML -->\n{generated_html}"
    except Exception as e:
        logger.error(f"Error invoking coder LLM: {e}")
        generated_html = f"<!-- Error during code generation: {e} -->"

    return generated_html


# --- Runnable Definition ---


def get_codegen_agent_runnable(llm: BaseChatModel):
    """Creates the runnable for the HTML/CSS generation agent."""

    def _wrapped_invoke(state_dict: Dict):
        # Ensure required keys are present in the state dictionary before calling
        if "fixed_layout_input" not in state_dict or "generated_copy" not in state_dict:
            logger.error(
                "Error: State missing 'fixed_layout_input' or 'generated_copy' for coder agent."
            )
            # Return error HTML directly, don't invoke logic
            return "<!-- Error: Graph state missing required inputs for code generation. -->"

        # Pass relevant parts of the state to the logic function
        return invoke_coder_logic(llm, state_dict)

    return RunnableLambda(_wrapped_invoke)
