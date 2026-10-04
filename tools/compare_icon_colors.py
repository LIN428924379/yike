"""配色对比：深色版 vs 白底版。

同一个"量规"设计（四分之三的环 + 四分之一红弧），只换配色，
并排放在一起比较，附带 48px / 24px 的缩小效果。

用法：
    python tools/compare_icon_colors.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets-src" / "designs-quarter" / "配色对比.png"

SIZE = 1024
SS = 2                      # 已经够大，不用 4 倍

RED = (240, 74, 60)
INK = (22, 24, 29)          # App 里的深色，不是纯黑 —— 更耐看
WHITE = (255, 255, 255)

VARIANTS = [
    ("深色版", INK, WHITE, 0.115, 0.055),
    ("白底版", WHITE, INK, 0.115, 0.055),
]


def font(size: int):
    for name in ("msyhbd.ttc", "msyh.ttc", "simhei.ttf"):
        path = Path(r"C:\Windows\Fonts") / name
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return None


def gauge(bg, ring_color, thick: float, thin: float) -> Image.Image:
    """画量规：四分之三细环 + 四分之一粗红弧。"""
    u = SIZE * SS
    image = Image.new("RGBA", (u, u), tuple(bg) + (255,))
    pen = ImageDraw.Draw(image)
    c = u / 2
    r = 0.275 * u
    box = [c - r, c - r, c + r, c + r]

    pen.arc(box, 0, 270, fill=tuple(ring_color) + (255,), width=round(thin * u))
    pen.arc(box, -90, 0, fill=tuple(RED) + (255,), width=round(thick * u))
    return image


def rounded(image: Image.Image, size: int, ratio: float = 0.225) -> Image.Image:
    small = image.resize((size, size), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1],
                                           radius=round(ratio * size), fill=255)
    small.putalpha(mask)
    return small


def main() -> int:
    big, mid, tiny, label_w, pad, gap = 260, 52, 26, 210, 34, 40
    width = pad * 2 + label_w + big + gap + mid + gap + tiny
    height = pad * 2 + len(VARIANTS) * (big + gap) - gap
    sheet = Image.new("RGB", (width, height), (208, 208, 214))   # 中性灰底，深浅色都能看清
    pen = ImageDraw.Draw(sheet)
    label_font = font(30)
    small_font = font(18)

    for index, (name, bg, ring, thick, thin) in enumerate(VARIANTS):
        image = gauge(bg, ring, thick, thin)
        y = pad + index * (big + gap)
        pen.text((pad, y + big / 2 - 18), name, font=label_font, fill=(30, 30, 36))

        x = pad + label_w
        sheet.paste(rounded(image, big), (x, y), rounded(image, big))

        x += big + gap
        sheet.paste(image.resize((mid, mid), Image.LANCZOS), (x, y + big - mid))
        if small_font:
            pen.text((x, y + big - mid - 26), "48px", font=small_font, fill=(60, 60, 68))

        x += mid + gap
        sheet.paste(image.resize((tiny, tiny), Image.LANCZOS), (x + 12, y + big - tiny))
        if small_font:
            pen.text((x, y + big - tiny - 26), "24px", font=small_font, fill=(60, 60, 68))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(OUT, format="PNG", optimize=True)
    print(f"✓ 对比图：{OUT.relative_to(ROOT)}")

    # 顺便把白底版单独存成一个大图，方便细看
    light = gauge(WHITE, INK, 0.115, 0.055).resize((SIZE, SIZE), Image.LANCZOS).convert("RGB")
    light_path = OUT.parent / "C-量规-白底版.png"
    light.save(light_path, format="PNG", optimize=True)
    print(f"✓ 白底版单图：{light_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
