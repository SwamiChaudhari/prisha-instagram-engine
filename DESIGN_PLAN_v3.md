# Image Engine v3.0 — Premium Design Rebuild Plan

## REFERENCE ANALYSIS SUMMARY (10 Images)

### Physical Properties
- **Format**: All portrait 689x1536 (use 1080x1350 for 4:5 Instagram max)
- **Average brightness**: 41/255 (consistently dark-themed)
- **Dark area**: 58-92% of image is dark

### Color System (extracted from refs)
- **Background darks**: #0d161f, #0a0e11, #0f1111, #080a0c
- **Text whites**: #f0f0f0, #e8e8e8, #ffffff
- **Accent warm**: #e9d064 (gold), #e85d04 (orange-red)
- **Accent cool**: #4cc9f0 (cyan), #4361ee (blue)
- **Accent green**: #06d6a0 (mint), #179e50
- **Accent red**: #e63946, #a81314
- **Neutral gray**: #6c757d for secondary text

## DESIGN SYSTEM v3.0

### Canvas
- Size: 1080x1350 (4:5 ratio — max Instagram real estate)
- Resolution: 2x render at 2160x2700, downscale for anti-aliasing

### Typography Hierarchy (3+ fonts needed)
1. **Display Bold** — Headlines (Bebas Neue / Oswald Bold) — 72-96px
2. **Body Bold** — Sub-headlines & CTAs (Montserrat Bold) — 42-54px  
3. **Body Regular** — Info text (Montserrat Regular) — 28-34px
4. **Caption** — Small text, footers (Montserrat Light) — 20-24px

### Layout Templates (5 distinct layouts)

#### Template A: "Authority Card"
- Dark gradient bg with subtle noise texture
- Top: Category badge (small pill, accent color)
- Center: Large headline (max 2 lines), sub-headline in accent color
- Middle: 2-column info grid with STAT HIGHLIGHTS (big numbers)
- Bottom: 2-column feature cards with PROPER SVG icons
- Footer: Branding + CTA button

#### Template B: "Breaking Impact"
- Bold solid color bg (red/blue/green depending on urgency)
- Top accent bar (6px) + bottom accent bar
- Large emoji-free icon (SVG) top-left
- Headline with colored highlight words
- Info cards in ROW format (not grid) — horizontal cards with icon + text
- Stats section with big numbers
- CTA strip at bottom

#### Template C: "Compare Contrast"
- Split layout — dark left, accent right
- "BEFORE vs AFTER" or "WITHOUT vs WITH" structure
- Large numbers as visual anchors
- Feature checklist with tick icons
- Bottom CTA

#### Template D: "Infographic Story"
- Vertical flow layout with numbered steps
- Each step has icon + head + sub-text
- Progress indicator dots on left side
- Color-coded sections
- Summary stat box at bottom

#### Template E: "Social Proof"
- Testimonial/case study format
- Large quote typography
- Highlighted stat callout box (floating card)
- Source attribution at bottom
- CTA overlay

### Visual Elements (replacing emojis)
- **SVG Icons**: Business, finance, government, growth, warning, success, contact
- **Decorative**: Corner accents, geometric shapes, data circles, arrows
- **Charts**: Mini bar charts, progress rings, comparison bars
- **Badges**: Pill-shaped category tags with accent bg + white text

### Color Scheme Per Pillar
- **loans_subsidies**: Deep blue bg (#0a1628) + Gold accent (#e9d064) + White text
- **government_schemes**: Dark green bg (#0a1f15) + Mint accent (#06d6a0) + White text
- **compliance**: Dark red bg (#1f0a0a) + Orange accent (#e85d04) + White text
- **business_registration**: Navy bg (#0a0e1f) + Cyan accent (#4cc9f0) + White text
- **taxation**: Dark purple bg (#150a1f) + Purple accent (#9d4edd) + White text
- **startup_resources**: Dark teal bg (#0a1f1f) + Teal accent (#2ec4b6) + White text

### Quality Gates (PASS/FAIL auto-checks)
1. Minimum 6 distinct visual elements (icons, cards, bars, badges)
2. No more than 30% empty/blank space
3. At least 3 different font sizes used
4. Color contrast ratio ≥ 4.5:1 (WCAG AA)
5. Headline must be readable at thumbnail size (font ≥ 60px)
6. Must have accent color usage (not monochrome)
7. Must have CTA element
8. Must have branding element
9. **AUTO-REJECT**: Flat single-color background
10. **AUTO-REJECT**: Emoji used as icons
11. **AUTO-REJECT**: >40% whitespace

## BUILD ORDER

### Step 1: Install premium fonts
- Google Fonts: Bebas Neue, Montserrat (full family)
- Download TTF files to insta_engine/fonts/

### Step 2: Build SVG Icon Library  
- Create 40+ SVG icons in assets/svg_icons/
- Business, finance, government, compliance, growth, communication, etc.
- Render SVGs to PNG at runtime using cairosvg or svglib

### Step 3: Rebuild image_engine.py
- New class: PremiumImageEngine
- 5 layout templates (A through E)
- Gradient background generator with texture noise
- SVG icon renderer
- Info card renderer (3 card styles: grid, row, floating)
- Number/stat renderer with visual emphasis
- CTA button renderer (pill + arrow)
- Quality scorer built-in

### Step 4: Font Manager
- FontManager class that loads and caches TTF fonts
- Fallback chain: Premium → Google → System → Default
- Dynamic sizing based on text length

### Step 5: Update main.py
- Wire PremiumImageEngine into pipeline
- Update spec format for new templates

### Step 6: Scoring Script
- Compare generated images against reference palette
- Measure: color distance, layout density, typography variance
- Output quality score 0-100
