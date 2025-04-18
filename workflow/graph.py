# In workflow/graph.py

import json
import os
from functools import partial
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# Import agent runnables and state definition
from core.state import PageState
from agents.layout_agent import get_layout_agent_runnable
from agents.coder_agent import run_codegen_with_image


# Helper function to run an agent node
def run_agent_node(
    state: PageState, agent_runnable, input_key: str or list, output_key: str
):
    """Runs an agent and updates the state."""
    print(
        f"--- Running Agent: {output_key.split('_')[0].capitalize()} ---"
    )  # Simple logging
    try:
        if isinstance(input_key, list):
            # Handle multiple input keys
            input_data = {key: state[key] for key in input_key}
            # Special handling if keys need specific formatting (like JSON strings)
            if "layout_spec" in input_data:
                input_data["layout_spec_str"] = json.dumps(
                    input_data.pop("layout_spec"), indent=2
                )
            if "preferences" in input_data:
                input_data["preferences_str"] = json.dumps(
                    input_data.pop("preferences"), indent=2
                )

        else:
            input_data = state[input_key]
            # Convert dicts to JSON strings if needed by the prompt template
            if isinstance(input_data, dict):
                input_data = json.dumps(input_data, indent=2)
            # Wrap single string input in expected dict key if necessary (check agent prompts)
            # This depends heavily on how agent prompts are structured. Assuming they expect a dict:
            if input_key == "layout_spec":
                input_data = {
                    "layout_spec_str": input_data
                }  # Use the variable name from the prompt
            elif input_key == "landing_page_code":
                input_data = {
                    "landing_page_code": input_data
                }  # Assuming prompt expects this key
            # Add more specific input structuring as needed based on your prompts

        # Make sure input_data is a dictionary for the runnable
        if not isinstance(input_data, dict):
            # If input_key was a single string, find the expected key name from the agent's prompt vars
            # This part is tricky and might need refinement based on actual prompt input variables
            # For simplicity, let's assume the agent runnables now expect a dict corresponding to state keys
            # Let's revise the agent prompt definitions slightly if needed, or handle it here.
            # Sticking with the current agent structure which expects specific dict keys:
            if (
                output_key == "layout_spec"
            ):  # Layout agent needs description, audience, prefs
                input_data = {
                    "product_description": state["product_description"],
                    "target_audience": state["target_audience"],
                    "preferences_str": json.dumps(
                        state.get("preferences", {}), indent=2
                    ),
                }
            elif (
                output_key == "landing_page_code"
            ):  # Codegen agent needs layout_spec_str
                input_data = {
                    "layout_spec_str": json.dumps(state["layout_spec"], indent=2)
                }
            elif (
                output_key == "evaluation_report"
            ):  # Eval agent needs layout_spec_str and code
                input_data = {
                    "layout_spec_str": json.dumps(state["layout_spec"], indent=2),
                    "landing_page_code": state[
                        "landing_page_code"
                    ],  # Assuming code is stored as string
                }
            elif (
                output_key == "suggestions"
            ):  # Suggestion agent needs desc, audience, layout_spec_str
                input_data = {
                    "product_description": state["product_description"],
                    "target_audience": state["target_audience"],
                    "layout_spec_str": json.dumps(state["layout_spec"], indent=2),
                }

        result = agent_runnable.invoke(input_data)

        # Handle potential code string output for codegen to fit PageState structure
        if output_key == "landing_page_code" and isinstance(result, str):
            state[output_key] = {"html": result}  # Store basic HTML string in dict
        elif output_key == "evaluation_report" and isinstance(result, str):
            state[output_key] = result  # Store eval report string directly
            # If evaluator also outputs improved code, handle that separately
            state["improved_code"] = None  # Placeholder
        else:
            state[output_key] = (
                result  # Assumes dict output for layout_spec, suggestions
            )

        state["error_message"] = None  # Clear error on success
    except Exception as e:
        print(f"Error in agent {output_key}: {e}")
        state["error_message"] = f"Error in {output_key}: {str(e)}"
    return state


def create_graph(llm: ChatOpenAI):
    """Creates and compiles the LangGraph workflow."""

    # Get agent runnables, passing the initialized LLM
    layout_agent = get_layout_agent_runnable(llm)
    codegen_agent = run_codegen_with_image(llm)
    evaluation_agent = None  # Placeholder for evaluation agent, replace with actual runnable
    suggestion_agent = None  # Placeholder for suggestion agent, replace with actual runnable

    # Create graph instance
    graph = StateGraph(PageState)

    # Define nodes using partial to pass the correct runnable to the generic node function
    graph.add_node(
        "layout_researcher",
        partial(
            run_agent_node,
            agent_runnable=layout_agent,
            input_key=["product_description", "target_audience", "preferences"],
            output_key="layout_spec",
        ),
    )
    graph.add_node(
        "code_generator",
        partial(
            run_agent_node,
            agent_runnable=codegen_agent,
            input_key="layout_spec",
            output_key="landing_page_code",
        ),
    )
    graph.add_node(
        "evaluator",
        partial(
            run_agent_node,
            agent_runnable=evaluation_agent,
            input_key=["layout_spec", "landing_page_code"],
            output_key="evaluation_report",
        ),
    )
    graph.add_node(
        "suggester",
        partial(
            run_agent_node,
            agent_runnable=suggestion_agent,
            input_key=["product_description", "target_audience", "layout_spec"],
            output_key="suggestions",
        ),
    )

    # Define edges for the workflow
    graph.set_entry_point("layout_researcher")
    graph.add_edge("layout_researcher", "code_generator")
    graph.add_edge("code_generator", "evaluator")
    graph.add_edge("evaluator", "suggester")  # Connect evaluator to suggester
    graph.add_edge("suggester", END)  # End after suggestions

    # Compile the graph
    compiled_graph = graph.compile()
    return compiled_graph


# Optional: Add a main block to test graph creation itself
if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found.")
    else:
        test_llm = ChatOpenAI(
            model="gpt-3.5-turbo"
        )  # Use a cheaper model for structure test
        try:
            app = create_graph(test_llm)
            print("Graph compiled successfully!")
            # You could potentially invoke it here with dummy data for a basic test
            # print(app.get_graph().print_ascii()) # Print graph structure
        except Exception as e:
            print(f"Error creating graph: {e}")
