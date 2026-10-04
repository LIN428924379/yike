"""扁平矢量风格的图标方案（对标微信/支付宝那种）。

设计原则：
  1. 只用纯色，不用渐变、不用阴影、不用材质 ✗
  2. 形状极简 —— 剪影要能认出来
  3. 必须通过"48px 测试"：缩小后还看得清才合格
  4. 一个图标最多两个颜色 + 一个底色

输出：每个方案 512px 的成品 + 一张对比图（240px / 48px / 24px 并排）

用法：
    python tools/make_flat_icons.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets-src" / "designs-flat"

SIZE = 512
SS = 4                      # 超采样，边缘才干净

RED = (255, 90, 77, 255)        # App 主色
DARK = (23, 26, 33, 255)        # App 的深色底
INK = (17, 24, 39, 255)
WHITE = (255, 255, 255, 255)
CREAM = (253, 253, 250, 255)


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


# --------------------------------------------------------------------------- #
def design_glyph() -> Image.Image:
    """汉字「刻」—— 和支付宝的「支」、淘宝的「淘」同一种思路。

    最少的笔画表达最多的意思；中文用户一眼就懂，而且没有任何番茄钟是这么做的。
    """
    image, pen = new(RED)
    c = SIZE * SS / 2
    glyph = font(round(0.60 * SIZE * SS))
    box = pen.textbbox((0, 0), "刻", font=glyph)
    pen.text((c - (box[2] - box[0]) / 2 - box[0], c - (box[3] - box[1]) / 2 - box[1]),
             "刻", font=glyph, fill=WHITE)
    return image


def design_hourglass() -> Image.Image:
    """沙漏 —— "一刻钟"的字面形状。纯几何，剪影极清晰。"""
    image, pen = new(DARK)
    u = SIZE * SS
    c = u / 2
    bar_w, bar_h = 0.44 * u, 0.055 * u
    top_y, bot_y = 0.20 * u, 0.80 * u
    neck = 0.022 * u

    # 上下两条横梁（圆角）
    for y in (top_y, bot_y):
        pen.rounded_rectangle([c - bar_w / 2, y - bar_h / 2, c + bar_w / 2, y + bar_h / 2],
                              radius=bar_h / 2, fill=WHITE)

    # 两个相对的三角锥（玻璃体）
    half = bar_w / 2 * 0.92
    pen.polygon([(c - half, top_y + bar_h / 2), (c + half, top_y + bar_h / 2), (c, c - neck)], fill=WHITE)
    pen.polygon([(c - half, bot_y - bar_h / 2), (c + half, bot_y - bar_h / 2), (c, c + neck)], fill=WHITE)

    # 下半部的红沙：把底锥挖出一个更小的红三角，形成"沙子堆"
    sand_h = 0.20 * u
    pen.polygon([(c - half * 0.62, bot_y - bar_h / 2), (c + half * 0.62, bot_y - bar_h / 2),
                 (c, bot_y - bar_h / 2 - sand_h)], fill=RED)
    return image


def design_tomato() -> Image.Image:
    """扁平番茄 —— 最"番茄钟"的形状，但做成干净的几何剪影。"""
    image, pen = new(CREAM)
    u = SIZE * SS
    c = u / 2
    body_r = 0.30 * u
    cy = c + 0.045 * u

    # 叶子：三片，简单有力
    top = cy - body_r * 0.86
    for dx, dy, spread in ((-0.62, -0.42, 0.30), (0.0, -0.62, 0.34), (0.62, -0.42, 0.30)):
        tip = (c + dx * body_r * 1.15, top + dy * body_r * 1.1)
        left = (c - spread * body_r * 0.42, top + body_r * 0.22)
        right = (c + spread * body_r * 0.42, top + body_r * 0.22)
        pen.polygon([tip, right, left], fill=RED)

    pen.ellipse([c - body_r, cy - body_r, c + body_r, cy + body_r], fill=RED)
    return image


def design_ring() -> Image.Image:
    """进度环 —— 一个四分之三的粗环，端点圆头。

    和 App 里那个倒计时圆环完全同源，缩到 24px 都还能看出"环"。
    """
    image, pen = new(DARK)
    u = SIZE * SS
    c = u / 2
    r = 0.285 * u
    thickness = 0.115 * u

    box = [c - r, c - r, c + r, c + r]
    pen.arc(box, -90, 200, fill=RED, width=round(thickness))
    half = thickness / 2
    for angle in (-90, 200):
        import math
        rad = math.radians(angle)
        x, y = c + r * math.cos(rad), c + r * math.sin(rad)
        pen.ellipse([x - half, y - half, x + half, y + half], fill=RED)
    return image


def design_dot_arc() -> Image.Image:
    """点与弧 —— 一个圆点悬在环的缺口处，"就在这一刻"。"""
    image, pen = new(DARK)
    u = SIZE * SS
    c = u / 2
    r = 0.26 * u
    thickness = 0.072 * u

    box = [c - r, c - r, c + r, c + r]
    pen.arc(box, 40, 320, fill=WHITE, width=round(thickness))
    half = thickness / 2
    import math
    for angle in (40, 320):
        rad = math.radians(angle)
        x, y = c + r * math.cos(rad), c + r * math.sin(rad)
        pen.ellipse([x - half, y - half, x + half, y + half], fill=WHITE)

    # 缺口处那个红点
    rad = math.radians(-40)
    pen.ellipse([c + r * math.cos(rad) - 0.085 * u, c + r * math.sin(rad) - 0.085 * u,
                 c + r * math.cos(rad) + 0.085 * u, c + r * math.sin(rad) + 0.085 * u], fill=RED)
    return image


DESIGNS = [
    ("1-刻字", design_glyph),
    ("2-沙漏", design_hourglass),
    ("3-番茄", design_tomato),
    ("4-进度环", design_ring),
    ("5-点与弧", design_dot_arc),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    made = []
    for name, builder in DESIGNS:
        full = builder().resize((SIZE, SIZE), Image.LANCZOS).convert("RGB")
        full.save(OUT / f"{name}.png", format="PNG", optimize=True)
        made.append((name, full))
        print(f"  {name}")

    # 对比图：每个方案并排显示 240px / 48px / 24px —— 缩不小就不合格
    big, mid, tiny, label_w, pad, gap = 240, 48, 24, 150, 30, 34
    width = pad * 2 + label_w + big + gap + mid + gap + tiny
    height = pad * 2 + len(made) * (big + gap) - gap
    sheet = Image.new("RGB", (width, height), (16, 16, 20))
    pen = ImageDraw.Draw(sheet)
    label_font = font(30)
    small_font = font(18)

    for index, (name, image) in enumerate(made):
        y = pad + index * (big + gap)
        pen.text((pad, y + big / 2 - 18), name, font=label_font, fill=(225, 225, 232))
        x = pad + label_w
        sheet.paste(image.resize((big, big), Image.LANCZOS), (x, y))
        x += big + gap
        sheet.paste(image.resize((mid, mid), Image.LANCZOS), (x, y + big - mid))
        if small_font:
            pen.text((x, y + big - mid - 26), "48px", font=small_font, fill=(140, 140, 150))
        x += mid + gap
        sheet.paste(image.resize((tiny, tiny), Image.LANCZOS), (x, y + big - tiny))
        if small_font:
            pen.text((x, y + big - tiny - 26), "24px", font=small_font, fill=(140, 140, 150))

    sheet_path = OUT / "对比图.png"
    sheet.save(sheet_path, format="PNG", optimize=True)
    print(f"\n共 {len(made)} 个方案")
    print(f"总览：{sheet_path.relative_to(ROOT)}")
    print("右边两列是缩小后的效果 —— 缩不小就说明不合格")
    return 0


if __name__ == "__main__":
    sys.exit(main())
