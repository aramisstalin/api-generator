"""
Validation rule extractor.

Extracts and generates validation rules for Schema.org properties.
"""

from typing import List, Dict, Any
from api_forge.schema_org.models import (
    SchemaProperty,
    SchemaEntity,
    ValidationRule
)
from api_forge.schema_org.type_mapper import TypeMapper


class ValidationExtractor:
    """
    Extracts validation rules from Schema.org properties.

    Generates Pydantic validators based on:
    - Property types
    - Property names (semantic meaning)
    - Schema.org constraints
    """

    def __init__(self):
        """Initialize extractor."""
        self.type_mapper = TypeMapper()

    def extract_validations(
            self,
            property: SchemaProperty,
            entity: SchemaEntity
    ) -> List[ValidationRule]:
        """
        Extract validation rules for a property.

        Args:
            property: Property to analyze
            entity: Entity containing the property

        Returns:
            List of validation rules
        """
        rules = []

        # Required validation
        if property.required:
            rules.append(ValidationRule(
                type="required",
                error_message=f"{property.name} is required"
            ))

        # Type-specific validations
        if property.expected_types:
            primary_type = property.expected_types[0]

            # String validations
            if self.type_mapper.is_text_type(primary_type):
                rules.extend(self._extract_string_validations(property))

            # Numeric validations
            elif self.type_mapper.is_numeric_type(primary_type):
                rules.extend(self._extract_numeric_validations(property))

            # DateTime validations
            elif self.type_mapper.is_datetime_type(primary_type):
                rules.extend(self._extract_datetime_validations(property))

            # URL validation
            if primary_type == "URL":
                rules.append(ValidationRule(
                    type="url_validation",
                    validator="AnyHttpUrl",
                    error_message="Invalid URL format"
                ))

        # Property name-based validations
        rules.extend(self._extract_semantic_validations(property))

        return rules

    def _extract_string_validations(
            self,
            property: SchemaProperty
    ) -> List[ValidationRule]:
        """Extract validations for string properties."""
        rules = []
        lower_name = property.name.lower()

        # Email validation
        if any(pattern in lower_name for pattern in ["email", "emailaddress"]):
            rules.append(ValidationRule(
                type="email_validation",
                validator="EmailStr",
                error_message="Invalid email format"
            ))

        # Phone validation
        elif any(pattern in lower_name for pattern in ["phone", "telephone", "mobile"]):
            rules.append(ValidationRule(
                type="phone_validation",
                params={"pattern": r"^\+?[1-9]\d{1,14}$"},
                error_message="Invalid phone number format"
            ))

        # String length validation
        else:
            # Large text fields
            if any(pattern in lower_name for pattern in ["description", "text", "content", "bio"]):
                rules.append(ValidationRule(
                    type="string_length",
                    params={"min_length": 0, "max_length": 5000},
                    error_message="Text too long (max 5000 characters)"
                ))
            # Regular string fields
            else:
                rules.append(ValidationRule(
                    type="string_length",
                    params={"min_length": 0, "max_length": 255},
                    error_message=f"{property.name} too long (max 255 characters)"
                ))

        return rules

    def _extract_numeric_validations(
            self,
            property: SchemaProperty
    ) -> List[ValidationRule]:
        """Extract validations for numeric properties."""
        rules = []
        lower_name = property.name.lower()

        # Age validation
        if "age" in lower_name:
            rules.append(ValidationRule(
                type="numeric_range",
                params={"ge": 0, "le": 150},
                error_message="Age must be between 0 and 150"
            ))

        # Rating validation
        elif "rating" in lower_name:
            rules.append(ValidationRule(
                type="numeric_range",
                params={"ge": 0, "le": 5},
                error_message="Rating must be between 0 and 5"
            ))

        # Percentage validation
        elif "percent" in lower_name or "percentage" in lower_name:
            rules.append(ValidationRule(
                type="numeric_range",
                params={"ge": 0, "le": 100},
                error_message="Percentage must be between 0 and 100"
            ))

        # Price/amount validation (must be positive)
        elif any(pattern in lower_name for pattern in ["price", "amount", "cost", "salary"]):
            rules.append(ValidationRule(
                type="numeric_range",
                params={"ge": 0},
                error_message=f"{property.name} must be positive"
            ))

        # Quantity validation
        elif "quantity" in lower_name or "count" in lower_name:
            rules.append(ValidationRule(
                type="numeric_range",
                params={"ge": 0},
                error_message=f"{property.name} must be non-negative"
            ))

        return rules

    def _extract_datetime_validations(
            self,
            property: SchemaProperty
    ) -> List[ValidationRule]:
        """Extract validations for datetime properties."""
        rules = []
        lower_name = property.name.lower()

        # Birth date (must be in the past)
        if "birth" in lower_name:
            rules.append(ValidationRule(
                type="date_past",
                error_message="Birth date must be in the past"
            ))

        # Expiry/end date (typically in the future)
        elif any(pattern in lower_name for pattern in ["expir", "end", "deadline"]):
            rules.append(ValidationRule(
                type="date_future",
                error_message=f"{property.name} must be in the future"
            ))

        # Start/creation date consistency
        elif "start" in lower_name or "begin" in lower_name:
            rules.append(ValidationRule(
                type="date_validation",
                error_message="Invalid start date"
            ))

        return rules

    def _extract_semantic_validations(
            self,
            property: SchemaProperty
    ) -> List[ValidationRule]:
        """Extract validations based on semantic meaning of property names."""
        rules = []
        lower_name = property.name.lower()

        # Username validation
        if "username" in lower_name:
            rules.append(ValidationRule(
                type="pattern",
                params={"pattern": r"^[a-zA-Z0-9_-]{3,30}$"},
                error_message="Username must be 3-30 characters (letters, numbers, _, -)"
            ))

        # Password validation
        elif "password" in lower_name:
            rules.append(ValidationRule(
                type="string_length",
                params={"min_length": 8, "max_length": 100},
                error_message="Password must be at least 8 characters"
            ))

        # Postal/zip code
        elif any(pattern in lower_name for pattern in ["postal", "zip", "zipcode"]):
            rules.append(ValidationRule(
                type="pattern",
                params={"pattern": r"^\d{5}(-\d{4})?$"},
                error_message="Invalid postal code format"
            ))

        # Tax ID / SSN
        elif any(pattern in lower_name for pattern in ["taxid", "ssn", "socialsecurity"]):
            rules.append(ValidationRule(
                type="pattern",
                params={"pattern": r"^\d{3}-\d{2}-\d{4}$"},
                error_message="Invalid tax ID format"
            ))

        # ISBN
        elif "isbn" in lower_name:
            rules.append(ValidationRule(
                type="pattern",
                params={"pattern": r"^(?:\d{9}X|\d{10}|\d{13})$"},
                error_message="Invalid ISBN format"
            ))

        return rules

    def extract_all_validations(
            self,
            entity: SchemaEntity
    ) -> Dict[str, List[ValidationRule]]:
        """
        Extract all validation rules for an entity.

        Args:
            entity: Entity to analyze

        Returns:
            Dictionary mapping property names to validation rules
        """
        all_validations = {}

        for property_name, property in entity.properties.items():
            rules = self.extract_validations(property, entity)
            if rules:
                all_validations[property_name] = rules

        return all_validations

    def generate_validator_code(self, rule: ValidationRule, field_name: str) -> str:
        """
        Generate Pydantic validator code for a rule.

        Args:
            rule: Validation rule
            field_name: Name of the field

        Returns:
            Python code for the validator
        """
        if rule.type == "email_validation":
            return f"""@field_validator('{field_name}')
            @classmethod
            def validate_{field_name}(cls, v):
                if v and '@' not in v:
                    raise ValueError('{rule.error_message or "Invalid email"}')
                return v"""

        elif rule.type == "string_length":
            min_len = rule.params.get("min_length", 0)
            max_len = rule.params.get("max_length", 255)
            return f"""@field_validator('{field_name}')
                @classmethod
                def validate_{field_name}_length(cls, v):
                    if v and (len(v) < {min_len} or len(v) > {max_len}):
                        raise ValueError('{rule.error_message or f"Length must be between {min_len} and {max_len}"}')
                    return v"""

        elif rule.type == "numeric_range":
            ge = rule.params.get("ge")
            le = rule.params.get("le")
            conditions = []
            if ge is not None:
                conditions.append(f"v < {ge}")
            if le is not None:
                conditions.append(f"v > {le}")

            condition = " or ".join(conditions)
            return f"""@field_validator('{field_name}')
                @classmethod
                def validate_{field_name}_range(cls, v):
                    if v is not None and ({condition}):
                        raise ValueError('{rule.error_message or "Value out of range"}')
                    return v"""

        elif rule.type == "pattern":
            pattern = rule.params.get("pattern", "")
            return f"""@field_validator('{field_name}')
                @classmethod
                def validate_{field_name}_pattern(cls, v):
                    import re
                    if v and not re.match(r'{pattern}', v):
                        raise ValueError('{rule.error_message or "Invalid format"}')
                    return v"""

        # Default fallback
        return f"""@field_validator('{field_name}')
            @classmethod
            def validate_{field_name}(cls, v):
                # TODO: Implement validation for {rule.type}
                return v"""


__all__ = ["ValidationExtractor"]