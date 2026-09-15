/*
 * 创建时间：2026-06-15
 * 文件职责：提供页头用的漂浮 emoji 动效区，替代原有卡片式头图。
 * 主要输入：无。
 * 主要输出：填充页头空间的漂浮 emoji 视觉层。
 * 最后更改：2026-06-16
 * 变更记录：
 * - 2026-06-15 初始创建 emoji 版页头组件。
 * - 2026-06-16 改为无边框的漂浮 emoji 区，减少文字和装饰框。
 */

const EMOJI_ITEMS = [
  { icon: "👾", className: "emoji-orbit--1", sizeClass: "text-4xl md:text-5xl" },
  { icon: "🛸", className: "emoji-orbit--2", sizeClass: "text-3xl md:text-4xl" },
  { icon: "🫧", className: "emoji-orbit--3", sizeClass: "text-4xl md:text-5xl" },
  { icon: "✨", className: "emoji-orbit--4", sizeClass: "text-2xl md:text-3xl" },
  { icon: "🪐", className: "emoji-orbit--5", sizeClass: "text-3xl md:text-4xl" },
  { icon: "👽", className: "emoji-orbit--6", sizeClass: "text-3xl md:text-4xl" },
];

export function EmojiHero() {
  return (
    <section className="emoji-hero relative h-[168px] w-full overflow-hidden rounded-[28px] md:h-[220px]">
      {EMOJI_ITEMS.map((item) => (
        <span
          key={`${item.icon}-${item.className}`}
          className={`emoji-orbit ${item.className} ${item.sizeClass}`}
          aria-hidden="true"
        >
          {item.icon}
        </span>
      ))}
    </section>
  );
}