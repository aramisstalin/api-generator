"""
Code generation commands.

Generates FastAPI components from Schema.org entity definitions.
"""

import typer
import asyncio
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm
from pathlib import Path
from typing import List, Optional

from api_forge.core.config import cli_config
from api_forge.core.exceptions import CodeGenerationError, ConfigurationError
from api_forge.generators.orchestrator import GenerationOrchestrator
from api_forge.ai.config import AIConfig

app = typer.Typer(help="Generate application components from Schema.org entities")
console = Console()


@app.command(name="entity")
def generate_entity(
        name: str = typer.Argument(..., help="Schema.org entity name (e.g., Person, Organization)"),
        force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files"),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files"),
        no_ai: bool = typer.Option(False, "--no-ai", help="Disable AI-enhanced generation"),
        no_tests: bool = typer.Option(False, "--no-tests", help="Skip test generation"),
) -> None:
    """
    Generate a complete CRUD API for a Schema.org entity.

    Creates:
    • SQLAlchemy model
    • Pydantic request/response schemas
    • Repository (data access layer)
    • Service (business logic layer)
    • FastAPI router (API endpoints)
    • Test suite (with AI-generated tests)

    AI Features (when enabled):
    • Smart field analysis (unique, indexed, required)
    • Business rule suggestions
    • Security insights
    • Comprehensive test scenarios

    Examples:
        # Generate Person entity with AI enhancement
        api-forge generate entity Person

        # Generate without AI
        api-forge generate entity Product --no-ai

        # Force overwrite existing files
        api-forge generate entity Organization --force

        # Preview without writing
        api-forge generate entity Product --dry-run

        # Skip tests
        api-forge generate entity Order --no-tests

        # Force overwrite
        api-forge generate entity Organization --force
    """
    # Find project configuration
    config_path = cli_config.find_project_config()

    if not config_path:
        console.print("[red]✗[/red] Not in an API Forge project directory")
        console.print(
            "[yellow]Hint:[/yellow] Run this command from a project directory or use 'api-forge init' to create one")
        raise typer.Exit(1)

    # Load configuration
    try:
        config = cli_config.load_project_config(config_path)
        project_path = config_path.parent
    except ConfigurationError as e:
        console.print(f"[red]✗[/red] Configuration error: {e.message}")
        raise typer.Exit(1)

    # Configure AI
    ai_config = None
    if not no_ai and config.generation.ai_enabled:
        try:
            ai_config = AIConfig(
                enabled=True,
                provider=config.generation.ai_provider,
                model=config.generation.ai_model
            )

            if not ai_config.is_configured:
                console.print("[yellow]⚠[/yellow] AI requested but API key not found")
                console.print("[yellow]Set ANTHROPIC_API_KEY environment variable to enable AI[/yellow]")
                ai_config = None
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] AI initialization failed: {e}")
            ai_config = None

    # Override test generation if flag set
    if no_tests:
        config.testing.generate_tests = False

    # Run generation
    try:
        asyncio.run(_generate_entity_async(
            name=name,
            project_path=project_path,
            config=config,
            ai_config=ai_config,
            force=force,
            dry_run=dry_run
        ))
    except CodeGenerationError as e:
        console.print(f"\n[red]✗[/red] Generation failed: {e.message}")
        if e.details:
            console.print(f"[dim]{e.details}[/dim]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]⊘[/yellow] Generation cancelled")
        raise typer.Exit(0)


async def _generate_entity_async(
        name: str,
        project_path: Path,
        config: any,
        ai_config: Optional[AIConfig],
        force: bool,
        dry_run: bool
) -> None:
    """Async wrapper for entity generation."""

    # Display AI status
    if ai_config and ai_config.is_configured:
        console.print(f"[dim]🤖 AI-enhanced generation enabled ({ai_config.model})[/dim]\n")
    else:
        console.print(f"[dim]📝 Template-based generation (no AI)[/dim]\n")

    # Create orchestrator
    orchestrator = GenerationOrchestrator(project_path, config, ai_config)

    # Generate entity
    artifacts = await orchestrator.generate_entity(
        entity_name=name,
        force=force,
        write_files=not dry_run
    )

    # Display summary
    _display_generation_summary(name, artifacts, dry_run, ai_config is not None)

    # Display next steps
    if not dry_run:
        _display_next_steps(name, project_path)


def _display_generation_summary(
        entity_name: str,
        artifacts: List[any],
        dry_run: bool,
        ai_enhanced: bool
) -> None:
    """Display generation summary table."""

    title = f"Generated Files for {entity_name}"
    if ai_enhanced:
        title += " 🤖 AI-Enhanced"

    table = Table(title=title, show_header=True)
    table.add_column("Type", style="cyan", no_wrap=True)
    table.add_column("File", style="white")
    table.add_column("Lines", justify="right", style="magenta")
    table.add_column("Status", style="green")

    for artifact in artifacts:
        status = "✓ Generated" if not dry_run else "Preview"
        if ai_enhanced and artifact.type.value in ["service", "test"]:
            status += " 🤖"

        table.add_row(
            artifact.type.value.title(),
            str(artifact.path),
            str(artifact.lines),
            status
        )

    console.print("\n")
    console.print(table)

    # Summary stats
    total_lines = sum(a.lines for a in artifacts)
    console.print(f"\n[bold]Total:[/bold] {len(artifacts)} files, {total_lines} lines of code")

    if ai_enhanced:
        console.print("[dim]🤖 AI-enhanced components include smart validations and comprehensive tests[/dim]")


def _display_next_steps(entity_name: str, project_path: Path) -> None:
    """Display next steps after generation."""

    entity_lower = entity_name.lower()
    app_name = project_path.name.replace("-", "_")

    next_steps = f"""
[bold cyan]Next Steps:[/bold cyan]

1. Create database migration:
   [green]alembic revision --autogenerate -m "Add {entity_name}"[/green]
   [green]alembic upgrade head[/green]

2. Test the API endpoints:
   [green]# Start the server[/green]
   [green]uvicorn {app_name}.main:app --reload[/green]

   [green]# Visit documentation[/green]
   [green]http://localhost:8000/api/v1/docs[/green]
   
3. Run the tests:
   [green]pytest tests/e2e/test_{entity_lower}_crud.py -v[/green]

4. Try the endpoints:
   [green]POST   /api/v1/{entity_lower}s      [/green] - Create new {entity_name}
   [green]GET    /api/v1/{entity_lower}s      [/green] - List all {entity_name}s
   [green]GET    /api/v1/{entity_lower}s/{{id}} [/green] - Get specific {entity_name}
   [green]PATCH  /api/v1/{entity_lower}s/{{id}} [/green] - Update {entity_name}
   [green]DELETE /api/v1/{entity_lower}s/{{id}} [/green] - Delete {entity_name}

5. Customize the code:
   • Add business logic in [cyan]services/{entity_lower}_service.py[/cyan]
   • Add custom queries in [cyan]repositories/{entity_lower}_repository.py[/cyan]
   • Modify validation in [cyan]schemas/{entity_lower}.py[/cyan]
"""

    console.print(Panel(next_steps, title="🚀 What's Next?", border_style="green"))


@app.command(name="batch")
def generate_batch(
        entities: List[str] = typer.Argument(..., help="List of Schema.org entities"),
        force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files"),
        no_ai: bool = typer.Option(False, "--no-ai", help="Disable AI-enhanced generation"),
        no_tests: bool = typer.Option(False, "--no-tests", help="Skip test generation"),
) -> None:
    """
    Generate multiple entities at once.

    Example:
        api-forge generate batch Person Organization Product Event

        # Without AI
        api-forge generate batch Product Order --no-ai
    """
    # Find project configuration
    config_path = cli_config.find_project_config()

    if not config_path:
        console.print("[red]✗[/red] Not in an API Forge project directory")
        raise typer.Exit(1)

    try:
        config = cli_config.load_project_config(config_path)
        project_path = config_path.parent
    except ConfigurationError as e:
        console.print(f"[red]✗[/red] Configuration error: {e.message}")
        raise typer.Exit(1)

    # Configure AI
    ai_config = None
    if not no_ai and config.generation.ai_enabled:
        try:
            ai_config = AIConfig(
                enabled=True,
                provider=config.generation.ai_provider,
                model=config.generation.ai_model
            )
            if not ai_config.is_configured:
                console.print("[yellow]⚠[/yellow] AI not configured, using templates")
                ai_config = None
        except Exception:
            ai_config = None

    if no_tests:
        config.testing.generate_tests = False

    console.print(f"\n[bold cyan]Batch generating {len(entities)} entities...[/bold cyan]\n")
    if ai_config:
        console.print("[dim]🤖 AI-enhanced generation enabled[/dim]\n")

    # Generate each entity
    success_count = 0
    for entity in entities:
        try:
            console.print(f"\n[bold]→ {entity}[/bold]")
            asyncio.run(_generate_entity_async(
                name=entity,
                project_path=project_path,
                config=config,
                ai_config=ai_config,
                force=force,
                dry_run=False
            ))
            success_count += 1
        except Exception as e:
            console.print(f"[red]✗[/red] Failed: {e}")
            continue

        console.print(
            f"\n[bold green]✓[/bold green] Batch generation complete: {success_count}/{len(entities)} succeeded")


@app.command(name="auth")
def generate_auth() -> None:
    """
    Generate complete authentication system.

    Creates:
    • User, Role, Permission models
    • Authentication endpoints (login, register, refresh)
    • JWT token management
    • RBAC support
    • Security middleware
    • Exception handling

    Example:
        api-forge generate auth
    """
    from rich.prompt import Confirm

    # Find project configuration
    config_path = cli_config.find_project_config()

    if not config_path:
        console.print("[red]✗[/red] Not in an API Forge project directory")
        console.print("[yellow]Hint:[/yellow] Run this command from a project directory")
        raise typer.Exit(1)

    # Load configuration
    try:
        config = cli_config.load_project_config(config_path)
        project_path = config_path.parent
    except ConfigurationError as e:
        console.print(f"[red]✗[/red] Configuration error: {e.message}")
        raise typer.Exit(1)

    # Confirm generation
    console.print("\n[bold]This will generate:[/bold]")
    console.print("  • User, Role, Permission models")
    console.print("  • Authentication endpoints")
    console.print("  • JWT security utilities")
    console.print("  • RBAC dependencies")
    console.print("  • Middleware (logging, rate limiting, correlation)")
    console.print("  • Exception handling system")
    console.print("  • Utility functions (pagination, filtering)")
    console.print()

    if not Confirm.ask("Continue?", default=True):
        console.print("[yellow]Cancelled[/yellow]")
        raise typer.Exit(0)

    # Run generation
    try:
        asyncio.run(_generate_auth_async(project_path, config))
    except CodeGenerationError as e:
        console.print(f"\n[red]✗[/red] Generation failed: {e.message}")
        raise typer.Exit(1)


async def _generate_auth_async(project_path: Path, config: any) -> None:
    """Async wrapper for auth generation."""

    # Create orchestrator
    orchestrator = GenerationOrchestrator(project_path, config)

    # Generate auth system
    artifacts = await orchestrator.generate_auth_system(write_files=True)

    # Display summary
    _display_auth_summary(artifacts)

    # Display next steps
    _display_auth_next_steps(project_path)


def _display_auth_summary(artifacts: List[any]) -> None:
    """Display auth generation summary."""

    table = Table(title="Generated Authentication Files", show_header=True)
    table.add_column("Type", style="cyan", no_wrap=True)
    table.add_column("File", style="white")
    table.add_column("Lines", justify="right", style="magenta")

    for artifact in artifacts:
        table.add_row(
            artifact.type.value.title(),
            str(artifact.path),
            str(artifact.lines)
        )

    console.print("\n")
    console.print(table)

    total_lines = sum(a.lines for a in artifacts)
    console.print(f"\n[bold]Total:[/bold] {len(artifacts)} files, {total_lines} lines of code")


def _display_auth_next_steps(project_path: Path) -> None:
    """Display next steps after auth generation."""

    app_name = project_path.name.replace("-", "_")

    next_steps = f"""
[bold cyan]Next Steps:[/bold cyan]

1. Update configuration:
   • Add SECRET_KEY to .env (use: openssl rand -hex 32)
   • Configure REFRESH_TOKEN_EXPIRE_DAYS
   • Set RATE_LIMIT_ANONYMOUS and RATE_LIMIT_AUTHENTICATED

2. Create database migration:
   [green]alembic revision --autogenerate -m "Add authentication system"[/green]
   [green]alembic upgrade head[/green]

3. Create initial admin user (in Python shell):
   [green]from {app_name}.services.user_service import UserService[/green]
   [green]from {app_name}.schemas.auth import UserRegister[/green]
   [green]# Create admin user...[/green]

4. Test authentication:
   • POST /api/v1/auth/register - Register new user
   • POST /api/v1/auth/login - Get access token
   • Use token in Authorization: Bearer <token>

5. Configure roles and permissions as needed
"""

    console.print(Panel(next_steps, title="🔐 Authentication Setup", border_style="green"))


if __name__ == "__main__":
    app()