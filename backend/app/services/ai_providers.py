"""
AI提供商抽象接口和适配器实现
"""
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from app.config import settings
from app.utils.logger import logger


class AIProvider(ABC):
    """AI提供商抽象基类"""

    @abstractmethod
    async def chat(
        self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]] | None = None
    ) -> Dict[str, Any]:
        """
        发送聊天请求

        Args:
            messages: 消息列表
            tools: 工具函数列表（用于Function Calling）

        Returns:
            Dict: AI响应
        """
        pass

    @abstractmethod
    async def stream_chat(
        self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]] | None = None
    ) -> AsyncIterator[str]:
        """
        流式聊天请求

        Args:
            messages: 消息列表
            tools: 工具函数列表

        Yields:
            str: 响应文本块
        """
        pass


class OpenAIProvider(AIProvider):
    """OpenAI AI提供商适配器"""

    def __init__(self, api_key: str | None = None, model: str = "gpt-4"):
        """
        初始化OpenAI提供商

        Args:
            api_key: API密钥
            model: 模型名称
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = model
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def chat(
        self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]] | None = None
    ) -> Dict[str, Any]:
        """发送聊天请求到OpenAI"""
        try:
            params = {
                "model": self.model,
                "messages": messages,
            }

            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"

            response = await self.client.chat.completions.create(**params)

            # 格式化响应
            message = response.choices[0].message
            result = {
                "role": "assistant",
                "content": message.content or "",
            }

            # 处理工具调用
            if hasattr(message, "tool_calls") and message.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message.tool_calls
                ]

            logger.debug(f"OpenAI response: {result}")
            return result

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise Exception(f"OpenAI API error: {str(e)}")

    async def stream_chat(
        self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]] | None = None
    ) -> AsyncIterator[str]:
        """流式聊天"""
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "stream": True,
            }

            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"

            stream = await self.client.chat.completions.create(**params)

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming error: {str(e)}")
            raise Exception(f"OpenAI streaming error: {str(e)}")


class ClaudeProvider(AIProvider):
    """Anthropic Claude AI提供商适配器"""

    def __init__(self, api_key: str | None = None, model: str = "claude-3-5-sonnet-20241022"):
        """
        初始化Claude提供商

        Args:
            api_key: API密钥
            model: 模型名称
        """
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model
        self.client = AsyncAnthropic(api_key=self.api_key)

    def _convert_messages(self, messages: List[Dict[str, Any]]) -> tuple[str, List[Dict]]:
        """
        转换消息格式（Claude需要单独的system消息）

        Args:
            messages: 原始消息列表

        Returns:
            tuple: (system消息, 其他消息列表)
        """
        system_message = ""
        claude_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                claude_messages.append(msg)

        return system_message, claude_messages

    def _convert_tools(self, tools: List[Dict[str, Any]] | None) -> List[Dict] | None:
        """
        转换工具格式为Claude格式

        Args:
            tools: OpenAI格式的工具列表

        Returns:
            List[Dict]: Claude格式的工具列表
        """
        if not tools:
            return None

        claude_tools = []
        for tool in tools:
            if tool["type"] == "function":
                claude_tools.append(
                    {
                        "name": tool["function"]["name"],
                        "description": tool["function"]["description"],
                        "input_schema": tool["function"]["parameters"],
                    }
                )

        return claude_tools

    async def chat(
        self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]] | None = None
    ) -> Dict[str, Any]:
        """发送聊天请求到Claude"""
        try:
            system_message, claude_messages = self._convert_messages(messages)
            claude_tools = self._convert_tools(tools)

            params = {
                "model": self.model,
                "max_tokens": 4096,
                "messages": claude_messages,
            }

            if system_message:
                params["system"] = system_message

            if claude_tools:
                params["tools"] = claude_tools

            response = await self.client.messages.create(**params)

            # 格式化响应
            result = {
                "role": "assistant",
                "content": "",
            }

            # 处理响应内容
            for content_block in response.content:
                if content_block.type == "text":
                    result["content"] += content_block.text
                elif content_block.type == "tool_use":
                    if "tool_calls" not in result:
                        result["tool_calls"] = []
                    result["tool_calls"].append(
                        {
                            "id": content_block.id,
                            "type": "function",
                            "function": {
                                "name": content_block.name,
                                "arguments": str(content_block.input),
                            },
                        }
                    )

            logger.debug(f"Claude response: {result}")
            return result

        except Exception as e:
            logger.error(f"Claude API error: {str(e)}")
            raise Exception(f"Claude API error: {str(e)}")

    async def stream_chat(
        self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]] | None = None
    ) -> AsyncIterator[str]:
        """流式聊天"""
        try:
            system_message, claude_messages = self._convert_messages(messages)
            claude_tools = self._convert_tools(tools)

            params = {
                "model": self.model,
                "max_tokens": 4096,
                "messages": claude_messages,
                "stream": True,
            }

            if system_message:
                params["system"] = system_message

            if claude_tools:
                params["tools"] = claude_tools

            async with self.client.messages.stream(**params) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.error(f"Claude streaming error: {str(e)}")
            raise Exception(f"Claude streaming error: {str(e)}")


class OllamaProvider(AIProvider):
    """Ollama本地AI提供商适配器"""

    def __init__(self, base_url: str | None = None, model: str = "llama2"):
        """
        初始化Ollama提供商

        Args:
            base_url: Ollama服务地址
            model: 模型名称
        """
        self.base_url = base_url or settings.ollama_base_url
        self.model = model

    async def chat(
        self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]] | None = None
    ) -> Dict[str, Any]:
        """发送聊天请求到Ollama"""
        try:
            import httpx

            # Ollama API调用
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                    },
                    timeout=60.0,
                )

                response.raise_for_status()
                data = response.json()

                result = {
                    "role": "assistant",
                    "content": data["message"]["content"],
                }

                logger.debug(f"Ollama response: {result}")
                return result

        except Exception as e:
            logger.error(f"Ollama API error: {str(e)}")
            raise Exception(f"Ollama API error: {str(e)}")

    async def stream_chat(
        self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]] | None = None
    ) -> AsyncIterator[str]:
        """流式聊天"""
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": True,
                    },
                    timeout=60.0,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            import json

                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]

        except Exception as e:
            logger.error(f"Ollama streaming error: {str(e)}")
            raise Exception(f"Ollama streaming error: {str(e)}")


class AIServiceFactory:
    """AI服务工厂类"""

    @staticmethod
    def create(
        provider: str | None = None, model: str | None = None, **kwargs
    ) -> AIProvider:
        """
        创建AI提供商实例

        Args:
            provider: 提供商名称 (openai, claude, ollama)
            model: 模型名称
            **kwargs: 其他参数

        Returns:
            AIProvider: AI提供商实例

        Raises:
            ValueError: 不支持的提供商
        """
        provider = provider or settings.ai_provider
        model = model or settings.ai_model

        if provider == "openai":
            return OpenAIProvider(model=model, **kwargs)
        elif provider == "claude":
            return ClaudeProvider(model=model, **kwargs)
        elif provider == "ollama":
            return OllamaProvider(model=model, **kwargs)
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")
