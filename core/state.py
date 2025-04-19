# core/state.py (Updated)

from typing import TypedDict, List, Optional, Dict

class PageState(TypedDict):
    # --- Inputs (From User/Config) ---
    product_description: Optional[str] # Might be needed for research
    product_image_url: Optional[str]   # URL for image analysis
    marketing_angle_input: Optional[str] # Provided by user (optional)
    fixed_layout_input: Dict # User-provided layout structure (e.g., JSON describing sections)
    language: str              # Target language for copy (e.g., 'en')
    # Removed 'preferences' as theme might come from image analysis or fixed layout style

    # --- Agent Outputs ---
    # Marketing Research Agent Output (if run)
    marketing_strategy: Optional[Dict] # Researched angles, keywords, trends

    # Image Analysis Agent Output
    product_image_analysis: Optional[Dict] # Description, features seen, style notes

    # Copywriting Agent Output
    generated_copy: Optional[Dict] # Structured copy (e.g., {'hero_headline': '...', 'feature_1_desc': '...'})

    # HTML Generation Agent Output (previously landing_page_code)
    generated_html: Optional[str] # The final HTML string

    # --- Workflow Control & Errors ---
    # Removed layout_spec as it's now an input (fixed_layout_input)
    # Removed landing_page_code, replaced by generated_html
    # Keep evaluation/suggestion fields if you plan to add them later
    evaluation_report: Optional[str]
    suggestions: Optional[List[Dict]]
    error_message: Optional[str]