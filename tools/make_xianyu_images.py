"""闲鱼用的图（重做版）。

上一版的问题：封面全是字，一张作品都没有 —— 闲鱼买家是来看货的，
看不到东西不会点进来。流程说明图也没用（买家不关心流程）。

这一版：
  1-封面      —— 手机界面 + 大字，一眼看到"东西"和"能做什么"
  2-作品集    —— 四个界面拼一起，证明真会做
  3-能做什么  —— 范围 + 说明（不再讲流程）

用法：
    python tools/make_xianyu_images.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_xhs_images import draw_countdown, draw_stats, draw_tasks, draw_timer  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "上架材料" / "闲鱼图"

S = 1080
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


def tick(pen, x, y, size, color=FOCUS):
    w = max(4, round(size * 0.17))
    pen.line([x, y + size * 0.52, x + size * 0.36, y + size * 0.88], fill=color, width=w)
    pen.line([x + size * 0.36, y + size * 0.88, x + size, y + size * 0.12], fill=color, width=w)


# --------------------------------------------------------------------------- #
def cover() -> Image.Image:
    """封面：中间一台手机（放真界面），上下压大字。"""
    img = bg((S, S)).convert("RGB")
    pen = ImageDraw.Draw(img)

    center(pen, S / 2, 52, "帮做小程序 / 网站 / App", font(66), INK)

    # 手机放中间，稍微大一点，让人看清界面
    pw, ph = 430, 640
    px, py = (S - pw) / 2, 172
    phone(pen, px, py, pw, ph)
    draw_timer(pen, px, py, pw, ph)

    # 左下角：这不是截图，是示意图
    center(pen, S / 2, 850, "学生练手 · 前 3 个不收费", font(46), FOCUS)
    center(pen, S / 2, 916, "能装能用 · 不满意可以改", font(34, False), MUTED)

    pen.rounded_rectangle([90, 984, S - 90, 1044], radius=30, fill=DARK)
    center(pen, S / 2, 996, "你出想法，我出技术", font(36), fill=(255, 255, 255))
    return img


def portfolio() -> Image.Image:
    """作品集：一行三台手机（2x2 塞不下，会被切掉）。"""
    img = bg((S, S), (255, 255, 255), (232, 236, 244)).convert("RGB")
    pen = ImageDraw.Draw(img)

    center(pen, S / 2, 74, "我做过的界面", font(64), INK)

    pw, ph = 302, 486
    gap = 26
    left = (S - (pw * 3 + gap * 2)) / 2
    top = 196
    labels = ["番茄钟", "倒计时", "统计"]
    drawers = [draw_timer, draw_countdown, draw_stats]
    for i in range(3):
        x = left + i * (pw + gap)
        phone(pen, x, top, pw, ph)
        drawers[i](pen, x, top, pw, ph)
        box = pen.textbbox((0, 0), labels[i], font=font(30))
        pen.text((x + pw / 2 - (box[2] - box[0]) / 2 - box[0], top + ph + 24), labels[i],
                 font=font(30), fill=MUTED)

    center(pen, S / 2, 830, "还有任务管理、深色主题、自定义背景图", font(30, False), MUTED)
    pen.rounded_rectangle([90, 918, S - 90, 1006], radius=28, fill=DARK)
    center(pen, S / 2, 936, "这些都可以按你的想法改成别的", font(34), fill=(255, 255, 255))
    return img


def scope() -> Image.Image:
    """范围说明：能做什么、多少钱、做不了什么。"""
    img = bg((S, S), (255, 255, 255), (236, 240, 247)).convert("RGB")
    pen = ImageDraw.Draw(img)

    center(pen, S / 2, 62, "能做什么", font(58), INK)

    items = [
        ("小程序", "点单 · 预约 · 报名 · 展示", "微信里直接用"),
        ("网站", "活动页 · 展示页 · 小工具", "发个链接就能打开"),
        ("安卓 App", "简单工具类", "能装到手机上，离线也能用"),
    ]
    y = 172
    for name, l1, l2 in items:
        pen.rounded_rectangle([80, y, S - 80, y + 188], radius=26, fill=SURFACE, outline=LINE, width=2)
        tick(pen, 116, y + 46, 44)
        pen.text((186, y + 28), name, font=font(44), fill=INK)
        pen.text((186, y + 92), l1, font=font(28, False), fill=MUTED)
        pen.text((186, y + 134), l2, font=font(28, False), fill=MUTED)
        y += 208

    pen.rounded_rectangle([80, 812, S - 80, 950], radius=26, fill=(255, 241, 239), outline=(255, 214, 208), width=2)
    pen.text((116, 838), "做不了的：", font=font(32), fill=FOCUS)
    pen.text((116, 884), "大型平台 / 要对接微信支付 / 需要长期维护的", font=font(27, False), fill=MUTED)
    pen.text((116, 922), "这些我真做不了，别耽误你时间", font=font(27, False), fill=MUTED)

    pen.rounded_rectangle([80, 976, S - 80, 1036], radius=30, fill=DARK)
    center(pen, S / 2, 988, "前 3 个不收费，我要的是案例", font(34), fill=(255, 255, 255))
    return img


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    old = OUT / "2-流程.png"
    if old.exists():
        old.unlink()
        print("  删掉了没用的「2-流程.png」")
    for name, builder in (("1-封面", cover), ("2-作品集", portfolio), ("3-能做什么", scope)):
        img = builder()
        path = OUT / f"{name}.png"
        img.save(path, format="PNG", optimize=True)
        print(f"  {name}.png   {img.size[0]}x{img.size[1]}   {path.stat().st_size // 1024} KB")
    if (OUT / "3-功能展示.png").exists():
        (OUT / "3-功能展示.png").unlink()
    print(f"\n都在：{OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
