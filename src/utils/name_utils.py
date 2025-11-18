"""
Name truncation utilities for badge generation.
Provides clean API for intelligent name display with cultural awareness.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch


@dataclass
class ParsedName:
    """Structured representation of a parsed name."""
    original: str
    first_name: str
    last_name: str
    middle_names: List[str]
    patronymic: Optional[str] = None
    connectors: List[str] = None
    is_eastern_order: bool = False

    def __post_init__(self):
        if self.connectors is None:
            self.connectors = []


class _NameParser:
    """Internal class for parsing names with cultural awareness."""

    # Cultural markers
    CONNECTORS = {'bin', 'ibn', 'bint', 'al', 'el', 'de', 'del', 'de la', 'von', 'van', 'zu'}
    PATRONYMIC_ENDINGS = {'ovich', 'evich', 'ovna', 'evna', 'son', 'dóttir'}
    EASTERN_SURNAMES = {'Zhang', 'Wang', 'Li', 'Liu', 'Chen', 'Kim', 'Park', 'Lee'}

    @classmethod
    def parse(cls, full_name: str) -> ParsedName:
        """Parse a full name into structured components."""
        if not full_name or not full_name.strip():
            return ParsedName(
                original=full_name,
                first_name="",
                last_name="",
                middle_names=[]
            )

        # Normalize and tokenize
        tokens = full_name.strip().split()

        if len(tokens) == 0:
            return ParsedName(original=full_name, first_name="", last_name="", middle_names=[])
        elif len(tokens) == 1:
            return ParsedName(original=full_name, first_name=tokens[0], last_name="", middle_names=[])

        # Detect name order
        is_eastern = cls._is_eastern_order(tokens)

        if is_eastern:
            return cls._parse_eastern(tokens, full_name)
        else:
            return cls._parse_western(tokens, full_name)

    @classmethod
    def _is_eastern_order(cls, tokens: List[str]) -> bool:
        """Detect if name follows Eastern order (family name first)."""
        if len(tokens) == 2 and tokens[0] in cls.EASTERN_SURNAMES:
            return True
        return False

    @classmethod
    def _parse_eastern(cls, tokens: List[str], original: str) -> ParsedName:
        """Parse Eastern-order names (Last First)."""
        return ParsedName(
            original=original,
            first_name=tokens[-1],  # Given name is last
            last_name=tokens[0],    # Family name is first
            middle_names=tokens[1:-1] if len(tokens) > 2 else [],
            is_eastern_order=True
        )

    @classmethod
    def _parse_western(cls, tokens: List[str], original: str) -> ParsedName:
        """Parse Western-order names (First Middle Last)."""
        connectors = []
        patronymic = None
        middle_names = []

        # Identify connectors
        connector_indices = []
        for i, token in enumerate(tokens[1:-1], start=1):
            if token.lower() in cls.CONNECTORS:
                connectors.append(token)
                connector_indices.append(i)

        # Identify patronymic (middle position, specific endings)
        if len(tokens) >= 3:
            middle_token = tokens[1] if len(tokens) == 3 else tokens[len(tokens) // 2]
            if any(middle_token.lower().endswith(ending) for ending in cls.PATRONYMIC_ENDINGS):
                patronymic = middle_token

        # Middle names are everything between first and last, excluding connectors and patronymic
        for i, token in enumerate(tokens[1:-1], start=1):
            if i not in connector_indices and token != patronymic:
                middle_names.append(token)

        return ParsedName(
            original=original,
            first_name=tokens[0],
            last_name=tokens[-1],
            middle_names=middle_names,
            patronymic=patronymic,
            connectors=connectors,
            is_eastern_order=False
        )


class _NameTruncator:
    """Internal class for progressive name truncation."""

    def __init__(self, max_width_inches: float, font_name: str,
                 default_size: float, min_size: float):
        """Initialize truncator with constraints."""
        self.max_width_inches = max_width_inches
        self.font_name = font_name
        self.default_size = default_size
        self.min_size = min_size

    def truncate(self, full_name: str) -> Dict[str, any]:
        """
        Progressively truncate name to fit constraints.

        Returns:
            dict with keys:
                - text: Display name (potentially truncated)
                - font_size: Font size to use
                - stage: Truncation stage applied (0=none, 1=shrink, 2=truncate)
        """
        if not full_name or not full_name.strip():
            return {"text": full_name, "font_size": self.default_size, "stage": 0}

        # Stage 1: Try at default size
        if self._fits_at_size(full_name, self.default_size):
            return {"text": full_name, "font_size": self.default_size, "stage": 0}

        # Stage 2: Try shrinking
        for size in range(int(self.default_size) - 1, int(self.min_size) - 1, -1):
            if self._fits_at_size(full_name, float(size)):
                return {"text": full_name, "font_size": float(size), "stage": 1}

        # Stage 3: Progressive truncation
        parsed = _NameParser.parse(full_name)
        truncated = self._progressive_truncate(parsed)

        # Try shrinking truncated name
        for size in range(int(self.default_size) - 1, int(self.min_size) - 1, -1):
            if self._fits_at_size(truncated, float(size)):
                return {"text": truncated, "font_size": float(size), "stage": 2}

        # Last resort: use truncated name at minimum size
        return {"text": truncated, "font_size": self.min_size, "stage": 2}

    def _fits_at_size(self, text: str, size: float) -> bool:
        """Check if text fits within max width at given font size."""
        width_pts = pdfmetrics.stringWidth(text, self.font_name, size)
        width_inches = width_pts / 72.0  # 72 points per inch
        # Add 8% safety margin to account for WeasyPrint PDF rendering differences
        safety_margin = 0.08 * self.max_width_inches
        return width_inches <= (self.max_width_inches - safety_margin)

    def _progressive_truncate(self, parsed: ParsedName) -> str:
        """Apply progressive truncation stages."""
        # Stage 3.1: Remove middle names
        if parsed.middle_names:
            return self._reconstruct_name(parsed, include_middle=False)

        # Stage 3.2: Remove patronymic
        if parsed.patronymic:
            return f"{parsed.first_name} {parsed.last_name}"

        # Stage 3.3: Remove connectors (already handled by removing middle names usually)

        # Stage 3.4: Last name to initial
        if parsed.last_name:
            return f"{parsed.first_name} {parsed.last_name[0]}."

        # Stage 3.5: Just first name
        return parsed.first_name

    def _reconstruct_name(self, parsed: ParsedName, include_middle: bool = True) -> str:
        """Reconstruct name from parsed components."""
        if parsed.is_eastern_order:
            # Eastern order: Last First
            if include_middle and parsed.middle_names:
                return f"{parsed.last_name} {' '.join(parsed.middle_names)} {parsed.first_name}"
            return f"{parsed.last_name} {parsed.first_name}"
        else:
            # Western order: First Middle Last
            parts = [parsed.first_name]

            if include_middle:
                if parsed.middle_names:
                    parts.extend(parsed.middle_names)
                if parsed.patronymic:
                    parts.append(parsed.patronymic)

            if parsed.last_name:
                parts.append(parsed.last_name)

            return ' '.join(parts)


def get_display_name(original_name: str, max_width: float = 2.7,
                    font_family: str = "Helvetica",
                    default_font_size: float = 18.0,
                    min_font_size: float = 12.0) -> Dict[str, any]:
    """
    Get optimized display name with intelligent truncation.

    Clean API - implementation details hidden.

    Args:
        original_name: Full name to display
        max_width: Maximum width in inches
        font_family: Font family name (must be registered in ReportLab)
        default_font_size: Preferred font size in points
        min_font_size: Minimum acceptable font size in points

    Returns:
        Dictionary with keys:
            - text: Display name (original or truncated)
            - font_size: Font size to use in points
            - truncated: Boolean indicating if truncation was applied
    """
    truncator = _NameTruncator(
        max_width_inches=max_width,
        font_name=font_family,
        default_size=default_font_size,
        min_size=min_font_size
    )

    result = truncator.truncate(original_name)

    return {
        "text": result["text"],
        "font_size": result["font_size"],
        "truncated": result["text"] != original_name
    }
