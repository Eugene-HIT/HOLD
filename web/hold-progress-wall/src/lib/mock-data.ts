/*
 * 创建时间：2026-06-08
 * 文件职责：提供未登录时的预览记录与默认色板。
 * 主要输入：无。
 * 主要输出：演示记录、成员颜色集合。
 * 最后更改：2026-06-08
 * 变更记录：
 * - 2026-06-08 初始创建预览数据。
 */

import type { ProgressRecord } from "@/lib/types";

export const COLOR_PRESETS = [
  "#ff8fb1",
  "#7fc8f8",
  "#8bd3a8",
  "#f7b267",
  "#b8a1ff",
  "#ff9770",
];

export const SAMPLE_RECORDS: ProgressRecord[] = [
  {
    id: "sample-imu-record",
    title: "IMU开发",
    details: "开发学习式呼吸检测算法，整理姿态扰动下的峰谷切分思路，并记录后续优化方向。",
    startAt: "2026-06-08T00:30:00+08:00",
    endAt: "2026-06-08T03:20:00+08:00",
    ownerId: "preview-eugene",
    ownerName: "Eugene",
    ownerColor: "#ff8fb1",
    imageUrls: [
      "https://placehold.co/720x480/f8d9e4/6b4d70?text=IMU+Notebook",
      "https://placehold.co/720x480/d7f1e3/497d68?text=Respiration+Peaks",
      "https://placehold.co/720x480/dde8ff/47628a?text=Signal+Review",
    ],
    createdAt: "2026-06-08T03:20:00+08:00",
    updatedAt: "2026-06-08T03:20:00+08:00",
  },
];