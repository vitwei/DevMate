"""配置管理模块.

从 config.toml 加载和管理所有配置项.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

import toml


@dataclass
class ModelConfig:
    """LLM 模型配置."""

    ai_base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model_name: str = "gpt-4o"
    embedding_model_name: str = "text-embedding-3-small"


@dataclass
class SearchConfig:
    """搜索服务配置."""

    tavily_api_key: str = ""


@dataclass
class LangSmithConfig:
    """LangSmith 可观测性配置."""

    langchain_tracing_v2: bool = True
    langchain_api_key: str = ""
    langchain_endpoint: str = "https://api.smith.langchain.com"
    langchain_project: str = "DevMate"


@dataclass
class SkillsConfig:
    """Agent Skills 配置."""

    skills_dir: str = ".skills"


@dataclass
class ServerConfig:
    """Web 服务器配置."""

    host: str = "0.0.0.0"
    port: int = 5003
    debug: bool = False


@dataclass
class RAGConfig:
    """RAG 配置."""

    vector_store_path: str = ".knowledge/vector_db"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 30
    kb_dir: str = ".knowledge/docs"
    embedding_base_url: str = ""
    embedding_api_key: str = ""
    score_threshold: float = 0.3


@dataclass
class FileConfig:
    """文件工具配置."""

    work_dir: str = "workspace"


@dataclass
class Config:
    """主配置类."""

    model: ModelConfig = field(default_factory=ModelConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    langsmith: LangSmithConfig = field(default_factory=LangSmithConfig)
    skills: SkillsConfig = field(default_factory=SkillsConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    file: FileConfig = field(default_factory=FileConfig)
    project_root: Path = field(default_factory=Path.cwd)

    @classmethod
    def load(cls, config_path: str | None = None) -> "Config":
        """从 TOML 文件加载配置.

        Args:
            config_path: 配置文件路径，默认为项目根目录的 config.toml

        Returns:
            Config 实例
        """
        if config_path is None:
            config_path = "config.toml"

        config_file = Path(config_path)
        if not config_file.exists():
            config_file = Path.cwd() / config_path

        config_data: dict[str, dict[str, str | bool | int]] = {}
        if config_file.exists():
            with open(config_file, encoding="utf-8") as f:
                config_data = toml.load(f)

        config = cls()

        if "model" in config_data:
            model_data = config_data["model"]
            config.model = ModelConfig(
                ai_base_url=str(model_data.get("ai_base_url", os.getenv("AI_BASE_URL", ModelConfig.ai_base_url))),
                api_key=str(model_data.get("api_key", os.getenv("OPENAI_API_KEY", ""))),
                model_name=str(model_data.get("model_name", os.getenv("MODEL_NAME", ModelConfig.model_name))),
                embedding_model_name=str(
                    model_data.get(
                        "embedding_model_name", os.getenv("EMBEDDING_MODEL_NAME", ModelConfig.embedding_model_name)
                    )
                ),
            )

        if "search" in config_data:
            search_data = config_data["search"]
            config.search = SearchConfig(
                tavily_api_key=str(search_data.get("tavily_api_key", os.getenv("TAVILY_API_KEY", ""))),
            )

        if "langsmith" in config_data:
            langsmith_data = config_data["langsmith"]
            config.langsmith = LangSmithConfig(
                langchain_tracing_v2=bool(langsmith_data.get("langchain_tracing_v2", True)),
                langchain_api_key=str(langsmith_data.get("langchain_api_key", os.getenv("LANGCHAIN_API_KEY", ""))),
                langchain_endpoint=str(
                    langsmith_data.get("langchain_endpoint", os.getenv("LANGCHAIN_ENDPOINT", LangSmithConfig.langchain_endpoint))
                ),
                langchain_project=str(
                    langsmith_data.get("langchain_project", os.getenv("LANGCHAIN_PROJECT", LangSmithConfig.langchain_project))
                ),
            )

        if "skills" in config_data:
            skills_data = config_data["skills"]
            config.skills = SkillsConfig(
                skills_dir=str(skills_data.get("skills_dir", SkillsConfig.skills_dir)),
            )

        if "server" in config_data:
            server_data = config_data["server"]
            config.server = ServerConfig(
                host=str(server_data.get("host", ServerConfig.host)),
                port=int(server_data.get("port", ServerConfig.port)),
                debug=bool(server_data.get("debug", ServerConfig.debug)),
            )

        if "rag" in config_data:
            rag_data = config_data["rag"]
            config.rag = RAGConfig(
                vector_store_path=str(rag_data.get("vector_store_path", RAGConfig.vector_store_path)),
                chunk_size=int(rag_data.get("chunk_size", RAGConfig.chunk_size)),
                chunk_overlap=int(rag_data.get("chunk_overlap", RAGConfig.chunk_overlap)),
                top_k=int(rag_data.get("top_k", RAGConfig.top_k)),
                kb_dir=str(rag_data.get("kb_dir", RAGConfig.kb_dir)),
                embedding_base_url=str(rag_data.get("embedding_base_url")),
                embedding_api_key=str(rag_data.get("embedding_api_key", os.getenv("EMBEDDING_MODEL_KEY", ""))),
            )

        if "file" in config_data:
            file_data = config_data["file"]
            config.file = FileConfig(
                work_dir=str(file_data.get("work_dir", FileConfig.work_dir)),
            )

        config.project_root = config_file.parent if config_file.exists() else Path.cwd()

        return config


settings = Config.load()
