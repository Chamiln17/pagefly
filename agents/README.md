## 1. Agent Design  
   
**Agents as Nodes**  
Each agent is a node in a computational graph that takes an input, processes it (using an LLM or code), and outputs a result for the next agent.  
   
**Data Passing**  
Define a clear schema (e.g., dict/JSON structure) for data to move through nodes.  
   
### Agent 1: Layout Research Agent  
   
- **Input:**    
  - `product_description: str`  
  - `target_audience: str`  
  - `preferences: dict`  
- **Output:**    
  - `layout_spec: {"sections": [{ "type": "hero", "content": ...}], "features": ...}`  
   
- **Implementation (LangChain):**  
  - Use an LLMChain with a structured prompt and output parser.  
  - Can optionally enhance with tools (web search/retrieval).  
   
**Prompt Example:**  
```text  
Given the following product "{product_description}" for the audience "{target_audience}", propose a landing page layout as a list of sections (with types like hero, features, testimonials, cta, faq) and their suggested content. Output as JSON.  
```  
   
### Agent 2: Code Generation Agent  
   
- **Input:**    
  - `layout_spec` (from Agent 1)  
- **Output:**    
  - `landing_page_code: str` (HTML/CSS/JS or React, as desired)  
   
- **Implementation:**  
  - Another LLMChain with code-focused prompting. Consider using function-calling or guards for output validation.  
   
**Prompt Example:**  
```text  
Given this landing page specification:  
{layout_spec}  
Generate valid HTML/CSS/JS (or a React component) implementing the layout. Output only code.  
```  
   
### Agent 3: Code Evaluator/Enhancer  
   
- **Input:**    
  - `landing_page_code`  
- **Output:**    
  - `improved_code: str`  
  - `evaluation: str` (comments, suggested fixes)  
   
- **Implementation:**  
  - LLMChain for critique/enhancement, optionally auto-linting (call ESLint/Prettier for JS).  
   
**Prompt Example:**  
```text  
Review this landing page code for structure, accessibility, and performance. Suggest and apply improvements if needed. Output improved code, and summarize changes.  
```  
   
### Agent 4: Section/UX Suggestions (Optional)  
   
- **Input:**    
  - `current_layout_spec or landing_page_code`  
- **Output:**    
  - `suggestions: [{section_name: str, rationale: str, mini_code: str}]`  
   
**Prompt Example:**  
```text  
Suggest 1-3 optional sections or togglers to improve this landing page for user engagement, and for each, provide rationale and example code.  
```  
   
---  
   

   
## 2. Step-by-Step: Agent Design & Building with LangGraph  
   
### 1. **Define Each Agent as a LangChain Runnable**  
   
You can use `LLMChain`, `RunnableLambda`, or any Callable as your node.  
   
```python  
from langchain.prompts import PromptTemplate  
from langchain.chains import LLMChain  
from langchain.llms import OpenAI  
   
# Example: Agent 1 - Layout Research  
layout_prompt = PromptTemplate.from_template(  
    "Given the following product \"{product_description}\" for the audience \"{target_audience}\", "  
    "propose a landing page layout as a JSON list of sections with types and suggested content."  
)  
layout_chain = LLMChain(llm=OpenAI(), prompt=layout_prompt)  
   
# Example: Agent 2 - Code Generator  
codegen_prompt = PromptTemplate.from_template(  
    "Here is a landing page layout spec: {layout_spec}\nGenerate the matching HTML/CSS/JS. Output code only."  
)  
codegen_chain = LLMChain(llm=OpenAI(), prompt=codegen_prompt)  
```  
   
Create similar chains for each agent.  
   
---  
   
### 2. **Define State and Data Passing**  
   
Let’s define a simple layout for shared state (you could use a dataclass):  
   
```python  
class PageState(dict):  
    pass  
```  
   
Each node receives and returns a `PageState` (dict-like object).  
   
---  
   
### 3. **Build the LangGraph**  
   
```python  
from langgraph.graph import StateGraph, END  
   
graph = StateGraph(PageState)  
   
# Define agent node functions  
def layout_node(state: PageState):  
    layout = layout_chain({  
        'product_description': state['product_description'],  
        'target_audience': state['target_audience'],  
        # Add other fields if needed  
    })['text']  
    state['layout_spec'] = layout  
    return state  
   
def codegen_node(state: PageState):  
    code = codegen_chain({  
        'layout_spec': state['layout_spec']  
    })['text']  
    state['landing_page_code'] = code  
    return state  
   
def evaluate_node(state: PageState):  
    # Similar pattern; critique and improve code  
    return state  
   
# Add nodes to the graph  
graph.add_node("layout_agent", layout_node)  
graph.add_node("codegen_agent", codegen_node)  
graph.add_node("evaluator_agent", evaluate_node)  
# Add more as needed  
   
# Specify edges (flow)  
graph.add_edge("layout_agent", "codegen_agent")  
graph.add_edge("codegen_agent", "evaluator_agent")  
graph.add_edge("evaluator_agent", END)  
```  
   
---  
   
### 4. **Run the Graph**  
   
```python  
compiled_graph = graph.compile()  
   
# Initial user input  
initial_state = PageState(  
    product_description="Smart Dog Collar with GPS tracking",  
    target_audience="Dog owners who want security for their pets",  
    preferences={'style': 'modern', 'main_color': 'blue'}  
)  
   
result = compiled_graph.invoke(initial_state)  
print(result['landing_page_code'])  
```  
   
---  
   
### 5. **Tips & Tricks**  
   
- **Input/Output Specification:**   
  - Carefully validate and clean output between agents (especially JSON→code).  
- **Prompt Engineering:**   
  - Use clear, example-driven prompts for best LLM results.  
- **Evaluation Agent:**   
  - Can integrate LLM critique AND programmatic checks (e.g., HTML validators, linters).  
- **Interactivity:**  
  - Allow users to submit edits, then trigger only the relevant graph nodes again.  
- **Extensibility:**   
  - Add more agents (e.g., image generator)