# core/state.py (Corrected Version)

from typing import TypedDict, List, Optional, Dict

class PageState(TypedDict):
    # --- Inputs (From User/Config) ---
    product_name: Optional[str]        # Added: Name of the product being analyzed
    product_description: Optional[str] # Kept: Might be needed for research
    product_image_urls: Optional[List[str]] # List of image URLs for analysis (Input for image node)
    marketing_angle_input: Optional[str] # Provided by user (optional)
    fixed_layout_input: Dict # User-provided layout structure (e.g., JSON describing sections)
    language: str              # Target language for copy (e.g., 'en')
    # Removed redundant product_image_url

    # --- Agent Outputs ---
    # Image Analysis Agent Output
    product_image_descriptions: Optional[List[Dict]] # CORRECTED: List of analysis dicts (Output of image node)

    # Marketing Research Agent Output (if run)
    marketing_strategy: Optional[Dict] # Researched angles, keywords, trends (Output of research node)

    # Copywriting Agent Output
    generated_copy: Optional[Dict] # Structured copy (Output of copywriting node)

    # HTML Generation Agent Output
    generated_html: Optional[str] # The final HTML string (Output of coder node)

    # --- Workflow Control & Errors ---
    error_message: Optional[str]

    # --- Optional Future Fields ---
    # evaluation_report: Optional[str]
    # suggestions: Optional[List[Dict]]