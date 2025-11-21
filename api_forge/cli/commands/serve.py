"""
Development server commands.

Starts the FastAPI development server with hot reload.
"""

import typer
from rich.console import Console

app = typer.Typer(help="Development server commands")
console = Console()


@app.command(name="dev")
def serve_dev(
        host: str = typer.Option("0.0.0.0", help="Host to bind to"),
        port: int = typer.Option(8000, help="Port to bind to"),
) -> None:
    """
    Start development server with hot reload.

    Example:
        api-forge serve dev --port 8000
    """
    console.print("[yellow]⚠[/yellow] Server commands will be implemented in Phase 2")
    console.print(f"[cyan]Would start server at:[/cyan] http://{host}:{port}")


if __name__ == "__main__":
    app()