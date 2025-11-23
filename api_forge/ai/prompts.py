"""
Prompt templates for AI-powered code generation.

Contains carefully crafted prompts for different generation tasks.
"""

from typing import Dict, Any, List
from api_forge.schema_org.models import SchemaEntity


class PromptTemplates:
    """Collection of prompt templates for AI generation"""

    # System prompts
    SYSTEM_PYTHON_EXPERT = """You are an expert Python developer specializing in:
- FastAPI and modern async Python
- Clean architecture and SOLID principles
- Type hints and Pydantic validation
- SQLAlchemy ORM
- Production-ready, maintainable code
- Comprehensive error handling
- Security best practices

Always generate code that is:
- Well-documented with docstrings
- Fully typed with type hints
- Following PEP 8 style guide
- Production-ready and secure
- Efficiently handling edge cases"""

    @staticmethod
    def analyze_entity(entity: SchemaEntity) -> str:
        """Generate prompt for entity analysis"""
        return f"""Analyze this Schema.org entity for FastAPI application development:

Entity: {entity.name}
Description: {entity.description}
URL: {entity.url}

Properties:
{PromptTemplates._format_properties(entity)}

Tasks:
1. Identify which properties should be:
   - Required vs optional (be practical for real-world use)
   - Unique (email, username, slug, code, identifier)
   - Indexed for query performance
   - Immutable after creation
   - Have default values

2. Suggest sensible validation rules:
   - String length limits
   - Numeric ranges
   - Pattern validations
   - Cross-field validations

3. Identify business rules:
   - State transitions (status changes)
   - Computed fields
   - Cascade delete rules
   - Uniqueness constraints

4. Security considerations:
   - Fields containing PII (need encryption/masking)
   - Fields requiring access control
   - Sensitive operations requiring audit logs

5. Suggest common patterns:
   - Should use soft delete?
   - Need audit timestamps?
   - Version tracking?
   - Full-text search on which fields?

6. Identify useful custom methods:
   - Activation/deactivation
   - Status transitions
   - Computed properties
   - Search methods

Respond with JSON matching this schema:
{{
    "required_fields": ["field1", "field2"],
    "unique_fields": ["email", "username"],
    "indexed_fields": ["status", "created_at"],
    "immutable_fields": ["id", "created_at"],
    "default_values": {{"field": "value"}},
    "validation_rules": [
        {{"field": "email", "type": "email", "description": "..."}}
    ],
    "business_rules": [
        {{"name": "activate", "description": "...", "implementation": "..."}}
    ],
    "security_notes": ["PII in field X", "Audit field Y changes"],
    "custom_methods": [
        {{"name": "method_name", "description": "...", "signature": "..."}}
    ],
    "use_soft_delete": true,
    "searchable_fields": ["name", "description"]
}}"""

    @staticmethod
    def generate_business_method(
            entity_name: str,
            method_description: str,
            context: Dict[str, Any]
    ) -> str:
        """Generate prompt for business method"""
        return f"""Generate a Python async method for a {entity_name} service class.

Method Description: {method_description}

Context:
- Entity: {entity_name}
- Available fields: {context.get('fields', [])}
- Relationships: {context.get('relationships', [])}
- Repository available as: self.repository
- Database session available as: self.db

Requirements:
- Use async/await
- Include proper type hints
- Add comprehensive docstring (Google style)
- Include error handling with custom exceptions
- Validate inputs
- Follow repository pattern
- Return appropriate type

Generate only the method implementation (including decorator, signature, docstring, and body).
"""

    @staticmethod
    def generate_validation(
            entity_name: str,
            field_name: str,
            validation_type: str,
            context: Dict[str, Any]
    ) -> str:
        """Generate prompt for field validation"""
        return f"""Generate a Pydantic field_validator for:

Entity: {entity_name}
Field: {field_name}
Validation Type: {validation_type}
Field Type: {context.get('field_type', 'str')}

Context: {context.get('description', '')}

Requirements:
- Use @field_validator decorator
- Include proper error messages
- Handle None values if field is optional
- Return the validated value
- Consider edge cases

Generate only the validator method (decorator + method).
"""

    @staticmethod
    def generate_test_suite(
            entity_name: str,
            endpoints: List[str],
            context: Dict[str, Any]
    ) -> str:
        """Generate prompt for test suite"""
        return f"""Generate a comprehensive pytest test suite for {entity_name} CRUD operations.

Endpoints to test:
{chr(10).join(f'- {ep}' for ep in endpoints)}

Entity Context:
- Required fields: {context.get('required_fields', [])}
- Optional fields: {context.get('optional_fields', [])}
- Unique fields: {context.get('unique_fields', [])}
- Relationships: {context.get('relationships', [])}

Generate tests for:
1. Successful operations (happy path)
2. Validation errors (missing required fields, invalid formats)
3. Not found errors (404)
4. Duplicate errors (409) for unique fields
5. Authorization errors (401, 403) if auth is enabled
6. Edge cases and boundary conditions

Requirements:
- Use pytest with async support
- Use realistic test data (Faker-like)
- Clear test names describing what is tested
- Arrange-Act-Assert pattern
- Proper fixtures usage
- Test both success and failure scenarios
- Use proper HTTP status code assertions

Generate a complete test class with all methods.
"""

    @staticmethod
    def enhance_code(
            code: str,
            improvement_type: str
    ) -> str:
        """Generate prompt for code enhancement"""
        return f"""Review and enhance this Python code:
```python
{code}
```

Enhancement Type: {improvement_type}

Please improve:
1. Error handling - add try/except where appropriate
2. Documentation - ensure comprehensive docstrings
3. Type hints - add missing type annotations
4. Edge cases - handle boundary conditions
5. Performance - optimize where possible
6. Security - add input validation
7. Readability - improve code clarity

Return only the improved code, no explanations.
"""

    @staticmethod
    def _format_properties(entity: SchemaEntity) -> str:
        """Format entity properties for prompt"""
        lines = []
        for prop_name, prop in entity.properties.items():
            type_str = ", ".join(prop.expected_types)
            lines.append(f"- {prop_name}: {type_str}")
            if prop.description:
                lines.append(f"  Description: {prop.description}")
        return "\n".join(lines)


__all__ = ["PromptTemplates"]