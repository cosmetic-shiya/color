#!/usr/bin/env python3
"""Screenshot a markdown file section by section (## headings).

Usage:
    python3 tools/screenshot_md.py docs/viseart/compare-violette.md
    python3 tools/screenshot_md.py docs/viseart/compare-violette.md --level 3
    python3 tools/screenshot_md.py docs/viseart/compare-violette.md --out docs/viseart/screenshots
"""

import argparse
import asyncio
import re
import sys
from pathlib import Path
import markdown
from playwright.async_api import async_playwright

CSS = """
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  font-size: 14px;
  line-height: 1.6;
  color: #24292e;
  background: #ffffff;
  max-width: 900px;
  margin: 0 auto;
  padding: 24px 32px 40px;
}
h1 { font-size: 1.8em; border-bottom: 1px solid #eaecef; padding-bottom: .3em; margin-bottom: .8em; }
h2 { font-size: 1.4em; border-bottom: 1px solid #eaecef; padding-bottom: .3em; margin-top: 1.5em; }
h3 { font-size: 1.1em; margin-top: 1.2em; }
table { border-collapse: collapse; margin: 1em 0; }
th, td { border: 1px solid #dfe2e5; padding: 8px 16px; text-align: center; }
th { background: #f6f8fa; font-weight: 600; }
img { max-width: 120px; height: auto; display: block; margin: 4px auto; }
hr { border: none; border-top: 1px solid #eaecef; margin: 1.5em 0; }
p { margin: .5em 0; }
strong { font-weight: 600; }
"""


def split_by_heading(md_text: str, level: int = 2) -> list[tuple[str, str]]:
    """Split markdown into sections at the given heading level."""
    pattern = re.compile(r'^#{' + str(level) + r'}\s+(.+)$', re.MULTILINE)
    matches = list(pattern.finditer(md_text))

    sections = []
    first_start = matches[0].start() if matches else len(md_text)
    preamble = md_text[:first_start].strip()
    if preamble:
        sections.append(('__preamble__', preamble))

    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md_text)
        body = md_text[start:end].strip()
        sections.append((title, body))

    return sections


def md_to_html(md_text: str) -> str:
    """Convert markdown to full HTML (image paths stay relative to the HTML file)."""
    body_html = markdown.markdown(
        md_text,
        extensions=['tables', 'fenced_code', 'nl2br'],
    )
    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<style>{CSS}</style>
</head>
<body>
{body_html}
</body>
</html>"""


def safe_filename(title: str) -> str:
    s = re.sub(r'[^\w一-鿿\s-]', '', title)
    s = re.sub(r'\s+', '_', s.strip())
    return s[:60] or 'section'


async def screenshot_sections(md_path: Path, out_dir: Path, level: int = 2):
    md_text = md_path.read_text(encoding='utf-8')
    base_dir = md_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    sections = split_by_heading(md_text, level)
    print(f"Found {len(sections)} section(s) at H{level} level")

    # Write temp HTML files beside the markdown so relative image paths work
    # under a file:// URL on the same origin.
    tmp_html = base_dir / '__screenshot_md_tmp__.html'

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 960, 'height': 800})

        try:
            for idx, (title, body) in enumerate(sections):
                tmp_html.write_text(md_to_html(body), encoding='utf-8')
                await page.goto(f'file://{tmp_html.resolve()}', wait_until='load')
                # Wait for every <img> to finish loading
                await page.evaluate("""() => {
                    const imgs = Array.from(document.querySelectorAll('img'));
                    return Promise.all(imgs.map(img =>
                        img.complete ? Promise.resolve() :
                        new Promise(r => { img.onload = r; img.onerror = r; })
                    ));
                }""")
                await page.wait_for_timeout(200)

                fname = "00_preamble.png" if title == '__preamble__' else f"{idx:02d}_{safe_filename(title)}.png"
                out_path = out_dir / fname
                await page.screenshot(path=str(out_path), full_page=True)
                print(f"  → {out_path.relative_to(md_path.parent.parent.parent)}")
        finally:
            tmp_html.unlink(missing_ok=True)
            await browser.close()

    print(f"\nDone. {len(sections)} screenshots in {out_dir}")


def main():
    parser = argparse.ArgumentParser(description="Screenshot a markdown file by section")
    parser.add_argument('md_file', help="Path to the markdown file")
    parser.add_argument('--level', type=int, default=2, help="Heading level to split on (default: 2 for ##)")
    parser.add_argument('--out', help="Output directory (default: <md_dir>/screenshots/<md_stem>/)")
    args = parser.parse_args()

    md_path = Path(args.md_file).resolve()
    if not md_path.exists():
        print(f"Error: {md_path} not found", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.out).resolve() if args.out else md_path.parent / 'screenshots' / md_path.stem
    asyncio.run(screenshot_sections(md_path, out_dir, args.level))


if __name__ == '__main__':
    main()
