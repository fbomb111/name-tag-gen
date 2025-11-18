# Edge Case Testing Catalog

This document catalogs all edge cases that must be tested to ensure the badge generation system handles real-world data variations gracefully and professionally.

## Overview

The system must handle **70+ edge cases** across multiple dimensions: names, locations, titles, interests, social media, tags, events, and rendering. This document organizes edge cases by category, priority level, and maps them to specific test users.

---

## Edge Case Categories

1. [Name Edge Cases](#1-name-edge-cases)
2. [Location Edge Cases](#2-location-edge-cases)
3. [Job Title Edge Cases](#3-job-title-edge-cases)
4. [Company Name Edge Cases](#4-company-name-edge-cases)
5. [Interests Edge Cases](#5-interests-edge-cases)
6. [Social Media Edge Cases](#6-social-media-edge-cases)
7. [Tag Edge Cases](#7-tag-edge-cases)
8. [Event Edge Cases](#8-event-edge-cases)
9. [Image & QR Code Edge Cases](#9-image--qr-code-edge-cases)
10. [Rendering Edge Cases](#10-rendering-edge-cases)
11. [Unicode & International Edge Cases](#11-unicode--international-edge-cases)
12. [Null/Missing Data Edge Cases](#12-nullmissing-data-edge-cases)

---

## 1. Name Edge Cases

### 1.1 Length Variations

| Edge Case | Description | Test User | Expected Behavior |
|-----------|-------------|-----------|-------------------|
| **Very short name** | 5-10 characters | `user_003` (Bo Yi) | Render at full 18pt font |
| **Short name** | 10-20 characters | `user_001` (Sarah Chen) | Render at full 18pt font |
| **Medium name** | 20-40 characters | `user_005` (Priya Kowalski) | Render at 18pt or slightly smaller |
| **Long name** | 40-60 characters | `user_008` (Srinivasa Ramanujan Krishnamurthy) | Font shrink to ~14pt |
| **Very long name** | 60-90 characters | `user_020` (Dr. Anastasia Alexandrovna...) | Font shrink to 12pt, may abbreviate |
| **Extreme long name** | 90-100 characters | `user_021` (Name at exact boundary) | Shrink to 12pt, abbreviate surname |
| **Over limit** | 101+ characters | N/A (form validation) | Hard reject at form submission |

### 1.2 Format Variations

| Edge Case | Description | Test User | Expected Behavior |
|-----------|-------------|-----------|-------------------|
| **Mononym** (single name) | "Cher", "Madonna" | `user_002` (Cher) | Render as-is, no truncation needed |
| **Hyphenated first name** | Mary-Kate | `user_018` (Mary-Kate O'Connor-Smith) | Render with hyphen intact |
| **Hyphenated last name** | García-Fernández | `user_015` (María García-Hernández) | May abbreviate to "García-H." if needed |
| **Multiple hyphens** | Smith-Jones-Williams | `user_022` | Abbreviate progressively |
| **Apostrophe in name** | O'Connor, D'Angelo | `user_007` (Sean O'Connor) | Render apostrophe correctly |
| **Name with period** | J.R.R. Tolkien | `user_024` (J.D. Martinez) | Render periods intact |
| **Suffix** | Jr., III, PhD | `user_020` (... III, PhD) | Include suffix, may truncate if needed |
| **Title prefix** | Dr., Prof. | `user_020` (Dr. Anastasia...) | Include title, may remove if space needed |

### 1.3 Cultural Name Formats

| Edge Case | Description | Test User | Expected Behavior |
|-----------|-------------|-----------|-------------------|
| **Eastern name order** | Family name first | `user_012` (Zhang Wei) | Render as provided by user |
| **Patronymic** | Mikhailovna | `user_016` (Anastasia Mikhailovna Kovalenko) | May remove patronymic if truncating |
| **Arabic naming** | bin Mohammed, Al-Sayed | `user_011` (Abdul Rahman bin Mohammed Al-Sayed) | Render full name, abbreviate if needed |
| **Spanish double surname** | García de la Cruz | `user_015` (María García-Hernández) | Render both surnames |

### 1.4 Special Characters

| Edge Case | Description | Test User | Expected Behavior |
|-----------|-------------|-----------|-------------------|
| **Latin accents** | ñ, ü, ø, å | `user_015` (María) | Render accents correctly |
| **Diacritics** | Björk, São | `user_014` (Björk) | Render diacritics correctly |
| **Extra whitespace** | "John  Smith" (double space) | `user_025` (whitespace test) | Normalize to single space |
| **Leading/trailing space** | " Jane Doe " | `user_025` | Trim whitespace |

---

## 2. Location Edge Cases

### 2.1 Length Variations

| Edge Case | Description | Test User | Expected Behavior |
|-----------|-------------|-----------|-------------------|
| **Very short** | "LA", "NYC" | `user_006` (LA) | Render as-is |
| **Medium** | "San Francisco, CA" | `user_001` | Render as-is |
| **Long** | "Saint-Pierre-et-Miquelon, France" | `user_019` | Truncate with ellipsis if exceeds width |
| **Very long** | "Llanfairpwll...gogogoch, Wales" | `user_023` | Truncate with ellipsis |

### 2.2 Format Variations

| Edge Case | Description | Test User | Expected Behavior |
|-----------|-------------|-----------|-------------------|
| **US city, state** | Portland, OR | `user_001` | Render as-is |
| **US neighborhood** | Short North, Columbus, OH | `user_009` | Geocode to "Columbus, OH" or render as-is |
| **International city** | Barcelona, Spain | `user_010` | Render as-is |
| **Ambiguous location** | Springfield, Portland | `user_027` | Geocode or render as provided |
| **Special characters** | São Paulo, Brazil | `user_028` | Render special chars correctly |
| **Invalid location** | Atlantis, Lost Kingdom | `user_008` | Render as-is (geocoding fails gracefully) |
| **Null location** | null | `user_004` | Omit location field from badge |

### 2.3 Geocoding Edge Cases

| Edge Case | Description | Expected Behavior |
|-----------|-------------|-------------------|
| **API timeout** | Geocoding takes >5s | Use original input string |
| **API unavailable** | Network error | Use original input string |
| **No results** | Unknown location | Use original input string |
| **Multiple results** | Ambiguous (e.g., Springfield) | Use first result or original input |

---

## 3. Job Title Edge Cases

### 3.1 Length Variations

| Edge Case | Description | Test User | Expected Behavior |
|-----------|-------------|-----------|-------------------|
| **Very short** | "CEO", "VP", "CFO" | `user_006` (CEO) | Render as-is |
| **Medium** | "Software Engineer" | `user_001` | Render on 1 line |
| **Long (1 line)** | "Senior Vice President of Marketing" | `user_005` | Render on 1 line if fits, wrap to 2 if needed |
| **Very long (2 lines)** | "Senior Executive Vice President of..." | `user_017` (90+ chars) | Wrap to 2 lines, truncate overflow |
| **Exceeds 2 lines** | 150+ character title | `user_017` | Truncate at 2 lines (CSS line-clamp) |

### 3.2 Content Variations

| Edge Case | Description | Test User | Expected Behavior |
|-----------|-------------|-----------|-------------------|
| **C-level** | CEO, CTO, CMO, CFO | `user_006` (CEO) | Render as-is |
| **Entry-level** | Intern, Junior, Associate | `user_026` (Junior Developer) | Render as-is |
| **Creative/unusual** | "Chief Happiness Officer" | `user_029` | Render as-is |
| **Multi-role** | "Designer/Developer" | `user_030` (Designer/Developer & Consultant) | Render with special chars |
| **Special characters** | &, /, - in title | `user_030` | Render special chars correctly |
| **All caps** | "DIRECTOR OF OPERATIONS" | `user_031` | Render as-is (case preserved) |
| **Null title** | null | `user_004` | Omit title field from badge |

---

## 4. Company Name Edge Cases

### 4.1 Length Variations

| Edge Case | Description | Test User | Expected Behavior |
|-----------|-------------|-----------|-------------------|
| **Very short** | "IBM", "CNN", "BBC" | `user_006` (IBM) | Render as-is |
| **Medium** | "Northwestern Mutual" | `user_009` | Render as-is |
| **Long** | "Columbus Metropolitan Libraries" | `user_001` | Truncate with ellipsis if exceeds width |
| **Very long** | "International Business Machines..." | `user_032` | Truncate with ellipsis |

### 4.2 Content Variations

| Edge Case | Description | Test User | Expected Behavior |
|-----------|-------------|-----------|-------------------|
| **Special characters** | "AT&T", "Procter & Gamble" | `user_013` (AT&T / Warner Bros.) | Render &, /, etc. correctly |
| **Abbreviations** | "NASA", "FBI", "WHO" | `user_033` | Render as-is |
| **Self-employed** | "Self-Employed", "Freelance" | `user_005` | Render as-is |
| **Multiple names** | "Google / YouTube" | `user_013` | Render with separator |
| **Null company** | null | `user_004` | Omit company field from badge |

---

## 5. Interests Edge Cases

### 5.1 Count Boundaries

| Edge Case | Description | Test User | Expected Behavior |
|-----------|-------------|-----------|-------------------|
| **0 interests (null raw_interests)** | No raw_interests text | N/A | `interests_normalized: []`, no interests band |
| **0 interests (generic raw_interests)** | Raw text too generic to extract interests | `user_004` | `interests: []`, `interests_normalized: []`, no interests band |
| **1 interest** | Single item | `user_027` | AI may keep it or return [] if not distinctive |
| **2 interests** | Below min (3) | `user_010` (Below Minimum) | AI may keep both or return [] |
| **3 interests** | Minimum | `user_001`, `user_003` | Keep all 3 |
| **5-7 interests** | Mid-range | `user_005`, `user_007` | Keep all if distinctive |
| **8 interests** | Maximum | `user_009`, `user_011` | Exactly 8 after normalization |
| **9-14 interests** | Above max (before norm) | `user_018` (15 interests) | Normalize to 3-8 most distinctive |
| **15+ interests** | Many interests | `user_018` (Brand Overload) | Aggressive normalization to 8 max |

### 5.2 Normalization Testing (Brand → Generic)

| Brand/Celebrity | Normalized To | Test User | Visual Representation |
|-----------------|---------------|-----------|----------------------|
| "Nike running" | "Running" | `user_018` | Generic runner silhouette |
| "Cleveland Browns fan" | "Football fan" | `user_018` | Football helmet with team colors (no logos) |
| "Taylor Swift concerts" | "Pop music concerts" | `user_018` | Generic concert stage |
| "LeBron James fan" | "Basketball fan" | `user_018` | Basketball player silhouette |
| "Starbucks coffee" | "Coffee" | `user_018` | Generic coffee cup |
| "Apple products" | "Tech gadgets" | `user_018` | Generic smartphone/laptop |
| "CrossFit" | "Fitness training" | `user_021` | Generic gym equipment |
| "Peloton" | "Indoor cycling" | `user_021` | Stationary bike |
| "SoulCycle" | "Group fitness" | `user_021` | Fitness class scene |
| "Tesla owner" | "Electric vehicles" | `user_018` | Generic EV car |
| "Yankees fan" | "Baseball fan" | `user_022` | Baseball glove/bat |
| "Oprah's book club" | "Reading" | `user_023` | Generic books |
| "Netflix" | "Streaming entertainment" | `user_024` | TV/screen icon |

### 5.3 Content Variations

| Edge Case | Description | Test User | Expected Behavior |
|-----------|-------------|-----------|-------------------|
| **Niche hobbies** | "Competitive soap carving" | `user_028` | Normalize to generic craft/hobby |
| **Controversial** | Political, religious topics | `user_019` (Controversial) | Abstract to generic categories or omit |
| **Abstract concepts** | "Mindfulness", "Personal growth" | `user_025` | Keep as-is if visually representable |
| **Profession-adjacent** | "Coding at night" | `user_026` | Distinguish from professional title |
| **Very long interest** | "Parent of five amazing kids..." | `user_034` | Truncate or simplify to "Parent of 5 kids" |
| **Duplicate interests** | "Coffee" and "Coffee enthusiast" | `user_035` | Deduplicate to single "Coffee" |

### 5.4 raw_interests Text Length

| Edge Case | Description | Test User | Expected Behavior |
|-----------|-------------|-----------|-------------------|
| **Very short** | "I like cats." (11 chars) | `user_036` | Parse to simple interests array |
| **Medium** | 200-500 chars | Most users | Standard AI parsing |
| **Long** | 500-1000 chars | `user_018` | Parse and normalize to 3-8 items |
| **At limit** | Exactly 1000 chars | `user_037` | Parse successfully |
| **Over limit** | 1001+ chars | N/A | Hard reject at form |

---

## 6. Social Media Edge Cases

### 6.1 Handle Formats

| Edge Case | Description | Test User | Expected Behavior |
|-----------|-------------|-----------|-------------------|
| **With @** | "@username" | `user_009` (@katebizdev) | Render with @ |
| **Without @** | "username" | `user_001` (sarahchen) | Render without @ |
| **Very long** | 40-50 chars | `user_014` (@this_is_an_extremely_long...) | Render, may truncate if exceeds width |
| **Special chars** | Periods, underscores | `user_038` (@john.smith, @jane_doe_123) | Render special chars |
| **With numbers** | "@user12345" | `user_039` | Render as-is |
| **Multiple @** | "@@username" | `user_040` | Render as-is (user error) |

### 6.2 Platform Variations

| Edge Case | Description | Test User | Expected Behavior |
|-----------|-------------|-----------|-------------------|
| **LinkedIn** | linkedin (no @) | `user_001` | Render with LinkedIn icon |
| **Twitter** | twitter | `user_009` | Render with Twitter/X icon |
| **Instagram** | instagram | `user_005` | Render with Instagram icon |
| **Facebook** | facebook | `user_011` | Render with Facebook icon |
| **GitHub** | github | `user_012` | Render with GitHub icon |
| **TikTok** | tiktok | `user_041` | Render with TikTok icon if available |
| **YouTube** | youtube | `user_042` | Render with YouTube icon if available |
| **Unknown platform** | "myspace" | `user_043` | Skip social media rendering |

### 6.3 Null/Missing

| Edge Case | Description | Test User | Expected Behavior |
|-----------|-------------|-----------|-------------------|
| **No social media** | Both fields null | `user_004` | Omit social media section |
| **Platform but no handle** | Platform set, handle null | `user_044` | Render icon only, no handle text |
| **Handle but no platform** | Handle set, platform null | `user_045` | Omit social media section |

---

## 7. Tag Edge Cases

### 7.1 Count & Layout

| Edge Case | Description | Test Event | Expected Behavior |
|-----------|-------------|------------|-------------------|
| **No tags** | Empty tags object | `minimal_event` | Omit tag sections |
| **1 tag** | Single tag | `user_046` | Render single tag |
| **3 tags** | Standard | Most users | 3 tags at top |
| **5 tags** | Current max | `user_001`, `user_009` | 3 at top, 2 at bottom |
| **8 tags** | High count | `user_047` in `tag_overload` event | Test overflow behavior |
| **10+ tags** | Extreme | `user_048` | Overflow or truncate |

### 7.2 Tag Text Length

| Edge Case | Description | Test User | Expected Behavior |
|-----------|-------------|-----------|-------------------|
| **Short tag** | "VIP" (3 chars) | `user_001` | Render as-is |
| **Medium tag** | "First-Timer" (11 chars) | `user_009` | Render as-is |
| **Long tag** | "International" (13 chars) | `user_011` | Render as-is |
| **Very long tag** | "This Is An Extremely Long Tag Value..." | `user_049` | May truncate or overflow |

### 7.3 Tag Overflow

| Edge Case | Description | Expected Behavior |
|-----------|-------------|-------------------|
| **Tags exceed 2.7" width** | Too many or too long | Currently: overflow hidden (cut off) |
| **Multi-row tags** | Wrapping tags | Future consideration: wrap to multiple rows |
| **Dynamic sizing** | Shrink font to fit | Future consideration: reduce font size |

### 7.4 Tag Values

| Edge Case | Description | Test User | Expected Behavior |
|-----------|-------------|-----------|-------------------|
| **Predefined values** | From tag_categories values | Standard | Render with category color |
| **Write-in values** | User-entered text | `user_001` (Rep: "Northeast") | Render as-is |
| **Invalid values** | Not in allowed list | `user_050` | Render as-is (no strict validation MVP) |
| **Special characters** | &, /, - in tag value | `user_051` | Render special chars |

---

## 8. Event Edge Cases

### 8.1 Event Name Length

| Edge Case | Description | Test Event | Expected Behavior |
|-----------|-------------|------------|-------------------|
| **Very short** | "BBQ", "Gala" (5-6 chars) | `short_event` | Render at full font size |
| **Medium** | "Spring Block Party" | `neighborhood_gathering` | Render on 1 line |
| **Long** | "AfterHours at COHATCH" | `cohatch_afterhours` | May wrap to 2 lines |
| **Very long** | "The Annual International Conference on..." | `long_event` | Wrap to 2 lines, truncate overflow |
| **At limit** | Exactly 100 chars | `boundary_event` | Fit in 3 lines with truncation |

### 8.2 Event Configuration

| Edge Case | Description | Test Event | Expected Behavior |
|-----------|-------------|------------|-------------------|
| **Null date** | No date specified | `afterhours_networking` | Omit date field |
| **Long date** | "November 15-17, 2025 (Extended Weekend)" | `long_date_event` | Truncate if exceeds width |
| **Null sponsor** | No sponsor | Most events | Omit sponsor text |
| **With sponsor** | Sponsor name provided | Some events | Render sponsor name |
| **With sponsor logo** | sponsor_logo_path set | `sponsored_event` | Render sponsor logo |
| **Null logo** | No event logo | `minimal_event` | Omit event logo |
| **8 tag categories** | Maximum categories | `tag_overload` | Test tag overflow |
| **No tag categories** | Empty array | `minimal_event` | No tags rendered |

---

## 9. Image & QR Code Edge Cases

### 9.1 Interests Image

| Edge Case | Description | Test User | Expected Behavior |
|-----------|-------------|-----------|-------------------|
| **Null image path** | interests_image_path: null | `user_004`, `user_012` | Omit interests band, badge still renders |
| **Missing file** | Path set but file doesn't exist | `user_052` | Gracefully skip image, render rest of badge |
| **Wrong aspect ratio** | Not 2:1 | `user_053` | Crop/pad to 2:1 via crop_interests_image.py |
| **Low resolution** | <288 DPI | `user_054` | Render as-is, may appear pixelated |
| **Large file size** | >10 MB | `user_055` | Load and render (may be slow) |
| **Corrupted file** | Invalid PNG | `user_056` | Error handling, skip image |
| **Transparent background** | PNG with alpha | `user_057` | Handle transparency correctly |

### 9.2 QR Code

| Edge Case | Description | Test User | Expected Behavior |
|-----------|-------------|-----------|-------------------|
| **Null profile_url** | No URL provided | `user_004`, `user_006`, `user_010`, `user_023` | Omit QR code, badge still renders |
| **Null profile_url (minimal badge)** | No QR, all fields minimal | `user_004` | Tests complete minimal scenario |
| **Null profile_url (otherwise complete)** | No QR but other fields present | `user_006` | Tests QR-less badge with full data |
| **Very long URL** | 200+ char URL | `user_058` | QR code generated successfully (QR can handle) |
| **Invalid URL** | Not HTTP/HTTPS | `user_059` | May fail QR generation, skip gracefully |

### 9.3 Logos

| Edge Case | Description | Test Event | Expected Behavior |
|-----------|-------------|------------|-------------------|
| **Event logo null** | No logo path | `minimal_event` | Omit event logo |
| **Sponsor logo null** | No sponsor logo | Most events | Omit sponsor logo |
| **Sponsor logo present** | Path provided | `sponsored_event` | Render sponsor logo |
| **Wrong aspect ratio** | Very wide or tall logo | `logo_test_event` | object-fit: contain scales correctly |
| **SVG logo** | Vector format | `svg_logo_event` | Render SVG correctly |

---

## 10. Rendering Edge Cases

### 10.1 Text Overflow

| Edge Case | Description | Expected Behavior |
|-----------|-------------|-------------------|
| **Name exceeds width** | Name too long at 12pt | Progressive truncation per name_utils.py |
| **Title exceeds 2 lines** | Long title | CSS line-clamp truncates at 2 lines |
| **Company exceeds width** | Long company name | text-overflow: ellipsis |
| **Location exceeds width** | Long location | text-overflow: ellipsis |
| **Event name exceeds 3 lines** | Very long event name | CSS line-clamp truncates at 3 lines |
| **Social handle exceeds width** | Very long handle | May overflow or truncate |

### 10.2 Layout Edge Cases

| Edge Case | Description | Expected Behavior |
|-----------|-------------|-------------------|
| **All elements present** | Full badge with all optional fields | All elements render in designated positions |
| **Minimal badge** | Name only | Only name and event header render |
| **No professional info** | Null title, company, location | More vertical space, cleaner look |
| **Many tags** | 8+ tags | Test overflow and positioning |
| **Long text everywhere** | All fields at max length | Comprehensive truncation test |

### 10.3 Font Edge Cases

| Edge Case | Description | Expected Behavior |
|-----------|-------------|-------------------|
| **Font not available** | Helvetica missing | Fallback to Arial, sans-serif |
| **Unicode font support** | Chinese, Arabic characters | Fallback fonts render correctly |
| **Emoji rendering** | 🎸☕🚀 in text | Color emoji or text-style emoji render |
| **Very small text** | 5pt sponsor text | Readable at 300 DPI when printed |

---

## 11. Unicode & International Edge Cases

### 11.1 Character Sets

| Edge Case | Description | Test User | Expected Behavior |
|-----------|-------------|-----------|-------------------|
| **Chinese characters** | 李娜, 北京 | `user_012` (Zhang Wei / 李娜) | Render correctly with font fallback |
| **Arabic characters** | محمد بن عبدالله | `user_016` (Abdul Rahman...) | Render RTL correctly |
| **Cyrillic** | Москва, Россия | `user_015` (Anastasia Mikhailovna...) | Render correctly |
| **Latin extended** | ñ, ü, ø, å, ł | Various users | Render accents correctly |
| **Emoji** | 🎸 ☕ 🚀 | `user_060` (Emoji Test) | Render color or monochrome emoji |
| **Mixed scripts** | "Elena Müller-中村" | `user_061` | Render mixed scripts in single field |
| **Right-to-left text** | Arabic, Hebrew | `user_016` | Handle RTL direction |
| **Combining diacritics** | Café (é vs e+´) | `user_062` | Normalize to composed form |

### 11.2 International Formats

| Edge Case | Description | Test User | Expected Behavior |
|-----------|-------------|-----------|-------------------|
| **Date formats** | DD/MM/YYYY vs MM/DD/YYYY | Various events | Render as provided (no parsing) |
| **Name order** | Family name first (East Asian) | `user_012` | Render as provided by user |
| **Honorifics** | San, Sama, Señor | `user_063` | Render as part of name if provided |

---

## 12. Null/Missing Data Edge Cases

### 12.1 Optional Field Combinations

| Edge Case | Description | Test User | Expected Behavior |
|-----------|-------------|-----------|-------------------|
| **Null title** | title: null | `user_004` | Omit title field |
| **Null company** | company: null | `user_004` | Omit company field |
| **Null location** | location: null | `user_004` | Omit location field |
| **Null title + company** | Both null | `user_004` | Omit entire professional info section |
| **Null interests** | All interest fields null/empty | `user_004` | Omit interests band, render badge without interests section |
| **Generic raw_interests** | Text provided but too generic | `user_004` | `raw_interests` present but `interests: []`, no interests band renders |
| **Null social** | Both social fields null | `user_004` | Omit social media section |
| **Null profile_url** | profile_url: null | `user_004` | Omit QR code |
| **Null image path** | interests_image_path: null | `user_004` | Omit interests illustration |
| **All optional fields null** | Minimal attendee | `user_004` (Minimal Badge) | Only name + event header render |

### 12.2 Empty Arrays/Objects

| Edge Case | Description | Test User | Expected Behavior |
|-----------|-------------|-----------|-------------------|
| **Empty interests array** | interests: [] | `user_004` | Omit interests band |
| **Empty tags object** | tags: {} | `user_064` | Omit tag sections |
| **Empty normalized interests** | interests_normalized: [] | `user_004` | Omit interests band |

### 12.3 Whitespace/Empty Strings

| Edge Case | Description | Test User | Expected Behavior |
|-----------|-------------|-----------|-------------------|
| **Empty string name** | name: "" | N/A | Hard reject at form |
| **Whitespace-only name** | name: "   " | N/A | Hard reject at form |
| **Empty string title** | title: "" | `user_065` | Treat as null, omit field |
| **Empty string location** | location: "" | `user_066` | Treat as null, omit field |

---

## Priority Levels

### Critical Priority (Must Test Immediately)

1. **Null profile_url** (`user_004`) - No QR code scenario
2. **Null interests_image_path** (`user_004`) - No interests band
3. **Minimal badge** (`user_004`) - Name only
4. **Mononym** (`user_002`) - Single name
5. **Apostrophe in name** (`user_007`) - O'Connor format
6. **Very long name** (`user_020`) - Truncation testing
7. **Below min interests** (`user_010`) - 2 interests edge case
8. **15+ interests normalization** (`user_018`) - Brand filtering
9. **Invalid location** (`user_008`) - Geocoding failure
10. **Very long title** (`user_017`) - >2 line truncation

### High Priority (Test Soon)

11. Tag overflow (8+ tags, `user_047`)
12. Very long event name (`long_event`)
13. Special characters in company (`user_013` - AT&T)
14. Chinese characters throughout (`user_012`)
15. Very long social handle (`user_014`)
16. Null title + null company (`user_004`)
17. Controversial interests (`user_019`)
18. Wrong aspect ratio image (`user_053`)

### Medium Priority (Test During Development)

19-40. Various unicode, emoji, and international edge cases
41-60. Additional rendering and validation edge cases

### Low Priority (Nice to Have)

61-70. Extreme edge cases, security tests, performance tests

---

## Test User Mapping

### Quick Reference Table

| User ID | Primary Edge Cases Tested |
|---------|--------------------------|
| `user_001` | Short name, standard fields, 3 interests |
| `user_002` | Mononym (single name) |
| `user_003` | Very short name (5 chars) |
| `user_004` | **Minimal badge** - all optional fields null, generic raw_interests with no extractable interests |
| `user_005` | Medium name, 8 normalized interests |
| `user_006` | Short title (CEO), short company (IBM), no QR code despite complete data |
| `user_007` | **Apostrophe** in name (O'Connor) |
| `user_008` | **Invalid location** (Atlantis) - geocoding failure test |
| `user_009` | Standard user with 8 interests normalized |
| `user_010` | **Below min interests** (2 interests), no QR code |
| `user_011` | Arabic name format (bin Mohammed Al-Sayed) |
| `user_012` | Chinese characters (李娜), Eastern name order |
| `user_013` | **Special chars** in company (AT&T / Warner Bros.) |
| `user_014` | **Diacritics** (Björk), very long social handle |
| `user_015` | Spanish double surname, accents (María García-Hernández) |
| `user_016` | Russian patronymic (Anastasia Mikhailovna Kovalenko) |
| `user_017` | **Very long title** (90+ chars, >2 lines) |
| `user_018` | **15+ interests** with many brands/celebrities (normalization test) |
| `user_019` | **Controversial interests** (political/religious content) |
| `user_020` | **Extreme long name** (Dr. ... III, PhD) with title prefix and suffix |
| `user_021` | Trademarked activities (CrossFit, Peloton, SoulCycle) normalization |
| `user_022` | Multiple hyphens in name (Smith-Jones-Williams) |
| `user_023` | Very long location (Llanfairpwll...gogogoch), no QR code |
| `user_024` | Name with periods (J.D. Martinez) |
| `user_025` | Whitespace test, abstract interests (Mindfulness) |
| `user_026` | Entry-level title, profession-adjacent interests |

---

## Testing Checklist

Use this checklist to verify edge case handling:

### Names
- [ ] Mononym renders correctly
- [ ] Very long name truncates with font shrinking
- [ ] Apostrophe renders correctly
- [ ] Hyphenated names render correctly
- [ ] Name with suffix (Jr., III, PhD) renders correctly
- [ ] Chinese characters render correctly
- [ ] Arabic names render correctly
- [ ] Diacritics and accents render correctly

### Locations
- [ ] Very short location (2-3 chars) renders
- [ ] Very long location truncates with ellipsis
- [ ] Invalid location renders as-is (graceful geocoding failure)
- [ ] Null location omits field
- [ ] Special characters in location render correctly

### Titles & Companies
- [ ] Very short title/company renders
- [ ] Very long title wraps to 2 lines and truncates
- [ ] Special characters (&, /, -) render correctly
- [ ] Null title/company omits field
- [ ] Title >2 lines truncates correctly

### Interests
- [ ] 0 interests renders badge without interests band
- [ ] 2 interests (below min) handles gracefully
- [ ] 3 interests (min) renders correctly
- [ ] 8 interests (max) renders correctly
- [ ] 15+ interests normalizes to 3-8
- [ ] Brands normalize correctly (Nike → Running)
- [ ] Celebrities normalize correctly (Taylor Swift → Pop music concerts)
- [ ] Sports teams normalize correctly (Cleveland Browns → Football fan)
- [ ] Trademarked activities normalize (CrossFit → Fitness training)

### Social Media
- [ ] Very long handle renders or truncates
- [ ] Handle with special chars renders
- [ ] Null social media omits section
- [ ] All platform icons render correctly

### Tags
- [ ] 1 tag renders correctly
- [ ] 5 tags position correctly (3 top, 2 bottom)
- [ ] 8+ tags test overflow behavior
- [ ] Very long tag text handles gracefully
- [ ] No tags omits tag sections

### Events
- [ ] Very short event name renders
- [ ] Very long event name wraps to 3 lines and truncates
- [ ] Null date omits date field
- [ ] Sponsor logo renders when provided
- [ ] 8 tag categories test overflow

### Images & QR
- [ ] Null profile_url omits QR code
- [ ] Null interests_image_path omits interests band
- [ ] Wrong aspect ratio image crops/pads correctly
- [ ] Missing image file handles gracefully

### Rendering
- [ ] Minimal badge (name only) renders professionally
- [ ] All max-length fields render without breaking layout
- [ ] Unicode characters render correctly
- [ ] Emoji render correctly
- [ ] RTL text (Arabic) renders correctly

---

## Automated Testing Recommendations

### Unit Tests
- Name truncation logic (`name_utils.py`)
- Interest normalization logic (brand detection)
- Geocoding fallback behavior
- Image cropping to 2:1 aspect ratio

### Integration Tests
- Full badge generation for each test user
- Verify PDF output dimensions (3" × 4")
- Verify image quality (300 DPI)
- Verify all fonts embed correctly

### Visual Regression Tests
- Screenshot comparison for each test user
- Detect unexpected layout shifts
- Verify consistent styling across edge cases

### Performance Tests
- Batch generation (25-30 badges)
- Large event (100+ attendees)
- Image generation timeout handling

---

**Document Version:** 1.0
**Last Updated:** 2025-11-16
**Status:** Complete Edge Case Catalog
