"""Runs the real agent graph once against real providers. This makes paid API calls.

Usage: uv run python scripts/smoke_run.py [--model MODEL] [--angle TEXT] [--image-url URL] [--out PATH] [--language CODE]
       uv run python scripts/smoke_run.py --repair-demo [--model MODEL]
"""

import argparse
import logging
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.callbacks import BaseCallbackHandler, get_usage_metadata_callback
from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import ChatGeneration, LLMResult
from langchain_core.tools import BaseTool, tool

from agents.repair_agent import get_repair_runnable
from core.llm import make_llm, make_search_tool
from workflow.graph import check_page, create_graph, should_run_marketing_research

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
# Known problems for --repair-demo: no "cta" section and an <img> without alt.
REPAIR_DEMO_HTML = (
    "<!DOCTYPE html><html><body>"
    f"<section id='hero'><h1>Ceramic Coffee Mug</h1><img src='{IMAGE_URL}'></section>"
    "<section id='features'><ul><li>Keeps coffee hot</li></ul></section>"
    "</body></html>"
)


def run_smoke(
    llm: BaseChatModel,
    search_tool: BaseTool,
    *,
    angle: str | None,
    out_path: Path,
    image_url: str = IMAGE_URL,
    language: str = "en",
) -> str:
    """Runs the graph once, writes the HTML to out_path and returns a summary."""
    state = {
        "product_name": PRODUCT_NAME,
        "product_image_urls": [image_url],
        "marketing_angle": angle,
        "fixed_layout_input": LAYOUT,
        "language": language,
    }
    costs = CostCallback()
    with get_usage_metadata_callback() as usage:
        final = create_graph(llm, search_tool).invoke(
            state, config={"callbacks": [costs]}
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(final.get("generated_html") or "", encoding="utf-8")

    problems = final.get("check_problems")
    if problems is None:
        check = "skipped (earlier error)"
    else:
        check = f"failed: {problems}" if problems else "passed"
    return "\n".join(
        [
            f"route: {should_run_marketing_research(final)}",
            f"check: {check}",
            f"repair passes: {final.get('repair_passes') or 0}",
            f"error: {final.get('error_message') or 'none'}",
            f"html: {out_path}",
            *usage_lines(usage.usage_metadata, costs),
        ]
    )


def run_repair_demo(llm: BaseChatModel) -> str:
    """Sends REPAIR_DEMO_HTML and its check problems to the repair agent (one
    model call), checks the result and returns a summary."""
    image_urls = [IMAGE_URL]
    before = check_page(REPAIR_DEMO_HTML, LAYOUT, image_urls)
    costs = CostCallback()
    with get_usage_metadata_callback() as usage:
        repaired = get_repair_runnable(llm).invoke(
            {"html": REPAIR_DEMO_HTML, "problems": before},
            config={"callbacks": [costs]},
        )
    after = check_page(repaired, LAYOUT, image_urls)
    return "\n".join(
        [
            "before:",
            *(f"  {p}" for p in before),
            "after: passed" if not after else "after:",
            *(f"  {p}" for p in after),
            *usage_lines(usage.usage_metadata, costs),
        ]
    )


def usage_lines(usage_metadata: dict, costs: "CostCallback") -> list[str]:
    """Token counts per model and the summed provider-reported cost."""
    tokens = [
        f"  {model}: input {u['input_tokens']}, output {u['output_tokens']}, total {u['total_tokens']}"
        for model, u in usage_metadata.items()
    ]
    return [
        "tokens:" if tokens else "tokens: none reported",
        *tokens,
        "cost: not reported" if not costs.costs else f"cost: {sum(costs.costs):.6f}",
    ]


class CostCallback(BaseCallbackHandler):
    """Collects the provider-reported `usage.cost` of every model call.

    ChatOpenAI keeps the provider's raw `usage` dict in
    `response_metadata["token_usage"]`; `usage_metadata` drops extra fields such as cost.
    """

    def __init__(self) -> None:
        self.costs: list[float] = []

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        for generations in response.generations:
            for gen in generations:
                if isinstance(gen, ChatGeneration):
                    usage = gen.message.response_metadata.get("token_usage") or {}
                    if usage.get("cost") is not None:
                        self.costs.append(usage["cost"])


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
    parser.add_argument("--language", default="en", help="copy language, e.g. ar")
    parser.add_argument(
        "--repair-demo",
        action="store_true",
        help="skip the graph; repair a fixed broken page with one model call",
    )
    args = parser.parse_args()

    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    if args.repair_demo:
        print(run_repair_demo(make_llm(args.model)))
        return
    summary = run_smoke(
        make_llm(args.model),
        no_search if args.angle else make_search_tool(),
        angle=args.angle,
        out_path=args.out,
        image_url=args.image_url,
        language=args.language,
    )
    print(summary)


if __name__ == "__main__":
    main()
