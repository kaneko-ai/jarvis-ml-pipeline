"""Generate OGP image and favicon assets for docs/ static site.

Usage:
    python scripts/generate_site_assets.py
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def _load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                pass
    return ImageFont.load_default()


def _draw_vertical_gradient(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    top: tuple[int, int, int],
    bottom: tuple[int, int, int],
) -> None:
    for y in range(height):
        t = y / max(height - 1, 1)
        color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        draw.line([(0, y), (width, y)], fill=color)


def generate_og_image() -> None:
    width, height = 1200, 630
    image = Image.new("RGB", (width, height), "#0F172A")
    draw = ImageDraw.Draw(image)

    _draw_vertical_gradient(draw, width, height, (15, 23, 42), (30, 27, 75))

    # soft glow
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((-140, -120, 420, 440), fill=(99, 102, 241, 70))
    glow_draw.ellipse((760, 120, 1320, 680), fill=(139, 92, 246, 90))
    image = Image.alpha_composite(image.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(image)

    # card
    card = (70, 90, 1130, 540)
    draw.rounded_rectangle(card, radius=30, fill=(15, 23, 42), outline=(99, 102, 241), width=3)

    title_font = _load_font(62)
    subtitle_font = _load_font(32)
    body_font = _load_font(28)

    draw.text((120, 150), "JARVIS Research OS", font=title_font, fill=(241, 245, 249))
    draw.text(
        (120, 240),
        "AI-Powered Literature Review Platform",
        font=subtitle_font,
        fill=(148, 163, 184),
    )

    features = [
        "Evidence Grading",
        "Citation Analysis",
        "Contradiction Detection",
    ]
    y = 320
    for feature in features:
        draw.ellipse((120, y + 10, 140, y + 30), fill=(99, 102, 241))
        draw.text((160, y), feature, font=body_font, fill=(226, 232, 240))
        y += 60

    draw.rounded_rectangle((790, 160, 1080, 430), radius=20, fill=(30, 41, 59))
    draw.rectangle((825, 210, 1045, 230), fill=(99, 102, 241))
    draw.rectangle((825, 250, 995, 270), fill=(6, 182, 212))
    draw.rectangle((825, 290, 960, 310), fill=(16, 185, 129))
    draw.rectangle((825, 330, 1020, 350), fill=(139, 92, 246))
    draw.text((825, 380), "Live Demo Ready", font=_load_font(24), fill=(241, 245, 249))

    (DOCS / "og-image.png").parent.mkdir(parents=True, exist_ok=True)
    image.save(DOCS / "og-image.png", format="PNG", optimize=True)


def _generate_icon(size: int) -> Image.Image:
    image = Image.new("RGBA", (size, size), (15, 23, 42, 255))
    draw = ImageDraw.Draw(image)
    _draw_vertical_gradient(draw, size, size, (49, 46, 129), (139, 92, 246))

    pad = int(size * 0.12)
    draw.rounded_rectangle(
        (pad, pad, size - pad, size - pad),
        radius=max(4, int(size * 0.16)),
        fill=(15, 23, 42, 230),
        outline=(129, 140, 248, 255),
        width=max(1, size // 32),
    )

    # Stylized J
    stroke = max(1, size // 12)
    x_mid = size // 2
    y_top = int(size * 0.28)
    y_bottom = int(size * 0.70)
    radius = int(size * 0.18)
    draw.line([(x_mid, y_top), (x_mid, y_bottom)], fill=(226, 232, 240, 255), width=stroke)
    draw.arc(
        (x_mid - radius, y_bottom - radius, x_mid + radius, y_bottom + radius),
        start=45,
        end=210,
        fill=(226, 232, 240, 255),
        width=stroke,
    )
    return image


def generate_icons() -> None:
    icon16 = _generate_icon(16)
    icon32 = _generate_icon(32)
    apple = _generate_icon(180)
    icon192 = _generate_icon(192)
    icon512 = _generate_icon(512)

    icon16.save(DOCS / "favicon-16x16.png", format="PNG", optimize=True)
    icon32.save(DOCS / "favicon-32x32.png", format="PNG", optimize=True)
    apple.save(DOCS / "apple-touch-icon.png", format="PNG", optimize=True)
    icon192.save(DOCS / "icon-192.png", format="PNG", optimize=True)
    icon512.save(DOCS / "icon-512.png", format="PNG", optimize=True)

    # Multi-size ICO
    icon32.convert("RGBA").save(
        DOCS / "favicon.ico",
        sizes=[(16, 16), (32, 32)],
        format="ICO",
    )


def write_manifest() -> None:
    manifest = {
        "name": "JARVIS Research OS",
        "short_name": "JARVIS",
        "description": "AI-powered research assistant for systematic literature reviews",
        "start_url": "/jarvis-ml-pipeline/",
        "scope": "/jarvis-ml-pipeline/",
        "display": "standalone",
        "background_color": "#0F172A",
        "theme_color": "#6366F1",
        "icons": [
            {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
        ],
    }
    (DOCS / "site.webmanifest").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    generate_og_image()
    generate_icons()
    write_manifest()
    print("Generated OGP and favicon assets in docs/")


if __name__ == "__main__":
    main()
