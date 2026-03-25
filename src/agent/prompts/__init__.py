"""Agent 提示词管理模块.

提供从文件加载和管理系统提示词的功能。
"""

from src.agent.prompts.PromptManager import (
    PromptManager,
    get_prompt_manager,
)

__all__ = ["PromptManager", "get_prompt_manager"]
