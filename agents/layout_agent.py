# In agents/layout_agent.py
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from typing import List, Optional

# Define the desired JSON structure for the layout
class Section(BaseModel):
    type: str = Field(description="Type of the section (e.g., 'hero', 'features', 'testimonials', 'cta', 'faq', 'footer')")
    content_ideas: List[str] = Field(description="List of key content elements or ideas for this section")

class LayoutSpec(BaseModel):
    sections: List[Section] = Field(description="Ordered list of sections for the landing page")
    theme_suggestions: Optional[List[str]] = Field(description="Optional suggestions for theme or style based on preferences")

# Initialize the LLM (we'll pass the actual llm object later when creating the graph)
# For now, define the structure assuming an llm variable exists

# Setup the output parser
layout_parser = JsonOutputParser(pydantic_object=LayoutSpec)

# Define the prompt template
layout_prompt_template = """
You are an expert landing page designer. Based on the following product information, design a structured layout plan.
Product Description:
{product_description}
Target Audience:
{target_audience}
User Preferences:
{preferences_str}
Structure the output as a JSON object following the required format. Focus on a logical flow that guides the user towards the call to action.

{format_instructions}
"""

layout_prompt = PromptTemplate(
    template=layout_prompt_template,
    input_variables=["product_description", "target_audience", "preferences_str"],
    partial_variables={"format_instructions": layout_parser.get_format_instructions()}
)

# Define the agent's core runnable chain (Prompt -> LLM -> Parser)
# We will initialize this with the actual LLM later in the workflow graph file
def get_layout_agent_runnable(llm: ChatOpenAI):
    """Creates the runnable chain for the layout agent."""
    return layout_prompt | llm | layout_parser

if __name__ == "__main__":
    import os
    import json
    from dotenv import load_dotenv
    from langchain_openai import ChatOpenAI

    load_dotenv()

    # Ensure API key is available
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables.")
    else:
        try:
            # Initialize LLM
            llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7) # Or your preferred model

            # Get the runnable
            layout_agent = get_layout_agent_runnable(llm)

            # Sample input
            sample_input = {
                "product_description": "A smart water bottle that tracks hydration and glows to remind you to drink.",
                "target_audience": "Busy professionals and health-conscious individuals.",
                "preferences_str": json.dumps({"style": "minimalist", "main_color": "cyan"}) # Pass preferences as JSON string
            }

            print("--- Testing Layout Agent ---")
            print(f"Input:\n{json.dumps(sample_input, indent=2)}")

            # Invoke the agent
            result = layout_agent.invoke(sample_input)

            print("\nOutput (Layout Spec):")
            print(json.dumps(result, indent=2)) # result should already be a dict from JsonOutputParser

        except Exception as e:
            print(f"An error occurred during testing: {e}")