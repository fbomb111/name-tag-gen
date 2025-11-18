#!/usr/bin/env python3
"""
Remove profession and industry fields from all attendees.
These fields should only appear as event-specific tags if needed.
"""
from pathlib import Path
import json

ROOT = Path(__file__).parent.parent


def main():
    """Remove profession and industry from attendees.json"""
    attendees_path = ROOT / "mocks" / "attendees.json"

    # Load current attendees
    with open(attendees_path, "r", encoding="utf-8") as f:
        attendees = json.load(f)

    # Remove profession and industry from each attendee
    updated_count = 0
    for attendee in attendees:
        removed_fields = []

        if "profession" in attendee:
            del attendee["profession"]
            removed_fields.append("profession")

        if "industry" in attendee:
            del attendee["industry"]
            removed_fields.append("industry")

        if removed_fields:
            updated_count += 1
            print(f"✓ {attendee['id']}: Removed {', '.join(removed_fields)}")

    # Write updated attendees
    with open(attendees_path, "w", encoding="utf-8") as f:
        json.dump(attendees, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Updated {updated_count} attendees")
    print(f"📄 Saved to {attendees_path}")


if __name__ == "__main__":
    main()
