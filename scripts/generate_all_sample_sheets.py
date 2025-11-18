#!/usr/bin/env python3
"""
Generate ALL sample sheet PDFs and combine them into a single PDF for distribution.

Output:
- Individual PDFs in output/sample_sheets/all/
- Combined PDF at output/sample_sheets/ALL_SAMPLES_COMBINED.pdf
"""
from pathlib import Path
import json
import sys
from pypdf import PdfWriter

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.renderers.sample_sheet_renderer import SampleSheetRenderer
from src.renderers.badge_renderer_html import BadgeRendererHTML
from src.models import Event, Attendee, EventAttendee

ROOT = Path(__file__).parent.parent


def load_events() -> dict[str, Event]:
    """Load events from JSON."""
    events_path = ROOT / "mocks" / "events.json"
    with open(events_path, "r", encoding="utf-8") as f:
        events_data = json.load(f)
    return {evt["event_id"]: Event.model_validate(evt) for evt in events_data}


def load_attendees() -> dict[str, Attendee]:
    """Load attendees from JSON."""
    attendees_path = ROOT / "mocks" / "attendees.json"
    with open(attendees_path, "r", encoding="utf-8") as f:
        attendees_data = json.load(f)
    return {a["id"]: Attendee.model_validate(a) for a in attendees_data}


def load_event_attendees() -> dict[str, list[dict]]:
    """Load event-attendee mapping from JSON."""
    mapping_path = ROOT / "mocks" / "event_attendees.json"
    with open(mapping_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    """Generate all sample sheets and combine into one PDF."""
    print("=" * 70)
    print("ALL Sample Sheets Generator + PDF Combiner")
    print("=" * 70)
    print()

    # Load data
    events = load_events()
    attendees = load_attendees()
    event_attendees = load_event_attendees()

    # Output directory - flat structure
    output_dir = ROOT / "output" / "sample_sheets" / "all"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Statistics
    generated = 0
    errors = 0
    generated_paths = []

    # Iterate through event-attendee combinations
    for event_id, ea_list in sorted(event_attendees.items()):
        if event_id not in events:
            print(f"⊘ SKIP event {event_id} - not found in events data")
            continue

        event = events[event_id]

        for ea_dict in ea_list:
            user_id = ea_dict["user_id"]

            if user_id not in attendees:
                print(f"⊘ SKIP {event_id}/{user_id} - not in attendees data")
                continue

            attendee = attendees[user_id]
            event_attendee = EventAttendee.model_validate(ea_dict)

            try:
                # Initialize badge renderer
                badge_renderer = BadgeRendererHTML(
                    template_dir=ROOT / "config" / "html_templates" / "professional",
                    event_id=event_id,
                    event_name=event.display_name,
                    event_date=event.date,
                    sponsor=event.sponsor,
                    event_logo_path=event.logo_path,
                    sponsor_logo_path=event.sponsor_logo_path,
                    tags=event.tags
                )

                # Generate badge PDF first
                badge_output_dir = ROOT / "output" / "badges" / event_id
                badge_output_dir.mkdir(parents=True, exist_ok=True)
                badge_pdf_path = badge_output_dir / f"{user_id}_badge.pdf"

                badge_renderer.render_badge(
                    attendee=attendee,
                    output_path=badge_pdf_path,
                    tags=event_attendee.tags
                )

                # Initialize sample sheet renderer
                sample_sheet_renderer = SampleSheetRenderer()

                # Generate sample sheet PDF - flat naming scheme
                output_filename = f"{event_id}_{user_id}_sample.pdf"
                output_path = output_dir / output_filename

                sample_sheet_renderer.render(
                    event=event,
                    attendee=attendee,
                    event_attendee=event_attendee,
                    badge_pdf_path=badge_pdf_path,
                    output_path=output_path
                )

                print(f"✓ {event_id}/{user_id} - {attendee.name}")
                generated += 1
                generated_paths.append(output_path)

            except Exception as e:
                print(f"✗ ERROR: {event_id}/{user_id} - {e}")
                import traceback
                traceback.print_exc()
                errors += 1

    print()
    print("=" * 70)
    print(f"Generated {generated} individual sample sheets")
    print()

    # Combine all PDFs into one
    if generated_paths:
        print("Combining all PDFs into one master file...")
        combined_path = ROOT / "output" / "sample_sheets" / "ALL_SAMPLES_COMBINED.pdf"

        merger = PdfWriter()

        for pdf_path in sorted(generated_paths):
            merger.append(str(pdf_path))

        merger.write(str(combined_path))
        merger.close()

        print(f"✓ Combined PDF created: {combined_path}")
        print(f"   Total pages: {len(generated_paths)}")

    print()
    print("=" * 70)
    print("Summary:")
    print(f"  Generated: {generated}")
    print(f"  Errors: {errors}")
    print()
    print(f"Individual PDFs: {output_dir}")
    if generated_paths:
        print(f"Combined PDF: {combined_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
