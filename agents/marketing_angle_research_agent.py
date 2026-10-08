# agents/marketing_angle_research_agent.py (Refactored for LangGraph using Tavily)

import os
import json
from dotenv import load_dotenv
from typing import Dict

from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableLambda

# Import Tavily search tool and agent components
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain import hub  # To pull pre-made agent prompts
from langchain.agents import create_openai_functions_agent, AgentExecutor

# --- Agent Setup ---

# Define the desired JSON structure for the output
# (This helps guide the LLM within the agent prompt later)
angle_output_format_with_justification = """
Format your response as a JSON object with the following structure:
{{
    "recommended_angle": {{
        "angle": "Clear description of the marketing angle in one sentence",
        "target_demographic": "Specific demographic that would respond best to this angle",
        "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
        "justification": "Brief explanation of why this angle is recommended, referencing visual insights and/or web research findings."
    }}
}}
Include only this JSON structure in your response - no explanations or additional text outside the JSON object.
"""


def get_marketing_research_runnable(llm: ChatOpenAI):
    """Creates an agent runnable that uses Tavily search for marketing angles."""
    # 1. Initialize Tools
    tavily_tool = TavilySearchResults(max_results=4)  # Increased results slightly
    tools = [tavily_tool]

    # 2. Get the Agent Prompt Template
    prompt = hub.pull("hwchase17/openai-functions-agent")

    # 3. Create the Agent using OpenAI function calling
    agent = create_openai_functions_agent(llm, tools, prompt)

    # 4. Create the Agent Executor
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # 5. Wrap in RunnableLambda
    def _wrapped_invoke(state_dict: Dict) -> Dict:
        product_name = state_dict.get("product_name", "the product")
        # Use the generated descriptions as primary context
        descriptions = state_dict.get("product_image_descriptions", [])
        visual_insights_summary = []
        for desc_dict in descriptions:
            # Adapt this based on the actual keys returned by your improved image analysis agent
            summary = f"- Image ({desc_dict.get('image_url_analyzed', 'N/A')}): "
            summary += f"Summary='{desc_dict.get('visual_summary', 'N/A')}'. "
            summary += f"Features={desc_dict.get('key_features_visible', [])}. "
            summary += f"Style='{desc_dict.get('style_mood_aesthetics', 'N/A')}'. "
            summary += f"Context='{desc_dict.get('implied_context_user', 'N/A')}'."
            visual_insights_summary.append(summary)
        visual_insights_str = "\n".join(visual_insights_summary)

        # Construct the IMPROVED input query for the agent
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
            f"{angle_output_format_with_justification}"  # Reference the string var defined above
        )

        # Invoke the agent executor
        try:
            result = agent_executor.invoke({"input": agent_query})
            agent_output_str = result.get("output", "")

            # Attempt to parse the JSON output from the agent
            try:
                # Sometimes agent output might have extra text, try finding JSON block
                json_start = agent_output_str.find("{")
                json_end = agent_output_str.rfind("}") + 1
                if json_start != -1 and json_end != -1:
                    json_str = agent_output_str[json_start:json_end]
                    parsed_output = json.loads(json_str)
                    # We want the content under the 'recommended_angle' key based on prompt
                    marketing_strategy = parsed_output.get(
                        "recommended_angle",
                        {
                            "error": "Agent output missing 'recommended_angle'",
                            "raw_output": agent_output_str,
                        },
                    )
                else:
                    marketing_strategy = {
                        "error": "Agent output did not contain valid JSON",
                        "raw_output": agent_output_str,
                    }

            except json.JSONDecodeError:
                print(
                    f"Warning: Failed to parse JSON from marketing research response: {agent_output_str}"
                )
                marketing_strategy = {
                    "error": "Failed to parse agent JSON output",
                    "raw_output": agent_output_str,
                }

        except Exception as e:
            print(f"Error during marketing research agent execution: {e}")
            marketing_strategy = {"error": f"Agent execution failed: {e}"}

        # --- Removed file writing side effect ---
        # Return the parsed angle structure (or error)
        return {"marketing_strategy": marketing_strategy}

    return RunnableLambda(_wrapped_invoke)


# --- Testing Block ---
if __name__ == "__main__":
    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY") or not os.environ.get("TAVILY_API_KEY"):
        print("Error: OPENAI_API_KEY and TAVILY_API_KEY must be set.")
    else:
        test_llm = ChatOpenAI(
            model="gpt-4o", temperature=0.5
        )  # Use a good model for agent work
        research_runnable = get_marketing_research_runnable(test_llm)

        # Simulate input state with descriptions from the previous agent
        test_state_input = {
            "product_name": "Smart Coffee Mug",
            "product_image_descriptions": [
                {
                    "image_url": "url1",
                    "product": "Smart Coffee Mug",
                    "description": "A sleek black mug on a coaster, glowing softly.",
                },
                {
                    "image_url": "url2",
                    "product": "Smart Coffee Mug",
                    "description": "Close up of the mug showing an LED temperature display.",
                },
                {
                    "image_url": "url3",
                    "product": "Smart Coffee Mug",
                    "description": "Person holding the mug at an office desk, looking pleased.",
                },
            ],
        }

        print("--- Testing Marketing Research Runnable ---")
        print("Input State:")
        print(json.dumps(test_state_input, indent=2))
        try:
            research_result = research_runnable.invoke(test_state_input)
            print("\nOutput (Marketing Strategy Dictionary):")
            print(json.dumps(research_result, indent=2))
        except Exception as e:
            print(f"An error occurred during test: {e}")
            import traceback

            traceback.print_exc()
