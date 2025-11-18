"""
Generate standalone HTML preview of a badge for fast iteration.
Opens in browser without PDF conversion for instant visual feedback.
"""
from pathlib import Path
import json
import io
import base64
from datetime import datetime
from PIL import Image
from jinja2 import Template
import qrcode

from models import EventV2, AttendeeV2, EventAttendee
from location_renderer import render_location_graphic
from name_utils import get_display_name


ROOT = Path(__file__).parent


def load_json(path: Path):
    """Load and parse JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def make_qr(url: str, box_size: int = 6, border: int = 2) -> Image.Image:
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


def image_to_data_uri(img: Image.Image, format: str = "PNG") -> str:
    """Convert PIL Image to base64 data URI."""
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    return f"data:image/{format.lower()};base64,{img_base64}"


def file_to_data_uri(file_path: Path) -> str:
    """Convert image file to data URI."""
    if not file_path.exists():
        return ""
    img = Image.open(file_path)
    return image_to_data_uri(img)


def svg_to_data_uri(svg_path: Path) -> str:
    """Convert SVG file to data URI."""
    if not svg_path.exists():
        return ""
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg_content = f.read()
    svg_base64 = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
    return f"data:image/svg+xml;base64,{svg_base64}"


def generate_preview(user_id: str = "user_007", output_path: Path = None,
                     show_grid: bool = True) -> Path:
    """
    Generate standalone HTML preview of a badge.

    Args:
        user_id: Attendee ID to preview (default: user_007 - long name/title)
        output_path: Where to save HTML (default: output/preview/badge_preview.html)
        show_grid: Whether to show alignment grid overlay

    Returns:
        Path to generated HTML file
    """
    if output_path is None:
        output_path = ROOT / "output" / "preview" / "badge_preview.html"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load data
    events_data = load_json(ROOT / "mocks" / "events.json")
    attendees_data = load_json(ROOT / "mocks" / "attendees.json")
    event_attendees_data = load_json(ROOT / "mocks" / "event_attendees.json")

    # Parse models
    events = {e["event_id"]: EventV2.model_validate(e) for e in events_data}
    attendees = {a["id"]: AttendeeV2.model_validate(a) for a in attendees_data}

    # Use Ohio Business Meetup event
    event_id = "cohatch_afterhours"
    event = events[event_id]
    attendee = attendees[user_id]

    # Get tags for this attendee
    event_attendees = [EventAttendee.model_validate(ea)
                      for ea in event_attendees_data[event_id]]
    tags = {}
    for ea in event_attendees:
        if ea.user_id == user_id:
            tags = ea.tags
            break

    # Build tag color mapping
    tag_color_map = {}
    for category in event.tag_categories:
        tag_color_map[category.name] = category.color

    # Load HTML template
    html_template_path = ROOT / "config" / "html_templates" / "professional" / "template.html"
    with open(html_template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()

    # Load CSS
    css_path = ROOT / "config" / "html_templates" / "professional" / "styles.css"
    with open(css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()

    # Generate QR code as data URI
    qr_code_data_uri = None
    if attendee.profile_url:
        qr_img = make_qr(attendee.profile_url)
        qr_code_data_uri = image_to_data_uri(qr_img)

    # Convert images to data URIs for embedded preview
    event_logo_uri = ""
    if event.logo_path and Path(event.logo_path).exists():
        event_logo_uri = file_to_data_uri(Path(event.logo_path))

    sponsor_logo_uri = ""
    if event.sponsor_logo_path and Path(event.sponsor_logo_path).exists():
        sponsor_logo_uri = file_to_data_uri(Path(event.sponsor_logo_path))

    interests_uri = ""
    if attendee.interests_image_path and Path(attendee.interests_image_path).exists():
        interests_uri = file_to_data_uri(Path(attendee.interests_image_path))

    # Generate location graphic
    location_graphic_uri = ""
    if attendee.location:
        cache_dir = ROOT / "output" / "location_graphics"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_filename = attendee.location.replace(", ", "_").replace(" ", "_") + ".svg"
        cache_path = cache_dir / cache_filename

        # Generate if not cached
        if not cache_path.exists():
            render_location_graphic(
                location_str=attendee.location,
                output_path=cache_path,
                canvas_size=(144, 144)
            )

        # Convert to data URI
        if cache_path.exists():
            location_graphic_uri = svg_to_data_uri(cache_path)

    # Get optimized display name with smart truncation
    name_info = get_display_name(
        original_name=attendee.name,
        max_width=2.7,  # Full badge width minus margins
        font_family="Helvetica",
        default_font_size=18.0,
        min_font_size=12.0
    )

    # Render template
    template = Template(template_content)
    badge_html = template.render(
        event_name=event.display_name,
        event_date=event.date,
        sponsor=event.sponsor,
        event_logo_path=event_logo_uri,  # Use data URI
        sponsor_logo_path=sponsor_logo_uri,  # Use data URI
        name=name_info['text'],
        name_font_size=name_info['font_size'],
        title=attendee.title,
        company=attendee.company,
        location=attendee.location,
        location_graphic_path=location_graphic_uri,  # Use data URI
        tags=tags,
        tag_colors=tag_color_map,
        qr_code_data_uri=qr_code_data_uri,
        interests_image_path=interests_uri  # Use data URI
    )

    # Create full HTML page with embedded CSS and auto-refresh
    grid_overlay = ""
    if show_grid:
        grid_overlay = """
    <div class="grid-overlay" id="gridOverlay">
      <!-- Vertical lines every 0.25 inches -->
      <div class="grid-line-v" style="left: 0.25in;"></div>
      <div class="grid-line-v" style="left: 0.5in;"></div>
      <div class="grid-line-v" style="left: 0.75in;"></div>
      <div class="grid-line-v" style="left: 1in;"></div>
      <div class="grid-line-v" style="left: 1.25in;"></div>
      <div class="grid-line-v" style="left: 1.5in;"></div>
      <div class="grid-line-v" style="left: 1.75in;"></div>
      <div class="grid-line-v" style="left: 2in;"></div>
      <div class="grid-line-v" style="left: 2.25in;"></div>
      <div class="grid-line-v" style="left: 2.5in;"></div>
      <div class="grid-line-v" style="left: 2.75in;"></div>

      <!-- Horizontal lines every 0.25 inches -->
      <div class="grid-line-h" style="top: 0.25in;"></div>
      <div class="grid-line-h" style="top: 0.5in;"></div>
      <div class="grid-line-h" style="top: 0.75in;"></div>
      <div class="grid-line-h" style="top: 1in;"></div>
      <div class="grid-line-h" style="top: 1.25in;"></div>
      <div class="grid-line-h" style="top: 1.5in;"></div>
      <div class="grid-line-h" style="top: 1.75in;"></div>
      <div class="grid-line-h" style="top: 2in;"></div>
      <div class="grid-line-h" style="top: 2.25in;"></div>
      <div class="grid-line-h" style="top: 2.5in;"></div>
      <div class="grid-line-h" style="top: 2.75in;"></div>
      <div class="grid-line-h" style="top: 3in;"></div>
      <div class="grid-line-h" style="top: 3.25in;"></div>
      <div class="grid-line-h" style="top: 3.5in;"></div>
      <div class="grid-line-h" style="top: 3.75in;"></div>
    </div>
    <button class="grid-toggle" onclick="toggleGrid()">Toggle Grid</button>
    """

    # Generate timestamp for cache busting
    timestamp = datetime.now().isoformat()

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">
  <meta http-equiv="refresh" content="1">
  <!-- Cache buster: {timestamp} -->
  <title>Badge Preview - {attendee.name}</title>
  <style>
/* Generated: {timestamp} */
{css_content}

/* Preview-specific styles */
body {{
  margin: 20px;
  background: #f5f5f5;
  font-family: system-ui, -apple-system, sans-serif;
}}

.preview-container {{
  max-width: 800px;
  margin: 0 auto;
}}

.preview-info {{
  background: white;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}}

.preview-info h2 {{
  margin: 0 0 10px 0;
  font-size: 18px;
  color: #333;
}}

.preview-info p {{
  margin: 5px 0;
  color: #666;
  font-size: 14px;
}}

.badge-wrapper {{
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  display: inline-block;
  position: relative;
}}

.grid-overlay {{
  position: absolute;
  top: 20px;
  left: 20px;
  width: 3in;
  height: 4in;
  pointer-events: none;
  z-index: 9999;
}}

.grid-line-v, .grid-line-h {{
  position: absolute;
  background: rgba(255, 0, 0, 0.2);
}}

.grid-line-v {{
  width: 1px;
  height: 100%;
  top: 0;
}}

.grid-line-h {{
  height: 1px;
  width: 100%;
  left: 0;
}}

.grid-toggle {{
  position: fixed;
  bottom: 20px;
  right: 20px;
  padding: 10px 20px;
  background: #3D405B;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}}

.grid-toggle:hover {{
  background: #2d2f45;
}}

.timestamp {{
  font-size: 12px;
  color: #999;
  font-family: monospace;
}}
  </style>
  <script>
function toggleGrid() {{
  const grid = document.getElementById('gridOverlay');
  grid.style.display = grid.style.display === 'none' ? 'block' : 'none';
}}

function autoShrinkText(selector, maxFontSize = 6, minFontSize = 3) {{
  const element = document.querySelector(selector);
  if (!element || !element.textContent.trim()) return;

  let fontSize = maxFontSize;
  element.style.fontSize = fontSize + 'pt';

  // Shrink font until text fits within container width
  while (element.scrollWidth > element.clientWidth && fontSize > minFontSize) {{
    fontSize -= 0.25;
    element.style.fontSize = fontSize + 'pt';
  }}
}}

// Name truncation with cultural awareness
function autoTruncateName(selector, maxSize = 18, minSize = 12) {{
  const element = document.querySelector(selector);
  if (!element || !element.textContent.trim()) return;

  const originalName = element.textContent.trim();
  element.setAttribute('data-original-name', originalName);

  // Stage 1 & 2: Try shrinking first
  let fontSize = maxSize;
  element.style.fontSize = fontSize + 'pt';

  while (element.scrollWidth > element.clientWidth && fontSize > minSize) {{
    fontSize -= 1;
    element.style.fontSize = fontSize + 'pt';
  }}

  // Stage 3: Progressive truncation if still doesn't fit
  if (element.scrollWidth > element.clientWidth) {{
    const truncated = progressiveTruncate(originalName);
    element.textContent = truncated;
    element.setAttribute('data-truncated', 'true');
    element.setAttribute('aria-label', originalName);  // Accessibility

    // Try shrinking truncated name
    fontSize = maxSize;
    element.style.fontSize = fontSize + 'pt';
    while (element.scrollWidth > element.clientWidth && fontSize > minSize) {{
      fontSize -= 1;
      element.style.fontSize = fontSize + 'pt';
    }}
  }}
}}

function progressiveTruncate(name) {{
  const parts = name.split(' ');

  if (parts.length === 1) {{
    return parts[0];  // Single name, can't truncate
  }}

  // Stage 3.1: Remove middle names (keep first and last)
  if (parts.length > 2) {{
    return parts[0] + ' ' + parts[parts.length - 1];
  }}

  // Stage 3.2: First name + last initial
  if (parts.length === 2) {{
    return parts[0] + ' ' + parts[1][0] + '.';
  }}

  return parts[0];
}}

// Auto-shrink sponsor text on load
window.addEventListener('load', function() {{
  autoShrinkText('.sponsor', 6, 3);
  // Note: Name truncation is now handled server-side via get_display_name()
}});
  </script>
</head>
<body>
  <div class="preview-container">
    <div class="preview-info">
      <h2>📋 Badge Preview</h2>
      <p><strong>Attendee:</strong> {attendee.name}</p>
      <p><strong>Title:</strong> {attendee.title}</p>
      <p><strong>Template:</strong> Professional (3" × 4")</p>
      <p class="timestamp">Auto-refreshes every 1 second • Generated: {timestamp}</p>
    </div>

    <div class="badge-wrapper">
{badge_html}
{grid_overlay}
    </div>
  </div>

  <script>
    // Force cache clear on load
    if (window.performance && performance.navigation.type === performance.navigation.TYPE_RELOAD) {{
      location.reload(true);
    }}
  </script>
</body>
</html>"""

    # Write HTML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_html)

    return output_path


if __name__ == "__main__":
    import sys

    user_id = sys.argv[1] if len(sys.argv) > 1 else "user_007"
    output = generate_preview(user_id)
    print(f"✓ Preview generated: {output}")
    print(f"  Open in VS Code Simple Browser:")
    print(f"  file://{output.absolute()}")
