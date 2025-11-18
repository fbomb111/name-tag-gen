#!/usr/bin/env python3
"""
Generate sample sheet PDFs showing input data alongside rendered badges.

Each sample sheet displays:
- Left column: All form data in human-readable key:value format
- Right column: Rendered 3"×4" badge as it will appear when printed

Output: 8.5"×11" landscape PDFs in output/sample_sheets/{event_id}/{user_id}_sample.pdf
"""
from pathlib import Path
import json
import sys
import argparse

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
    """Generate sample sheets for all or filtered attendees."""
    parser = argparse.ArgumentParser(
        description="Generate sample sheet PDFs showing input data + rendered badge"
    )
    parser.add_argument(
        "--event",
        help="Filter to specific event_id (e.g., cohatch_afterhours)"
    )
    parser.add_argument(
        "--user",
        help="Filter to specific user_id (e.g., user_001)"
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Sample Sheet Generator")
    print("=" * 70)
    if args.event:
        print(f"Event filter: {args.event}")
    if args.user:
        print(f"User filter: {args.user}")
    print()

    # Load data
    events = load_events()
    attendees = load_attendees()
    event_attendees = load_event_attendees()

    # Output directory
    output_base = ROOT / "output" / "sample_sheets"

    # Statistics
    generated = 0
    skipped = 0
    errors = 0

    # Iterate through event-attendee combinations
    for event_id, ea_list in sorted(event_attendees.items()):
        # Apply event filter
        if args.event and event_id != args.event:
            continue

        if event_id not in events:
            print(f"⊘ SKIP event {event_id} - not found in events data")
            skipped += len(ea_list)
            continue

        event = events[event_id]

        for ea_dict in ea_list:
            user_id = ea_dict["user_id"]

            # Apply user filter
            if args.user and user_id != args.user:
                continue

            if user_id not in attendees:
                print(f"⊘ SKIP {event_id}/{user_id} - not in attendees data")
                skipped += 1
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

                # Generate sample sheet PDF using the badge PDF
                output_dir = output_base / event_id
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / f"{user_id}_sample.pdf"

                sample_sheet_renderer.render(
                    event=event,
                    attendee=attendee,
                    event_attendee=event_attendee,
                    badge_pdf_path=badge_pdf_path,
                    output_path=output_path
                )

                print(f"✓ {event_id}/{user_id} - {attendee.name}")
                generated += 1

            except Exception as e:
                print(f"✗ ERROR: {event_id}/{user_id} - {e}")
                import traceback
                traceback.print_exc()
                errors += 1

    print()
    print("=" * 70)
    print("Summary:")
    print(f"  Generated: {generated}")
    print(f"  Skipped: {skipped}")
    print(f"  Errors: {errors}")
    print()
    print(f"Sample sheets saved to: {output_base}")
    print("=" * 70)


if __name__ == "__main__":
    main()
