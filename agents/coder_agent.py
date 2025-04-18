import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


def build_messages_from_spec(layout_spec):
    """
    Create a system/user message list for GPT-4o, including an image if provided.
    """
    # System prompt (optional but recommended)
    system_content = """
        You are an expert frontend developer specializing in creating modern, responsive landing pages. 
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
        
        9.  **Error Handling:** If the provided `layout_spec` is empty or clearly invalid, output a simple HTML page with a title and a message indicating the issue (e.g., "No layout provided." or "Invalid layout specification.").
        """

    # Build user content list (may have text + image parts)
    user_content = [
        {
            "type": "text",
            "text": f"Here is the layout specification (JSON):\n{json.dumps(layout_spec, indent=2)}",
        }
    ]

    # Add image if present
    inspiration_image = layout_spec.get("inspiration_image")
    if inspiration_image:
        user_content.append(
            {"type": "image_url", "image_url": {"url": inspiration_image}}
        )
    # Add instruction
    user_content.append(
        {
            "type": "text",
            "text": "Use the provided layout spec and image. For the code output, match the style (colors, fonts, layout) shown in the image if provided. Output a single HTML file, with CSS in <style> tags, begin with <!DOCTYPE html>.",
        }
    )

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def run_codegen_with_image(layout_spec):
    llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
    messages = build_messages_from_spec(layout_spec)
    result = llm.invoke(messages)
    return result.content


if __name__ == "__main__":
    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found.")
    else:
        # Example: with image ("file://" path, or use HTTPS URL if deployed in the cloud)

        # Replace with your image path or URL
        sample_layout_spec = {
            "inspiration_image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQt0CiX0sVdMAHRACvWpx1EqZNAbqIdvuT5nHsDWnOwjK33PjGdb4nyxGzXYDxzSAjYXjw&usqp=CAU",  # or "https://..." if hosted
            "sections": [
                {
                    "type": "hero",
                    "content_ideas": [
                        "Hydrate Smarter!",
                        "Track your water intake effortlessly with GlowBottle.",
                        "CTA Button: 'Get Yours Now'",
                        "[Hero Image Placeholder: Smart Water Bottle]",
                    ],
                },
                {
                    "type": "features",
                    "content_ideas": [
                        "Feature 1: Automatic Hydration Tracking",
                        "Feature 2: Customizable Glow Reminders",
                        "Feature 3: Syncs with Health Apps",
                    ],
                },
                {
                    "type": "how_it_works",
                    "content_ideas": [
                        "Step 1: Fill the bottle",
                        "Step 2: Drink throughout the day",
                        "Step 3: Check stats on app",
                    ],
                },
                {
                    "type": "testimonials",
                    "content_ideas": [
                        "[Testimonial 1: Quote + Name]",
                        "[Testimonial 2: Quote + Name]",
                    ],
                },
                {
                    "type": "cta",
                    "content_ideas": [
                        "Ready to Improve Your Hydration?",
                        "Button: 'Order GlowBottle Today'",
                    ],
                },
            ],
            "theme_suggestions": ["modern", "techy", "cyan and dark grey"],
        }
        print("--- Testing Code Generation Agent with Image Inspiration ---")
        result = run_codegen_with_image(sample_layout_spec)
        print("\n---- Generated Code ----")
        print(result)
