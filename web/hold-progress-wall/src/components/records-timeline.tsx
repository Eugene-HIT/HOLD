/*
 * 创建时间：2026-06-08
 * 文件职责：将记录列表绘制为轻量甘特时间轴。
 * 主要输入：记录列表、当前选中项、选择回调。
 * 主要输出：可点击的时间轴视图。
 * 最后更改：2026-06-08
 * 变更记录：
 * - 2026-06-08 初始创建时间轴组件。
 */

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
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function createTimelineMarks(startMs: number, endMs: number) {
  const totalHours = Math.max(1, Math.ceil((endMs - startMs) / (1000 * 60 * 60)));
  const stepHours = totalHours > 24 ? 6 : totalHours > 12 ? 3 : 2;
  const stepMs = stepHours * 60 * 60 * 1000;
  const alignedStart = Math.floor(startMs / stepMs) * stepMs;
  const marks: number[] = [];

  for (let cursor = alignedStart; cursor <= endMs + stepMs; cursor += stepMs) {
    marks.push(cursor);
  }

  return marks;
}

export function RecordsTimeline({
  records,
  selectedRecordId,
  onSelect,
}: RecordsTimelineProps) {
  if (!records.length) {
    return (
      <div className="panel-card rounded-[28px] p-8 text-center text-[var(--ink-soft)]">
        还没有正式记录。登录后点“新增记录”，就能开始同步开发进度。
      </div>
    );
  }

  const starts = records.map((record) => new Date(record.startAt).getTime());
  const ends = records.map((record) => new Date(record.endAt).getTime());
  const minTime = Math.min(...starts) - 30 * 60 * 1000;
  const maxTime = Math.max(...ends) + 30 * 60 * 1000;
  const totalSpan = Math.max(1, maxTime - minTime);
  const marks = createTimelineMarks(minTime, maxTime);
  const width = Math.max(920, marks.length * 120);

  return (
    <div className="panel-card rounded-[32px] p-4 md:p-6">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-[#4b3a50]">开发记录时间轴</h2>
          <p className="mt-1 text-sm text-[var(--ink-soft)]">
            点击任意色块可查看详情。颜色由成员个人名片决定。
          </p>
        </div>
        <div className="rounded-full bg-white/70 px-4 py-2 text-xs font-mono uppercase tracking-[0.2em] text-[#8d6f84]">
          live timeline
        </div>
      </div>

      <div className="overflow-x-auto rounded-[24px] border border-[var(--line)] bg-white/65">
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
            {records.map((record) => {
              const startMs = new Date(record.startAt).getTime();
              const endMs = new Date(record.endAt).getTime();
              const left = ((startMs - minTime) / totalSpan) * 100;
              const widthPercent = Math.max(8, ((endMs - startMs) / totalSpan) * 100);
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
                        ? "border-[#ff8fb1] bg-[#fff4f7]"
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
                        background: `linear-gradient(135deg, ${record.ownerColor}, #6d526d)`,
                      }}
                    >
                      <span className="block font-semibold">{record.title}</span>
                      <span className="mt-1 block text-xs text-white/85">
                        {new Intl.DateTimeFormat("zh-CN", {
                          hour: "2-digit",
                          minute: "2-digit",
                        }).format(new Date(record.startAt))}
                        {" - "}
                        {new Intl.DateTimeFormat("zh-CN", {
                          hour: "2-digit",
                          minute: "2-digit",
                        }).format(new Date(record.endAt))}
                      </span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}