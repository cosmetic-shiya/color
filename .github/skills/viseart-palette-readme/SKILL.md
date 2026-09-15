---
name: viseart-palette-readme
description: "Use when a Viseart palette folder contains an id image, an icons image, and English shade descriptions, and you need to slice the icon grid, insert the sliced images into README, and add Chinese translations. Keywords: Viseart, id image, icons image, split grid, slices, shade descriptions, README, Chinese translation, palette page, GitHub Pages."
---

# Viseart Palette README Skill

## Purpose
Turn a palette folder under `docs/viseart/` into a publishable GitHub Pages document by combining:
- the cover or id image
- the icon grid image
- the English shade descriptions
- the sliced shade images
- a bilingual README with Chinese translation

This skill is intended for the workflow already used in this repository.

In this repo, the usual source preference is:
- use the official open-palette image as `id`
- use the shade-board image with printed descriptions as `icons`
- if the official page does not provide a separate `icons`-style board, fall back to `id`

README title convention in this repo:
- brand name
- shade count
- palette size in Chinese: `小号` for Viseart `1g`, `中号` for `1.5g`, `大号` for `2g`
- Chinese palette name
- English palette name

Preferred format:

```text
Viseart <几色> <铁盘大小> <中文盘名> <英文盘名>
```

Examples:
- `Viseart 12色 小号 哑光冷调盘 Petites Mattes Cool`
- `Viseart 35色 中号 哑光大盘 Grande Pro 1X`
- `Viseart 12色 大号 哑光冷调盘 Matte Cool 2`

## Use When
- A folder under `docs/viseart/` has an `id` image, an `icons` image, and English shade text.
- You need to split the `icons` image into per-shade images.
- You need to rewrite or normalize `README.md` into one section per shade.
- You need to insert one sliced image under each shade heading.
- You need to add concise Chinese name and usage translations.
- Or you have the official product page link and want the skill to pull the `Shade Description` box directly from the website.
- Or you provide the palette name or slug and it matches an existing folder or known mapping.

## Expected Folder Layout
Typical target folder:

```text
docs/viseart/<palette-slug>/
  README.md
  id.jpg | id.png
  icons.jpg | icons.png | icons.webp
  slices/
```

Common patterns already present in this repo:
- `big-12-*` palettes: 12 shades, usually `4 x 3`
- `middle-35-*` palettes: 35 shades, usually `7 x 5`

## Inputs
Required:
- `README.md` or another file containing the English shade descriptions
- `id.*` or cover image for the page header

One of the following image sources is required:
- `icons.*` source grid image, preferably the palette board that already includes shade descriptions
- or a Viseart product page that exposes a usable open-palette image

Optional:
- a reference palette with the same layout to reuse margin ratios
- a Viseart product page URL to download missing assets from

Important input rule:
- a product page link is enough to identify one palette reliably
- a palette name or palette slug is usually enough when it matches the folder or known mapping
- a shade number alone is not enough because many palettes have `Shade 1`, `Shade 2`, and so on
- if you only provide a palette name, the skill may still need the product link when there is ambiguity

## Output
- `slices/NN.<ext>` files, one per shade
- normalized `README.md`
- one `## Shade N: ...` section per shade
- one inserted image per shade
- one Chinese translation block per shade
- updated `docs/README.md` index entry when the palette should appear on the Pages homepage

## Workflow

### 1. Inspect the folder
Confirm:
- the target folder path
- cover image file name
- icon grid file name
- description source file
- expected shade count

If the shade count is unclear, infer it from:
- the number of English `Shade N:` entries
- or the icon grid layout visible in the image

### 2. Determine grid layout
Use the following default mappings unless the image proves otherwise:
- 12 shades -> `4 x 3`
- 35 shades -> `7 x 5`

If there is a matching reference palette with identical visual structure, prefer reference-based slicing.

### 3. Slice the icons image
Preferred strategies:

1. Reference-based slicing
- Use a known-good palette with the same layout.
- Detect the content bounding box of the reference.
- Reuse its margin ratios on the target image.
- Split only the content area.

2. Margin-aware auto-detection
- Detect the outer non-white content bounding box.
- Remove the outer margin.
- Shrink the cropped region to dimensions divisible by columns and rows.
- Split the cropped region into equal cells.

3. Plain equal split
- Only use this if the grid fully fills the source image.
- Do not use this when there is visible outer margin.

4. Cover-image fallback
- If `icons.*` is missing, use the open-palette `id.*` image or a downloaded product image.
- Detect the darker tray area below the lid.
- Split only the tray region into the expected grid.
- Expect weaker results than a real `icons.*` board because the first row may be partially covered by the lid.
- When this happens, record the limitation in `README.md` and prefer a later re-run from `icons.*`.
- For 3-row palettes, align rows 2 and 3 first from the lower visible area, then derive row 1 using the same row height.

### 3.5. Download source assets from the product page when needed
If local assets are incomplete, prefer the official product page as the source of truth.

Examples already verified in this repo:
- `https://viseartparis.com/en-de/products/petites-mattes-cool`
- `https://viseartparis.com/en-de/products/petites-mattes-neutral`

What to pull:
- the main open-palette image as `id.*`
- a dedicated shade-board image with printed descriptions as `icons.*` when the product page or another official source provides one
- if no dedicated `icons.*` exists, use the open-palette image as the slicing source fallback
- the `Shade Description` accordion text block when it is present in the product page HTML

Current companion-script support:
- `--download-product-assets`
- `--product-url`
- `--crop-bbox LEFT TOP RIGHT BOTTOM`

### 4. File naming for slices
Use ordered names to preserve reading order:

```text
slices/01.png
slices/02.png
...
slices/12.png
```

or:

```text
slices/01.jpg
slices/02.jpg
...
slices/35.jpg
```

The numbering order must be left-to-right, top-to-bottom.

### 5. Normalize the README structure
Use this structure:

```md
# <palette title>
![id](id.jpg)

## Shade 1: <English shade name> - <English short description>
![Shade 1 <Name>](./slices/01.png)

Use: <English usage text>

##### 色号 1：<Chinese name> (<English name>) —— <Chinese short description>。
用途：<Chinese usage text>
```

Rules:
- Use one `##` section per shade.
- Insert the matching slice directly under the shade heading.
- Preserve important warnings in English and Chinese.
- Keep the Chinese translation concise and product-facing.
- If the slices were generated from `id.*` instead of `icons.*`, add a short note near the top explaining that the first row may be slightly occluded.
- Format the main page title using the repo title convention unless the user explicitly asks for a different naming style.

### 6. Translation guidance
When translating:
- Preserve the makeup function, not just literal wording.
- Prefer concise beauty-product Chinese, not academic translation.
- Keep shade names in Chinese plus English in parentheses when useful.
- Translate `Use:` into `用途：`.
- Preserve legal warnings as `提示：` if needed.

Examples of preferred tone:
- `all-over lid shade` -> `全眼铺色`
- `transitional shade` -> `过渡色`
- `outer corners` -> `眼尾`
- `brow bone highlight` -> `眉骨提亮`
- `smokey eye base` -> `烟熏打底`
- `mix to lighten other shades` -> `与其他颜色混合提亮`

### 7. Validation
After editing, verify:
- the number of `## Shade` sections equals the shade count
- the number of inserted shade images equals the shade count
- `README.md` points to existing slice files
- the header image path is valid
- `docs/README.md` links to the new palette page when homepage navigation should include it

### 8. Update the Pages index
If the palette is ready to publish, add it to `docs/README.md` under the Viseart section.

Rules:
- use the final palette display name, not the folder slug
- link directly to `./viseart/<palette-slug>/README.md`
- keep the homepage list concise and human-readable
- do not add unfinished palette folders to the homepage

Useful checks:

```bash
grep -c '^## Shade' docs/viseart/<palette-slug>/README.md
grep -c '^!\[Shade' docs/viseart/<palette-slug>/README.md
ls docs/viseart/<palette-slug>/slices | wc -l
```

## Repository-Specific Notes
- This repo publishes from `docs/` for GitHub Pages.
- Work directly under `docs/viseart/<palette-slug>/`.
- Keep the README ready for static Markdown rendering.
- Use relative image links only.
- `docs/README.md` is the Pages landing index and should be updated when a palette page is publish-ready.

## Existing Assets in This Repo
Potential references:
- `docs/viseart/big-12-mattes-neutral/README.md`
- `docs/viseart/big-12-mattes-neutral/icons.png`
- `docs/viseart/middle-35-pro-x1/README.md`
- `.github/skills/viseart-palette-readme/viseart_palette_tool.py`

## Companion Script
This skill includes a reusable script:

```text
.github/skills/viseart-palette-readme/viseart_palette_tool.py
```

It can:
- fetch the product page and parse the `Shade Description` block directly from the site HTML
- parse English `Shade N:` and `Use:` entries
- slice `icons.*` into `slices/`
- fall back to slicing the open-palette `id.*` image when `icons.*` is missing
- use a reference icons file when outer margin needs to match a known-good palette
- accept a manual crop box for difficult source images that defeat auto-detection
- generate known palette titles using the repo naming convention
- rewrite `README.md` into one section per shade
- add a top-of-page note when slices were derived from `id.*` instead of `icons.*`
- add heuristic Chinese description and usage text as a first draft
- optionally update `docs/README.md` with a homepage entry
- optionally download a primary image from a Viseart product page

Example for a 12-shade palette:

```bash
python .github/skills/viseart-palette-readme/viseart_palette_tool.py \
  docs/viseart/big-12-mattes-cool2 \
  --reference-icons docs/viseart/big-12-mattes-neutral/icons.png \
  --rewrite-readme \
  --update-docs-index
```

Example when the folder only has `README.md` and the product page should supply or backfill imagery:

```bash
python .github/skills/viseart-palette-readme/viseart_palette_tool.py \
  docs/viseart/small-12-matte-cool \
  --product-url https://viseartparis.com/en-de/products/petites-mattes-cool \
  --download-product-assets \
  --rewrite-readme \
  --update-docs-index
```

Example when the folder has no reliable local shade-description text and the product page should supply it directly:

```bash
python .github/skills/viseart-palette-readme/viseart_palette_tool.py \
  docs/viseart/<palette-slug> \
  --product-url https://viseartparis.com/en-de/products/<product-slug> \
  --rewrite-readme \
  --update-docs-index
```

Example for a 35-shade palette:

```bash
python .github/skills/viseart-palette-readme/viseart_palette_tool.py \
  docs/viseart/middle-35-pro-x1 \
  --grid 7 5 \
  --slice-ext jpg \
  --slice-name-mode number \
  --rewrite-readme \
  --update-docs-index
```

Optional homepage label override:

```bash
python .github/skills/viseart-palette-readme/viseart_palette_tool.py \
  docs/viseart/<palette-slug> \
  --rewrite-readme \
  --update-docs-index \
  --homepage-label "<homepage display name>"
```

Example when auto-detection is unreliable and you want to lock the slicing region explicitly:

```bash
python .github/skills/viseart-palette-readme/viseart_palette_tool.py \
  docs/viseart/<palette-slug> \
  --rewrite-readme \
  --crop-bbox <left> <top> <right> <bottom>
```

## Minimal Execution Checklist
1. Read the target folder and identify `id`, `icons`, and description text.
2. Determine shade count and grid layout.
3. Generate `slices/` with left-to-right, top-to-bottom numbering.
4. Rewrite `README.md` into one section per shade.
5. Insert the corresponding slice image under each shade heading.
6. Add Chinese translations for each shade description and usage.
7. Update `docs/README.md` if the palette should be visible from the Pages homepage.
8. Validate section count, image count, and link correctness.

## Common Failure Modes
- Cutting by equal thirds or fifths without removing outer margin.
- Mixing `.png` and `.jpg` links incorrectly in README.
- Leaving raw description text at top level instead of converting it into `## Shade` sections.
- Treating a lid-covered open-palette image as if it were a clean `icons.*` board.
- Translating too literally and losing cosmetic meaning.
- Forgetting to preserve warnings for non-eye-safe pigments.
