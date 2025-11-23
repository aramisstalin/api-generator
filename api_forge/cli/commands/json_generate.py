"""
CLI command for JSON metadata generation.

Provides command-line interface for generating FastAPI apps from JSON metadata.
"""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.table import Table

from api_forge.core.config import cli_config
from api_forge.analyzer_factory import AnalyzerFactory, AnalyzerType
from api_forge.ai.config import AIConfig
from api_forge.generators.orchestrator import GenerationOrchestrator
from api_forge.core.console import console
from api_forge.core.exceptions import ValidationError, ConfigurationError

app = typer.Typer(
    name="json",
    help="Generate FastAPI artifacts from JSON metadata",
    no_args_is_help=True
)


@app.command("generate")
def generate(
        metadata_file: Path = typer.Argument(
            ...,
            help="Path to JSON metadata file",
            exists=True,
            file_okay=True,
            dir_okay=False,
        ),
        no_ai: bool = typer.Option(False, "--no-ai", help="Disable AI-enhanced generation"),
        no_tests: bool = typer.Option(False, "--no-tests", help="Skip test generation"),
        force: bool = typer.Option(
            False,
            "--force", "-f",
            help="Overwrite existing files"
        ),
        dry_run: bool = typer.Option(
            False,
            "--dry-run",
            help="Preview without writing files"
        ),
):
    """
    Generate FastAPI application from JSON metadata file.

    Examples:

        # Basic generation
        api-forge json generate metadata.json

        # With AI enhancement
        api-forge json generate metadata.json --ai

        # Custom output directory
        api-forge json generate metadata.json -o ./my-app

        # Dry run to preview
        api-forge json generate metadata.json --dry-run
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

    asyncio.run(_generate_async(
        metadata_file=metadata_file,
        output_dir=project_path,
        config=config,
        ai_config=ai_config,
        force=force,
        dry_run=dry_run,
    ))


async def _generate_async(
        metadata_file: Path,
        output_dir: Path,
        config: any,
        ai_config: Optional[AIConfig],
        force: bool,
        dry_run: bool,
):
    """Async generation logic."""
    console.print("\n[bold cyan]═══ API Forge - JSON Metadata Generator ═══[/bold cyan]\n")

    enabled_ai = ai_config is not None and ai_config.is_configured
    # Display AI status
    if enabled_ai:
        console.print(f"[dim]🤖 AI-enhanced generation enabled ({ai_config.model})[/dim]\n")
    else:
        console.print(f"[dim]📝 Template-based generation (no AI)[/dim]\n")

    # Create orchestrator
    orchestrator = GenerationOrchestrator(output_dir, config, ai_config)

    # Create analyzer
    try:
        analyzer = AnalyzerFactory.create(
            source=metadata_file,
            analyzer_type=AnalyzerType.JSON_METADATA,
            ai_config=ai_config,
        )
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to create analyzer: {e}")
        raise typer.Exit(1)

    # Analyze entities
    try:
        async with analyzer:
            analyses = await analyzer.analyze_all(use_ai=enabled_ai)

            if not analyses:
                console.print("[red]✗[/red] No entities found in metadata")
                raise typer.Exit(1)

            # Display analysis results
            _display_analysis_results(analyses)

            # Get generation config
            gen_config = analyzer.get_generation_config()

            if dry_run:
                console.print("\n[yellow]Dry run mode - no files will be created[/yellow]")
                _display_generation_plan(analyses, gen_config, output_dir)
                return

            # Check output directory
            if output_dir.exists() and not force:
                console.print(f"\n[red]✗[/red] Output directory exists: {output_dir}")
                console.print("  Use --force to overwrite")
                raise typer.Exit(1)

            # Generate code
            console.print(f"\n[bold cyan]Generating artifacts...[/bold cyan]")
            console.print(f"Output directory: {output_dir}")

            # Create orchestrator
            generator = GenerationOrchestrator(output_dir, config, ai_config)

            await generator.generate_all(analyses)

            console.print(f"\n[green]✓ Generation complete![/green]")
            console.print(f"\nYour FastAPI application is ready at: [bold]{output_dir}[/bold]")

            _display_next_steps(output_dir)

    except ValidationError as e:
        console.print(f"\n[red]✗[/red] Validation error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[red]✗[/red] Generation failed: {e}")
        raise typer.Exit(1)


@app.command("validate")
def validate(
        metadata_file: Path = typer.Argument(
            ...,
            help="Path to JSON metadata file",
            exists=True,
            file_okay=True,
            dir_okay=False,
        ),
):
    """
    Validate JSON metadata file without generating code.

    Checks for:
    - Valid JSON syntax
    - Required fields
    - Relationship consistency
    - Foreign key references
    """
    asyncio.run(_validate_async(metadata_file))


async def _validate_async(metadata_file: Path):
    """Async validation logic."""
    console.print("\n[bold cyan]Validating metadata...[/bold cyan]\n")

    try:
        analyzer = AnalyzerFactory.create(
            source=metadata_file,
            analyzer_type=AnalyzerType.JSON_METADATA,
        )

        # Load triggers validation
        metadata = analyzer.metadata

        if not metadata:
            console.print("[red]✗[/red] Failed to load metadata")
            raise typer.Exit(1)

        console.print("\n[green]✓ Metadata is valid![/green]\n")

        # Show summary
        summary = analyzer.loader.get_summary()

        table = Table(title="Metadata Summary", show_header=True)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Application", summary['app_name'])
        table.add_row("Version", summary['version'])
        table.add_row("Entities", str(summary['total_entities']))
        table.add_row("Fields", str(summary['total_fields']))
        table.add_row("Relationships", str(summary['total_relationships']))
        table.add_row("Backend", summary['backend_framework'])
        table.add_row("Database", summary['database_engine'])

        console.print(table)

    except ValidationError as e:
        console.print(f"\n[red]✗[/red] Validation failed: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[red]✗[/red] Validation failed: {e}")
        raise typer.Exit(1)


@app.command("inspect")
def inspect(
        metadata_file: Path = typer.Argument(
            ...,
            help="Path to JSON metadata file",
            exists=True,
            file_okay=True,
            dir_okay=False,
        ),
        entity: Optional[str] = typer.Option(
            None,
            "--entity", "-e",
            help="Inspect specific entity"
        ),
):
    """
    Inspect metadata file and display entity details.
    """
    asyncio.run(_inspect_async(metadata_file, entity))


async def _inspect_async(metadata_file: Path, entity_name: Optional[str]):
    """Async inspect logic."""
    console.print("\n[bold cyan]Inspecting metadata...[/bold cyan]\n")

    try:
        analyzer = AnalyzerFactory.create(
            source=metadata_file,
            analyzer_type=AnalyzerType.JSON_METADATA,
        )

        if entity_name:
            # Inspect specific entity
            analysis = await analyzer.analyze_entity(entity_name, use_ai=False)
            _display_entity_details(analysis)
        else:
            # List all entities
            analyses = await analyzer.analyze_all(use_ai=False)
            _display_entities_list(analyses)

    except ValidationError as e:
        console.print(f"\n[red]✗[/red] Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[red]✗[/red] Error: {e}")
        raise typer.Exit(1)


def _display_analysis_results(analyses):
    """Display analysis results table."""
    console.print("\n[bold]Analyzed Entities:[/bold]\n")

    table = Table(show_header=True)
    table.add_column("Entity", style="cyan", no_wrap=True)
    table.add_column("Fields", justify="right", style="white")
    table.add_column("Relations", justify="right", style="white")
    table.add_column("Unique", justify="right", style="yellow")
    table.add_column("Indexed", justify="right", style="green")

    for name, analysis in analyses.items():
        table.add_row(
            name,
            str(len(analysis.entity.properties)),
            str(len(analysis.entity.relationships)),
            str(len(analysis.unique_fields)),
            str(len(analysis.suggested_indexes)),
        )

    console.print(table)


def _display_entity_details(analysis):
    """Display detailed entity information."""
    entity = analysis.entity

    console.print(f"\n[bold cyan]Entity: {entity.name}[/bold cyan]")
    console.print(f"Description: {entity.description}\n")

    # Fields
    if entity.properties:
        console.print("[bold]Fields:[/bold]")
        for name, prop in entity.properties.items():
            field_meta = getattr(prop, 'field_metadata', {})
            type_info = getattr(prop, 'type_info', {})

            flags = []
            if field_meta.get('primary'):
                flags.append("PK")
            if field_meta.get('unique'):
                flags.append("UNIQUE")
            if not prop.required:
                flags.append("NULL")
            if field_meta.get('foreign_key'):
                flags.append("FK")

            flags_str = f" [{', '.join(flags)}]" if flags else ""
            type_str = type_info.get('python_type', 'Unknown')

            console.print(f"  • {name}: {type_str}{flags_str}")

    # Relationships
    if entity.relationships:
        console.print("\n[bold]Relationships:[/bold]")
        for rel in entity.relationships:
            console.print(f"  • {rel.name}: {rel.type} → {rel.target_entity}")

    # Metadata
    metadata = getattr(entity, 'metadata', {})
    if metadata:
        console.print("\n[bold]Metadata:[/bold]")
        if metadata.get('audit'):
            console.print("  • Audit logging enabled")
        if metadata.get('soft_delete'):
            console.print("  • Soft delete enabled")
        if metadata.get('permissions'):
            console.print(f"  • Permissions configured")


def _display_entities_list(analyses):
    """Display list of all entities."""
    console.print("\n[bold]Entities:[/bold]\n")

    for name, analysis in analyses.items():
        entity = analysis.entity
        console.print(f"[cyan]{name}[/cyan]")
        console.print(f"  {entity.description}")
        console.print(f"  Fields: {len(entity.properties)}, Relations: {len(entity.relationships)}\n")


def _display_generation_plan(analyses, gen_config, output_dir):
    """Display what would be generated."""
    console.print("\n[bold]Generation Plan:[/bold]\n")

    console.print(f"Output directory: {output_dir}\n")

    console.print("[bold]Files to be generated:[/bold]")
    console.print("  Backend:")
    console.print("    • Database models")
    console.print("    • Pydantic schemas")
    console.print("    • CRUD services")
    console.print("    • API routers")
    console.print("    • Alembic migrations")

    if gen_config.get('generation_options', {}).get('backend', {}).get('create_auth'):
        console.print("    • Authentication system")

    frontend_config = gen_config.get('app', {}).get('frontend')
    if frontend_config:
        console.print("\n  Frontend:")
        console.print("    • Angular components")
        console.print("    • Services")
        console.print("    • Models")
        console.print("    • Routes")


def _display_next_steps(output_dir: Path):
    """Display next steps after generation."""
    console.print("\n[bold cyan]Next Steps:[/bold cyan]\n")

    console.print("1. Install dependencies:")
    console.print(f"   cd {output_dir}")
    console.print("   pip install -r requirements.txt\n")

    console.print("2. Configure environment:")
    console.print("   cp .env.example .env")
    console.print("   # Edit .env with your settings\n")

    console.print("3. Run migrations:")
    console.print("   alembic upgrade head\n")

    console.print("4. Start the server:")
    console.print("   uvicorn main:app --reload\n")

    console.print("5. Access API docs:")
    console.print("   http://localhost:8000/docs\n")


if __name__ == "__main__":
    app()