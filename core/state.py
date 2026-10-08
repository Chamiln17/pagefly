# core/state.py: the graph state shared by all nodes

from typing import Dict, List, Optional, TypedDict


class PageState(TypedDict):
    # Inputs
    product_name: Optional[str]
    product_description: Optional[str]
    product_image_urls: Optional[List[str]]
    marketing_angle: Optional[str]  # given by the user; research runs without it
    product_price: Optional[float]
    currency: Optional[str]  # e.g. 'DZD'
    fixed_layout_input: Dict  # {"sections": [{id, type, required_copy, ...}]}
    language: str  # target language for the copy, e.g. 'en'

    # Outputs
    product_image_descriptions: Optional[List[Dict]]  # one analysis per image
    marketing_research: Optional[Dict]  # research that yields the Marketing Angle
    generated_copy: Optional[Dict]
    generated_html: Optional[str]
    check_problems: Optional[List[str]]  # one message per problem; [] = passed
    repair_passes: Optional[int]  # the repair agent runs at most once
    error_message: Optional[str]


def format_price(state: Dict) -> str:
    """'4500.0 DZD', or 'not provided' when the state has no price."""
    if state.get("product_price") is None:
        return "not provided"
    return f"{state['product_price']} {state.get('currency') or ''}".strip()
