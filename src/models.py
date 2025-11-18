# models.py
"""
Badge system focused on AI-generated images instead of icon grids.
Simpler data model for MVP proof-of-concept.
"""
from __future__ import annotations
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

Align = Literal["left", "center", "right"]

# ---------- Template ----------

class TextZone(BaseModel):
    """Simple text zone with position, size, and styling."""
    x: float
    y: float
    size: float
    max_width: float
    align: Align = "left"
    bold: bool = False
    color: Optional[str] = None  # hex color like "#3D405B"
    max_lines: Optional[int] = None
    model_config = ConfigDict(extra="forbid")


class ImageZone(BaseModel):
    """Zone for placing AI-generated or placeholder images."""
    x: float
    y: float
    w: float
    h: float
    placeholder_color: Optional[str] = "#E07A5F"  # Used if no image provided
    model_config = ConfigDict(extra="forbid")


class TagStyle(BaseModel):
    """Visual style for tags"""
    bg_color: str = "#E07A5F"  # Fallback color if category doesn't specify
    text_color: str = "#FFFFFF"
    font_size: float = 8
    padding_h: float = 0.08  # horizontal padding in inches
    padding_v: float = 0.04  # vertical padding in inches
    radius: float = 0.05     # corner radius in inches
    model_config = ConfigDict(extra="forbid")


class TagZone(BaseModel):
    """Where to place tags on the badge"""
    x: float
    y: float
    max_width: float = 2.0
    gap: float = 0.06  # gap between tags
    style: TagStyle = Field(default_factory=TagStyle)
    model_config = ConfigDict(extra="forbid")


class Template(BaseModel):
    """Simplified template for AI-image-based badges."""
    id: str
    size_in: List[float]  # [w, h] inches - typically [3, 4]
    fonts: Dict[str, str] = Field(default_factory=lambda: {
        "name": "Helvetica",
        "bold": "Helvetica-Bold"
    })
    text_zones: Dict[str, TextZone]
    image_zones: Dict[str, ImageZone]  # e.g., "professional_visual", "interests_band"
    tag_zone: Optional[TagZone] = None
    qr_slot: Optional[Dict[str, float]] = None  # {x, y, size}
    model_config = ConfigDict(extra="forbid")

    @field_validator("size_in")
    @classmethod
    def _ensure_wh(cls, v: List[float]) -> List[float]:
        if len(v) != 2:
            raise ValueError("size_in must be [width, height] in inches")
        return v


# ---------- Event & Attendee ----------

class TagCategory(BaseModel):
    """Definition of a tag category for an event."""
    name: str  # e.g., "Role", "Years as Member"
    type: Literal["select", "write_in"]
    values: List[str] = Field(default_factory=list)  # Allowed values for "select" type
    color: str  # Hex color for tags in this category (e.g., "#E07A5F")
    display_type: Literal["standard", "micro"] = "standard"  # Rendering style: standard (pill) or micro (circular)
    model_config = ConfigDict(extra="forbid")


class EventAttendee(BaseModel):
    """Attendee data specific to an event (includes event-specific tags)."""
    user_id: str
    tags: Dict[str, str] = Field(default_factory=dict)  # category_name → value
    model_config = ConfigDict(extra="forbid")


class Event(BaseModel):
    """Event metadata for badge generation."""
    event_id: str
    display_name: str
    date: Optional[str] = None  # e.g., "Nov 15-17, 2025"
    sponsor: Optional[str] = None
    logo_path: Optional[str] = None  # Path to event logo image
    sponsor_logo_path: Optional[str] = None  # Path to sponsor logo image
    template_id: str
    tags: List[TagCategory] = Field(default_factory=list)

    # Testing/development metadata (displayed in sample sheets only, not used in badge rendering)
    testing_notes: List[str] = Field(default_factory=list)  # e.g., ["Tests long event name", "Multiple tags overflow"]

    model_config = ConfigDict(extra="forbid")


class Attendee(BaseModel):
    """Simplified attendee data for AI-image-based badges."""
    id: str
    name: str
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None  # e.g., "San Francisco, CA"
    pronouns: Optional[str] = None  # e.g., "she/her", "he/him", "they/them"
    profile_url: Optional[str] = None  # For QR code

    # Social media (single preferred platform)
    preferred_social_platform: Optional[str] = None  # e.g., "linkedin", "twitter", "instagram"
    social_handle: Optional[str] = None  # e.g., "@username" or "username"

    # Raw data for AI prompt generation (not used in rendering)
    raw_interests: Optional[str] = None  # Free-form text from user input
    interests: List[str] = Field(default_factory=list)  # AI-parsed from raw_interests
    interests_normalized: List[str] = Field(default_factory=list)  # Filtered, sanitized (3-8 items max)

    # Testing/development metadata (displayed in sample sheets only, not used in badge rendering)
    testing_notes: List[str] = Field(default_factory=list)  # e.g., ["Tests missing location", "Long name truncation"]

    model_config = ConfigDict(extra="forbid")


class BadgeRequest(BaseModel):
    """Request to generate a single badge."""
    event_id: str
    attendee: Attendee
    model_config = ConfigDict(extra="forbid")


class BadgeBatchRequest(BaseModel):
    """Request to generate multiple badges."""
    event_id: str
    attendees: List[Attendee]
    model_config = ConfigDict(extra="forbid")
