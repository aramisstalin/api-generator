"""
Main CLI entry point for API Forge.

This module provides the primary command-line interface for all API Forge operations.
"""

import typer
from rich.console import Console
from pathlib import Path

from api_forge import __version__
from api_forge.cli.commands import init, generate, migrate, serve, test, json_generate

# Initialize Typer app
app = typer.Typer(
    name="api-forge",
    help="🔨 API Forge - Enterprise-grade FastAPI application generator from Schema.org",
    add_completion=True,
    rich_markup_mode="rich",
    no_args_is_help=True,
)

# Initialize Rich console for beautiful output
console = Console()


def version_callback(value: bool) -> None:
    """Display version information."""
    if value:
        console.print(f"[bold cyan]API Forge[/bold cyan] version [green]{__version__}[/green]")
        console.print("🔨 Enterprise-grade FastAPI application generator")
        raise typer.Exit()


@app.callback()
def callback(
        version: bool = typer.Option(
            None,
            "--version",
            "-v",
            help="Show version information",
            callback=version_callback,
            is_eager=True,
        )
) -> None:
    """
    🔨 API Forge - Enterprise-grade FastAPI application generator.

    Generate production-ready FastAPI applications from Schema.org entity definitions.

    [bold cyan]Features:[/bold cyan]
    • Complete CRUD operations with async database support
    • JWT authentication & RBAC authorization
    • Automatic test suite generation
    • Docker & Kubernetes configurations
    • CI/CD pipeline templates
    • AI-enhanced code generation

    [bold yellow]Quick Start:[/bold yellow]
        api-forge init my-api
        cd my-api
        api-forge generate entity Person
        api-forge serve dev

    [bold green]Documentation:[/bold green] https://docs.apiforge.dev
    """
    pass


@app.command()
def info() -> None:
    """
    Display information about API Forge installation.
    """
    from rich.table import Table
    from rich.panel import Panel
    import sys
    import platform

    # Create info table
    table = Table(title="🔨 API Forge Installation Info", show_header=False)
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    table.add_row("Version", __version__)
    table.add_row("Python Version", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    table.add_row("Platform", platform.system())
    table.add_row("Architecture", platform.machine())

    # Installation path
    import api_forge
    install_path = Path(api_forge.__file__).parent.parent
    table.add_row("Install Path", str(install_path))

    console.print(table)
    console.print()

    # Quick links panel
    links = """
[bold cyan]Documentation:[/bold cyan] https://docs.apiforge.dev
[bold cyan]GitHub:[/bold cyan] https://github.com/apiforge/api-forge
[bold cyan]Issues:[/bold cyan] https://github.com/apiforge/api-forge/issues
    """
    console.print(Panel(links, title="📚 Resources", border_style="blue"))


# Register command groups
app.add_typer(init.app, name="init")
app.add_typer(generate.app, name="generate")
app.add_typer(json_generate.app, name="generate")
app.add_typer(migrate.app, name="migrate")
app.add_typer(serve.app, name="serve")
app.add_typer(test.app, name="test")

if __name__ == "__main__":
    app()