# workflow/graph.py: the agent graph

import logging
from typing import Callable

from bs4 import BeautifulSoup
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.graph import END, StateGraph

from agents.coder_agent import get_codegen_agent_runnable
from agents.copywriting_agent import get_copywriting_agent_runnable
from agents.image_analysis_agent import get_image_analysis_runnable
from agents.marketing_angle_research_agent import get_marketing_research_runnable
from agents.repair_agent import get_repair_runnable
from core.state import PageState

logger = logging.getLogger(__name__)


def should_run_marketing_research(state: PageState) -> str:
    """Skip research when the user supplied a Marketing Angle."""
    if state.get("marketing_angle"):
        logger.info("Marketing Angle provided: skipping research")
        return "skip_research"
    logger.info("No Marketing Angle provided: running research")
    return "run_research"


MAX_REPAIR_PASSES = 1


def should_repair(state: PageState) -> str:
    """Repair only a page with check problems, at most MAX_REPAIR_PASSES times."""
    if (
        state.get("check_problems")
        and not state.get("error_message")
        and (state.get("repair_passes") or 0) < MAX_REPAIR_PASSES
    ):
        return "repair"
    return "finish"


def check_page(
    html: str, layout: dict, image_urls: list[str] | None = None
) -> list[str]:
    """Deterministic page check: the HTML parses and ends with `</html>`
    (nothing trails the document), every layout section has an
    element whose `id` is the section's layout id, every `<img>` has alt text,
    and, when the run has product images, one of them is an `<img src>`."""
    # ponytail: html.parser recovers from almost anything, so "does not parse"
    # means no <html> element came out; a strict parser is the upgrade if needed.
    soup = BeautifulSoup(html, "html.parser")
    if soup.find("html") is None:
        return ["HTML does not parse: no <html> element."]
    problems = []
    if not html.rstrip().lower().endswith("</html>"):
        problems.append(
            "Text outside the HTML document: the page must end with </html>."
        )
    problems += [
        f"Layout section '{s['id']}' has no element with id=\"{s['id']}\"."
        for s in layout.get("sections", [])
        if soup.find(id=s["id"]) is None
    ]
    problems += [
        f'<img src="{img.get("src", "")}"> has no alt text.'
        for img in soup.find_all("img")
        if not str(img.get("alt") or "").strip()
    ]
    srcs = {img.get("src") for img in soup.find_all("img")}
    if image_urls and srcs.isdisjoint(image_urls):
        problems.append(
            "No product image shown: add an <img> whose src is one of: "
            + ", ".join(image_urls)
        )
    return problems


def guarded(name: str, step: Callable[[PageState], None]):
    """Node running `step` on the state: skipped after an earlier error, and a
    failure becomes `error_message`. `step` writes its results into the state."""

    def node(state: PageState):
        if state.get("error_message"):
            logger.info("Skipping %s after an earlier error", name)
            return state
        logger.info("Running %s", name)
        try:
            step(state)
        except Exception as e:
            logger.exception("%s failed", name)
            state["error_message"] = f"Error in {name}: {e}"
        return state

    return node


def create_graph(llm: BaseChatModel, search_tool: BaseTool):
    """Builds and compiles the agent graph around the given chat model and search tool."""
    image_analysis_runnable = get_image_analysis_runnable(llm)
    marketing_research_runnable = get_marketing_research_runnable(llm, search_tool)
    copywriting_runnable = get_copywriting_agent_runnable(llm)
    html_coder_runnable = get_codegen_agent_runnable(llm)
    repair_runnable = get_repair_runnable(llm)

    def analyze_images(state: PageState):
        if not state.get("product_image_urls"):
            logger.warning("No product_image_urls in state; skipping image analysis")
            state["product_image_descriptions"] = []
            return
        state["product_image_descriptions"] = image_analysis_runnable.invoke(state)[
            "product_image_descriptions"
        ]

    def research(state: PageState):
        state["marketing_research"] = marketing_research_runnable.invoke(state)

    def write_copy(state: PageState):
        state["generated_copy"] = copywriting_runnable.invoke(state)

    def generate_html(state: PageState):
        state["generated_html"] = html_coder_runnable.invoke(state)

    def check(state: PageState):
        problems = check_page(
            state.get("generated_html") or "",
            state["fixed_layout_input"],
            state.get("product_image_urls"),
        )
        state["check_problems"] = problems
        logger.info("Page check found %d problems", len(problems))

    def repair(state: PageState):
        state["repair_passes"] = (state.get("repair_passes") or 0) + 1
        state["generated_html"] = repair_runnable.invoke(
            {
                "html": state.get("generated_html") or "",
                "problems": state.get("check_problems") or [],
            }
        )

    def finish_node(state: PageState):
        """Problems still left after the last check fail the run."""
        problems = state.get("check_problems")
        if problems and not state.get("error_message"):
            state["error_message"] = "Page check failed: " + " ".join(problems)
        return state

    graph = StateGraph(PageState)
    graph.add_node("image_analyzer", guarded("Image Analysis Node", analyze_images))
    graph.add_node("marketing_researcher", guarded("Marketing Research Node", research))
    graph.add_node("copywriter", guarded("Copywriting Node", write_copy))
    graph.add_node("html_generator", guarded("HTML Generation Node", generate_html))
    graph.add_node("checker", guarded("Check Node", check))
    graph.add_node("repairer", guarded("Repair Node", repair))
    graph.add_node("finish", finish_node)

    graph.set_entry_point("image_analyzer")
    graph.add_conditional_edges(
        "image_analyzer",
        should_run_marketing_research,
        {"skip_research": "copywriter", "run_research": "marketing_researcher"},
    )
    graph.add_edge("marketing_researcher", "copywriter")
    graph.add_edge("copywriter", "html_generator")
    graph.add_edge("html_generator", "checker")
    graph.add_conditional_edges(
        "checker", should_repair, {"repair": "repairer", "finish": "finish"}
    )
    graph.add_edge("repairer", "checker")
    graph.add_edge("finish", END)

    return graph.compile()
