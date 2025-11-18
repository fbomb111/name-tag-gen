"""
Compare ReportLab vs HTML rendering for badges.
Generates the same badges with both renderers for side-by-side comparison.
"""
from pathlib import Path
import json

from models import EventV2, AttendeeV2, EventAttendee
from badge_renderer_json import BadgeRendererJSON
from badge_renderer_html import BadgeRendererHTML


ROOT = Path(__file__).parent


def load_json(path: Path):
    """Load and parse JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    print("=" * 60)
    print("Badge Renderer Comparison: ReportLab vs HTML")
    print("=" * 60)
    print()

    # Load data
    print("📂 Loading configuration...")
    events_data = load_json(ROOT / "mocks" / "events.json")
    attendees_data = load_json(ROOT / "mocks" / "attendees.json")
    event_attendees_data = load_json(ROOT / "mocks" / "event_attendees.json")

    # Parse models
    events = {e["event_id"]: EventV2.model_validate(e) for e in events_data}
    attendees = {a["id"]: AttendeeV2.model_validate(a) for a in attendees_data}

    # Focus on Ohio Business Meetup (has our test attendees)
    event_id = "cohatch_afterhours"
    event = events[event_id]

    print(f"   Event: {event.display_name}")
    print()

    # Load template
    template_path = ROOT / "config" / "badge_templates" / f"{event.template_id}.json"
    template = load_json(template_path)

    # Create output directories
    reportlab_dir = ROOT / "output" / "badges" / "reportlab" / event_id
    html_dir = ROOT / "output" / "badges" / "html" / event_id
    reportlab_dir.mkdir(parents=True, exist_ok=True)
    html_dir.mkdir(parents=True, exist_ok=True)

    # Initialize renderers
    print("🎨 Initializing renderers...")

    # ReportLab renderer
    reportlab_renderer = BadgeRendererJSON(
        template=template,
        event_name=event.display_name,
        event_date=event.date or "",
        sponsor=event.sponsor or "",
        event_logo_path=event.logo_path,
        sponsor_logo_path=event.sponsor_logo_path,
        tag_categories=event.tag_categories
    )

    # HTML renderer
    html_template_dir = ROOT / "config" / "html_templates" / "professional"
    html_renderer = BadgeRendererHTML(
        template_dir=html_template_dir,
        event_name=event.display_name,
        event_date=event.date or "",
        sponsor=event.sponsor or "",
        event_logo_path=event.logo_path,
        sponsor_logo_path=event.sponsor_logo_path,
        tag_categories=event.tag_categories
    )

    print("   ✓ ReportLab renderer ready")
    print("   ✓ HTML renderer ready")
    print()

    # Get event attendees
    event_attendees = [EventAttendee.model_validate(ea)
                      for ea in event_attendees_data[event_id]]

    # Focus on test attendees with long names (user_007 through user_011)
    test_user_ids = ["user_007", "user_008", "user_009", "user_010", "user_011"]

    print("🔄 Generating comparison badges for test attendees with long names...")
    print()

    generated_count = 0
    for event_attendee in event_attendees:
        user_id = event_attendee.user_id

        # Skip if not a test user
        if user_id not in test_user_ids:
            continue

        if user_id not in attendees:
            continue

        attendee = attendees[user_id]
        tags = event_attendee.tags

        # Generate with ReportLab
        reportlab_output = reportlab_dir / f"{user_id}.pdf"
        reportlab_renderer.render_badge(attendee, reportlab_output, tags)

        # Generate with HTML
        html_output = html_dir / f"{user_id}.pdf"
        html_renderer.render_badge(attendee, html_output, tags)

        generated_count += 1
        print(f"   ✔ {attendee.name}")
        print(f"      Title: {attendee.title}")
        print(f"      ReportLab → {reportlab_output.relative_to(ROOT)}")
        print(f"      HTML      → {html_output.relative_to(ROOT)}")
        print()

    print("=" * 60)
    print(f"✅ Generated {generated_count} badge comparison(s)")
    print()
    print("📁 Output directories:")
    print(f"   ReportLab: {reportlab_dir.relative_to(ROOT)}")
    print(f"   HTML:      {html_dir.relative_to(ROOT)}")
    print()
    print("🔍 Compare the PDFs to evaluate:")
    print("   • Text wrapping quality (especially long names and titles)")
    print("   • Print quality and sharpness")
    print("   • Layout precision")
    print("   • Overall appearance")
    print("=" * 60)


if __name__ == "__main__":
    main()
