"""DevMate Web UI 应用.

使用 FastAPI 提供 Web 界面.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.agent.agent import get_agent
from src.logging_config import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan 上下文管理器."""
    logger.info("DevMate Web 服务器启动")
    agent = await get_agent()
    app.state.agent = agent
    yield
    await agent.close()
    logger.info("DevMate Web 服务器关闭")


app = FastAPI(title="DevMate", description="智能编程助手", lifespan=lifespan)

templates_path = Path(__file__).parent / "templates"

static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


class ChatMessage(BaseModel):
    """聊天消息模型."""
    message: str
    history: list[tuple[str, str]] | None = None


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    """主页."""
    index_file = templates_path / "index.html"
    with open(index_file, encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@app.post("/api/chat")
async def chat_endpoint(
    message: Annotated[str, Form()],
) -> dict[str, str]:
    """聊天 API 端点.

    Args:
        message: 用户消息

    Returns:
        Agent 响应
    """
    agent = await get_agent()
    response_parts = []
    async for part in agent.astream(message):
        response_parts.append(part)
    response = "".join(response_parts)
    return {"response": response}


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket) -> None:
    """WebSocket 聊天端点.

    Args:
        websocket: WebSocket 连接
    """
    await websocket.accept()
    agent = await get_agent()
    chat_history = []

    try:
        while True:
            data = await websocket.receive_json()
            user_message = data.get("message", "")

            await websocket.send_json({
                "type": "typing",
                "status": True,
            })

            full_response = ""
            
            await websocket.send_json({
                "type": "stream_start",
            })

            async for part in agent.astream(user_message, chat_history):
                if part:
                    full_response += part
                    await websocket.send_json({
                        "type": "stream_chunk",
                        "content": part,
                    })

            await websocket.send_json({
                "type": "stream_end",
                "content": full_response,
            })

            chat_history.append(("human", user_message))
            chat_history.append(("ai", full_response))

            await websocket.send_json({
                "type": "typing",
                "status": False,
            })

    except WebSocketDisconnect:
        logger.info("WebSocket 连接断开")
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}", exc_info=True)
        await websocket.close(code=1011)
