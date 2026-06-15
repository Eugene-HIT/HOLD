/*
 * 创建时间：2026-06-15
 * 文件职责：提供页头用的简洁 emoji 头图，替代原像素人物区域。
 * 主要输入：无。
 * 主要输出：轻量的 emoji 标签和说明卡片。
 * 最后更改：2026-06-15
 * 变更记录：
 * - 2026-06-15 初始创建 emoji 版页头组件。
 */

const EMOJI_ITEMS = [
  { icon: "👾", label: "记录", note: "像 Claude 那种小外星人感" },
  { icon: "🛸", label: "推进", note: "每周翻页看进度" },
  { icon: "🫧", label: "同步", note: "轻一点，不堆复杂装饰" },
];

export function EmojiHero() {
  return (
    <section className="rounded-[28px] border border-white/70 bg-white/45 px-4 py-4 shadow-[0_16px_40px_rgba(91,108,176,0.12)] backdrop-blur-sm md:px-5 md:py-5">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <p className="text-[11px] font-mono uppercase tracking-[0.24em] text-[#5660a7]">
            emoji header
          </p>
          <h3 className="mt-1 text-base font-semibold text-[#3f457d] md:text-lg">
            简洁一点，用图标提示当前是记录墙
          </h3>
        </div>
        <div className="rounded-full bg-white/70 px-3 py-1 text-[11px] font-mono uppercase tracking-[0.16em] text-[#5b64aa]">
          soft mode
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        {EMOJI_ITEMS.map((item) => (
          <div
            key={item.label}
            className="rounded-[22px] border border-white/75 bg-gradient-to-br from-white/85 to-[#eef3ff] px-4 py-4 text-center shadow-[0_12px_30px_rgba(91,108,176,0.1)]"
          >
            <div className="text-3xl leading-none">{item.icon}</div>
            <p className="mt-3 text-sm font-semibold text-[#4c5292]">{item.label}</p>
            <p className="mt-1 text-xs leading-6 text-[var(--ink-soft)]">{item.note}</p>
          </div>
        ))}
      </div>
    </section>
  );
}