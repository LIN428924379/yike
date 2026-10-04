"""纯几何平涂图标 —— 围绕「四分之一」这个核心概念。

"一刻" = 一刻钟 = 四分之一小时。这个概念本身就是一个几何构造：
把任何一个完整形状切成四份，其中一份是红的，剩下的三份是灰的。

好的几何图标都有一个"聪明的构造"（Mastercard 是两个圆相交、
Google Photos 是四色块绕中心旋转），而不是"一个形状居中放在方框里"。
所以这一版每一张都围绕"四份里的一份"来做。

规矩：纯色平涂，不用渐变、不用阴影、不用材质。

用法：
    python tools/make_quarter_icons.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets-src" / "designs-quarter"

SIZE = 512
SS = 4

DARK = (22, 24, 29, 255)
GRAY = (60, 65, 76, 255)
WHITE = (255, 255, 255, 255)
RED = (240, 74, 60, 255)


def font(size: int):
    for name in ("msyhbd.ttc", "msyh.ttc", "simhei.ttf"):
        path = Path(r"C:\Windows\Fonts") / name
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return None


def new(bg) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGBA", (SIZE * SS, SIZE * SS), bg)
    return image, ImageDraw.Draw(image)


def rounded_rect(pen, x0, y0, x1, y1, radius, color) -> None:
    pen.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=color)


# --------------------------------------------------------------------------- #
def design_quarters() -> Image.Image:
    """四格：2x2 的方块，三灰一红。

    最直白的"四分之一"。四个方块紧凑成一个整体块，本身就是个正方形，
    所以整张图可以看成"一个正方形被分成了四份"。
    """
    image, pen = new(DARK)
    u = SIZE * SS
    side = 0.268 * u
    gap = 0.056 * u
    total = side * 2 + gap
    x0 = (u - total) / 2
    y0 = (u - total) / 2
    radius = side * 0.16

    for row in range(2):
        for col in range(2):
            x = x0 + col * (side + gap)
            y = y0 + row * (side + gap)
            last = (row == 1 and col == 1)
            rounded_rect(pen, x, y, x + side, y + side, radius, RED if last else GRAY)
    return image


def design_pie() -> Image.Image:
    """圆饼切掉四分之一：一个实心圆，右上缺掉 90°。

    缺掉的那块露出底色 —— "从时间里取走了一刻"。
    """
    image, pen = new(RED)
    u = SIZE * SS
    c = u / 2
    r = 0.305 * u
    # 从 -90° 开始，顺时针画 270° —— 右上角那块正好空着
    pen.pieslice([c - r, c - r, c + r, c + r], -90, 180, fill=WHITE)
    return image


def design_gauge() -> Image.Image:
    """量规：一个完整的环，四分之三是细白线，四分之一是粗红线。

    读作"计时器走到了四分之一"，是现代计时类图标里最干净的一种。
    """
    image, pen = new(u) if False else new(DARK)
    u = SIZE * SS
    c = u / 2
    r = 0.275 * u
    thin, thick = 0.055 * u, 0.115 * u

    box = [c - r, c - r, c + r, c + r]
    # 白弧：四分之三，细
    pen.arc(box, 0, 270, fill=WHITE, width=round(thin))
    # 红弧：四分之一，粗。
    # 两端不做圆头 —— 平直的径向切口更利落，也更像"刻度"而不是"钩子"。
    pen.arc(box, -90, 0, fill=RED, width=round(thick))
    return image


def design_dial() -> Image.Image:
    """表盘：白色圆环 + 内部十字，把圆分成四格，右上那格是红的。

    同时读作"钟面"和"四分之一"，缩到 24px 依然清楚。
    """
    image, pen = new(DARK)
    u = SIZE * SS
    c = u / 2
    r = 0.305 * u
    thickness = 0.062 * u

    # 外圈
    pen.ellipse([c - r, c - r, c + r, c + r], outline=WHITE, width=round(thickness))

    # 内部十字：把圆分成四格
    inner = r - thickness
    bar = 0.035 * u
    pen.rectangle([c - bar / 2, c - inner, c + bar / 2, c + inner], fill=WHITE)
    pen.rectangle([c - inner, c - bar / 2, c + inner, c + bar / 2], fill=WHITE)

    # 右上那一格的红色扇形（半径缩进去一点，别压住外圈）
    pen.pieslice([c - inner, c - inner, c + inner, c + inner], -90, 0, fill=RED)
    return image


def design_glyph_quarter() -> Image.Image:
    """汉字「刻」压在四格上 —— 文字版和图形版的折中。"""
    image, pen = new(RED)
    u = SIZE * SS
    c = u / 2
    glyph = font(round(0.50 * u))
    box = pen.textbbox((0, 0), "刻", font=glyph)
    pen.text((c - (box[2] - box[0]) / 2 - box[0], c - (box[3] - box[1]) / 2 - box[1] + 0.01 * u),
             "刻", font=glyph, fill=WHITE)
    return image


DESIGNS = [
    ("A-四格", design_quarters),
    ("B-圆饼", design_pie),
    ("C-量规", design_gauge),
    ("D-表盘", design_dial),
    ("E-刻字", design_glyph_quarter),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    made = []
    for name, builder in DESIGNS:
        full = builder().resize((SIZE, SIZE), Image.LANCZOS).convert("RGB")
        full.save(OUT / f"{name}.png", format="PNG", optimize=True)
        made.append((name, full))
        print(f"  {name}")

    def mask(size: int, ratio: float = 0.225) -> Image.Image:
        m = Image.new("L", (size, size), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, size - 1, size - 1],
                                            radius=round(ratio * size), fill=255)
        return m

    big, mid, tiny, label_w, pad, gap = 220, 46, 24, 132, 28, 30
    width = pad * 2 + label_w + big + gap + mid + gap + tiny
    height = pad * 2 + len(made) * (big + gap) - gap
    sheet = Image.new("RGB", (width, height), (13, 13, 17))
    pen = ImageDraw.Draw(sheet)
    label_font = font(28)
    small_font = font(17)

    for index, (name, image) in enumerate(made):
        y = pad + index * (big + gap)
        pen.text((pad, y + big / 2 - 17), name, font=label_font, fill=(228, 228, 234))

        rounded = image.resize((big, big), Image.LANCZOS).convert("RGBA")
        rounded.putalpha(mask(big))
        x = pad + label_w
        sheet.paste(rounded, (x, y), rounded)

        x += big + gap
        sheet.paste(image.resize((mid, mid), Image.LANCZOS), (x, y + big - mid))
        if small_font:
            pen.text((x, y + big - mid - 24), "48px", font=small_font, fill=(135, 135, 145))

        x += mid + gap
        sheet.paste(image.resize((tiny, tiny), Image.LANCZOS), (x + 10, y + big - tiny))
        if small_font:
            pen.text((x, y + big - tiny - 24), "24px", font=small_font, fill=(135, 135, 145))

    sheet_path = OUT / "预览.png"
    sheet.save(sheet_path, format="PNG", optimize=True)
    print(f"\n预览：{sheet_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
