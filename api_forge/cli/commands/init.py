"""
Project initialization command.

Creates a new API Forge project with complete structure, configuration,
and initial files ready for development.
"""

import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from pathlib import Path
from typing import Optional
import subprocess
import sys

from api_forge.core.exceptions import ProjectExistsError, ConfigurationError
from api_forge.core.config import ProjectConfig, GenerationConfig, DatabaseConfig
from api_forge.templates.project import ProjectTemplate

app = typer.Typer(help="Initialize new API Forge projects")
console = Console()


@app.command(name="project")
def init_project(
        name: str = typer.Argument(..., help="Project name (e.g., my-project)"),
        path: Optional[Path] = typer.Option(
            None,
            "--path",
            "-p",
            help="Project directory (defaults to current directory)",
        ),
        template: str = typer.Option(
            "standard",
            "--template",
            "-t",
            help="Project template (standard, minimal, enterprise)",
        ),
        skip_docker: bool = typer.Option(False, "--skip-docker", help="Skip Docker setup"),
        skip_git: bool = typer.Option(False, "--skip-git", help="Skip Git initialization"),
        skip_venv: bool = typer.Option(False, "--skip-venv", help="Skip virtual environment creation"),
        interactive: bool = typer.Option(
            False,
            "--interactive",
            "-i",
            help="Interactive mode with prompts",
        ),
) -> None:
    """
    Initialize a new FastAPI project.

    Creates a complete project structure with:
    • FastAPI application skeleton
    • Database configuration (PostgreSQL + Alembic)
    • Authentication & authorization setup
    • Docker & Docker Compose files
    • CI/CD pipeline templates
    • Testing infrastructure
    • Documentation templates

    Examples:
        # Create a new project in current directory
        api-forge init my-api

        # Create project in specific location
        api-forge init my-api --path ./projects

        # Interactive mode
        api-forge init my-api --interactive

        # Minimal setup without Docker
        api-forge init my-api --skip-docker --skip-git
    """
    console.print("\n[bold cyan]🔨 API Forge - Project Initialization[/bold cyan]\n")

    # Interactive mode - collect additional info
    if interactive:
        name = Prompt.ask("Project name", default=name)
        description = Prompt.ask("Project description", default="Auto-generated API")
        db_name = Prompt.ask("Database name", default=f"{name.replace('-', '_')}_db")
        enable_docker = Confirm.ask("Enable Docker setup?", default=not skip_docker)
        enable_git = Confirm.ask("Initialize Git repository?", default=not skip_git)
        skip_docker = not enable_docker
        skip_git = not enable_git
    else:
        description = "Auto-generated API from Schema.org"
        db_name = f"{name.replace('-', '_')}_db"

    # Determine project path
    if path is None:
        path = Path.cwd()

    project_path = path / name

    # Check if directory exists
    if project_path.exists():
        if not Confirm.ask(
                f"[yellow]Directory {project_path} already exists. Overwrite?[/yellow]"
        ):
            console.print("[red]✗[/red] Project initialization cancelled.")
            raise typer.Exit(1)

    try:
        # Create project configuration
        config = ProjectConfig(
            name=name,
            description=description,
            database=DatabaseConfig(
                provider="postgresql",
                host="localhost",
                port=5432,
                name=db_name,
            ),
            generation=GenerationConfig(),
        )

        # Initialize project using template
        console.print(f"[bold green]Creating project:[/bold green] {name}")
        console.print(f"[bold green]Location:[/bold green] {project_path}\n")

        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
        ) as progress:
            # Task 1: Create directory structure
            task1 = progress.add_task("Creating directory structure...", total=None)
            project_template = ProjectTemplate(project_path, config)
            project_template.create_structure()
            progress.update(task1, completed=True)

            # Task 2: Generate core files
            task2 = progress.add_task("Generating core files...", total=None)
            project_template.generate_core_files(skip_docker=skip_docker)
            progress.update(task2, completed=True)

            # Task 3: Create configuration files
            task3 = progress.add_task("Creating configuration files...", total=None)
            project_template.generate_config_files()
            progress.update(task3, completed=True)

            # Task 4: Initialize Git
            if not skip_git:
                task4 = progress.add_task("Initializing Git repository...", total=None)
                _init_git(project_path)
                progress.update(task4, completed=True)

            # Task 5: Create virtual environment
            if not skip_venv:
                task5 = progress.add_task("Creating virtual environment...", total=None)
                _create_venv(project_path)
                progress.update(task5, completed=True)

        # Success message
        console.print(f"\n[bold green]✓[/bold green] Project initialized successfully!\n")

        # Display next steps
        _display_next_steps(name, project_path, skip_venv)

    except ProjectExistsError as e:
        console.print(f"[red]✗[/red] {e.message}")
        raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]✗[/red] Project initialization failed: {e}")
        raise typer.Exit(1)


def _init_git(project_path: Path) -> None:
    """Initialize Git repository."""
    try:
        subprocess.run(
            ["git", "init"],
            cwd=project_path,
            check=True,
            capture_output=True,
        )

        subprocess.run(
            ["git", "add", "."],
            cwd=project_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit - API Forge project"],
            cwd=project_path,
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        console.print("[yellow]⚠[/yellow] Git initialization failed: verify git is installed and its configuration (user.name and user.email).")
    except FileNotFoundError:
        console.print("[yellow]⚠[/yellow] Git not found - skipping Git initialization")


def _create_venv(project_path: Path) -> None:
    """Create virtual environment and install dependencies."""
    venv_path = project_path / ".venv"

    try:
        # Create venv
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            capture_output=True,
        )

        # Determine pip path
        if sys.platform == "win32":
            pip_path = venv_path / "Scripts" / "pip.exe"
            python_path = venv_path / "Scripts" / "python.exe"
        else:
            pip_path = venv_path / "bin" / "pip"
            python_path = venv_path / "bin" / "python"

        # Upgrade pip
        result = subprocess.run(
            [str(python_path), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            capture_output=True,
        )

        if result.returncode != 0:
            console.print(result.stderr)

        # Install requirements
        requirements_file = project_path / "requirements.txt"
        if requirements_file.exists():
            subprocess.run(
                [str(pip_path), "install", "-r", str(requirements_file), " --trusted-host pypi.org --trusted-host files.pythonhosted.org"],
                check=True,
                capture_output=True,
            )

    except subprocess.CalledProcessError as e:
        console.print(f"[yellow]⚠[/yellow] Virtual environment setup failed: {e}")
    except Exception as e:
        console.print(f"[yellow]⚠[/yellow] Could not create virtual environment: {e}")


def _display_next_steps(name: str, project_path: Path, skip_venv: bool) -> None:
    """Display next steps to user."""

    # Determine activation command
    if sys.platform == "win32":
        activate_cmd = ".\\.venv\\Scripts\\activate"
    else:
        activate_cmd = "source .venv/bin/activate"

    next_steps = f"""
[bold cyan]Next Steps:[/bold cyan]

1. Navigate to your project:
   [green]cd {name}[/green]

{"2. Activate virtual environment:" if not skip_venv else "2. Create and activate virtual environment:"}
   {"[green]" + activate_cmd + "[/green]" if not skip_venv else "[green]python -m venv venv && " + activate_cmd + "[/green]"}

{"3" if not skip_venv else "4"}. Configure your environment:
   [green]cp .env.example .env[/green]
   [green]# Edit .env with your settings[/green]

{"4" if not skip_venv else "5"}. Generate your first entity:
   [green]api-forge generate entity Person[/green]

{"5" if not skip_venv else "6"}. Create and apply database migrations:
   [green]api-forge migrate create "Initial setup"[/green]
   [green]api-forge migrate apply[/green]

{"6" if not skip_venv else "7"}. Start development server:
   [green]api-forge serve dev[/green]

{"7" if not skip_venv else "8"}. Visit your API documentation:
   [green]http://localhost:8000/api/v1/docs[/green]

[bold yellow]Useful Commands:[/bold yellow]
- Generate entity:     [cyan]api-forge generate entity <EntityName>[/cyan]
- Run tests:           [cyan]api-forge test run[/cyan]
- View project info:   [cyan]api-forge info[/cyan]

[bold]Documentation:[/bold] https://docs.apiforge.dev
"""

    console.print(Panel(next_steps, title="🚀 Getting Started", border_style="green"))


if __name__ == "__main__":
    app()