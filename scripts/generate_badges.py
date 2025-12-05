#!/usr/bin/env python3
"""
Generate sample badges using AI-image-based system.
Creates badges for attendees across multiple events with AI-generated images.
"""
from pathlib import Path
import json
import sys

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import Event, Attendee, EventAttendee
from src.renderers.badge_renderer_json import BadgeRendererJSON
from src.utils.paths import get_badges_dir, get_working_dir, get_config_dir, get_mocks_dir

BADGES_DIR = get_badges_dir()
WORKING_DIR = get_working_dir()


def load_template(template_id: str) -> dict:
    """Load a template from JSON file."""
    template_path = get_config_dir() / "badge_templates" / f"{template_id}.json"
    with open(template_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_events() -> dict[str, Event]:
    """Load events from JSON."""
    events_path = get_mocks_dir() / "events.json"
    with open(events_path, "r", encoding="utf-8") as f:
        events_data = json.load(f)
    return {evt["event_id"]: Event.model_validate(evt) for evt in events_data}


def load_attendees() -> list[Attendee]:
    """Load attendees from JSON."""
    attendees_path = get_mocks_dir() / "attendees.json"
    with open(attendees_path, "r", encoding="utf-8") as f:
        attendees_data = json.load(f)
    return [Attendee.model_validate(a) for a in attendees_data]


def load_event_mapping() -> dict[str, list[EventAttendee]]:
    """Load mapping of event_id -> [EventAttendee objects]."""
    mapping_path = get_mocks_dir() / "event_attendees.json"
    with open(mapping_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {
        event_id: [EventAttendee.model_validate(ea) for ea in attendee_list]
        for event_id, attendee_list in data.items()
    }


def main():
    """Generate all sample badges."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate badges for events")
    parser.add_argument("--event", help="Filter to specific event_id (e.g., cohatch_afterhours)")
    args = parser.parse_args()

    print("=" * 60)
    print("Badge Generator - AI Image-Based System")
    print("=" * 60)

    # Load data
    print("\n📂 Loading configuration...")
    events = load_events()
    attendees = load_attendees()
    event_mapping = load_event_mapping()
    templates = {}

    # Create lookup for attendees by ID
    attendees_by_id = {a.id: a for a in attendees}

    print(f"   Loaded {len(events)} events")
    print(f"   Loaded {len(attendees)} attendees")

    # Filter events if specified
    if args.event:
        print(f"   Filtering to event: {args.event}")

    # Generate badges
    print("\n🎨 Generating badges...")
    generated = 0
    generated_files = []

    for event_id, event_attendees in event_mapping.items():
        # Skip if filtering to specific event
        if args.event and event_id != args.event:
            continue

        if event_id not in events:
            print(f"   ⚠ Unknown event: {event_id}")
            continue

        event = events[event_id]

        for event_attendee in event_attendees:
            attendee_id = event_attendee.user_id
            if attendee_id not in attendees_by_id:
                print(f"   ⚠ Unknown attendee: {attendee_id}")
                continue

            attendee = attendees_by_id[attendee_id]

            # Override image paths to use new working directory structure
            interests_img_path = WORKING_DIR / event.event_id / attendee.id / "generated_images" / "interests_illustration.png"

            # Create a copy of the attendee with updated image path
            attendee_copy = attendee.model_copy()
            if interests_img_path.exists():
                attendee_copy.interests_image_path = str(interests_img_path)

            # Load template if not cached
            if event.template_id not in templates:
                templates[event.template_id] = load_template(event.template_id)

            template = templates[event.template_id]

            # Create renderer with tag_categories from event
            renderer = BadgeRendererJSON(
                template=template,
                event_name=event.display_name,
                event_date=event.date or "",
                sponsor=event.sponsor or "",
                event_logo_path=event.logo_path,
                sponsor_logo_path=event.sponsor_logo_path,
                tag_categories=event.tag_categories
            )

            # Create event-specific output directory
            event_badges_dir = BADGES_DIR / event.event_id
            event_badges_dir.mkdir(parents=True, exist_ok=True)

            # Generate badge with user_id filename, passing event-specific tags
            output_path = event_badges_dir / f"{attendee.id}.pdf"
            try:
                renderer.render_badge(attendee_copy, output_path, tags=event_attendee.tags)
                print(f"   ✔ {attendee.name} → {output_path.relative_to(BADGES_DIR)}")
                generated += 1
                generated_files.append(output_path)
            except Exception as e:
                print(f"   ✖ {attendee.name}: {e}")

    # Summary
    print("\n" + "=" * 60)
    print(f"✅ Generated {generated} badge(s)")
    print(f"📁 Output directory: {BADGES_DIR}")
    print("=" * 60)

    # List generated files grouped by event
    if generated_files:
        print("\nGenerated files:")
        for pdf_file in sorted(generated_files):
            size_kb = pdf_file.stat().st_size / 1024
            print(f"   • {pdf_file.relative_to(BADGES_DIR)} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
