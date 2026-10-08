# core/state.py: the graph state shared by all nodes

from typing import TypedDict


class PageState(TypedDict):
    # Inputs
    product_name: str | None
    product_description: str | None
    product_image_urls: list[str] | None
    marketing_angle: str | None  # given by the user; research runs without it
    product_price: float | None
    currency: str | None  # e.g. 'DZD'
    fixed_layout_input: dict  # {"sections": [{id, type, required_copy, ...}]}
    language: str  # target language for the copy, e.g. 'en'

    # Outputs
    product_image_descriptions: list[dict] | None  # one analysis per image
    marketing_research: dict | None  # research that yields the Marketing Angle
    generated_copy: dict | None
    generated_html: str | None
    check_problems: list[str] | None  # one message per problem; [] = passed
    repair_passes: int | None  # the repair agent runs at most once
    error_message: str | None


def format_price(state: dict) -> str:
    """'4500.0 DZD', or 'not provided' when the state has no price."""
    if state.get("product_price") is None:
        return "not provided"
    return f"{state['product_price']} {state.get('currency') or ''}".strip()
