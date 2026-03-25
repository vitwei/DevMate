"""RAG 检索工具.

提供知识库检索的 LangChain 工具集成。
"""

from typing import Any

from langchain_core.tools import tool

from src.config import settings
from src.logging_config import get_logger
from src.rag.retriever import LocalRAGRetriever

logger = get_logger(__name__)

_retriever_instance: LocalRAGRetriever | None = None


def _get_retriever() -> LocalRAGRetriever:
    """获取或初始化 RAG 检索器实例.

    Returns:
        LocalRAGRetriever 实例
    """
    global _retriever_instance

    if _retriever_instance is None:
        model_name = settings.model.embedding_model_name
        api_key = settings.rag.embedding_api_key
        base_url = settings.rag.embedding_base_url

        if not api_key:
            raise RuntimeError("未配置 embedding_api_key，请先配置 config.toml。")

        _retriever_instance = LocalRAGRetriever(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
        )
        logger.info("RAG 检索器初始化成功")

    return _retriever_instance


@tool
def search_knowledge_base(query: str, top_k: int = 3, score_threshold: float = 0.7) -> str:
    """查询本地知识库获取相关信息.

    当你需要查找项目规范、指南、最佳实践或其他已存储在本地知识库中的信息时，使用此工具。

    Args:
        query: 用户的查询问题或关键词
        top_k: 返回的最相关结果数量，默认为 3
        score_threshold: 相似度阈值（0-1），只有高于此阈值的结果才会返回，默认为 0.7

    Returns:
        格式化的检索结果字符串
    """
    try:
        retriever = _get_retriever()
        results = retriever.search_knowledge_recall(
            query=query,
            k=top_k,
            score_threshold=score_threshold,
        )

        if not results:
            return f"未找到与 '{query}' 相关的知识库内容。"

        output_parts = [f"知识库检索结果 (查询: '{query}'):"]
        output_parts.append("=" * 60)

        for idx, result in enumerate(results, 1):
            output_parts.append(f"\n【结果 {idx}】")
            output_parts.append(f"来源: {result['来源']}")
            output_parts.append(f"内容:\n{result['内容']}")
            output_parts.append("-" * 40)

        final_output = "\n".join(output_parts)
        logger.debug(f"知识库查询 '{query}' 返回 {len(results)} 个结果")
        return final_output

    except Exception as e:
        logger.error(f"知识库查询失败: {e}", exc_info=True)
        return f"知识库查询出错: {str(e)}"


def get_rag_tools() -> list[Any]:
    """获取所有 RAG 相关工具.

    Returns:
        工具列表
    """
    return [search_knowledge_base]
