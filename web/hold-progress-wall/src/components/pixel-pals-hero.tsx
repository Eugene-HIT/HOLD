/*
 * 创建时间：2026-06-08
 * 文件职责：提供页头使用的像素人物动效场景，强化进度墙的轻松感与辨识度。
 * 主要输入：无。
 * 主要输出：三位像素角色与星点装饰组成的紫蓝主题头图。
 * 最后更改：2026-06-08
 * 变更记录：
 * - 2026-06-08 初始创建像素人物动效组件。
 */

interface PixelBuddy {
  id: string;
  label: string;
  bubble: string;
  className: string;
  palette: Record<string, string>;
  pattern: string[];
}

const PIXEL_BUDDIES: PixelBuddy[] = [
  {
    id: "builder",
    label: "builder",
    bubble: "build",
    className: "pixel-sprite--1",
    palette: {
      h: "#2f2852",
      s: "#ffd9c8",
      c: "#ffffff",
      j: "#8d7dff",
      p: "#6ea8ff",
      b: "#5a59a2",
      e: "#2a2447",
    },
    pattern: [
      "...hhhh...",
      "..hcssh...",
      "..hssssh..",
      "..hseshh..",
      "..hjjjhh..",
      "..hjjjhh..",
      "..hppphh..",
      "..hppphh..",
      "...p..p...",
      "..bb..bb..",
    ],
  },
  {
    id: "reviewer",
    label: "review",
    bubble: "check",
    className: "pixel-sprite--2",
    palette: {
      h: "#312b5f",
      s: "#ffe3d7",
      c: "#ffffff",
      j: "#a38bff",
      p: "#7bd3ff",
      b: "#5f72c8",
      e: "#251f48",
    },
    pattern: [
      "...hhhh...",
      "..hcssh...",
      "..hssssh..",
      "..hseshh..",
      "..hjjjhh..",
      "..hjjjhh..",
      "..hppphh..",
      "..hppphh..",
      "...p..p...",
      "..bb..bb..",
    ],
  },
  {
    id: "writer",
    label: "log it",
    bubble: "ship",
    className: "pixel-sprite--3",
    palette: {
      h: "#2d2755",
      s: "#ffd7d1",
      c: "#ffffff",
      j: "#6ea8ff",
      p: "#c39cff",
      b: "#4d5db4",
      e: "#231d44",
    },
    pattern: [
      "...hhhh...",
      "..hcssh...",
      "..hssssh..",
      "..hseshh..",
      "..hjjjhh..",
      "..hjjjhh..",
      "..hppphh..",
      "..hppphh..",
      "...p..p...",
      "..bb..bb..",
    ],
  },
];

export function PixelPalsHero() {
  return (
    <section className="pixel-scene rounded-[28px] px-4 py-4 md:px-5 md:py-5">
      <div className="pixel-star pixel-star--1" />
      <div className="pixel-star pixel-star--2" />
      <div className="pixel-star pixel-star--3" />
      <div className="pixel-star pixel-star--4" />

      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <p className="text-[11px] font-mono uppercase tracking-[0.24em] text-[#5660a7]">
            pixel crew
          </p>
          <h3 className="mt-1 text-base font-semibold text-[#3f457d] md:text-lg">
            今天谁在 build，谁在 check，谁在 log
          </h3>
        </div>
        <div className="rounded-full bg-white/70 px-3 py-1 text-[11px] font-mono uppercase tracking-[0.16em] text-[#5b64aa]">
          cute mode
        </div>
      </div>

      <div className="pixel-stage">
        {PIXEL_BUDDIES.map((buddy) => (
          <div key={buddy.id} className={`pixel-sprite ${buddy.className}`}>
            <div className="rounded-full bg-white/75 px-3 py-1 text-[10px] font-mono uppercase tracking-[0.18em] text-[#5962a8]">
              {buddy.bubble}
            </div>
            <div
              className="pixel-character-grid"
              style={{ gridTemplateColumns: `repeat(${buddy.pattern[0]?.length ?? 0}, minmax(0, 1fr))` }}
            >
              {buddy.pattern.flatMap((row, rowIndex) =>
                Array.from(row).map((cell, columnIndex) => (
                  <span
                    key={`${buddy.id}-${rowIndex}-${columnIndex}`}
                    className="pixel-cell"
                    style={{
                      backgroundColor:
                        cell === "." ? "transparent" : buddy.palette[cell] ?? "transparent",
                    }}
                  />
                )),
              )}
            </div>
            <div className="pixel-shadow" />
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-[#5a63ab]">
              {buddy.label}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}