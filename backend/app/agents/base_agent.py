"""Base agent class for AI-powered assistants via OpenRouter."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

import structlog
from openai import AsyncOpenAI

from app.config import settings


logger = structlog.get_logger()


def _get_ai_client() -> AsyncOpenAI:
    """Create OpenAI-compatible client for OpenRouter."""
    api_key = settings.OPENROUTER_API_KEY or settings.ANTHROPIC_API_KEY
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is not set")
    return AsyncOpenAI(
        api_key=api_key,
        base_url=settings.OPENROUTER_BASE_URL,
    )


class BaseAgent(ABC):
    """Base class for all AI agents."""

    def __init__(self) -> None:
        self.client = _get_ai_client()
        self.model = settings.AI_MODEL
        self.tools = self._define_tools()
        self.system_prompt = self._get_system_prompt()

    @abstractmethod
    def _define_tools(self) -> list[dict]:
        """Define tools available to this agent."""
        ...

    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        ...

    def _get_system_prompt_for_region(self, region: str = "all") -> str:
        """Get the system prompt, optionally adjusted for region. Override in subclass."""
        return self._get_system_prompt()

    @abstractmethod
    async def _execute_tool(self, name: str, input_data: dict) -> str:
        """Execute a tool call and return the result as string."""
        ...

    def _convert_tools_to_openai(self) -> list[dict]:
        """Convert Anthropic tool format to OpenAI function calling format."""
        openai_tools = []
        for tool in self.tools:
            openai_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get(
                            "input_schema", {"type": "object", "properties": {}}
                        ),
                    },
                }
            )
        return openai_tools

    async def chat(
        self,
        message: str,
        history: list[dict] | None = None,
        context: str = "",
        region: str = "all",
    ) -> AsyncGenerator[dict, None]:
        """Chat with the agent, yielding events.

        Events:
        - {"type": "text", "content": "..."} - text chunk
        - {"type": "searching", "query": "..."} - tool search started
        - {"type": "products", "items": [...]} - product results
        - {"type": "done"} - conversation complete
        """
        system = self._get_system_prompt_for_region(region)
        if context:
            system += f"\n\nКонтекст пользователя:\n{context}"

        messages: list[dict] = [{"role": "system", "content": system}]
        if history:
            for h in history[-10:]:
                if h.get("role") in ("user", "assistant") and h.get("content"):
                    messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": message})

        openai_tools = self._convert_tools_to_openai()

        # Step 1: Call with tools
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                max_tokens=1024,
                messages=messages,
                tools=openai_tools if openai_tools else None,
            )
        except Exception as e:
            logger.error("agent_call_failed", error=str(e))
            yield {"type": "text", "content": "Ошибка AI, попробуй ещё раз"}
            yield {"type": "done"}
            return

        choice = response.choices[0]

        # Check if tool use is needed
        if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
            # Emit any text before tool calls
            if choice.message.content:
                yield {"type": "text", "content": choice.message.content}

            tool_results = []
            for tool_call in choice.message.tool_calls:
                import json

                fn = tool_call.function
                input_data = json.loads(fn.arguments) if fn.arguments else {}

                yield {"type": "searching", "query": input_data.get("query", "")}

                result_text, products = await self._execute_tool_with_products(fn.name, input_data)

                if products:
                    yield {"type": "products", "items": products}

                tool_results.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result_text,
                    }
                )

            # Step 2: Stream final response with tool results
            if tool_results:
                messages.append(choice.message.model_dump())
                messages.extend(tool_results)

                try:
                    stream = await self.client.chat.completions.create(
                        model=self.model,
                        max_tokens=1200,
                        messages=messages,
                        stream=True,
                    )
                    async for chunk in stream:
                        delta = chunk.choices[0].delta if chunk.choices else None
                        if delta and delta.content:
                            yield {"type": "text", "content": delta.content}
                except Exception as e:
                    logger.error("agent_stream_failed", error=str(e))
                    yield {"type": "text", "content": "Ошибка при генерации ответа"}
        elif choice.message.content:
            yield {"type": "text", "content": choice.message.content}

        yield {"type": "done"}

    async def _execute_tool_with_products(
        self, name: str, input_data: dict
    ) -> tuple[str, list[dict]]:
        """Execute tool and return (result_text, products_list)."""
        result = await self._execute_tool(name, input_data)
        return result, []
