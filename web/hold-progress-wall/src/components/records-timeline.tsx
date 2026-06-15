/*
 * 创建时间：2026-06-08
 * 文件职责：将记录列表绘制为轻量甘特时间轴。
 * 主要输入：记录列表、当前选中项、选择回调。
 * 主要输出：可点击的时间轴视图。
 * 最后更改：2026-06-08
 * 变更记录：
 * - 2026-06-08 初始创建时间轴组件。
 */

"use client";

import { useMemo, useState } from "react";

import type { ProgressRecord } from "@/lib/types";

interface RecordsTimelineProps {
  records: ProgressRecord[];
  selectedRecordId?: string;
  onSelect: (recordId: string) => void;
}

function formatTimelineLabel(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "numeric",
    day: "numeric",
    weekday: "short",
  }).format(new Date(value));
}

function formatTimeOnly(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function getWeekStart(date: Date) {
  const value = new Date(date);
  const day = value.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  value.setDate(value.getDate() + diff);
  value.setHours(0, 0, 0, 0);
  return value;
}

function toWeekKey(date: Date) {
  return getWeekStart(date).toISOString();
}

function createWeekMarks(startMs: number) {
  const marks: number[] = [];
  const stepMs = 24 * 60 * 60 * 1000;
  const endMs = startMs + 7 * stepMs;

  for (let cursor = startMs; cursor <= endMs; cursor += stepMs) {
    marks.push(cursor);
  }

  return marks;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

export function RecordsTimeline({
  records,
  selectedRecordId,
  onSelect,
}: RecordsTimelineProps) {
  const weekKeys = useMemo(() => {
    return Array.from(
      new Set(records.map((record) => toWeekKey(new Date(record.startAt)))),
    ).sort((left, right) => new Date(left).getTime() - new Date(right).getTime());
  }, [records]);

  const selectedRecord =
    records.find((record) => record.id === selectedRecordId) ?? records[0];

  const selectedWeekKey = selectedRecord
    ? toWeekKey(new Date(selectedRecord.startAt))
    : weekKeys[weekKeys.length - 1];

  const [manualWeekKey, setManualWeekKey] = useState<string | null>(null);

  const currentWeekKey =
    manualWeekKey && weekKeys.includes(manualWeekKey)
      ? manualWeekKey
      : selectedWeekKey;

  if (!records.length || !selectedWeekKey) {
    return (
      <div className="panel-card rounded-[28px] p-8 text-center text-[var(--ink-soft)]">
        还没有正式记录。登录后点“新增记录”，就能开始同步开发进度。
      </div>
    );
  }

  const currentWeekIndex = Math.max(
    0,
    weekKeys.findIndex((weekKey) => weekKey === currentWeekKey),
  );

  const resolvedWeekKey = weekKeys[currentWeekIndex] ?? weekKeys[0];
  const weekStart = new Date(resolvedWeekKey);
  const weekEnd = new Date(weekStart);
  weekEnd.setDate(weekEnd.getDate() + 7);

  const minTime = weekStart.getTime();
  const maxTime = weekEnd.getTime();
  const totalSpan = Math.max(1, maxTime - minTime);
  const marks = createWeekMarks(minTime);
  const width = 980;

  const weekRecords = records.filter((record) => {
    const recordStart = new Date(record.startAt).getTime();
    const recordEnd = new Date(record.endAt).getTime();

    return recordEnd > minTime && recordStart < maxTime;
  });

  const weekRangeLabel = `${new Intl.DateTimeFormat("zh-CN", {
    month: "numeric",
    day: "numeric",
  }).format(weekStart)} - ${new Intl.DateTimeFormat("zh-CN", {
    month: "numeric",
    day: "numeric",
  }).format(new Date(maxTime - 1))}`;

  return (
    <div className="panel-card rounded-[32px] p-4 md:p-6">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-[#45497d]">开发记录时间轴</h2>
          <p className="mt-1 text-sm text-[var(--ink-soft)]">
            现在按周分页展示，避免跨度一拉长整页一起被撑开。
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() =>
              setManualWeekKey(
                weekKeys[clamp(currentWeekIndex - 1, 0, weekKeys.length - 1)] ??
                  resolvedWeekKey,
              )
            }
            disabled={currentWeekIndex === 0}
            className="rounded-full border border-[var(--line)] bg-white/80 px-3 py-2 text-xs font-semibold text-[#5f66ab] disabled:cursor-not-allowed disabled:opacity-50"
          >
            上一周
          </button>
          <div className="rounded-full bg-[#eef1ff] px-4 py-2 text-xs font-mono uppercase tracking-[0.12em] text-[#5f66ab]">
            {weekRangeLabel}
          </div>
          <button
            type="button"
            onClick={() =>
              setManualWeekKey(
                weekKeys[clamp(currentWeekIndex + 1, 0, weekKeys.length - 1)] ??
                  resolvedWeekKey,
              )
            }
            disabled={currentWeekIndex === weekKeys.length - 1}
            className="rounded-full border border-[var(--line)] bg-white/80 px-3 py-2 text-xs font-semibold text-[#5f66ab] disabled:cursor-not-allowed disabled:opacity-50"
          >
            下一周
          </button>
        </div>
      </div>

      <div className="rounded-[24px] border border-[var(--line)] bg-white/65">
        <div className="min-w-full p-4" style={{ width }}>
          <div className="grid grid-cols-[220px_1fr] gap-4">
            <div />
            <div className="relative h-12">
              {marks.map((mark) => {
                const left = ((mark - minTime) / totalSpan) * 100;

                return (
                  <div
                    key={mark}
                    className="absolute top-0 h-full text-[11px] text-[#826b84]"
                    style={{ left: `${left}%` }}
                  >
                    <div className="h-full w-px bg-[var(--line)]" />
                    <span className="absolute left-2 top-1 whitespace-nowrap">
                      {formatTimelineLabel(new Date(mark).toISOString())}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="timeline-grid mt-3 space-y-3 rounded-[20px] p-3">
            {weekRecords.length ? (
              weekRecords.map((record) => {
              const startMs = new Date(record.startAt).getTime();
              const endMs = new Date(record.endAt).getTime();
              const clampedStart = clamp(startMs, minTime, maxTime);
              const clampedEnd = clamp(endMs, minTime, maxTime);
              const left = ((clampedStart - minTime) / totalSpan) * 100;
              const widthPercent = Math.max(
                8,
                ((Math.max(clampedEnd, clampedStart + 30 * 60 * 1000) - clampedStart) /
                  totalSpan) *
                  100,
              );
              const selected = selectedRecordId === record.id;

              return (
                <div
                  key={record.id}
                  className="grid grid-cols-[220px_1fr] items-center gap-4"
                >
                  <button
                    type="button"
                    onClick={() => onSelect(record.id)}
                    className={`rounded-[20px] border px-4 py-3 text-left transition ${
                      selected
                        ? "border-[var(--accent)] bg-[#f0efff]"
                        : "border-transparent bg-white/75 hover:border-[var(--line)]"
                    }`}
                  >
                    <p className="text-sm font-semibold text-[#48374d]">{record.title}</p>
                    <p className="mt-1 text-xs text-[var(--ink-soft)]">{record.ownerName}</p>
                  </button>

                  <div className="relative h-16 rounded-[18px] bg-white/55 px-3">
                    <button
                      type="button"
                      onClick={() => onSelect(record.id)}
                      className={`absolute top-1/2 -translate-y-1/2 rounded-[18px] px-4 py-3 text-left text-sm text-white shadow-lg transition ${
                        selected ? "ring-4 ring-white/80" : "hover:scale-[1.01]"
                      }`}
                      style={{
                        left: `${left}%`,
                        width: `${widthPercent}%`,
                        background: `linear-gradient(135deg, ${record.ownerColor}, #4d63b0)`,
                      }}
                    >
                      <span className="block font-semibold">{record.title}</span>
                      <span className="mt-1 block text-xs text-white/85">
                        {formatTimeOnly(record.startAt)}
                        {" - "}
                        {formatTimeOnly(record.endAt)}
                      </span>
                    </button>
                  </div>
                </div>
              );
              })
            ) : (
              <div className="rounded-[18px] border border-dashed border-[var(--line)] bg-white/70 px-4 py-8 text-center text-sm text-[var(--ink-soft)]">
                这一周还没有记录，切到上一周或下一周看看。
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}