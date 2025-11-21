"""
Pydantic schema generator.

Generates request/response schemas from Schema.org entities.
"""

from pathlib import Path
from typing import Dict, Any, List

from api_forge.generators.base import BaseGenerator
from api_forge.generators.artifacts import CodeArtifact, ArtifactType, GenerationContext
from api_forge.schema_org.models import SchemaEntity, ValidationRule
from api_forge.core.console import console


class SchemaGenerator(BaseGenerator):
    """
    Generates Pydantic schemas.

    Creates schemas for:
    - Request validation (Create, Update)
    - Response serialization
    - List/pagination responses
    """

    def generate(
            self,
            entity: SchemaEntity,
            context: GenerationContext
    ) -> CodeArtifact:
        """
        Generate Pydantic schemas for an entity.

        Args:
            entity: Schema.org entity
            context: Generation context

        Returns:
            Generated schema artifact
        """
        console.print(f"[cyan]Generating schemas for:[/cyan] {entity.name}")

        # Prepare template context
        template_context = self._prepare_context(entity, context)

        # Render template
        code = self.render_template("schema.py.jinja", template_context)

        # Format code
        code = self.format_code(code)

        # Create artifact
        artifact = CodeArtifact(
            type=ArtifactType.SCHEMA,
            path=Path(context.app_name) / "schemas" / f"{entity.name.lower()}.py",
            content=code,
            entity_name=entity.name,
        )

        # Add dependency on model
        artifact.add_dependency(f"{context.app_name}/models/{entity.name.lower()}.py")

        # Validate
        if self.validate_artifact(artifact):
            artifact.mark_generated()
            console.print(f"[green]✓[/green] Schemas generated: {artifact.lines} lines")

        return artifact

    def _prepare_context(
            self,
            entity: SchemaEntity,
            context: GenerationContext
    ) -> Dict[str, Any]:
        """
        Prepare template context for schema generation.

        Args:
            entity: Schema.org entity
            context: Generation context

        Returns:
            Template context dictionary
        """
        # Separate fields by category
        base_fields = []
        required_fields = []
        updatable_fields = []

        for prop_name, prop in entity.properties.items():
            if not prop.is_relationship:
                type_info = getattr(prop, 'type_info', None)
                if not type_info:
                    continue

                field_info = {
                    "name": prop.name,
                    "type_annotation": self._get_pydantic_type(type_info, prop),
                    "description": prop.description,
                    "has_default": not prop.required,
                    "default": "None" if not prop.required else None,
                }

                base_fields.append(field_info)

                if prop.required:
                    required_fields.append(field_info)

                # Most fields are updatable except IDs and timestamps
                if prop.name not in ["id", "created_at", "updated_at"]:
                    updatable_fields.append(field_info)

        # Generate validators
        validators = self._generate_validators(entity)

        # Generate example data
        create_example = self._generate_create_example(entity)
        update_example = self._generate_update_example(entity)

        return {
            "entity": entity,
            "app_name": context.app_name,
            "base_fields": base_fields,
            "required_fields": required_fields,
            "updatable_fields": updatable_fields,
            "validators": validators,
            "relationships": entity.relationships,
            "has_timestamps": context.config.generation.use_audit_timestamps if context.config else True,
            "has_soft_delete": context.config.generation.use_soft_delete if context.config else True,
            "create_example": create_example,
            "update_example": update_example,
        }

    def _get_pydantic_type(self, type_info: Any, prop: Any) -> str:
        """
        Get Pydantic type annotation.

        Args:
            type_info: TypeInfo object
            prop: SchemaProperty

        Returns:
            Pydantic type string
        """
        base_type = type_info.pydantic_annotation

        if type_info.is_optional or not prop.required:
            if not base_type.startswith("Optional["):
                return f"Optional[{base_type}]"

        return base_type

    def _generate_validators(self, entity: SchemaEntity) -> List[Dict[str, str]]:
        """
        Generate Pydantic validators.

        Args:
            entity: Schema.org entity

        Returns:
            List of validator dictionaries
        """
        validators = []

        for prop_name, rules in entity.validation_rules.items():
            for rule in rules:
                validator_code = self._generate_validator_code(prop_name, rule)
                if validator_code:
                    validators.append({
                        "name": f"validate_{prop_name}",
                        "field": prop_name,
                        "code": validator_code
                    })

        return validators

    def _generate_validator_code(
            self,
            field_name: str,
            rule: ValidationRule
    ) -> str:
        """
        Generate validator code for a validation rule.

        Args:
            field_name: Field name
            rule: Validation rule

        Returns:
            Python code for validator
        """
        if rule.type == "email_validation":
            return f"""@field_validator('{field_name}')
    @classmethod
    def validate_{field_name}(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v"""

        elif rule.type == "string_length":
            min_len = rule.params.get("min_length", 0)
            max_len = rule.params.get("max_length", 255)
            return f"""@field_validator('{field_name}')
    @classmethod
    def validate_{field_name}_length(cls, v):
        if v and (len(v) < {min_len} or len(v) > {max_len}):
            raise ValueError('{rule.error_message}')
        return v"""

        elif rule.type == "numeric_range":
            ge = rule.params.get("ge")
            le = rule.params.get("le")
            conditions = []
            if ge is not None:
                conditions.append(f"v < {ge}")
            if le is not None:
                conditions.append(f"v > {le}")

            if conditions:
                condition = " or ".join(conditions)
                return f"""@field_validator('{field_name}')
    @classmethod
    def validate_{field_name}_range(cls, v):
        if v is not None and ({condition}):
            raise ValueError('{rule.error_message}')
        return v"""

        elif rule.type == "pattern":
            pattern = rule.params.get("pattern", "")
            return f"""@field_validator('{field_name}')
    @classmethod
    def validate_{field_name}_pattern(cls, v):
        import re
        if v and not re.match(r'{pattern}', v):
            raise ValueError('{rule.error_message}')
        return v"""

        return ""

    def _generate_create_example(self, entity: SchemaEntity) -> Dict[str, Any]:
        """Generate example data for Create schema."""
        example = {}

        for prop_name, prop in entity.properties.items():
            if not prop.is_relationship and prop.required:
                example[prop_name] = self._get_example_value(prop)

        return example

    def _generate_update_example(self, entity: SchemaEntity) -> Dict[str, Any]:
        """Generate example data for Update schema."""
        example = {}

        # Include a few non-required fields
        count = 0
        for prop_name, prop in entity.properties.items():
            if not prop.is_relationship and prop_name not in ["id", "created_at", "updated_at"]:
                example[prop_name] = self._get_example_value(prop)
                count += 1
                if count >= 3:  # Limit to 3 examples
                    break

        return example

    def _get_example_value(self, prop: Any) -> Any:
        """Get example value for a property."""
        type_info = getattr(prop, 'type_info', None)
        if not type_info:
            return "string"

        lower_name = prop.name.lower()

        # Specific examples based on field name
        if "email" in lower_name:
            return "user@example.com"
        elif "name" in lower_name:
            return "John Doe"
        elif "phone" in lower_name or "telephone" in lower_name:
            return "+1234567890"
        elif "url" in lower_name or "website" in lower_name:
            return "https://example.com"
        elif "age" in lower_name:
            return 25
        elif "price" in lower_name or "amount" in lower_name:
            return 99.99
        elif "description" in lower_name or "text" in lower_name:
            return "Sample description text"
        elif "date" in lower_name:
            return "2024-01-01"

        # Default by type
        python_type = type_info.python_type
        if python_type == "str":
            return "string"
        elif python_type == "int":
            return 0
        elif python_type == "float":
            return 0.0
        elif python_type == "bool":
            return False
        elif python_type == "date":
            return "2024-01-01"
        elif python_type == "datetime":
            return "2024-01-01T00:00:00Z"

        return "value"


__all__ = ["SchemaGenerator"]
