import os  
import json  
from dotenv import load_dotenv  
from langchain_openai import ChatOpenAI  
  
def build_messages_from_spec(layout_spec):  
    """  
    Create a system/user message list for GPT-4o, including an image if provided.  
    """  
    # System prompt (optional but recommended)  
    system_content = (  
        "You are an expert frontend developer. "  
        "Given a layout spec for a landing page and, if provided, an inspiration image, "  
        "generate the corresponding HTML and CSS. "  
        "Match the visual style of the inspiration image if included. "  
        "Always include a call-to-action (CTA): use the spec if present, otherwise invent a suitable generic CTA."  
        "Output only the raw HTML, CSS (in <style>), and minimal JS if needed—no explanations."  
        "Output only the raw HTML code starting directly with <!DOCTYPE html>. Do not include explanations, markdown formatting like ```html, or anything before or after the code block."
        "If the layout spec is empty, output a simple HTML page with a title and a message indicating no layout was provided."
        "If the layout spec is invalid, output a simple HTML page with a title and a message indicating the layout spec was invalid."
        
    )  
  
    # Build user content list (may have text + image parts)  
    user_content = [  
        {"type": "text", "text":  
            f"Here is the layout specification (JSON):\n{json.dumps(layout_spec, indent=2)}"  
        }  
    ]  
  
    # Add image if present  
    inspiration_image = layout_spec.get('inspiration_image')  
    if inspiration_image:  
        user_content.append({"type": "image_url", "image_url": {"url": inspiration_image}})       
    # Add instruction  
    user_content.append(  
        {"type": "text", "text":  
            "Use the provided layout spec and image. For the code output, match the style (colors, fonts, layout) shown in the image if provided. Output a single HTML file, with CSS in <style> tags, begin with <!DOCTYPE html>."  
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
