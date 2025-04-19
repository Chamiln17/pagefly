# workflow/graph.py (Final Version with All Agents and Conditional Logic)

import json
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END # Import ConditionalEdge
from IPython.display import Image, display # Keep for graph visualization if desired

# Import the state definition (ensure core/state.py is up-to-date)
from core.state import PageState

# Import the *runnable creation functions* for ALL agents
from agents.image_analysis_agent import get_image_analysis_runnable
from agents.marketing_angle_research_agent import get_marketing_research_runnable
from agents.copywriting_agent import get_copywriting_agent_runnable
from agents.coder_agent import get_codegen_agent_runnable # Use the revised coder

# --- Define Global Variables for Runnables ---
# These will be initialized in create_graph
image_analysis_runnable = None
marketing_research_runnable = None
copywriting_runnable = None
html_coder_runnable = None # Renamed for clarity

# --- Define Node Functions ---

def image_analysis_node(state: PageState):
    """Runs the image analysis agent(s)."""
    print("--- Running: Image Analysis ---")
    try:
        # The runnable expects a dict with 'product_image_urls' and 'product_name'
        # Ensure these keys are in the state when the graph starts
        if not state.get("product_image_urls"):
             print("Warning: No product_image_urls found in state for analysis.")
             state["product_image_descriptions"] = [] # Set empty list
             return state # Continue workflow even without images? Or raise error?

        agent_input = {
            "product_image_urls": state["product_image_urls"],
            "product_name": state.get("product_name", "Unknown Product")
        }
        result_dict = image_analysis_runnable.invoke(agent_input)
        # Update state with the list of description dicts
        state['product_image_descriptions'] = result_dict.get("product_image_descriptions", [])
        state['error_message'] = None # Clear previous errors if successful
        print(f"--- Image Analysis Complete ({len(state['product_image_descriptions'])} images analyzed) ---")
    except Exception as e:
        print(f"Error in image_analysis_node: {e}")
        state['error_message'] = f"Error in Image Analysis Node: {str(e)}"
        state['product_image_descriptions'] = [] # Ensure it's an empty list on error
    return state

def marketing_research_node(state: PageState):
    """Runs the marketing research agent."""
    print("--- Running: Marketing Research ---")
    # This node should only run if no marketing angle was provided
    if state.get("error_message"): # Skip if previous node failed
         print("Skipping marketing research due to previous error.")
         return state
    if not state.get("product_image_descriptions"):
        print("Warning: Skipping marketing research as no image descriptions are available.")
        state["marketing_strategy"] = {"error": "Skipped due to missing image descriptions."}
        return state

    try:
        # The runnable expects state dict containing 'product_name' and 'product_image_descriptions'
        result_dict = marketing_research_runnable.invoke(state)
        # Update state with the marketing strategy dict (or error dict)
        state['marketing_strategy'] = result_dict.get("marketing_strategy", {"error": "No strategy returned from agent"})
        state['error_message'] = None # Clear error
        print("--- Marketing Research Complete ---")
    except Exception as e:
        print(f"Error in marketing_research_node: {e}")
        state['error_message'] = f"Error in Marketing Research Node: {str(e)}"
        state['marketing_strategy'] = {"error": f"Node execution failed: {str(e)}"}
    return state

def copywriting_node(state: PageState):
    """Runs the copywriting agent."""
    print("--- Running: Copywriting ---")
    if state.get("error_message"): # Skip if previous critical node failed
         print("Skipping copywriting due to previous error.")
         return state
    if not state.get("fixed_layout_input"):
        print("Error: Skipping copywriting as fixed_layout_input is missing.")
        state['error_message'] = "Missing fixed_layout_input for copywriting."
        return state

    try:
        # The runnable expects the full state dict and extracts what it needs
        # It needs: language, fixed_layout_input, product_image_descriptions
        # And EITHER marketing_angle_input OR marketing_strategy
        generated_copy_dict = copywriting_runnable.invoke(state)
        state['generated_copy'] = generated_copy_dict # Store the generated copy dict
        state['error_message'] = None # Clear error
        print("--- Copywriting Complete ---")
    except Exception as e:
        print(f"Error in copywriting_node: {e}")
        state['error_message'] = f"Error in Copywriting Node: {str(e)}"
        state['generated_copy'] = {"error": f"Node execution failed: {str(e)}"}
    return state

def html_generation_node(state: PageState):
    """Runs the HTML coder agent."""
    print("--- Running: HTML Generation ---")
    if state.get("error_message"): # Skip if previous critical node failed
         print("Skipping HTML generation due to previous error.")
         return state
    if not state.get("fixed_layout_input") or not state.get("generated_copy"):
        print("Error: Skipping HTML generation - missing fixed layout or generated copy.")
        state['error_message'] = "Missing fixed layout or generated copy for HTML generation."
        state['generated_html'] = "<!-- Generation skipped due to missing inputs -->"
        return state
    # Check if generated_copy itself is an error object
    if isinstance(state.get("generated_copy"), dict) and state["generated_copy"].get("error"):
        print(f"Skipping HTML generation due to error in generated_copy: {state['generated_copy']['error']}")
        state['error_message'] = "Error reported in generated_copy."
        state['generated_html'] = f"<!-- Generation skipped due to copywriting error: {state['generated_copy']['error']} -->"
        return state


    try:
        # The runnable expects the state dict and extracts what it needs
        # Needs: fixed_layout_input, generated_copy
        # Optional: product_image_url (handled internally by the runnable)
        generated_html_str = html_coder_runnable.invoke(state)
        state['generated_html'] = generated_html_str # Store the final HTML string
        state['error_message'] = None # Clear error
        print("--- HTML Generation Complete ---")
    except Exception as e:
        print(f"Error in html_generation_node: {e}")
        state['error_message'] = f"Error in HTML Generation Node: {str(e)}"
        state['generated_html'] = f"<!-- Node execution failed: {str(e)} -->"
    return state

# --- Conditional Logic Function ---

def should_run_marketing_research(state: PageState) -> str:
    """Determines whether to run marketing research or go directly to copywriting."""
    print("--- Checking: Run Marketing Research? ---")
    if state.get("marketing_angle_input"):
        print("Decision: Skip Marketing Research (User provided angle).")
        return "skip_research" # Route directly to copywriter
    else:
        print("Decision: Run Marketing Research (No user angle provided).")
        return "run_research" # Route to the research node

# --- Graph Creation Function ---

def create_graph(llm: ChatOpenAI):
    """Creates and compiles the full LangGraph workflow."""

    # Make runnables accessible to node functions
    global image_analysis_runnable, marketing_research_runnable
    global copywriting_runnable, html_coder_runnable

    # Initialize ALL agent runnables using the passed LLM
    # Use a capable model like gpt-4o for agents involving vision or complex reasoning/tool use
    llm_vision = ChatOpenAI(model="gpt-4o", temperature=0.3, max_tokens=4095,  request_timeout=120) # For image, copy, code
    llm_research = ChatOpenAI(model="gpt-4o", temperature=0.5,  max_tokens=4095,  request_timeout=120) # For agent/tool use

    image_analysis_runnable = get_image_analysis_runnable(llm_vision)
    marketing_research_runnable = get_marketing_research_runnable(llm_research) # Uses agent executor
    copywriting_runnable = get_copywriting_agent_runnable(llm_vision)
    html_coder_runnable = get_codegen_agent_runnable(llm_vision) # Uses the revised coder

    # Create graph instance using the PageState
    graph = StateGraph(PageState)

    # Add ALL nodes to the graph
    graph.add_node("image_analyzer", image_analysis_node)
    graph.add_node("marketing_researcher", marketing_research_node)
    graph.add_node("copywriter", copywriting_node)
    graph.add_node("html_generator", html_generation_node)

    # --- Define Workflow Edges ---
    # 1. Entry Point
    graph.set_entry_point("image_analyzer")

    # 2. Conditional branch after image analysis
    graph.add_conditional_edges(
        "image_analyzer", # Node to branch from
        should_run_marketing_research, # Function to decide the route
        {
            # Mapping: "function_return_value": "destination_node_name"
            "skip_research": "copywriter",
            "run_research": "marketing_researcher"
        }
    )

    # 3. Connect marketing researcher to copywriter
    graph.add_edge("marketing_researcher", "copywriter")

    # 4. Connect copywriter to html generator
    graph.add_edge("copywriter", "html_generator")

    # 5. Connect html generator to the END
    graph.add_edge("html_generator", END)

    # Compile the graph
    print("Compiling the full graph...")
    compiled_graph = graph.compile()
    print("Graph compilation complete.")
    return compiled_graph


# --- Testing Block ---
if __name__ == "__main__":
    load_dotenv()
    # Ensure ALL necessary API keys are set
    required_keys = ["OPENAI_API_KEY", "TAVILY_API_KEY"]
    if not all(os.environ.get(key) for key in required_keys):
        print(f"Error: Missing required API keys in environment variables: {required_keys}")
    else:
        # Use a placeholder LLM for compilation testing if needed,
        # but invocation testing needs the real one passed potentially.
        # Using the real LLM here for simplicity if testing invocation.
        llm_instance = ChatOpenAI(model="gpt-4o", temperature=0.3, timeout=120) # Or specific models as in create_graph

        print("Attempting to create and compile the full graph...")
        try:
            app = create_graph(llm_instance) # Pass the LLM instance
            print("Full graph compiled successfully!")

            # Optional: Visualize the graph
            try:
                print("\nAttempting to draw graph...")
                # Make sure graphviz and pygraphviz/pydot are installed
                # pip install graphviz pygraphviz pydot
                graph_image = app.get_graph().draw_mermaid_png()
                if graph_image:
                     display(Image(graph_image))
                else:
                     print("(Could not generate graph image. Ensure dependencies are installed.)")
            except Exception as draw_err:
                print(f"(Graph drawing failed: {draw_err}. Ensure dependencies are installed.)")
                # This requires some extra dependencies (like graphviz) and is optional

           # --- Test Invocation (Example - Run from main.py for real use) ---
            # ---vvv UNCOMMENTED BLOCK vvv---
            print("\n--- Testing Full Graph Invocation (Example) ---")
            sample_initial_state = PageState(
                product_name="Smart Thermos Flask",
                product_image_urls=[
                    # Replace with REAL URLs for image analysis to work
                    "https://images.pexels.com/photos/376464/pexels-photo-376464.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1", # Example: Pancakes (not a thermos!)
                    "https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1"  # Example: Salad (not a thermos!)
                    ],
                marketing_angle_input=None, # Set to None to test research path, or a string to skip research
                fixed_layout_input={ # Example fixed layout
                    # If inspiration image URL is placeholder, style matching might be basic
                    "inspiration_image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQt0CiX0sVdMAHRACvWpx1EqZNAbqIdvuT5nHsDWnOwjK33PjGdb4nyxGzXYDxzSAjYXjw&usqp=CAU", # Using the previous example image
                    "sections": [
                        {"id": "hero", "type": "hero", "required_copy": ["headline", "subheadline", "cta_button"]},
                        {"id": "benefits", "type": "benefit_list_3_items", "required_copy_per_item": ["title", "description"]},
                        {"id": "how", "type": "text_section", "required_copy": ["headline", "body"]},
                        {"id": "final_cta", "type": "cta_simple", "required_copy": ["headline", "cta_button"]}
                    ]
                },
                language="en",
                # Other fields initialized to None or empty lists/dicts as appropriate
                product_image_descriptions=[], # Start empty
                marketing_strategy=None,
                generated_copy=None,
                generated_html=None,
                error_message=None
            )
            print(f"Initial State: {json.dumps(sample_initial_state, indent=2)}")
            try:
                # This executes the full graph with the sample data
                final_result_state = app.invoke(sample_initial_state)

                print("\n--- Final State ---")
                # Use default=str for safety in case non-serializable items sneak in
                print(json.dumps(final_result_state, indent=2, default=str))

                print("\n--- Final Generated HTML ---")
                final_html = final_result_state.get("generated_html", "HTML not generated or error.")
                print(final_html)

                # Optionally save the test HTML output
                if isinstance(final_html, str) and final_html.strip().lower().startswith("<!doctype html>"):
                     with open("test/test_graph_output.html", "w", encoding="utf-8") as f:
                         f.write(final_html)
                     print("\n--- Saved test output to test_graph_output.html ---")

            except Exception as invoke_err:
                print(f"\nError during graph invocation test: {invoke_err}")
                import traceback
                traceback.print_exc() # See where in the invocation it failed
            print("\n--- End Invocation Test ---")
            # ---^^^ END UNCOMMENTED BLOCK ^^^---

        except Exception as e:
            print(f"\nError creating or testing graph: {e}")
            import traceback
            traceback.print_exc() # Print full traceback for debugging