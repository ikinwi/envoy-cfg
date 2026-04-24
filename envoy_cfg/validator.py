"""Config validator that combines schema validation with interpolation checks."""

from typing import Any, Dict, List, Optional
from .schema import Schema
from .interpolator import interpolate_config


class ValidationError(Exception):
    """Raised when config validation fails."""

    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(self._format(errors))

    @staticmethod
    def _format(errors: List[str]) -> str:
        lines = ["Config validation failed with the following errors:"]
        for i, err in enumerate(errors, 1):
            lines.append(f"  {i}. {err}")
        return "\n".join(lines)


class ConfigValidator:
    """Validates a config dict against a Schema and checks interpolation."""

    def __init__(self, schema: Optional[Schema] = None):
        self._schema = schema

    def validate(self, config: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate and interpolate config, returning the final resolved dict.

        Args:
            config: Raw config dictionary to validate.
            context: Optional extra key/value pairs used for interpolation.

        Returns:
            Validated and interpolated config dict.

        Raises:
            ValidationError: If schema validation fails or interpolation errors occur.
        """
        errors: List[str] = []

        # Step 1: schema validation
        if self._schema is not None:
            try:
                config = self._schema.validate(config)
            except (TypeError, ValueError) as exc:
                errors.append(f"Schema error: {exc}")

        if errors:
            raise ValidationError(errors)

        # Step 2: interpolation
        interp_context = dict(config)
        if context:
            interp_context.update(context)

        try:
            resolved = interpolate_config(config, interp_context)
        except KeyError as exc:
            errors.append(f"Interpolation error — missing key: {exc}")

        if errors:
            raise ValidationError(errors)

        return resolved

    def is_valid(self, config: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> bool:
        """Return True if config passes validation, False otherwise."""
        try:
            self.validate(config, context)
            return True
        except ValidationError:
            return False
