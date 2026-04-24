"""Schema validation for environment configuration."""

from typing import Any, Dict, Optional, Type


CONFIG_TYPES = (str, int, float, bool, list, dict)


class SchemaField:
    """Defines a single field in a configuration schema."""

    def __init__(
        self,
        field_type: Type,
        required: bool = True,
        default: Any = None,
        description: str = "",
    ):
        if field_type not in CONFIG_TYPES:
            raise TypeError(f"Unsupported field type: {field_type}")
        self.field_type = field_type
        self.required = required
        self.default = default
        self.description = description

    def validate(self, value: Any, key: str) -> Any:
        """Validate and coerce a value against this field definition."""
        if value is None:
            if self.required and self.default is None:
                raise ValueError(f"Required field '{key}' is missing.")
            return self.default
        if not isinstance(value, self.field_type):
            try:
                value = self.field_type(value)
            except (ValueError, TypeError):
                raise TypeError(
                    f"Field '{key}' expects {self.field_type.__name__}, "
                    f"got {type(value).__name__}."
                )
        return value


class Schema:
    """Collection of SchemaFields used to validate a config layer."""

    def __init__(self, fields: Dict[str, SchemaField]):
        self.fields = fields

    def validate(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a config dict against the schema.

        Returns a new dict with validated (and defaulted) values.
        Raises ValueError or TypeError on validation failure.
        """
        validated: Dict[str, Any] = {}
        for key, field in self.fields.items():
            raw = config.get(key)
            validated[key] = field.validate(raw, key)

        unknown = set(config.keys()) - set(self.fields.keys())
        if unknown:
            raise ValueError(f"Unknown config keys: {', '.join(sorted(unknown))}")

        return validated
