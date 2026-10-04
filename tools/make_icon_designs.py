"""用代码画图标方案（几何 / 极简风格）。

为什么不用 AI 画图：图像生成模型能画水墨、水彩那种"有笔触"的图，
但画不了精确的几何图形（圆、环、刻度）。而「一刻」是个极简 App，
几何图标反而更配 —— 而且我能保证它是正圆、居中、边缘干净。

做法：4 倍超采样（先画 4096，再缩到 1024），这样边缘不会有锯齿。

用法：
    python tools/make_icon_designs.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets-src" / "designs"

SIZE = 1024
SS = 4                      # 超采样倍数
BG = (0, 0, 0, 255)         # 黑底
FG = (255, 255, 255, 255)   # 白图
GRAY = (150, 150, 155, 255)


def font(size: int):
    for name in ("msyhbd.ttc", "msyh.ttc", "simhei.ttf", "segoeui.ttf"):
        path = Path(r"C:\Windows\Fonts") / name
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return None


def canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGBA", (SIZE * SS, SIZE * SS), BG)
    return image, ImageDraw.Draw(image)


def dot(pen: ImageDraw.ImageDraw, x: float, y: float, r: float, color=FG) -> None:
    """一个圆点 —— 也用来给线条两端做圆头。"""
    pen.ellipse([x - r, y - r, x + r, y + r], fill=color)


def ring(pen: ImageDraw.ImageDraw, cx, cy, outer, thickness, color=FG) -> None:
    inner = outer - thickness
    pen.ellipse([cx - outer, cy - outer, cx + outer, cy + outer], fill=color)
    pen.ellipse([cx - inner, cy - inner, cx + inner, cy + inner], fill=BG)


def arc(pen: ImageDraw.ImageDraw, cx, cy, radius, start, end, thickness, color=FG) -> None:
    """带圆头的弧。"""
    box = [cx - radius, cy - radius, cx + radius, cy + radius]
    pen.arc(box, start, end, fill=color, width=round(thickness))
    half = thickness / 2
    for angle in (start, end):
        rad = math.radians(angle)
        dot(pen, cx + radius * math.cos(rad), cy + radius * math.sin(rad), half, color)


# --------------------------------------------------------------------------- #
def design_tomato() -> Image.Image:
    """番茄：圆身 + 五瓣叶。保留"番茄"这个出处，但画成干净的几何形。"""
    image, pen = canvas()
    c = SIZE * SS / 2
    body_r = 0.295 * SIZE * SS
    cy = c + 0.055 * SIZE * SS

    # 叶子：五片带尖的瓣，绕中心展开
    leaf_center_y = cy - body_r * 0.82
    for offset in (-58, -29, 0, 29, 58):
        angle = math.radians(-90 + offset)
        length = body_r * (0.75 if offset == 0 else 0.62)
        tip_x = c + length * math.cos(angle)
        tip_y = leaf_center_y + length * math.sin(angle)
        side = math.radians(90 + offset)
        w = body_r * 0.13
        left = (c + w * math.cos(side), leaf_center_y + w * math.sin(side))
        right = (c - w * math.cos(side), leaf_center_y - w * math.sin(side))
        pen.polygon([tip_x and (tip_x, tip_y), left, right], fill=FG)

    pen.ellipse([c - body_r, cy - body_r, c + body_r, cy + body_r], fill=FG)
    return image


def design_clock() -> Image.Image:
    """时钟：粗圆环 + 一根指针。最经典的极简计时器。"""
    image, pen = canvas()
    c = SIZE * SS / 2
    ring(pen, c, c, 0.345 * SIZE * SS, 0.062 * SIZE * SS)
    hand = 0.21 * SIZE * SS
    angle = math.radians(-60)
    dot(pen, c, c, 0.042 * SIZE * SS)
    pen.line([c, c, c + hand * math.cos(angle), c + hand * math.sin(angle)],
             fill=FG, width=round(0.052 * SIZE * SS))
    dot(pen, c + hand * math.cos(angle), c + hand * math.sin(angle), 0.026 * SIZE * SS)
    return image


def design_orbit() -> Image.Image:
    """轨道：一个小圆 + 一圈斜环（把原来那版的星球画成矢量版）。"""
    image, pen = canvas()
    c = SIZE * SS / 2
    planet_r = 0.205 * SIZE * SS

    # 环画在单独图层上，整体旋转，才有"穿过星球"的立体感
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    lpen = ImageDraw.Draw(layer)
    lpen.ellipse(
        [c - 0.40 * SIZE * SS, c - 0.115 * SIZE * SS, c + 0.40 * SIZE * SS, c + 0.115 * SIZE * SS],
        outline=FG, width=round(0.038 * SIZE * SS))
    layer = layer.rotate(-16, resample=Image.BICUBIC, center=(c, c))
    image.alpha_composite(layer)

    pen.ellipse([c - planet_r, c - planet_r, c + planet_r, c + planet_r], fill=FG)
    return image


def design_dial() -> Image.Image:
    """刻度盘：12 根刻度 + 一段弧。强调"一刻钟"的时间感。"""
    image, pen = canvas()
    c = SIZE * SS / 2
    arc(pen, c, c, 0.335 * SIZE * SS, -90, 180, 0.045 * SIZE * SS)
    for step in range(12):
        angle = math.radians(step * 30 - 90)
        r1 = 0.245 * SIZE * SS
        r2 = 0.315 * SIZE * SS if step % 3 == 0 else 0.288 * SIZE * SS
        width = 0.030 * SIZE * SS if step % 3 == 0 else 0.018 * SIZE * SS
        pen.line([c + r1 * math.cos(angle), c + r1 * math.sin(angle),
                  c + r2 * math.cos(angle), c + r2 * math.sin(angle)],
                 fill=FG, width=round(width))
    return image


def design_progress() -> Image.Image:
    """进度弧：四分之三的环 + 端点圆点。和 App 里那个倒计时圆环呼应。"""
    image, pen = canvas()
    c = SIZE * SS / 2
    arc(pen, c, c, 0.30 * SIZE * SS, -90, 180, 0.085 * SIZE * SS, GRAY)
    arc(pen, c, c, 0.30 * SIZE * SS, -90, 90, 0.085 * SIZE * SS, FG)
    return image


def design_glyph() -> Image.Image:
    """汉字「刻」：最直接、最有中国味，也最能一眼看出名字。"""
    image, pen = canvas()
    c = SIZE * SS / 2
    text_font = font(round(0.62 * SIZE * SS))
    if text_font is None:
        return design_clock()
    box = pen.textbbox((0, 0), "刻", font=text_font)
    pen.text((c - (box[2] - box[0]) / 2 - box[0], c - (box[3] - box[1]) / 2 - box[1]),
             "刻", font=text_font, fill=FG)
    return image


DESIGNS = [
    ("A-番茄", design_tomato),
    ("B-时钟", design_clock),
    ("C-轨道", design_orbit),
    ("D-刻度", design_dial),
    ("E-进度弧", design_progress),
    ("F-刻字", design_glyph),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    made = []
    for name, builder in DESIGNS:
        big = builder()
        small = big.resize((SIZE, SIZE), Image.LANCZOS).convert("RGB")
        path = OUT / f"{name}.png"
        small.save(path, format="PNG", optimize=True)
        made.append((name, small))
        print(f"  {name}  ->  {path.name}")

    # 拼一张总览图，方便挑
    cols, rows, cell, pad = 3, 2, 340, 26
    sheet = Image.new("RGB", (cols * cell + (cols + 1) * pad,
                              rows * (cell + 46) + (rows + 1) * pad), (18, 18, 22))
    pen = ImageDraw.Draw(sheet)
    label_font = font(26)
    for index, (name, image) in enumerate(made):
        col, row = index % cols, index // cols
        x = pad + col * (cell + pad)
        y = pad + row * (cell + 46 + pad)
        sheet.paste(image.resize((cell, cell), Image.LANCZOS), (x, y))
        if label_font:
            pen.text((x + 6, y + cell + 8), name, font=label_font, fill=(220, 220, 226))
    sheet_path = OUT / "总览.png"
    sheet.save(sheet_path, format="PNG", optimize=True)

    print(f"\n共 {len(made)} 个方案，总览图：{sheet_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
