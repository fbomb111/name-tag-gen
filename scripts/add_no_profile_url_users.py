#!/usr/bin/env python3
"""
Set profile_url to null for selected users to test optional QR code edge case.
Updates testing notes to document this edge case.
"""
from pathlib import Path
import json

ROOT = Path(__file__).parent.parent

# Users to set profile_url to null
USERS_WITHOUT_PROFILE = {
    "user_004": {
        # Already has null profile_url, just update notes
        "note": "No QR code (profile_url is null)"
    },
    "user_010": {
        # Morgan Blake - minimal interests user
        "note": "No QR code (profile_url is null)"
    },
    "user_006": {
        # Raj Patel - very short values
        "note": "No QR code despite otherwise complete data"
    },
    "user_023": {
        # Dylan Hughes - extremely long location
        "note": "No QR code (tests layout without QR)"
    }
}


def main():
    """Set profile_url to null for selected users"""
    attendees_path = ROOT / "mocks" / "attendees.json"

    # Load current attendees
    with open(attendees_path, "r", encoding="utf-8") as f:
        attendees = json.load(f)

    # Update profile_url and testing notes for each selected user
    updated_count = 0
    for attendee in attendees:
        user_id = attendee["id"]
        if user_id in USERS_WITHOUT_PROFILE:
            # Set profile_url to null
            old_url = attendee.get("profile_url")
            attendee["profile_url"] = None

            # Add note to testing_notes if not already present
            note = USERS_WITHOUT_PROFILE[user_id]["note"]
            if "testing_notes" in attendee:
                if note not in attendee["testing_notes"]:
                    attendee["testing_notes"].append(note)
            else:
                attendee["testing_notes"] = [note]

            updated_count += 1
            print(f"✓ {user_id}: profile_url '{old_url}' → null, added note")

    # Write updated attendees
    with open(attendees_path, "w", encoding="utf-8") as f:
        json.dump(attendees, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Updated {updated_count} users to have no profile_url")
    print(f"📄 Saved to {attendees_path}")


if __name__ == "__main__":
    main()
