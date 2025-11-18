"""
Badge renderer using HTML/CSS templates and WeasyPrint for PDF generation.
This is a parallel implementation to badge_renderer_json.py for comparison.
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional
import io
import base64
from PIL import Image

from jinja2 import Template
from weasyprint import HTML, CSS
import qrcode
from reportlab.pdfbase import pdfmetrics

from ..models import Attendee, TagCategory
from ..utils.name_utils import get_display_name
from ..location.location_renderer import render_location_graphic
from ..location.location_normalizer import LocationNormalizer


class BadgeRendererHTML:
    """Renders badges using HTML/CSS templates and WeasyPrint."""

    def __init__(self, template_dir: Path, event_id: str, event_name: str = "",
                 event_date: str = "", sponsor: str = "",
                 event_logo_path: Optional[str] = None,
                 sponsor_logo_path: Optional[str] = None,
                 tags: Optional[list[TagCategory]] = None):
        """
        Initialize the HTML badge renderer.

        Args:
            template_dir: Path to directory containing template.html and styles.css
            event_id: Event ID for convention-based paths
            event_name: Name of the event
            event_date: Event date string
            sponsor: Sponsor name
            event_logo_path: Path to event logo image
            sponsor_logo_path: Path to sponsor logo image
            tags: List of tag categories with colors and display types
        """
        self.template_dir = Path(template_dir)
        self.event_id = event_id
        self.event_name = event_name
        self.event_date = event_date
        self.sponsor = sponsor
        self.event_logo_path = event_logo_path
        self.sponsor_logo_path = sponsor_logo_path
        self.tags = tags or []

        # Load HTML template
        html_path = self.template_dir / "template.html"
        with open(html_path, 'r', encoding='utf-8') as f:
            self.html_template = Template(f.read())

        # Load CSS
        css_path = self.template_dir / "styles.css"
        with open(css_path, 'r', encoding='utf-8') as f:
            self.css_content = f.read()

        # Build tag color and display_type mapping from tags
        self.tag_color_map = {}
        self.tag_display_type_map = {}
        for category in self.tags:
            self.tag_color_map[category.name] = category.color
            self.tag_display_type_map[category.name] = category.display_type

        # Cache directory for location graphics
        self.location_cache_dir = Path("output/location_graphics")
        self.location_cache_dir.mkdir(parents=True, exist_ok=True)

        # Location normalizer for handling user input
        self.location_normalizer = LocationNormalizer()

    def _make_qr(self, url: str, box_size: int = 6, border: int = 2) -> Image.Image:
        """Generate a QR code image."""
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=box_size,
            border=border
        )
        qr.add_data(url or "")
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        return img

    def _image_to_data_uri(self, img: Image.Image, format: str = "PNG") -> str:
        """Convert PIL Image to base64 data URI."""
        buffer = io.BytesIO()
        img.save(buffer, format=format)
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        return f"data:image/{format.lower()};base64,{img_base64}"

    def _get_location_graphic(self, location_str: str) -> Optional[Path]:
        """
        Get or generate location graphic for a location string.

        Uses location normalization to handle neighborhoods, misspellings, etc.
        Uses caching to avoid regenerating graphics for the same location.

        Args:
            location_str: Location string (e.g., "Dayton, Ohio" or "Short North, Columbus, OH")

        Returns:
            Path to SVG file, or None if generation failed
        """
        if not location_str:
            return None

        # Normalize location to standard format (e.g., "Columbus, OH")
        normalized_location = self.location_normalizer.normalize(location_str)

        if not normalized_location:
            print(f"  Warning: Could not normalize location: {location_str}")
            return None

        # Create cache filename from normalized location
        cache_filename = normalized_location.replace(", ", "_").replace(" ", "_") + ".svg"
        cache_path = self.location_cache_dir / cache_filename

        # Return cached version if it exists
        if cache_path.exists():
            return cache_path.absolute()

        # Generate new graphic using normalized location
        result = render_location_graphic(
            location_str=normalized_location,
            output_path=cache_path,
            canvas_size=(144, 144)  # 0.5in at 288 DPI
        )

        if result:
            return result.absolute()
        return None

    def _calculate_title_lines(self, title: Optional[str]) -> int:
        """
        Calculate how many lines a title will occupy.

        Uses text width measurement to predict wrapping behavior.
        Conservative: if close to threshold, assumes it wraps.

        Args:
            title: Job title text

        Returns:
            0 (no title), 1 (single line), or 2 (wraps to 2 lines)
        """
        if not title or not title.strip():
            return 0

        # Title constraints from styles.css
        max_width_inches = 2.2  # Width available for title (to right of location graphic)
        font_size = 10.0  # Title font size
        font_name = "Helvetica"

        # Measure rendered width
        width_pts = pdfmetrics.stringWidth(title, font_name, font_size)
        width_inches = width_pts / 72.0

        # Conservative threshold: if within 5% of max, assume it wraps
        safety_margin = 0.05 * max_width_inches

        if width_inches <= (max_width_inches - safety_margin):
            return 1
        else:
            return 2  # CSS line-clamp limits to 2 max

    def _validate_micro_tag(self, category_name: str, value: str, max_chars: int = 5) -> None:
        """
        Validate that a micro-tag value doesn't exceed character limit.

        Args:
            category_name: Name of the tag category
            value: Tag value to validate
            max_chars: Maximum allowed characters (default 5)

        Raises:
            ValueError: If micro-tag exceeds character limit
        """
        if len(value) > max_chars:
            raise ValueError(
                f"Micro-tag '{category_name}' value '{value}' exceeds {max_chars} character limit "
                f"({len(value)} chars). Micro-tags must be ≤{max_chars} chars for circular display."
            )

    def _calculate_tag_row_styling(self, tag_values: list[str], max_width: float = 2.7) -> dict:
        """
        Calculate optimal styling for a row of tags to ensure they fit within max_width.

        AUTO-SHRINK ALGORITHM:
        Tags are sized by progressively reducing visual properties in this order:
        1. Gap (space between tags): 0.08in → 0.06in → 0.04in
        2. Padding (horizontal): 0.12in → 0.10in → 0.08in
        3. Font size: 8pt → 7.5pt → 7pt

        This creates 27 possible combinations (3×3×3). The algorithm tries each combination
        in order until it finds one where the total width fits within the safe max width
        (93% of max_width to account for font rendering variations).

        CRITICAL: The calculated values are applied via INLINE STYLES in template.html.
        The CSS file contains default values only. For this to work correctly, the CSS
        MUST have `flex-shrink: 0` to prevent the browser from overriding these calculations.

        See docs/DESIGN.md#tag-system and docs/TAG_SYSTEM.md for detailed documentation.

        Args:
            tag_values: List of tag text values for this row
            max_width: Maximum width in inches (default 2.7in, 2.25in for bottom with micro badge)

        Returns:
            dict with font_size (float), padding_h (float), gap (float) values in inches/points
        """
        if not tag_values:
            return {'font_size': 8, 'padding_h': 0.12, 'gap': 0.08}

        # Default styling
        base_font_size = 8
        base_padding_h = 0.12
        base_padding_v = 0.06
        base_gap = 0.08
        border_radius = 0.08
        font_name = "Helvetica"
        font_weight = 600  # Using semibold weight

        # Safety margin: pdfmetrics.stringWidth doesn't account for bold/semibold rendering
        # which makes text slightly wider. Add 7% safety margin.
        safety_factor = 0.93  # Use 93% of max_width to ensure tags don't overflow
        safe_max_width = max_width * safety_factor

        # Progressive reduction steps
        gap_steps = [0.08, 0.06, 0.04]
        padding_steps = [0.12, 0.10, 0.08]
        font_steps = [8, 7.5, 7]

        # Try each combination until we find one that fits
        for font_size in font_steps:
            for padding_h in padding_steps:
                for gap in gap_steps:
                    total_width = 0

                    for i, tag_text in enumerate(tag_values):
                        # Calculate text width
                        text_width_pts = pdfmetrics.stringWidth(tag_text, font_name, font_size)
                        text_width_in = text_width_pts / 72.0

                        # Tag width = padding + text + padding
                        tag_width = (padding_h * 2) + text_width_in
                        total_width += tag_width

                        # Add gap after each tag except the last
                        if i < len(tag_values) - 1:
                            total_width += gap

                    # Check if this configuration fits within safe max width
                    if total_width <= safe_max_width:
                        return {
                            'font_size': font_size,
                            'padding_h': padding_h,
                            'gap': gap
                        }

        # If nothing fits, return most aggressive shrinking
        return {
            'font_size': 7,
            'padding_h': 0.08,
            'gap': 0.04
        }

    def _calculate_professional_positioning(self, title: Optional[str]) -> dict:
        """
        Calculate positioning for professional info block with vertical centering.

        Returns:
            dict with professional_top and graphic_offset values
        """
        title_lines = self._calculate_title_lines(title)

        # Professional block starts after separator
        # Separator at 1.75in, add 0.08in gap to mirror gap above separator
        professional_top = 1.83

        # Font size and line height constants
        title_font_pt = 10.0
        title_line_height = 1.2
        company_font_pt = 9.0
        company_line_height = 1.2
        company_margin_top = 0.04
        graphic_size = 0.4

        # Calculate title height in inches
        if title_lines == 0:
            title_height = 0
        elif title_lines == 1:
            title_height = (title_font_pt * title_line_height) / 72
        else:  # 2 lines
            title_height = (title_font_pt * title_line_height * 2) / 72

        # Company height in inches
        company_height = (company_font_pt * company_line_height) / 72

        # Total text block height
        total_height = title_height + company_margin_top + company_height

        # Center graphic with text block
        text_center = total_height / 2
        graphic_offset = text_center - (graphic_size / 2)

        return {
            'professional_top': professional_top,
            'graphic_offset': graphic_offset
        }

    def _prepare_badge_html(self, attendee: Attendee,
                            tags: Optional[dict[str, str]] = None) -> str:
        """
        Prepare badge HTML content (internal method used by both render_badge and render_badge_html).

        Args:
            attendee: Attendee data
            tags: Dictionary of tag_category_key -> tag_value

        Returns:
            Rendered HTML string
        """
        # Generate QR code as data URI
        qr_code_data_uri = None
        if attendee.profile_url:
            qr_img = self._make_qr(attendee.profile_url)
            qr_code_data_uri = self._image_to_data_uri(qr_img)

        # Get optimized display name with smart truncation
        name_info = get_display_name(
            original_name=attendee.name,
            max_width=2.7,  # Full badge width minus margins
            font_family="Helvetica",
            default_font_size=18.0,
            min_font_size=12.0
        )

        # Calculate title lines and interests band position
        # Position interests band based on title lines for optimal spacing
        title_lines = self._calculate_title_lines(attendee.title)

        # Calculate professional block positioning for vertical centering
        prof_layout = self._calculate_professional_positioning(attendee.title)

        # Calculate interests_bottom dynamically based on professional block height
        # Professional block starts at 1.75in, we need to calculate where it ends
        professional_top = prof_layout['professional_top']

        # Calculate content height (same logic as in _calculate_professional_positioning)
        title_font_pt = 10.0
        title_line_height = 1.2
        company_font_pt = 9.0
        company_line_height = 1.2
        company_margin_top = 0.04

        if title_lines == 0:
            title_height = 0
        elif title_lines == 1:
            title_height = (title_font_pt * title_line_height) / 72
        else:
            title_height = (title_font_pt * title_line_height * 2) / 72

        company_height = (company_font_pt * company_line_height) / 72
        total_content_height = title_height + company_margin_top + company_height

        # Calculate where professional block ends
        professional_bottom = professional_top + total_content_height

        # Desired gap before interests band
        desired_gap = 0.10  # Gap between professional block and interests

        # Calculate interests band top position
        interests_top = professional_bottom + desired_gap

        # Interests band dimensions
        badge_height = 4.0  # inches
        interests_band_height = 1.35  # inches

        # Bottom tags constraints - they're positioned at bottom: 0.15in with ~0.23in total height
        # This means tags top is at ~4.0 - 0.15 - 0.23 = 3.62in from top
        bottom_tags_top = 3.62  # Top edge of bottom tags
        min_gap_to_tags = 0.10  # Minimum gap between interests band and tags

        # Calculate maximum allowed bottom edge of interests band
        max_interests_bottom_edge = bottom_tags_top - min_gap_to_tags  # 3.52in from top

        # Calculate available height for interests band
        available_height = max_interests_bottom_edge - interests_top

        # Scale down interests band if it won't fit (maintaining 2:1 aspect ratio)
        if available_height < interests_band_height:
            # Scale proportionally to fit available space
            scale_factor = available_height / interests_band_height
            scaled_height = available_height
            scaled_width = 2.7 * scale_factor  # Maintain 2:1 aspect ratio

            # Center horizontally when scaled down
            left_offset = (2.7 - scaled_width) / 2
        else:
            # Use full size
            scaled_height = interests_band_height
            scaled_width = 2.7
            left_offset = 0

        # Calculate bottom position (distance from bottom edge)
        interests_bottom = badge_height - interests_top - scaled_height

        # Generate location graphic if location exists
        location_graphic_path = None
        if attendee.location:
            location_graphic_path = self._get_location_graphic(attendee.location)

        # Map social platform to Font Awesome icon name
        social_platform = None
        if attendee.preferred_social_platform:
            # Map platform names to Font Awesome brand icon names
            platform_map = {
                'linkedin': 'linkedin',
                'twitter': 'x-twitter',
                'x': 'x-twitter',
                'github': 'github',
                'instagram': 'instagram',
                'facebook': 'facebook',
                'youtube': 'youtube',
                'tiktok': 'tiktok',
            }
            social_platform = platform_map.get(attendee.preferred_social_platform.lower())

        # Get interests image using convention-based path
        # Interests images are OPTIONAL - only required if attendee has interests
        interests_image_path = None

        # Check if attendee has any interests (normalized or regular)
        has_interests = (
            (attendee.interests_normalized and len(attendee.interests_normalized) > 0) or
            (attendee.interests and len(attendee.interests) > 0)
        )

        if has_interests:
            interests_image_path = (
                Path(__file__).parent.parent.parent /
                "output" / "working" / self.event_id / attendee.id /
                "generated_images" / "interests_illustration.png"
            )

            if not interests_image_path.exists():
                raise FileNotFoundError(
                    f"Interests image not found at {interests_image_path}. "
                    f"Attendee has interests but image is missing. "
                    f"Generate the image first before rendering the badge."
                )

        # Calculate optimal tag styling for each row
        tags_dict = tags or {}
        tag_items = list(tags_dict.items())

        # Validate micro-tags and build tag metadata
        tag_metadata = []
        micro_badge = None  # Will hold micro-tag for special positioning

        for category_name, value in tag_items:
            display_type = self.tag_display_type_map.get(category_name, "standard")

            # Validate micro-tag character limit
            if display_type == "micro":
                self._validate_micro_tag(category_name, value)
                # Extract micro-tag for special positioning (only support one micro-tag)
                if micro_badge is None:
                    micro_badge = {
                        'category': category_name,
                        'value': value,
                        'color': self.tag_color_map.get(category_name, '#E07A5F')
                    }
                    continue  # Skip adding to tag_metadata - it'll be positioned separately

            tag_metadata.append({
                'category': category_name,
                'value': value,
                'display_type': display_type,
                'color': self.tag_color_map.get(category_name, '#E07A5F')
            })

        # Top row: first 2 tags (excluding micro-tag)
        top_tag_values = [value for _, value in tag_items[:2] if self.tag_display_type_map.get(_[0] if isinstance(_, tuple) else _, "standard") != "micro"]
        # Need to get values from tag_metadata instead
        top_tags = [t for t in tag_metadata[:2]]
        top_tag_values = [t['value'] for t in top_tags]
        top_tag_styling = self._calculate_tag_row_styling(top_tag_values)

        # Bottom row: remaining tags (2-3 tags)
        # LAYOUT: Bottom tags use space-between layout - standard tags left, micro badge right
        bottom_tags = [t for t in tag_metadata[2:]]
        bottom_tag_values = [t['value'] for t in bottom_tags]

        # CRITICAL: Micro badge width reservation
        # When a micro badge exists, it takes up space on the right side of the bottom row.
        # Total badge width (minus margins): 2.7in
        # Micro badge layout: 0.35in (circle) + ~0.1in (implicit gap from space-between)
        # Available width for standard tags: 2.7 - 0.45 = 2.25in
        #
        # Without micro badge, standard tags can use full width: 2.7in
        #
        # This max_width is passed to _calculate_tag_row_styling() to ensure proper auto-shrink.
        bottom_max_width = 2.25 if micro_badge else 2.7
        bottom_tag_styling = self._calculate_tag_row_styling(bottom_tag_values, max_width=bottom_max_width)

        # Prepare template context
        context = {
            'event_name': self.event_name,
            'event_date': self.event_date,
            'sponsor': self.sponsor,
            'event_logo_path': Path(self.event_logo_path).absolute() if self.event_logo_path else None,
            'sponsor_logo_path': Path(self.sponsor_logo_path).absolute() if self.sponsor_logo_path else None,
            'name': name_info['text'],
            'name_font_size': name_info['font_size'],
            'title': attendee.title,
            'company': attendee.company,
            'location': attendee.location,
            'pronouns': attendee.pronouns,
            'location_graphic_path': location_graphic_path,
            'social_platform': social_platform,
            'social_handle': attendee.social_handle,
            'tags': tags or {},
            'tag_metadata': tag_metadata,
            'micro_badge': micro_badge,  # Micro-tag for special positioning on identity row
            'tag_colors': self.tag_color_map,
            'top_tag_styling': top_tag_styling,
            'bottom_tag_styling': bottom_tag_styling,
            'qr_code_data_uri': qr_code_data_uri,
            'interests_image_path': interests_image_path.absolute() if interests_image_path else None,
            'interests_bottom': interests_bottom,
            'interests_width': scaled_width,
            'interests_height': scaled_height,
            'interests_left_offset': left_offset,
            'professional_top': prof_layout['professional_top'],
            'graphic_offset': prof_layout['graphic_offset'],
        }

        # Render HTML
        html_content = self.html_template.render(**context)
        return html_content

    def render_badge_html(self, attendee: Attendee,
                          tags: Optional[dict[str, str]] = None) -> str:
        """
        Render badge HTML (without generating PDF).

        This is useful for embedding badges in other documents (e.g., sample sheets).

        Args:
            attendee: Attendee data
            tags: Dictionary of tag_category_key -> tag_value

        Returns:
            Rendered HTML string for the badge
        """
        return self._prepare_badge_html(attendee, tags)

    def render_badge(self, attendee: Attendee, output_path: Path,
                     tags: Optional[dict[str, str]] = None) -> None:
        """
        Render a badge to PDF using HTML/CSS.

        Args:
            attendee: Attendee data
            output_path: Path to save the PDF
            tags: Dictionary of tag_category_key -> tag_value
        """
        # Generate HTML content
        html_content = self._prepare_badge_html(attendee, tags)

        # Generate PDF with WeasyPrint
        output_path.parent.mkdir(parents=True, exist_ok=True)
        HTML(string=html_content, base_url=str(self.template_dir)).write_pdf(
            str(output_path),
            stylesheets=[CSS(string=self.css_content)]
        )
