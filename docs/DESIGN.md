# Badge Design System

This document defines the visual design standards, layout rules, and consistency guidelines for the name badge generation system. It complements [DATA_CONSTRAINTS.md](DATA_CONSTRAINTS.md) (which covers data validation) by focusing on visual presentation and layout consistency.

## Table of Contents
1. [Typography Hierarchy](#1-typography-hierarchy)
2. [Spacing System & Vertical Rhythm](#2-spacing-system--vertical-rhythm)
3. [Tag System](#3-tag-system)
4. [Interests Illustration Integration](#4-interests-illustration-integration)
5. [Layout Rules & Element Positioning](#5-layout-rules--element-positioning)
6. [Fallback Behavior for Missing Data](#6-fallback-behavior-for-missing-data)
7. [Accessibility Standards](#7-accessibility-standards)
8. [Visual Consistency Checklist](#8-visual-consistency-checklist)

---

## 1. Typography Hierarchy

### Scale Definition
The typography scale is optimized for readability at 2-3 feet viewing distance on a 3" × 4" badge:

| Element | Font Size | Weight | Line Height | Max Lines |
|---------|-----------|--------|-------------|-----------|
| Name | 18pt (12pt min) | Bold | 1.1 | 2 |
| Event Title | 11pt | Bold | 1.2 | 3 |
| Title/Role | 10pt | Regular | 1.1 | 2 |
| Company | 9pt | Regular | 1.0 | 1 |
| Location (full) | 9pt | Regular | 1.0 | 1 |
| Tag Text | 8pt | Medium | 1.0 | 1 |
| Social Handle | 7pt | Regular | 1.0 | 1 |
| Location Label | 5pt | Regular | 1.0 | 2 |
| Sponsor Text | 5pt | Regular | 1.1 | 1 |

### Rationale
- **18pt name**: Largest element, must be readable from across a room (6-10 feet)
- **11pt event title**: Secondary prominence, identifies the event
- **10pt title/role**: Professional context, slightly larger than company
- **9pt company/location**: Supporting information, still clearly readable at 2-3 feet
- **8pt tags**: Categorical information, readable but not dominant
- **7pt social**: Tertiary information, readable at arm's length
- **5pt labels**: Minimum readable size for supplementary text

### Name Truncation Strategy
Implemented in `src/utils/name_utils.py`:
- Start at 18pt font size
- Measure rendered width
- If exceeds 2.7" (max badge width minus margins), shrink in 0.5pt increments
- Minimum font size: 12pt
- If still too wide at 12pt, intelligently truncate:
  - Remove middle names/initials first
  - Shorten first name if necessary
  - Never truncate last name

### Font Weights
- **Bold**: Name, event title (high importance)
- **Medium**: Tags (categorical emphasis)
- **Regular**: All other text (readable but not dominant)

### Color Usage
- **Navy (#3D405B)**: Name, title, event title (primary text)
- **Teal/Template Secondary**: Company name (brand color coordination)
- **Gray (#6C757D)**: Location label, social handle (supporting text)
- **White (#FFFFFF)**: Tag text (high contrast on colored backgrounds)

---

## 2. Spacing System & Vertical Rhythm

### Base Spacing Units
The design uses a consistent spacing scale for margins, padding, and gaps:

- **XS**: 0.05in - Minimal spacing (rarely used)
- **SM**: 0.08in - Tag gaps, corner rounding, small element spacing
- **MD**: 0.15in - Standard margins, section padding
- **LG**: 0.33in+ - Major section gaps

### Badge Margins
- **Standard margin**: 0.15in on all four sides
- **No-bleed design**: All elements must be inset from physical badge edges

### Vertical Layout Map
```
┌─────────────────────────────────────┐
│ Top Margin: 0.15in                  │
├─────────────────────────────────────┤
│ Event Header (0.15in - 0.65in)      │ 0.5in height
│   - Event Logo + Title + QR Code    │
├─────────────────────────────────────┤
│ Gap: 0.15in                          │
├─────────────────────────────────────┤
│ Top Tags (at 0.8in)                  │ 0.3in height
├─────────────────────────────────────┤
│ Gap: 0.35in                          │
├─────────────────────────────────────┤
│ Name (at 1.15in)                     │ ~0.2in height
├─────────────────────────────────────┤
│ Gap: 0.1in                           │
├─────────────────────────────────────┤
│ Professional Info (at 1.45in)        │ ~0.4in height
│   - Location Graphic + Title/Company │
├─────────────────────────────────────┤
│ Flexible gap (~0.42in)               │
├─────────────────────────────────────┤
│ Interests Band (bottom: 0.53in)      │ 1.35in height
│                                      │ (spans to top: 1.88in)
├─────────────────────────────────────┤
│ Gap: 0.38in                          │
├─────────────────────────────────────┤
│ Bottom Tags + Social (at 0.15in)     │ 0.3in height
├─────────────────────────────────────┤
│ Bottom Margin: 0.15in                │
└─────────────────────────────────────┘
Total Badge Height: 4.0in
```

### Section Gaps
- **Event header to top tags**: 0.15in
- **Top tags to name**: 0.35in
- **Name to professional info**: 0.1in (tight grouping)
- **Professional info to interests band**: ~0.42in (flexible)
- **Interests band to bottom elements**: 0.38in
- **Bottom elements to margin**: 0.15in

### Principles
- **Consistent margins**: 0.15in on all edges
- **Tight grouping**: Related elements (name + title + company) have smaller gaps
- **Breathing room**: Unrelated sections have larger gaps (0.3in+)
- **Visual hierarchy**: Larger gaps create stronger visual separation

---

## 3. Tag System

### Tag Anatomy
- **Height**: 0.3in
- **Padding**: 0.08in-0.12in (horizontal, adaptive), 0.06in (vertical)
- **Corner radius**: 0.08in (rounded corners)
- **Text**: 8pt medium weight (adaptive 7-8pt), white color
- **Gap between tags**: 0.04in-0.08in (adaptive)

### Tag Layout System

#### Top Tags (First 2 Tags)
- **Position**: `top: 0.85in, left: 0.15in`
- **Container**: `.tags-top` with fixed height 0.22in
- **Alignment**: Vertically centered within container (`align-items: center`)
- **Flow**: Left to right, horizontal flow
- **Max width**: 2.7in (full badge width minus margins)

#### Bottom Tags (Remaining 2-3 Tags + Optional Micro Badge)
- **Position**: `bottom: 0.15in, left: 0.15in`
- **Container**: `.tags-bottom` with fixed height 0.35in
- **Layout**: Flexbox with `justify-content: space-between`
- **Alignment**: Bottom-aligned (`align-items: flex-end`)
  - Standard tags: Left-aligned group (`.tags-group`)
  - Micro badge: Right-aligned (if present)
- **Max width**:
  - **With micro badge**: 2.25in for standard tags (micro badge takes 0.35in + 0.1in gap = 0.45in)
  - **Without micro badge**: 2.7in for standard tags
- **Gap between standard tags**: 0.04in-0.08in (dynamic, calculated per row)

**CRITICAL**: The bottom tags layout uses `space-between` to separate standard tags (left) from micro badge (right), with all tags bottom-aligned to the same baseline using `align-items: flex-end`.

#### Micro Badge
- **Size**: 0.35in × 0.35in (circular)
- **Position**: Right side of `.tags-bottom` container
- **Purpose**: Compact representation of short values (e.g., "2-4", "20+", "VIP")
- **Font**: 8pt bold, centered text
- **Layout**: Part of same flex container as standard tags, using `space-between` for separation

### Auto-Shrink Algorithm

**Purpose**: Ensure tags fit within available width without truncating text by progressively reducing visual properties.

**Strategy**: The Python renderer (`badge_renderer_html.py`) calculates optimal styling before HTML generation. Tags progressively reduce in this order:

1. **Gap** (space between tags): 0.08in → 0.06in → 0.04in
2. **Padding** (horizontal): 0.12in → 0.10in → 0.08in
3. **Font size**: 8pt → 7.5pt → 7pt

**Safety factor**: 93% of max width to account for font rendering variations across systems.

**Example calculation** (3 tags with values "Committee", "Years as Member", "Industry"):
```python
for font_size in [8, 7.5, 7]:
    for padding_h in [0.12, 0.10, 0.08]:
        for gap in [0.08, 0.06, 0.04]:
            text_widths = [calculate_width(value, font_size) for value in tag_values]
            tag_widths = [w + (2 * padding_h) for w in text_widths]
            total_width = sum(tag_widths) + (gap * (len(tags) - 1))

            if total_width <= (max_width * 0.93):
                return {'font_size': font_size, 'padding_h': padding_h, 'gap': gap}
```

**Implementation**:
- Calculations in `badge_renderer_html.py`: `_calculate_tag_row_styling()`
- Applied via inline styles in `template.html`: `style="font-size: {{ top_tag_styling.font_size }}pt; ..."`
- Top tags and bottom tags calculated independently with different max widths

### CRITICAL CSS Requirements

⚠️ **DO NOT MODIFY THESE CSS PROPERTIES** - They are essential for the auto-shrink algorithm to work correctly:

```css
.tag {
  flex-shrink: 0; /* CRITICAL: Prevents browser from overriding Python calculations */
  /* DO NOT add: min-width: 0; - This allows browser to shrink tags infinitely */
}
```

**Why this matters**:
- Without `flex-shrink: 0`, the browser's flexbox algorithm will shrink tags below their calculated size, causing text truncation even when there's available space
- The browser doesn't know about the 93% safety factor and will aggressively shrink to fit 100% width
- Setting `flex-shrink: 0` ensures tags respect their Python-calculated dimensions
- This was the root cause of the "tags truncating with plenty of room" bug

**What NOT to do**:
- ❌ `flex-shrink: 1` - Allows browser to shrink tags unpredictably
- ❌ `min-width: 0` - Tells browser tags can shrink to zero width
- ❌ Fixed CSS gap values - Must use dynamic `style="gap: {{ bottom_tag_styling.gap }}in;"`

### Tag Quantity Guidelines
- **Optimal**: 3-5 tags total (3 top, 2 bottom)
- **Maximum**: 8 tags before visual crowding occurs
- **Overflow strategy**:
  - Prioritize top 3 tags (most important categorical info)
  - Limit bottom tags to 2-3 (+ optional micro badge)
  - If more tags exist, truncate with ellipsis or "+" indicator
  - Consider abbreviating long tag values at data level

### Tag Color System
**Important**: Tag colors are **custom per event**, not predefined globally.

#### How Colors Work
1. Each event defines `tag_categories` in `events.json`
2. Each category has a custom `color` (hex code)
3. Colors are chosen to match event branding and template color palette
4. Example from Ohio Business Meetup:
   - Role: `#E07A5F` (warm orange)
   - Years as Member: `#81B29A` (teal)
   - Rep: `#F2CC8F` (golden yellow)

#### Color Selection Guidelines
When choosing tag colors for a new event:
1. **Use template palette colors**: Draw from the event's `colorPalette` in template.json
2. **Ensure contrast**: Maintain 4.5:1 contrast ratio with white text (WCAG AA)
3. **Avoid similar adjacents**: Don't use visually similar colors for adjacent tag categories
4. **Test at scale**: Print test badge to verify readability
5. **Fallback color**: If color undefined, system uses `#E07A5F` (warm orange)

#### Technical Implementation
- Colors defined in `events.json`: `tag_categories[].color`
- Rendered via `badge_renderer_html.py`: Builds `tag_color_map`
- Applied in template: `style="background-color: {{ tag_colors.get(category_key, '#E07A5F') }}"`
- Text color: Always white (`#FFFFFF`)

### Tag Behavior
- **No wrapping**: `white-space: nowrap` prevents text wrapping
- **No browser shrinking**: `flex-shrink: 0` prevents layout shifts
- **Overflow**: Auto-shrink algorithm prevents overflow; if all reduction steps exhausted, text may truncate
- **Positioning**: Absolute positioning prevents layout shifts

---

## 4. Interests Illustration Integration

The interests illustration is a critical visual element that connects attendees through their hobbies and passions.

### Physical Specifications
- **Size**: 2.7in × 1.35in (2:1 aspect ratio)
- **Position**:
  - Left edge: 0.15in from badge left
  - Bottom edge: 0.53in from badge bottom
  - Spans horizontally across full badge width (minus margins)
- **Corner radius**: 0.08in (consistent with tags)
- **No border**: Border removed for cleaner aesthetic

### Spacing Relationships
- **Above bottom tags**: 0.38in gap (0.53in - 0.15in)
- **Below professional info**: ~0.42in gap (flexible based on title/company height)
- **Side margins**: 0.15in from left/right edges

### Connection to AI Generation Prompt
The interests illustration is generated using an AI prompt with explicit consistency rules (see `scripts/generate_ai_prompts.py`):

**Key prompt rules that affect layout:**
1. **Equal padding**: ~80-100px margins on all sides of illustration
2. **2:1 aspect ratio**: Generated at 1536×1024px, cropped to 2:1
3. **Vertical staggering**: Elements at different heights (not single horizontal line)
4. **Consistent visual treatment**: Same stroke weights, corner rounding, detail level
5. **One element per interest**: Equal visual weight for all interests
6. **Color palette enforcement**: Uses only template colors

### Image Processing Pipeline
1. **Generate**: Azure OpenAI creates 1536×1024 horizontal image
2. **Normalize background**: Convert near-white pixels to pure white (#FFFFFF)
3. **Smart crop**: Remove dead space while maintaining 2:1 ratio
4. **Output**: Saved at `output/working/{event_id}/{user_id}/generated_images/interests_illustration.png`

### Visual Integration Guidelines
- **Maintain aspect ratio**: Always 2:1, no stretching or distortion
- **Consistent positioning**: Same position regardless of other badge content
- **No overlap**: Z-index lower than social/QR code to avoid conflicts
- **Graceful degradation**: If image missing, show error (images are required)

---

## 5. Layout Rules & Element Positioning

### Badge Dimensions
- **Physical size**: 3.0in × 4.0in (standard badge size)
- **Orientation**: Portrait (vertical)
- **Safe area**: 2.7in × 3.7in (after 0.15in margins)

### Z-Index Hierarchy
All overlay elements use `z-index: 10` to appear above the interests band:
- QR code (top-right): z-index 10
- Location graphic/text: z-index 10
- Tags (top and bottom): z-index 10
- Social media section: z-index 10
- Event logo: z-index 10
- Interests band: z-index 0 (base layer)

### Element Positioning Rules

#### Event Header
- **Position**: `top: 0.15in`, spans full width
- **Height**: ~0.5in
- **Components**: Event logo (left), event title (center), QR code (right)

#### QR Code
- **Size**: 0.5in × 0.5in
- **Position**: `top: 0.15in, right: 0.15in`
- **Content**: Links to attendee profile URL

#### Name
- **Position**: `top: 1.15in, left: 0.15in`
- **Max width**: 2.7in
- **Font**: 18pt bold (adaptive sizing)

#### Location Section
- **Graphic mode** (current implementation):
  - **Map graphic**: 0.4in × 0.4in at `left: 0.15in, top: 1.45in`
  - **Label text**: 5pt at `top: 1.87in` (under graphic)
- **Text mode** (alternative, currently unused):
  - **Full location**: 9pt at `top: 1.95in`

#### Title/Company Container
- **Position**: `left: 0.55in, top: 1.45in` (to right of location graphic)
- **Max width**: 2.3in (accommodates graphic on left)

#### Social Media Section
- **Position**: `bottom: 0.15in, right: 0.15in` (bottom-right anchor)
- **Components**: Social icon (0.25in × 0.25in) + handle text (7pt)
- **Gap**: 0.08in between icon and text
- **Max width**: ~2in (to avoid overlap with bottom tags)

### Collision Detection Rules
- **Title overflow**: If title wraps to 2 lines and would overlap location graphic, graphic shifts right by 0.1in
- **Social overlap**: If social handle exceeds 2in width, truncate with ellipsis
- **Tag overflow**: If 6+ bottom tags exist, consider wrapping to second row or truncating

---

## 6. Fallback Behavior for Missing Data

The badge system gracefully handles missing or optional data fields. See also [DATA_CONSTRAINTS.md, Section 8](DATA_CONSTRAINTS.md#8-graceful-degradation--fallback-behavior) for data-level fallback rules.

### Required vs Optional Elements

#### Always Present (Required)
- Name
- Event header (logo + title + QR code)

#### Optional (May Be Missing)
- Title
- Company
- Location
- Interests illustration (currently required but could be made optional)
- Social media handle/icon
- Tags (both top and bottom)

### Layout Behavior When Elements Are Missing

#### Missing Title
- Company moves up to take title's vertical position
- Gap between name and company reduces from 0.1in to 0.05in
- Location graphic remains at same position

#### Missing Company
- Title remains at normal position
- No gap collapse (maintains spacing consistency)

#### Missing Location
- Location graphic and label removed
- Title/company container expands to full width (2.7in instead of 2.3in)
- Moves left to `left: 0.15in` (no longer offset for graphic)

#### Missing Social Media
- Social icon and handle removed
- Bottom-right corner remains empty
- Bottom tags do not shift right (maintains consistent positioning)

#### Missing Tags
- **No top tags**: Gap between event header and name increases
- **No bottom tags**: Interests band appears to "float" with more space below
- **No tags at all**: Cleaner, more minimal design (still valid)

#### Missing Interests Illustration
- **Current behavior**: Shows error (images are required)
- **Potential graceful fallback**: Could collapse space, move bottom tags up by 1.73in (band height + gap)

### Minimal Valid Badge
The absolute minimum badge contains:
- Event header (logo + title + QR code)
- Name

All other elements can be gracefully omitted without breaking layout.

### Maintaining Visual Balance
When multiple sections are missing:
1. **Preserve vertical rhythm**: Don't let elements "float" - maintain consistent gaps
2. **Center sparse content**: If badge is very sparse, consider centering name vertically
3. **No empty space stretching**: Collapse gaps between missing sections rather than stretching

---

## 7. Accessibility Standards

### Viewing Distance Optimization
- **Primary viewing distance**: 2-3 feet (networking/conversation distance)
- **Secondary viewing distance**: 6-10 feet (across-the-room identification)
- **Name must be readable**: At 6-10 feet (hence 18pt minimum size)

### Minimum Font Sizes
- **5pt**: Absolute minimum for supplementary labels (location label, sponsor text)
- **7pt**: Minimum for tertiary information (social handle)
- **8pt**: Minimum for categorical information (tags)
- **10pt+**: Required for primary content (name, title, company)

### Color Contrast Requirements
All text must meet WCAG AA standards:
- **Body text (< 18pt)**: 4.5:1 contrast ratio minimum
- **Large text (≥ 18pt)**: 3.0:1 contrast ratio minimum

#### Current Contrast Ratios
- **Navy (#3D405B) on white**: 9.5:1 ✓ (exceeds AA)
- **White (#FFFFFF) on tag colors**: Must verify per event
  - Warm orange (#E07A5F): 3.2:1 ✗ (fails for body text, acceptable for tags only if considered "large")
  - Teal (#81B29A): 2.8:1 ✗ (fails, requires darker shade)
  - Golden yellow (#F2CC8F): 1.8:1 ✗ (fails, requires much darker shade)

**Recommendation**: When selecting tag colors, use online contrast checkers (e.g., WebAIM) to verify 4.5:1 ratio with white text. Consider darkening colors by 20-30% if needed.

### Physical Accessibility
- **Tactile elements**: QR code provides digital alternative to reading badge
- **Large text**: Name at 18pt assists readers with low vision
- **High contrast**: Navy on white ensures readability in various lighting

### Print Considerations
- **Resolution**: 288 DPI for crisp text at small sizes
- **Color profiles**: Test print with event's specific tag colors
- **Paper quality**: Matte finish reduces glare, improves readability

---

## 8. Visual Consistency Checklist

This checklist mirrors the explicit consistency rules in the interests illustration AI prompt, ensuring the entire badge system maintains unified visual standards.

### Typography Consistency
- [ ] All text uses documented font sizes from hierarchy
- [ ] Line heights follow standards (1.2 for multi-line, 1.0 for labels)
- [ ] Font weights are consistent (bold for name/events, medium for tags, regular elsewhere)
- [ ] Color usage follows semantic meaning (navy for primary, teal for company, gray for supporting)

### Spacing Consistency
- [ ] All margins are 0.15in (badge edges)
- [ ] Element gaps use base spacing units (0.05in, 0.08in, 0.15in, 0.33in+)
- [ ] Vertical rhythm is maintained between sections
- [ ] Related elements are tightly grouped (< 0.15in gaps)

### Color Consistency
- [ ] Tag colors are drawn from template color palette
- [ ] All tag colors meet 4.5:1 contrast with white text
- [ ] Company name color coordinates with template secondary color
- [ ] No arbitrary color choices (all colors have documented purpose)

### Element Consistency
- [ ] All rounded corners use 0.08in radius (tags, interests band)
- [ ] All icons are same visual treatment (solid color, consistent size)
- [ ] Tags have consistent height (0.3in) and padding (0.08in × 0.06in)
- [ ] Z-index hierarchy is respected (all overlays at z-index 10)

### Interests Illustration Consistency
Following rules from `generate_ai_prompts.py`:
- [ ] 2:1 aspect ratio maintained (2.7in × 1.35in)
- [ ] Equal padding on all four sides (~80-100px in source image)
- [ ] Elements vertically staggered (not single horizontal line)
- [ ] Consistent stroke weights across all elements (4-6px)
- [ ] One element per interest (equal visual weight)
- [ ] Uses only template color palette
- [ ] Pure white background (#FFFFFF)

### Layout Consistency
- [ ] Elements positioned at documented coordinates
- [ ] No overlap between elements (unless intentional with z-index)
- [ ] Graceful degradation when optional elements missing
- [ ] Minimum margins respected (no elements touch badge edges)

### Quality Assurance
- [ ] Print test badge at actual size (3" × 4")
- [ ] Verify readability at 2-3 feet
- [ ] Check QR code scans reliably
- [ ] Confirm all text is legible (no blurry rendering)
- [ ] Test with minimal data (name only) and maximal data (all fields)

---

## Revision History

- **2025-01-17**: Initial creation - Comprehensive design system documentation
  - Documented typography hierarchy, spacing system, tag system
  - Integrated interests illustration specifications
  - Defined layout rules, fallback behavior, accessibility standards
  - Created visual consistency checklist
