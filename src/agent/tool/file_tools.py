"""文件管理工具.

提供文件系统操作的 LangChain 工具集成，支持读取、写入、列出目录等功能。
"""

import os
from pathlib import Path

from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_core.tools import BaseTool, tool

from src.config import settings
from src.logging_config import get_logger

logger = get_logger(__name__)

_tools_instance: list[BaseTool] | None = None


@tool
def mkdir_tool(path: str) -> str:
    """Creates a directory at the given path (limited to work directory)."""
    try:
        os.makedirs(_get_work_dir() / path, exist_ok=True)
        return f"Directory '{path}' created successfully."
    except Exception as e:
        return f"Error creating directory '{path}': {e}"







def _get_work_dir() -> Path:
    """获取工作目录.

    如果 config.toml 中配置了 [file] work_dir，则使用该目录；
    否则使用项目根目录下的 workspace 目录。

    Returns:
        工作目录路径
    """
    project_root = Path(settings.project_root)

    if hasattr(settings, "file") and hasattr(settings.file, "work_dir"):
        work_dir = Path(settings.file.work_dir)
        if not work_dir.is_absolute():
            work_dir = project_root / work_dir
    else:
        work_dir = project_root / "workspace"

    work_dir.mkdir(parents=True, exist_ok=True)
    return work_dir


def _validate_path(file_path: str, work_dir: Path) -> Path:
    """验证文件路径是否在工作目录内（安全检查）.

    Args:
        file_path: 文件路径
        work_dir: 工作目录

    Returns:
        安全的完整路径

    Raises:
        ValueError: 如果路径超出工作目录范围
    """
    full_path = (work_dir / file_path).resolve()
    work_dir_resolved = work_dir.resolve()

    if not str(full_path).startswith(str(work_dir_resolved)):
        raise ValueError(f"路径 '{file_path}' 超出工作目录范围")

    return full_path


def get_file_tools() -> list[BaseTool]:
    """获取所有文件管理工具.

    Returns:
        文件工具列表
    """
    global _tools_instance

    if _tools_instance is None:
        work_dir = _get_work_dir()

        toolkit = FileManagementToolkit(
            root_dir=str(work_dir),
        )

        _tools_instance = toolkit.get_tools()
        _tools_instance.append(mkdir_tool)
        logger.info("文件工具初始化完成，共 %d 个工具", len(_tools_instance))
    return _tools_instance
