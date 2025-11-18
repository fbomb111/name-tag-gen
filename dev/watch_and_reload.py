#!/usr/bin/env python3
"""
Hot-reload badge generator - watches template files and regenerates badges on changes.
"""
import sys
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

ROOT = Path(__file__).resolve().parent


class TemplateChangeHandler(FileSystemEventHandler):
    """Handler for template file changes."""

    def __init__(self, badge_id: str):
        self.badge_id = badge_id
        self.last_regenerate = 0
        self.debounce_seconds = 0.5  # Prevent multiple rapid regenerations

    def on_modified(self, event):
        """Trigger badge regeneration when template is modified."""
        if event.is_directory:
            return

        # Only react to JSON template changes
        if not event.src_path.endswith('.json'):
            return

        # Debounce - ignore if we just regenerated
        current_time = time.time()
        if current_time - self.last_regenerate < self.debounce_seconds:
            return

        self.last_regenerate = current_time

        print(f"\n{'='*70}")
        print(f"📝 Template changed: {Path(event.src_path).name}")
        print(f"🔄 Regenerating badge: {self.badge_id}")
        print(f"{'='*70}\n")

        # Regenerate just the specific badge using Python directly
        try:
            # Import and run the badge generation for just this one badge
            import json
            from models import EventV2, AttendeeV2, EventAttendee
            from badge_renderer_json import BadgeRendererJSON

            # Parse badge_id to get event and attendee
            # Format: {event_id}_{attendee_id}
            parts = self.badge_id.split('_', 2)  # Split on first 2 underscores
            if len(parts) < 3:
                print(f"❌ Invalid badge_id format: {self.badge_id}")
                return

            event_id = f"{parts[0]}_{parts[1]}"  # e.g., "neighborhood_gathering"
            attendee_id = parts[2]  # e.g., "user_003"

            # Load data
            events_path = ROOT / "mocks" / "events.json"
            attendees_path = ROOT / "mocks" / "attendees.json"
            event_attendees_path = ROOT / "mocks" / "event_attendees.json"

            with open(events_path) as f:
                events_data = json.load(f)
            with open(attendees_path) as f:
                attendees_data = json.load(f)
            with open(event_attendees_path) as f:
                event_attendees_data = json.load(f)

            # Find the specific event and attendee
            event = None
            for evt_data in events_data:
                if evt_data["event_id"] == event_id:
                    event = EventV2.model_validate(evt_data)
                    break

            attendee = None
            for att_data in attendees_data:
                if att_data["id"] == attendee_id:
                    attendee = AttendeeV2.model_validate(att_data)
                    break

            if not event or not attendee:
                print(f"❌ Could not find event or attendee for: {self.badge_id}")
                return

            # Find event-specific tags for this attendee
            tags = {}
            if event_id in event_attendees_data:
                for ea_data in event_attendees_data[event_id]:
                    if ea_data.get("user_id") == attendee_id:
                        tags = ea_data.get("tags", {})
                        break

            # Override image paths to use new working directory structure
            working_dir = ROOT / "output" / "working"
            interests_img_path = working_dir / event_id / attendee_id / "generated_images" / "interests_illustration.png"

            # Create a copy of the attendee with updated image path
            attendee_copy = attendee.model_copy()
            if interests_img_path.exists():
                attendee_copy.interests_image_path = str(interests_img_path)

            # Load template
            template_path = ROOT / "config" / "badge_templates" / f"{event.template_id}.json"
            with open(template_path) as f:
                template = json.load(f)

            # Generate badge with tag_categories from event
            renderer = BadgeRendererJSON(
                template=template,
                event_name=event.display_name,
                event_date=event.date or "",
                sponsor=event.sponsor or "",
                event_logo_path=event.logo_path,
                sponsor_logo_path=event.sponsor_logo_path,
                tag_categories=event.tag_categories
            )

            # Use new badges directory structure
            event_badges_dir = ROOT / "output" / "badges" / event_id
            event_badges_dir.mkdir(parents=True, exist_ok=True)
            output_path = event_badges_dir / f"{attendee_id}.pdf"
            renderer.render_badge(attendee_copy, output_path, tags=tags)

            print(f"✅ Badge regenerated: {output_path.name}")

        except Exception as e:
            print(f"❌ Error regenerating badge: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Watch template files and regenerate badge on changes."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Watch badge template and auto-regenerate on changes"
    )
    parser.add_argument(
        "badge_id",
        help="Badge ID to watch (e.g., 'neighborhood_gathering_user_003')"
    )
    args = parser.parse_args()

    badge_id = args.badge_id
    template_dir = ROOT / "config" / "badge_templates"

    if not template_dir.exists():
        print(f"❌ Template directory not found: {template_dir}")
        return

    print("="*70)
    print("🔥 Hot Reload Badge Generator")
    print("="*70)
    print(f"Watching: {template_dir}")
    print(f"Badge ID: {badge_id}")
    print(f"\nMake changes to any .json template file to trigger regeneration.")
    print(f"Press Ctrl+C to stop.\n")
    print("="*70)

    # Initial generation - just the specific badge
    print("\n🚀 Generating initial badge...\n")

    # Trigger initial generation using the event handler
    handler = TemplateChangeHandler(badge_id)

    # Find which template file to use based on badge_id
    parts = badge_id.split('_', 2)
    if len(parts) >= 3:
        event_id = f"{parts[0]}_{parts[1]}"

        # Load event to get template_id
        import json
        events_path = ROOT / "mocks" / "events.json"
        with open(events_path) as f:
            events_data = json.load(f)

        for evt in events_data:
            if evt["event_id"] == event_id:
                template_id = evt.get("template_id", "casual_template")
                print(f"Using template: {template_id}.json")
                break

    # Do initial generation by simulating a file change
    class FakeEvent:
        def __init__(self, path):
            self.src_path = str(path)
            self.is_directory = False

    template_path = template_dir / f"{template_id}.json"
    handler.on_modified(FakeEvent(template_path))

    # Set up file watcher
    event_handler = TemplateChangeHandler(badge_id)
    observer = Observer()
    observer.schedule(event_handler, str(template_dir), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Stopping hot reload...")
        observer.stop()

    observer.join()
    print("✅ Done!")


if __name__ == "__main__":
    main()
