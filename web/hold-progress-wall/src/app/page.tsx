/*
 * 创建时间：2026-06-08
 * 文件职责：HOLD 进度墙首页入口，承载记录墙主应用。
 * 主要输入：无。
 * 主要输出：进度墙页面组件。
 * 最后更改：2026-06-08
 * 变更记录：
 * - 2026-06-08 初始替换默认首页，接入进度墙主应用。
 */

import { ProgressWallApp } from "@/components/progress-wall-app";

export default function Home() {
  return <ProgressWallApp />;
}
