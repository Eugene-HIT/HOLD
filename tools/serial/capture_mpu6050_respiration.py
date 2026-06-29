#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建时间: 2026-06-18
文件主要职责: 采集 XIAO ESP32S3 + MPU6050 呼吸实验串口数据，并整理为算法可直接使用的 23 列 CSV。
核心输入输出:
- 输入: 串口号、波特率、采集时长或手动中断；默认适配 COM9 / 115200。
- 输出: 23 列运行期 VOFA CSV vofa_runtime.csv。
最后更改时间: 2026-06-18
累加式更改日志:
- 2026-06-18: 新增首版串口采集脚本，兼容当前 MPU6050 呼吸实验的 VOFA 运行帧与文本事件输出。
- 2026-06-18: 配合固件扩列到 23 列，脚本改为只输出单份 CSV，不再生成其他日志文件。
注意事项:
- 当前脚本只采集运行期 23 列数值帧，非数值文本行会直接忽略。
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


VOFA_HEADERS = [
    "device_uptime_ms",
    "breath_carrier_g",
    "breath_baseline_g",
    "breath_detrended_g",
    "breath_filtered_g",
    "slope_g",
    "amplitude_threshold_g",
    "last_peak_value_g",
    "last_trough_value_g",
    "dynamic_acc_norm_g",
    "gyro_norm_dps",
    "motion_level_code",
    "reject_reason_code",
    "has_peak",
    "has_trough",
    "accepted_cycle_count",
    "peak_trough_balance",
    "acc_raw_x",
    "acc_raw_y",
    "acc_raw_z",
    "gyro_raw_x",
    "gyro_raw_y",
    "gyro_raw_z",
]

VOFA_VALUE_COUNT = len(VOFA_HEADERS)
CSV_HEADERS = VOFA_HEADERS
VOFA_LINE_PATTERN = re.compile(r"^\s*[-+0-9eE.,]+\s*$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture MPU6050 respiration serial output and export 23-column VOFA runtime CSV."
    )
    parser.add_argument("--port", default="COM9", help="Serial port, default: COM9")
    parser.add_argument("--baudrate", type=int, default=115200, help="Baudrate, default: 115200")
    parser.add_argument(
        "--duration",
        type=float,
        default=0.0,
        help="Capture duration in seconds. 0 means run until Ctrl+C.",
    )
    parser.add_argument(
        "--output-root",
        default="captures/mpu6050_respiration",
        help="Root output directory, default: captures/mpu6050_respiration",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=1.0,
        help="Serial read timeout in seconds, default: 1.0",
    )
    return parser.parse_args()


def build_output_dir(output_root: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(output_root) / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def is_vofa_frame(line: str) -> bool:
    if not VOFA_LINE_PATTERN.match(line):
        return False

    parts = [part.strip() for part in line.split(",")]
    if len(parts) != VOFA_VALUE_COUNT:
        return False

    try:
        for value in parts:
            float(value)
    except ValueError:
        return False

    return True
def main() -> int:
    args = parse_args()
    output_dir = build_output_dir(args.output_root)

    vofa_csv_path = output_dir / "vofa_runtime.csv"
    raw_line_count = 0
    vofa_frame_count = 0
    malformed_numeric_line_count = 0

    print(f"[capture] port={args.port} baudrate={args.baudrate} output_dir={output_dir}")
    if args.duration > 0:
        print(f"[capture] duration={args.duration:.1f}s")
    else:
        print("[capture] duration=until Ctrl+C")

    end_monotonic = time.monotonic() + args.duration if args.duration > 0 else None

    try:
        with serial.Serial(args.port, args.baudrate, timeout=args.timeout) as ser, \
            vofa_csv_path.open("w", encoding="utf-8", newline="") as vofa_csv_file:
            csv_writer = csv.writer(vofa_csv_file)
            csv_writer.writerow(CSV_HEADERS)

            while True:
                if end_monotonic is not None and time.monotonic() >= end_monotonic:
                    print("[capture] duration reached, stopping")
                    break

                try:
                    raw_bytes = ser.readline()
                except SerialException as error:
                    print(f"[error] serial read failed: {error}", file=sys.stderr)
                    return 1

                if not raw_bytes:
                    continue

                raw_line = raw_bytes.decode("utf-8", errors="replace").rstrip("\r\n")
                raw_line_count += 1

                stripped_line = raw_line.strip()
                if not stripped_line:
                    continue

                if is_vofa_frame(stripped_line):
                    values = [part.strip() for part in stripped_line.split(",")]
                    csv_writer.writerow(values)
                    vofa_csv_file.flush()
                    vofa_frame_count += 1
                    continue

                if VOFA_LINE_PATTERN.match(stripped_line) and "," in stripped_line:
                    malformed_numeric_line_count += 1

    except SerialException as error:
        print(f"[error] failed to open serial port {args.port}: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n[capture] interrupted by user")

    print(
        "[capture] done | raw_lines={raw} vofa_frames={vofa} malformed_numeric={bad}".format(
            raw=raw_line_count,
            vofa=vofa_frame_count,
            bad=malformed_numeric_line_count,
        )
    )
    print(f"[capture] vofa csv: {vofa_csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())