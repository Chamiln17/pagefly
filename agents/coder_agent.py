# agents/coder_agent.py: turns the layout and generated copy into one HTML page

import json
from typing import Any, Dict, List

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableLambda

from core.html_document import extract_html_document
from core.state import format_price


codegen_system_prompt = """You are an expert frontend developer. Your task is to generate a complete, single-file HTML page based on a structural definition and provided text content (copy).

**Inputs (Provided in User Message):**
- {LANGUAGE}: Determines document language attribute ('en', 'fr', etc.).
- {COLOR_PRIMARY}, {COLOR_SECONDARY}, {COLOR_BACKGROUND}: Use as CSS variables (--clr-primary, etc.).
- {COPY_JSON}: JSON object with nested sections containing the text copy for each element. Contains image placeholders like `[IMAGE: Description...]`.
- {DIRECTION}: 'ltr' or 'rtl', derived from language.

**Core Task:**
- Generate full HTML code, including CSS in `<style>` tags in the `<head>`.
- Implement the structure defined in the 'Page Structure Definition' (provided in user message). Use semantic HTML tags.
- **Section ids (required):** For every section in the 'Page Structure Definition', wrap that section in exactly one element whose `id` attribute equals the section's `id` value (e.g. `<section id="hero">`). Do not reuse these ids on other elements. A section without its id fails the page check.
- **Alt text (required):** Every `<img>` tag you write must have a non-empty, descriptive `alt` attribute.
- Populate HTML elements precisely with text from the 'Generated Copy Content' JSON (provided in user message), mapping keys correctly. Handle sections with list items.
- **Styling:**
    - Use the CSS color variables (--clr-primary, --clr-secondary, --clr-background) to create a clean, modern, professional style.
    - Ensure the page is reasonably responsive using standard CSS (e.g., flexbox/grid, max-width containers, relative units like rem/%). Avoid fixed pixel widths for layout.
- **Product Images (required):** Show the product images listed under 'Product Images' (provided in user message) as `<img>` tags, using each image's `src` URL exactly as given and a short `alt` text based on its description. Put them where the copy has image placeholders like `[IMAGE: Description...]`, and at least one in the first section.
- **Output Format:** Output *only* the raw HTML code, starting *exactly* with `<!DOCTYPE html>` and ending with `</html>` no "```" and not "html". No explanations, comments outside code, or markdown.
"""


def build_coder_messages(
    fixed_layout: Dict,
    generated_copy: Dict,
    price: str = "not provided",
    images: List[Dict] | None = None,
) -> List:
    """Builds the message list for the coder agent LLM. `images` holds one
    {"src", "alt"} per product image."""
    image_lines = "\n".join(
        f"- src: {img['src']}\n  alt: {img['alt']}" for img in images or []
    )
    user_content_parts: list[str | dict[Any, Any]] = [
        {
            "type": "text",
            "text": "**Page Structure Definition:**\n```json\n"
            + json.dumps(fixed_layout, indent=2)
            + "\n```",
        },
        {
            "type": "text",
            "text": "**Generated Copy Content:**\n```json\n"
            + json.dumps(generated_copy, indent=2)
            + "\n```",
        },
        {
            "type": "text",
            "text": f"**Product Price:** {price} (show this exact price and currency on the page)",
        },
        {
            "type": "text",
            "text": "**Product Images:**\n" + (image_lines or "None provided."),
        },
        {
            "type": "text",
            "text": "Generate the HTML code following all instructions in the system prompt, using the structure and copy provided above.",
        },
    ]
    return [
        SystemMessage(content=codegen_system_prompt),
        HumanMessage(content=user_content_parts),
    ]


def get_codegen_agent_runnable(llm: BaseChatModel):
    """Runnable taking the graph state and returning the page HTML; raises when
    the layout or copy has no 'sections' or the model fails."""

    def generate_html(state: Dict) -> str:
        fixed_layout = state.get("fixed_layout_input")
        generated_copy = state.get("generated_copy")
        if not isinstance(fixed_layout, dict) or "sections" not in fixed_layout:
            raise ValueError("HTML generation needs a layout with 'sections'.")
        if not isinstance(generated_copy, dict) or "sections" not in generated_copy:
            raise ValueError("HTML generation needs copy with 'sections'.")

        alt_by_url = {
            d["image_url"]: d["description"]
            for d in state.get("product_image_descriptions") or []
        }
        images = [
            {"src": url, "alt": alt_by_url.get(url) or state.get("product_name")}
            for url in state.get("product_image_urls") or []
        ]
        response = llm.invoke(
            build_coder_messages(
                fixed_layout, generated_copy, format_price(state), images
            )
        )
        return extract_html_document(str(response.content), "coder")

    return RunnableLambda(generate_html)
