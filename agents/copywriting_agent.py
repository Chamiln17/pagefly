# agents/copywriting_agent.py

import json
import logging
from typing import Dict

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate

# Using JsonOutputParser to get structured output
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableLambda

logger = logging.getLogger(__name__)

# --- Prompt Template ---

# Using f-string for cleaner multi-line definition
copywriting_prompt_template = """

You are a world‑class direct‑response copywriter who specialises in e‑commerce storytelling in {language} language.

**Inputs:**

1.  **Marketing Angle/Strategy:**
    ```json
    {marketing_context}
    ```
    (This is either user-provided input or research summary. Use this as the primary theme.)

2.  **Product Image Analysis:**
    ```json
    {product_image_analysis_str}
    ```
    (Use this for details about product appearance, style, and visual features.)

3.  **Required Landing Page Structure & Copy Elements:**
    ```json
    {fixed_layout_input_str}
    ```
    (This defines the sections and the specific text elements needed for each.)

**Task:**

Generate concise, persuasive, and engaging copy for *all* the required text elements defined in the 'fixed_layout_input'.
- Write in the target language: **{language}**.
- Ensure the copy aligns strongly with the provided 'Marketing Angle/Strategy'.
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
        "marketing_context",  # Combined user input or research
        "product_image_analysis_str",
        "fixed_layout_input_str",
    ],
    # Although not strictly needed for JsonOutputParser, explicitly mentioning format helps
    # Note: JsonOutputParser doesn't use format_instructions directly like Pydantic parsers might.
    # Including it in the main template text is the primary way to guide the LLM here.
)


def invoke_copywriting_logic(llm: BaseChatModel, inputs: Dict) -> Dict:
    """Prepares input and invokes the copywriting LLM chain."""
    # 1. Determine Marketing Context
    marketing_context = inputs.get("marketing_angle_input")
    if not marketing_context:
        # Use research if angle not provided
        marketing_context = inputs.get(
            "marketing_strategy",
            {
                "summary": "No specific marketing angle provided; focus on general benefits."
            },
        )
    # Ensure it's a serializable format (string or dict for JSON dump)
    if not isinstance(marketing_context, (str, dict)):
        marketing_context = str(marketing_context)  # Fallback to string conversion
    # 2. Prepare other inputs (ensure they are strings for the prompt)
    image_analysis_str = json.dumps(inputs.get("product_image_analysis", {}), indent=2)
    fixed_layout_str = json.dumps(inputs.get("fixed_layout_input", {}), indent=2)
    language = inputs.get("language", "en")  # Default to English

    # 3. Create the chain dynamically for this invocation
    copywriting_chain = copywriting_prompt | llm | copy_output_parser

    # 4. Invoke
    try:
        # Prepare final input dictionary for the chain
        chain_input = {
            "language": language,
            "marketing_context": json.dumps(marketing_context, indent=2)
            if isinstance(marketing_context, dict)
            else marketing_context,
            "product_image_analysis_str": image_analysis_str,
            "fixed_layout_input_str": fixed_layout_str,
        }
        generated_copy = copywriting_chain.invoke(chain_input)
        # Ensure the output is a dictionary
        if not isinstance(generated_copy, dict):
            logger.warning(
                f"Warning: Copywriting output was not a dict: {type(generated_copy)}"
            )
            # Attempt to parse if it looks like a JSON string
            if isinstance(generated_copy, str):
                try:
                    generated_copy = json.loads(generated_copy)
                except json.JSONDecodeError:
                    logger.error(
                        "Error: Failed to parse copywriting output string as JSON."
                    )
                    return {
                        "error": "Copywriting output format error",
                        "raw_output": generated_copy,
                    }
            else:  # Not a dict or string, return error
                return {
                    "error": "Copywriting output format error",
                    "raw_output": str(generated_copy),
                }
        return generated_copy
    except Exception as e:
        logger.exception("Copywriting chain invocation failed")
        return {"error": f"LLM invocation failed: {e}"}


def get_copywriting_agent_runnable(llm: BaseChatModel):
    """Creates the runnable for the copywriting agent."""

    # This agent needs multiple inputs from the state dictionary
    def _wrapped_invoke(state_dict: Dict):
        # Pass the relevant parts of the state directly to the logic function
        return invoke_copywriting_logic(llm, state_dict)

    return RunnableLambda(_wrapped_invoke)
