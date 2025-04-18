# workflow/graph.py (updated)
import json
import os
from functools import partial
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from core.state import PageState
from agents.layout_agent import get_layout_agent_runnable
from agents.coder_agent import run_codegen_with_image

def run_agent_node(state: PageState, agent_runnable, input_key: str | list, output_key: str):
    """Runs an agent and updates the state."""
    print(f"--- Running Agent: {output_key.split('_')[0].capitalize()} ---")
    try:
        # Handle input data extraction
        if isinstance(input_key, list):
            input_data = {key: state[key] for key in input_key}
        else:
            input_data = state[input_key]

        # Convert dicts to JSON strings if needed
        if isinstance(input_data, dict):
            input_data = json.dumps(input_data, indent=2)

        # Execute the agent runnable
        result = agent_runnable.invoke(input_data)
        
        # Update state with results
        state[output_key] = result
        state["error_message"] = None
    except Exception as e:
        print(f"Error in agent {output_key}: {e}")
        state["error_message"] = f"Error in {output_key}: {str(e)}"
    return state

def create_graph(llm: ChatOpenAI):
    """Creates and compiles the LangGraph workflow."""
    # Initialize agents with the shared LLM
    layout_agent = get_layout_agent_runnable(llm)
    codegen_agent = run_codegen_with_image(llm)  # Use the class-based code generator

    # Create graph instance
    graph = StateGraph(PageState)

    # Add nodes
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

    # Set up workflow edges
    graph.set_entry_point("layout_researcher")
    graph.add_edge("layout_researcher", "code_generator")
    graph.add_edge("code_generator", END)

    return graph.compile()


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
