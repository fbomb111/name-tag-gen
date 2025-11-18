"""
Test badge generation with location graphics.
Tests various US and international locations.
"""
from pathlib import Path
import json
from badge_renderer_html import BadgeRendererHTML
from models import EventV2, AttendeeV2, EventAttendee

ROOT = Path(__file__).parent

# Load data
with open(ROOT / "mocks" / "events.json", 'r') as f:
    events_data = json.load(f)
with open(ROOT / "mocks" / "attendees.json", 'r') as f:
    attendees_data = json.load(f)
with open(ROOT / "mocks" / "event_attendees.json", 'r') as f:
    event_attendees_data = json.load(f)

# Parse models
events = {e["event_id"]: EventV2.model_validate(e) for e in events_data}
attendees = {a["id"]: AttendeeV2.model_validate(a) for a in attendees_data}

# Use Ohio Business Meetup event
event_id = "cohatch_afterhours"
event = events[event_id]

# Initialize renderer
renderer = BadgeRendererHTML(
    template_dir=ROOT / "config" / "html_templates" / "professional",
    event_name=event.display_name,
    event_date=event.date,
    sponsor=event.sponsor,
    event_logo_path=event.logo_path,
    sponsor_logo_path=event.sponsor_logo_path,
    tag_categories=event.tag_categories
)

# Get event attendees
event_attendees = [EventAttendee.model_validate(ea)
                  for ea in event_attendees_data[event_id]]

# Test attendees with different locations
test_users = [
    "user_001",  # Columbus, Ohio (US state)
    "user_002",  # Portland, Oregon (US state)
    "user_007",  # Bangalore, India (International)
    "user_010",  # Tokyo, Japan (International)
]

output_dir = Path("output/test_badges_with_locations")
output_dir.mkdir(parents=True, exist_ok=True)

print("Testing badge generation with location graphics...")
print("=" * 70)

for user_id in test_users:
    if user_id not in attendees:
        print(f"\nSkipping {user_id} - not found in attendees")
        continue

    attendee = attendees[user_id]

    # Get tags for this attendee
    tags = {}
    for ea in event_attendees:
        if ea.user_id == user_id:
            tags = ea.tags
            break

    # Generate badge
    output_path = output_dir / f"badge_{user_id}.pdf"

    print(f"\nGenerating badge for: {attendee.name}")
    print(f"  Location: {attendee.location}")

    try:
        renderer.render_badge(attendee, output_path, tags)
        print(f"  ✓ Generated: {output_path}")
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
print("Test complete!")
print(f"\nBadges saved to: {output_dir}")
print(f"Location graphics cached in: output/location_graphics/")
