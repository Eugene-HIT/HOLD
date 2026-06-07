/*
 * 创建时间：2026-06-08
 * 文件职责：展示当前选中记录的详细说明与图片。
 * 主要输入：选中记录、编辑权限与操作回调。
 * 主要输出：记录详情侧栏。
 * 最后更改：2026-06-08
 * 变更记录：
 * - 2026-06-08 初始创建详情侧栏。
 */

import Image from "next/image";

import type { ProgressRecord } from "@/lib/types";

interface RecordDetailPanelProps {
  record: ProgressRecord | null;
  canEdit: boolean;
  onEdit: () => void;
}

function formatDetailTime(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function RecordDetailPanel({
  record,
  canEdit,
  onEdit,
}: RecordDetailPanelProps) {
  return (
    <aside className="panel-card rounded-[28px] p-5 md:p-6">
      {record ? (
        <div className="space-y-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="mb-2 inline-flex items-center gap-2 rounded-full bg-white/70 px-3 py-1 text-xs text-[#866b85]">
                <span
                  className="h-2.5 w-2.5 rounded-full"
                  style={{ backgroundColor: record.ownerColor }}
                />
                {record.ownerName}
              </div>
              <h3 className="text-2xl font-semibold text-[#4a394f]">
                {record.title}
              </h3>
              <p className="mt-2 text-sm text-[var(--ink-soft)]">
                {formatDetailTime(record.startAt)} 至 {formatDetailTime(record.endAt)}
              </p>
            </div>

            {canEdit ? (
              <button
                type="button"
                onClick={onEdit}
                className="rounded-full border border-[var(--line)] bg-white/80 px-4 py-2 text-sm font-medium text-[#5f4a61] transition hover:border-[#ff8fb1]"
              >
                编辑记录
              </button>
            ) : null}
          </div>

          <section className="rounded-[24px] bg-white/65 p-4">
            <h4 className="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-[#8c7386]">
              记录说明
            </h4>
            <p className="whitespace-pre-wrap text-sm leading-7 text-[#58485d]">
              {record.details || "这条记录还没有补充详细说明。"}
            </p>
          </section>

          <section>
            <h4 className="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-[#8c7386]">
              图片记录
            </h4>
            {record.imageUrls.length ? (
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {record.imageUrls.map((imageUrl, index) => (
                  <a
                    key={`${record.id}-${imageUrl}`}
                    href={imageUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="overflow-hidden rounded-[22px] border border-[var(--line)] bg-white/70 transition hover:-translate-y-0.5"
                  >
                    <Image
                      src={imageUrl}
                      alt={`${record.title} 图片 ${index + 1}`}
                      width={720}
                      height={540}
                      className="aspect-[4/3] w-full object-cover"
                      unoptimized
                    />
                  </a>
                ))}
              </div>
            ) : (
              <div className="rounded-[22px] border border-dashed border-[var(--line)] bg-white/55 px-4 py-8 text-center text-sm text-[var(--ink-soft)]">
                当前没有附图。
              </div>
            )}
          </section>
        </div>
      ) : (
        <div className="flex min-h-[320px] items-center justify-center rounded-[24px] border border-dashed border-[var(--line)] bg-white/55 p-8 text-center text-sm leading-7 text-[var(--ink-soft)]">
          从左侧时间轴选中一条记录，这里会展示完整说明、图片和编辑入口。
        </div>
      )}
    </aside>
  );
}