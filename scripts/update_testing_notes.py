#!/usr/bin/env python3
"""
Update testing notes to be concise and non-redundant.
Each note should provide distinct value about what edge case is being tested.
"""
from pathlib import Path
import json

ROOT = Path(__file__).parent.parent

# Revised testing notes - concise, no redundancy, each bullet provides distinct value
TESTING_NOTES = {
    "user_001": [
        "Baseline test with all common fields populated",
        "Name: 10-20 chars (typical length)",
        "3 interests (minimum recommended count)"
    ],
    "user_002": [
        "**CRITICAL** Mononym (single-word name with no space)",
        "Tests name field without surname"
    ],
    "user_003": [
        "**CRITICAL** Very short name (5 chars: 'Bo Yi')",
        "Should render at full 18pt font with no scaling"
    ],
    "user_004": [
        "**CRITICAL** Minimal badge - only name field populated",
        "All optional fields null: title, company, location, interests, social, QR",
        "Tests graceful degradation with minimal data"
    ],
    "user_005": [
        "Name: 20-40 chars (medium length)",
        "8 interests (maximum recommended count)",
        "Tests interest count upper boundary"
    ],
    "user_006": [
        "**CRITICAL** Very short values across multiple fields",
        "Title: 'CEO' (3 chars), Company: 'IBM' (3 chars)",
        "Tests minimum field length handling"
    ],
    "user_007": [
        "**CRITICAL** Apostrophe in name (O'Connor)",
        "Tests special character rendering in primary text field"
    ],
    "user_008": [
        "**CRITICAL** Invalid location (Atlantis, Lost Kingdom)",
        "Tests geocoding failure - should use original text when geocoding fails",
        "No location graphic should render"
    ],
    "user_009": [
        "**CRITICAL** Very long title (74 chars)",
        "Should wrap to 2 lines with proper overflow handling",
        "8 interests normalized from 10 original"
    ],
    "user_010": [
        "2 interests (below minimum recommended count of 3)",
        "Tests system behavior with minimal interest data"
    ],
    "user_011": [
        "Arabic patronymic naming (bin Mohammed Al-Sayed)",
        "Tests cultural name format with connecting particles"
    ],
    "user_012": [
        "**CRITICAL** Chinese characters throughout (name, company, location)",
        "Tests unicode rendering and font fallback for non-Latin scripts",
        "Eastern name order (family name first)"
    ],
    "user_013": [
        "Special characters in company: ampersand (&) and forward slash (/)",
        "Pronouns: 'she/they' format variant"
    ],
    "user_014": [
        "**CRITICAL** Diacritics in name (Björk Magnúsdóttir)",
        "Very long social handle (27 chars)",
        "Tests Latin extended characters"
    ],
    "user_015": [
        "Spanish double surname with hyphen (García-Hernández)",
        "Latin accents in first name (María José)",
        "Tests combined Latin extended + hyphenation"
    ],
    "user_016": [
        "Russian patronymic (three-part name: Anastasia Mikhailovna Kovalenko)",
        "Tests name truncation if patronymic causes overflow"
    ],
    "user_017": [
        "**CRITICAL** Extremely long title (74 chars) exceeding 2-line capacity",
        "Tests CSS line-clamp truncation with ellipsis"
    ],
    "user_018": [
        "**CRITICAL** Brand overload in raw interests (15+ trademarked brands)",
        "Tests AI normalization: brands → generic categories",
        "Examples: Nike → Running, Starbucks → Coffee, LeBron James → Basketball fan"
    ],
    "user_019": [
        "**CRITICAL** Politically sensitive interests (climate, gun policy, healthcare)",
        "Tests abstraction to neutral categories for visual generation",
        "Avoids controversial imagery while preserving user intent"
    ],
    "user_020": [
        "**CRITICAL** Extreme long name with titles (80+ chars)",
        "Academic prefix/suffix: Dr. ... PhD",
        "Tests maximum name truncation strategy"
    ],
    "user_021": [
        "Trademarked fitness brands (CrossFit, Peloton, SoulCycle)",
        "Tests normalization: CrossFit → Fitness training, Peloton → Indoor cycling"
    ],
    "user_022": [
        "Triple-hyphenated surname (Smith-Jones-Williams)",
        "Tests rendering of complex hyphenated names"
    ],
    "user_023": [
        "**CRITICAL** Extremely long location (58 chars)",
        "Welsh town: Llanfairpwllgwyngyllgogerychwyrndrobwllllantysiliogogogoch",
        "Tests location truncation with ellipsis"
    ],
    "user_024": [
        "Name with periods (J.D. Martinez)",
        "Tests period character handling in name field"
    ],
    "user_025": [
        "**CRITICAL** Extra whitespace in name ('   Skyler   Reed   ')",
        "Tests whitespace normalization (trim + collapse)",
        "Abstract/spiritual interests (Mindfulness, Personal growth)"
    ],
    "user_026": [
        "Entry-level title (Junior Software Developer)",
        "Profession-adjacent interests (coding, hackathons)",
        "Tests distinction between job role and personal interests"
    ]
}


def main():
    """Update testing notes for all attendees"""
    attendees_path = ROOT / "mocks" / "attendees.json"

    # Load current attendees
    with open(attendees_path, "r", encoding="utf-8") as f:
        attendees = json.load(f)

    # Update testing notes for each attendee
    updated_count = 0
    for attendee in attendees:
        user_id = attendee["id"]
        if user_id in TESTING_NOTES:
            old_notes = attendee.get("testing_notes", [])
            attendee["testing_notes"] = TESTING_NOTES[user_id]
            updated_count += 1
            print(f"✓ {user_id}: Updated {len(old_notes)} → {len(TESTING_NOTES[user_id])} notes")
        else:
            print(f"⚠ No testing notes defined for {user_id}")

    # Write updated attendees
    with open(attendees_path, "w", encoding="utf-8") as f:
        json.dump(attendees, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Updated {updated_count} attendees with revised testing notes")
    print(f"📄 Saved to {attendees_path}")


if __name__ == "__main__":
    main()
