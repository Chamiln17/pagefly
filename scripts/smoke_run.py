"""Runs the real agent graph once against real providers. This makes paid API calls.

Usage: uv run python scripts/smoke_run.py [--model MODEL] [--angle TEXT] [--image-url URL] [--out PATH]
"""

import argparse
import logging
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.callbacks import get_usage_metadata_callback
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool, tool

from core.llm import make_llm, make_search_tool

from workflow.graph import create_graph, should_run_marketing_research

PRODUCT_NAME = "Ceramic Coffee Mug"
IMAGE_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/4/45/A_small_cup_of_coffee.JPG"
)
LAYOUT = {
    "sections": [
        {"id": "hero", "type": "hero", "required_copy": ["headline", "subheadline"]},
        {"id": "features", "type": "features", "required_copy": ["feature_list"]},
        {"id": "cta", "type": "cta", "required_copy": ["button_text"]},
    ]
}
DEFAULT_OUT = Path("out/smoke_page.html")
CHECK_KEY = "check_problems"


def run_smoke(
    llm: BaseChatModel,
    search_tool: BaseTool,
    *,
    angle: str | None,
    out_path: Path,
    image_url: str = IMAGE_URL,
) -> str:
    """Runs the graph once, writes the HTML to out_path and returns a summary."""
    state = {
        "product_name": PRODUCT_NAME,
        "product_image_urls": [image_url],
        "marketing_angle_input": angle,
        "fixed_layout_input": LAYOUT,
        "language": "en",
    }
    with get_usage_metadata_callback() as usage:
        final = create_graph(llm, search_tool).invoke(state)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(final.get("generated_html") or "", encoding="utf-8")

    if CHECK_KEY not in final:
        check = "not run (no check step in graph state)"
    elif final[CHECK_KEY]:
        check = f"failed: {final[CHECK_KEY]}"
    else:
        check = "passed"
    tokens = [
        f"  {model}: input {u['input_tokens']}, output {u['output_tokens']}, total {u['total_tokens']}"
        for model, u in usage.usage_metadata.items()
    ]
    return "\n".join(
        [
            f"route: {should_run_marketing_research(final)}",
            f"check: {check}",
            f"error: {final.get('error_message') or 'none'}",
            f"html: {out_path}",
            "tokens:" if tokens else "tokens: none reported",
            *tokens,
        ]
    )


@tool
def no_search(query: str) -> str:
    """Stand-in so --angle runs need no TAVILY_API_KEY; research is skipped."""
    raise RuntimeError("research is skipped when a Marketing Angle is given")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", help="overrides LLM_MODEL")
    parser.add_argument(
        "--angle", help="Marketing Angle; given, the research step is skipped"
    )
    parser.add_argument("--image-url", default=IMAGE_URL)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    summary = run_smoke(
        make_llm(args.model),
        no_search if args.angle else make_search_tool(),
        angle=args.angle,
        out_path=args.out,
        image_url=args.image_url,
    )
    print(summary)


if __name__ == "__main__":
    main()
