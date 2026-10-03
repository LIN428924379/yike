"""从你发的收款码图片里裁出二维码，嵌进单文件 App。

为什么要裁：原始收款码是一张带背景、带品牌文字的竖版海报；直接放进 App
又占地方又和界面不搭。这里自动找出那块"白色卡片"的区域裁下来，
压到合适大小，再以 base64 内联进 HTML（保持"一个文件就是全部"）。

用法：
    python tools/embed_tip_qr.py
"""

from __future__ import annotations

import base64
import io
import re
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "assets-src" / "tip-qr-source.jpg"
OUT = ROOT / "assets-src" / "tip-qr.png"
TARGET_HTML = ROOT / "focus" / "index.html"
MAX_WIDTH = 520          # 二维码够扫就行，不用留原图那么大
WHITE_LEVEL = 232        # 判定"白"的阈值
ROW_WHITE_RATIO = 0.25   # 一行里白像素超过这个比例，就认为在白卡片里
COLORS = 96              # 调色板压缩，能小很多，且不影响扫码
GAP_TOLERANCE = 90       # 相隔这么近的段算同一块（二维码黑白密集会把卡片切碎）


def _runs(indexes: np.ndarray) -> list[tuple[int, int]]:
    """把 [1,2,3,7,8] 这样的下标切成 [(1,3),(7,8)] 这样的连续段。"""
    out: list[tuple[int, int]] = []
    start = prev = None
    for value in indexes:
        if start is None:
            start = prev = int(value)
            continue
        if int(value) != prev + 1:
            out.append((start, prev))
            start = int(value)
        prev = int(value)
    if start is not None:
        out.append((start, prev))
    return out


def _merge(runs: list[tuple[int, int]], gap: int) -> list[tuple[int, int]]:
    """把挨得近的段合成一块。二维码的黑白方块会把卡片切成好几段。"""
    if not runs:
        return []
    merged = [runs[0]]
    for start, end in runs[1:]:
        last_start, last_end = merged[-1]
        if start - last_end <= gap:
            merged[-1] = (last_start, end)
        else:
            merged.append((start, end))
    return merged


def find_card_box(image: Image.Image) -> tuple[int, int, int, int]:
    """找出那块白色卡片。

    收款码海报上不止一处是白的（底下还有一条白底），而且二维码的黑白方块
    会把卡片行切成好几段 —— 所以先按"连续 + 挨得近"合并成块，再取最高的一块。
    """
    pixels = np.asarray(image.convert("RGB"))
    white = (pixels >= WHITE_LEVEL).all(axis=2)

    row_runs = _merge(_runs(np.where(white.mean(axis=1) > ROW_WHITE_RATIO)[0]), GAP_TOLERANCE)
    row_runs = [run for run in row_runs if run[1] - run[0] > 60]
    if not row_runs:
        raise SystemExit("没找到白卡片区域，裁不了")
    top, bottom = max(row_runs, key=lambda run: run[1] - run[0])

    band = white[top:bottom + 1, :]
    col_runs = _merge(_runs(np.where(band.mean(axis=0) > ROW_WHITE_RATIO)[0]), GAP_TOLERANCE)
    if not col_runs:
        raise SystemExit("没找到卡片左右边界")
    left, right = max(col_runs, key=lambda run: run[1] - run[0])

    return left, top, right + 1, bottom + 1


def main() -> int:
    if not SOURCE.exists():
        print(f"找不到收款码原图：{SOURCE}")
        return 1

    with Image.open(SOURCE) as raw:
        image = raw.convert("RGB")
        print(f"原图 {image.size[0]}x{image.size[1]}")
        box = find_card_box(image)
        print(f"检测到白色卡片区域：{box}  （宽 {box[2]-box[0]}，高 {box[3]-box[1]}）")

        crop = image.crop(box)
        if crop.width > MAX_WIDTH:
            ratio = MAX_WIDTH / crop.width
            crop = crop.resize((MAX_WIDTH, round(crop.height * ratio)), Image.LANCZOS)
        # 调色板压缩：照片部分变少色，二维码依然清晰，体积能小一大截
        crop.convert("RGB").quantize(colors=COLORS, method=Image.MEDIANCUT).save(
            OUT, format="PNG", optimize=True
        )
        print(f"裁剪结果 {crop.size[0]}x{crop.size[1]}  ->  {OUT.relative_to(ROOT)}  "
              f"({OUT.stat().st_size // 1024} KB)")

    payload = base64.b64encode(OUT.read_bytes()).decode("ascii")
    data_uri = "data:image/png;base64," + payload

    html = TARGET_HTML.read_text(encoding="utf-8")
    tag = f'<img id="tip-qr" alt="收款码" src="{data_uri}">'
    new_html, count = re.subn(r'<img id="tip-qr"[^>]*>', tag.replace("\\", "\\\\"), html, count=1)
    if count == 0:
        print("HTML 里找不到 <img id=\"tip-qr\">，无法嵌入")
        return 1

    TARGET_HTML.write_text(new_html, encoding="utf-8")
    print(f"已嵌入 {TARGET_HTML.relative_to(ROOT)}："
          f"{len(html.encode('utf-8')) // 1024} KB -> {len(new_html.encode('utf-8')) // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
