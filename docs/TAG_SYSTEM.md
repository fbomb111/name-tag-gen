# Tag System Reference

**Complete technical reference for the badge tag layout system, auto-shrink algorithm, and troubleshooting guide.**

This document provides detailed implementation notes for developers working on the tag system. For high-level design principles, see [DESIGN.md](DESIGN.md).

---

## Table of Contents
1. [System Overview](#1-system-overview)
2. [Tag Layout Architecture](#2-tag-layout-architecture)
3. [Auto-Shrink Algorithm](#3-auto-shrink-algorithm)
4. [Critical CSS Constraints](#4-critical-css-constraints)
5. [Micro Badge Integration](#5-micro-badge-integration)
6. [Common Issues & Troubleshooting](#6-common-issues--troubleshooting)
7. [Testing Guidelines](#7-testing-guidelines)

---

## 1. System Overview

### Architecture
The tag system uses a hybrid Python + CSS approach:
- **Python** (`badge_renderer_html.py`): Calculates optimal dimensions before HTML generation
- **Jinja2 templates** (`template.html`): Applies calculated values via inline styles
- **CSS** (`styles.css`): Provides layout structure and default values

### Key Design Decision: Why Python Calculations?
Tags cannot be reliably auto-sized using pure CSS because:
1. CSS has no way to measure text width before rendering
2. WeasyPrint (PDF generator) has different font metrics than browsers
3. We need pixel-perfect control for print layouts at 3"×4" physical size

### Data Flow
```
Event data (events.json)
    ↓
Python: Calculate optimal font-size, padding, gap
    ↓
Jinja2: Render HTML with inline styles
    ↓
WeasyPrint: Generate PDF
    ↓
Physical badge printed at 3"×4"
```

---

## 2. Tag Layout Architecture

### Container Structure

```html
<!-- Top Tags -->
<div class="tags-top">
  <span class="tag" style="...inline styles...">Tag 1</span>
  <span class="tag" style="...inline styles...">Tag 2</span>
</div>

<!-- Bottom Tags -->
<div class="tags-bottom">                    <!-- Parent flex container -->
  <div class="tags-group" style="gap: ...">  <!-- Standard tags on left -->
    <span class="tag" style="...">Tag 3</span>
    <span class="tag" style="...">Tag 4</span>
  </div>
  <span class="micro-badge-identity">VIP</span>  <!-- Micro badge on right -->
</div>
```

### Layout Specifications

| Element | Position | Width | Height | Alignment |
|---------|----------|-------|--------|-----------|
| `.tags-top` | `top: 0.85in` | 2.7in | 0.22in (fixed) | Vertical center |
| `.tags-bottom` | `bottom: 0.15in` | 2.7in | 0.35in (fixed) | Bottom (`flex-end`) |
| `.tags-group` | Inside `.tags-bottom` | Variable | Inherit | Bottom (`flex-end`) |
| `.tag` | Inline within parents | Auto-calculated | Auto | N/A |
| `.micro-badge-identity` | Right side of `.tags-bottom` | 0.35in | 0.35in | Bottom |

### Bottom Tags Layout Behavior

**Flexbox Properties:**
```css
.tags-bottom {
  display: flex;
  justify-content: space-between;  /* Pushes micro badge to right */
  align-items: flex-end;            /* Bottom-aligns all children */
}

.tags-group {
  display: flex;
  gap: [dynamic];                   /* Calculated by Python */
  align-items: flex-end;            /* Match parent alignment */
}
```

**Result:**
- Standard tags group on left side
- Micro badge (if present) on right side
- All tags aligned to same bottom baseline
- Visual gap between groups created by `space-between`

---

## 3. Auto-Shrink Algorithm

### Purpose
Ensure tags fit within available width without text truncation by progressively reducing visual properties.

### Implementation Location
`src/renderers/badge_renderer_html.py`: `_calculate_tag_row_styling()`

### Algorithm Steps

1. **Calculate safe max width**
   ```python
   safety_factor = 0.93  # 93% of available width
   safe_max_width = max_width * safety_factor
   ```

   The 93% safety factor accounts for:
   - Font rendering variations between systems
   - Bold/semibold weight making text slightly wider
   - PDF generation edge cases in WeasyPrint

2. **Progressive reduction order**
   - **Gap** (space between tags): 0.08in → 0.06in → 0.04in
   - **Padding** (horizontal): 0.12in → 0.10in → 0.08in
   - **Font size**: 8pt → 7.5pt → 7pt

3. **Try all combinations**
   ```python
   for font_size in [8, 7.5, 7]:
       for padding_h in [0.12, 0.10, 0.08]:
           for gap in [0.08, 0.06, 0.04]:
               # Calculate total width with these values
               if total_width <= safe_max_width:
                   return {'font_size': font_size, 'padding_h': padding_h, 'gap': gap}
   ```

   This creates 27 possible combinations (3×3×3). The algorithm returns the **first** combination that fits, preferring larger sizes.

4. **Fallback**
   If no combination fits (rare), return most aggressive shrinking:
   ```python
   {'font_size': 7, 'padding_h': 0.08, 'gap': 0.04}
   ```

### Width Calculation Details

```python
# For each tag:
text_width_pts = pdfmetrics.stringWidth(tag_text, "Helvetica", font_size)
text_width_in = text_width_pts / 72.0  # Convert points to inches
tag_width = (padding_h * 2) + text_width_in

# Total row width:
total_width = sum(all_tag_widths) + (gap * (num_tags - 1))
```

### Independent Calculations

**Top tags and bottom tags are calculated independently:**
- **Top tags**: Always use `max_width = 2.7` (full width)
- **Bottom tags**: Use `max_width = 2.25` if micro badge present, else `2.7`

This means top tags might use different sizing than bottom tags on the same badge.

---

## 4. Critical CSS Constraints

### The `flex-shrink: 0` Requirement

**Location:** `config/html_templates/professional/styles.css` line 176

```css
.tag {
  flex-shrink: 0; /* ⚠️ CRITICAL - DO NOT CHANGE */
}
```

**Why this is critical:**

Without `flex-shrink: 0`, the browser's flexbox algorithm will shrink tags to fit the container, **completely overriding Python calculations**. Here's what happens:

1. Python calculates tag needs 1.2in width
2. Python applies `width: 1.2in` via inline style
3. Browser sees flex container is slightly too narrow
4. Browser applies `flex-shrink: 1` (default) and shrinks tag to 1.0in
5. Text truncates with ellipsis even though there's room

**The bug we fixed:**

Before fix:
```css
.tag {
  flex-shrink: 1;        /* ❌ Browser overrides Python calculations */
  min-width: 0;          /* ❌ Allows infinite shrinking */
}
```

After fix:
```css
.tag {
  flex-shrink: 0;        /* ✅ Browser respects Python calculations */
  /* min-width removed */ /* ✅ No shrinking allowed */
}
```

### Dynamic vs Static Values

| Property | Source | Notes |
|----------|--------|-------|
| `font-size` | **Inline style** (Python) | CSS value is default only |
| `padding` (horizontal) | **Inline style** (Python) | CSS value is default only |
| `padding` (vertical) | CSS static | Always 0.06in |
| `gap` (between tags) | **Inline style** (Python) | CSS value is default only |
| `margin-right` (top tags) | **Inline style** (Python) | Used instead of gap for top tags |
| `background-color` | **Inline style** (event config) | Per-event custom colors |
| `border-radius` | CSS static | Always 0.08in |
| `line-height` | CSS static | Always 1.0 |

**Key principle:** Properties that affect width MUST be inline styles from Python. Layout properties can be static CSS.

---

## 5. Micro Badge Integration

### What is a Micro Badge?
A circular tag (0.35in diameter) for compact values like:
- Numeric ranges: "2-4", "5-9", "20+"
- Short codes: "VIP", "NEW"
- Single characters: "A", "1"

### Configuration
In `events.json`:
```json
{
  "name": "Years as Member",
  "type": "select",
  "display_type": "micro",           // ← This makes it a micro badge
  "values": ["1st", "2-4", "5-9", "10-19", "20+"],
  "color": "#81B29A"
}
```

### Character Limits
- **Optimal**: 2-3 characters
- **Maximum**: 4 characters (5 char limit enforced in code)
- Examples that fit: "VIP", "20+", "NEW", "1st"
- Examples too long: "STAFF" (5 chars), "SPONSOR" (7 chars)

### Width Reservation

When a micro badge exists, bottom tags have **reduced width**:

```python
# badge_renderer_html.py lines 491-501
bottom_max_width = 2.25 if micro_badge else 2.7
```

**Calculation:**
- Total badge width (minus margins): 2.7in
- Micro badge circle: 0.35in
- Implicit gap from `space-between`: ~0.10in
- Available for standard tags: 2.7 - 0.45 = **2.25in**

### Layout Mechanics

The micro badge uses the same flex container as standard tags:

```html
<div class="tags-bottom">               <!-- justify-content: space-between -->
  <div class="tags-group">...</div>     <!-- Standard tags pushed left -->
  <span class="micro-badge-identity">   <!-- Micro badge pushed right -->
    VIP
  </span>
</div>
```

The `space-between` property creates the visual gap. No explicit margin needed.

---

## 6. Common Issues & Troubleshooting

### Issue 1: Tags Truncating Despite Available Space

**Symptoms:**
- Tags show ellipsis ("Committee...")
- Visual inspection shows plenty of room
- Happens even after auto-shrink runs

**Root cause:** CSS has `flex-shrink: 1` or `min-width: 0`, allowing browser to override Python calculations.

**Fix:**
```css
.tag {
  flex-shrink: 0;  /* ✅ Must be 0 */
}
/* Remove min-width: 0 if present */
```

**Verification:**
1. Inspect tag element in browser/PDF
2. Check computed `flex-shrink` value (should be 0)
3. Check if width matches inline style value

---

### Issue 2: Bottom Tags Not Bottom-Aligned

**Symptoms:**
- Tags vertically centered instead of bottom-aligned
- Micro badge at different baseline than standard tags

**Root cause:** `align-items` not set to `flex-end` on parent or child containers.

**Fix:**
```css
.tags-bottom {
  align-items: flex-end;  /* ✅ Bottom align all children */
}

.tags-group {
  align-items: flex-end;  /* ✅ Match parent alignment */
}
```

**Verification:**
1. Inspect `.tags-bottom` computed styles
2. Verify `align-items: flex-end`
3. Check that all tags touch same baseline

---

### Issue 3: Micro Badge Not Right-Aligned

**Symptoms:**
- Micro badge appears next to standard tags, not on right edge
- All tags grouped together on left

**Root cause:** Parent container missing `justify-content: space-between`.

**Fix:**
```css
.tags-bottom {
  justify-content: space-between;  /* ✅ Separate standard tags from micro badge */
}
```

**Verification:**
1. Check `.tags-bottom` computed styles
2. Verify `justify-content: space-between`
3. Visual check: micro badge should be at right edge

---

### Issue 4: Gap Not Applied Correctly

**Symptoms:**
- Tags too close together or too far apart
- Spacing doesn't match auto-shrink calculations

**Root cause:** Gap applied via static CSS instead of inline style.

**Fix in template.html:**
```html
<!-- ✅ Correct: Dynamic gap from Python -->
<div class="tags-group" style="gap: {{ bottom_tag_styling.gap }}in;">

<!-- ❌ Wrong: Static CSS gap -->
<div class="tags-group">  <!-- Relies on CSS .tags-group { gap: 0.08in; } -->
```

**Verification:**
1. Inspect `.tags-group` inline styles
2. Verify `style="gap: 0.04in;"` (or 0.06in/0.08in)
3. Gap should vary per badge based on tag widths

---

### Issue 5: Bottom Tags Wrapper Not Rendering

**Symptoms:**
- Template has bottom tags but `.tags-group` div is missing
- Tags render without flexbox grouping

**Root cause:** Incorrect Jinja2 condition checking for tags.

**Fix:**
```jinja2
<!-- ✅ Correct: Check if slice has elements -->
{% if tag_metadata[2:] %}

<!-- ❌ Wrong: Check length > 2 (fails when exactly 3 tags) -->
{% if tag_metadata and tag_metadata|length > 2 %}
```

**Why this matters:** `tag_metadata[2:]` returns a list slice. An empty slice is falsy, a non-empty slice is truthy. The `length > 2` check fails when there are exactly 3 total tags (first 2 are top tags, 1 remaining for bottom).

**Verification:**
1. Test with exactly 3 tags total
2. Verify `.tags-group` div renders in HTML
3. Check flexbox layout applies correctly

---

## 7. Testing Guidelines

### Test Cases for Auto-Shrink

**Test 1: Optimal sizing (no shrinking needed)**
- Input: 3 short tags ["VIP", "New", "Staff"]
- Expected: `font_size: 8, padding_h: 0.12, gap: 0.08` (defaults)

**Test 2: Gap reduction only**
- Input: 3 medium tags ["Committee", "Industry", "Member"]
- Expected: `font_size: 8, padding_h: 0.12, gap: 0.04` (gap reduced)

**Test 3: Padding reduction**
- Input: 3 long tags ["Innovation Council", "Small Business", "Corporate"]
- Expected: `font_size: 8, padding_h: 0.08, gap: 0.04` (gap + padding reduced)

**Test 4: Font size reduction**
- Input: 3 very long tags ["Chamber of Commerce Board", "Government Affairs", "Logistics"]
- Expected: `font_size: 7, padding_h: 0.08, gap: 0.04` (all reductions applied)

**Test 5: Micro badge width reservation**
- Input: 2 long bottom tags + micro badge
- Expected: `max_width = 2.25` used for calculations (not 2.7)

### Visual Test Cases

**Print Test Checklist:**
1. [ ] Print badge at actual 3"×4" size
2. [ ] Verify no tag text is truncated
3. [ ] Measure physical spacing with ruler
4. [ ] Check bottom tags aligned to same baseline
5. [ ] Verify micro badge is right-aligned
6. [ ] Check gap between standard tags and micro badge (~0.1in)
7. [ ] Confirm text is readable at 2-3 feet

### Edge Cases to Test

1. **Single tag:** Should use defaults, no shrinking
2. **Two tags with very long text:** Should shrink appropriately
3. **Three short tags:** Should not shrink at all
4. **Micro badge alone (no standard bottom tags):** Should render on right side
5. **No tags at all:** Containers should not render
6. **Exactly 3 total tags:** Bottom wrapper should render for 1 bottom tag

### Regression Test: "Plenty of Room" Bug

**Reproduce the bug we fixed:**
1. Set CSS: `.tag { flex-shrink: 1; min-width: 0; }`
2. Generate badge with tags ["Committee", "Years: 2-4"]
3. Observe: Tags truncate even with available space

**Verify fix:**
1. Set CSS: `.tag { flex-shrink: 0; }` (remove min-width)
2. Generate same badge
3. Observe: Tags render at full width, no truncation

---

## Quick Reference: Files & Line Numbers

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| Auto-shrink algorithm | `src/renderers/badge_renderer_html.py` | 191-258 | Calculates optimal sizing |
| Bottom width reservation | `src/renderers/badge_renderer_html.py` | 486-501 | Reduces width for micro badge |
| Tag CSS constraints | `config/html_templates/professional/styles.css` | 98-217 | Layout structure |
| Critical flex-shrink | `config/html_templates/professional/styles.css` | 176 | Prevents browser override |
| Top tags template | `config/html_templates/professional/template.html` | 29-43 | Renders top 2 tags |
| Bottom tags template | `config/html_templates/professional/template.html` | 45-81 | Renders bottom tags + micro badge |
| Tag configuration | `mocks/events.json` | Varies | Event-specific tag definitions |

---

## Additional Resources

- **[DESIGN.md](DESIGN.md)**: High-level design principles and visual standards
- **[DATA_CONSTRAINTS.md](DATA_CONSTRAINTS.md)**: Data validation and character limits
- **CSS Comments**: Inline documentation in `styles.css` explaining critical properties
- **Python Docstrings**: Detailed algorithm notes in `badge_renderer_html.py`

---

## Revision History

- **2025-01-17**: Initial creation - Complete tag system technical reference
  - Documented auto-shrink algorithm, critical CSS constraints, micro badge integration
  - Created troubleshooting guide for common issues
  - Added testing guidelines and edge case coverage
