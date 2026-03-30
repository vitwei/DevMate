"""
LocalRAGRetriever：本地知识库检索组件（RAG - Retrieval 阶段）。

模块职责：
- 加载本地已构建的向量数据库（FAISS）
- 基于用户查询执行相似度检索
- 返回带有来源信息的知识片段，支持可追溯性

设计说明：
- 本模块仅负责"召回"，不负责回答生成
- Embedding 模型通过参数注入，避免与 Ingestion 阶段强耦合
- 返回结构中保留 source 与 chunk 索引，便于后续引用与调试
"""

# ===== 标准库 =====
from pathlib import Path

# ===== 第三方库 =====
from langchain_community.vectorstores import FAISS

# ===== 项目模块 =====
from src.config import settings
from src.logging_config import get_logger

# ===== 项目模块 =====
from src.rag.embedding import DirectEmbeddings

logger = get_logger(__name__)


class LocalRAGRetriever:
    """
    本地 RAG 知识库检索器。

    用于在已构建的 FAISS 向量索引中，
    根据用户查询召回最相关的知识片段。
    """

    def __init__(self, model_name: str, api_key: str, base_url: str | None = None):
        """
        初始化检索器并加载向量数据库。

        Args:
            model_name: Embedding 模型名称
            api_key: API Key
            base_url: Embedding API 基础 URL
        """

        vector_db_dir = Path(settings.rag.vector_store_path)

        if base_url is None:
            base_url = settings.rag.embedding_base_url
        self.embeddings = DirectEmbeddings(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
        )

        self.vectorstore = FAISS.load_local(
            vector_db_dir,
            self.embeddings,
            allow_dangerous_deserialization=True,
        )

    def search_knowledge_recall(
        self, query: str, k: int = 30, score_threshold: float = 0.5
    ) -> list[dict]:
        """
        在本地知识库中执行相似度检索。

        Args:
            query: 用户输入的自然语言查询
            k: 返回的相似文本块数量
            score_threshold: 相似度阈值。

        Returns:
            一个包含多个知识片段的列表，每个片段包含：
            - 来源文件
            - chunk 索引
            - 具体内容
        """
        docs = self.vectorstore.similarity_search_with_score(query, k=k)

        results: list[dict] = []
        for idx, (doc, score) in enumerate(docs):
            if score > score_threshold:
                continue

            results.append(
                {
                    "来源": doc.metadata.get("source", "unknown"),
                    "chunk索引": idx,
                    "内容": doc.page_content,
                }
            )

        return results


if __name__ == "__main__":
    """
    本地调试入口：
    用于快速验证知识库检索是否生效。
    """

    embedding_model_name = settings.model.embedding_model_name
    embedding_api_key = settings.rag.embedding_api_key

    if not embedding_api_key:
        raise RuntimeError("未检测到 embedding_api_key，请先配置 config.toml。")

    retriever = LocalRAGRetriever(
        model_name=embedding_model_name,
        api_key=embedding_api_key,
    )

    query = "DevMate 能做什么？"
    recall_results = retriever.search_knowledge_recall(query)

    for item in recall_results:
        logger.info(item)
