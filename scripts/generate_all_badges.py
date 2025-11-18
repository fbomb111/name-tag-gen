#!/usr/bin/env python3
"""
Generate final badges for all attendees in all events.
Uses current design: smart-cropped images, location normalization, all layout improvements.
"""
from pathlib import Path
import json
import sys

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.renderers.badge_renderer_html import BadgeRendererHTML
from src.models import Event, Attendee

ROOT = Path(__file__).parent.parent

# Load data
with open(ROOT / "mocks" / "events.json", 'r') as f:
    events_data = json.load(f)
with open(ROOT / "mocks" / "attendees.json", 'r') as f:
    attendees_data = json.load(f)
with open(ROOT / "mocks" / "event_attendees.json", 'r') as f:
    event_attendees_data = json.load(f)

# Parse models
events = {e["event_id"]: Event.model_validate(e) for e in events_data}
attendees = {a["id"]: Attendee.model_validate(a) for a in attendees_data}

# Count total attendees
total_attendees = sum(len(ea_list) for ea_list in event_attendees_data.values())

print("=" * 70)
print("Generating Final Badges for All Attendees")
print("=" * 70)
print(f"Events: {len(event_attendees_data)}")
print(f"Total attendees: {total_attendees}")
print()

# Output directory
output_base = ROOT / "output" / "badges"

generated = 0
skipped = 0
errors = 0

# Iterate through all event-attendee combinations
for event_id, ea_list in sorted(event_attendees_data.items()):
    if event_id not in events:
        print(f"⊘ SKIP event {event_id} - not found in events data")
        skipped += len(ea_list)
        continue

    event = events[event_id]

    for ea in ea_list:
        user_id = ea["user_id"]
        tags = ea.get("tags", {})

        if user_id not in attendees:
            print(f"⊘ SKIP {event_id}/{user_id} - not in attendees data")
            skipped += 1
            continue

        attendee = attendees[user_id]

        try:
            # Initialize renderer
            renderer = BadgeRendererHTML(
                template_dir=ROOT / "config" / "html_templates" / "professional",
                event_id=event_id,
                event_name=event.display_name,
                event_date=event.date,
                sponsor=event.sponsor,
                event_logo_path=event.logo_path,
                sponsor_logo_path=event.sponsor_logo_path,
                tags=event.tags
            )

            # Generate badge
            output_dir = output_base / event_id
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{user_id}.pdf"

            renderer.render_badge(attendee, output_path, tags)
            print(f"✓ {event_id}/{user_id} - {attendee.name}")
            generated += 1

        except Exception as e:
            print(f"✗ ERROR: {event_id}/{user_id} - {e}")
            errors += 1

print()
print("=" * 70)
print("Summary:")
print(f"  Generated: {generated}")
print(f"  Skipped: {skipped}")
print(f"  Errors: {errors}")
print()
print(f"Badges saved to: {output_base}")
print("=" * 70)
