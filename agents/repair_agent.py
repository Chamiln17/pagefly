# agents/repair_agent.py: fixes a page the check step rejected

import re

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableLambda

repair_system_prompt = """You repair single-file HTML landing pages that failed an automated check.
You receive the page and the list of problems the check found. Fix every problem and change nothing else: keep the copy, structure and styling.
- Every layout section needs one element whose `id` is the section's id.
- Every `<img>` needs a non-empty, descriptive `alt` attribute.
- When a problem lists product image URLs, add an `<img>` with one of those URLs as its `src`.
- The page must be a full HTML document with an `<html>` element.
Output *only* the fixed HTML, starting with `<!DOCTYPE html>` and ending with `</html>`. No markdown fences, no explanations."""

FENCE = re.compile(r"^\s*```[a-zA-Z]*\s*\n(.*?)\n?```\s*$", re.DOTALL)


def strip_fences(text: str) -> str:
    """Returns the body of a markdown code fence, or the text unchanged."""
    match = FENCE.match(text)
    return match.group(1) if match else text


def get_repair_runnable(llm: BaseChatModel):
    """Runnable taking {"html", "problems"} and returning the repaired HTML."""

    def _repair(inputs: dict) -> str:
        problems = "\n".join(f"- {p}" for p in inputs["problems"])
        reply = llm.invoke(
            [
                SystemMessage(content=repair_system_prompt),
                HumanMessage(
                    content=f"**Problems:**\n{problems}\n\n**Page:**\n{inputs['html']}"
                ),
            ]
        )
        return strip_fences(str(reply.content))

    return RunnableLambda(_repair)
