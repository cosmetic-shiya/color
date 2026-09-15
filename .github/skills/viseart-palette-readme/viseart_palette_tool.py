#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import re
import unicodedata
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


SHADE_RE = re.compile(r"^(?:##\s+)?Shade\s+(\d+):\s+(.*?)\s+(?:-|—)\s+(.*)$")
USE_RE = re.compile(r"^Use:\s*(.*)$")


NAME_TRANSLATIONS = {
    "Salt": "盐白",
    "Sand": "沙色",
    "Seashell": "贝壳粉",
    "Lilac": "淡紫",
    "Shoreline": "海岸线棕",
    "Fog": "雾灰",
    "Sky": "天蓝",
    "Lupine": "羽扇豆紫",
    "Ghirardelli": "吉拉德利棕",
    "Elk": "麋鹿棕",
    "Bluebells": "风铃草蓝",
    "Iris": "鸢尾紫蓝",
}


DESCRIPTION_TRANSLATIONS = {
    "Pale bone matte finish.": "淡骨色，哑光质地。",
    "Cool light beige matte finish.": "冷调浅米色，哑光质地。",
    "Light pink matte finish.": "浅粉色，哑光质地。",
    "Light purple matte finish.": "浅紫色，哑光质地。",
    "Medium cool brown matte finish.": "中等冷调棕色，哑光质地。",
    "Light cool grey matte finish.": "浅冷调灰色，哑光质地。",
    "Light blue matte finish.": "浅蓝色，哑光质地。",
    "Dusty medium purple.": "柔和中紫色。",
    "Chocolate cool matte finish.": "冷调巧克力棕，哑光质地。",
    "Bitter brown matte finish.": "深苦棕，哑光质地。",
    "Deep fresh blue matte finish.": "深清爽蓝，哑光质地。",
    "Deep purple-blue matte finish.": "深紫蓝色，哑光质地。",
}


USE_TRANSLATIONS = {
    "Use to highlight and blend into all other tones to soften shades, use on brow bone to highlight.": "可用作高光，并与其他色号混合以柔和整体色调，也可用于眉骨提亮。",
    "Base tone for light to medium skin tones.": "适合浅至中等肤色的底色。",
    "Base tone for light to medium skin tones. Use as a highlight on brow bone for deeper tones. Mix-in with lighter tones and deeper tones to create variegated base tones in an array of depth.": "适合浅至中等肤色的底色；深肤色可作为眉骨提亮；可与更浅或更深的颜色混合，调出不同深浅层次的底色。",
    "Base tone for all skin tones.": "适合所有肤色的底色。",
    "All over solid tone for all skin types. Base tone, as well as midtone for eyeshadow depth and dimension. Also can be used in brows, and as contour.": "适合所有肤色的大面积实色铺陈；可作底色或中间色调，增强眼影深度与立体感；也可用于眉部与修容。",
    "All over tone for all skin types, use as a soft eyeliner for light to medium tones.": "适合所有肤色的大面积铺色；可作为浅至中等肤色的柔和眼线。",
}


PALETTE_TITLE_PARTS = {
    "big-12-matte-cool2": {
        "shade_count": "12色",
        "size_label": "大号",
        "cn_name": "哑光冷调盘",
        "en_name": "Matte Cool 2",
    },
    "big-12-matte-neutral": {
        "shade_count": "12色",
        "size_label": "大号/小号",
        "cn_name": "哑光中性盘",
        "en_name": "Matte Neutral",
    },
    "middle-35-pro-x1": {
        "shade_count": "35色",
        "size_label": "中号",
        "cn_name": "哑光大盘",
        "en_name": "Grande Pro 1X",
    },
    "small-12-matte-cool": {
        "shade_count": "12色",
        "size_label": "小号",
        "cn_name": "哑光冷调盘",
        "en_name": "Petites Mattes Cool",
    },
}


HOMEPAGE_LABELS = {
    "big-12-matte-cool2": "12色大号 哑光冷调盘 Matte Cool 2",
    "big-12-matte-neutral": "12色大号/小号中性盘 Matte Neutral",
    "middle-35-pro-x1": "35色中号铁盘哑光盘 Pro X1",
    "small-12-matte-cool": "12色小号 哑光冷调盘 Petites Mattes Cool",
}


HOMEPAGE_SECTION = "### 眼影 Viseart"


PRODUCT_URLS = {
    "small-12-matte-cool": "https://viseartparis.com/en-de/products/petites-mattes-cool",
    "big-12-matte-neutral": "https://viseartparis.com/en-de/products/petites-mattes-neutral",
}


CDN_IMAGE_RE = re.compile(r"https://viseartparis\.com/cdn/shop/[^\"' )]+")
SHADE_BLOCK_RE = re.compile(
    r'<span class="metafield-multi_line_text_field">(.*?)</span>', re.DOTALL
)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.DOTALL | re.IGNORECASE)


@dataclass
class Shade:
    number: int
    name: str
    description: str
    use: str
    warning: str = ""


@dataclass
class SliceContext:
    source_kind: str
    has_occluded_top_row_risk: bool = False


@dataclass
class ProductPageData:
    title: str | None
    shade_text: str | None


def default_title_for_palette(folder_name: str) -> str:
    parts = PALETTE_TITLE_PARTS.get(folder_name)
    if not parts:
        return folder_name
    return (
        f"Viseart {parts['shade_count']} {parts['size_label']} "
        f"{parts['cn_name']} {parts['en_name']}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Slice Viseart palette icons and generate a bilingual README skeleton."
    )
    parser.add_argument("palette_dir", type=Path, help="Palette folder under docs/viseart")
    parser.add_argument(
        "--source-readme",
        type=Path,
        help="File containing the English shade descriptions. Defaults to README.md in the palette folder.",
    )
    parser.add_argument(
        "--reference-icons",
        type=Path,
        help="Optional reference icons image with the same visual structure.",
    )
    parser.add_argument(
        "--grid",
        type=int,
        nargs=2,
        metavar=("COLS", "ROWS"),
        help="Grid size override. Defaults to 4 3 for 12 shades and 7 5 for 35 shades.",
    )
    parser.add_argument(
        "--slice-ext",
        choices=("png", "jpg"),
        help="Output slice extension. Defaults to the source icons extension if png/jpg, else png.",
    )
    parser.add_argument(
        "--slice-name-mode",
        choices=("number", "number-name"),
        default="number-name",
        help="Whether slice files use 01.png or 01_Name.png style naming.",
    )
    parser.add_argument(
        "--rewrite-readme",
        action="store_true",
        help="Rewrite README.md with generated sections.",
    )
    parser.add_argument(
        "--update-docs-index",
        action="store_true",
        help="Update docs/README.md to include this palette on the Pages homepage.",
    )
    parser.add_argument(
        "--homepage-label",
        help="Optional label text to use in docs/README.md instead of the default mapped label.",
    )
    parser.add_argument(
        "--download-product-assets",
        action="store_true",
        help="Download an id image from the mapped or provided product page when local assets are missing.",
    )
    parser.add_argument(
        "--product-url",
        help="Optional Viseart product page URL to fetch images from.",
    )
    parser.add_argument(
        "--crop-bbox",
        type=int,
        nargs=4,
        metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"),
        help="Optional manual crop box override for slicing difficult source images.",
    )
    return parser.parse_args()


def sanitize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    safe = re.sub(r"[^A-Za-z0-9]+", "_", ascii_only).strip("_")
    return safe or "Shade"


def detect_file(folder: Path, candidates: list[str]) -> Path:
    for candidate in candidates:
        path = folder / candidate
        if path.exists():
            return path
    matches = []
    for pattern in candidates:
        matches.extend(folder.glob(pattern))
    if matches:
        return sorted(matches)[0]
    raise FileNotFoundError(f"Could not find any of: {candidates} in {folder}")


def product_url_for_palette(palette_dir: Path, explicit_url: str | None) -> str | None:
    if explicit_url:
        return explicit_url
    return PRODUCT_URLS.get(palette_dir.name)


def clean_html_text(value: str) -> str:
    text = value.replace("<br />", "\n")
    text = text.replace("<br/>", "\n")
    text = text.replace("<br>", "\n")
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = text.replace("\u2028", "\n")
    text = text.replace("\xa0", " ")
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def fetch_product_page_data(product_url: str) -> ProductPageData:
    with urllib.request.urlopen(product_url) as response:
        html_text = response.read().decode("utf-8", errors="ignore")

    title = None
    title_match = H1_RE.search(html_text)
    if title_match:
        title = clean_html_text(title_match.group(1))

    shade_text = None
    for block in SHADE_BLOCK_RE.findall(html_text):
        cleaned = clean_html_text(block)
        if "Shade 1:" in cleaned and "Use:" in cleaned:
            shade_text = cleaned
            break

    return ProductPageData(title=title, shade_text=shade_text)


def download_primary_product_image(product_url: str, target_path: Path) -> Path:
    with urllib.request.urlopen(product_url) as response:
        html = response.read().decode("utf-8", errors="ignore")

    matches = CDN_IMAGE_RE.findall(html)
    unique_matches: list[str] = []
    for match in matches:
        clean = match.replace("&amp;", "&")
        if clean not in unique_matches:
            unique_matches.append(clean)

    if not unique_matches:
        raise ValueError(f"No product images found at {product_url}")

    preferred = None
    for url in unique_matches:
        if "width=750" in url:
            preferred = url
            break
    image_url = preferred or unique_matches[0]

    target_path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(image_url, target_path)
    return target_path


def parse_shades_from_text(
    source_text: str,
    folder_name: str,
    fallback_title: str | None = None,
) -> tuple[str, list[Shade]]:
    source_text = re.sub(r"(?<!\n)Shade\s*\n+\s*(\d+:)", r"\nShade \1", source_text)
    source_text = re.sub(r"(Use:\s+[^\n]+?)Shade\s*\n+\s*(\d+:)", r"\1\n\nShade \2", source_text)
    lines = source_text.splitlines()
    title = fallback_title or default_title_for_palette(folder_name)
    for line in lines:
        if line.startswith("# "):
            heading_title = line[2:].strip()
            if heading_title == folder_name and folder_name in PALETTE_TITLE_PARTS:
                title = default_title_for_palette(folder_name)
            else:
                title = heading_title
            break

    shades: list[Shade] = []
    current: dict[str, str] | None = None
    warning_lines: list[str] = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        shade_match = SHADE_RE.match(line)
        if shade_match:
            if current is not None:
                shades.append(
                    Shade(
                        number=int(current["number"]),
                        name=current["name"],
                        description=current["description"],
                        use=current.get("use", ""),
                        warning=" ".join(warning_lines).strip(),
                    )
                )
            current = {
                "number": shade_match.group(1),
                "name": shade_match.group(2).strip(),
                "description": shade_match.group(3).strip(),
            }
            warning_lines = []
            continue
        use_match = USE_RE.match(line)
        if use_match and current is not None:
            current["use"] = use_match.group(1).strip()
            continue
        if line.startswith("*WARNING*") and current is not None:
            warning_lines.append(line)

    if current is not None:
        shades.append(
            Shade(
                number=int(current["number"]),
                name=current["name"],
                description=current["description"],
                use=current.get("use", ""),
                warning=" ".join(warning_lines).strip(),
            )
        )
    if not shades:
        raise ValueError("No shade entries found in the source text")
    return title, shades


def parse_shades(source_path: Path) -> tuple[str, list[Shade]]:
    source_text = source_path.read_text(encoding="utf-8")
    return parse_shades_from_text(source_text, source_path.parent.name)


def infer_grid(shade_count: int) -> tuple[int, int]:
    if shade_count == 12:
        return 4, 3
    if shade_count == 35:
        return 7, 5
    raise ValueError(f"No default grid for {shade_count} shades. Use --grid COLS ROWS.")


def content_bbox(image: Image.Image, threshold: int = 245) -> tuple[int, int, int, int]:
    rgb = image.convert("RGB")
    width, height = rgb.size
    pixels = rgb.load()
    xs: list[int] = []
    ys: list[int] = []

    for y in range(height):
        for x in range(width):
            red, green, blue = pixels[x, y]
            if red < threshold or green < threshold or blue < threshold:
                xs.append(x)
                ys.append(y)

    if not xs or not ys:
        return (0, 0, width, height)

    pad = 4
    left = max(0, min(xs) - pad)
    top = max(0, min(ys) - pad)
    right = min(width, max(xs) + 1 + pad)
    bottom = min(height, max(ys) + 1 + pad)
    return (left, top, right, bottom)


def scaled_reference_bbox(reference: Image.Image, target: Image.Image) -> tuple[int, int, int, int]:
    ref_left, ref_top, ref_right, ref_bottom = content_bbox(reference)
    ref_width, ref_height = reference.size
    target_width, target_height = target.size

    left_ratio = ref_left / ref_width
    top_ratio = ref_top / ref_height
    right_ratio = (ref_width - ref_right) / ref_width
    bottom_ratio = (ref_height - ref_bottom) / ref_height

    left = int(target_width * left_ratio)
    top = int(target_height * top_ratio)
    right = target_width - int(target_width * right_ratio)
    bottom = target_height - int(target_height * bottom_ratio)
    return (left, top, right, bottom)


def fitted_bbox(bbox: tuple[int, int, int, int], cols: int, rows: int) -> tuple[int, int, int, int]:
    left, top, right, bottom = bbox
    width = right - left
    height = bottom - top
    fitted_width = (width // cols) * cols
    fitted_height = (height // rows) * rows
    left += (width - fitted_width) // 2
    top += (height - fitted_height) // 2
    return (left, top, left + fitted_width, top + fitted_height)


def palette_bbox_from_cover(image: Image.Image, threshold: int = 80) -> tuple[int, int, int, int]:
    rgb = image.convert("RGB")
    outer_left, outer_top, outer_right, outer_bottom = content_bbox(rgb)
    _, height = rgb.size
    pixels = rgb.load()
    content_width = outer_right - outer_left

    row_activity: list[tuple[int, int]] = []
    for y in range(outer_top, outer_bottom):
        active_pixels = 0
        for x in range(outer_left, outer_right):
            red, green, blue = pixels[x, y]
            average = (red + green + blue) // 3
            if average < 245:
                active_pixels += 1
        row_activity.append((y, active_pixels))

    upper_rows = row_activity[: max(2, len(row_activity) // 3)]
    strongest_drop_y = outer_top
    strongest_drop = 0
    for index in range(1, len(upper_rows)):
        prev_y, prev_count = upper_rows[index - 1]
        curr_y, curr_count = upper_rows[index]
        drop = prev_count - curr_count
        if drop > strongest_drop:
            strongest_drop = drop
            strongest_drop_y = curr_y

    if strongest_drop == 0:
        return fitted_bbox((outer_left, outer_top, outer_right, outer_bottom), 4, 3)

    top = max(0, strongest_drop_y - 42)
    bottom = min(height, outer_bottom - 8)
    return (outer_left, top, outer_right, bottom)


def translate_description(text: str) -> str:
    if text in DESCRIPTION_TRANSLATIONS:
        return DESCRIPTION_TRANSLATIONS[text]
    return text


def translate_use(text: str) -> str:
    if text in USE_TRANSLATIONS:
        return USE_TRANSLATIONS[text]

    replacements = [
        ("All over-lid shade", "全眼铺色"),
        ("all-over lid shade", "全眼铺色"),
        ("All-over lid shade", "全眼铺色"),
        ("Base tone", "底色"),
        ("base tone", "底色"),
        ("transitional shade", "过渡色"),
        ("inner corner", "眼头"),
        ("inner corners", "眼头"),
        ("brow bone", "眉骨"),
        ("highlight", "提亮"),
        ("smokey eye", "烟熏妆"),
        ("soft eyeliner", "柔和眼线"),
        ("outer corners", "眼尾"),
        ("creases", "眼窝"),
        ("crease", "眼窝"),
        ("blush", "腮红"),
        ("contour", "修容"),
        ("brows", "眉部"),
        ("mix", "混合"),
        ("lighten", "提亮"),
        ("soften", "柔和"),
    ]
    result = text
    for source, target in replacements:
        result = re.sub(source, target, result, flags=re.IGNORECASE)
    return result


def build_readme(
    title: str,
    cover_name: str,
    shades: list[Shade],
    slice_names: list[str],
    slice_context: SliceContext,
) -> str:
    blocks = [f"# {title}", f"![id]({cover_name})", ""]
    if slice_context.source_kind == "id":
        blocks.append(
            "> 提示：本页切片来自官网开盖图 `id`，并非独立的带描述色板图 `icons`。"
        )
        if slice_context.has_occluded_top_row_risk:
            blocks.append(
                "> 第一排色块可能会受到盖子边缘轻微遮挡；如果后续拿到带描述色板图，应优先用 `icons` 重新切图。"
            )
        blocks.append("")
    for shade, slice_name in zip(shades, slice_names):
        chinese_name = NAME_TRANSLATIONS.get(shade.name, shade.name)
        chinese_description = translate_description(shade.description)
        chinese_use = translate_use(shade.use)
        blocks.append(f"## Shade {shade.number}: {shade.name} — {shade.description}")
        blocks.append(f"![Shade {shade.number} {shade.name}](./slices/{slice_name})")
        blocks.append("")
        blocks.append(f"Use: {shade.use}")
        blocks.append("")
        blocks.append(
            f"##### 色号 {shade.number}：{chinese_name} ({shade.name}) —— {chinese_description}"
        )
        blocks.append(f"用途：{chinese_use}")
        if shade.warning:
            blocks.append("")
            blocks.append(shade.warning)
            blocks.append("提示：在美国法规下，此色含有未获 FDA 批准用于眼周的色料。")
        blocks.append("")
    return "\n".join(blocks).strip() + "\n"


def derive_homepage_label(palette_dir: Path, title: str, explicit_label: str | None) -> str:
    if explicit_label:
        return explicit_label.strip()
    if palette_dir.name in HOMEPAGE_LABELS:
        return HOMEPAGE_LABELS[palette_dir.name]
    return title.removeprefix("Viseart ").strip()


def update_docs_index(repo_root: Path, palette_dir: Path, homepage_label: str) -> Path:
    docs_readme = repo_root / "docs" / "README.md"
    lines = docs_readme.read_text(encoding="utf-8").splitlines()
    relative_path = f"./viseart/{palette_dir.name}/README.md"
    entry = f"- 📄 [{homepage_label}]({relative_path})"

    if entry in lines:
        return docs_readme

    updated_lines: list[str] = []
    inserted = False
    inside_section = False

    for line in lines:
        updated_lines.append(line)
        if line.strip() == HOMEPAGE_SECTION:
            inside_section = True
            continue

        if inside_section and line.startswith("### "):
            updated_lines.insert(len(updated_lines) - 1, entry)
            inserted = True
            inside_section = False

    if inside_section and not inserted:
        updated_lines.append(entry)
        inserted = True

    if not inserted:
        if updated_lines and updated_lines[-1] != "":
            updated_lines.append("")
        updated_lines.append(HOMEPAGE_SECTION)
        updated_lines.append(entry)

    docs_readme.write_text("\n".join(updated_lines).rstrip() + "\n", encoding="utf-8")
    return docs_readme


def save_slices(
    icons_path: Path,
    output_dir: Path,
    shades: list[Shade],
    cols: int,
    rows: int,
    reference_icons: Path | None,
    slice_ext: str,
    slice_name_mode: str,
    use_cover_palette_bbox: bool,
    crop_bbox: tuple[int, int, int, int] | None,
) -> list[str]:
    image = Image.open(icons_path)
    if crop_bbox:
        bbox = crop_bbox
    elif use_cover_palette_bbox:
        bbox = palette_bbox_from_cover(image)
    elif reference_icons:
        reference = Image.open(reference_icons)
        bbox = scaled_reference_bbox(reference, image)
    else:
        bbox = content_bbox(image)
    bbox = fitted_bbox(bbox, cols, rows)

    left, top, right, bottom = bbox
    content = image.crop((left, top, right, bottom))
    cell_width = content.width // cols
    cell_height = content.height // rows

    output_dir.mkdir(parents=True, exist_ok=True)
    names: list[str] = []

    for index, shade in enumerate(shades):
        row = index // cols
        col = index % cols
        crop_left = col * cell_width
        crop_top = row * cell_height
        crop_right = crop_left + cell_width
        crop_bottom = crop_top + cell_height
        tile = content.crop((crop_left, crop_top, crop_right, crop_bottom))

        prefix = f"{shade.number:02d}"
        if slice_name_mode == "number-name":
            filename = f"{prefix}_{sanitize_name(shade.name)}.{slice_ext}"
        else:
            filename = f"{prefix}.{slice_ext}"

        save_path = output_dir / filename
        if slice_ext == "jpg":
            tile.convert("RGB").save(save_path, quality=95)
        else:
            tile.save(save_path)
        names.append(filename)
    return names


def main() -> None:
    args = parse_args()
    palette_dir = args.palette_dir.resolve()
    repo_root = palette_dir.parents[2]
    source_readme = (args.source_readme or palette_dir / "README.md").resolve()
    product_url = product_url_for_palette(palette_dir, args.product_url)

    page_data: ProductPageData | None = None
    if product_url:
        page_data = fetch_product_page_data(product_url)

    if source_readme.exists():
        try:
            title, shades = parse_shades(source_readme)
        except ValueError:
            if not page_data or not page_data.shade_text:
                raise
            title, shades = parse_shades_from_text(
                page_data.shade_text,
                palette_dir.name,
                fallback_title=default_title_for_palette(palette_dir.name)
                if palette_dir.name in PALETTE_TITLE_PARTS
                else page_data.title,
            )
    else:
        if not page_data or not page_data.shade_text:
            raise FileNotFoundError(
                f"No local shade text found at {source_readme} and no parsable product page data available"
            )
        title, shades = parse_shades_from_text(
            page_data.shade_text,
            palette_dir.name,
            fallback_title=default_title_for_palette(palette_dir.name)
            if palette_dir.name in PALETTE_TITLE_PARTS
            else page_data.title,
        )

    cols, rows = tuple(args.grid) if args.grid else infer_grid(len(shades))

    if args.download_product_assets:
        try:
            cover_path = detect_file(palette_dir, ["id.png", "id.jpg", "id.jpeg", "id.webp"])
        except FileNotFoundError:
            if not product_url:
                raise ValueError("No local id image and no product URL available for download")
            cover_path = download_primary_product_image(product_url, palette_dir / "id.jpg")
    else:
        cover_path = detect_file(palette_dir, ["id.png", "id.jpg", "id.jpeg", "id.webp"])

    use_cover_palette_bbox = False
    try:
        icons_path = detect_file(palette_dir, ["icons.png", "icons.jpg", "icons.jpeg", "icons.webp"])
    except FileNotFoundError:
        icons_path = cover_path
        use_cover_palette_bbox = True

    slice_context = SliceContext(
        source_kind="id" if use_cover_palette_bbox else "icons",
        has_occluded_top_row_risk=use_cover_palette_bbox,
    )

    if args.slice_ext:
        slice_ext = args.slice_ext
    else:
        source_ext = icons_path.suffix.lower().lstrip(".")
        slice_ext = source_ext if source_ext in {"png", "jpg"} else "png"

    slice_names = save_slices(
        icons_path=icons_path,
        output_dir=palette_dir / "slices",
        shades=shades,
        cols=cols,
        rows=rows,
        reference_icons=args.reference_icons.resolve() if args.reference_icons else None,
        slice_ext=slice_ext,
        slice_name_mode=args.slice_name_mode,
        use_cover_palette_bbox=use_cover_palette_bbox,
        crop_bbox=tuple(args.crop_bbox) if args.crop_bbox else None,
    )

    readme_body = build_readme(title, cover_path.name, shades, slice_names, slice_context)
    if args.rewrite_readme:
        (palette_dir / "README.md").write_text(readme_body, encoding="utf-8")
        print(f"Rewrote README: {palette_dir / 'README.md'}")
    else:
        print(readme_body)

    if args.update_docs_index:
        homepage_label = derive_homepage_label(palette_dir, title, args.homepage_label)
        docs_readme = update_docs_index(repo_root, palette_dir, homepage_label)
        print(f"Updated docs index: {docs_readme}")

    print(f"Generated {len(slice_names)} slices in {palette_dir / 'slices'}")


if __name__ == "__main__":
    main()