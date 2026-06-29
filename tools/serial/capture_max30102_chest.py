#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建时间: 2026-06-23
文件主要职责: 采集 MAX30102 胸口模式 VOFA 串口输出，并导出带表头 CSV。
核心输入输出:
- 输入: 串口号、波特率、采集时长；默认适配 COM9 / 115200 / 60 秒。
- 输出: 单份 CSV，包含当前 MAX30102 胸口 VOFA 运行帧的 12 列数据。
最后更改时间: 2026-06-23
累加式更改日志:
- 2026-06-23: 新增首版 MAX30102 胸口模式采集脚本。
- 2026-06-23: 对齐胸口版最新 12 列 VOFA 输出，补充接触态与检测链调试列。
注意事项:
- 当前脚本只识别纯数值 VOFA 行，其他文本行会自动忽略。
- 若主机未安装 pyserial，请先执行: pip install pyserial
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import serial
    from serial import SerialException
except ImportError as error:
    print("[error] missing dependency: pyserial. install with: pip install pyserial", file=sys.stderr)
    raise SystemExit(2) from error


CSV_HEADERS = [
    "device_uptime_ms",
    "raw_ir",
    "raw_red",
    "avg_ir",
    "avg_red",
    "detrended_ir",
    "filtered_ir",
    "beat_marker",
    "bpm",
    "contact_present",
    "detector_filtered_ir",
    "signal_amplitude",
]

VALUE_COUNT = len(CSV_HEADERS)
NUMERIC_LINE_PATTERN = re.compile(r"^\s*[-+0-9eE.,]+\s*$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture MAX30102 chest-mode VOFA serial stream and export CSV."
    )
    parser.add_argument("--port", default="COM9", help="Serial port, default: COM9")
    parser.add_argument("--baudrate", type=int, default=115200, help="Baudrate, default: 115200")
    parser.add_argument("--duration", type=float, default=60.0, help="Capture duration in seconds, default: 60")
    parser.add_argument(
        "--output-root",
        default="captures/max30102_chest",
        help="Root output directory, default: captures/max30102_chest",
    )
    parser.add_argument("--timeout", type=float, default=1.0, help="Serial read timeout in seconds, default: 1.0")
    return parser.parse_args()


def build_output_dir(output_root: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(output_root) / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def is_valid_vofa_line(line: str) -> bool:
    if not NUMERIC_LINE_PATTERN.match(line):
        return False

    values = [value.strip() for value in line.split(",")]
    if len(values) != VALUE_COUNT:
        return False

    try:
        for value in values:
            float(value)
    except ValueError:
        return False

    return True


def main() -> int:
    args = parse_args()
    output_dir = build_output_dir(args.output_root)
    csv_path = output_dir / "max30102_chest_vofa.csv"

    print(f"[capture] port={args.port} baudrate={args.baudrate} duration={args.duration:.1f}s")
    print(f"[capture] output={csv_path}")

    end_monotonic = time.monotonic() + args.duration
    raw_line_count = 0
    frame_count = 0
    malformed_numeric_line_count = 0

    try:
        with serial.Serial(args.port, args.baudrate, timeout=args.timeout) as ser, \
                csv_path.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(CSV_HEADERS)

            while True:
                if time.monotonic() >= end_monotonic:
                    print("[capture] duration reached, stopping")
                    break

                try:
                    raw_bytes = ser.readline()
                except SerialException as error:
                    print(f"[error] serial read failed: {error}", file=sys.stderr)
                    return 1

                if not raw_bytes:
                    continue

                raw_line_count += 1
                line = raw_bytes.decode("utf-8", errors="replace").rstrip("\r\n")
                stripped_line = line.strip()
                if not stripped_line:
                    continue

                if is_valid_vofa_line(stripped_line):
                    writer.writerow([value.strip() for value in stripped_line.split(",")])
                    csv_file.flush()
                    frame_count += 1
                    continue

                if NUMERIC_LINE_PATTERN.match(stripped_line) and "," in stripped_line:
                    malformed_numeric_line_count += 1

    except SerialException as error:
        print(f"[error] failed to open serial port {args.port}: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n[capture] interrupted by user")

    print(
        "[capture] done | raw_lines={raw} frames={frames} malformed_numeric={bad}".format(
            raw=raw_line_count,
            frames=frame_count,
            bad=malformed_numeric_line_count,
        )
    )
    print(f"[capture] csv={csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())