# Data Mapping Verification

## Data Flow: Attendee → Template → AI Prompts → Badge

### Attendee JSON Fields (attendees.json)
```json
{
  "id": "user_001",
  "name": "Sarah C.",                    // → badge text
  "title": "UX Designer",                // → badge text + AI prompt
  "company": "MedFlow",                  // → badge text
  "location": "San Francisco, CA",       // → badge text
  "profile_url": "https://...",          // → QR code
  "interests_image_path": "...",         // → badge interests band zone
  "profession": "UX Designer",           // → AI prompt (professional visual)
  "industry": "healthcare startup",      // → AI prompt (professional visual)
  "interests": [...]                     // → AI prompt (interests illustration)
}
```

**Note**: Attendee data is now shared across all events. Event-specific data (tags) is stored in `event_attendees.json`.

### Template JSON Fields (professional_template.json, casual_template.json)

#### Required Top-Level Keys:
- `id` - Template identifier
- `name` - Human-readable template name
- `colorPalette` - Color scheme for AI prompts and rendering
- `dimensions` - Badge physical size
- `fonts` - Font settings for each text field
- `layout` - Positioning for all elements
- `tagStyle` - Visual style for tags (background, text color, padding, radius)

#### Layout Keys (must match renderer expectations):
- `event_name` - Event title position
- `event_date` - Event date position
- `name` - Attendee name position
- `title` - Job title position
- `company` - Company name position
- `location` - Location position
- `tags` - Tag zone position (x, y, max_width, gap)
- `interests_band` - Interests image zone (x, y, w, h)
- `event_logo` - Event logo zone (x, y, w, h)
- `sponsor_logo` - Sponsor logo zone (x, y, w, h)
- `qr_code` - QR code position (x, y, size)

#### Font Keys (must match layout keys):
- `name` - Font settings for attendee name
- `title` - Font settings for job title
- `company` - Font settings for company
- `location` - Font settings for location
- `event_name` - Font settings for event name
- `event_date` - Font settings for event date

### AI Prompt Generation Mapping

#### Professional Visual Prompt Uses:
- `attendee.profession` or `attendee.title` → PROFESSION
- `attendee.industry` → INDUSTRY
- `template.colorPalette` → COLOR PALETTE
- `template.professionalVisualSize` → size reference

#### Interests Illustration Prompt Uses:
- `attendee.interests[]` → INTERESTS TO VISUALIZE
- `len(attendee.interests)` → TARGET count (3-7 elements)
- `template.colorPalette` → COLOR PALETTE
- `template.interestBandHeight` → size reference

### Badge Renderer Mapping (badge_renderer_json.py)

#### Text Fields (drawn via `_draw_text`):
- `event_name` ← renderer init param
- `event_date` ← renderer init param
- `name` ← `attendee.name`
- `title` ← `attendee.title`
- `company` ← `attendee.company`
- `location` ← `attendee.location`

#### Image Fields (drawn via `_draw_image`):
- `professional_visual` ← `attendee.professional_image_path`
- `interests_band` ← `attendee.interests_image_path`

#### Special Elements:
- Tags ← event-specific `tags` dict from `event_attendees.json`
- QR code ← `attendee.profile_url`
- Event logo ← `event.logo_path`
- Sponsor logo ← `event.sponsor_logo_path`

### Event-Specific Data (event_attendees.json)

Events define **tag categories** that determine what tags are available and their colors:

```json
{
  "event_id": "cohatch_afterhours",
  "tag_categories": [
    {
      "name": "Role",
      "type": "select",
      "values": ["Speaker", "Attendee", "Panelist"],
      "color": "#E07A5F"
    },
    {
      "name": "Rep",
      "type": "write_in",
      "values": [],
      "color": "#F2CC8F"
    }
  ]
}
```

Each attendee's participation in an event includes their tag values:

```json
{
  "cohatch_afterhours": [
    {
      "user_id": "user_001",
      "tags": {
        "Role": "Speaker",
        "Years as Member": "First-Timer",
        "Rep": "Northeast"
      }
    }
  ]
}
```

**Key Points**:
- Tag categories are defined per event in `events.json`
- Each category has a `color` that determines the background color for tags in that category
- Category `type` can be:
  - `"select"`: Predefined values (most categories)
  - `"write_in"`: Any value allowed (e.g., Rep)
- Only tag **values** are displayed on badges (e.g., "Speaker", not "Role: Speaker")
- Same attendee can have different tag values for different events

## Verification Checklist

### ✅ Attendee Data Complete
- [x] All fields present in JSON
- [x] `profession` and `industry` populated for AI prompts
- [x] `interests` list has 3-7 items
- [x] Image paths reference valid locations

### ✅ Template Settings Complete
- [x] All layout keys present
- [x] All font keys match layout keys
- [x] Color palette defined
- [x] Dimensions specified

### ✅ AI Prompt Generator Working
- [x] Reads `profession`, `industry`, `interests` from attendee
- [x] Reads `colorPalette` from template
- [x] Outputs structured prompts with all required data
- [x] Generates 2 prompts per attendee (professional + interests)

### ✅ Badge Renderer Working
- [x] Reads all text fields from attendee
- [x] Reads image paths from attendee
- [x] Reads layout/font settings from template
- [x] Renders to PDF successfully

## Current Output Structure

```
output/
├── ai_prompts/
│   ├── cohatch_afterhours_user_001/
│   │   ├── professional_visual_prompt.txt
│   │   └── interests_illustration_prompt.txt
│   ├── cohatch_afterhours_user_002/
│   ├── neighborhood_gathering_user_003/
│   ├── neighborhood_gathering_user_004/
│   └── prompts_summary.json
│
└── badges/
    ├── cohatch_afterhours_user_001.pdf
    ├── cohatch_afterhours_user_002.pdf
    ├── neighborhood_gathering_user_003.pdf
    └── neighborhood_gathering_user_004.pdf
```

## Next Steps Workflow

1. **Generate prompts**: `python generate_ai_prompts.py`
2. **Review prompts**: Check `output/ai_prompts/*/` directories
3. **Generate images**: Use prompts with AI image generator
4. **Save images**: Store in appropriate directory (e.g., `assets/ai_generated/`)
5. **Update paths**: Edit `v2_attendees.json` to point to new images
6. **Regenerate badges**: `python generate_badges.py`
7. **Review PDFs**: Check `output/badges/` for final badges
