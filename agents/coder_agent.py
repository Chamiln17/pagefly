# agents/coder_agent.py (Refactored for LangGraph Integration)

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


# --- NEW Runnable Creation Function ---
def get_codegen_agent_runnable(llm: ChatOpenAI):
    """
    Creates a LangChain runnable for the code generation agent.
    This runnable expects a dictionary containing 'layout_spec'.
    """
    # Define the function that will be wrapped by RunnableLambda
    # It takes the dictionary input from the graph state
    def _wrapped_invoke(input_dict: dict):
        layout_spec = input_dict.get("layout_spec") # Extract the spec
        if not layout_spec:
             return "<!DOCTYPE html><html><head><title>Error</title></head><body><h1>Error: Layout specification missing in input.</h1></body></html>"
        # Call the core logic, passing the llm and extracted spec
        return invoke_codegen_logic(llm, layout_spec)

    # Return the RunnableLambda
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