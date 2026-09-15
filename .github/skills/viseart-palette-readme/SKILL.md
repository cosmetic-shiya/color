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

## Use When
- A folder under `docs/viseart/` has an `id` image, an `icons` image, and English shade text.
- You need to split the `icons` image into per-shade images.
- You need to rewrite or normalize `README.md` into one section per shade.
- You need to insert one sliced image under each shade heading.
- You need to add concise Chinese name and usage translations.

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
- `icons.*` source grid image
- `id.*` or cover image for the page header

Optional:
- a reference palette with the same layout to reuse margin ratios
- an existing `slice_icons.py` script to adapt

## Output
- `slices/NN.<ext>` files, one per shade
- normalized `README.md`
- one `## Shade N: ...` section per shade
- one inserted image per shade
- one Chinese translation block per shade

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

## Existing Assets in This Repo
Potential references:
- `docs/viseart/big-12-matte-neutral/README.md`
- `docs/viseart/big-12-matte-neutral/icons.png`
- `docs/viseart/middle-35-pro-x1/README.md`
- `.github/skills/viseart-palette-readme/viseart_palette_tool.py`

## Companion Script
This skill includes a reusable script:

```text
.github/skills/viseart-palette-readme/viseart_palette_tool.py
```

It can:
- parse English `Shade N:` and `Use:` entries
- slice `icons.*` into `slices/`
- use a reference icons file when outer margin needs to match a known-good palette
- rewrite `README.md` into one section per shade
- add heuristic Chinese description and usage text as a first draft

Example for a 12-shade palette:

```bash
python .github/skills/viseart-palette-readme/viseart_palette_tool.py \
  docs/viseart/big-12-matte-cool2 \
  --reference-icons docs/viseart/big-12-matte-neutral/icons.png \
  --rewrite-readme
```

Example for a 35-shade palette:

```bash
python .github/skills/viseart-palette-readme/viseart_palette_tool.py \
  docs/viseart/middle-35-pro-x1 \
  --grid 7 5 \
  --slice-ext jpg \
  --slice-name-mode number \
  --rewrite-readme
```

## Minimal Execution Checklist
1. Read the target folder and identify `id`, `icons`, and description text.
2. Determine shade count and grid layout.
3. Generate `slices/` with left-to-right, top-to-bottom numbering.
4. Rewrite `README.md` into one section per shade.
5. Insert the corresponding slice image under each shade heading.
6. Add Chinese translations for each shade description and usage.
7. Validate section count, image count, and link correctness.

## Common Failure Modes
- Cutting by equal thirds or fifths without removing outer margin.
- Mixing `.png` and `.jpg` links incorrectly in README.
- Leaving raw description text at top level instead of converting it into `## Shade` sections.
- Translating too literally and losing cosmetic meaning.
- Forgetting to preserve warnings for non-eye-safe pigments.
