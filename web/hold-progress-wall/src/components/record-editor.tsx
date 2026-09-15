/*
 * 创建时间：2026-06-08
 * 文件职责：负责新增或编辑记录的表单弹层。
 * 主要输入：初始记录、提交状态、提交与关闭回调。
 * 主要输出：记录编辑表单。
 * 最后更改：2026-06-08
 * 变更记录：
 * - 2026-06-08 初始创建记录编辑器。
 */

"use client";

import { useState } from "react";

import type { RecordEditorValue } from "@/lib/types";

interface RecordEditorProps {
  initialValue: RecordEditorValue | null;
  saving: boolean;
  onClose: () => void;
  onSubmit: (value: RecordEditorValue, files: File[]) => void;
}

function toInputValue(value: string) {
  const date = new Date(value);
  const timezoneOffset = date.getTimezoneOffset() * 60 * 1000;
  return new Date(date.getTime() - timezoneOffset).toISOString().slice(0, 16);
}

export function RecordEditor({
  initialValue,
  saving,
  onClose,
  onSubmit,
}: RecordEditorProps) {
  const [draft, setDraft] = useState<RecordEditorValue | null>(initialValue);
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);

  if (!draft) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#312f55]/40 p-4 backdrop-blur-sm">
      <div className="panel-card w-full max-w-3xl rounded-[32px] p-6 md:p-8">
        <div className="mb-5 flex items-center justify-between gap-4">
          <div>
            <p className="text-xs font-mono uppercase tracking-[0.24em] text-[#6669b0]">
              record editor
            </p>
            <h3 className="mt-2 text-2xl font-semibold text-[#48374d]">
              {draft.id ? "编辑记录" : "新增记录"}
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-[var(--line)] bg-white/80 px-4 py-2 text-sm text-[#4f4d82]"
          >
            关闭
          </button>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <label className="space-y-2 md:col-span-2">
            <span className="text-sm font-medium text-[#4f4d82]">标题</span>
            <input
              value={draft.title}
              onChange={(event) =>
                setDraft((current) =>
                  current ? { ...current, title: event.target.value } : current,
                )
              }
              className="w-full rounded-2xl border border-[var(--line)] bg-white/80 px-4 py-3 outline-none transition focus:border-[var(--accent)]"
            />
          </label>

          <label className="space-y-2">
            <span className="text-sm font-medium text-[#4f4d82]">开始时间</span>
            <input
              type="datetime-local"
              value={toInputValue(draft.startAt)}
              onChange={(event) =>
                setDraft((current) =>
                  current
                    ? {
                        ...current,
                        startAt: new Date(event.target.value).toISOString(),
                      }
                    : current,
                )
              }
              className="w-full rounded-2xl border border-[var(--line)] bg-white/80 px-4 py-3 outline-none transition focus:border-[var(--accent)]"
            />
          </label>

          <label className="space-y-2">
            <span className="text-sm font-medium text-[#4f4d82]">结束时间</span>
            <input
              type="datetime-local"
              value={toInputValue(draft.endAt)}
              onChange={(event) =>
                setDraft((current) =>
                  current
                    ? {
                        ...current,
                        endAt: new Date(event.target.value).toISOString(),
                      }
                    : current,
                )
              }
              className="w-full rounded-2xl border border-[var(--line)] bg-white/80 px-4 py-3 outline-none transition focus:border-[var(--accent)]"
            />
          </label>

          <label className="space-y-2 md:col-span-2">
            <span className="text-sm font-medium text-[#4f4d82]">记录说明</span>
            <textarea
              value={draft.details}
              onChange={(event) =>
                setDraft((current) =>
                  current ? { ...current, details: event.target.value } : current,
                )
              }
              rows={6}
              className="w-full rounded-2xl border border-[var(--line)] bg-white/80 px-4 py-3 outline-none transition focus:border-[var(--accent)]"
            />
          </label>

          <label className="space-y-2 md:col-span-2">
            <span className="text-sm font-medium text-[#4f4d82]">新增图片</span>
            <input
              type="file"
              multiple
              accept="image/*"
              onChange={(event) =>
                setPendingFiles(Array.from(event.target.files ?? []))
              }
              className="w-full rounded-2xl border border-[var(--line)] bg-white/80 px-4 py-3 outline-none transition file:mr-4 file:rounded-full file:border-0 file:bg-[#e6e3ff] file:px-4 file:py-2 file:text-sm file:font-medium file:text-[#575ca5]"
            />
          </label>

          <div className="space-y-2 md:col-span-2">
            <span className="text-sm font-medium text-[#4f4d82]">当前图片</span>
            <div className="flex flex-wrap gap-2">
              {draft.imageUrls.length ? (
                draft.imageUrls.map((imageUrl) => (
                  <button
                    key={imageUrl}
                    type="button"
                    onClick={() =>
                      setDraft((current) =>
                        current
                          ? {
                              ...current,
                              imageUrls: current.imageUrls.filter(
                                (item) => item !== imageUrl,
                              ),
                            }
                          : current,
                      )
                    }
                    className="rounded-full border border-[var(--line)] bg-white/80 px-3 py-1 text-xs text-[#6d566f]"
                  >
                    移除已选图片
                  </button>
                ))
              ) : (
                <p className="text-sm text-[var(--ink-soft)]">当前还没有图片。</p>
              )}
            </div>
            {pendingFiles.length ? (
              <p className="text-xs text-[#6669b0]">
                待上传 {pendingFiles.length} 张图片。
              </p>
            ) : null}
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-[var(--line)] bg-white/80 px-5 py-2.5 text-sm text-[#4f4d82]"
          >
            取消
          </button>
          <button
            type="button"
            disabled={saving}
            onClick={() => onSubmit(draft, pendingFiles)}
            className="rounded-full bg-[var(--accent-strong)] px-5 py-2.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
          >
            {saving ? "保存中..." : "保存记录"}
          </button>
        </div>
      </div>
    </div>
  );
}