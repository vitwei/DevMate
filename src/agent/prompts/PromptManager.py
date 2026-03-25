"""Agent 提示词管理模块.

提供从文件加载和管理系统提示词的功能。
"""

import time
from pathlib import Path
from typing import Any

from src.agent.prompts.constants import PromptConstants
from src.logging_config import get_logger

logger = get_logger(__name__)


class PromptCacheEntry:
    """提示词缓存条目."""

    def __init__(self, content: str, mtime: float):
        """初始化缓存条目.

        Args:
            content: 提示词内容
            mtime: 文件修改时间戳
        """
        self.content = content
        self.mtime = mtime
        self.last_access = time.time()


class PromptManager:
    """提示词管理器.

    负责从 prompts 目录加载和管理系统提示词文件。
    支持缓存、验证和热重载功能。
    """

    def __init__(self, prompts_dir: Path | None = None):
        """初始化提示词管理器.

        Args:
            prompts_dir: 提示词文件目录
        """
        if prompts_dir is None:
            prompts_dir = PromptConstants.get_default_prompts_path()

        self.prompts_dir = Path(prompts_dir)
        self._cache: dict[str, PromptCacheEntry] = {}
        self._ensure_prompts_dir()
        logger.info(f"提示词管理器初始化，目录: {self.prompts_dir}")

    def _ensure_prompts_dir(self) -> None:
        """确保提示词目录存在."""
        if not self.prompts_dir.exists():
            self.prompts_dir.mkdir(parents=True, exist_ok=True)
            logger.warning(f"提示词目录不存在，已创建: {self.prompts_dir}")

    def _is_cache_valid(self, filename: str, file_path: Path) -> bool:
        """检查缓存是否有效.

        Args:
            filename: 提示词文件名
            file_path: 文件路径

        Returns:
            缓存是否有效
        """
        if filename not in self._cache:
            return False

        cache_entry = self._cache[filename]
        current_mtime = file_path.stat().st_mtime

        return cache_entry.mtime >= current_mtime

    def _validate_prompt_content(self, content: str, filename: str) -> bool:
        """验证提示词内容.

        Args:
            content: 提示词内容
            filename: 文件名（用于日志）

        Returns:
            内容是否有效
        """
        if not content or not content.strip():
            logger.warning(f"提示词文件为空: {filename}")
            return False

        if len(content.encode("utf-8")) > PromptConstants.MAX_PROMPT_SIZE_BYTES:
            logger.warning(
                f"提示词文件过大 ({len(content)} bytes): {filename}"
            )

        return True

    def list_prompt_files(self) -> list[Path]:
        """列出所有可用的提示词文件.

        Returns:
            提示词文件路径列表
        """
        prompt_files = []
        for ext in PromptConstants.SUPPORTED_EXTENSIONS:
            prompt_files.extend(self.prompts_dir.glob(f"*{ext}"))

        logger.info(f"找到 {len(prompt_files)} 个提示词文件")
        return sorted(prompt_files)

    def load_prompt(
        self, filename: str, use_cache: bool = True, force_reload: bool = False
    ) -> str | None:
        """加载指定的提示词文件.

        Args:
            filename: 提示词文件名（如 "test.txt"）
            use_cache: 是否使用缓存
            force_reload: 是否强制重新加载

        Returns:
            提示词内容，如果文件不存在返回 None
        """
        prompt_path = self.prompts_dir / filename

        if not prompt_path.exists():
            logger.warning(f"提示词文件不存在: {prompt_path}")
            return None

        if not prompt_path.is_file():
            logger.warning(f"提示词路径不是文件: {prompt_path}")
            return None

        if use_cache and not force_reload:
            if self._is_cache_valid(filename, prompt_path):
                logger.debug(f"使用缓存的提示词: {filename}")
                cache_entry = self._cache[filename]
                cache_entry.last_access = time.time()
                return cache_entry.content

        try:
            content = prompt_path.read_text(encoding="utf-8")

            if not self._validate_prompt_content(content, filename):
                return None

            mtime = prompt_path.stat().st_mtime
            self._cache[filename] = PromptCacheEntry(content, mtime)
            logger.info(f"成功加载提示词文件: {filename}")
            return content.strip()

        except Exception as e:
            logger.error(f"加载提示词文件失败 {filename}: {e}", exc_info=True)
            return None

    def load_all_prompts(
        self, use_cache: bool = True, force_reload: bool = False
    ) -> dict[str, str]:
        """加载所有提示词文件.

        Args:
            use_cache: 是否使用缓存
            force_reload: 是否强制重新加载

        Returns:
            字典，键为文件名，值为提示词内容
        """
        prompts = {}
        for prompt_file in self.list_prompt_files():
            content = self.load_prompt(
                prompt_file.name,
                use_cache=use_cache,
                force_reload=force_reload,
            )
            if content:
                prompts[prompt_file.name] = content

        logger.info(f"共加载 {len(prompts)} 个提示词")
        return prompts

    def reload_prompt(self, filename: str) -> str | None:
        """重新加载指定的提示词文件.

        Args:
            filename: 提示词文件名

        Returns:
            重新加载的提示词内容
        """
        logger.info(f"重新加载提示词: {filename}")
        return self.load_prompt(filename, use_cache=False, force_reload=True)

    def reload_all_prompts(self) -> dict[str, str]:
        """重新加载所有提示词文件.

        Returns:
            重新加载的提示词字典
        """
        logger.info("重新加载所有提示词")
        return self.load_all_prompts(use_cache=False, force_reload=True)

    def clear_cache(self, filename: str | None = None) -> None:
        """清除缓存.

        Args:
            filename: 指定文件名清除单个缓存，None 清除所有缓存
        """
        if filename:
            if filename in self._cache:
                del self._cache[filename]
                logger.info(f"清除提示词缓存: {filename}")
        else:
            self._cache.clear()
            logger.info("清除所有提示词缓存")

    def get_cache_stats(self) -> dict[str, Any]:
        """获取缓存统计信息.

        Returns:
            缓存统计字典
        """
        return {
            "total_entries": len(self._cache),
            "entries": {
                filename: {
                    "mtime": entry.mtime,
                    "last_access": entry.last_access,
                    "size": len(entry.content),
                }
                for filename, entry in self._cache.items()
            },
        }


_prompt_manager: PromptManager | None = None


def get_prompt_manager() -> PromptManager:
    """获取提示词管理器单例.

    Returns:
        PromptManager 实例
    """
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
