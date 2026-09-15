/*
 * 创建时间：2026-06-08
 * 文件职责：集中管理进度墙的运行配置与默认值。
 * 主要输入：环境变量或默认演示值。
 * 主要输出：站点标题、管理员邮箱、Supabase 连接信息。
 * 最后更改：2026-06-08
 * 变更记录：
 * - 2026-06-08 初始创建运行配置。
 */

export const APP_CONFIG = {
  siteName: "HOLD 进度墙",
  subtitle: "记录谁做了什么，而不是堆一套复杂项目管理流程。",
  authEmailCooldownMs: 75_000,
  authOtpProjectHourlyLimit: 30,
  adminEmail:
    process.env.NEXT_PUBLIC_ADMIN_EMAIL?.toLowerCase() ??
    "15049922303@163.com",
  supabaseUrl:
    process.env.NEXT_PUBLIC_SUPABASE_URL ??
    "https://oeqivlgrvlzrtxwsgrzm.supabase.co",
  supabasePublishableKey:
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ??
    "sb_publishable_sfiRjOVewD-jQV9R81G_yQ_sZTnBcQX",
  storageBucket: "record-images",
};

export function hasSupabaseConfig() {
  return Boolean(
    APP_CONFIG.supabaseUrl && APP_CONFIG.supabasePublishableKey,
  );
}