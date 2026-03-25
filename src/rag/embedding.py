"""自定义 Embedding 类.

使用 httpx 直接调用 API，避免 OpenAI SDK 版本兼容性问题。
"""


import httpx
from langchain_core.embeddings import Embeddings

from src.config import settings
from src.logging_config import get_logger

logger = get_logger(__name__)


class DirectEmbeddings(Embeddings):
    """直接使用 httpx 调用 embedding API."""

    def __init__(
        self,
        model_name: str,
        api_key: str,
        base_url: str | None = None,
        dimensions: int | None = None,
    ) -> None:
        """初始化 DirectEmbeddings.

        Args:
            model_name: 模型名称
            api_key: API Key
            base_url: API 基础 URL
            dimensions: 嵌入向量维度 (可选)
        """
        self.model_name = model_name
        self.api_key = api_key
        self.dimensions = dimensions
        if base_url is None:
            base_url = settings.rag.embedding_base_url
        self.base_url = base_url.rstrip("/")
        logger.info(f"DirectEmbeddings 初始化，模型: {model_name}")

    def embed_query(self, text: str) -> list[float]:
        """嵌入查询文本.

        Args:
            text: 查询文本

        Returns:
            嵌入向量
        """
        return self.embed_documents([text])[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """嵌入多个文档.

        Args:
            texts: 文档列表

        Returns:
            嵌入向量列表
        """
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        embeddings: list[list[float]] = []

        for text in texts:
            payload = {
                "model": self.model_name,
                "input": text,
            }
            if self.dimensions is not None:
                payload["dimensions"] = self.dimensions

            try:
                response = httpx.post(url, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                data = response.json()

                if data.get("data") and len(data["data"]) > 0:
                    embedding = data["data"][0]["embedding"]
                    embeddings.append(embedding)
                else:
                    logger.warning(f"API 返回格式异常: {data}")
                    embeddings.append([0.0] * 1536)

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP 错误: {e.response.status_code}, {e.response.text}", exc_info=True)
                raise
            except Exception as e:
                logger.error(f"嵌入失败: {e}", exc_info=True)
                raise

        return embeddings
