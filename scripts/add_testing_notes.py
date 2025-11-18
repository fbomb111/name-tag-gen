#!/usr/bin/env python3
"""
Add testing_notes to all attendees based on edge case documentation.
"""
from pathlib import Path
import json

ROOT = Path(__file__).parent.parent

# Map each user to their testing notes based on EDGE_CASES.md
TESTING_NOTES = {
    "user_001": [
        "Standard baseline user with all common fields",
        "Short name (10-20 chars)",
        "3 interests (minimum count)",
        "Standard fields: title, company, location, social media",
        "Tests basic functionality and typical use case"
    ],
    "user_002": [
        "Mononym (single name) - tests name with no space",
        "Entertainment industry professional",
        "Tests single-word name handling and rendering"
    ],
    "user_003": [
        "Very short name (5 chars: 'Bo Yi')",
        "Tests minimum name length handling",
        "Should render at full 18pt font with no truncation"
    ],
    "user_004": [
        "**CRITICAL** Minimal badge - all optional fields null",
        "Tests graceful degradation with name only",
        "No title, company, location, interests, social media, or QR code",
        "Verifies badge still renders professionally with minimal data"
    ],
    "user_005": [
        "Medium name length (20-40 chars)",
        "8 interests normalized (maximum count)",
        "Tests interest count boundary and normalization",
        "Self-employed company variant"
    ],
    "user_006": [
        "Very short title ('CEO' - 3 chars)",
        "Very short company ('IBM' - 3 chars)",
        "Very short location ('Los Angeles, CA')",
        "Tests minimum field lengths across multiple fields"
    ],
    "user_007": [
        "**CRITICAL** Apostrophe in name (O'Connor)",
        "Tests special character rendering in name field",
        "GitHub social platform",
        "Irish location variant"
    ],
    "user_008": [
        "**CRITICAL** Invalid/fabricated location (Atlantis, Lost Kingdom)",
        "Tests geocoding failure graceful handling",
        "Verifies system uses original input when geocoding fails",
        "No location graphic should be rendered"
    ],
    "user_009": [
        "Very long title (>50 chars): 'Senior Vice President of Digital Transformation & Strategy'",
        "Tests title wrapping to 2 lines",
        "8 interests normalized from 10 original",
        "Neighborhood location format (Short North, Columbus, OH)"
    ],
    "user_010": [
        "Below minimum interests (2 interests)",
        "Tests interest count below recommended minimum (3-8)",
        "Minimal interests text in raw_interests",
        "Self-employed/freelance profession"
    ],
    "user_011": [
        "Arabic naming convention (bin Mohammed Al-Sayed)",
        "Tests cultural name format - patronymic naming",
        "International location (Dubai, UAE)",
        "3 interests (minimum)"
    ],
    "user_012": [
        "**CRITICAL** Chinese characters throughout (李娜, 字节跳动, 北京)",
        "Tests unicode rendering for name, company, and location",
        "Eastern name order (family name first)",
        "Verifies font fallback for non-Latin scripts"
    ],
    "user_013": [
        "Special characters in company name (AT&T / Warner Bros.)",
        "Tests ampersand and forward slash rendering",
        "Multiple company format",
        "Pronouns: she/they variant"
    ],
    "user_014": [
        "**CRITICAL** Diacritics in name (Björk Magnúsdóttir)",
        "Very long social handle (@bjork_creative_reykjavik - 27 chars)",
        "Icelandic location and cultural context",
        "6 interests (mid-range count)"
    ],
    "user_015": [
        "Spanish double surname (García-Hernández)",
        "Latin accents (María José)",
        "Tests hyphenated last name rendering",
        "Puerto Rico location variant"
    ],
    "user_016": [
        "Russian patronymic (Anastasia Mikhailovna Kovalenko)",
        "Cyrillic location context (Moscow, Russia)",
        "Tests patronymic name truncation if needed",
        "3 interests normalized from 5 original"
    ],
    "user_017": [
        "**CRITICAL** Very long title (90+ chars) exceeding 2 lines",
        "Tests CSS line-clamp truncation at 2 lines",
        "Professional services industry",
        "4 interests (normalized)"
    ],
    "user_018": [
        "**CRITICAL** Brand overload - 15+ interests with many brands/celebrities",
        "Tests aggressive AI normalization (12 brands → 8 generic interests)",
        "Nike → Running, Starbucks → Coffee, CrossFit → Fitness training",
        "LeBron James → Basketball fan, Taylor Swift → Pop music concerts",
        "Verifies trademark/brand safety in image generation"
    ],
    "user_019": [
        "**CRITICAL** Controversial interests (political/religious content)",
        "Tests abstraction of political topics to generic categories",
        "Climate policy, gun violence, healthcare, voting rights",
        "Washington DC location (government affairs)"
    ],
    "user_020": [
        "**CRITICAL** Extreme long name with title prefix and suffix",
        "Dr. Anastasia Alexandrovna Konstantinopolous-Vanderbilt III, PhD (80+ chars)",
        "Tests maximum name truncation strategy",
        "Should abbreviate surname and possibly remove patronymic/suffix",
        "Academic title handling"
    ],
    "user_021": [
        "Trademarked fitness brands (CrossFit, Peloton, SoulCycle)",
        "Tests normalization of trademarked activity names",
        "CrossFit → Fitness training, Peloton → Indoor cycling",
        "SoulCycle → Group fitness",
        "Fitness industry professional"
    ],
    "user_022": [
        "Multiple hyphens in name (Smith-Jones-Williams)",
        "Tests hyphenated surname with 3 parts",
        "May abbreviate to Smith-J.-W. if truncation needed",
        "6 interests (mid-range)"
    ],
    "user_023": [
        "**CRITICAL** Very long location (Llanfairpwllgwyngyllgogerychwyrndrobwllllantysiliogogogoch)",
        "Tests location truncation with ellipsis",
        "Welsh town with longest name in Europe",
        "Tourism industry context"
    ],
    "user_024": [
        "Name with periods (J.D. Martinez)",
        "Tests period handling in name field",
        "Technology/analytics professional",
        "GitHub social platform variant"
    ],
    "user_025": [
        "**CRITICAL** Extra whitespace in name ('   Skyler   Reed   ')",
        "Tests whitespace normalization (trim + collapse)",
        "Abstract interests (Mindfulness, Personal growth, Minimalism)",
        "They/them pronouns variant",
        "Boulder, CO wellness industry"
    ],
    "user_026": [
        "Entry-level title (Junior Software Developer)",
        "Profession-adjacent interests (coding, hackathons)",
        "Tests distinction between professional role and personal interests",
        "Tech meetup and gaming interests",
        "GitHub social platform"
    ]
}


def main():
    """Add testing notes to attendees.json"""
    attendees_path = ROOT / "mocks" / "attendees.json"

    # Load current attendees
    with open(attendees_path, "r", encoding="utf-8") as f:
        attendees = json.load(f)

    # Add testing notes to each attendee
    updated_count = 0
    for attendee in attendees:
        user_id = attendee["id"]
        if user_id in TESTING_NOTES:
            attendee["testing_notes"] = TESTING_NOTES[user_id]
            updated_count += 1
            print(f"✓ Added testing notes to {user_id}")
        else:
            print(f"⚠ No testing notes defined for {user_id}")

    # Write updated attendees
    with open(attendees_path, "w", encoding="utf-8") as f:
        json.dump(attendees, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Updated {updated_count} attendees with testing notes")
    print(f"📄 Saved to {attendees_path}")


if __name__ == "__main__":
    main()
