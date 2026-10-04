"""小红书「纯分享」版配图（3:4，1080x1440）。

和之前那版的区别（之前被小红书判"推广其他平台"限流了）：
  · 一张 App 界面截图都不放 ✗ —— 规则里"展示其他平台界面信息"就是踩这个
  · 全部改成【纯文字卡片】✓ —— 图上只有字，没有任何别的 App 的界面
  · 不留任何联系方式、网址、引导词 ✓

三张：封面 / 踩的坑 / 名字的由来

用法：
    python tools/make_share_images.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "上架材料" / "小红书图-分享版"

W, H = 1080, 1440
INK = (17, 24, 39)
MUTED = (108, 115, 128)
FOCUS = (208, 52, 42)
LINE = (226, 232, 240)
SURFACE = (255, 255, 255)
DARK = (23, 25, 33)


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


def tick(pen, x, y, size, color=FOCUS):
    w = max(3, round(size * 0.16))
    pen.line([x, y + size * 0.52, x + size * 0.36, y + size * 0.88], fill=color, width=w)
    pen.line([x + size * 0.36, y + size * 0.88, x + size, y + size * 0.12], fill=color, width=w)


def marker(pen, cx, cy, r, color=FOCUS):
    """一个编号圆点。"""
    pen.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)


# --------------------------------------------------------------------------- #
def cover() -> Image.Image:
    img = bg((W, H)).convert("RGB")
    pen = ImageDraw.Draw(img)

    center(pen, W / 2, 118, "一个学人工智能的大学生", font(38, False), MUTED)
    center(pen, W / 2, 200, "我用 AI", font(92), INK)
    center(pen, W / 2, 310, "做了个 App", font(92), INK)
    pen.line([W / 2 - 90, 452, W / 2 + 90, 452], fill=LINE, width=3)
    center(pen, W / 2, 490, "这是我第一次真的做出东西", font(40, False), FOCUS)

    icon_path = ROOT / "一刻-图标.png"
    if icon_path.exists():
        icon = Image.open(icon_path).convert("RGBA").resize((320, 320), Image.LANCZOS)
        img.paste(icon, (round(W / 2 - 160), 592), icon)

    center(pen, W / 2, 966, "课上学的全是公式和模型", font(34, False), MUTED)
    center(pen, W / 2, 1018, "直到昨天，才有了一个真的能跑的东西", font(34, False), MUTED)

    pen.rounded_rectangle([110, 1102, W - 110, 1272], radius=26, fill=SURFACE, outline=LINE, width=2)
    center(pen, W / 2, 1136, "以前想做个东西", font(32, False), MUTED)
    center(pen, W / 2, 1184, "总觉得「还早，等我再学学」", font(36), INK)

    return img


def pitfalls() -> Image.Image:
    img = bg((W, H), (255, 255, 255), (233, 237, 244)).convert("RGB")
    pen = ImageDraw.Draw(img)

    center(pen, W / 2, 62, "我踩的三个坑", font(64), INK)

    items = [
        ("计时到点了不响",
         "查了一晚上才发现 —— 是代码在提醒响的那一瞬间\n把它自己给取消了"),
        ("我把整个文件夹删光了",
         "回收站里也找不到，最后是从安装包里\n把整个 App 完整「抠」了出来"),
        ("图标改了五轮",
         "水墨番茄 → 几何色块 → 最后定成一个圆\n因为「一刻」就是四分之一小时"),
    ]
    y = 216
    for i, (title, body) in enumerate(items):
        box_h = 340
        pen.rounded_rectangle([70, y, W - 70, y + box_h], radius=30, fill=SURFACE, outline=LINE, width=3)
        marker(pen, 130, y + 62, 26)
        center_num = font(30, True)
        b = pen.textbbox((0, 0), str(i + 1), font=center_num)
        pen.text((130 - (b[2] - b[0]) / 2 - b[0], y + 42), str(i + 1), font=center_num, fill=(255, 255, 255))
        pen.text((178, y + 40), title, font=font(40), fill=INK)
        for j, line in enumerate(body.split("\n")):
            pen.text((178, y + 116 + j * 52), line, font=font(29, False), fill=MUTED)
        y += box_h + 44

    center(pen, W / 2, H - 96, "每一个都是自己撞出来的", font(30, False), MUTED)
    return img


def naming() -> Image.Image:
    img = bg((W, H), (255, 255, 255), (235, 239, 246)).convert("RGB")
    pen = ImageDraw.Draw(img)

    center(pen, W / 2, 74, "它为什么叫「一刻」", font(62), INK)

    # 画一个环：四分之三是深色，四分之一是红色（就是图标的形状）
    cx, cy, R = W / 2, 470, 190
    pen.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(30, 32, 40), width=42)
    pen.arc([cx - R, cy - R, cx + R, cy + R], -90, 0, fill=FOCUS, width=42)

    center(pen, cx, cy - 34, "一刻", font(64), INK)
    center(pen, cx, cy + 46, "= 一刻钟", font(34, False), MUTED)
    center(pen, cx, cy + 92, "= 四分之一小时", font(34, False), MUTED)

    y = 760
    pen.rounded_rectangle([80, y, W - 80, y + 220], radius=28, fill=SURFACE, outline=LINE, width=2)
    pen.text((126, y + 44), "所以图标就是一个完整的圆，", font=font(34), fill=INK)
    pen.text((126, y + 100), "四分之一是红的。", font=font(34), fill=INK)
    pen.text((126, y + 158), "既是「计时器走到四分之一」，", font=font(29, False), fill=MUTED)

    pen.rounded_rectangle([80, 1030, W - 80, 1250], radius=28, fill=DARK)
    center(pen, W / 2, 1070, "也是「从时间里取走一刻」", font(34), fill=(255, 255, 255))

    center(pen, W / 2, 1300, "一个名字想了三个晚上", font(30, False), MUTED)
    return img


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, builder in (("1-封面", cover), ("2-踩的坑", pitfalls), ("3-名字由来", naming)):
        img = builder()
        path = OUT / f"{name}.png"
        img.save(path, format="PNG", optimize=True)
        print(f"  {name}.png   {img.size[0]}x{img.size[1]}   {path.stat().st_size // 1024} KB")
    print(f"\n都在：{OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
