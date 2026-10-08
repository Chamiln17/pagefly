"""Bridge between the API request and the agent graph."""

from functools import cache

from core.llm import make_llm, make_search_tool
from core.state import PageState
from workflow.graph import create_graph

from .schemas import LandingPageParams

# One section definition per `is_*` switch, in page order.
SECTIONS = {
    "is_hero": {
        "id": "hero",
        "type": "hero",
        "required_copy": ["headline", "subheadline", "button_text"],
    },
    "is_feature": {
        "id": "features",
        "type": "feature_list",
        "required_copy": ["headline"],
        "required_copy_per_item": ["title", "description"],
    },
    "is_testimonials": {
        "id": "testimonials",
        "type": "testimonials",
        "required_copy": ["headline"],
        "required_copy_per_item": ["quote", "author"],
    },
    "is_pricing": {
        "id": "pricing",
        "type": "pricing",
        "required_copy": ["headline", "price_text", "button_text"],
    },
    "is_contact": {
        "id": "contact",
        "type": "contact",
        "required_copy": ["headline", "description", "button_text"],
    },
    "is_footer": {
        "id": "footer",
        "type": "footer",
        "required_copy": ["tagline", "copyright"],
    },
}


def initial_state(data: LandingPageParams) -> PageState:
    """Graph input for a request: the layout from the enabled switches plus product data."""
    sections = [s for switch, s in SECTIONS.items() if getattr(data, switch)]
    return {  # type: ignore[typeddict-item]
        "product_name": data.product_name,
        # ponytail: the request has no description field; the name is the best we have.
        "product_description": data.product_name,
        "product_image_urls": [str(url) for url in data.images],
        "product_price": data.product_price,
        "currency": data.currency,
        "marketing_angle": data.marketing_angle,
        "fixed_layout_input": {"sections": sections},
        "language": data.language,
    }


@cache
def get_graph():
    """The real graph, built on first request so importing the app needs no API keys."""
    return create_graph(make_llm(), make_search_tool())
