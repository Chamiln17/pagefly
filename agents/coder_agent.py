# agents/coder_agent.py (Revised for Robustness with Fixed Layout + Generated Copy)

import os
import json
from dotenv import load_dotenv
from typing import Dict, List, Any

from langchain_openai import ChatOpenAI
# Using PromptTemplate is less direct here since we build messages manually
# from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import HumanMessage, SystemMessage

# --- System Prompt ---
# Defines the core role and requirements

codegen_system_prompt = """
You are an expert frontend developer. Your task is to generate a complete, single-file HTML page based on a specified structure and provided text content (copy). You might also receive an optional inspiration image URL for styling guidance.

**Inputs:**

1.  **Page Structure Definition (`fixed_layout_input`):**
    ```json
    {fixed_layout_input_str}
    ```
    (This defines the sections, their types, and the required copy elements/structure within each section, like section IDs and copy keys.)

2.  **Generated Copy Content (`generated_copy`):**
    ```json
    {generated_copy_str}
    ```
    (This JSON object contains the actual text content for each element defined in the page structure, mapped by section ID and copy key.)

3.  **Optional Inspiration Image URL (`inspiration_image_url`):**
    {inspiration_image_prompt_part}
    (If provided, use this image as a strong reference for visual style: colors, fonts, element shapes, layout.)


**Core Requirements:**
1.  **Implement Layout:** Accurately translate the provided JSON `layout_spec` into semantic HTML sections (`<section>`, `<header>`, `<footer>`, etc.). Represent all specified sections and their `content_ideas`.
2.  **Visual Style Matching:** If an `inspiration_image` URL is provided, meticulously match its visual style, focusing on:
    *   Color Palette: Use the exact or very similar colors for backgrounds, text, buttons, and accents.
    *   Typography: Match font styles (serif/sans-serif, weight) and relative sizes. Use a modern, clean sans-serif font stack like `font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;` as a base unless the image strongly dictates otherwise.
    *   Element Shapes: Mimic button shapes, card styles (sharp/rounded corners), etc.
    *   Layout Approach: Replicate the overall spacing, alignment, and visual flow seen in the image.
3.  **Responsiveness:** Ensure the generated page is fully responsive and looks professional on both desktop and mobile devices. Use modern CSS techniques like Flexbox and Grid for layout within sections. Include basic media queries (e.g., around 768px) to adjust layout (e.g., stack columns), font sizes, and spacing for smaller screens.
4.  **Placeholders:** Use the specific text provided in the `content_ideas` array from the layout specification. For image placeholders, use the description from the spec in the `alt` text (e.g., `alt='Hero Image: Smart Water Bottle'`) and a standard placeholder service (e.g., `https://via.placeholder.com/800x400`). For text placeholders like testimonials, use the format given in the spec (e.g., `'[Testimonial 1: Quote + Name]'`).
5.  **CSS:** Embed all CSS within `<style>` tags in the HTML `<head>`. Keep CSS clean, well-organized, and use classes effectively. Avoid inline styles unless absolutely necessary.
6.  **JavaScript:** Include minimal, vanilla JavaScript within `<script>` tags before the closing `</body>` *only* if required for basic interactivity explicitly suggested by the `content_ideas` (like simple toggles). Do not include JS otherwise.
7.  **Call-to-Action (CTA):** Always include at least one clear CTA. Use the CTA details from the `layout_spec` if present; otherwise, invent a suitable, generic CTA relevant to the page context.
8.  **Output Format:** Output *only* the raw HTML code, starting *exactly* with `<!DOCTYPE html>` and ending with `</html>`. Do not include *any* explanations, comments outside the code, markdown formatting (like ```html), or any text before or after the HTML code itself.
9.  **Error Handling:** If the provided `layout_spec` is empty or clearly invalid, output a simple HTML page with a title and a message indicating the issue (e.g., "No layout provided." or "Invalid layout specification.").
"""

# --- Helper to build messages ---

def build_coder_messages(fixed_layout: Dict, generated_copy: Dict, inspiration_image_url: str = None) -> List:
    """Builds the message list for the coder agent LLM."""

    # Prepare the data payloads as JSON strings for the prompt
    fixed_layout_str = json.dumps(fixed_layout, indent=2)
    generated_copy_str = json.dumps(generated_copy, indent=2)

    # Construct the user message content parts
    user_content_parts = [
        {"type": "text", "text": "**Page Structure Definition:**\n```json\n" + fixed_layout_str + "\n```"},
        {"type": "text", "text": "**Generated Copy Content:**\n```json\n" + generated_copy_str + "\n```"},
        {"type": "text", "text": "Generate the HTML code following all instructions in the system prompt, using the structure and copy provided above."}
    ]

    # Add image if provided
    if inspiration_image_url:
        try:
            # Basic check if URL seems valid before adding
            if inspiration_image_url.startswith(('http://', 'https://')):
                user_content_parts.append({"type": "text", "text": "**Inspiration Image:**"})
                user_content_parts.append({"type": "image_url", "image_url": {"url": inspiration_image_url}})
                user_content_parts.append({"type": "text", "text": "Use the image above for visual style guidance."})
            else:
                 print(f"Warning: Invalid inspiration image URL format provided to coder: {inspiration_image_url}")
                 user_content_parts.append({"type": "text", "text": "**Inspiration Image:** (URL not provided or invalid format - use default style)"})
        except Exception as img_err:
             print(f"Warning: Error processing inspiration image URL {inspiration_image_url}: {img_err}")
             user_content_parts.append({"type": "text", "text": "**Inspiration Image:** (Error processing URL - use default style)"})

    else:
        user_content_parts.append({"type": "text", "text": "**Inspiration Image:** None provided - use default clean, modern style."})

    return [
        SystemMessage(content=codegen_system_prompt),
        HumanMessage(content=user_content_parts)
    ]


# --- Core Logic Function ---

def invoke_coder_logic(llm: ChatOpenAI, inputs: Dict) -> str:
    """Prepares inputs and invokes the coder LLM chain."""

    fixed_layout = inputs.get("fixed_layout_input")
    generated_copy = inputs.get("generated_copy")
    # Try to get image URL from fixed_layout first, then top-level state
    inspiration_image_url = inputs.get("fixed_layout_input", {}).get("inspiration_image") \
                            or inputs.get("product_image_url") # Assumes state might have product_image_url

    # Basic validation
    if not fixed_layout or not generated_copy:
        print("Error: Coder agent missing fixed_layout_input or generated_copy.")
        return "<!-- Error: Missing required layout or copy input. -->"
    # Add more specific validation if needed (e.g., check if 'sections' key exists)
    if not isinstance(fixed_layout, dict) or not isinstance(generated_copy, dict):
        print("Error: Coder agent received invalid input types for layout or copy.")
        return "<!-- Error: Invalid input type for layout or copy. -->"
    if 'sections' not in fixed_layout or 'sections' not in generated_copy:
        print("Error: Coder input 'sections' key missing in fixed_layout or generated_copy.")
        return "<!-- Error: Missing 'sections' key in layout or copy input. -->"


    # Build the messages for the LLM call
    messages = build_coder_messages(fixed_layout, generated_copy, inspiration_image_url)

    try:
        response = llm.invoke(messages)
        generated_html = response.content
        # Basic check if output looks like HTML
        if not generated_html or not generated_html.strip().lower().startswith("<!doctype html>"):
             print(f"Warning: Coder output doesn't start with <!DOCTYPE html>:\n{generated_html[:200]}...")
             # Return the potentially flawed output anyway, or an error comment
             # return f"<!-- Error: Generated output may not be valid HTML -->\n{generated_html}"
    except Exception as e:
        print(f"Error invoking coder LLM: {e}")
        generated_html = f"<!-- Error during code generation: {e} -->"

    return generated_html


# --- Runnable Definition ---

def get_codegen_agent_runnable(llm: ChatOpenAI):
    """Creates the runnable for the HTML/CSS generation agent."""
    def _wrapped_invoke(state_dict: Dict):
        # Ensure required keys are present in the state dictionary before calling
        if "fixed_layout_input" not in state_dict or "generated_copy" not in state_dict:
             print("Error: State missing 'fixed_layout_input' or 'generated_copy' for coder agent.")
             # Return error HTML directly, don't invoke logic
             return "<!-- Error: Graph state missing required inputs for code generation. -->"

        # Pass relevant parts of the state to the logic function
        return invoke_coder_logic(llm, state_dict)

    return RunnableLambda(_wrapped_invoke)


# --- Testing Block ---
# (Keep the same testing block from the previous version, it should work with this structure)
if __name__ == "__main__":
    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found.")
    else:
        test_llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
        codegen_runnable = get_codegen_agent_runnable(test_llm)

        # --- Sample Inputs (Mimicking State) ---
        sample_state = {
            "fixed_layout_input": {
                 "inspiration_image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQt0CiX0sVdMAHRACvWpx1EqZNAbqIdvuT5nHsDWnOwjK33PjGdb4nyxGzXYDxzSAjYXjw&usqp=CAU",
                 "sections": [
                    {"id": "hero", "type": "hero_banner", "required_copy": ["headline", "subheadline", "button_text"]},
                    {"id": "problem", "type": "text_section", "required_copy": ["headline", "body_text"]},
                    {"id": "features", "type": "feature_list_3_items", "required_copy_per_item": ["title", "description"]},
                    {"id": "cta", "type": "call_to_action_simple", "required_copy": ["headline", "button_text"]}
                 ]
            },
            "generated_copy": {
                 "sections": [
                    {"id": "hero", "type": "hero_banner", "copy": {"headline": "Never Sip Cold Coffee Again!", "subheadline": "Keep your drink perfectly hot for hours with the Ember Smart Mug.", "button_text": "Discover Ember"}},
                    {"id": "problem", "type": "text_section", "copy": {"headline": "Tired of Cold Coffee?", "body_text": "Your busy day demands focus. Don't let lukewarm coffee ruin your flow. Standard mugs just don't keep up."}},
                    {"id": "features", "type": "feature_list_3_items", "items": [
                        {"copy": {"title": "Precision Temperature Control", "description": "Set your ideal temperature via the Ember app."}},
                        {"copy": {"title": "Extended Battery Life", "description": "Enjoy hours of perfect warmth on a single charge."}},
                        {"copy": {"title": "Sleek & Durable Design", "description": "Looks great on any desk and built to last."}}
                    ]},
                    {"id": "cta", "type": "call_to_action_simple", "copy": {"headline": "Upgrade Your Coffee Experience", "button_text": "Shop Smart Mugs"}}
                 ]
            },
            # product_image_url could also be a top-level key if preferred state structure
        }
        # --- End Sample Inputs ---

        print("--- Testing Coder Agent (Revised) ---")
        print("Sample State (Input):")
        print(json.dumps(sample_state, indent=2, default=str))

        try:
            generated_html_output = codegen_runnable.invoke(sample_state)
            print("\nOutput (Generated HTML):")
            # Add a basic check before printing/saving
            if isinstance(generated_html_output, str) and generated_html_output.strip().lower().startswith("<!doctype html>"):
                print(generated_html_output)
                with open("test_coder_output_revised.html", "w", encoding="utf-8") as f:
                    f.write(generated_html_output)
                print("\n--- Saved output to test_coder_output_revised.html ---")
            else:
                print("\n--- Output was not valid HTML ---")
                print(generated_html_output)

        except Exception as e:
            print(f"An error occurred: {e}")
            import traceback
            traceback.print_exc()
import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
# Import necessary LangChain components
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import HumanMessage, SystemMessage

# Keep your function that builds the message list - NO CHANGES NEEDED HERE
def build_messages_from_spec(layout_spec):
    """
    Create a system/user message list for GPT-4o, including an image if provided.
    """
    system_content = """You are an expert frontend developer specializing in creating modern, responsive landing pages.
Given a layout specification (JSON) for a landing page and, potentially, an inspiration image URL, generate the corresponding complete, single-file HTML code.

**Core Requirements:**
1.  **Implement Layout:** Accurately translate the provided JSON `layout_spec` into semantic HTML sections (`<section>`, `<header>`, `<footer>`, etc.). Represent all specified sections and their `content_ideas`.
2.  **Visual Style Matching:** If an `inspiration_image` URL is provided, meticulously match its visual style, focusing on:
    *   Color Palette: Use the exact or very similar colors for backgrounds, text, buttons, and accents.
    *   Typography: Match font styles (serif/sans-serif, weight) and relative sizes. Use a modern, clean sans-serif font stack like `font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;` as a base unless the image strongly dictates otherwise.
    *   Element Shapes: Mimic button shapes, card styles (sharp/rounded corners), etc.
    *   Layout Approach: Replicate the overall spacing, alignment, and visual flow seen in the image.
3.  **Responsiveness:** Ensure the generated page is fully responsive and looks professional on both desktop and mobile devices. Use modern CSS techniques like Flexbox and Grid for layout within sections. Include basic media queries (e.g., around 768px) to adjust layout (e.g., stack columns), font sizes, and spacing for smaller screens.
4.  **Placeholders:** Use the specific text provided in the `content_ideas` array from the layout specification. For image placeholders, use the description from the spec in the `alt` text (e.g., `alt='Hero Image: Smart Water Bottle'`) and a standard placeholder service (e.g., `https://via.placeholder.com/800x400`). For text placeholders like testimonials, use the format given in the spec (e.g., `'[Testimonial 1: Quote + Name]'`).
5.  **CSS:** Embed all CSS within `<style>` tags in the HTML `<head>`. Keep CSS clean, well-organized, and use classes effectively. Avoid inline styles unless absolutely necessary.
6.  **JavaScript:** Include minimal, vanilla JavaScript within `<script>` tags before the closing `</body>` *only* if required for basic interactivity explicitly suggested by the `content_ideas` (like simple toggles). Do not include JS otherwise.
7.  **Call-to-Action (CTA):** Always include at least one clear CTA. Use the CTA details from the `layout_spec` if present; otherwise, invent a suitable, generic CTA relevant to the page context.
8.  **Output Format:** Output *only* the raw HTML code, starting *exactly* with `<!DOCTYPE html>` and ending with `</html>`. Do not include *any* explanations, comments outside the code, markdown formatting (like ```html), or any text before or after the HTML code itself.
9.  **Error Handling:** If the provided `layout_spec` is empty or clearly invalid, output a simple HTML page with a title and a message indicating the issue (e.g., "No layout provided." or "Invalid layout specification.")."""

    # Build user content list (may have text + image parts)
    user_content = [
        {
            "type": "text",
            "text": f"Here is the layout specification (JSON):\n{json.dumps(layout_spec, indent=2)}",
        }
    ]
    inspiration_image = layout_spec.get("inspiration_image")
    if inspiration_image:
        user_content.append(
            {"type": "image_url", "image_url": {"url": inspiration_image}}
        )
    user_content.append(
        {
            "type": "text",
            "text": "Use the provided layout spec and image. For the code output, match the style (colors, fonts, layout) shown in the image if provided. Output a single HTML file, with CSS in <style> tags, begin with <!DOCTYPE html>.",
        }
    )
    # Ensure correct LangChain message format
    return [
        SystemMessage(content=system_content),
        HumanMessage(content=user_content),
    ]


# --- MODIFIED Core Logic Function ---
# Now accepts the llm instance as an argument
def invoke_codegen_logic(llm: ChatOpenAI, layout_spec: dict):
    """Handles message building and LLM invocation."""
    # Basic validation of layout_spec input
    if not isinstance(layout_spec, dict):
        return "<!DOCTYPE html><html><head><title>Error</title></head><body><h1>Error: Invalid layout specification format (not a dictionary).</h1></body></html>"
    if not layout_spec.get("sections") and not layout_spec.get("inspiration_image"): # Allow image-only for simplicity? Or require sections?
         # Handle potentially empty spec according to requirements in prompt
         return "<!DOCTYPE html><html><head><title>Invalid Layout</title></head><body><h1>Layout specification provided, but no sections found.</h1></body></html>"

    messages = build_messages_from_spec(layout_spec)
    result = llm.invoke(messages)
    return result.content


def get_codegen_agent_runnable(llm: ChatOpenAI):
    """Creates the runnable for the HTML/CSS generation agent."""
    def _wrapped_invoke(state_dict: Dict):
        # This wrapper function receives the full state dictionary from LangGraph.
        # It's responsible for calling the core logic with the correct parts of the state.

        # Add validation *before* calling the logic function
        if "fixed_layout_input" not in state_dict or "generated_copy" not in state_dict:
             print("Error inside _wrapped_invoke: State missing 'fixed_layout_input' or 'generated_copy'.")
             return "<!-- Error: Graph state missing required inputs for code generation. -->"

        # Pass relevant parts of the state (the whole state dict in this case,
        # as invoke_coder_logic expects 'inputs' dict) to the logic function.
        # invoke_coder_logic will then extract what it needs.
        return invoke_coder_logic(llm, state_dict)

    return RunnableLambda(_wrapped_invoke)


# --- UPDATED Testing Block ---
if __name__ == "__main__":
    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found.")
    else:
        # Sample layout spec (same as before)
        sample_layout_spec = {
            "inspiration_image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQt0CiX0sVdMAHRACvWpx1EqZNAbqIdvuT5nHsDWnOwjK33PjGdb4nyxGzXYDxzSAjYXjw&usqp=CAU",
            "sections": [
                {"type": "hero","content_ideas": ["Hydrate Smarter!","Track your water intake effortlessly with GlowBottle.","CTA Button: 'Get Yours Now'","[Hero Image Placeholder: Smart Water Bottle]",],},
                {"type": "features","content_ideas": ["Feature 1: Automatic Hydration Tracking","Feature 2: Customizable Glow Reminders","Feature 3: Syncs with Health Apps",],},
                {"type": "how_it_works","content_ideas": ["Step 1: Fill the bottle","Step 2: Drink throughout the day","Step 3: Check stats on app",],},
                {"type": "testimonials","content_ideas": ["[Testimonial 1: Quote + Name]","[Testimonial 2: Quote + Name]",],},
                {"type": "cta","content_ideas": ["Ready to Improve Your Hydration?","Button: 'Order GlowBottle Today'",],},
            ],
            "theme_suggestions": ["modern", "techy", "cyan and dark grey"],
        }

        print("--- Testing Code Generation Agent Runnable ---")
        try:
            # 1. Initialize LLM (only once for the test)
            test_llm = ChatOpenAI(model="gpt-4o", temperature=0.2)

            # 2. Get the runnable by calling the new function
            codegen_runnable = get_codegen_agent_runnable(test_llm)

            # 3. Prepare the input dictionary for the runnable
            # The key MUST match what the runnable expects ("layout_spec")
            runnable_input = {"layout_spec": sample_layout_spec}

            # 4. Invoke the runnable
            result = codegen_runnable.invoke(runnable_input)

            print("\n---- Generated Code ----")
            print(result)

        except Exception as e:
            print(f"An error occurred during testing: {e}")
            import traceback
            traceback.print_exc() # Print full traceback for debugging