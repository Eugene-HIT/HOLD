/*
 * 创建时间：2026-06-08
 * 文件职责：管理员维护成员白名单与当前成员概览。
 * 主要输入：邀请列表、成员列表、表单数据与操作回调。
 * 主要输出：后台管理面板。
 * 最后更改：2026-06-08
 * 变更记录：
 * - 2026-06-08 初始创建后台成员管理面板。
 */

import type { InviteEditorValue, MemberInvite, MemberProfile } from "@/lib/types";

interface AdminPanelProps {
  inviteDraft: InviteEditorValue;
  invites: MemberInvite[];
  profiles: MemberProfile[];
  saving: boolean;
  onInviteDraftChange: (value: InviteEditorValue) => void;
  onAddInvite: () => void;
  onRemoveInvite: (inviteId: string) => void;
}

export function AdminPanel({
  inviteDraft,
  invites,
  profiles,
  saving,
  onInviteDraftChange,
  onAddInvite,
  onRemoveInvite,
}: AdminPanelProps) {
  return (
    <section className="panel-card rounded-[28px] p-5 md:p-6">
      <div className="mb-5 flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-mono uppercase tracking-[0.24em] text-[#6a6bb1]">
            admin
          </p>
          <h3 className="mt-2 text-xl font-semibold text-[#4a394f]">成员后台</h3>
        </div>
        <div className="rounded-full bg-[#eef0ff] px-3 py-1 text-xs text-[#5960a6]">
          仅管理员可见
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
        <div className="rounded-[24px] bg-white/70 p-4">
          <h4 className="mb-3 text-sm font-semibold text-[#4f4d82]">添加允许登录的邮箱</h4>
          <div className="grid gap-3 md:grid-cols-2">
            <input
              value={inviteDraft.email}
              onChange={(event) =>
                onInviteDraftChange({
                  ...inviteDraft,
                  email: event.target.value,
                })
              }
              placeholder="成员邮箱"
              className="rounded-2xl border border-[var(--line)] bg-white/80 px-4 py-3 outline-none transition focus:border-[var(--accent)]"
            />
            <input
              value={inviteDraft.displayNameHint}
              onChange={(event) =>
                onInviteDraftChange({
                  ...inviteDraft,
                  displayNameHint: event.target.value,
                })
              }
              placeholder="默认昵称"
              className="rounded-2xl border border-[var(--line)] bg-white/80 px-4 py-3 outline-none transition focus:border-[var(--accent)]"
            />
            <input
              type="color"
              value={inviteDraft.colorHint}
              onChange={(event) =>
                onInviteDraftChange({
                  ...inviteDraft,
                  colorHint: event.target.value,
                })
              }
              className="h-12 rounded-2xl border border-[var(--line)] bg-white/80 px-2 py-2"
            />
            <select
              value={inviteDraft.role}
              onChange={(event) =>
                onInviteDraftChange({
                  ...inviteDraft,
                  role: event.target.value as InviteEditorValue["role"],
                })
              }
              className="rounded-2xl border border-[var(--line)] bg-white/80 px-4 py-3 outline-none transition focus:border-[var(--accent)]"
            >
              <option value="member">member</option>
              <option value="admin">admin</option>
            </select>
          </div>

          <button
            type="button"
            disabled={saving}
            onClick={onAddInvite}
            className="mt-4 rounded-full bg-[var(--accent-strong)] px-5 py-2.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
          >
            {saving ? "保存中..." : "加入白名单"}
          </button>
        </div>

        <div className="rounded-[24px] bg-white/70 p-4">
          <h4 className="mb-3 text-sm font-semibold text-[#4f4d82]">当前成员</h4>
          <div className="space-y-3">
            {profiles.length ? (
              profiles.map((profile) => (
                <div
                  key={profile.id}
                  className="flex items-center justify-between rounded-2xl border border-[var(--line)] bg-white/75 px-4 py-3"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span
                        className="h-3 w-3 rounded-full"
                        style={{ backgroundColor: profile.colorHex }}
                      />
                      <p className="text-sm font-semibold text-[#49394d]">
                        {profile.displayName}
                      </p>
                    </div>
                    <p className="mt-1 text-xs text-[var(--ink-soft)]">
                      {profile.email}
                    </p>
                  </div>
                  <span className="rounded-full bg-[#eef0ff] px-3 py-1 text-xs text-[#5960a6]">
                    {profile.role}
                  </span>
                </div>
              ))
            ) : (
              <p className="text-sm text-[var(--ink-soft)]">还没有成员完成首次登录。</p>
            )}
          </div>
        </div>
      </div>

      <div className="mt-5 rounded-[24px] bg-white/70 p-4">
        <h4 className="mb-3 text-sm font-semibold text-[#4f4d82]">白名单邮箱</h4>
        <div className="space-y-3">
          {invites.length ? (
            invites.map((invite) => (
              <div
                key={invite.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-[var(--line)] bg-white/75 px-4 py-3"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span
                      className="h-3 w-3 rounded-full"
                      style={{ backgroundColor: invite.colorHint }}
                    />
                    <p className="text-sm font-semibold text-[#49394d]">
                      {invite.displayNameHint || "未设置昵称"}
                    </p>
                  </div>
                  <p className="mt-1 text-xs text-[var(--ink-soft)]">{invite.email}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-[#eef0ff] px-3 py-1 text-xs text-[#5960a6]">
                    {invite.role}
                  </span>
                  <button
                    type="button"
                    onClick={() => onRemoveInvite(invite.id)}
                    className="rounded-full border border-[var(--line)] bg-white px-3 py-1 text-xs text-[#5c5f98]"
                  >
                    删除
                  </button>
                </div>
              </div>
            ))
          ) : (
            <p className="text-sm text-[var(--ink-soft)]">当前还没有配置额外成员邮箱。</p>
          )}
        </div>
      </div>
    </section>
  );
}