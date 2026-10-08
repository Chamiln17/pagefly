"""Offline stand-ins for the chat model and web search tool."""

from typing import Any

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult
from langchain_core.tools import tool


class FakeChatModel(GenericFakeChatModel):
    """Replies with scripted messages in order and records every prompt it gets.

    Unlike LangChain's built-in fakes, it accepts `bind_tools`, so tool-calling
    agents run against it. Scripted `AIMessage`s may carry `tool_calls`.
    """

    prompts: list[list[BaseMessage]] = []

    def bind_tools(self, tools: Any, **kwargs: Any) -> "FakeChatModel":  # type: ignore[override]
        return self

    def _generate(
        self, messages: list[BaseMessage], *args: Any, **kwargs: Any
    ) -> ChatResult:
        self.prompts.append(messages)
        return super()._generate(messages, *args, **kwargs)


def fake_llm(*replies: Any) -> FakeChatModel:
    return FakeChatModel(messages=iter(replies), prompts=[])


def make_fake_search(results: str = "Competitors stress battery life."):
    """A search tool returning fixed results, plus the list of queries it receives."""
    queries: list[str] = []

    @tool
    def web_search(query: str) -> str:
        """Search the web."""
        queries.append(query)
        return results

    return web_search, queries
