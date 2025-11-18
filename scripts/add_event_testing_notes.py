#!/usr/bin/env python3
"""
Add testing_notes to all events based on edge case documentation.
"""
from pathlib import Path
import json

ROOT = Path(__file__).parent.parent

# Map each event to their testing notes based on EDGE_CASES.md Section 8 (Event Edge Cases)
TESTING_NOTES = {
    "cohatch_afterhours": [
        "Standard baseline event with all common fields",
        "5 tag categories (moderate complexity)",
        "Mix of select and write_in tag types",
        "Mix of standard and micro display types",
        "Event logo but no sponsor logo",
        "Tests typical real-world event configuration"
    ],
    "short_name_event": [
        "**CRITICAL** Very short event name (3 chars: 'BBQ')",
        "Tests minimum event name length handling",
        "Minimal tag configuration (1 category only)",
        "No sponsor text (graceful null handling)",
        "Tests event name rendering at small sizes"
    ],
    "long_name_event": [
        "**CRITICAL** Very long event name (80+ chars)",
        "Very long sponsor text (50+ chars)",
        "Tests event name truncation/wrapping in header",
        "Tests sponsor text truncation if needed",
        "2 tag categories (minimal multi-category setup)",
        "Date format variation: 'September 20-22, 2025'"
    ],
    "tag_overload": [
        "**CRITICAL** Tag overflow - 8 tag categories",
        "Tests maximum tag count rendering",
        "Tests tag wrapping/overflow behavior on badge",
        "Tests UI/UX when many tags assigned to single attendee",
        "No sponsor (null handling)",
        "Mix of select and write_in types across many categories"
    ],
    "sponsored_event": [
        "**CRITICAL** Both event logo AND sponsor logo present",
        "Tests dual logo rendering and layout",
        "Tests sponsor logo positioning and scaling",
        "3 tag categories (mid-range complexity)",
        "Mix of select and write_in tag types",
        "Healthcare industry context"
    ],
    "minimal_event": [
        "**CRITICAL** Minimal event - all optional fields null",
        "Tests graceful degradation with minimal event data",
        "No date (null handling)",
        "No sponsor (null handling)",
        "No event logo (null handling)",
        "No sponsor logo (null handling)",
        "No tags (empty array handling)",
        "Verifies badges still render with minimal event configuration"
    ]
}


def main():
    """Add testing notes to events.json"""
    events_path = ROOT / "mocks" / "events.json"

    # Load current events
    with open(events_path, "r", encoding="utf-8") as f:
        events = json.load(f)

    # Add testing notes to each event
    updated_count = 0
    for event in events:
        event_id = event["event_id"]
        if event_id in TESTING_NOTES:
            event["testing_notes"] = TESTING_NOTES[event_id]
            updated_count += 1
            print(f"✓ Added testing notes to {event_id}")
        else:
            print(f"⚠ No testing notes defined for {event_id}")

    # Write updated events
    with open(events_path, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Updated {updated_count} events with testing notes")
    print(f"📄 Saved to {events_path}")


if __name__ == "__main__":
    main()
