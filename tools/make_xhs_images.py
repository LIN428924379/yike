"""生成小红书发帖用的图（3:4，1080x1440）。

三张：
  1. 封面        —— 大标题，抓眼球
  2. 功能展示    —— App 的四个界面，2x2 并排
  3. 能做什么    —— 小程序 / 网站 / App 三张卡片

两个踩过的坑：
  · emoji（🍅）和 ✓ ✗ 在微软雅黑里没有字形，会变成空心方块 —— 所以勾和叉【自己画】。
  · 界面元素的位置必须【按手机框高度等比算】，写死像素的话换个尺寸就被切掉。

用法：
    python tools/make_xhs_images.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "上架材料" / "小红书图"

W, H = 1080, 1440

# App 浅色主题的真实颜色
BG = (242, 244, 249)
SURFACE = (255, 255, 255)
LINE = (226, 232, 240)
INK = (17, 24, 39)
MUTED = (100, 107, 120)
FOCUS = (208, 52, 42)
TRACK = (230, 234, 242)
DARK = (23, 25, 33)
WHITE = (255, 255, 255)
SLICE = [(255, 90, 77), (255, 152, 56), (255, 209, 102), (53, 208, 165), (74, 168, 255)]


def font(size: int, bold: bool = True):
    names = ("msyhbd.ttc", "msyh.ttc", "simhei.ttf") if bold else ("msyh.ttc", "msyhbd.ttc", "simhei.ttf")
    for name in names:
        path = Path(r"C:\Windows\Fonts") / name
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return None


def soft_bg(size, top=(255, 255, 255), bottom=(238, 241, 247)) -> Image.Image:
    img = Image.new("RGB", (1, size[1]))
    pen = ImageDraw.Draw(img)
    for y in range(size[1]):
        t = y / max(1, size[1] - 1)
        pen.point((0, y), fill=tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return img.resize(size, Image.BILINEAR)


def text_center(pen, cx, y, s, f, fill):
    box = pen.textbbox((0, 0), s, font=f)
    pen.text((cx - (box[2] - box[0]) / 2 - box[0], y), s, font=f, fill=fill)


def tick(pen, x, y, size, color=FOCUS, width=None):
    """自己画一个勾 —— 不依赖字体里有没有 ✓ 这个字形。"""
    w = width or max(3, round(size * 0.16))
    pen.line([x, y + size * 0.52, x + size * 0.36, y + size * 0.88], fill=color, width=w)
    pen.line([x + size * 0.36, y + size * 0.88, x + size, y + size * 0.12], fill=color, width=w)


def cross(pen, x, y, size, color=(190, 196, 206), width=None):
    w = width or max(3, round(size * 0.16))
    pen.line([x, y, x + size, y + size], fill=color, width=w)
    pen.line([x + size, y, x, y + size], fill=color, width=w)


def tomato(pen, x, y, r, color=FOCUS):
    """自己画一个小番茄（其实就是一个红圆点）—— emoji 会变方块。"""
    pen.ellipse([x - r, y - r, x + r, y + r], fill=color)


# --------------------------------------------------------------------------- #
def make_cover() -> Image.Image:
    img = soft_bg((W, H)).convert("RGB")
    pen = ImageDraw.Draw(img)

    text_center(pen, W / 2, 90, "一名大学生，用 AI 从零做的", font(34, False), MUTED)
    text_center(pen, W / 2, 160, "帮 3 个人", font(104), INK)
    text_center(pen, W / 2, 292, "做小程序 / 网站 / App", font(64), FOCUS)
    pen.line([W / 2 - 90, 404, W / 2 + 90, 404], fill=LINE, width=3)
    text_center(pen, W / 2, 440, "我只想要 3 个真实案例", font(38, False), MUTED)

    icon_path = ROOT / "一刻-图标.png"
    if icon_path.exists():
        icon = Image.open(icon_path).convert("RGBA").resize((280, 280), Image.LANCZOS)
        img.paste(icon, (round(W / 2 - 140), 556), icon)
    else:
        pen.rounded_rectangle([W / 2 - 140, 556, W / 2 + 140, 836], radius=64, fill=FOCUS)

    text_center(pen, W / 2, 872, "上面这个番茄钟，就是我自己做的", font(34, False), INK)
    text_center(pen, W / 2, 924, "（图 2 是它的界面）", font(28, False), MUTED)

    box_top = 1010
    pen.rounded_rectangle([88, box_top, W - 88, box_top + 300], radius=28, fill=SURFACE, outline=LINE, width=2)
    rows = [
        ("需求能一句话说清楚", True, "“给奶茶店做个点单”"),
        ("你自己真的用得上", True, "不是随便试试"),
        ("做完我可以展示", True, "这就是我的报酬"),
    ]
    y = box_top + 42
    for i, (title, ok, sub) in enumerate(rows):
        if ok:
            tick(pen, 126, y + 2, 30)
        else:
            cross(pen, 126, y + 2, 30)
        pen.text((176, y), title, font=font(31), fill=INK)
        pen.text((176, y + 42), sub, font=font(25, False), fill=MUTED)
        y += 84
        if i < len(rows) - 1:
            pen.line([126, y - 14, W - 126, y - 14], fill=(240, 242, 246), width=2)

    return img


# --------------------------------------------------------------------------- #
def phone_frame(pen, x, y, w, h):
    pen.rounded_rectangle([x, y, x + w, y + h], radius=30, fill=SURFACE, outline=LINE, width=3)
    pen.rounded_rectangle([x + w / 2 - 30, y + 12, x + w / 2 + 30, y + 19], radius=4, fill=LINE)


def tabbar(pen, x, y, w, h, active):
    """底部三个 tab，active = 0/1/2。"""
    pen.line([x + 3, y + h - 0.09 * h, x + w - 3, y + h - 0.09 * h], fill=LINE, width=2)
    for i, name in enumerate(("任务", "倒计时", "总结")):
        tx = x + w * (i * 2 + 1) / 6
        text_center(pen, tx, y + h - 0.062 * h, name, font(round(h * 0.036)),
                    FOCUS if i == active else MUTED)


def draw_timer(pen, x, y, w, h):
    s = h / 560.0
    pen.text((x + 26 * s, y + 34 * s), "写周报", font=font(round(30 * s)), fill=INK)
    cx, cy, R = x + w / 2, y + 210 * s, 96 * s
    pen.ellipse([cx - R, cy - R, cx + R, cy + R], outline=TRACK, width=round(18 * s))
    pen.arc([cx - R, cy - R, cx + R, cy + R], -90, 96, fill=FOCUS, width=round(18 * s))
    text_center(pen, cx, cy - 40 * s, "25:00", font(round(50 * s)), INK)
    text_center(pen, cx, cy + 26 * s, "专注中", font(round(21 * s)), FOCUS)
    tomato(pen, cx - 74 * s, cy + R + 42 * s, 8 * s)
    pen.text((cx - 58 * s, cy + R + 30 * s), "已完成 2 个番茄", font=font(round(19 * s), False), fill=MUTED)
    by = cy + R + 66 * s
    pen.rounded_rectangle([x + 24 * s, by, x + 24 * s + 120 * s, by + 50 * s], radius=14 * s, fill=FOCUS)
    text_center(pen, x + 24 * s + 60 * s, by + 12 * s, "开始", font(round(21 * s)), WHITE)
    pen.rounded_rectangle([x + 152 * s, by, x + 152 * s + 84 * s, by + 50 * s], radius=14 * s, fill=BG, outline=LINE, width=2)
    text_center(pen, x + 152 * s + 42 * s, by + 12 * s, "暂停", font(round(20 * s)), MUTED)
    pen.rounded_rectangle([x + 244 * s, by, x + 244 * s + 84 * s, by + 50 * s], radius=14 * s, fill=BG, outline=LINE, width=2)
    text_center(pen, x + 244 * s + 42 * s, by + 12 * s, "结束", font(round(20 * s)), MUTED)
    tabbar(pen, x, y, w, h, 0)


def draw_countdown(pen, x, y, w, h):
    s = h / 560.0
    card = [x + 22 * s, y + 34 * s, x + w - 22 * s, y + 430 * s]
    pen.rounded_rectangle(card, radius=22 * s, fill=DARK)
    cx = (card[0] + card[2]) / 2
    text_center(pen, cx, card[1] + 74 * s, "87", font(round(104 * s)), WHITE)
    text_center(pen, cx, card[1] + 196 * s, "天", font(round(27 * s)), (210, 212, 218))
    text_center(pen, cx, card[1] + 248 * s, "考研上岸", font(round(31 * s)), WHITE)
    text_center(pen, cx, card[1] + 292 * s, "2026年12月20日", font(round(19 * s), False), (170, 172, 180))
    pen.line([cx - 96 * s, card[1] + 328 * s, cx + 96 * s, card[1] + 328 * s], fill=(70, 72, 80), width=2)
    text_center(pen, cx, card[1] + 344 * s, "你正在靠近那个日子", font(round(19 * s), False), (205, 205, 212))
    tabbar(pen, x, y, w, h, 1)


def draw_tasks(pen, x, y, w, h):
    s = h / 560.0
    pen.text((x + 26 * s, y + 34 * s), "任务", font=font(round(31 * s)), fill=INK)
    pen.text((x + 100 * s, y + 39 * s), "2026-10-05", font=font(round(18 * s), False), fill=MUTED)
    pen.ellipse([x + w - 68 * s, y + 28 * s, x + w - 24 * s, y + 72 * s], fill=FOCUS)
    text_center(pen, x + w - 46 * s, y + 38 * s, "＋", font(round(26 * s)), WHITE)

    items = [("写周报", "2 个番茄 · 共专注 50分"), ("背单词", "1 个番茄 · 15分钟/番茄"), ("看书", "还没开始")]
    for i, (name, meta) in enumerate(items):
        top = y + 92 * s + i * 92 * s
        pen.rounded_rectangle([x + 22 * s, top, x + w - 22 * s, top + 76 * s], radius=16 * s,
                              fill=SURFACE, outline=LINE, width=2)
        pen.ellipse([x + 42 * s, top + 24 * s, x + 68 * s, top + 50 * s], outline=FOCUS, width=3)
        pen.text((x + 84 * s, top + 14 * s), name, font=font(round(26 * s)), fill=INK)
        pen.text((x + 84 * s, top + 44 * s), meta, font=font(round(17 * s), False), fill=MUTED)
    tabbar(pen, x, y, w, h, 0)


def draw_stats(pen, x, y, w, h):
    s = h / 560.0
    pen.text((x + 26 * s, y + 34 * s), "总结", font=font(round(31 * s)), fill=INK)
    cx, cy, R = x + w / 2, y + 190 * s, 92 * s
    start = -90.0
    for i, share in enumerate((0.46, 0.27, 0.16, 0.11)):
        end = start + share * 360
        pen.pieslice([cx - R, cy - R, cx + R, cy + R], start, end, fill=SLICE[i % len(SLICE)])
        start = end
    pen.ellipse([cx - 36 * s, cy - 36 * s, cx + 36 * s, cy + 36 * s], fill=SURFACE)
    text_center(pen, cx, cy - 12 * s, "1小时", font(round(20 * s)), INK)

    legend = [("写周报", "50分"), ("背单词", "30分"), ("看书", "18分"), ("其他", "12分")]
    for i, (name, val) in enumerate(legend):
        ly = y + 310 * s + i * 34 * s
        pen.rounded_rectangle([x + 26 * s, ly + 5 * s, x + 44 * s, ly + 23 * s], radius=4, fill=SLICE[i % len(SLICE)])
        pen.text((x + 56 * s, ly), name, font=font(round(19 * s)), fill=INK)
        pen.text((x + w - 84 * s, ly), val, font=font(round(19 * s), False), fill=MUTED)

    pen.rounded_rectangle([x + 22 * s, y + 452 * s, x + w - 22 * s, y + 528 * s], radius=16 * s,
                          fill=(255, 241, 239), outline=(255, 220, 216), width=2)
    text_center(pen, x + w / 2, y + 462 * s, "本周专注总和", font(round(17 * s), False), MUTED)
    text_center(pen, x + w / 2, y + 486 * s, "1小时50分", font(round(27 * s)), INK)
    tabbar(pen, x, y, w, h, 2)


def make_screens() -> Image.Image:
    """四个界面 2x2 并排。尺寸算过，保证不超框。"""
    img = soft_bg((W, H), (255, 255, 255), (233, 237, 244)).convert("RGB")
    pen = ImageDraw.Draw(img)

    text_center(pen, W / 2, 46, "它能干这些", font(58), INK)

    pw, ph = 402, 546          # 2 列：70 + 402 + 56 + 402 + 70 = 1000（居中）
    gap_x, gap_y = 56, 52
    left = (W - (pw * 2 + gap_x)) / 2
    top = 140
    labels = ["① 番茄钟：退到后台也会响", "② 倒计时：考试还剩几天",
              "③ 任务：每天自动换新的一天", "④ 统计：看你专注在哪儿"]
    drawers = [draw_timer, draw_countdown, draw_tasks, draw_stats]

    for i in range(4):
        col, row = i % 2, i // 2
        x = left + col * (pw + gap_x)
        y = top + row * (ph + 76)
        phone_frame(pen, x, y, pw, ph)
        drawers[i](pen, x, y, pw, ph)
        text_center(pen, x + pw / 2, y + ph + 16, labels[i], font(26), MUTED)

    return img


def make_scope() -> Image.Image:
    img = soft_bg((W, H), (255, 255, 255), (236, 240, 247)).convert("RGB")
    pen = ImageDraw.Draw(img)

    text_center(pen, W / 2, 74, "我能帮你做这些", font(60), INK)

    cards = [
        ("小程序", "点单 / 预约 / 展示 / 报名", "微信里就能用，不用下载", FOCUS),
        ("网站", "活动页 / 展示页 / 小工具", "发个链接就能打开", (74, 168, 255)),
        ("手机 App", "安卓 App / 网页版", "能装到手机上，离线也能用", (53, 208, 165)),
    ]
    y = 200
    for name, l1, l2, color in cards:
        pen.rounded_rectangle([68, y, W - 68, y + 306], radius=30, fill=SURFACE, outline=LINE, width=3)
        pen.rounded_rectangle([104, y + 46, 118, y + 122], radius=7, fill=color)
        pen.text((146, y + 44), name, font=font(50), fill=INK)
        pen.text((146, y + 122), l1, font=font(30, False), fill=MUTED)
        pen.text((146, y + 170), l2, font=font(30, False), fill=MUTED)
        pen.line([106, y + 230, W - 106, y + 230], fill=(242, 244, 248), width=2)
        tick(pen, W / 2 - 92, y + 252, 26, color)
        pen.text((W / 2 - 56, y + 246), "限 3 个名额", font=font(29), fill=color)
        y += 348

    text_center(pen, W / 2, H - 96, "有想法的，评论区聊～", font(33, False), MUTED)
    return img


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, builder in (("1-封面", make_cover), ("2-功能展示", make_screens), ("3-能做什么", make_scope)):
        img = builder()
        path = OUT / f"{name}.png"
        img.save(path, format="PNG", optimize=True)
        print(f"  {name}.png   {img.size[0]}x{img.size[1]}   {path.stat().st_size // 1024} KB")
    print(f"\n都在：{OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
