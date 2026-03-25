"""提示词模块常量配置."""

from pathlib import Path


class PromptConstants:
    """提示词相关常量."""

    DEFAULT_PROMPTS_DIR: str = "template"
    SUPPORTED_EXTENSIONS: list[str] = [".txt", ".md"]
    CACHE_TTL_SECONDS: int = 300
    DEFAULT_PROMPT_NAME: str = "default"
    MAX_PROMPT_SIZE_BYTES: int = 100 * 1024

    @classmethod
    def get_default_prompts_path(cls) -> Path:
        """获取默认提示词目录路径.

        Returns:
            默认提示词目录的 Path 对象
        """
        return Path(__file__).parent / cls.DEFAULT_PROMPTS_DIR
