"""
Base generator class.

Provides common functionality for all code generators.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape

from api_forge.schema_org.models import SchemaEntity
from api_forge.generators.artifacts import CodeArtifact, GenerationContext, ArtifactType
from api_forge.core.console import console


class BaseGenerator(ABC):
    """
    Base class for all code generators.

    Provides common functionality like template loading, file writing,
    and code formatting.
    """

    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize generator.

        Args:
            templates_dir: Directory containing Jinja2 templates
        """
        if templates_dir is None:
            # Default to templates directory in package
            templates_dir = Path(__file__).parent.parent / "templates" / "code"

        self.templates_dir = templates_dir

        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self._register_filters()

    def _register_filters(self) -> None:
        """Register custom Jinja2 filters."""
        self.jinja_env.filters['snake_case'] = self._to_snake_case
        self.jinja_env.filters['camel_case'] = self._to_camel_case
        self.jinja_env.filters['pascal_case'] = self._to_pascal_case
        self.jinja_env.filters['pluralize'] = self._pluralize
        self.jinja_env.filters['singularize'] = self._singularize

    @staticmethod
    def _to_snake_case(text: str) -> str:
        """Convert text to snake_case."""
        import re
        # Insert underscore before uppercase letters
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
        # Insert underscore before uppercase letters preceded by lowercase
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    @staticmethod
    def _to_camel_case(text: str) -> str:
        """Convert text to camelCase."""
        components = text.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])

    @staticmethod
    def _to_pascal_case(text: str) -> str:
        """Convert text to PascalCase."""
        return ''.join(x.title() for x in text.split('_'))

    @staticmethod
    def _pluralize(text: str) -> str:
        """Simple pluralization."""
        if text.endswith('y'):
            return text[:-1] + 'ies'
        elif text.endswith('s'):
            return text + 'es'
        else:
            return text + 's'

    @staticmethod
    def _singularize(text: str) -> str:
        """Simple singularization."""
        if text.endswith('ies'):
            return text[:-3] + 'y'
        elif text.endswith('ses'):
            return text[:-2]
        elif text.endswith('s'):
            return text[:-1]
        return text

    @abstractmethod
    def generate(
            self,
            entity: SchemaEntity,
            context: GenerationContext
    ) -> CodeArtifact:
        """
        Generate code artifact.

        Args:
            entity: Schema.org entity to generate code for
            context: Generation context

        Returns:
            Generated code artifact
        """
        pass

    def render_template(
            self,
            template_name: str,
            context: Dict[str, Any]
    ) -> str:
        """
        Render a Jinja2 template.

        Args:
            template_name: Name of the template file
            context: Template context variables

        Returns:
            Rendered template content
        """
        template = self.jinja_env.get_template(template_name)
        return template.render(**context)

    @staticmethod
    def format_code(code: str) -> str:
        """
        Format Python code using black.

        Args:
            code: Python code to format

        Returns:
            Formatted code
        """
        try:
            import black

            mode = black.Mode(
                line_length=100,
                string_normalization=True,
                is_pyi=False,
            )

            formatted = black.format_str(code, mode=mode)
            return formatted

        except ImportError:
            console.print("[yellow]⚠[/yellow] black not installed, skipping formatting")
            return code
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Code formatting failed: {e}")
            return code

    @staticmethod
    def add_imports(code: str, imports: List[str]) -> str:
        """
        Add import statements to code.

        Args:
            code: Existing code
            imports: List of import statements to add

        Returns:
            Code with imports added
        """
        if not imports:
            return code

        # Find where to insert imports (after docstring if present)
        lines = code.split('\n')
        insert_index = 0

        # Skip module docstring
        if lines and lines[0].strip().startswith('"""'):
            in_docstring = True
            for i, line in enumerate(lines[1:], 1):
                if '"""' in line:
                    insert_index = i + 1
                    break

        # Add imports
        import_lines = [f"{imp}" for imp in imports]
        lines[insert_index:insert_index] = import_lines + ['']

        return '\n'.join(lines)

    @staticmethod
    def write_artifact(
            artifact: CodeArtifact,
            project_path: Path,
            force: bool = False
    ) -> bool:
        """
        Write artifact to disk.

        Args:
            artifact: Artifact to write
            project_path: Root project path
            force: Overwrite if file exists

        Returns:
            True if written successfully
        """
        file_path = project_path / artifact.path

        # Check if file exists
        if file_path.exists() and not force:
            console.print(f"[yellow]⚠[/yellow] File exists: {artifact.path}")
            return False

        try:
            # Create directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            file_path.write_text(artifact.content, encoding='utf-8')

            artifact.mark_written()
            console.print(f"[green]✓[/green] Written: {artifact.path}")
            return True

        except Exception as e:
            console.print(f"[red]✗[/red] Failed to write {artifact.path}: {e}")
            artifact.mark_error()
            return False

    @staticmethod
    def validate_artifact(artifact: CodeArtifact) -> bool:
        """
        Validate generated artifact.

        Args:
            artifact: Artifact to validate

        Returns:
            True if valid
        """
        # Basic validation: check syntax for Python
        if artifact.language == "python":
            try:
                import ast
                ast.parse(artifact.content)
                artifact.mark_validated()
                return True
            except SyntaxError as e:
                console.print(
                    f"[red]✗[/red] Syntax error in {artifact.path}: {e}"
                )
                artifact.mark_error()
                return False

        # For other languages, mark as validated
        artifact.mark_validated()
        return True


__all__ = ["BaseGenerator"]