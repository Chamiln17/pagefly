# agents/copywriting_agent.py

import json
from typing import Dict

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda

from core.state import format_price

copywriting_prompt_template = """

You are a world‑class direct‑response copywriter who specialises in e‑commerce storytelling in {language} language.

**Inputs:**

1.  **Marketing Angle:**
    ```json
    {marketing_context}
    ```
    (Given by the user or derived from research. Use this as the primary theme.)

2.  **Product Image Analysis:**
    ```json
    {product_image_analysis_str}
    ```
    (Use this for details about product appearance, style, and visual features.)

3.  **Price:** {price}
    (Use this exact price and currency wherever the copy mentions the price.)

4.  **Required Landing Page Structure & Copy Elements:**
    ```json
    {fixed_layout_input_str}
    ```
    (This defines the sections and the specific text elements needed for each.)

**Task:**

Generate concise, persuasive, and engaging copy for *all* the required text elements defined in the 'fixed_layout_input'.
- Write in the target language: **{language}**.
- Ensure the copy aligns strongly with the provided 'Marketing Angle'.
- Incorporate relevant details or style cues from the 'Product Image Analysis'.
- Match the tone appropriate for the product and marketing context (e.g., professional, playful, urgent).
- RETURN ONLY THE COPY—NO STYLES, NO LAYOUT CODE. Deliver one JSON object with these exact keys
- **Be Concise:** Keep headlines punchy and descriptions brief (e.g., 1-2 sentences maximum per description field). Focus on the core benefit or feature. Avoid overly long paragraphs.
**Output Format:**

Output *only* a single JSON object.
- The main key should be `"sections"`, containing a list of section objects.
- Each section object in the list should correspond to a section in the 'fixed_layout_input' and contain:
    - `"id"`: The original section ID (e.g., "hero", "features").
    - `"type"`: The original section type (e.g., "hero_banner").
    - `"copy"`: A JSON object containing the generated text for that section. The keys in the `"copy"` object should be the element names from the original `required_copy` list (e.g., "headline", "subheadline").
- **For sections with multiple items** (defined by `required_copy_per_item` in the input):
    - The section object should contain `"items"` instead of `"copy"`.
    - `"items"` should be a list where each element represents an item.
    - Each item in the `"items"` list should have a `"copy"` object containing the generated text for that item (e.g., `{{"copy": {{"title": "...", "description": "..."}}}}`). Generate the appropriate number of items based on the section type or input hints.

**Example Output Structure (based on hypothetical input):**
```json
{{
  "sections": [
    {{
      "id": "hero",
      "type": "hero_banner",
      "copy": {{
        "headline": "Generated Headline Text...",
        "subheadline": "Generated Subheadline Text...",
        "button_text": "Generated Button Text"
      }}
    }},
    {{
      "id": "features",
      "type": "feature_list_3_items",
      "items": [
        {{
          "copy": {{
            "title": "Generated Feature 1 Title",
            "description": "Generated Feature 1 Description..."
          }}
        }},
        {{
          "copy": {{
            "title": "Generated Feature 2 Title",
            "description": "Generated Feature 2 Description..."
          }}
        }},
        {{
          "copy": {{
            "title": "Generated Feature 3 Title",
            "description": "Generated Feature 3 Description..."
          }}
        }}
      ]
    }},
    {{
      "id": "cta",
      "type": "call_to_action_simple",
      "copy": {{
         "headline": "Generated CTA Headline...",
         "button_text": "Generated CTA Button Text"
      }}
    }}
    // ... etc. for all sections defined in the input layout
  ]
}}
Generate the JSON object now based on the provided inputs. Ensure every required element from the layout input has a corresponding key-value pair in your output.
"""
copy_output_parser = JsonOutputParser()
copywriting_prompt = PromptTemplate(
    template=copywriting_prompt_template,
    input_variables=[
        "language",
        "marketing_context",
        "product_image_analysis_str",
        "fixed_layout_input_str",
        "price",
    ],
)


def get_copywriting_agent_runnable(llm: BaseChatModel):
    """Runnable taking the graph state and returning the copy as a dict; raises
    when the model's reply is not JSON."""
    chain = copywriting_prompt | llm | copy_output_parser

    def write_copy(state: Dict):
        marketing_context = state.get("marketing_angle") or state.get(
            "marketing_research"
        )
        return chain.invoke(
            {
                "language": state.get("language", "en"),
                "marketing_context": json.dumps(marketing_context, indent=2)
                if isinstance(marketing_context, dict)
                else marketing_context,
                "product_image_analysis_str": json.dumps(
                    state.get("product_image_descriptions") or [], indent=2
                ),
                "fixed_layout_input_str": json.dumps(
                    state.get("fixed_layout_input", {}), indent=2
                ),
                "price": format_price(state),
            }
        )

    return RunnableLambda(write_copy)
