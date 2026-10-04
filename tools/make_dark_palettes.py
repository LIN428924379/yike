"""深色主题配色对比图。

为什么要画这个：调颜色码是"盲调"。把同一套界面用不同配色画出来并排看，
一眼就能选出顺眼的那个 —— 跟选图标时用的办法一样。

每套配色都画出 App 里最关键的地方：顶栏、任务卡、大红圆环、按钮、底部 tab。

用法：
    python tools/make_dark_palettes.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets-src" / "dark-palettes.png"

W, H = 268, 470

# 每套配色：底色 / 卡片 / 输入框 / 分割线 / 正文 / 次要 / 主色 / 按钮色 / 圆环底 / 底栏
PALETTES = [
    ("A 中性黑（Notion 风）", {
        "bg": "#191919", "surface": "#242424", "surface2": "#2c2c2c", "line": "#343434",
        "ink": "#e9e9e7", "muted": "#9d9d9a", "focus": "#ff6f5e", "solid": "#d63c31",
        "track": "#2f2f2f", "tabbar": "#1f1f1f", "bar": "#1f1f1f",
    }),
    ("B 纯黑（OLED）", {
        "bg": "#000000", "surface": "#121212", "surface2": "#1c1c1c", "line": "#262626",
        "ink": "#ededed", "muted": "#8f8f8f", "focus": "#ff7060", "solid": "#d63c31",
        "track": "#242424", "tabbar": "#0a0a0a", "bar": "#0a0a0a",
    }),
    ("C 冷深灰（Linear 风）", {
        "bg": "#0d0e12", "surface": "#171921", "surface2": "#1e212b", "line": "#272b36",
        "ink": "#eceef4", "muted": "#8d93a3", "focus": "#ff7a68", "solid": "#d63c31",
        "track": "#232733", "tabbar": "#12141b", "bar": "#12141b",
    }),
    ("D 蓝黑（GitHub 风）", {
        "bg": "#0d1117", "surface": "#161b22", "surface2": "#1d232c", "line": "#262c36",
        "ink": "#e6edf3", "muted": "#8b949e", "focus": "#ff7b6b", "solid": "#d63c31",
        "track": "#222831", "tabbar": "#11161c", "bar": "#11161c",
    }),
    ("E 暖炭灰（现在这版）", {
        "bg": "#141312", "surface": "#1c1a18", "surface2": "#262321", "line": "#302c29",
        "ink": "#ece7e2", "muted": "#a29b94", "focus": "#ff6f5e", "solid": "#d63c31",
        "track": "#2a2623", "tabbar": "#171513", "bar": "#171513",
    }),
    ("F 中性黑 + 柔和红", {
        "bg": "#191919", "surface": "#242424", "surface2": "#2c2c2c", "line": "#343434",
        "ink": "#e9e9e7", "muted": "#9d9d9a", "focus": "#e8837a", "solid": "#c04a40",
        "track": "#2f2f2f", "tabbar": "#1f1f1f", "bar": "#1f1f1f",
    }),
]


def rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def font(size: int, bold: bool = False):
    names = ("msyhbd.ttc", "msyh.ttc", "simhei.ttf") if bold else ("msyh.ttc", "msyhbd.ttc", "simhei.ttf")
    for name in names:
        path = Path(r"C:\Windows\Fonts") / name
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return None


def mock(pal: dict) -> Image.Image:
    """画一屏：顶栏 + 两个任务卡 + 大红圆环 + 按钮 + 底部 tab。"""
    img = Image.new("RGB", (W, H), rgb(pal["bg"]))
    d = ImageDraw.Draw(img)
    f_title = font(17, True)
    f_task = font(13)
    f_clock = font(34, True)
    f_phase = font(12, True)
    f_btn = font(13, True)
    f_tab = font(10)

    # 顶栏
    d.rectangle([0, 0, W, 44], fill=rgb(pal["bar"]))
    d.text((14, 14), "任务", font=f_title, fill=rgb(pal["ink"]))
    d.ellipse([W - 38, 10, W - 12, 36], outline=rgb(pal["line"]), width=2)
    d.text((W - 30, 15), "＋", font=font(13), fill=rgb(pal["muted"]))

    # 两个任务卡
    for index, name in enumerate(("写周报", "背单词")):
        top = 58 + index * 46
        d.rounded_rectangle([12, top, W - 12, top + 38], radius=11,
                            fill=rgb(pal["surface"]), outline=rgb(pal["line"]), width=1)
        d.ellipse([24, top + 14, 34, top + 24], outline=rgb(pal["focus"]), width=2)
        d.text((44, top + 12), name, font=f_task, fill=rgb(pal["ink"]))
        d.text((W - 46, top + 12), "2 🍅", font=f_task, fill=rgb(pal["muted"]))

    # 大红圆环（App 的视觉主角）
    cx, cy, R = W / 2, 262, 62
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=rgb(pal["track"]), width=12)
    d.arc([cx - R, cy - R, cx + R, cy + R], -90, 95, fill=rgb(pal["focus"]), width=12)
    d.text((cx, cy - 22), "25:00", font=f_clock, fill=rgb(pal["ink"]), anchor="mm")
    d.text((cx, cy + 12), "专注中", font=f_phase, fill=rgb(pal["focus"]), anchor="mm")

    # 番茄计数
    d.text((cx, cy + R + 20), "🍅 已完成 2 个番茄", font=f_task, fill=rgb(pal["muted"]), anchor="mm")

    # 三颗按钮
    by = cy + R + 42
    d.rounded_rectangle([16, by, 16 + 74, by + 36], radius=11, fill=rgb(pal["solid"]))
    d.text((16 + 37, by + 18), "开始", font=f_btn, fill=(255, 255, 255), anchor="mm")
    d.rounded_rectangle([98, by, 98 + 74, by + 36], radius=11,
                        fill=rgb(pal["surface"]), outline=rgb(pal["line"]), width=1)
    d.text((98 + 37, by + 18), "暂停", font=f_btn, fill=rgb(pal["muted"]), anchor="mm")
    d.rounded_rectangle([180, by, 180 + 74, by + 36], radius=11,
                        fill=rgb(pal["surface"]), outline=rgb(pal["line"]), width=1)
    d.text((180 + 37, by + 18), "结束任务", font=f_btn, fill=rgb(pal["muted"]), anchor="mm")

    # 底部 tab（三个，第一个是选中的）
    d.rectangle([0, H - 52, W, H], fill=rgb(pal["tabbar"]))
    d.line([0, H - 52, W, H - 52], fill=rgb(pal["line"]), width=1)
    labels = (("☰", "任务"), ("⧗", "倒计时"), ("◔", "总结"))
    for index, (icon, label) in enumerate(labels):
        x = W * (index * 2 + 1) / 6
        color = rgb(pal["focus"]) if index == 0 else rgb(pal["muted"])
        d.text((x, H - 40), icon, font=font(14), fill=color, anchor="mm")
        d.text((x, H - 20), label, font=f_tab, fill=color, anchor="mm")

    return img


def main() -> int:
    cols, rows = 3, 2
    pad, gap, label_h = 26, 22, 40
    width = pad * 2 + cols * W + (cols - 1) * gap
    height = pad * 2 + rows * (H + label_h) + (rows - 1) * gap
    sheet = Image.new("RGB", (width, height), (48, 48, 52))
    pen = ImageDraw.Draw(sheet)
    f_label = font(17, True)

    for index, (name, pal) in enumerate(PALETTES):
        col, row = index % cols, index // cols
        x = pad + col * (W + gap)
        y = pad + row * (H + label_h + gap)
        sheet.paste(mock(pal), (x, y))
        pen.rectangle([x, y, x + W, y + H], outline=(90, 90, 96), width=1)
        pen.text((x + 4, y + H + 10), name, font=f_label, fill=(232, 232, 236))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(OUT, format="PNG", optimize=True)
    print(f"✓ {OUT.relative_to(ROOT)}")
    for name, _ in PALETTES:
        print(f"  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
