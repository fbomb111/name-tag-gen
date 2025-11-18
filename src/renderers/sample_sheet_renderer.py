#!/usr/bin/env python3
"""
Sample Sheet Renderer - Generates demonstration PDFs showing input data alongside rendered badges.

This renderer creates 8.5"x11" landscape PDFs with a two-column layout:
- Left column: All form data in human-readable key:value format
- Right column: Rendered 3"x4" badge centered

Used for showing clients/stakeholders sample input → sample output.
"""
from pathlib import Path
from typing import Optional
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from datetime import datetime
import base64
from pdf2image import convert_from_path
import io

from ..models import Event, Attendee, EventAttendee


class SampleSheetRenderer:
    """Generates sample sheet PDFs combining form data display with rendered badge."""

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize renderer with template directory.

        Args:
            template_dir: Path to sample_sheet template directory.
                         Defaults to config/html_templates/sample_sheet/
        """
        if template_dir is None:
            root = Path(__file__).resolve().parent.parent.parent
            template_dir = root / "config" / "html_templates" / "sample_sheet"

        self.template_dir = template_dir
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))

    def render(
        self,
        event: Event,
        attendee: Attendee,
        event_attendee: EventAttendee,
        badge_pdf_path: Path,
        output_path: Path
    ) -> None:
        """
        Render a sample sheet PDF showing input data and rendered badge.

        Args:
            event: Event object with event details
            attendee: Attendee object with personal information
            event_attendee: EventAttendee object with event-specific assignments (tags)
            badge_pdf_path: Path to the pre-rendered badge PDF
            output_path: Path where PDF should be saved
        """
        # Convert badge PDF to image
        badge_image_data = self._pdf_to_base64_image(badge_pdf_path)

        # Format data for display
        form_data = self._format_form_data(event, attendee, event_attendee)

        # Load and render template
        template = self.env.get_template("template.html")
        html_content = template.render(
            event=event,
            attendee=attendee,
            form_data=form_data,
            badge_image_data=badge_image_data,
            generation_date=datetime.now().strftime("%B %d, %Y at %I:%M %p")
        )

        # Generate PDF
        output_path.parent.mkdir(parents=True, exist_ok=True)

        css_path = self.template_dir / "styles.css"
        HTML(string=html_content).write_pdf(
            output_path,
            stylesheets=[CSS(filename=str(css_path))]
        )

    def _pdf_to_base64_image(self, pdf_path: Path, dpi: int = 300) -> str:
        """
        Convert a PDF to a base64-encoded PNG image.

        Args:
            pdf_path: Path to the PDF file
            dpi: DPI for the output image (default 300 for print quality)

        Returns:
            Base64-encoded PNG image data as a data URI string
        """
        # Convert PDF to PIL Image
        images = convert_from_path(pdf_path, dpi=dpi)

        # Use the first page (badges are single-page)
        image = images[0]

        # Convert to PNG bytes
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)

        # Encode as base64
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')

        # Return as data URI
        return f"data:image/png;base64,{image_base64}"

    def _format_form_data(
        self,
        event: Event,
        attendee: Attendee,
        event_attendee: EventAttendee
    ) -> dict:
        """
        Format all data into human-readable sections.

        Returns dict with sections:
        - event_info: Event details
        - attendee_info: Name, title, company, location, pronouns, social, profile URL
        - interests: List of interests (normalized version shown on badge)
        - assignments: Tag assignments with colors

        All fields display "None" if not provided (per user requirement).
        """
        # Helper to format optional values
        def fmt(value, default="None"):
            if value is None or value == "":
                return default
            if isinstance(value, list):
                return ", ".join(value) if value else "None"
            return str(value)

        # Event information
        event_info = {
            "Event Name": fmt(event.display_name),
            "Event Date": fmt(event.date),
            "Event ID": fmt(event.event_id),
            "Sponsor": fmt(event.sponsor),
            "Template": fmt(event.template_id)
        }

        # Attendee information (all personal and professional fields)
        attendee_info = {
            "Full Name": fmt(attendee.name),
            "Job Title": fmt(attendee.title),
            "Company": fmt(attendee.company),
            "Location": fmt(attendee.location),
            "Pronouns": fmt(attendee.pronouns),
            "Profile URL (QR code)": fmt(attendee.profile_url),
            "Social Platform": fmt(attendee.preferred_social_platform),
            "Social Handle": fmt(attendee.social_handle)
        }

        # Interests - show raw input, parsed list, and normalized version
        interests_section = {
            "Raw interests (original user input)": fmt(attendee.raw_interests),
            "Parsed interests (structured list)": fmt(attendee.interests),
            "Normalized interests (displayed on badge)": fmt(attendee.interests_normalized) if attendee.interests_normalized else fmt(attendee.interests)
        }

        # Event-specific assignments (tags)
        # Load event tag categories to get colors and display names
        assignments = []
        if event_attendee.tags:
            for tag_name, tag_value in event_attendee.tags.items():
                # Find matching tag category in event configuration
                event_tag_category = next((t for t in event.tags if t.name == tag_name), None)

                if event_tag_category:
                    display_name = event_tag_category.name  # TagCategory uses 'name', not 'display_name'
                    color = event_tag_category.color or "#E07A5F"
                    display_type = event_tag_category.display_type or "standard"

                    assignments.append({
                        "field": display_name,
                        "value": fmt(tag_value),
                        "color": color,
                        "display_type": display_type
                    })

        # If no assignments, show placeholder
        if not assignments:
            assignments.append({
                "field": "No event-specific assignments",
                "value": "None",
                "color": "#9CA3AF",
                "display_type": "tag"
            })

        return {
            "event_info": event_info,
            "attendee_info": attendee_info,
            "interests": interests_section,
            "assignments": assignments,
            "testing_notes": attendee.testing_notes  # Optional field for documenting test cases
        }
