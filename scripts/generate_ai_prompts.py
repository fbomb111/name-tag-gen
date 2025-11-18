#!/usr/bin/env python3
"""
Generate AI image prompts for all attendees.
Outputs structured prompts that can be used to create professional visuals and interest illustrations.
"""
from pathlib import Path
import json
import sys

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import Event, Attendee, EventAttendee

ROOT = Path(__file__).resolve().parent.parent
WORKING_DIR = ROOT / "output" / "working"


def load_template(template_id: str) -> dict:
    """Load a template from JSON file."""
    template_path = ROOT / "config" / "badge_templates" / f"{template_id}.json"
    with open(template_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_events() -> dict[str, Event]:
    """Load events from JSON."""
    events_path = ROOT / "mocks" / "events.json"
    with open(events_path, "r", encoding="utf-8") as f:
        events_data = json.load(f)
    return {evt["event_id"]: Event.model_validate(evt) for evt in events_data}


def load_attendees() -> list[Attendee]:
    """Load attendees from JSON."""
    attendees_path = ROOT / "mocks" / "attendees.json"
    with open(attendees_path, "r", encoding="utf-8") as f:
        attendees_data = json.load(f)
    return [Attendee.model_validate(a) for a in attendees_data]


def load_event_mapping() -> dict[str, list[EventAttendee]]:
    """Load mapping of event_id -> [EventAttendee objects]."""
    mapping_path = ROOT / "mocks" / "event_attendees.json"
    with open(mapping_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {
        event_id: [EventAttendee.model_validate(ea) for ea in attendee_list]
        for event_id, attendee_list in data.items()
    }


def generate_professional_visual_prompt(attendee: Attendee, template: dict) -> str:
    """Generate prompt for professional visual (square image) matching template."""
    color_palette = template.get("colorPalette", {})

    # Format color palette as descriptive string
    color_names = {
        # Professional template colors
        "warmOrange": "warm oranges",
        "teal": "teals",
        "navyBlue": "navy blues",
        "goldenYellow": "golden yellow",
        "cream": "cream",
        # Casual template colors
        "coral": "coral reds",
        "skyBlue": "bright sky blue",
        "lavender": "rich lavender purple",
        "peach": "soft peach",
        "mintCream": "mint cream"
    }
    color_parts = []
    for key, hex_val in color_palette.items():
        display_name = color_names.get(key, key)
        color_parts.append(f"{display_name} ({hex_val})")
    color_palette_str = ", ".join(color_parts)

    # Extract data
    profession_title = attendee.profession or attendee.title or "professional"
    company_name = attendee.company or "their company"
    industry_context = attendee.industry or "business"

    prompt = f"""Create a square visual element (aspect ratio 1:1) in a modern flat illustration style that represents a specific profession AND industry context through creative imagery that blends both elements.

The design will be programmatically extended with additional background space, so ensure a clean, solid background color that can be easily matched and extended.

CRITICAL: Do NOT include any depictions of people or human figures. Do NOT include any text, letters, numbers, or words in the image.

Layout specifications:
- Format: Square, 1:1 aspect ratio
- Composition: Balanced illustration that clearly shows BOTH the profession and the industry/company context through objects, tools, symbols, and scenes only
- Background: Solid, flat color with NO gradients or texture - this is critical for seamless extension
- Visual placement: Imagery should work well when additional space is added to the left side

Visual guidelines:
- Style: Contemporary flat illustration with slight depth through layering or subtle shadows
- Color palette: {color_palette_str} - use 3-4 colors harmoniously
- Profession + Industry representation: This is critical - the image must incorporate recognizable elements of BOTH the specific profession (tools, activities, symbols associated with that role) AND the industry context provided. The profession elements and industry elements should be naturally integrated into a cohesive scene, not placed as separate concepts side by side
- Background color: MUST be pure white (#FFFFFF) - solid, flat, no gradients or texture
- Visual complexity: Moderate detail is fine since this won't have text overlaid
- Edges: Clean, no border needed
- NO people, NO text, NO letters, NO numbers anywhere in the image

The profession is: {profession_title}
The company context is: {company_name} ({industry_context})

Create a professional visual using only objects, tools, and symbols that someone would immediately recognize as representing both this specific profession AND this industry/domain. The blend should feel natural and integrated. The aesthetic should feel professional yet approachable.
"""
    return prompt


def generate_interests_illustration_prompt(attendee: Attendee, template: dict) -> str:
    """Generate prompt for interests illustration (horizontal image) matching template."""
    color_palette = template.get("colorPalette", {})

    # Format color palette as descriptive string
    color_names = {
        # Professional template colors
        "warmOrange": "warm oranges",
        "teal": "teals",
        "navyBlue": "navy blues",
        "goldenYellow": "golden yellow",
        "cream": "cream",
        # Casual template colors
        "coral": "coral reds",
        "skyBlue": "bright sky blue",
        "lavender": "rich lavender purple",
        "peach": "soft peach",
        "mintCream": "mint cream"
    }
    color_parts = []
    for key, hex_val in color_palette.items():
        display_name = color_names.get(key, key)
        color_parts.append(f"{display_name} ({hex_val})")
    color_palette_str = ", ".join(color_parts)

    # Get interests list - use normalized version to avoid brand/celebrity violations
    interests = attendee.interests_normalized if attendee.interests_normalized else attendee.interests
    interests = interests if interests else []
    interests_list = ", ".join(interests)
    num_interests = len(interests)

    prompt = f"""⚠️ ABSOLUTE REQUIREMENT - NO TEXT WHATSOEVER ⚠️
This illustration must contain ZERO text, letters, numbers, labels, or words of ANY kind. This is a non-negotiable requirement. If you include any text, the image will be rejected and must be regenerated.

Create a clean, friendly illustration in a modern flat design style for a professional name badge.

FORMAT & DIMENSIONS:
- Canvas: 1536x1024 pixels (3:2 aspect ratio, horizontal/landscape orientation)
- Elements: {num_interests} distinct, immediately recognizable icons/symbols
- Each element should be identifiable from several feet away - think icon clarity with personality

ILLUSTRATION STYLE:
Modern flat illustration with subtle texture - similar to Dropbox or Headspace brand illustration style.
- Consistent stroke weights across ALL elements (approximately 4-6px outlines)
- Flat/2D composition with slight gradients OK within individual elements
- Unified visual treatment: all elements must feel like they're from the same illustration set
- Not corporate clipart, not overly artistic - friendly and approachable
- Professional but playful

CRITICAL - COLOR PALETTE:
Use ONLY these exact colors: {color_palette_str}
- No other hues or colors are permitted
- Each element should use 2-3 colors from this palette
- Maintain consistent color distribution across the composition
- Avoid neon or muddy colors

CRITICAL - BACKGROUND:
Pure white background (#FFFFFF) - solid, flat, no gradients, no texture, no tinting

🚫 CRITICAL CONSTRAINT - ABSOLUTELY NO TEXT OR PEOPLE 🚫
This is the MOST IMPORTANT requirement:
- Do NOT include ANY text, letters, numbers, words, labels, captions, or typography
- This means NO text on objects (like labels on jars, words on books, etc.)
- This means NO floating text labels identifying the icons
- This means NO decorative text or letterforms
- Do NOT include any people or human figures (see exception below)
- Do NOT draw badge shapes, lanyards, or framing elements
VIOLATION OF THE NO-TEXT RULE WILL RESULT IN IMAGE REJECTION

LAYOUT & COMPOSITION:
- Equal padding/margins on ALL FOUR SIDES (approximately 80-100 pixels from each edge)
- Elements should fill BOTH horizontal AND vertical space generously after accounting for margins
- Use the full height of the canvas - avoid thin horizontal strips across the middle
- Composition style: Like a modern brand hero illustration - elements flow naturally across horizontal space with rhythmic spacing, not a rigid grid
- Vertical positioning: Stagger elements at different heights to create visual interest. Some higher, some lower - avoid aligning all elements on a single horizontal baseline

SIZING GUIDELINES:
Scale elements to fill the space regardless of count:
- 3 elements: Larger scale (~400-500px height each)
- 7 elements: Smaller scale (~250-300px height each)
- Goal: Consistent visual density and balanced spacing across all compositions

ONE ELEMENT PER INTEREST:
Each interest must be represented by EXACTLY ONE visual element - not multiple separate objects.
- "Coffee" = ONE mug (not mug + beans + pot)
- "Rock climbing" = ONE climbing wall OR ONE carabiner (not multiple pieces of gear)
- "Hunting" = ONE rifle OR ONE deer (not 2 guns + target)
This ensures equal visual weight and consistent spacing. Think: one cohesive icon/symbol per interest.

VISUAL COHERENCE & CONSISTENCY:
All elements must feel like they belong to the same illustration set. Maintain consistent:
- Stroke weights (4-6px across all elements)
- Corner rounding (same radius on all rounded shapes)
- Level of detail (all elements should have similar complexity)
- Shadow treatment (if using shadows, apply consistently to all elements with same angle/opacity)
- Visual style (all outlined, all filled, or consistent mix)

HANDLING PEOPLE-RELATED INTERESTS:
If an interest references being a parent or family (parent, dad, mom, family time):
- Represent using ONLY child-related objects (toys, children's books, baby items)
- OR use abstract family symbols (heart, house, etc.)
- NEVER depict actual people, adults, or children
- Use generic silhouettes ONLY if absolutely necessary (no identifiable features)

The interests to depict are: {interests_list}

Create a cohesive, professional, friendly illustration that maintains visual consistency across all elements while remaining fun and approachable for name badge use.

⚠️ FINAL REMINDER: DO NOT INCLUDE ANY TEXT, LETTERS, NUMBERS, OR WORDS IN THIS ILLUSTRATION. The icons must speak for themselves without text labels. ⚠️
"""
    return prompt


def main():
    """Generate all AI prompts."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate AI image prompts")
    parser.add_argument("--skip-professional", action="store_true",
                       help="Skip professional visual prompts (deprecated)")
    parser.add_argument("--event", help="Filter to specific event_id (e.g., cohatch_afterhours)")
    args = parser.parse_args()

    print("=" * 70)
    print("AI Image Prompt Generator")
    print("=" * 70)
    if args.event:
        print(f"Event filter: {args.event}")

    # Load data
    events = load_events()
    attendees = load_attendees()
    event_mapping = load_event_mapping()
    templates = {}

    # Create lookup
    attendees_by_id = {a.id: a for a in attendees}

    all_prompts = []

    for event_id, event_attendees in event_mapping.items():
        # Skip if event filter is specified and doesn't match
        if args.event and event_id != args.event:
            continue

        if event_id not in events:
            continue

        event = events[event_id]

        # Load template if needed
        if event.template_id not in templates:
            templates[event.template_id] = load_template(event.template_id)

        template = templates[event.template_id]

        for event_attendee in event_attendees:
            attendee_id = event_attendee.user_id
            if attendee_id not in attendees_by_id:
                continue

            attendee = attendees_by_id[attendee_id]

            # Generate prompts
            prof_prompt = None if args.skip_professional else generate_professional_visual_prompt(attendee, template)
            interests_prompt = generate_interests_illustration_prompt(attendee, template)

            # Save individual prompt files in event/user structure
            event_dir = WORKING_DIR / event.event_id
            attendee_dir = event_dir / attendee.id / "ai_prompts"
            attendee_dir.mkdir(parents=True, exist_ok=True)

            if prof_prompt:
                (attendee_dir / "professional_visual_prompt.txt").write_text(prof_prompt, encoding="utf-8")
            (attendee_dir / "interests_illustration_prompt.txt").write_text(interests_prompt, encoding="utf-8")

            # Collect for summary
            all_prompts.append({
                "event": event.display_name,
                "attendee_id": attendee.id,
                "attendee_name": attendee.name,
                "profession": attendee.profession or attendee.title,
                "industry": attendee.industry,
                "interests_count": len(attendee.interests),
                "output_dir": str(attendee_dir.relative_to(ROOT))
            })

            print(f"✔ {attendee.name} ({event.display_name})")
            print(f"  → {attendee_dir.relative_to(ROOT)}/")

    # Save summary JSON
    summary_path = WORKING_DIR / "prompts_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(all_prompts, f, indent=2)

    print("\n" + "=" * 70)
    print(f"✅ Generated {len(all_prompts)} prompt sets")
    print(f"📁 Output directory: {WORKING_DIR}")
    print(f"📄 Summary: {summary_path.relative_to(ROOT)}")
    print("=" * 70)

    print("\nNext steps:")
    print("1. Review the prompt files in output/working/")
    print("2. Use generate_images.py to generate AI images")
    print("3. Use generate_badges.py to create final badges")


if __name__ == "__main__":
    main()
