"""生成打包安卓 App 需要的图标和启动图。

产物（放在 android-app/assets/）：
    icon.png    1024x1024   应用图标（铺满整张，不加圆角——圆角由安卓系统自己裁）
    splash.png  2732x2732   启动图（深色底 + 居中的图标 + 应用名）

用法：
    python tools/make_app_assets.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "android-app" / "assets"
ICON_SIZE = 1024
SPLASH_SIZE = 2732
WHITE = (255, 255, 255, 255)
GRADIENT_TOP = (255, 138, 104)
GRADIENT_BOTTOM = (226, 58, 44)
DARK_TOP = (24, 28, 38)
DARK_BOTTOM = (15, 17, 22)
APP_NAME = "一刻"


def load_font(size: int):
    for name in ("msyhbd.ttc", "msyh.ttc", "segoeui.ttf", "arial.ttf"):
        path = Path(r"C:\Windows\Fonts") / name
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return None


def gradient(size: int, top, bottom) -> Image.Image:
    image = Image.new("RGBA", (size, size))
    pen = ImageDraw.Draw(image)
    for y in range(size):
        ratio = y / (size - 1)
        color = tuple(round(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3))
        pen.line([(0, y), (size, y)], fill=color + (255,))
    return image


def draw_clock(pen: ImageDraw.ImageDraw, size: int, cx: float, cy: float) -> None:
    """白色的表盘：圆环 + 指针。比例跟网页里的图标一致。"""
    radius = 0.2889 * size
    pen.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        outline=WHITE,
        width=max(2, round(0.0611 * size)),
    )
    pen.line(
        [(cx, cy + 0.0556 * size), (cx, cy - 0.1444 * size)],
        fill=WHITE,
        width=max(2, round(0.0722 * size)),
    )
    cap = 0.0361 * size
    pen.ellipse([cx - cap, cy + 0.0556 * size - cap, cx + cap, cy + 0.0556 * size + cap], fill=WHITE)


def rounded_mask(size: int, radius_ratio: float = 0.2333) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size - 1, size - 1], radius=round(radius_ratio * size), fill=255
    )
    return mask


def build_icon() -> Image.Image:
    """应用图标：铺满整张，不加圆角（圆角交给系统裁）。"""
    icon = gradient(ICON_SIZE, GRADIENT_TOP, GRADIENT_BOTTOM).convert("RGBA")
    draw_clock(ImageDraw.Draw(icon), ICON_SIZE, ICON_SIZE / 2, ICON_SIZE / 2)
    return icon


def build_splash() -> Image.Image:
    """启动图：深色底 + 居中的圆角图标 + 应用名。"""
    splash = gradient(SPLASH_SIZE, DARK_TOP, DARK_BOTTOM).convert("RGBA")

    icon_size = 860
    icon = gradient(icon_size, GRADIENT_TOP, GRADIENT_BOTTOM).convert("RGBA")
    draw_clock(ImageDraw.Draw(icon), icon_size, icon_size / 2, icon_size / 2)
    icon.putalpha(rounded_mask(icon_size))

    left = (SPLASH_SIZE - icon_size) // 2
    top = round(SPLASH_SIZE * 0.34)
    splash.paste(icon, (left, top), icon)

    font = load_font(150)
    if font is not None:
        pen = ImageDraw.Draw(splash)
        box = pen.textbbox((0, 0), APP_NAME, font=font)
        pen.text(
            ((SPLASH_SIZE - (box[2] - box[0])) / 2 - box[0], top + icon_size + 120),
            APP_NAME,
            font=font,
            fill=(238, 241, 246, 255),
        )
    return splash


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    icon = build_icon()
    icon.save(OUT / "icon.png", format="PNG", optimize=True)

    splash = build_splash()
    splash.save(OUT / "splash.png", format="PNG", optimize=True)

    for name in ("icon.png", "splash.png"):
        path = OUT / name
        with Image.open(path) as check:
            print(f"{name:12s} {check.size[0]}x{check.size[1]}  {path.stat().st_size // 1024} KB")
    print(f"已生成到 {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
