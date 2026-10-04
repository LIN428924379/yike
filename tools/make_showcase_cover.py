"""作品展示版的封面（3:4，1080x1440）。

风格：像作品集的一页 —— 干净、信息直接，不讲故事。

用法：
    python tools/make_showcase_cover.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "上架材料" / "小红书图-作品展示"

W, H = 1080, 1440
INK = (17, 24, 39)
MUTED = (108, 115, 128)
FOCUS = (208, 52, 42)
LINE = (226, 232, 240)
SURFACE = (255, 255, 255)


def font(size, bold=True):
    names = ("msyhbd.ttc", "msyh.ttc", "simhei.ttf") if bold else ("msyh.ttc", "msyhbd.ttc", "simhei.ttf")
    for name in names:
        path = Path(r"C:\Windows\Fonts") / name
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return None


def bg(size, top=(255, 255, 255), bottom=(236, 240, 247)):
    img = Image.new("RGB", (1, size[1]))
    pen = ImageDraw.Draw(img)
    for y in range(size[1]):
        t = y / max(1, size[1] - 1)
        pen.point((0, y), fill=tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return img.resize(size, Image.BILINEAR)


def center(pen, cx, y, s, f, fill):
    box = pen.textbbox((0, 0), s, font=f)
    pen.text((cx - (box[2] - box[0]) / 2 - box[0], y), s, font=f, fill=fill)


def main() -> int:
    img = bg((W, H)).convert("RGB")
    pen = ImageDraw.Draw(img)

    # 顶部标签
    pen.rounded_rectangle([W / 2 - 210, 96, W / 2 + 210, 168], radius=36, fill=INK)
    center(pen, W / 2, 114, "VIBE CODING 作品 01", font(32), fill=(255, 255, 255))

    # 作品名
    center(pen, W / 2, 232, "一刻", font(132), INK)
    center(pen, W / 2, 402, "极简番茄钟 + 考试倒计时", font(42, False), MUTED)

    # 图标
    icon_path = ROOT / "一刻-图标.png"
    if icon_path.exists():
        icon = Image.open(icon_path).convert("RGBA").resize((360, 360), Image.LANCZOS)
        img.paste(icon, (round(W / 2 - 180), 508), icon)

    # 一行关键信息
    pen.line([W / 2 - 120, 964, W / 2 + 120, 964], fill=LINE, width=3)
    center(pen, W / 2, 1000, "安卓 App ｜ 网页版 ｜ 完全离线", font(34, False), FOCUS)

    # 三条卖点
    y = 1096
    for text in ("番茄钟：退到后台也会响",
                 "每个任务可以单独设时长",
                 "不联网 · 不注册 · 不收集数据"):
        pen.ellipse([170, y + 14, 190, y + 34], fill=FOCUS)
        pen.text((214, y), text, font=font(34), fill=INK)
        y += 78

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "1-封面.png"
    img.save(path, format="PNG", optimize=True)
    print(f"  {path.name}   {img.size[0]}x{img.size[1]}   {path.stat().st_size // 1024} KB")

    # 功能展示那张直接复用之前画好的
    src = ROOT / "上架材料" / "小红书图" / "2-功能展示.png"
    if src.exists():
        Image.open(src).save(OUT / "2-功能.png", format="PNG", optimize=True)
        print("  2-功能.png   （复用之前画好的四界面图）")

    print(f"\n都在：{OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
