"""
Учебная программа, которая не завершается: перерисовывает окно, как htop. Снимок экрана берет termsnap.
"""

import math
import sys
import time

ESC = chr(27)
FRAME_SECONDS = 0.2
WORKERS = ("worker-1", "worker-2", "worker-3", "worker-4")


def bar(share: float, width: int = 30) -> str:
    """
    Полоса загрузки: зеленая до 60%, желтая до 85%, дальше красная.
    """
    filled = round(share * width)
    color = 32 if share < 0.6 else 33 if share < 0.85 else 31
    return f"[{ESC}[{color}m{'|' * filled}{ESC}[0m{' ' * (width - filled)}] {share:6.1%}"


def frame(tick: int) -> str:
    lines = [f"{ESC}[1;7m монитор задач   кадр {tick:>4} {ESC}[0m", ""]
    for index, name in enumerate(WORKERS):
        share = 0.5 + 0.45 * math.sin(tick / 4 + index * 1.7)
        lines.append(f"{name:<9}{bar(max(0.02, min(share, 0.99)))}")
    lines += ["", f"{ESC}[2mв демонстрации программа не завершается сама{ESC}[0m"]
    return "".join(f"{line}{ESC}[K\r\n" for line in lines)


sys.stdout.write(f"{ESC}[2J{ESC}[?25l")
tick = 0
while True:
    sys.stdout.write(f"{ESC}[H{frame(tick)}")
    sys.stdout.flush()
    time.sleep(FRAME_SECONDS)
    tick += 1
