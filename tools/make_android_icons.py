"""把图标和启动图直接写进安卓工程，不依赖 @capacitor/assets。

为什么不用 @capacitor/assets：它依赖 sharp，而 sharp 在国内装预编译包时会去
GitHub 下载（经常失败），失败后回退源码编译又需要 Visual Studio C++。

图案有两个来源：
  1. 如果 assets-src/icon-source.png 存在（你自己设计的图标，正方形、铺满），就用它
  2. 否则退回脚本自己画的白底黑表盘

生成 / 覆盖：
    mipmap-*/ic_launcher.png             传统图标        48 / 72 / 96 / 144 / 192
    mipmap-*/ic_launcher_round.png       圆形图标        同上
    mipmap-*/ic_launcher_foreground.png  自适应图标·前景  108 / 162 / 216 / 324 / 432
    mipmap-*/ic_launcher_background.png  自适应图标·背景  同上
    drawable*/splash.png                 启动图          按工程里已有的尺寸逐个覆盖
    mipmap-anydpi-v26/ic_launcher*.xml   自适应图标配置
    values/ic_launcher_background.xml    背景色

用法：
    python tools/make_android_icons.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import numpy as np

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "android-app" / "android" / "app" / "src" / "main" / "res"
SOURCE = ROOT / "assets-src" / "icon-source.png"
# 启动画面可以单独配一张源图：图标可以是白底，但 App 内部是深色的，
# 白色启动画面会"闪一下白"再进深色界面，很突兀。有这张就用它。
SPLASH_SOURCE = ROOT / "assets-src" / "icon-source-splash.png"

WHITE = (255, 255, 255, 255)
BLACK = (16, 16, 18, 255)
# 自己画的那个表盘用的颜色（没有手绘图标时才会用到）
GRADIENT_TOP = (255, 255, 255)
GRADIENT_BOTTOM = (233, 236, 242)
DARK_TOP = (16, 17, 20)
DARK_BOTTOM = (0, 0, 0)
GLYPH = BLACK
APP_NAME = "一刻"

# 图案在自适应图标画布上占多大。
# 注意：安卓只显示 108dp 画布中间约 66.7%（72dp），所以这个数字要比"看起来的"小。
# 44% → 在桌面上看起来约占可见区的 66%，透气、极简。
ADAPTIVE_ART_RATIO = 0.44
# 传统桌面图标整个方块都可见，按同样的"视觉大小"换算回来，
# 这样自适应版和传统版在桌面上看起来一样大（不用分别调两个数）。
VISIBLE_RATIO = 0.667
LEGACY_ART_RATIO = ADAPTIVE_ART_RATIO / VISIBLE_RATIO
# 启动图里图标占短边的比例
SPLASH_ART_RATIO = 0.34

DENSITIES = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}
LEGACY_BASE = 48
ADAPTIVE_BASE = 108


# --------------------------------------------------------------------------- #
# 图案来源
# --------------------------------------------------------------------------- #
def load_art(path: Path = SOURCE):
    """返回 (图案, 背景色)。没有图就返回 (None, None)。

    会把四周和底色一样的空白裁掉 —— 有些图（比如"星球+光环"）图案只占画面
    中间一块，不裁的话缩到图标上会显得很小。
    """
    if not path.exists():
        return None, None
    art = Image.open(path).convert("RGBA")
    bg = art.getpixel((4, 4))[:3]
    return trim_to_art(art, bg), bg


def trim_to_art(art: Image.Image, bg, tolerance: int = 20) -> Image.Image:
    """裁掉和底色相同的边缘空白。"""
    pixels = np.asarray(art.convert("RGB")).astype(int)
    diff = np.abs(pixels - np.array(bg)).max(axis=2)
    mask = diff > tolerance
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    if rows.size == 0 or cols.size == 0:
        return art
    return art.crop((int(cols.min()), int(rows.min()), int(cols.max()) + 1, int(rows.max()) + 1))


def fit_square(art: Image.Image, size: int, bg=None) -> Image.Image:
    """等比缩放放进 size 的正方形里 —— 不拉伸变形。

    bg 传颜色就用它填满四周；传 None 就留透明（自适应图标的前景层要透明）。
    """
    ratio = min(size / art.width, size / art.height)
    width = max(1, round(art.width * ratio))
    height = max(1, round(art.height * ratio))
    small = art.resize((width, height), Image.LANCZOS)
    fill = (0, 0, 0, 0) if bg is None else tuple(bg) + (255,)
    canvas = Image.new("RGBA", (size, size), fill)
    canvas.paste(small, ((size - width) // 2, (size - height) // 2), small)
    return canvas


def load_font(size: int):
    for name in ("msyhbd.ttc", "msyh.ttc", "segoeui.ttf", "arial.ttf"):
        path = Path(r"C:\Windows\Fonts") / name
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return None


# --------------------------------------------------------------------------- #
# 自己画的表盘（兜底）
# --------------------------------------------------------------------------- #
def gradient_rect(width: int, height: int, top, bottom) -> Image.Image:
    image = Image.new("RGBA", (width, height))
    pen = ImageDraw.Draw(image)
    for y in range(height):
        ratio = y / max(1, height - 1)
        color = tuple(round(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3))
        pen.line([(0, y), (width, y)], fill=color + (255,))
    return image


def draw_clock(pen: ImageDraw.ImageDraw, size: float, cx: float, cy: float, color=GLYPH) -> None:
    radius = 0.2889 * size
    pen.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                outline=color, width=max(2, round(0.0611 * size)))
    pen.line([(cx, cy + 0.0556 * size), (cx, cy - 0.1444 * size)],
             fill=color, width=max(2, round(0.0722 * size)))
    cap = 0.0361 * size
    pen.ellipse([cx - cap, cy + 0.0556 * size - cap, cx + cap, cy + 0.0556 * size + cap], fill=color)


def rounded_mask(size: int, ratio: float = 0.2333) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1],
                                           radius=round(ratio * size), fill=255)
    return mask


def circle_mask(size: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
    return mask


# --------------------------------------------------------------------------- #
# 四种图
# --------------------------------------------------------------------------- #
def legacy_icon(size: int, art=None, bg=None, circular: bool = False) -> Image.Image:
    """桌面图标：图案居中并留出边距，或自己画的表盘。

    一定要留边距 —— 不留的话，圆角/圆形蒙版会正好切在图案上。
    """
    if art is not None:
        inner = round(size * LEGACY_ART_RATIO)
        small = fit_square(art, inner, bg=bg)
        icon = Image.new("RGBA", (size, size), tuple(bg) + (255,))
        icon.paste(small, ((size - inner) // 2, (size - inner) // 2), small)
    else:
        icon = gradient_rect(size, size, GRADIENT_TOP, GRADIENT_BOTTOM)
        draw_clock(ImageDraw.Draw(icon), size, size / 2, size / 2)
    icon.putalpha(circle_mask(size) if circular else rounded_mask(size))
    return icon


def adaptive_background(size: int, art=None, bg=None) -> Image.Image:
    """自适应图标背景层：整块不透明。"""
    if art is not None and bg is not None:
        return Image.new("RGBA", (size, size), tuple(bg) + (255,))
    return gradient_rect(size, size, GRADIENT_TOP, GRADIENT_BOTTOM)


def adaptive_foreground(size: int, art=None, bg=None) -> Image.Image:
    """自适应图标前景层。

    手绘图案自己带背景色，而背景层就是同一个颜色，所以直接缩放进中间即可 ——
    接缝看不出来，不用去抠图（水彩边缘抠不干净）。
    """
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    if art is not None:
        inner = round(size * ADAPTIVE_ART_RATIO)
        small = fit_square(art, inner, bg=None)
        canvas.paste(small, ((size - inner) // 2, (size - inner) // 2), small)
        return canvas
    draw_clock(ImageDraw.Draw(canvas), size, size / 2, size / 2)
    return canvas


def text_color_for(bg) -> tuple:
    """底色深就用白字，底色浅就用黑字。"""
    r, g, b = bg
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return (32, 30, 28, 255) if luminance > 128 else (246, 246, 248, 255)


def text_color_for(bg) -> tuple:
    """底色深就用白字，底色浅就用黑字。"""
    r, g, b = bg
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return (32, 30, 28, 255) if luminance > 128 else (246, 246, 248, 255)


def splash(width: int, height: int, art=None, bg=None) -> Image.Image:
    """启动图：底色 + 居中的图标 + 应用名。"""
    base = min(width, height)
    icon_size = max(48, round(base * SPLASH_ART_RATIO))
    gap = round(base * 0.05)
    font = load_font(max(12, round(base * 0.075)))
    text_height = round(base * 0.09) if font else 0
    total = icon_size + gap + text_height
    top = max(0, (height - total) // 2)

    if art is not None and bg is not None:
        image = Image.new("RGBA", (width, height), tuple(bg) + (255,))
        icon = fit_square(art, icon_size, bg=None)
        text_color = text_color_for(bg)
    else:
        image = gradient_rect(width, height, DARK_TOP, DARK_BOTTOM)
        icon = gradient_rect(icon_size, icon_size, GRADIENT_TOP, GRADIENT_BOTTOM)
        draw_clock(ImageDraw.Draw(icon), icon_size, icon_size / 2, icon_size / 2)
        text_color = (238, 241, 246, 255)

    icon.putalpha(rounded_mask(icon_size))
    image.paste(icon, ((width - icon_size) // 2, top), icon)

    if font:
        pen = ImageDraw.Draw(image)
        box = pen.textbbox((0, 0), APP_NAME, font=font)
        pen.text(((width - (box[2] - box[0])) / 2 - box[0], top + icon_size + gap),
                 APP_NAME, font=font, fill=text_color)
    return image


# --------------------------------------------------------------------------- #
def save(image: Image.Image, path: Path, count: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGBA").save(path, format="PNG", optimize=True)
    count.append(path)


def main() -> int:
    if not RES.exists():
        print(f"找不到安卓资源目录：{RES}")
        print("（要先在 android-app 里跑过 npx cap add android）")
        return 1

    art, bg = load_art(SOURCE)
    # 启动图可以有自己的源图；没有就用同一张
    if SPLASH_SOURCE.exists():
        splash_art, splash_bg = load_art(SPLASH_SOURCE)
    else:
        splash_art, splash_bg = art, bg

    if art is not None:
        print(f"图标来源：{SOURCE.relative_to(ROOT)}  {art.size[0]}x{art.size[1]}  底色 #{bg[0]:02X}{bg[1]:02X}{bg[2]:02X}")
    else:
        print("图标来源：脚本自己画的表盘（没找到 assets-src/icon-source.png）")
    if splash_art is not None and splash_art is not art:
        print(f"启动图来源：{SPLASH_SOURCE.relative_to(ROOT)}  底色 #{splash_bg[0]:02X}{splash_bg[1]:02X}{splash_bg[2]:02X}")

    written: list[Path] = []

    for name, scale in DENSITIES.items():
        folder = RES / f"mipmap-{name}"
        legacy = round(LEGACY_BASE * scale)
        canvas = round(ADAPTIVE_BASE * scale)

        save(legacy_icon(legacy, art, bg), folder / "ic_launcher.png", written)
        save(legacy_icon(legacy, art, bg, circular=True), folder / "ic_launcher_round.png", written)
        save(adaptive_background(canvas, art, bg), folder / "ic_launcher_background.png", written)
        save(adaptive_foreground(canvas, art, bg), folder / "ic_launcher_foreground.png", written)
        print(f"  mipmap-{name:8s} 图标 {legacy:3d}px，自适应 {canvas:3d}px")

    for existing in sorted(RES.glob("drawable*/splash.png")):
        with Image.open(existing) as probe:
            width, height = probe.size
        save(splash(width, height, splash_art, splash_bg), existing, written)
        print(f"  {existing.parent.name:22s} 启动图 {width}x{height}")

    adaptive_xml = """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@mipmap/ic_launcher_background" />
    <foreground android:drawable="@mipmap/ic_launcher_foreground" />
</adaptive-icon>
"""
    for name in ("ic_launcher.xml", "ic_launcher_round.xml"):
        target = RES / "mipmap-anydpi-v26" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(adaptive_xml, encoding="utf-8")
        written.append(target)
    print("  mipmap-anydpi-v26      自适应图标配置已更新")

    color = "#%02X%02X%02X" % tuple(bg) if bg else "#FFFFFF"
    color_xml = RES / "values" / "ic_launcher_background.xml"
    color_xml.parent.mkdir(parents=True, exist_ok=True)
    color_xml.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<resources>\n"
        f'    <color name="ic_launcher_background">{color}</color>\n'
        "</resources>\n",
        encoding="utf-8",
    )
    written.append(color_xml)
    print(f"  values                  背景色 -> {color}")

    print(f"\n共写入 {len(written)} 个文件，都在 {RES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
