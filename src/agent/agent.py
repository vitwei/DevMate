"""DevMate 核心 Agent 模块."""

import asyncio
import os
from collections.abc import AsyncGenerator
from typing import Optional

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from src.agent.prompts import get_prompt_manager
from src.agent.tool.tool_management import ToolManagement
from src.config import settings
from src.logging_config import get_logger

logger = get_logger(__name__)


class DevMateAgent:
    """DevMate 智能编程助手 Agent.

    单例模式，确保只有一个 Agent 实例。
    """

    _instance: Optional["DevMateAgent"] = None
    _lock = asyncio.Lock()

    def __new__(cls) -> "DevMateAgent":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """初始化 Agent 基础组件."""
        if hasattr(self, "_initialized_base"):
            return

        self._setup_langsmith()
        self.llm = self._init_llm()
        self.tool_manager = ToolManagement()
        self.agent = None
        self._initialized = False
        self._initialized_base = True

    def _init_llm(self) -> ChatOpenAI:
        """初始化 LLM 模型.

        Returns:
            ChatOpenAI 实例
        """
        llm = ChatOpenAI(
            base_url=settings.model.ai_base_url,
            api_key=settings.model.api_key,
            model=settings.model.model_name,
            temperature=0.7,
        )

        logger.info(f"LLM 已初始化: {settings.model.model_name}")
        return llm

    def _setup_langsmith(self) -> None:
        """配置 LangSmith 可观测性和 OpenAI 环境变量."""
        if settings.langsmith.langchain_tracing_v2:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = settings.langsmith.langchain_api_key
            os.environ["LANGCHAIN_ENDPOINT"] = settings.langsmith.langchain_endpoint
            os.environ["LANGCHAIN_PROJECT"] = settings.langsmith.langchain_project
            logger.info("LangSmith tracing 已启用")

        os.environ["OPENAI_API_KEY"] = settings.model.api_key
        os.environ["OPENAI_BASE_URL"] = settings.model.ai_base_url
        logger.info(f"OpenAI 环境变量已配置: {settings.model.ai_base_url}")

    async def initialize(self) -> None:
        """异步初始化 Agent，连接 MCP 并创建 agent 实例."""
        async with self._lock:
            if self._initialized:
                return

            await self.tool_manager.initialize()
            await self._init_agent()
            self._initialized = True
            logger.info("DevMateAgent 初始化完成")


    async def _init_agent(self) -> None:
        """初始化 Agent 实例."""
        try:
            tools = self.tool_manager.tools
            if tools:
                self.agent = create_agent(
                    model=self.llm,
                    tools=tools,
                    system_prompt=self._build_system_prompt(),
                )
                logger.info(f"Agent 创建成功，共加载 {len(tools)} 个工具")
            else:
                logger.warning("没有可用的工具")
        except Exception as e:
            logger.error(f"Agent 初始化失败: {e}", exc_info=True)
            raise

    def _build_system_prompt(self) -> str:
        """构建系统提示词.

        优先从 prompts/test       """
        prompt_manager = get_prompt_manager()
        test_prompt = prompt_manager.load_prompt("test.txt")

        if test_prompt:
            base_prompt = test_prompt
            logger.info("使用 prompt_manager 中的系统提示词")
        else:
            base_prompt = "你是一个智能编程助手，帮助用户生成和修改代码。"
            logger.info("使用默认系统提示词")

        return base_prompt

    async def astream(
        self, input_text: str, chat_history: list | None = None
    ) -> AsyncGenerator[str]:
        """异步流式调用 Agent.

        Args:
            input_text: 用户输入文本
            chat_history: 对话历史记录

        Yields:
            Agent 响应片段
        """
        if chat_history is None:
            chat_history = []

        try:
            enhanced_input = input_text
            messages = []

            for role, content in chat_history:
                if role == "human":
                    messages.append({"role": "user", "content": content})
                elif role == "ai":
                    messages.append({"role": "assistant", "content": content})

            messages.append({"role": "user", "content": enhanced_input})

            async for chunk in self.agent.astream({"messages": messages}):
                if isinstance(chunk, dict):
                    if "output" in chunk:
                        yield chunk["output"]
                    elif "messages" in chunk and chunk["messages"]:
                        last_msg = chunk["messages"][-1]
                        if hasattr(last_msg, "content"):
                            yield last_msg.content
                    elif "model" in chunk:
                        model_data = chunk["model"]
                        if isinstance(model_data, dict) and "messages" in model_data and model_data["messages"]:
                            last_msg = model_data["messages"][-1]
                            if hasattr(last_msg, "content"):
                                yield last_msg.content
                elif hasattr(chunk, "content"):
                    yield chunk.content

            logger.info("Agent 流式调用成功")
        except Exception as e:
            logger.error(f"Agent 流式调用失败: {e}", exc_info=True)
            yield f"抱歉，遇到了错误：{str(e)}"

    async def close(self) -> None:
        """关闭 Agent，清理资源."""
        logger.info("正在关闭 DevMateAgent...")
        try:
            await self.tool_manager.disconnect_mcp()
        except Exception as e:
            logger.error(f"关闭 MCP 连接时出错: {e}", exc_info=True)
        logger.info("DevMateAgent 已关闭")




_agent_instance: DevMateAgent | None = None


async def get_agent() -> DevMateAgent:
    """获取 DevMateAgent 单例实例，自动初始化.

    Returns:
        DevMateAgent 实例
    """
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = DevMateAgent()
        await _agent_instance.initialize()
    return _agent_instance
