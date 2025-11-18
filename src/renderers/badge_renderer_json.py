# badge_renderer_json.py
"""
Badge renderer that works with JSON template format.
Simpler, more flexible than the YAML-based system.
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional
from PIL import Image

from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
import qrcode

from ..models import Attendee, TagCategory


def _pt(inches_val: float) -> float:
    """Convert inches to points."""
    return inches_val * inch


def _hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color like '#3D405B' to RGB tuple (0-1 range)."""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return (r/255.0, g/255.0, b/255.0)


class BadgeRendererJSON:
    """Renders badges using JSON template format."""

    def __init__(self, template: dict, event_name: str = "",
                 event_date: str = "", sponsor: str = "", event_logo_path: Optional[str] = None,
                 sponsor_logo_path: Optional[str] = None,
                 tag_categories: Optional[list[TagCategory]] = None):
        self.tmpl = template
        self.event_name = event_name
        self.event_date = event_date
        self.sponsor = sponsor
        self.event_logo_path = event_logo_path
        self.sponsor_logo_path = sponsor_logo_path
        self.tag_categories = tag_categories or []

        # Extract template sections
        self.layout = template.get("layout", {})
        self.fonts = template.get("fonts", {})
        self.dimensions = template.get("dimensions", {"width": 3, "height": 4})
        self.tag_style = template.get("tagStyle", {})

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
        if not isinstance(img, Image.Image):
            img = img.convert("RGB")
        return img

    def _draw_text(self, c: canvas.Canvas, field_name: str, text: str) -> None:
        """Draw a text field using layout and font config."""
        if not text or field_name not in self.layout or field_name not in self.fonts:
            return

        layout = self.layout[field_name]
        font_cfg = self.fonts[field_name]

        x = _pt(layout["x"])
        y = _pt(layout["y"])
        max_w = _pt(layout["max_width"])
        align = layout.get("align", "left")

        font_family = font_cfg.get("family", "Helvetica")
        font_size = font_cfg.get("size", 10)
        color = font_cfg.get("color", "#000000")

        # Set color
        r, g, b = _hex_to_rgb(color)
        c.setFillColorRGB(r, g, b)
        c.setFont(font_family, font_size)

        # Handle text overflow with ellipsis
        display_text = text
        while display_text and c.stringWidth(display_text + "…", font_family, font_size) > max_w:
            display_text = display_text[:-1]
        if display_text and c.stringWidth(display_text, font_family, font_size) > max_w:
            display_text = display_text[:-1] + "…"

        # Apply alignment
        if align == "center":
            sw = c.stringWidth(display_text, font_family, font_size)
            x = x + (max_w - sw) / 2.0

        c.drawString(x, y, display_text)

        # Reset color
        c.setFillColorRGB(0, 0, 0)

    def _draw_image(self, c: canvas.Canvas, zone_name: str, image_path: Optional[str],
                    placeholder_color: str = "#CCCCCC") -> None:
        """Draw an image or placeholder in the specified zone."""
        if zone_name not in self.layout:
            return

        # Skip drawing if no image path is provided
        if not image_path:
            return

        zone = self.layout[zone_name]
        x = _pt(zone["x"])
        y = _pt(zone["y"])
        w = _pt(zone["w"])
        h = _pt(zone["h"])

        if Path(image_path).exists():
            # Draw actual image
            try:
                img = Image.open(image_path)
                c.drawImage(
                    ImageReader(img),
                    x, y, w, h,
                    preserveAspectRatio=True,
                    anchor='c'
                )
            except Exception as e:
                print(f"Warning: Failed to load image {image_path}: {e}")
                self._draw_placeholder(c, x, y, w, h, placeholder_color)
        else:
            # Draw placeholder if path provided but file doesn't exist
            self._draw_placeholder(c, x, y, w, h, placeholder_color)

    def _draw_placeholder(self, c: canvas.Canvas, x: float, y: float,
                         w: float, h: float, color: str) -> None:
        """Draw a colored placeholder rectangle."""
        r, g, b = _hex_to_rgb(color)
        c.setFillColorRGB(r, g, b)
        c.rect(x, y, w, h, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0)

    def _draw_tags(self, c: canvas.Canvas, tags: dict[str, str]) -> None:
        """Draw tags with colors from their categories."""
        if not tags or "tags" not in self.layout:
            return

        layout = self.layout["tags"]
        x_start = _pt(layout["x"])
        y_pos = _pt(layout["y"])
        gap = _pt(layout.get("gap", 0.08))
        max_w = _pt(layout.get("max_width", 2.7))

        # Style defaults
        default_bg_color = self.tag_style.get("bg_color", "#E07A5F")
        text_color = self.tag_style.get("text_color", "#FFFFFF")
        font_size = self.tag_style.get("font_size", 7)
        pad_h = _pt(self.tag_style.get("padding_h", 0.08))
        pad_v = _pt(self.tag_style.get("padding_v", 0.04))
        radius = _pt(self.tag_style.get("radius", 0.05))

        text_r, text_g, text_b = _hex_to_rgb(text_color)

        # Build category name -> color mapping
        category_colors = {}
        for cat in self.tag_categories:
            category_colors[cat.name] = cat.color

        font_family = "Helvetica"
        c.setFont(font_family, font_size)
        cur_x = x_start

        # Render each tag value with its category's color
        for category_name, tag_value in tags.items():
            # Get color for this category, fallback to default
            bg_color = category_colors.get(category_name, default_bg_color)
            bg_r, bg_g, bg_b = _hex_to_rgb(bg_color)

            text_w = c.stringWidth(tag_value, font_family, font_size)
            badge_w = text_w + (pad_h * 2)
            badge_h = font_size + (pad_v * 2)

            # Check if we exceed max width
            if cur_x + badge_w > x_start + max_w:
                break

            # Draw rounded rectangle with category color
            c.setFillColorRGB(bg_r, bg_g, bg_b)
            c.roundRect(cur_x, y_pos, badge_w, badge_h, radius, fill=1, stroke=0)

            # Draw text
            c.setFillColorRGB(text_r, text_g, text_b)
            text_x = cur_x + pad_h
            text_y = y_pos + pad_v + font_size * 0.2
            c.drawString(text_x, text_y, tag_value)

            cur_x += badge_w + gap

        # Reset color
        c.setFillColorRGB(0, 0, 0)

    def render_badge(self, attendee: Attendee, output_path: Path, tags: Optional[dict[str, str]] = None) -> None:
        """Render a complete badge to PDF."""
        w_in = self.dimensions.get("width", 3)
        h_in = self.dimensions.get("height", 4)
        c = canvas.Canvas(str(output_path), pagesize=(_pt(w_in), _pt(h_in)))

        # Draw text fields
        self._draw_text(c, "event_name", self.event_name)
        self._draw_text(c, "event_date", self.event_date)
        self._draw_text(c, "name", attendee.name)
        self._draw_text(c, "title", attendee.title or "")
        self._draw_text(c, "company", attendee.company or "")
        self._draw_text(c, "location", attendee.location or "")

        # Draw tags
        if tags:
            self._draw_tags(c, tags)

        # Draw images
        palette = self.tmpl.get("colorPalette", {})
        logo_color = palette.get("warmOrange", "#E07A5F")
        interest_color = palette.get("teal", "#81B29A")

        self._draw_image(c, "event_logo", self.event_logo_path, logo_color)
        self._draw_image(c, "sponsor_logo", self.sponsor_logo_path, logo_color)
        self._draw_image(c, "interests_band", attendee.interests_image_path, interest_color)

        # Draw QR code if configured and URL provided
        if "qr_code" in self.layout and attendee.profile_url:
            qr_cfg = self.layout["qr_code"]
            qr_img = self._make_qr(attendee.profile_url)
            qr_x = _pt(qr_cfg["x"])
            qr_y = _pt(qr_cfg["y"])
            qr_size = _pt(qr_cfg["size"])
            c.drawImage(
                ImageReader(qr_img),
                qr_x, qr_y,
                width=qr_size, height=qr_size,
                preserveAspectRatio=True, mask="auto"
            )

        # Finalize PDF
        c.showPage()
        c.save()
