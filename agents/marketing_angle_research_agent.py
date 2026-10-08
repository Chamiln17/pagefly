# agents/marketing_angle_research_agent.py: researches a Marketing Angle with web search

import json
from typing import Dict

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import BaseTool

research_system_prompt = """You are a marketing research assistant for e-commerce products.
Use the web search tool to look up market trends, competitors and customer keywords before answering.
When you have enough information, reply with the requested JSON object only."""

# Define the desired JSON structure for the output
angle_output_format_with_justification = """
Format your response as a JSON object with the following structure:
{
    "recommended_angle": {
        "angle": "Clear description of the marketing angle in one sentence",
        "target_demographic": "Specific demographic that would respond best to this angle",
        "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
        "justification": "Brief explanation of why this angle is recommended, referencing visual insights and/or web research findings."
    }
}
Include only this JSON structure in your response - no explanations or additional text outside the JSON object.
"""


def get_marketing_research_runnable(llm: BaseChatModel, search_tool: BaseTool):
    """Tool-calling agent runnable returning the research that yields the
    Marketing Angle; raises when the agent's reply has no usable JSON."""
    agent = create_agent(llm, [search_tool], system_prompt=research_system_prompt)

    def research_marketing_angle(state: Dict) -> Dict:
        product_name = state.get("product_name") or "the product"
        visual_insights_str = "\n".join(
            f"- Image ({d.get('image_url_analyzed', 'N/A')}): "
            f"Description='{d.get('description', 'N/A')}'."
            for d in state.get("product_image_descriptions") or []
        )
        description = state.get("product_description")
        description_line = (
            f"Product description: {description}\n\n" if description else ""
        )

        agent_query = (
            f"Task: Determine the single most effective marketing angle for the product '{product_name}'.\n\n"
            f"{description_line}"
            f"Context based on product image analysis:\n{visual_insights_str}\n\n"
            f"Instructions:\n"
            f"1. Analyze the provided visual context insights.\n"
            f"2. Use web search tools to research:\n"
            f"   - Current marketing trends for similar products (e.g., '{product_name}', related categories).\n"
            f"   - Key competitors and their apparent marketing angles.\n"
            f"   - Relevant high-intent keywords potential customers might use.\n"
            f"3. Synthesize the visual insights with the web research findings.\n"
            f"4. Recommend the best marketing angle, target demographic, keywords, and provide a justification.\n\n"
            f"Output Requirements:\n"
            f"{angle_output_format_with_justification}"
        )

        result = agent.invoke({"messages": [HumanMessage(content=agent_query)]})
        reply = result["messages"][-1].text
        # The reply may have extra text around the JSON object.
        json_start = reply.find("{")
        if json_start == -1:
            raise ValueError(f"Research reply has no JSON: {reply[:200]}")
        parsed = json.loads(reply[json_start : reply.rfind("}") + 1])
        if "recommended_angle" not in parsed:
            raise ValueError(
                f"Research reply has no 'recommended_angle': {reply[:200]}"
            )
        return parsed["recommended_angle"]

    return RunnableLambda(research_marketing_angle)
