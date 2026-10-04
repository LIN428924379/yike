"""精致扁平图标（对标微信/支付宝那种完成度）。

和上一版的区别：
  1. 底色用**温和的垂直渐变**，不是纯色平涂 —— 微信就是这么做的
  2. 颜色调**沉**，去掉荧光感 —— 亮红显廉价，深红才高级
  3. 预览图带圆角，模拟手机桌面上的真实效果

输出：每个方案 512px 成品 + 一张预览对比图（带圆角 / 48px / 24px）

用法：
    python tools/make_polished_icons.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets-src" / "designs-polished"

SIZE = 512
SS = 4

WHITE = (255, 255, 255)
# 沉的红色：上面亮一点，下面深，比纯亮红有质感
RED_TOP = (242, 92, 78)
RED_BOTTOM = (198, 42, 34)
# 沉的深色底
DARK_TOP = (38, 41, 51)
DARK_BOTTOM = (19, 21, 28)


def font(size: int):
    for name in ("msyhbd.ttc", "msyh.ttc", "simhei.ttf"):
        path = Path(r"C:\Windows\Fonts") / name
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return None


def gradient(size: int, top, bottom) -> Image.Image:
    """垂直渐变 —— 微信那种"上亮下深"，比纯色有厚度。"""
    image = Image.new("RGB", (size, 1))
    pen = ImageDraw.Draw(image)
    for x in range(size):
        t = x / max(1, size - 1)
        pen.point((x, 0), fill=tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return image.resize((size, size), Image.BILINEAR)


def rounded_mask(size: int, ratio: float = 0.225) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1],
                                           radius=round(ratio * size), fill=255)
    return mask


# --------------------------------------------------------------------------- #
def design_glyph() -> Image.Image:
    """汉字「刻」—— 红渐变底 + 纯白粗体字。"""
    image = gradient(SIZE * SS, RED_TOP, RED_BOTTOM).convert("RGBA")
    pen = ImageDraw.Draw(image)
    c = SIZE * SS / 2
    glyph = font(round(0.545 * SIZE * SS))
    box = pen.textbbox((0, 0), "刻", font=glyph)
    # 汉字的视觉重心偏上一点，稍微下移会更稳
    pen.text((c - (box[2] - box[0]) / 2 - box[0], c - (box[3] - box[1]) / 2 - box[1] + 0.012 * SIZE * SS),
             "刻", font=glyph, fill=WHITE)
    return image


def design_hourglass() -> Image.Image:
    """沙漏 —— 深色渐变底，白色剪影 + 红色沙。"""
    image = gradient(SIZE * SS, DARK_TOP, DARK_BOTTOM).convert("RGBA")
    pen = ImageDraw.Draw(image)
    u = SIZE * SS
    c = u / 2

    bar_w, bar_h = 0.42 * u, 0.052 * u
    top_y, bot_y = 0.235 * u, 0.765 * u
    neck = 0.018 * u
    half = bar_w / 2 * 0.90

    for y in (top_y, bot_y):
        pen.rounded_rectangle([c - bar_w / 2, y - bar_h / 2, c + bar_w / 2, y + bar_h / 2],
                              radius=bar_h / 2, fill=WHITE)

    pen.polygon([(c - half, top_y + bar_h / 2), (c + half, top_y + bar_h / 2), (c, c - neck)], fill=WHITE)
    pen.polygon([(c - half, bot_y - bar_h / 2), (c + half, bot_y - bar_h / 2), (c, c + neck)], fill=WHITE)

    # 下半部的红沙
    sand = 0.19 * u
    pen.polygon([(c - half * 0.60, bot_y - bar_h / 2), (c + half * 0.60, bot_y - bar_h / 2),
                 (c, bot_y - bar_h / 2 - sand)],
                fill=tuple(RED_TOP))
    return image


def design_ring() -> Image.Image:
    """进度环 —— 四分之三的粗环，圆头端点。和 App 里那个倒计时环同源。"""
    image = gradient(SIZE * SS, DARK_TOP, DARK_BOTTOM).convert("RGBA")
    pen = ImageDraw.Draw(image)
    u = SIZE * SS
    c = u / 2
    r = 0.265 * u
    thickness = 0.105 * u

    pen.arc([c - r, c - r, c + r, c + r], -85, 205,
            fill=tuple(RED_TOP), width=round(thickness))
    half = thickness / 2
    for angle in (-85, 205):
        rad = math.radians(angle)
        x, y = c + r * math.cos(rad), c + r * math.sin(rad)
        pen.ellipse([x - half, y - half, x + half, y + half], fill=tuple(RED_TOP))
    return image


def design_dot_ring() -> Image.Image:
    """环与点 —— 完整的白环 + 一颗红点停在上方，像指针停在某一刻。"""
    image = gradient(SIZE * SS, DARK_TOP, DARK_BOTTOM).convert("RGBA")
    pen = ImageDraw.Draw(image)
    u = SIZE * SS
    c = u / 2
    r = 0.245 * u
    thickness = 0.082 * u

    pen.ellipse([c - r - thickness / 2, c - r - thickness / 2,
                 c + r + thickness / 2, c + r + thickness / 2],
                outline=WHITE, width=round(thickness))

    dot_r = 0.088 * u
    dy = c - r
    pen.ellipse([c - dot_r, dy - dot_r, c + dot_r, dy + dot_r], fill=tuple(RED_TOP))
    return image


DESIGNS = [
    ("A-刻字", design_glyph),
    ("B-沙漏", design_hourglass),
    ("C-进度环", design_ring),
    ("D-环与点", design_dot_ring),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    made = []
    for name, builder in DESIGNS:
        full = builder().resize((SIZE, SIZE), Image.LANCZOS).convert("RGB")
        full.save(OUT / f"{name}.png", format="PNG", optimize=True)
        made.append((name, full))
        print(f"  {name}")

    # 预览：带圆角的大图（模拟手机桌面）+ 48px + 24px
    big, mid, tiny, label_w, pad, gap = 230, 46, 24, 140, 30, 32
    width = pad * 2 + label_w + big + gap + mid + gap + tiny
    height = pad * 2 + len(made) * (big + gap) - gap
    sheet = Image.new("RGB", (width, height), (14, 14, 18))
    pen = ImageDraw.Draw(sheet)
    label_font = font(30)
    small_font = font(17)

    for index, (name, image) in enumerate(made):
        y = pad + index * (big + gap)
        pen.text((pad, y + big / 2 - 18), name, font=label_font, fill=(228, 228, 234))

        # 大图带圆角（手机上的真实样子）—— 先缩到目标尺寸，再套圆角蒙版
        rounded = image.resize((big, big), Image.LANCZOS).convert("RGBA")
        rounded.putalpha(rounded_mask(big))
        x = pad + label_w
        sheet.paste(rounded, (x, y), rounded)

        x += big + gap
        small = image.resize((mid, mid), Image.LANCZOS)
        sheet.paste(small, (x, y + big - mid))
        if small_font:
            pen.text((x, y + big - mid - 24), "48px", font=small_font, fill=(135, 135, 145))

        x += mid + gap
        tiniest = image.resize((tiny, tiny), Image.LANCZOS)
        sheet.paste(tiniest, (x + 10, y + big - tiny))
        if small_font:
            pen.text((x, y + big - tiny - 24), "24px", font=small_font, fill=(135, 135, 145))

    sheet_path = OUT / "预览.png"
    sheet.save(sheet_path, format="PNG", optimize=True)
    print(f"\n预览图：{sheet_path.relative_to(ROOT)}")
    print("每行：手机上的样子（带圆角） / 48px / 24px")
    return 0


if __name__ == "__main__":
    sys.exit(main())
