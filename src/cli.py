"""DevMate CLI 主程序.

提供命令行交互界面.
"""
import asyncio
import logging
import sys

import typer
import uvicorn
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from src.agent.agent import get_agent
from src.config import Config, settings  # noqa: F401
from src.logging_config import get_logger, setup_logging

app = typer.Typer(
    name="devmate",
    help="DevMate - 智能编程助手",
    add_completion=False,
)
console = Console()
logger = get_logger(__name__)


def print_banner() -> None:
    """打印 DevMate 欢迎横幅."""
    banner = """
[bold cyan]██████╗ ███████╗██╗   ██╗███╗   ███╗ █████╗ ████████╗███████╗[/bold cyan]
[bold cyan]██╔══██╗██╔════╝██║   ██║████╗ ████║██╔══██╗╚══██╔══╝██╔════╝[/bold cyan]
[bold cyan]██║  ██║█████╗  ██║   ██║██╔████╔██║███████║   ██║   █████╗  [/bold cyan]
[bold cyan]██║  ██║██╔══╝  ╚██╗ ██╔╝██║╚██╔╝██║██╔══██║   ██║   ██╔══╝  [/bold cyan]
[bold cyan]██████╔╝███████╗ ╚████╔╝ ██║ ╚═╝ ██║██║  ██║   ██║   ███████╗[/bold cyan]
[bold cyan]╚═════╝ ╚══════╝  ╚═══╝  ╚═╝     ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝[/bold cyan]
"""
    console.print(banner)
    console.print("[dim]智能编程助手 - 帮助你构建和修改代码库[/dim]")
    console.print()


@app.command()
def chat(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细日志"),
    config_path: str | None = typer.Option(None, "--config", help="配置文件路径"),
) -> None:
    """启动交互式聊天会话."""
    if verbose:
        setup_logging(level=logging.DEBUG)
    else:
        setup_logging(level=logging.INFO)

    if config_path:
        new_settings = Config.load(config_path)
        sys.modules["src.config"].settings = new_settings
        global settings
        settings = new_settings

    print_banner()

    async def run_chat():
        try:
            with console.status("[bold green]正在初始化 DevMate...", spinner="dots"):
                agent = await get_agent()
            console.print("[bold green]✓ DevMate 已就绪![/bold green]")
            console.print()
        except Exception as e:
            console.print(f"[bold red]✗ 初始化失败: {e}[/bold red]")
            raise typer.Exit(code=1) from e

        chat_history = []

        console.print("[dim]输入 'quit' 或 'exit' 退出会话[/dim]")
        console.print()

        while True:
            try:
                user_input = Prompt.ask(
                    "[bold blue]你[/bold blue]",
                    console=console,
                )

                if user_input.lower() in ["quit", "exit", "q"]:
                    console.print("[bold yellow]再见！[/bold yellow]")
                    break

                if not user_input.strip():
                    continue

                with console.status("[bold green]正在思考...", spinner="dots"):
                    response_parts = []
                    async for part in agent.astream(user_input, chat_history):
                        response_parts.append(part)
                    response = "".join(response_parts)

                console.print()
                console.print(
                    Panel(
                        Markdown(response),
                        title="[bold cyan]DevMate[/bold cyan]",
                        border_style="cyan",
                    )
                )
                console.print()

                chat_history.append(("human", user_input))
                chat_history.append(("ai", response))

            except KeyboardInterrupt:
                console.print("\n[bold yellow]再见！[/bold yellow]")
                break
            except Exception as e:
                logger.error(f"交互出错: {e}", exc_info=True)
                console.print(f"[bold red]出错: {e}[/bold red]")

        await agent.close()

    asyncio.run(run_chat())


@app.command()
def ask(
    query: str = typer.Argument(..., help="你的问题或请求"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细日志"),
    config_path: str | None = typer.Option(None, "--config", help="配置文件路径"),
) -> None:
    """一次性问答模式."""
    if verbose:
        setup_logging(level=logging.DEBUG)
    else:
        setup_logging(level=logging.INFO)

    if config_path:
        new_settings = Config.load(config_path)
        sys.modules["src.config"].settings = new_settings
        global settings
        settings = new_settings

    print_banner()

    async def run_ask():
        try:
            with console.status("[bold green]正在初始化 DevMate...", spinner="dots"):
                agent = await get_agent()
        except Exception as e:
            console.print(f"[bold red]✗ 初始化失败: {e}[/bold red]")
            raise typer.Exit(1) from e

        console.print(f"[bold blue]你:[/bold blue] {query}")
        console.print()

        with console.status("[bold green]正在思考...", spinner="dots"):
            response_parts = []
            async for part in agent.astream(query):
                response_parts.append(part)
            response = "".join(response_parts)

        console.print(
            Panel(
                Markdown(response),
                title="[bold cyan]DevMate[/bold cyan]",
                border_style="cyan",
            )
        )

        await agent.close()

    asyncio.run(run_ask())


@app.command()
def serve(
    host: str = typer.Option(None, "--host", help="服务器主机地址"),
    port: int = typer.Option(None, "--port", help="服务器端口"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细日志"),
    config_path: str | None = typer.Option(None, "--config", help="配置文件路径"),
) -> None:
    """启动 Web UI 服务器."""
    if verbose:
        setup_logging(level=logging.DEBUG)
    else:
        setup_logging(level=logging.INFO)


    if config_path:
        new_settings = Config.load(config_path)
        sys.modules["src.config"].settings = new_settings
        global settings
        settings = new_settings

    server_host = host or settings.server.host
    server_port = port or settings.server.port

    print_banner()
    console.print(f"[bold green]启动 Web 服务器在 http://{server_host}:{server_port}[/bold green]")
    console.print()

    uvicorn.run(
        "src.web.app:app",
        host=server_host,
        port=server_port,
        reload=settings.server.debug,
        log_level="debug" if verbose else "info",
    )


def main() -> None:
    """CLI 入口点."""
    app()


if __name__ == "__main__":
    main()
