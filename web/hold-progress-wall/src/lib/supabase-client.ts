/*
 * 创建时间：2026-06-08
 * 文件职责：创建浏览器端 Supabase 客户端实例。
 * 主要输入：站点配置中的 Project URL 与 Publishable Key。
 * 主要输出：浏览器端 SupabaseClient 或空值。
 * 最后更改：2026-06-08
 * 变更记录：
 * - 2026-06-08 初始创建浏览器端客户端工厂。
 */

import { createClient, type SupabaseClient } from "@supabase/supabase-js";

import { APP_CONFIG, hasSupabaseConfig } from "@/lib/config";

let browserClient: SupabaseClient | null = null;

export function getBrowserSupabaseClient() {
  if (!hasSupabaseConfig()) {
    return null;
  }

  if (!browserClient) {
    browserClient = createClient(
      APP_CONFIG.supabaseUrl,
      APP_CONFIG.supabasePublishableKey,
      {
        auth: {
          persistSession: true,
          autoRefreshToken: true,
          detectSessionInUrl: true,
        },
      },
    );
  }

  return browserClient;
}