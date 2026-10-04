"""生成手机桌面图标，并嵌入各个单文件 App 里。

图标是 180x180 的 PNG，直接以 base64 内联进 HTML，
这样「一个文件就是全部」不被打破，加到手机桌面后也有正经图标而不是网页截图。

用法：
    python tools/make_icon.py            # 全部重新生成
    python tools/make_icon.py focus      # 只处理某一个

页面里需要留一行 <!--HOME-ICON--> 作为插入位置。
"""

from __future__ import annotations

import base64
import io
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZE = 180
ROOT = Path(__file__).resolve().parent.parent
MARKER = "<!--HOME-ICON-->"
# 你自己设计的图标放这里，有的话优先用它
SOURCE = ROOT / "assets-src" / "icon-source.png"
# 你自己设计的图标放这里，有的话优先用它
SOURCE = ROOT / "assets-src" / "icon-source.png"

# 每个 App：目标文件 + 图标样式
APPS = {
    "moneybook": {
        "target": "share/index.html",
        "style": "symbol",
        "symbol": "¥",
        "font_size": 112,
        "top": (110, 140, 255),
        "bottom": (123, 92, 245),
    },
    "focus": {
        "target": "focus/index.html",
        "style": "timer",
        # 白黑配色：白底 + 黑表盘
        "top": (255, 255, 255),
        "bottom": (233, 236, 242),
        "glyph": (16, 16, 18, 255),
    },
}


def load_font(size: int):
    for name in ("msyh.ttc", "msyhbd.ttc", "segoeui.ttf", "arial.ttf"):
        path = Path(r"C:\Windows\Fonts") / name
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return None


def gradient(top, bottom) -> Image.Image:
    image = Image.new("RGBA", (SIZE, SIZE))
    pen = ImageDraw.Draw(image)
    for y in range(SIZE):
        ratio = y / (SIZE - 1)
        color = tuple(round(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3))
        pen.line([(0, y), (SIZE, y)], fill=color + (255,))
    return image


def rounded_mask(radius: int = 42) -> Image.Image:
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], radius=radius, fill=255)
    return mask


def build_moneybook(spec) -> bytes:
    """蓝色渐变 + 白色 ¥"""
    icon = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    icon.paste(gradient(spec["top"], spec["bottom"]), (0, 0), rounded_mask())

    font = load_font(spec["font_size"])
    if font is not None:
        pen = ImageDraw.Draw(icon)
        left, top, right, bottom = pen.textbbox((0, 0), spec["symbol"], font=font)
        pen.text(
            ((SIZE - (right - left)) / 2 - left, (SIZE - (bottom - top)) / 2 - top - 4),
            spec["symbol"],
            font=font,
            fill=(255, 255, 255, 255),
            stroke_width=2,
            stroke_fill=(255, 255, 255, 255),
        )
    return encode(icon)


def build_focus(spec) -> bytes:
    """圆角方块 + 表盘（圆环 + 指针），颜色由 spec 决定"""
    icon = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    icon.paste(gradient(spec["top"], spec["bottom"]), (0, 0), rounded_mask())

    glyph = spec.get("glyph", (255, 255, 255, 255))
    pen = ImageDraw.Draw(icon)
    cx = cy = SIZE / 2
    radius = 52
    pen.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        outline=glyph,
        width=11,
    )
    # 指针：从圆心指向正上方
    pen.line([(cx, cy + 10), (cx, cy - 26)], fill=glyph, width=13)
    pen.ellipse([cx - 6.5, cy + 3.5, cx + 6.5, cy + 16.5], fill=glyph)
    return encode(icon)


def encode(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


BUILDERS = {"symbol": build_moneybook, "timer": build_focus}


def build_from_source() -> bytes | None:
    """用 assets-src/icon-source.png 生成网页图标；没有就返回 None。

    复用安卓那套逻辑：裁掉四周空白、等比缩放，并按"传统图标"的比例留边距 ——
    不留边距的话图案会顶到边缘，在浏览器标签页和"添加到主屏幕"上都不好看。
    """
    if not SOURCE.exists():
        return None
    from make_android_icons import LEGACY_ART_RATIO, fit_square, trim_to_art

    art = Image.open(SOURCE).convert("RGBA")
    bg = art.getpixel((4, 4))[:3]
    canvas = Image.new("RGBA", (SIZE, SIZE), tuple(bg) + (255,))
    inner = round(SIZE * LEGACY_ART_RATIO)
    small = fit_square(trim_to_art(art, bg), inner, bg=bg)
    offset = (SIZE - inner) // 2
    canvas.paste(small, (offset, offset), small)
    canvas.putalpha(rounded_mask())
    return encode(canvas)


def inject(html: str, data_uri: str) -> str:
    links = (
        f'<link rel="icon" type="image/png" href="{data_uri}">\n'
        f'<link rel="apple-touch-icon" href="{data_uri}">'
    )
    if MARKER in html:
        return html.replace(MARKER, links)
    if "apple-touch-icon" in html:
        return re.sub(
            r'<link rel="icon"[^>]*>\s*\n?\s*<link rel="apple-touch-icon"[^>]*>',
            links,
            html,
            count=1,
        )
    raise SystemExit("页面里既没有 <!--HOME-ICON--> 也没有旧图标，无法插入")


def main(argv) -> int:
    wanted = argv[1:] or list(APPS)
    failed = 0
    for name in wanted:
        spec = APPS.get(name)
        if spec is None:
            print(f"没有这个 App：{name}")
            failed += 1
            continue

        target = ROOT / spec["target"]
        if not target.exists():
            print(f"找不到 {target}")
            failed += 1
            continue

        png = None
        if name == "focus":
            png = build_from_source()
        if png is None:
            png = None
        if name == "focus":
            png = build_from_source()
        if png is None:
            png = BUILDERS[spec["style"]](spec)
        uri = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
        html = inject(target.read_text(encoding="utf-8"), uri)
        target.write_text(html, encoding="utf-8")
        print(f"{name:10s} 图标 {len(png):5d} 字节 -> {spec['target']}"
              f"（文件共 {len(html.encode('utf-8'))} 字节）")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
