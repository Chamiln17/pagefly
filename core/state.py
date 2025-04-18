from typing import TypedDict, List, Optional, Dict

class PageState(TypedDict):
    # Initial user inputs
    product_description: str
    target_audience: str
    preferences: Optional[Dict] # e.g., {'style': 'modern', 'main_color': 'blue'}

    # Output from Agent 1 (Layout Researcher)
    layout_spec: Optional[Dict] # This will hold the JSON layout structure

    # Output from Agent 2 (Code Generator)
    landing_page_code: Optional[Dict] # e.g., {'html': ..., 'css': ...} or {'react': ...}

    # Output from Agent 3 (Evaluator)
    evaluation_report: Optional[str]
    improved_code: Optional[Dict]

    # Output from Agent 4 (Suggestor)
    suggestions: Optional[List[Dict]]

    # For tracking errors
    error_message: Optional[str]

    # We might add more keys as we build, like intermediate steps or agent names