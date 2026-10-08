# workflow/graph.py: the agent graph

import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.graph import END, StateGraph

from agents.coder_agent import get_codegen_agent_runnable
from agents.copywriting_agent import get_copywriting_agent_runnable
from agents.image_analysis_agent import get_image_analysis_runnable
from agents.marketing_angle_research_agent import get_marketing_research_runnable
from core.state import PageState

logger = logging.getLogger(__name__)


def should_run_marketing_research(state: PageState) -> str:
    """Skip research when the user supplied a Marketing Angle."""
    if state.get("marketing_angle_input"):
        logger.info("Marketing Angle provided: skipping research")
        return "skip_research"
    logger.info("No Marketing Angle provided: running research")
    return "run_research"


def create_graph(llm: BaseChatModel, search_tool: BaseTool):
    """Builds and compiles the agent graph around the given chat model and search tool."""
    image_analysis_runnable = get_image_analysis_runnable(llm)
    marketing_research_runnable = get_marketing_research_runnable(llm, search_tool)
    copywriting_runnable = get_copywriting_agent_runnable(llm)
    html_coder_runnable = get_codegen_agent_runnable(llm)

    def image_analysis_node(state: PageState):
        logger.info("Running image analysis")
        if not state.get("product_image_urls"):
            logger.warning("No product_image_urls in state; skipping image analysis")
            state["product_image_descriptions"] = []
            return state
        try:
            result_dict = image_analysis_runnable.invoke(
                {
                    "product_image_urls": state["product_image_urls"],
                    "product_name": state.get("product_name", "Unknown Product"),
                }
            )
            state["product_image_descriptions"] = result_dict.get(
                "product_image_descriptions", []
            )
            state["error_message"] = None
            logger.info(
                "Image analysis complete (%d images analyzed)",
                len(state["product_image_descriptions"]),
            )
        except Exception as e:
            logger.exception("Image analysis node failed")
            state["error_message"] = f"Error in Image Analysis Node: {e}"
            state["product_image_descriptions"] = []
        return state

    def marketing_research_node(state: PageState):
        logger.info("Running marketing research")
        if state.get("error_message"):
            logger.info("Skipping marketing research due to previous error")
            return state
        if not state.get("product_image_descriptions"):
            logger.warning("Skipping marketing research: no image descriptions")
            state["marketing_strategy"] = {
                "error": "Skipped due to missing image descriptions."
            }
            return state
        try:
            result_dict = marketing_research_runnable.invoke(state)
            state["marketing_strategy"] = result_dict.get(
                "marketing_strategy", {"error": "No strategy returned from agent"}
            )
            state["error_message"] = None
            logger.info("Marketing research complete")
        except Exception as e:
            logger.exception("Marketing research node failed")
            state["error_message"] = f"Error in Marketing Research Node: {e}"
            state["marketing_strategy"] = {"error": f"Node execution failed: {e}"}
        return state

    def copywriting_node(state: PageState):
        logger.info("Running copywriting")
        if state.get("error_message"):
            logger.info("Skipping copywriting due to previous error")
            return state
        if not state.get("fixed_layout_input"):
            logger.error("Skipping copywriting: fixed_layout_input is missing")
            state["error_message"] = "Missing fixed_layout_input for copywriting."
            return state
        try:
            state["generated_copy"] = copywriting_runnable.invoke(state)
            state["error_message"] = None
            logger.info("Copywriting complete")
        except Exception as e:
            logger.exception("Copywriting node failed")
            state["error_message"] = f"Error in Copywriting Node: {e}"
            state["generated_copy"] = {"error": f"Node execution failed: {e}"}
        return state

    def html_generation_node(state: PageState):
        logger.info("Running HTML generation")
        if state.get("error_message"):
            logger.info("Skipping HTML generation due to previous error")
            return state
        generated_copy = state.get("generated_copy")
        if not state.get("fixed_layout_input") or not generated_copy:
            logger.error("Skipping HTML generation: missing layout or generated copy")
            state["error_message"] = (
                "Missing fixed layout or generated copy for HTML generation."
            )
            state["generated_html"] = (
                "<!-- Generation skipped due to missing inputs -->"
            )
            return state
        if isinstance(generated_copy, dict) and generated_copy.get("error"):
            logger.error(
                "Skipping HTML generation due to copywriting error: %s",
                generated_copy["error"],
            )
            state["error_message"] = "Error reported in generated_copy."
            state["generated_html"] = (
                f"<!-- Generation skipped due to copywriting error: {generated_copy['error']} -->"
            )
            return state
        try:
            state["generated_html"] = html_coder_runnable.invoke(state)
            state["error_message"] = None
            logger.info("HTML generation complete")
        except Exception as e:
            logger.exception("HTML generation node failed")
            state["error_message"] = f"Error in HTML Generation Node: {e}"
            state["generated_html"] = f"<!-- Node execution failed: {e} -->"
        return state

    graph = StateGraph(PageState)
    graph.add_node("image_analyzer", image_analysis_node)
    graph.add_node("marketing_researcher", marketing_research_node)
    graph.add_node("copywriter", copywriting_node)
    graph.add_node("html_generator", html_generation_node)

    graph.set_entry_point("image_analyzer")
    graph.add_conditional_edges(
        "image_analyzer",
        should_run_marketing_research,
        {"skip_research": "copywriter", "run_research": "marketing_researcher"},
    )
    graph.add_edge("marketing_researcher", "copywriter")
    graph.add_edge("copywriter", "html_generator")
    graph.add_edge("html_generator", END)

    return graph.compile()
