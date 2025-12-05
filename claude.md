# Badge Generation Pipeline Documentation

## Overview

This badge generation system creates professional name tag badges with AI-generated interest illustrations. The system processes attendee data, generates personalized imagery using Azure OpenAI's image generation API, and renders high-quality PDF badges with dynamic layout calculations.

## Pipeline Architecture

The badge generation pipeline consists of three sequential steps orchestrated by `scripts/generate_all.py`:

### Step 1: Generate AI Prompts
**Script:** `scripts/generate_ai_prompts.py`

Reads attendee data from:
- `mocks/attendees.json` - Personal information (name, title, company, location, interests)
- `mocks/event_attendees.json` - Event-specific tag assignments

Generates structured prompts for:
- **Professional visuals** (1024×1024 square) - Optional, typically skipped with `--skip-professional`
- **Interests illustrations** (1536×1024 horizontal) - Primary AI-generated image

Output: `output/working/{event_id}/{user_id}/ai_prompts/*.txt`

### Step 2: Generate AI Images
**Script:** `scripts/generate_images.py`

Uses Azure OpenAI GPT Image 1 API to generate images from prompts.

**Key features:**
- Rate limiting: 2-second delays between API calls to avoid throttling
- Smart skip: Checks for existing images, only generates missing ones
- Force mode: `--force` flag regenerates all images
- Interests-only mode: `--interests-only` skips professional visuals

Output: `output/working/{event_id}/{user_id}/generated_images/*.png`

### Step 3: Generate PDF Badges
**Script:** `scripts/generate_all_badges.py`

Renders final badges using HTML/CSS templates via WeasyPrint.

Uses: `src/renderers/badge_renderer_html.py`

Output: `output/badges/{event_id}/{user_id}.pdf`

---

## Image Processing Deep Dive

### Background Normalization

**Function:** `normalize_background_to_white()`
**Location:** `scripts/generate_images.py` lines 88-146

**Algorithm:**
1. **Edge Sampling** - Sample pixels from image edges to detect background color
2. **Color Analysis** - Calculate median RGB values of edge pixels
3. **Flood Fill** - Replace pixels within tolerance threshold with pure white (#FFFFFF)
4. **Tolerance** - Default: 30 (allows flexibility for near-background colors)

**Why it matters:** Ensures consistent white backgrounds across all AI-generated images, preventing color bleeding into badge layouts.

### Smart Cropping (Interests Illustrations)

**Function:** `crop_interests_image()`
**Location:** `scripts/image_processing/crop_interests_image.py`

**Target:** 2.0:1 aspect ratio (for 2.7" × 1.35" display area on badge)

**Algorithm:**

1. **Content Detection**
   - Scan image for non-white pixels (RGB < 245)
   - Calculate bounding box of all content
   - Ignore background pixels

2. **Margin Application**
   - Add 0.15" standard margin around detected content
   - Convert inches to pixels using DPI (288)
   - Ensures breathing room around illustrations

3. **Aspect Ratio Enforcement**
   - Calculate width and height with margins
   - Expand shorter dimension to achieve 2.0:1 ratio
   - Maintain content centering

4. **Padding Handling**
   - If content extends beyond image bounds, add white padding
   - Ensure final image meets exact aspect ratio requirements

**Parameters:**
```python
target_aspect_ratio: 2.0  # Width:Height ratio
margin_inches: 0.15       # Standard margin around content
dpi: 288                  # Matches badge rendering DPI
background_threshold: 245  # RGB value considered "background"
```

**Example:**
```
Input: 1536×1024 AI-generated image (1.5:1 ratio)
Content detected: 1200×800 pixels
Add margins: 0.15" × 288 DPI = 43px → 1286×886 pixels
Enforce 2.0:1: Expand height to 643 pixels (1286÷2)
Output: 1286×643 pixels, cropped and centered
```

---

## Badge Rendering & Alignment

### Dynamic Title Line Calculation

**Function:** `_calculate_title_lines()`
**Location:** `src/renderers/badge_renderer_html.py` lines 137-169

**Purpose:** Predict whether a job title will wrap to 2 lines before rendering.

**Algorithm:**
1. Measure text width using ReportLab's `pdfmetrics.stringWidth()`
2. Compare against max width (2.2 inches for title area)
3. Apply 5% safety margin (conservative threshold)
4. Return: 0 (no title), 1 (single line), or 2 (wraps to 2 lines)

**Why it matters:** Title line count affects vertical positioning of interests band and professional block alignment.

**Parameters:**
```python
max_width_inches: 2.2   # Available width to right of location graphic
font_size: 10.0         # Title font size in points
font_name: "Helvetica"  # Base font family
safety_margin: 5%       # Conservative wrapping threshold
```

### Professional Block Vertical Centering

**Function:** `_calculate_professional_positioning()`
**Location:** `src/renderers/badge_renderer_html.py` lines 239-281

**Purpose:** Vertically center the location graphic with the title+company text block.

**Algorithm:**

1. **Calculate Title Height**
   - 0 lines: 0 inches
   - 1 line: (10pt × 1.2 line-height) ÷ 72 = 0.167 inches
   - 2 lines: (10pt × 1.2 × 2) ÷ 72 = 0.333 inches

2. **Calculate Company Height**
   - (9pt × 1.2 line-height) ÷ 72 = 0.150 inches

3. **Total Text Block Height**
   - title_height + 0.04" gap + company_height

4. **Center Graphic**
   - Find midpoint of text block
   - Offset graphic by (text_center - graphic_size/2)

**Layout coordinates:**
```
Professional block top: 1.75" from badge top
Location graphic: 0.4" × 0.4" square
Title font: 10pt, line-height 1.2
Company font: 9pt, line-height 1.2
Gap between title and company: 0.04"
```

### Interests Band Dynamic Positioning

**Location:** `src/renderers/badge_renderer_html.py` lines 316-378

**Purpose:** Position interests band with appropriate spacing, scaling down if necessary to avoid overlapping with bottom tags.

**Algorithm:**

1. **Calculate Top Position**
   ```
   interests_top = professional_bottom + 0.10" gap
   ```

2. **Calculate Available Height**
   ```
   badge_height: 4.0"
   bottom_tags_top: 3.62"
   min_gap_to_tags: 0.10"
   max_interests_bottom: 3.52"

   available_height = max_interests_bottom - interests_top
   ```

3. **Scale If Necessary**
   ```python
   if available_height < interests_band_height (1.35"):
       scale_factor = available_height / 1.35
       scaled_height = available_height
       scaled_width = 2.7 × scale_factor  # Maintain 2:1 aspect ratio
       left_offset = (2.7 - scaled_width) / 2  # Center horizontally
   else:
       scaled_height = 1.35"
       scaled_width = 2.7"
       left_offset = 0
   ```

4. **Calculate Bottom Position**
   ```
   interests_bottom = 4.0" - interests_top - scaled_height
   ```

**Key constraints:**
- Default size: 2.7" × 1.35" (2:1 aspect ratio)
- Scales down proportionally if space is tight
- Maintains 0.10" minimum gap to bottom tags
- Centers horizontally when scaled

### Tag Auto-Fitting Algorithm

**Function:** `_calculate_tag_row_styling()`
**Location:** `src/renderers/badge_renderer_html.py` lines 170-238

**Purpose:** Ensure tags fit within max width by progressively reducing styling until tags fit.

**Algorithm:**

1. **Default Styling**
   ```python
   font_size: 8pt
   padding_h: 0.12"
   gap: 0.08"
   ```

2. **Calculate Total Width**
   ```python
   for each tag:
       text_width = pdfmetrics.stringWidth(tag_text, "Helvetica", font_size) / 72
       tag_width = (padding_h × 2) + text_width
       total_width += tag_width + gap
   ```

3. **Apply Safety Factor**
   ```python
   safety_factor = 0.93  # 93% of max_width
   safe_max_width = 2.7" × 0.93 = 2.511"
   ```

   **Why:** `pdfmetrics.stringWidth()` doesn't account for bold/semibold (font-weight 600) rendering, which makes text ~7% wider.

4. **Progressive Reduction Steps**
   ```python
   gap_steps = [0.08, 0.06, 0.04]
   padding_steps = [0.12, 0.10, 0.08]
   font_steps = [8, 7.5, 7]
   ```

5. **Try Combinations Until Fit**
   - For each font_size:
     - For each padding_h:
       - For each gap:
         - Calculate total width
         - If ≤ safe_max_width: RETURN this configuration

6. **Fallback** (if nothing fits)
   ```python
   { font_size: 7, padding_h: 0.08, gap: 0.04 }
   ```

**Example - 5 tags for cohatch_afterhours:**
```
Tags: "Innovation & Transformation Council", "5-9 years", "Cameron Wright", "Professional Services", "Corporate Plus"

Row 1 (top 3 tags):
- Default: font 8pt, padding 0.12", gap 0.08"
- Width calculation: 2.48" < 2.511" ✓
- Use: { font_size: 8, padding_h: 0.12, gap: 0.08 }

Row 2 (bottom 2 tags):
- Default: font 8pt, padding 0.12", gap 0.08"
- Width calculation: 2.35" < 2.511" ✓
- Use: { font_size: 8, padding_h: 0.12, gap: 0.08 }
```

### Name Dynamic Sizing

**Function:** `get_display_name()`
**Location:** `src/utils/name_utils.py`

**Purpose:** Ensure names fit within available width, using smart truncation if necessary.

**Algorithm:**

1. **Try Sizes from 18pt → 12pt**
   - Measure text width at each font size
   - If fits within max_width: Return full name at that size

2. **Progressive Truncation** (if still too long)
   - Abbreviate middle names to initials
   - Abbreviate last name to initial
   - Truncate first name if absolutely necessary

3. **Return**
   ```python
   {
       'text': "Optimized name",
       'font_size': 18.0  # (or smaller if shrunk)
   }
   ```

**Parameters:**
```python
max_width: 2.7"           # Full badge width minus margins
default_font_size: 18.0   # Starting size
min_font_size: 12.0       # Minimum allowed size
font_family: "Helvetica"  # Base font
```

---

## Commands Reference

### Run All Events (Recommended)
```bash
python scripts/generate_all.py
```
Generates badges for all attendees across all events.

### Run Single Event
```bash
python scripts/generate_all.py --event cohatch_afterhours
```
Generates badges only for specified event.

### Force Regeneration
```bash
python scripts/generate_all.py --force
```
Regenerates all images and badges, even if they already exist.

### Badges Only (Skip Image Generation)
```bash
python scripts/generate_all.py --event cohatch_afterhours --badges-only
```
Only regenerates PDF badges, assumes images already exist.

### Individual Steps

**Generate prompts only:**
```bash
python scripts/generate_ai_prompts.py
python scripts/generate_ai_prompts.py --event cohatch_afterhours
python scripts/generate_ai_prompts.py --skip-professional
```

**Generate images only:**
```bash
python scripts/generate_images.py
python scripts/generate_images.py --event cohatch_afterhours
python scripts/generate_images.py --interests-only
python scripts/generate_images.py --force
```

**Generate badges only:**
```bash
python scripts/generate_all_badges.py
python scripts/generate_all_badges.py --event cohatch_afterhours
```

---

## Azure Deployment

The badge generation system runs as an Azure Function for production use. See `DEPLOYMENT.md` for full setup instructions.

### Deploy Commands

```bash
# Full deployment (sync + validate + deploy)
./scripts/deploy-function.sh

# Sync files only, skip Azure deploy
./scripts/deploy-function.sh --no-deploy

# Preview changes (dry run)
./scripts/deploy-function.sh --dry-run

# Validate imports before deploying
python function_app/test-imports.py
```

### Function Endpoints

| Endpoint | URL |
|----------|-----|
| Health Check | `https://func-name-tag-gen-66802.azurewebsites.net/api/health` |
| Process Badge | `https://func-name-tag-gen-66802.azurewebsites.net/api/process-badge` |

---

## Environment Variables

### Azure OpenAI Credentials

The image generation supports two naming conventions for flexibility:

| Variable | Environment | Purpose |
|----------|-------------|---------|
| `AZURE_OPENAI_API_KEY` | Azure | Image generation API key |
| `AZURE_OPENAI_ENDPOINT` | Azure | Image generation endpoint |
| `AZUREAI_API_CUSTOM_API_KEY` | Local | Image generation API key (alternative) |
| `AZUREAI_API_CUSTOM_BASE_URL` | Local | Image generation endpoint (alternative) |

The code checks both naming conventions via fallback logic in `scripts/generate_images.py`.

### Azure Environment Detection

| Variable | Value | Purpose |
|----------|-------|---------|
| `ENVIRONMENT` | `prod` | Primary flag for Azure-specific behavior |

Detection logic in `src/utils/paths.py`:

1. **Primary**: `ENVIRONMENT=prod` (explicit, most reliable)
2. **Fallback**: Azure-specific env vars (`WEBSITE_INSTANCE_ID`, `FUNCTIONS_WORKER_RUNTIME`, etc.)

### Why This Matters: Azure Read-Only Filesystem

Azure Functions uses a read-only squashfs filesystem. The `output/` directory cannot be created at `/home/site/wwwroot/`. When `ENVIRONMENT=prod`:

- Output files go to `/tmp/badge_output/` (writable)
- Scripts use **lazy initialization** to avoid directory creation at import time

Key files with lazy initialization:

- `scripts/generate_ai_prompts.py` - `_get_working_dir_lazy()`
- `scripts/generate_images.py` - `_get_working_dir_lazy()`
- `src/utils/paths.py` - `get_output_dir()` returns `/tmp/badge_output` in Azure

---

## Event Configuration

### All Events

| Event ID | Display Name | Attendees | Tag Categories | Notes |
|----------|--------------|-----------|----------------|-------|
| cohatch_afterhours | AfterHours at COHATCH | 20 | 5 (Committee, Years, Rep, Industry, Membership Level) | Main demo event |
| short_name_event | BBQ | 2 | 1 (Guest Type) | Tests short event names |
| long_name_event | The Annual International Conference on Technology Innovation and Digital Transformation | 2 | 2 (Attendee Type, Track) | Tests long event names |
| tag_overload | Tech Summit 2025 | 1 | 8 (Role, Experience, Interest Area, Company Size, Looking For, Industry, Region, Dietary) | Tests maximum tag complexity |
| sponsored_event | Healthcare Innovation Forum | 1 | 3 (Role, Specialty, Organization) | Tests sponsor logo rendering |
| minimal_event | Community Meetup | 0 | 0 | Tests empty event (no attendees) |

### Total Counts
- **Events:** 6
- **Attendees:** 26 (user_001 through user_026)
- **Expected images:** 26 interests illustrations
- **Expected badges:** 26 PDF files

### Attendee Distribution
```
cohatch_afterhours: user_001 → user_020 (20 attendees)
short_name_event:   user_021 → user_022 (2 attendees)
long_name_event:    user_023 → user_024 (2 attendees)
tag_overload:       user_025 (1 attendee)
sponsored_event:    user_026 (1 attendee)
minimal_event:      (empty)
```

---

## Auto-Skip Logic

The pipeline automatically skips files that already exist to avoid unnecessary API calls and processing.

### Image Generation Skip
**Location:** `scripts/generate_images.py` lines 213-215

```python
if output_path.exists() and not force:
    print(f"⏭️  Skipping interests illustration (already exists)")
    print(f"  Use --force to regenerate")
    return
```

**Behavior:**
- Checks for `interests_illustration.png` in `output/working/{event_id}/{user_id}/generated_images/`
- If exists: Skips Azure OpenAI API call
- If missing: Generates new image
- Force mode: Regenerates even if exists

**Benefits:**
- Saves API costs
- Reduces generation time on subsequent runs
- Only generates missing/new attendees

### Badge Generation Skip
Badge PDFs are **always regenerated** on each run to ensure:
- Latest attendee data is reflected
- CSS/template changes are applied
- Tag values are current

**Rationale:** Badge rendering is fast (~1 second per badge) and doesn't incur API costs, so regenerating ensures accuracy.

---

## Expected Output

### Directory Structure
```
output/
├── working/
│   ├── cohatch_afterhours/
│   │   ├── user_001/
│   │   │   ├── ai_prompts/
│   │   │   │   ├── professional_visual_prompt.txt
│   │   │   │   └── interests_illustration_prompt.txt
│   │   │   └── generated_images/
│   │   │       └── interests_illustration.png
│   │   ├── user_002/
│   │   │   └── ... (same structure)
│   │   └── ... (user_003 through user_020)
│   ├── short_name_event/
│   │   ├── user_021/
│   │   └── user_022/
│   ├── long_name_event/
│   │   ├── user_023/
│   │   └── user_024/
│   ├── tag_overload/
│   │   └── user_025/
│   └── sponsored_event/
│       └── user_026/
│
├── badges/
│   ├── cohatch_afterhours/
│   │   ├── user_001.pdf
│   │   ├── user_002.pdf
│   │   └── ... (user_003.pdf through user_020.pdf)
│   ├── short_name_event/
│   │   ├── user_021.pdf
│   │   └── user_022.pdf
│   ├── long_name_event/
│   │   ├── user_023.pdf
│   │   └── user_024.pdf
│   ├── tag_overload/
│   │   └── user_025.pdf
│   └── sponsored_event/
│       └── user_026.pdf
│
└── location_graphics/
    ├── San_Francisco_CA.svg
    ├── Los_Angeles_CA.svg
    ├── Columbus_OH.svg
    └── ... (other location graphics)
```

### File Counts
- **AI prompts:** 52 files (26 attendees × 2 prompt types)
- **AI images:** 26 files (1 per attendee)
- **PDF badges:** 26 files (1 per attendee)
- **Location graphics:** ~15-20 SVG files (cached, generated on-demand)

### Time Estimates

**First run (no cached files):**
- AI prompt generation: ~5 seconds
- AI image generation: ~60 seconds (26 images × 2s delay + API time)
- Badge rendering: ~30 seconds
- **Total:** ~95 seconds

**Subsequent runs (images cached):**
- AI prompt generation: ~5 seconds
- AI image generation: ~0 seconds (all skipped)
- Badge rendering: ~30 seconds
- **Total:** ~35 seconds

---

## Configuration Files

### Badge Template
**File:** `config/badge_templates/cohatch_networking_template.json`

Defines layout coordinates, dimensions, and styling:
- Badge size: 3" × 4" at 300 DPI
- Text zones: name, title, company, location, event info
- Image zones: professional visual, interests band, QR code, logos
- Tag styling: colors, padding, spacing
- Font specifications: Helvetica family with sizes

### Event Configuration
**File:** `mocks/events.json`

Defines all events with:
- Event metadata (ID, name, date, sponsor)
- Logo paths (event and sponsor logos)
- Template assignment
- Tag category definitions (name, type, values, color)

### Attendee Data
**File:** `mocks/attendees.json`

Contains all attendee personal data:
- Basic info: name, title, company, location, pronouns
- Social media: platform, handle
- Interests: raw text, parsed list, normalized list
- Profile URL (for QR code)

### Event Attendees
**File:** `mocks/event_attendees.json`

Maps attendees to events with tag assignments:
- Event-specific tag values
- Links user_id to event_id
- Defines which attendees appear in which events

---

## Key Layout Coordinates

### Badge Dimensions
- Width: 3.0 inches
- Height: 4.0 inches
- Margins: 0.15 inches (left/right/top/bottom)
- Effective area: 2.7" × 3.7"

### Element Positions (from top)
```
Event header:        3.70" - 3.85"  (event name + sponsor)
Tags (top 3):        0.85"          (below sponsor text)
Name (identity):     1.20"          (large, bold, 18pt default)
Location/pronouns:   1.32"          (small, gray, 7pt)
Separator line:      1.65"          (1px gray horizontal rule)
Professional block:  1.75" - ~2.4"  (variable based on title lines)
  - Location graphic: 0.4" × 0.4" (vertically centered with text)
  - Title:           10pt, 1-2 lines max
  - Company:         9pt, single line
Interests band:      Variable top, ~0.7"-1.0" from bottom
Tags (bottom 2):     0.15" from bottom (bottom-left corner)
QR code:             0.15" from bottom (bottom-right corner)
Social media:        0.15" from bottom (next to QR code)
```

### Spacing Rules
- Gap between name and location: 0.05"
- Gap between title and company: 0.04"
- Gap between professional block and interests: 0.10"
- Min gap between interests and bottom tags: 0.10"
- Tag gap (horizontal): 0.08" (can shrink to 0.04")

---

## Troubleshooting

### Issue: Images not generating
**Symptoms:** Script reports "Skipping interests illustration (already exists)" but images don't exist.

**Solution:** Use `--force` flag to regenerate:
```bash
python scripts/generate_all.py --force
```

### Issue: Tags overflowing badge width
**Symptoms:** Tags appear cut off or extend beyond badge edge.

**Solution:** Auto-fitting algorithm should handle this. Check:
1. Tag text lengths in `mocks/event_attendees.json`
2. Safety factor in `_calculate_tag_row_styling()` (currently 93%)
3. Max tag count per row (3 top, 2 bottom)

### Issue: API rate limiting errors
**Symptoms:** "429 Too Many Requests" from Azure OpenAI.

**Solution:** Increase delay between API calls in `generate_images.py`:
```python
time.sleep(2)  # Increase to 3 or 4 seconds
```

### Issue: Interests band overlapping bottom tags
**Symptoms:** Visual overlap between interests illustration and bottom tags.

**Solution:** Dynamic scaling should prevent this. Check:
1. Professional block height calculation
2. Interests band available height calculation
3. Min gap setting (currently 0.10")

### Issue: Long names truncated
**Symptoms:** Names appear abbreviated when they shouldn't be.

**Solution:** Check `name_utils.py` sizing algorithm:
1. Max width: 2.7"
2. Font range: 18pt → 12pt
3. Truncation rules (middle name → last name → first name)

---

## Development Notes

### Adding New Events

1. Add event configuration to `mocks/events.json`
2. Define tag categories with colors
3. Add attendee mappings to `mocks/event_attendees.json`
4. Run generation: `python scripts/generate_all.py --event {new_event_id}`

### Modifying Tag Layout

Tag positioning is controlled in:
- `config/html_templates/professional/styles.css` (CSS positioning)
- `config/html_templates/professional/template.html` (HTML structure)
- `src/renderers/badge_renderer_html.py` (dynamic calculations)

### Adjusting Interests Band Size

Default: 2.7" × 1.35" (2:1 aspect ratio)

To change:
1. Update `interests_band_height` in `badge_renderer_html.py` line 348
2. Update aspect ratio in `crop_interests_image.py` if needed
3. Adjust positioning calculations accordingly

### Custom Badge Templates

Create new template by:
1. Copy `config/html_templates/professional/` to new directory
2. Modify `template.html` and `styles.css`
3. Update template path in event configuration
4. Test with: `python scripts/generate_all.py --event {event_id}`

---

## Performance Optimization

### Current Performance
- **26 attendees:** ~95 seconds (first run), ~35 seconds (cached)
- **Rate limiting:** 2 seconds per image
- **Bottleneck:** Azure OpenAI API calls

### Optimization Strategies

**1. Parallel Image Generation**
- Current: Sequential processing (1 image at a time)
- Potential: Parallel API calls (5-10 concurrent)
- Savings: ~50-70% reduction in image generation time

**2. Incremental Updates**
- Current: Regenerate all badges on each run
- Potential: Only regenerate if attendee data changed
- Savings: ~30 seconds on unchanged attendees

**3. Caching Location Graphics**
- Current: Generate on-demand, cache to disk
- Status: Already optimized ✓

**4. Template Precompilation**
- Current: Jinja2 template parsed on each render
- Potential: Precompile templates
- Savings: ~2-5 seconds

---

## Version History

- **v1.0** - Initial pipeline with JSON-based rendering
- **v2.0** - Migration to HTML/CSS rendering with WeasyPrint
- **v2.1** - Added dynamic tag auto-fitting algorithm
- **v2.2** - Added pronouns support in identity section
- **v2.3** - Refactored tag categories to 5-tag structure for cohatch event
- **v2.4** - Added smart image cropping with 2:1 aspect ratio enforcement

---

## Related Documentation

- `DEPLOYMENT.md` - Azure deployment setup and configuration
- `docs/DESIGN.md` - Visual design specifications
- `docs/DATA_MAPPING.md` - Attendee data structure
- `README.md` - Project overview and setup
- `scripts/README.md` - Script usage documentation
