"""Skills 管理模块.

负责从配置的 skills_dir 加载和管理 SKILL.md 文件.
"""

import logging
import re
from pathlib import Path

from src.agent.skills.models import Skill
from src.config import settings

logger = logging.getLogger(__name__)


class SkillManager:
    """技能管理器."""

    _skills: list[Skill] | None = None

    def __init__(self):
        """初始化技能管理器."""
        self._skills = None

    @classmethod
    def get_skills(cls, reload: bool = False) -> list[Skill]:
        """获取所有技能.

        Args:
            reload: 是否强制重新加载

        Returns:
            技能列表
        """
        if cls._skills is None or reload:
            cls._skills = cls._load_skills()
        return cls._skills

    @classmethod
    def _load_skills(cls) -> list[Skill]:
        """从 skills_dir 加载所有 SKILL.md 文件.

        Returns:
            技能列表
        """
        skills_dir = Path(settings.project_root) / settings.skills.skills_dir

        if not skills_dir.exists() or not skills_dir.is_dir():
            logger.warning("Skills directory does not exist: %s", skills_dir)
            return []

        skills: list[Skill] = []

        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue

            try:
                skill = cls._parse_skill_file(skill_file)
                if skill:
                    skills.append(skill)
                    logger.info("Loaded skill: %s", skill["name"])
            except Exception as e:
                logger.error("Failed to load skill from %s: %s", skill_file, e, exc_info=True)

        logger.info("Total skills loaded: %d", len(skills))
        return skills

    @classmethod
    def _parse_skill_file(cls, skill_file: Path) -> Skill | None:
        """解析 SKILL.md 文件.

        SKILL.md 格式:
        ---
        name: skill_name
        description: skill description
        license: ...
        ---
        content...

        Args:
            skill_file: SKILL.md 文件路径

        Returns:
            Skill 对象，如果解析失败返回 None
        """
        try:
            content = skill_file.read_text(encoding="utf-8")

            frontmatter_match = re.match(
                r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL
            )

            if not frontmatter_match:
                logger.warning("No frontmatter found in %s", skill_file)
                return None

            frontmatter = frontmatter_match.group(1)
            main_content = content[frontmatter_match.end() :]

            name = ""
            description = ""

            for line in frontmatter.split("\n"):
                line = line.strip()
                if not line:
                    continue
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    if key == "name":
                        name = value
                    elif key == "description":
                        description = value

            if not name or not description:
                logger.warning(
                    "Missing name or description in %s", skill_file
                )
                return None

            return Skill(
                name=name,
                description=description,
                content=main_content.strip(),
            )

        except Exception as e:
            logger.error("Error parsing %s: %s", skill_file, e, exc_info=True)
            return None

    @classmethod
    def get_skill(cls, name: str) -> Skill | None:
        """根据名称获取技能.

        Args:
            name: 技能名称

        Returns:
            Skill 对象，如果未找到返回 None
        """
        skills = cls.get_skills()
        for skill in skills:
            if skill["name"] == name:
                return skill
        return None

    def load_skills(self) -> None:
        """加载技能 (兼容 API)."""
        self.get_skills(reload=True)

    def list_skills(self) -> list[Skill]:
        """列出所有技能 (兼容 API).

        Returns:
            技能列表
        """
        return self.get_skills()

    def find_relevant_skills(self, query: str) -> list[Skill]:
        """查找相关技能 (兼容 API).

        Args:
            query: 查询文本

        Returns:
            相关技能列表
        """
        skills = self.get_skills()
        relevant_skills = []
        query_lower = query.lower()
        for skill in skills:
            if (
                query_lower in skill["name"].lower()
                or query_lower in skill["description"].lower()
            ):
                relevant_skills.append(skill)
        return relevant_skills

    @staticmethod
    def format_skills_for_prompt(skills: list[Skill]) -> str:
        """格式化技能用于提示词 (兼容 API).

        Args:
            skills: 技能列表

        Returns:
            格式化的提示词
        """
        if not skills:
            return ""
        parts = ["## Available Skills"]
        for skill in skills:
            parts.append(f"- **{skill['name']}**: {skill['description']}")
        return "\n".join(parts)



skill_manager = SkillManager()
