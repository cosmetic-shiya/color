#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import unicodedata
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


TITLE_TRANSLATIONS = {
    "big-12-matte-cool2": "Viseart 12色 大号 哑光冷调盘 Matte Cool 2",
    "big-12-matte-neutral": "Viseart 12色 大号/小号 哑光中性盘 Matte Neutral",
    "middle-35-pro-x1": "Viseart 35色 中盘 Grande Pro 1x",
}


@dataclass
class Shade:
    number: int
    name: str
    description: str
    use: str
    warning: str = ""


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


def parse_shades(source_path: Path) -> tuple[str, list[Shade]]:
    lines = source_path.read_text(encoding="utf-8").splitlines()
    folder_name = source_path.parent.name
    title = TITLE_TRANSLATIONS.get(folder_name, folder_name)
    for line in lines:
        if line.startswith("# "):
            heading_title = line[2:].strip()
            if heading_title == folder_name and folder_name in TITLE_TRANSLATIONS:
                title = TITLE_TRANSLATIONS[folder_name]
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
        raise ValueError(f"No shade entries found in {source_path}")
    return title, shades


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


def build_readme(title: str, cover_name: str, shades: list[Shade], slice_names: list[str]) -> str:
    blocks = [f"# {title}", f"![id]({cover_name})", ""]
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


def save_slices(
    icons_path: Path,
    output_dir: Path,
    shades: list[Shade],
    cols: int,
    rows: int,
    reference_icons: Path | None,
    slice_ext: str,
    slice_name_mode: str,
) -> list[str]:
    image = Image.open(icons_path)
    if reference_icons:
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
    source_readme = (args.source_readme or palette_dir / "README.md").resolve()
    title, shades = parse_shades(source_readme)

    cols, rows = tuple(args.grid) if args.grid else infer_grid(len(shades))
    icons_path = detect_file(palette_dir, ["icons.png", "icons.jpg", "icons.jpeg", "icons.webp"])
    cover_path = detect_file(palette_dir, ["id.png", "id.jpg", "id.jpeg", "id.webp"])

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
    )

    readme_body = build_readme(title, cover_path.name, shades, slice_names)
    if args.rewrite_readme:
        (palette_dir / "README.md").write_text(readme_body, encoding="utf-8")
        print(f"Rewrote README: {palette_dir / 'README.md'}")
    else:
        print(readme_body)

    print(f"Generated {len(slice_names)} slices in {palette_dir / 'slices'}")


if __name__ == "__main__":
    main()