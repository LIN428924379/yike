"""图标尺寸阶梯 —— 严格模拟安卓实际显示的样子。

之前比错的点：传统图标整个方块都可见，而自适应图标安卓只显示中间约 66%，
所以同样的前景比例，自适应版看起来会大一半左右。

这里直接按安卓的规则合成：
  1. 108dp 画布 + 背景层
  2. 前景层按比例缩放、居中
  3. 只取中间 66.7%（系统蒙版的实际可见区）
  4. 裁成圆形

用法：
    python tools/icon_size_ladder.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets-src" / "designs-quarter" / "尺寸阶梯.png"

sys.path.insert(0, str(ROOT / "tools"))
from make_android_icons import SOURCE, fit_square, load_art  # noqa: E402

CANVAS = 1080          # 模拟 108dp 的自适应图标画布
VISIBLE = 0.667        # 系统实际显示的区域（中间 72dp / 108dp）
PREVIEW = 200          # 预览图大小

RATIOS = [0.44, 0.52, 0.60, 0.68, 0.76]


def circle_mask(size: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
    return mask


def simulate(art, bg, ratio: float, shape: str = "circle") -> Image.Image:
    canvas = Image.new("RGBA", (CANVAS, CANVAS), tuple(bg) + (255,))
    inner = round(CANVAS * ratio)
    small = fit_square(art, inner, bg=None)
    off = (CANVAS - inner) // 2
    canvas.paste(small, (off, off), small)

    visible = round(CANVAS * VISIBLE)
    crop = (CANVAS - visible) // 2
    canvas = canvas.crop((crop, crop, crop + visible, crop + visible))
    canvas = canvas.resize((PREVIEW, PREVIEW), Image.LANCZOS)

    out = Image.new("RGBA", (PREVIEW, PREVIEW), (0, 0, 0, 0))
    out.paste(canvas, (0, 0), circle_mask(PREVIEW))
    return out


def font(size: int):
    for name in ("msyhbd.ttc", "msyh.ttc", "simhei.ttf"):
        path = Path(r"C:\Windows\Fonts") / name
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return None


def main() -> int:
    art, bg = load_art(SOURCE)
    if art is None:
        print("找不到图标源图")
        return 1

    label_font = font(24)
    note_font = font(19)
    pad, gap = 30, 28
    width = pad * 2 + len(RATIOS) * PREVIEW + (len(RATIOS) - 1) * gap
    height = pad * 2 + PREVIEW + 60

    sheet = Image.new("RGB", (width, height), (206, 206, 212))
    pen = ImageDraw.Draw(sheet)

    for index, ratio in enumerate(RATIOS):
        x = pad + index * (PREVIEW + gap)
        icon = simulate(art, bg, ratio)
        sheet.paste(icon, (x, pad), icon)
        label = f"{round(ratio * 100)}%"
        if abs(ratio - 0.60) < 0.001:
            label += "（现在）"
        pen.text((x + 4, pad + PREVIEW + 12), label, font=label_font, fill=(28, 28, 34))

    pen.text((pad, height - 32), "模拟安卓实际显示：108dp 画布 → 只取中间 66% → 裁圆",
             font=note_font, fill=(70, 70, 78))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(OUT, format="PNG", optimize=True)
    print(f"✓ {OUT.relative_to(ROOT)}")
    print("  从左到右：" + " / ".join(f"{round(r * 100)}%" for r in RATIOS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
