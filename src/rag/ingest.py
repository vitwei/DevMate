"""
本模块用于初始化并构建本地知识库向量索引（RAG - Ingestion 阶段）。

模块职责：
- 从指定目录中加载本地文档（Markdown / Text）
- 对文档进行分块（Chunking）
- 使用向量模型生成 Embedding
- 构建并持久化向量数据库（FAISS）

设计说明：
- 当前采用 FAISS 作为本地向量存储，适合单机 / Demo / 面试场景
- 文档切分策略针对 Markdown 标题结构进行了简单优化
- Embedding 模型通过参数注入，便于后续替换

特别说明：
- 构建知识库时，一个MD文件代表一类前端代码生成规范。若想生成多类网站规范，请直接添加MD即可。
"""

# ===== 标准库 =====
from pathlib import Path

# ===== 第三方库 =====
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

# ===== 项目模块 =====
from src.config import settings
from src.logging_config import get_logger

# ===== 项目模块 =====
from src.rag.embedding import DirectEmbeddings

logger = get_logger(__name__)


def ingest_documents(model_name: str, api_key: str, base_url: str | None = None) -> None:
    """
    执行知识库文档的向量化与索引构建。

    该函数会完成以下流程：
    1. 加载本地 Markdown / Text 文档
    2. 按指定规则进行文本切分
    3. 使用 Embedding 模型生成向量
    4. 构建 FAISS 向量索引并保存到本地

    Args:
        model_name: Embedding 模型名称
        api_key: API Key
        base_url: Embedding API 基础 URL
    """

    kb_dir = Path(settings.rag.kb_dir)
    vector_db_dir = Path(settings.rag.vector_store_path)

    all_chunks = []

    if not kb_dir.exists():
        logger.warning(f"知识库目录不存在: {kb_dir}")
        return

    for file_path in kb_dir.glob("*"):
        if file_path.suffix in {".md", ".txt"}:
            loader = TextLoader(str(file_path), encoding="utf-8")
            docs_from_file = loader.load()

            headers_to_split_on = [("###", "Header 3")]
            markdown_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=headers_to_split_on, strip_headers=False
            )

            for doc in docs_from_file:
                original_metadata = doc.metadata

                md_header_splits = markdown_splitter.split_text(doc.page_content)

                for md_split in md_header_splits:
                    md_split.metadata.update(original_metadata)

                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=settings.rag.chunk_size,
                    chunk_overlap=settings.rag.chunk_overlap,
                )
                chunks = text_splitter.split_documents(md_header_splits)

                all_chunks.extend(chunks)

    if not all_chunks:
        logger.warning("未发现可用文档或切分失败。")
        return

    if base_url is None:
        base_url = settings.rag.embedding_base_url

    embeddings = DirectEmbeddings(
        model_name=model_name,
        api_key=api_key,
        base_url=base_url,
    )

    vectorstore = FAISS.from_documents(all_chunks, embeddings)

    vector_db_dir.parent.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(vector_db_dir)

    logger.info(f"成功向量化并索引 {len(all_chunks)} 个文本块。")


if __name__ == "__main__":
    """
    脚本入口：
    用于在本地一次性完成知识库的初始化构建。
    """

    embedding_model_name = settings.model.embedding_model_name
    embedding_api_key = settings.rag.embedding_api_key
    embedding_base_url = settings.rag.embedding_base_url

    if not embedding_api_key:
        raise RuntimeError("未检测到 embedding_api_key，请先配置 config.toml。")

    ingest_documents(
        model_name=embedding_model_name,
        api_key=embedding_api_key,
        base_url=embedding_base_url,
    )
