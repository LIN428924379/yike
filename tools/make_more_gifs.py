"""另外两个动图：计时环转动 / 片头标题。

1. 计时环.gif  —— App 里的倒计时圆环从满到空，最后跳到「完成」
2. 片头.gif    —— 竖屏（9:16）的标题动效，可以放在视频开头

用法：
    python tools/make_more_gifs.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "上架材料"

BG = (242, 244, 249)
SURFACE = (255, 255, 255)
INK = (17, 24, 39)
MUTED = (108, 115, 128)
FOCUS = (208, 52, 42)
TRACK = (228, 232, 240)
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


def center(pen, cx, y, s, f, fill):
    box = pen.textbbox((0, 0), s, font=f)
    pen.text((cx - (box[2] - box[0]) / 2 - box[0], y), s, font=f, fill=fill)


def tick(pen, x, y, size, color=FOCUS):
    w = max(4, round(size * 0.16))
    pen.line([x, y + size * 0.52, x + size * 0.36, y + size * 0.88], fill=color, width=w)
    pen.line([x + size * 0.36, y + size * 0.88, x + size, y + size * 0.12], fill=color, width=w)


# --------------------------------------------------------------------------- #
def timer_frame(progress: float, done: bool = False) -> Image.Image:
    """progress: 0（刚开始）→ 1（走完）"""
    S = 640
    img = Image.new("RGB", (S, S), BG)
    pen = ImageDraw.Draw(img)

    cx, cy, R, thick = S / 2, S / 2 - 24, 196, 26
    pen.ellipse([cx - R, cy - R, cx + R, cy + R], outline=TRACK, width=thick)

    left_ratio = max(0.0, 1.0 - progress)
    if left_ratio > 0.002:
        pen.arc([cx - R, cy - R, cx + R, cy + R], -90, -90 + 360 * left_ratio,
                fill=FOCUS, width=thick)

    if done:
        center(pen, cx, cy - 62, "完成", font(72), FOCUS)
        tick(pen, cx - 52, cy + 26, 104)
        center(pen, cx, cy + 168, "起来动动", font(34, False), MUTED)
        return img

    seconds = round(25 * 60 * (1 - progress))
    text = f"{seconds // 60:02d}:{seconds % 60:02d}"
    center(pen, cx, cy - 62, text, font(96), INK)
    center(pen, cx, cy + 62, "专注中", font(36), FOCUS)
    center(pen, cx, cy + R + 56, "写周报", font(32, False), MUTED)
    return img


def make_timer() -> None:
    frames = []
    span = 92
    for i in range(span):
        # 先慢后快，看起来更像真的倒计时
        p = (i / (span - 1)) ** 0.85
        frames.append(timer_frame(p))
    for _ in range(4):
        frames.append(timer_frame(1.0, done=True))
    path = OUT / "计时环.gif"
    frames[0].save(path, format="GIF", save_all=True, append_images=frames[1:],
                   duration=round(1000 / FPS), loop=0, optimize=True)
    print(f"  ✓ {path.name}   {len(frames)} 帧  {len(frames)/FPS:.1f} 秒  {path.stat().st_size // 1024} KB")


# --------------------------------------------------------------------------- #
def intro_frame(t: float) -> Image.Image:
    """t: 0 → 1 的动画进度。图标放大淡入，然后标题滑入。"""
    W, H = 720, 1280
    img = Image.new("RGB", (W, H), BG)
    pen = ImageDraw.Draw(img)

    # 图标：0 → 0.45 之间放大淡入
    p1 = min(1.0, max(0.0, t / 0.45))
    icon_size = round(300 * (0.72 + 0.28 * p1))
    icon_path = ROOT / "一刻-图标.png"
    if icon_path.exists():
        icon = Image.open(icon_path).convert("RGBA").resize((icon_size, icon_size), Image.LANCZOS)
        alpha = icon.getchannel("A").point(lambda v: round(v * p1))
        icon.putalpha(alpha)
        img.paste(icon, ((W - icon_size) // 2, 380 - (icon_size - 300) // 2), icon)

    # 主标题：0.35 → 0.7
    p2 = min(1.0, max(0.0, (t - 0.35) / 0.35))
    if p2 > 0:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        lp = ImageDraw.Draw(layer)
        offset = round(40 * (1 - p2))
        f = font(120)
        box = lp.textbbox((0, 0), "一刻", font=f)
        lp.text(((W - (box[2] - box[0])) / 2 - box[0], 760 + offset), "一刻", font=f,
                fill=INK + (round(255 * p2),))
        img.paste(Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB"), (0, 0))

    # 副标题：0.65 → 1
    p3 = min(1.0, max(0.0, (t - 0.65) / 0.35))
    if p3 > 0:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        lp = ImageDraw.Draw(layer)
        offset = round(30 * (1 - p3))
        f = font(44, False)
        s = "极简番茄钟 · 完全离线"
        box = lp.textbbox((0, 0), s, font=f)
        lp.text(((W - (box[2] - box[0])) / 2 - box[0], 928 + offset), s, font=f,
                fill=MUTED + (round(255 * p3),))
        img.paste(Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB"), (0, 0))

    return img


def make_intro() -> None:
    frames = []
    span = 46
    for i in range(span):
        frames.append(intro_frame(i / (span - 1)))
    for _ in range(10):
        frames.append(intro_frame(1.0))
    path = OUT / "片头.gif"
    frames[0].save(path, format="GIF", save_all=True, append_images=frames[1:],
                   duration=round(1000 / FPS), loop=0, optimize=True)
    print(f"  ✓ {path.name}   {len(frames)} 帧  {len(frames)/FPS:.1f} 秒  {path.stat().st_size // 1024} KB")


def main() -> int:
    make_timer()
    make_intro()
    return 0


if __name__ == "__main__":
    sys.exit(main())
