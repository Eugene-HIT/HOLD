/*
 * 创建时间：2026-06-08
 * 文件职责：负责邮箱登录入口与登录说明展示。
 * 主要输入：当前邮箱、提交状态、提示消息。
 * 主要输出：登录卡片界面。
 * 最后更改：2026-06-08
 * 变更记录：
 * - 2026-06-08 初始创建登录面板。
 */

import { APP_CONFIG } from "@/lib/config";

interface AuthPanelProps {
  email: string;
  loading: boolean;
  cooldownSeconds: number;
  notice: string;
  onEmailChange: (value: string) => void;
  onSubmit: () => void;
}

export function AuthPanel({
  email,
  loading,
  cooldownSeconds,
  notice,
  onEmailChange,
  onSubmit,
}: AuthPanelProps) {
  const buttonDisabled = loading || cooldownSeconds > 0;
  const cooldownDisplaySeconds = Math.ceil(APP_CONFIG.authEmailCooldownMs / 1000);

  return (
    <section className="panel-card noise-overlay rounded-[28px] p-6 md:p-8">
      <div className="mb-5 flex items-center gap-3">
        <div className="pixel-chip pixel-float rounded-2xl bg-[var(--accent-soft)] px-3 py-2 text-[11px] font-mono uppercase tracking-[0.22em] text-[#4f4d8c]">
          Magic Link
        </div>
        <p className="text-sm text-[var(--ink-soft)]">
          先用邮箱登录，管理员会在后台添加允许进入的成员邮箱。
        </p>
      </div>

      <div className="space-y-4">
        <label className="block space-y-2">
          <span className="text-sm font-medium text-[#4f4d82]">登录邮箱</span>
          <input
            value={email}
            onChange={(event) => onEmailChange(event.target.value)}
            placeholder="例如：15049922303@163.com"
            className="w-full rounded-2xl border border-[var(--line)] bg-white/80 px-4 py-3 outline-none transition focus:border-[var(--accent)]"
          />
        </label>

        <button
          type="button"
          onClick={onSubmit}
          disabled={buttonDisabled}
          className="w-full rounded-2xl bg-[var(--accent-strong)] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading
            ? "发送登录链接中..."
            : cooldownSeconds > 0
              ? `${cooldownSeconds}s 后可再次发送`
              : "发送邮箱登录链接"}
        </button>

        <div className="rounded-2xl border border-dashed border-[var(--line)] bg-white/55 p-4 text-sm leading-7 text-[var(--ink-soft)]">
          <p>1. 输入邮箱后，Supabase 会发送一封登录邮件。</p>
          <p>2. 首次进入时会检查邮箱是否在成员白名单中。</p>
          <p>3. Supabase 官方默认同一邮箱至少间隔 60 秒才能再次请求 Magic Link。</p>
          <p>4. 同一项目默认还有每小时 {APP_CONFIG.authOtpProjectHourlyLimit} 次 OTP 总量限制，所以体感可能比 60 秒更久。</p>
          <p>5. 当前页面前端按 {cooldownDisplaySeconds} 秒冷却处理，尽量少撞到限流。</p>
          <p>6. 当前页面下方会展示一组预览记录，方便你先看界面形态。</p>
        </div>

        {notice ? (
          <p className="rounded-2xl bg-[var(--notice-bg)] px-4 py-3 text-sm text-[var(--notice-text)]">
            {notice}
          </p>
        ) : null}
      </div>
    </section>
  );
}