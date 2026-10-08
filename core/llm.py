"""Factories for the real chat model and web search tool. Agents never build their own."""

import os

from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "deepseek/deepseek-v4.1-flash"


def make_llm(model: str | None = None) -> ChatOpenAI:
    """OpenAI-compatible chat model from LLM_BASE_URL, LLM_API_KEY and LLM_MODEL."""
    return ChatOpenAI(
        base_url=os.environ.get("LLM_BASE_URL", DEFAULT_BASE_URL),
        api_key=os.environ.get("LLM_API_KEY"),
        model=model or os.environ.get("LLM_MODEL", DEFAULT_MODEL),
    )


def make_search_tool() -> TavilySearch:
    """Tavily web search for the research agent. Needs TAVILY_API_KEY."""
    return TavilySearch(max_results=4)
