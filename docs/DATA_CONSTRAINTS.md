# Data Constraints & Validation Rules

This document defines the constraints, validation rules, and business logic for the name tag generation system. These constraints guide form design, data validation, and edge case testing.

## Overview

The system operates on an **MVP philosophy**: minimal hard requirements with graceful degradation for missing or edge case data. The primary goal is professional, flexible badge design that handles real-world variation.

---

## 1. Field-Level Constraints

### 1.1 Hard Limits (Form Validation)

Character limits enforced at form submission:

| Field | Max Characters | Notes |
|-------|----------------|-------|
| **name** | 100 | Only truly required field |
| **title** | 60 | Job title - limited to ensure max 2 line wrap on badge |
| **company** | 100 | Company/organization name |
| **location** | 100 | City, state/country format |
| **raw_interests** | 1000 | Free-text paragraph about interests |
| **social_handle** | 50 | Social media handle (with or without @) |
| **event_name** | 30 | Display name for event - limited to ensure max 2 line wrap on badge (1.6in width at 11pt) |
| **event_date** | 50 | Free-form date string |
| **tag_values** (write-in) | 50 | Custom tag values for select tags |

### 1.2 Required vs Optional Fields

**Attendee Model:**
- **Required**: `name` (absolute minimum for valid badge)
- **Optional**: All other fields (title, company, location, interests, social media, profile_url, images)

**Event Model:**
- **Required**: `event_id`, `display_name`, `template_id`
- **Optional**: `date`, `sponsor`, `logo_path`, `sponsor_logo_path`, `tag_categories`

### 1.3 Data Types & Formats

**Text Fields:**
- Support full Unicode (emoji, Chinese, Arabic, Cyrillic, etc.)
- Trim leading/trailing whitespace
- Normalize internal multiple spaces to single space
- Allow special characters: `& - ' @ / . , ( )`

**URLs:**
- `profile_url`: Valid HTTP/HTTPS URL or null
- `logo_path`, `sponsor_logo_path`, `interests_image_path`: Valid file paths or null

**Arrays:**
- `interests`: Array of strings, 0-unlimited items
- `interests_normalized`: Array of strings, 0-8 items (see normalization rules)
- `tags`: Object/dictionary of tag_name → tag_value pairs

---

## 2. Content Validation

### 2.1 Security Sanitization

**XSS Prevention:**
- All text fields sanitized to remove HTML tags, scripts, and executable code
- Special handling for characters: `< > " ' &` → HTML entity encoding when rendering

**Path Traversal Prevention:**
- File paths validated to prevent `../` traversal attacks
- Image paths restricted to designated output directories

**Command Injection Prevention:**
- No shell commands constructed from user input
- All external API calls (geocoding) properly escaped

### 2.2 Unicode & Special Characters

**Fully Supported:**
- Emoji in any text field (🎸, ☕, 🚀)
- Chinese, Japanese, Korean characters (李娜, 北京)
- Arabic, Hebrew (right-to-left text)
- Latin extended (ñ, ü, ø, å)
- Accents and diacritics (María, Björk, São Paulo)

**Rendering Considerations:**
- Font stack includes fallbacks for non-Latin scripts
- WeasyPrint handles RTL text direction automatically

### 2.3 Profanity & Content Filtering

**No Automatic Filtering:**
- Profanity not automatically filtered (event organizer responsibility)
- AI normalization may abstract inappropriate content naturally
- Manual review recommended for public-facing events

---

## 3. Business Logic Constraints

### 3.1 Interests Processing Flow

The system uses a **three-stage interests pipeline**:

```
User Input (Form)
    ↓
raw_interests: "I love running in my Nike shoes, watching Cleveland Browns games,
               and going to Taylor Swift concerts!"
    ↓
AI Parsing → interests array
    ↓
interests: ["Running in Nike shoes", "Cleveland Browns fan", "Taylor Swift concerts"]
    ↓
AI Normalization → interests_normalized array
    ↓
interests_normalized: ["Running", "Football fan", "Pop music concerts"]
```

**Normalization Rules:**
1. **Brand Abstraction**: "Nike shoes" → "Running shoes" → "Running"
2. **Celebrity Abstraction**: "Taylor Swift concerts" → "Pop music concerts"
3. **Sports Team Abstraction**: "Cleveland Browns fan" → "Football fan"
4. **Trademark Abstraction**: "CrossFit" → "Fitness training", "Peloton" → "Indoor cycling"
5. **Count Constraint**: Reduce to 3-8 most distinctive interests
6. **Duplicate Removal**: "Coffee" and "coffee enthusiast" → single "Coffee" interest

**Why Normalize?**
- **Trademark safety**: Avoid using brand logos/names in AI-generated images
- **Visual abstraction**: Generic concepts easier to represent visually
  - Example: "Football fan" → Image of generic football helmet with team colors (no logos)
- **Content safety**: Celebrities → generic categories reduces potential issues

**Edge Cases:**
- **0 interests provided**: `interests_normalized: []` is valid (no interests band rendered)
- **1-2 interests**: AI may keep all if distinctive, or return empty array
- **15+ interests**: AI selects 3-8 most unique/conversation-worthy items

### 3.2 Location Geocoding

**Process:**
1. User enters location string (e.g., "San Francisco, CA")
2. System attempts geocoding via Nominatim API
3. If successful: Extract city/state or city/country for display
4. If unsuccessful: Use original user input as-is

**Fallback Behavior:**
- API timeout (>5s): Use original input
- API unavailable: Use original input
- No results: Use original input
- Invalid/nonsense location: Use original input (no error)

**Examples:**
- "Short North, Columbus, OH" → Geocodes to "Columbus, OH"
- "Atlantis, Lost Kingdom" → No match, displays "Atlantis, Lost Kingdom"
- "asdfasdf" → No match, displays "asdfasdf"

### 3.3 Tag Constraints

**Per Event:**
- **Max tag categories**: 5 total (4 standard + 1 micro)
  - Standard tags: Maximum 4 tags with `display_type: "standard"` (or null)
  - Micro tags: Maximum 1 tag with `display_type: "micro"`
- **Tag types**: `select` (predefined values) or `write_in` (user-entered)

**Per Attendee:**
- **Max tags rendered**: Limited by physical space (2.7" width)
- **Tag position**: Top 3 tags render at top, remaining at bottom
- **Overflow handling**: If tags exceed width, truncate or wrap (TBD during testing)

**Tag Value Validation:**
- Must match allowed `values` array for `select` type tags
- `write_in` tags: Any string up to 50 chars
- Invalid tag values: Render as-is (no strict enforcement in MVP)

### 3.4 Social Media Handling

**Platform Support:**
- linkedin, twitter, facebook, instagram, github, tiktok, youtube
- System uses corresponding icon SVG from `config/social_icons/`

**Handle Formats:**
- With @: "@username" → Rendered as-is
- Without @: "username" → Rendered as-is
- Platform determines if @ is appropriate (LinkedIn doesn't use @)

**Edge Cases:**
- `preferred_social_platform` set but `social_handle` null: Icon renders but no handle text
- `social_handle` set but `preferred_social_platform` null: No social media rendered
- Unknown platform: Gracefully skip social media rendering

---

## 4. Rendering Constraints

> **Note**: For detailed visual design rules (typography hierarchy, spacing system, color standards), see [DESIGN.md](DESIGN.md). This section focuses on data-level rendering constraints and truncation logic.

### 4.1 Physical Badge Dimensions

**Badge Size:** 3" × 4" (portrait orientation)
**Printable Area:** 2.7" × 3.7" (0.15" margins)

### 4.2 Text Rendering & Truncation

**Name Field:**
- **Max width**: 2.7"
- **Font size**: 18pt (default) → 12pt (minimum)
- **Truncation strategy** (see `src/utils/name_utils.py`):
  1. Try full name at 18pt
  2. Shrink font to 12pt
  3. Remove middle names/initials
  4. Remove patronymics (Mikhailovna, bin Mohammed)
  5. Abbreviate last name (e.g., "García-Fernández" → "García-F.")
  6. First name only (last resort)
- **Single line**: Name never wraps, always truncates

**Title Field:**
- **Max lines**: 2
- **Truncation**: CSS `-webkit-line-clamp: 2` cuts overflow
- **Font size**: 10pt (fixed)
- **Width**: 2.2" (constrained by location graphic)

**Company Field:**
- **Max lines**: 1
- **Truncation**: `text-overflow: ellipsis`
- **Font size**: 9pt (fixed)

**Event Name:**
- **Max lines**: 3
- **Truncation**: CSS `-webkit-line-clamp: 3`
- **Font size**: 11pt (fixed)
- **Width**: 1.5" (between logo and QR code)

**Location:**
- **Max lines**: 1
- **Truncation**: `text-overflow: ellipsis`
- **Font size**: Varies (5pt for graphic label, 9pt for full location field)

### 4.3 Image Rendering

**Interests Illustration:**
- **Dimensions**: 2.7" × 1.35" (2:1 aspect ratio)
- **Format**: PNG, RGB, 288 DPI
- **Positioning**: Absolute position, bottom section of badge
- **Missing image**: Graceful degradation (no interests band, badge still renders)
- **Wrong aspect ratio**: Image cropped/padded to 2:1 via `crop_interests_image.py`

**QR Code:**
- **Dimensions**: 0.5" × 0.5" square
- **Position**: Top right corner
- **Missing profile_url**: No QR code rendered (graceful degradation)

**Event Logo:**
- **Dimensions**: 0.5" × 0.5" square
- **Position**: Top left corner
- **Format**: SVG or PNG
- **Missing logo**: Graceful degradation (no logo rendered)

**Sponsor Logo:**
- **Dimensions**: 0.5" × 0.25" rectangle
- **Position**: Below event logo
- **Missing sponsor_logo_path**: No sponsor logo rendered

### 4.4 Tag Rendering

**Tag Positioning:**
- **Top tags** (first 3): Positioned at `top: 0.8in`
- **Bottom tags** (remaining): Positioned at `bottom: 0.15in`

**Tag Styling:**
- **Font size**: 8pt
- **Padding**: 0.05" vertical, 0.1" horizontal
- **Border radius**: 0.08"
- **Gap between tags**: 0.08"
- **Background color**: Defined per tag category (e.g., `#E07A5F`)

**Overflow Behavior:**
- **Current**: `white-space: nowrap` prevents wrapping
- **If tags exceed 2.7"**: Overflow hidden (tags cut off)
- **Future consideration**: Dynamic font sizing or multi-row tags

### 4.5 Graceful Degradation

**Missing Data Handling:**

| Missing Field | Rendering Behavior |
|---------------|-------------------|
| `title` | Title field not rendered, company moves up |
| `company` | Company field not rendered |
| `location` | Location field not rendered |
| `interests_image_path` | No interests band, more vertical space |
| `profile_url` | No QR code rendered |
| `social_handle` / `preferred_social_platform` | No social media section |
| `event_logo_path` | No event logo |
| `sponsor_logo_path` | No sponsor logo |
| `tags` (empty object) | No tags rendered |

**Minimal Valid Badge:**
- Name only: "John Doe"
- Event name at top
- All other sections omitted
- Still professional and printable

> **Note**: For visual layout behavior when elements are missing (gap collapsing, spacing adjustments, maintaining visual balance), see [DESIGN.md, Section 6](DESIGN.md#6-fallback-behavior-for-missing-data).

---

## 5. Validation Severity Levels

### 5.1 Hard Reject (Form Won't Submit)

- `name` is null, empty, or whitespace only
- `name` exceeds 100 characters
- `title` exceeds 150 characters
- `company` exceeds 100 characters
- `location` exceeds 100 characters
- `raw_interests` exceeds 1000 characters
- `social_handle` exceeds 50 characters
- XSS attempt detected (`<script>`, `javascript:`, etc.)
- Path traversal attempt (`../`, absolute paths in image fields)

### 5.2 Soft Warning (User Can Proceed)

- Name is very long (>50 chars) - warn about potential truncation
- Title is very long (>100 chars) - warn about potential truncation
- Many interests (>10 in raw text) - inform about normalization to 3-8
- Missing `location` - recommend providing for context
- Missing `profile_url` - inform QR code won't be generated

### 5.3 Silent Handling (System Deals With It)

- Name truncation via font shrinking and intelligent shortening
- Title/event name truncation via CSS line clamping
- Location geocoding failure → use original input
- Interest normalization (brand abstraction)
- Whitespace trimming and normalization
- Missing images → graceful omission from badge

### 5.4 Informational Only (No Action Required)

- Unicode characters detected
- Emoji in any field
- Special characters (& ' - @) in text
- Very short name (<10 chars)
- No interests provided

---

## 6. Testing Boundaries

### 6.1 Exact Boundary Tests

Test data should include cases at exact constraint limits:

- Name with exactly 100 characters
- Title with exactly 150 characters
- raw_interests with exactly 1000 characters
- social_handle with exactly 50 characters
- Name that causes exactly 1 line at 12pt font (max width)
- Title that fills exactly 2 lines
- Event name that fills exactly 3 lines

### 6.2 Just Under Limit Tests

- Name with 99 characters
- Title with 149 characters
- All fields just under limits to verify no false rejections

### 6.3 Over Limit Tests

- Name with 101 characters (should reject at form)
- Title with 151 characters (should reject at form)
- Verify form validation catches these

### 6.4 Null/Missing Data Tests

- Every optional field tested as null
- Combinations: null title + null company, null location + null interests, etc.
- Minimal badge: name only

### 6.5 Special Character Tests

- Every special character in every field
- Unicode boundary characters (emoji, combining diacritics, zero-width spaces)
- Right-to-left text (Arabic, Hebrew)
- Mixed scripts in single field

---

## 7. Future Considerations

### 7.1 Potential Enhancements

- **Dynamic tag sizing**: Shrink font if tags exceed width
- **Multi-row tags**: Allow tags to wrap to multiple rows
- **Image format support**: Accept JPEG, WebP, SVG for interests images
- **Batch validation**: Validate entire CSV upload at once
- **Profile URL verification**: Check that URL is accessible before generating QR
- **Location autocomplete**: Suggest locations as user types

### 7.2 Print Production Constraints (Future)

- **Bleed area**: Add 0.0625" bleed for professional printing
- **Color mode**: Convert RGB to CMYK for print
- **Resolution**: Ensure all images are 300 DPI minimum
- **Perforation**: Reserve space for badge holder punch holes
- **Paper stock**: Define standard paper sizes (8.5" × 11" sheet = 6 badges)

---

## 8. Summary Table

| Category | Constraint Type | Value | Enforcement |
|----------|----------------|-------|-------------|
| **Name** | Max length | 100 chars | Hard reject |
| | Required | Yes | Hard reject |
| | Truncation | Font 18pt→12pt, then text | Silent |
| **Title** | Max length | 150 chars | Hard reject |
| | Max lines | 2 | CSS truncation |
| **Company** | Max length | 100 chars | Hard reject |
| **Location** | Max length | 100 chars | Hard reject |
| | Geocoding | Nominatim API | Fallback to input |
| **raw_interests** | Max length | 1000 chars | Hard reject |
| **interests** | Count | 0-unlimited | AI parsing |
| **interests_normalized** | Count | 0-8 (prefer 3-8) | AI normalization |
| **social_handle** | Max length | 50 chars | Hard reject |
| **Event name** | Max length | 100 chars | Hard reject |
| | Max lines | 3 | CSS truncation |
| **Tags** | Max per person | No limit | Physical width limit |
| | Max width | 2.7" | Overflow hidden |
| **All text fields** | XSS | Sanitized | Hard reject |
| | Unicode | Fully supported | Render as-is |

---

**Document Version:** 1.0
**Last Updated:** 2025-11-16
**Status:** MVP Baseline
