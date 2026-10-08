# agents/marketing_angle_research_agent.py: researches a Marketing Angle with web search

import json
import logging
from typing import Dict

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)

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
    """Creates a tool-calling agent runnable that researches a Marketing Angle."""
    agent = create_agent(llm, [search_tool], system_prompt=research_system_prompt)

    def _wrapped_invoke(state_dict: Dict) -> Dict:
        product_name = state_dict.get("product_name", "the product")
        # Use the generated descriptions as primary context
        descriptions = state_dict.get("product_image_descriptions", [])
        visual_insights_summary = []
        for desc_dict in descriptions:
            summary = f"- Image ({desc_dict.get('image_url_analyzed', 'N/A')}): "
            summary += f"Description='{desc_dict.get('description', 'N/A')}'."
            visual_insights_summary.append(summary)
        visual_insights_str = "\n".join(visual_insights_summary)

        agent_query = (
            f"Task: Determine the single most effective marketing angle for the product '{product_name}'.\n\n"
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

        try:
            result = agent.invoke({"messages": [HumanMessage(content=agent_query)]})
            agent_output_str = result["messages"][-1].text

            # Agent output might have extra text around the JSON block
            json_start = agent_output_str.find("{")
            json_end = agent_output_str.rfind("}") + 1
            if json_start == -1:
                marketing_strategy = {
                    "error": "Agent output did not contain valid JSON",
                    "raw_output": agent_output_str,
                }
            else:
                try:
                    parsed_output = json.loads(agent_output_str[json_start:json_end])
                    marketing_strategy = parsed_output.get(
                        "recommended_angle",
                        {
                            "error": "Agent output missing 'recommended_angle'",
                            "raw_output": agent_output_str,
                        },
                    )
                except json.JSONDecodeError:
                    logger.warning(
                        "Failed to parse JSON from marketing research response: %s",
                        agent_output_str,
                    )
                    marketing_strategy = {
                        "error": "Failed to parse agent JSON output",
                        "raw_output": agent_output_str,
                    }
        except Exception as e:
            logger.exception("Marketing research agent execution failed")
            marketing_strategy = {"error": f"Agent execution failed: {e}"}

        return {"marketing_strategy": marketing_strategy}

    return RunnableLambda(_wrapped_invoke)
