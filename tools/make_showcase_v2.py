"""小红书「Vibe Coding 作品展示」配图（重做版，3:4，1080x1440）。

和第一版的区别：
  · 封面把【作品界面】放上去了 —— 之前只有图标和一堆字，太平
  · 界面从 2x2 改成一行三台 —— 之前四台塞不下会被切
  · 第三张改成【做了什么 + 用了什么】，比单纯的界面图有信息量

用法：
    python tools/make_showcase_v2.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_xhs_images import draw_countdown, draw_stats, draw_timer  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "上架材料" / "小红书图-作品展示v2"

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


def bg(size, top=(255, 255, 255), bottom=(233, 237, 244)):
    img = Image.new("RGB", (1, size[1]))
    pen = ImageDraw.Draw(img)
    for y in range(size[1]):
        t = y / max(1, size[1] - 1)
        pen.point((0, y), fill=tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return img.resize(size, Image.BILINEAR)


def center(pen, cx, y, s, f, fill):
    box = pen.textbbox((0, 0), s, font=f)
    pen.text((cx - (box[2] - box[0]) / 2 - box[0], y), s, font=f, fill=fill)


def phone(pen, x, y, w, h):
    pen.rounded_rectangle([x, y, x + w, y + h], radius=round(w * 0.075),
                          fill=SURFACE, outline=LINE, width=3)
    pen.rounded_rectangle([x + w / 2 - w * 0.075, y + h * 0.022,
                           x + w / 2 + w * 0.075, y + h * 0.035], radius=5, fill=LINE)


def dot(pen, x, y, r, color=FOCUS):
    pen.ellipse([x - r, y - r, x + r, y + r], fill=color)


# --------------------------------------------------------------------------- #
def cover() -> Image.Image:
    """封面：中间放 App 图标（不放界面 —— 界面容易被判"推广其他平台"）。"""
    img = bg((W, H)).convert("RGB")
    pen = ImageDraw.Draw(img)

    pen.rounded_rectangle([W / 2 - 200, 76, W / 2 + 200, 144], radius=34, fill=INK)
    center(pen, W / 2, 92, "VIBE CODING 作品 01", font(30), fill=(255, 255, 255))

    center(pen, W / 2, 210, "一刻", font(116), INK)
    center(pen, W / 2, 386, "极简番茄钟 + 考试倒计时", font(42, False), MUTED)

    icon_path = ROOT / "一刻-图标.png"
    size = 500
    if icon_path.exists():
        icon = Image.open(icon_path).convert("RGBA").resize((size, size), Image.LANCZOS)
        img.paste(icon, (round((W - size) / 2), 540), icon)

    center(pen, W / 2, 1108, "安卓 App ｜ 网页版 ｜ 完全离线", font(36), FOCUS)

    pen.rounded_rectangle([120, 1210, W - 120, 1296], radius=30, fill=SURFACE, outline=LINE, width=2)
    center(pen, W / 2, 1232, "用 AI 做的 · 一天时间", font(34), INK)
    return img


def screens() -> Image.Image:
    """一行三台手机。"""
    img = bg((W, H), (255, 255, 255), (232, 236, 244)).convert("RGB")
    pen = ImageDraw.Draw(img)

    center(pen, W / 2, 84, "它能干这些", font(66), INK)

    pw, ph = 302, 486
    gap = 26
    left = (W - (pw * 3 + gap * 2)) / 2
    top = 226
    labels = ["番茄钟", "倒计时", "统计"]
    drawers = [draw_timer, draw_countdown, draw_stats]
    for i in range(3):
        x = left + i * (pw + gap)
        phone(pen, x, top, pw, ph)
        drawers[i](pen, x, top, pw, ph)
        box = pen.textbbox((0, 0), labels[i], font=font(30))
        pen.text((x + pw / 2 - (box[2] - box[0]) / 2 - box[0], top + ph + 26), labels[i],
                 font=font(30), fill=MUTED)

    y = 862
    for text in ("番茄钟：专注 / 短休息 / 长休息，退到后台也会响",
                 "每个任务能单独设时长（背单词 15 分钟，写代码 45 分钟）",
                 "倒计时：多个日子 + 相册背景图 + 每天一句文案",
                 "统计：按任务看专注时长，扇形图 / 条形图"):
        dot(pen, 122, y + 17, 9)
        pen.text((152, y), text, font=font(30), fill=INK)
        y += 68
    return img


def facts() -> Image.Image:
    """做了什么 + 用了什么。"""
    img = bg((W, H), (255, 255, 255), (236, 240, 247)).convert("RGB")
    pen = ImageDraw.Draw(img)

    center(pen, W / 2, 84, "做了些什么", font(66), INK)

    rows = [
        ("技术", "单文件 HTML + CSS + JS\n一个文件就是整个 App"),
        ("打包", "Capacitor 打包成安卓 App\n同时有网页版"),
        ("离线", "不联网、不注册、不收集任何数据\n所有记录只存在手机里"),
        ("检查", "70 项自动化检查\n每次改完都跑一遍"),
    ]
    y = 220
    for title, body in rows:
        pen.rounded_rectangle([80, y, W - 80, y + 208], radius=28, fill=SURFACE, outline=LINE, width=3)
        pen.rounded_rectangle([112, y + 44, 124, y + 120], radius=6, fill=FOCUS)
        pen.text((152, y + 42), title, font=font(42), fill=INK)
        for j, line in enumerate(body.split("\n")):
            pen.text((152, y + 110 + j * 46), line, font=font(28, False), fill=MUTED)
        y += 228

    pen.rounded_rectangle([80, 1132, W - 80, 1252], radius=28, fill=DARK)
    center(pen, W / 2, 1156, "用时：一天", font(38), fill=(255, 255, 255))
    center(pen, W / 2, 1206, "工具：AI", font(38), fill=(255, 255, 255))

    center(pen, W / 2, 1300, "第 1 个作品，记录一下", font(32, False), MUTED)
    return img


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, builder in (("1-封面", cover), ("2-功能", screens), ("3-技术", facts)):
        img = builder()
        path = OUT / f"{name}.png"
        img.save(path, format="PNG", optimize=True)
        print(f"  {name}.png   {img.size[0]}x{img.size[1]}   {path.stat().st_size // 1024} KB")
    print(f"\n都在：{OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
