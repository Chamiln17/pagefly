# workflow/graph.py (Refactored Version)
import json
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from IPython.display import Image, display

# Import the state definition
from core.state import PageState
# Import the *runnable creation functions* from agent modules
from agents.layout_agent import get_layout_agent_runnable
from agents.coder_agent import get_codegen_agent_runnable # Changed import

# --- Define Node Functions ---

# Initialize runnables outside node functions but within graph creation scope
# This way, they capture the LLM instance passed to create_graph
layout_agent_runnable = None
codegen_agent_runnable = None

def layout_node(state: PageState):
    """
    Node to run the layout research agent.
    Reads required info from state, invokes the agent, and updates the state.
    """
    print("--- Running: Layout Researcher ---")
    try:
        # Prepare input for the layout agent runnable
        agent_input = {
            "product_description": state["product_description"],
            "target_audience": state["target_audience"],
            # Convert preferences dict to JSON string for the prompt template
            "preferences_str": json.dumps(state.get("preferences", {}))
        }
        # Invoke the layout agent runnable
        result = layout_agent_runnable.invoke(agent_input)
        # Update state
        state['layout_spec'] = result # result should be a dictionary from JsonOutputParser
        state['error_message'] = None
        print("--- Layout Spec Generated ---")
    except Exception as e:
        print(f"Error in layout_node: {e}")
        state['error_message'] = f"Error in Layout Node: {str(e)}"
        # Decide if you want to stop the graph here or continue
    return state # Always return the state

def codegen_node(state: PageState):
    """
    Node to run the code generation agent.
    Reads layout_spec from state, invokes the agent, and updates the state.
    """
    print("--- Running: Code Generator ---")
    # Check if layout generation failed in the previous step
    if state.get('error_message') or not state.get('layout_spec'):
        print("Skipping code generation due to previous error or missing layout spec.")
        # Ensure landing_page_code is None or indicates failure
        state['landing_page_code'] = {"html": "<!-- Code generation skipped -->"}
        return state

    try:
        # Prepare input for the codegen agent runnable
        # It expects a dictionary with the key "layout_spec" containing the layout dictionary
        agent_input = {"layout_spec": state['layout_spec']}

        # Invoke the codegen agent runnable
        generated_html = codegen_agent_runnable.invoke(agent_input)

        # Update state - store code, maybe in a structured way
        state['landing_page_code'] = {"html": generated_html} # Store raw HTML string
        state['error_message'] = None # Clear error on success
        print("--- Landing Page Code Generated ---")
    except Exception as e:
        print(f"Error in codegen_node: {e}")
        state['error_message'] = f"Error in Code Generation Node: {str(e)}"
        state['landing_page_code'] = {"html": f"<!-- Error during code generation: {e} -->"}
    return state # Always return the state


# --- Graph Creation Function ---

def create_graph(llm: ChatOpenAI):
    """Creates and compiles the LangGraph workflow."""

    global layout_agent_runnable, codegen_agent_runnable
    # Initialize agent runnables using the passed LLM
    # These are now accessible by the node functions defined above
    layout_agent_runnable = get_layout_agent_runnable(llm)
    codegen_agent_runnable = get_codegen_agent_runnable(llm) # Use the new function

    # Create graph instance using the PageState
    graph = StateGraph(PageState)

    # Add the nodes to the graph
    # The node name is a string, the node function is the callable
    graph.add_node("layout_researcher", layout_node)
    graph.add_node("code_generator", codegen_node)
    # Add evaluation/suggestion nodes here later if needed
    # graph.add_node("evaluator", evaluation_node)
    # graph.add_node("suggester", suggestion_node)

    # Define the workflow edges
    graph.set_entry_point("layout_researcher")
    graph.add_edge("layout_researcher", "code_generator")
    # If adding more nodes:
    # graph.add_edge("code_generator", "evaluator")
    # graph.add_edge("evaluator", "suggester")
    # graph.add_edge("suggester", END)
    # For now, end after code generation
    graph.add_edge("code_generator", END)

    # Compile the graph into a runnable application
    compiled_graph = graph.compile()
    return compiled_graph


# --- Testing Block ---
if __name__ == "__main__":
    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found.")
    else:
        # Use a capable model, especially for the coder agent
        # You might use different LLMs for different agents later
        test_llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        print("Attempting to create and compile graph...")
        try:
            app = create_graph(test_llm)
            print("Graph compiled successfully!")

            # --- Optional: Test Invocation (Example) ---
            print("\n--- Testing Graph Invocation ---")
            initial_state_test = PageState(
                product_description="A smart coffee mug that keeps drinks at the perfect temperature.",
                target_audience="Coffee lovers and tech enthusiasts.",
                preferences={"style": "sleek", "main_color": "black"},
                layout_spec=None,
                landing_page_code=None,
                evaluation_report=None,
                improved_code=None,
                suggestions=None,
                error_message=None
            )
            print(f"Initial State: {initial_state_test}")
            result_state = app.invoke(initial_state_test)
            print("\n--- Final State ---")
            print(result_state)
            print("\n--- Generated HTML (from final state) ---")
            print(result_state.get('landing_page_code', {}).get('html', 'HTML not generated or error occurred.'))
            print("\n--- End Invocation Test ---")
            # Comment out invoke test if you only want to test compilation

            # Print graph structure using built-in method if desired
            print("\n--- Graph Structure ---")

            try:
                display(Image(app.get_graph().draw_mermaid_png()))
            except Exception:
                # This requires some extra dependencies and is optional
                pass

        except Exception as e:
            print(f"Error creating or testing graph: {e}")
            import traceback
            traceback.print_exc() # Print full traceback for debugging```