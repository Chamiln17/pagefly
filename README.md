# Astro-Page-Agents   
**1. Functional Overview**  
   
- **Agent 1:** Landing page layout researcher (studies trends, composes layout proposals)  
- **Agent 2:** Generates valid HTML, CSS, JS according to Agent 1's output (AI coder)  
- **Agent 3:** Evaluates and enhances the generated code (quality, improvements, accessibility)  
- **Optional Agent(s):** Suggests sections & togglers, UX improvements  
   
---  
   
**2. Technology Stack**  
   
- **Backend:** Python (with FastAPI or Flask for APIs)  
- **Frontend:** React.js (for user interaction, previewing, and editing)  
- **AI Frameworks:** LangChain, LangGraph, OpenAI/Anthropic APIs  
- **Orchestration:** LangGraph (for agent workflow definition)  
- **Database:** PostgreSQL/MongoDB (for user/session/content persistence)  
- **Storage:** AWS S3 (for assets, images)  
- **Deployment:** Docker, Vercel/Heroku/AWS  
- **Collaboration/Prompt Management:** Weights & Biases, PromptLayer (optional)  
   
---  
   
**3. Detailed Execution Plan**  
   
### a. Design the Agent Workflow Graph  
   
You can visualize your workflow as a directed acyclic graph (DAG):  
   
```  
User Inputs Product Info  
        |  
   [Agent 1: Layout Research]  
        |  
   [Agent 2: Code Generator]  
        |  
   [Agent 3: Code Evaluator/Enhancer]  
        |  
[Optional Agent: Section/UX Suggestions]  
        |  
       Output to User (with editing capabilities)  
```  
   
Implement this workflow in **LangGraph**, which allows you to define nodes (agents) and transitions (data passing and logic).  
   
### b. Agent Design  
   
- **Agent 1 (`layout-research-agent`):**  
    - Input: Product description, target audience, preferences  
    - Output: JSON specification of landing page (sections, order, features)  
    - Implementation: Large Language Model (GPT-4, Claude, etc.) with retrieval-augmented techniques (use tools + embed recent landing page trends/pages)  
   
- **Agent 2 (`code-generation-agent`):**  
    - Input: JSON specification from Agent 1  
    - Output: React component code, or optionally plain HTML/CSS/JS  
    - Implementation: LLM specialized in code generation; provide format examples and enforce output schema  
   
- **Agent 3 (`evaluation-enhancement-agent`):**  
    - Input: Generated code from Agent 2  
    - Output: Improved code (fixes, accessibility, performance, etc.), suggestions if code is weak  
    - Implementation: LLM with code critique capabilities. Optionally, run automated linting/tests.  
   
- **Agent 4 - UX/Sections Suggestor (Optional):**  
    - Input: Current content/code  
    - Output: List of suggestions (add testimonial, hero section, toggler for FAQs, etc.) with rationale and mini-implementations  
    - Implementation: LLM with prompt library of best UX patterns  
   
- **User Feedback/Edits:**  
    - Allow inline edits, which can trigger another pass through code generation/evaluation if desired.  
   
### c. Building the Agents  
   
- Use **LangChain** agents, each with their own prompt templates, tools, retrievers, and chains.  
- Implement the full workflow and data passing in **LangGraph**. Each agent outputs to the next.  
   
### d. Frontend  
   
- User inputs product info, preferences, brand guidelines  
- Displays generated landing page. Inline code and content editor.  
- Suggestions/sections displayed contextually.  
   
### e. Infra & Orchestration  
   
- Run agents as FastAPI services or serverless functions.  
- Use queues/events (Celery, AWS SQS) to manage
## Usage 
1. install uv: https://docs.astral.sh/uv/getting-started/installation/#standalone-installer
2. run
   ```shell
   uv sync --all-extras --dev
   ```

### Lint (check & fix)
1. open a new terminal in the root of this repo and run:

```shell
uv run ruff check --fix
uv run ruff format
uv run mypy .
```

### Run tests 
1. open a new terminal in the root of this repo and run:
```shell
uv run pytest