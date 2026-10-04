"""生成到点提醒的铃声（打包进 App，不依赖系统默认提示音）。

为什么要自己做一个：
  系统默认通知音又短又轻，用户反馈"听不清、不够响"。
  自己做一个可以：音色更"铃"（能穿透环境噪音）、时长更长、音量拉满。

铃声设计：
  三个上行音（A5 → C#6 → E6，一个明亮的大三和弦）
  每个音是"钟"的音色：基频 + 几个不完全谐波，衰减包络
  总长约 3.6 秒，归一化到接近满刻度（这样播放时最响）

用法：
    python tools/make_alarm_sound.py
"""

from __future__ import annotations

import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "android-app" / "android" / "app" / "src" / "main" / "res" / "raw" / "pomodoro.wav"

SAMPLE_RATE = 22050      # 单声道 22k 够了，文件也小
DURATION = 3.6           # 总时长（秒）
PEAK = 0.97              # 归一化到 97%，避免削波又能尽量响

# (基频, 起始时间)
NOTES = [(880.00, 0.00), (1108.73, 0.42), (1318.51, 0.84)]
# 钟的音色：(频率倍数, 音量, 衰减速度)
PARTIALS = [(1.00, 1.00, 3.2), (2.01, 0.50, 4.5), (3.00, 0.28, 6.0), (4.18, 0.16, 7.5)]


def bell(freq: float, duration: float) -> np.ndarray:
    """一个钟形的音：几个不完全谐波叠起来，各自按指数衰减。"""
    t = np.linspace(0.0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    tone = np.zeros_like(t)
    for multiple, amplitude, decay in PARTIALS:
        tone += amplitude * np.sin(2 * np.pi * freq * multiple * t) * np.exp(-decay * t)

    # 6 毫秒的起音，避免开头"啪"的一声
    attack = max(1, int(SAMPLE_RATE * 0.006))
    tone[:attack] *= np.linspace(0.0, 1.0, attack)
    return tone


def main() -> int:
    track = np.zeros(int(SAMPLE_RATE * DURATION))
    for freq, start in NOTES:
        tone = bell(freq, DURATION - start)
        begin = int(SAMPLE_RATE * start)
        track[begin:begin + len(tone)] += tone

    peak = float(np.max(np.abs(track)))
    if peak <= 0:
        print("✗ 生成出来是静音，检查一下参数")
        return 1
    track = track / peak * PEAK

    samples = (track * 32767.0).astype(np.int16)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(samples.tobytes())

    size_kb = OUT.stat().st_size / 1024
    print(f"✓ 生成 {OUT.relative_to(ROOT)}")
    print(f"  {DURATION} 秒 · 单声道 {SAMPLE_RATE}Hz · {size_kb:.0f} KB")
    print(f"  峰值 {np.max(np.abs(samples))}/32767（拉满了，播放时最响）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
