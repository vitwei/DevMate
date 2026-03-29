"""Agent Skills 工具与中间件模块.

提供 Skills 相关的工具和中间件，用于将 Skills 注入到 Agent 的提示词中。
"""

import logging
from collections.abc import Callable

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.messages import SystemMessage
from langchain.tools import tool

from src.agent.skills.models import Skill
from src.agent.skills.skill_manager import skill_manager

logger = logging.getLogger(__name__)

SKILLS: list[Skill] = skill_manager.get_skills()




@tool
def load_skill(skill_name: str) -> str:
    """Load the full content of a skill into the agent's context.

    Use this when you need detailed information about how to handle a specific
    type of request. This will provide you with comprehensive instructions,
    policies, and guidelines for the skill area.

    Args:
        skill_name: The name of the skill to load (e.g., "expense_reporting", "travel_booking")
    """
    skill = skill_manager.get_skill(skill_name)
    if skill:
        return f"Loaded skill: {skill_name}\n\n{skill['content']}"

    skills = skill_manager.get_skills()
    available = ", ".join(s["name"] for s in skills)
    return f"Skill '{skill_name}' not found. Available skills: {available}"

class SkillMiddleware(AgentMiddleware):
    """Middleware that injects skill descriptions into the system prompt."""

    # Register the load_skill tool as a class variable
    tools = [load_skill]

    def __init__(self):
        """Initialize and generate the skills prompt from SKILLS."""
        # Build skills prompt from the SKILLS list
        skills = skill_manager.get_skills()
        skills_list = []
        for skill in skills:
            skills_list.append(
                f"- **{skill['name']}**: {skill['description']}"
            )
        self.skills_prompt = "\n".join(skills_list)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """Sync: Inject skill descriptions into system prompt."""
        # Build the skills addendum
        skills_addendum = (
            f"\n\n## Available Skills\n\n{self.skills_prompt}\n\n"
            "Use the load_skill tool when you need detailed information "
            "about handling a specific type of request."
        )

        # Append to system message content blocks
        new_content = list(request.system_message.content_blocks) + [
            {"type": "text", "text": skills_addendum}
        ]
        new_system_message = SystemMessage(content=new_content)
        modified_request = request.override(system_message=new_system_message)
        return await handler(modified_request)
