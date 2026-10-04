"""图标演变动图（GIF）。

把「一刻」图标改过的六个版本，从最早到定稿依次演一遍，
中间用交叉淡入淡出过渡。适合放 GitHub README、作品集、微信表情。

为什么不做 mp4：这台机器没有 ffmpeg。要 mp4 的话，把这个 GIF 拖进剪映导出即可。

用法：
    python tools/make_icon_gif.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "上架材料" / "图标演变.gif"

SIZE = 640
ICON = 400
BG = (245, 247, 251)
INK = (17, 24, 39)
MUTED = (120, 127, 140)

# 六个阶段（按时间顺序）
STEPS = [
    ("assets-src/icon-source-tomato.png", "水墨番茄"),
    ("assets-src/icon-source-ring-old.png", "光环星球"),
    ("assets-src/designs-quarter/A-四格.png", "四格"),
    ("assets-src/designs-quarter/B-圆饼.png", "圆饼"),
    ("assets-src/designs-quarter/C-量规.png", "圆环"),
    ("一刻-图标.png", "定稿"),
]

HOLD = 13       # 每张停留几帧
FADE = 7        # 过渡几帧
FPS = 20


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


def rounded(img: Image.Image, size: int, ratio: float = 0.22) -> Image.Image:
    small = img.resize((size, size), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=round(ratio * size), fill=255)
    small.putalpha(mask)
    return small


def build(index: int) -> Image.Image:
    """画出第 index 帧的样子（图标 + 名字 + 进度点）。"""
    path, label = STEPS[index]
    img = Image.new("RGB", (SIZE, SIZE), BG)
    pen = ImageDraw.Draw(img)

    src = ROOT / path
    if src.exists():
        icon = rounded(Image.open(src), ICON)
        img.paste(icon, ((SIZE - ICON) // 2, 78), icon)
    else:
        pen.rounded_rectangle([(SIZE - ICON) // 2, 78, (SIZE + ICON) // 2, 78 + ICON],
                              radius=round(0.22 * ICON), fill=(220, 224, 232))

    f = font(40)
    box = pen.textbbox((0, 0), label, font=f)
    pen.text(((SIZE - (box[2] - box[0])) / 2 - box[0], 78 + ICON + 34), label, font=f, fill=INK)

    # 底部进度点
    n = len(STEPS)
    dot_r, gap = 7, 26
    total = n * dot_r * 2 + (n - 1) * (gap - dot_r * 2)
    x = (SIZE - total) / 2
    for i in range(n):
        color = INK if i == index else (210, 215, 224)
        pen.ellipse([x, SIZE - 86, x + dot_r * 2, SIZE - 86 + dot_r * 2], fill=color)
        x += gap
    return img


def main() -> int:
    frames = []
    for i in range(len(STEPS)):
        cur = build(i)
        frames.extend([cur] * HOLD)
        if i < len(STEPS) - 1:
            nxt = build(i + 1)
            for t in range(1, FADE + 1):
                frames.append(Image.blend(cur, nxt, t / (FADE + 1)))
    # 结尾再停一下
    frames.extend([build(len(STEPS) - 1)] * HOLD)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        OUT,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=round(1000 / FPS),
        loop=0,
        optimize=True,
    )
    seconds = len(frames) / FPS
    print(f"  ✓ {OUT.relative_to(ROOT)}")
    print(f"    {SIZE}x{SIZE}  {len(frames)} 帧  {seconds:.1f} 秒  {OUT.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
