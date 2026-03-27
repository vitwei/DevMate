"""MCP Server with Streamable HTTP transport.

This server exposes a `search_web` tool that uses Tavily Search API.
"""


import httpx
from mcp.server.fastmcp import FastMCP

from src.config import settings
from src.logging_config import get_logger

logger = get_logger(__name__)

# 创建 MCP server 实例
mcp = FastMCP("search_web", host="0.0.0.0")


@mcp.tool()
async def search_web(query: str, max_results: int = 3) -> str:
    """使用 Tavily Search API 搜索网络。
    Args:
        query: 搜索查询字符串
        max_results: 返回的最大结果数（默认 3）
    Returns:
        搜索结果的格式化字符串
    """
    tavily_api_key = settings.search.tavily_api_key

    if not tavily_api_key:
        return "错误：Tavily API 密钥未配置"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": tavily_api_key,
                    "query": query,
                    "search_depth": "advanced",
                    "max_results": max_results,
                    "include_answer": True,
                },
            )
            response.raise_for_status()
            data = response.json()

            if "results" not in data or not data["results"]:
                return "未找到相关搜索结果"

            # 格式化搜索结果
            result_lines = []
            result_lines.append(f"搜索结果（关键词: {query}）:")
            result_lines.append("=" * 50)

            for i, result in enumerate(data["results"], 1):
                title = result.get("title", "无标题")
                url = result.get("url", "")
                content = result.get("content", "")

                result_lines.append(f"{i}. {title}")
                result_lines.append(f"   URL: {url}")
                result_lines.append(f"   摘要: {content[:200]}..." if len(content) > 200 else f"   摘要: {content}")
                result_lines.append("-" * 30)

            if "answer" in data and data["answer"]:
                result_lines.append("\nAI 总结:")
                result_lines.append("=" * 20)
                result_lines.append(data["answer"])

            return "\n".join(result_lines)

    except httpx.HTTPStatusError as e:
        logger.error(f"Tavily API 请求失败: {e}", exc_info=True)
        return f"搜索失败：HTTP 错误 {e.response.status_code}"
    except Exception as e:
        logger.error(f"搜索过程中发生错误: {e}", exc_info=True)
        return f"搜索失败：{str(e)}"


def main() -> None:
    """启动 MCP Server 并使用 Streamable HTTP 传输."""
    logger.info("启动 MCP Server...")

    # 使用 Streamable HTTP 传输方式启动服务器
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
