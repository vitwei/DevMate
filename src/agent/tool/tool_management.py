"""工具管理模块.

统一管理所有工具（MCP、RAG、文件工具等），支持异步注入和热更新。
"""

import asyncio

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from src.agent.tool.file_tools import get_file_tools
from src.agent.tool.rag_tools import get_rag_tools
from src.logging_config import get_logger

logger = get_logger(__name__)


class ToolManagement:
    """工具管理器，统一管理所有工具."""

    def __init__(self, mcp_config: dict | None = None):
        """初始化工具管理器.

        Args:
            mcp_config: MCP 服务器配置字典，格式为:
                {
                    "server-name": {
                        "transport": "streamable_http",
                        "url": "http://localhost:8000/mcp",
                    }
                }
        """
        self._tools: list[BaseTool] = []
        self._lock = asyncio.Lock()
        self._reconnect_lock = asyncio.Lock()
        self._mcp_tools: list[BaseTool] = []
        self._rag_tools: list[BaseTool] = []
        self._file_tools: list[BaseTool] = []
        self._mcp_available = False
        self._initialized = False
        self._mcp_client: MultiServerMCPClient | None = None
        self._mcp_config = mcp_config or {
            "local-mcp": {
                "transport": "streamable_http",
                "url": "http://localhost:8000/mcp",
            }
        }
        self._last_reconnect_attempt = 0.0
        self._reconnect_cooldown = 5.0

    async def initialize(self) -> None:
        """初始化工具管理器，加载所有工具（包括尝试连接MCP）."""
        async with self._lock:
            if self._initialized:
                return
            self._load_rag_tools()
            self._load_file_tools()
            self._update_tools_list()
            self._initialized = True
            logger.info("ToolManagement 初始化完成")

        await self._try_connect_mcp()

    async def _try_connect_mcp(self) -> None:
        """尝试连接 MCP 服务器（不抛出异常）."""
        try:
            success = await self.connect_mcp()
            if success:
                logger.info("MCP 连接成功")
            else:
                logger.warning("MCP 连接失败，将使用其他工具")
        except Exception as e:
            logger.error(f"尝试连接 MCP 时出错: {e}", exc_info=True)

    async def _check_and_reconnect_mcp(self) -> None:
        """检查 MCP 连接状态，如果不可用则尝试重连（带冷却时间）."""
        import time
        
        if self._mcp_available:
            return
        
        current_time = time.time()
        if current_time - self._last_reconnect_attempt < self._reconnect_cooldown:
            return
        
        async with self._reconnect_lock:
            if self._mcp_available:
                return
            
            if current_time - self._last_reconnect_attempt < self._reconnect_cooldown:
                return
            
            self._last_reconnect_attempt = time.time()
            logger.info("MCP 当前不可用，尝试重新连接...")
            await self._try_connect_mcp()

    def _load_rag_tools(self) -> None:
        """加载RAG工具."""
        try:
            self._rag_tools = get_rag_tools()
            logger.info(f"成功加载 {len(self._rag_tools)} 个 RAG 工具")
        except Exception as e:
            logger.error(f"加载 RAG 工具失败: {e}", exc_info=True)
            self._rag_tools = []

    def _load_file_tools(self) -> None:
        """加载文件工具."""
        try:
            self._file_tools = get_file_tools()
            logger.info(f"成功加载 {len(self._file_tools)} 个文件工具")
        except Exception as e:
            logger.error(f"加载文件工具失败: {e}", exc_info=True)
            self._file_tools = []

    async def connect_mcp(self) -> bool:
        """连接MCP服务器并加载MCP工具.

        Returns:
            是否成功连接并加载MCP工具
        """
        async with self._lock:
            try:
                self._mcp_client = MultiServerMCPClient(self._mcp_config)
                self._mcp_tools = await self._mcp_client.get_tools()
                self._mcp_available = True
                logger.info(f"✓ MCP: 加载 {len(self._mcp_tools)} tools")
                self._update_tools_list()
                return True
            except Exception as e:
                logger.error(f"MCP Server 连接失败: {e}", exc_info=True)
                self._mcp_tools = []
                self._mcp_available = False
                self._mcp_client = None
                return False

    async def disconnect_mcp(self) -> None:
        """断开MCP连接并移除MCP工具."""
        async with self._lock:
            self._mcp_tools = []
            self._mcp_available = False
            self._mcp_client = None
            self._update_tools_list()
            logger.info("MCP 工具已移除")

    async def refresh_mcp(self) -> bool:
        """刷新MCP工具.

        Returns:
            是否成功刷新
        """
        return await self.connect_mcp()

    async def inject_tools(self, tools: list[BaseTool]) -> None:
        """异步快速注入工具.

        Args:
            tools: 要注入的工具列表
        """
        async with self._lock:
            for tool in tools:
                if tool not in self._tools:
                    self._tools.append(tool)
            logger.info(f"快速注入 {len(tools)} 个工具")

    async def remove_tools(self, tool_names: list[str]) -> None:
        """移除指定名称的工具.

        Args:
            tool_names: 要移除的工具名称列表
        """
        async with self._lock:
            self._tools = [
                tool for tool in self._tools
                if tool.name not in tool_names
            ]
            logger.info(f"移除 {len(tool_names)} 个工具")

    def _update_tools_list(self) -> None:
        """更新工具列表（内部方法，需要在锁保护下调用）."""
        self._tools = []
        if self._mcp_available:
            self._tools.extend(self._mcp_tools)
        self._tools.extend(self._rag_tools)
        self._tools.extend(self._file_tools)

    async def get_tools(self) -> list[BaseTool]:
        """异步获取所有工具，会尝试自动重连 MCP.

        Returns:
            工具列表
        """
        await self._check_and_reconnect_mcp()
        return self._tools.copy()

    @property
    def tools(self) -> list[BaseTool]:
        """获取所有工具（同步版本，不会触发重连）.

        Returns:
            工具列表
        """
        return self._tools.copy()

    @property
    def mcp_available(self) -> bool:
        """MCP是否可用.

        Returns:
            MCP连接状态
        """
        return self._mcp_available

    @property
    def tool_count(self) -> int:
        """获取工具总数.

        Returns:
            工具数量
        """
        return len(self._tools)
