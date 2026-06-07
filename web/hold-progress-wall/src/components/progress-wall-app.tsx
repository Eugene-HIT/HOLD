/*
 * 创建时间：2026-06-08
 * 文件职责：统筹进度墙的登录、成员同步、记录读写与页面组合。
 * 主要输入：Supabase 会话、成员数据、记录数据与用户交互。
 * 主要输出：完整的 HOLD 进度墙页面。
 * 最后更改：2026-06-08
 * 变更记录：
 * - 2026-06-08 初始创建主应用组件。
 */

"use client";

import { useEffect, useMemo, useState, useTransition } from "react";
import type { Session, SupabaseClient } from "@supabase/supabase-js";

import { AdminPanel } from "@/components/admin-panel";
import { AuthPanel } from "@/components/auth-panel";
import { RecordDetailPanel } from "@/components/record-detail-panel";
import { RecordEditor } from "@/components/record-editor";
import { RecordsTimeline } from "@/components/records-timeline";
import { APP_CONFIG } from "@/lib/config";
import { COLOR_PRESETS, SAMPLE_RECORDS } from "@/lib/mock-data";
import { getBrowserSupabaseClient } from "@/lib/supabase-client";
import type {
  InviteEditorValue,
  MemberInvite,
  MemberProfile,
  ProgressRecord,
  RecordEditorValue,
} from "@/lib/types";

function hashString(input: string) {
  return Array.from(input).reduce(
    (accumulator, character) => accumulator + character.charCodeAt(0),
    0,
  );
}

function pickColor(seed: string) {
  return COLOR_PRESETS[hashString(seed) % COLOR_PRESETS.length];
}

function makeEmptyRecordDraft() {
  const now = new Date();
  now.setMinutes(now.getMinutes() - (now.getMinutes() % 10), 0, 0);

  const end = new Date(now);
  end.setHours(end.getHours() + 1);

  return {
    title: "",
    details: "",
    startAt: now.toISOString(),
    endAt: end.toISOString(),
    imageUrls: [],
  } satisfies RecordEditorValue;
}

function mapProfile(row: Record<string, unknown>): MemberProfile {
  return {
    id: String(row.id),
    email: String(row.email ?? ""),
    displayName: String(row.display_name ?? "未命名成员"),
    colorHex: String(row.color_hex ?? "#ff8fb1"),
    role: row.role === "admin" ? "admin" : "member",
    createdAt: row.created_at ? String(row.created_at) : undefined,
  };
}

function mapInvite(row: Record<string, unknown>): MemberInvite {
  return {
    id: String(row.id),
    email: String(row.email ?? ""),
    displayNameHint: String(row.display_name_hint ?? ""),
    colorHint: String(row.color_hint ?? "#ff8fb1"),
    role: row.role === "admin" ? "admin" : "member",
    enabled: Boolean(row.enabled),
    createdAt: row.created_at ? String(row.created_at) : undefined,
  };
}

function mapRecord(row: Record<string, unknown>): ProgressRecord {
  return {
    id: String(row.id),
    title: String(row.title ?? "未命名记录"),
    details: String(row.details ?? ""),
    startAt: String(row.start_at),
    endAt: String(row.end_at),
    ownerId: String(row.owner_id),
    ownerName: String(row.owner_name ?? "未知成员"),
    ownerColor: String(row.owner_color ?? "#ff8fb1"),
    imageUrls: Array.isArray(row.image_urls)
      ? row.image_urls.map((item) => String(item))
      : [],
    createdAt: row.created_at ? String(row.created_at) : undefined,
    updatedAt: row.updated_at ? String(row.updated_at) : undefined,
  };
}

async function ensureProfile(
  client: SupabaseClient,
  session: Session,
): Promise<MemberProfile | null> {
  const email = session.user.email?.toLowerCase();

  if (!email) {
    return null;
  }

  const { data: existingProfileRow } = await client
    .from("profiles")
    .select("*")
    .eq("id", session.user.id)
    .maybeSingle();

  const isAdmin = email === APP_CONFIG.adminEmail;
  let inviteRow: Record<string, unknown> | null = null;

  if (!isAdmin) {
    const { data } = await client
      .from("member_invites")
      .select("*")
      .eq("email", email)
      .eq("enabled", true)
      .maybeSingle();

    inviteRow = data;

    if (!inviteRow && !existingProfileRow) {
      return null;
    }
  }

  const profilePayload = {
    id: session.user.id,
    email,
    display_name:
      existingProfileRow?.display_name ??
      inviteRow?.display_name_hint ??
      email.split("@")[0],
    color_hex:
      existingProfileRow?.color_hex ?? inviteRow?.color_hint ?? pickColor(email),
    role:
      isAdmin ? "admin" : existingProfileRow?.role ?? inviteRow?.role ?? "member",
  };

  const { data: savedProfile, error } = await client
    .from("profiles")
    .upsert(profilePayload, { onConflict: "id" })
    .select("*")
    .single();

  if (error) {
    throw error;
  }

  return mapProfile(savedProfile);
}

async function loadWorkspaceData(
  client: SupabaseClient,
  isAdmin: boolean,
): Promise<{
  profiles: MemberProfile[];
  records: ProgressRecord[];
  invites: MemberInvite[];
}> {
  const [{ data: profileRows, error: profilesError }, { data: recordRows, error: recordsError }, invitesResult] =
    await Promise.all([
      client.from("profiles").select("*").order("created_at", { ascending: true }),
      client
        .from("progress_records")
        .select("*")
        .order("start_at", { ascending: false }),
      isAdmin
        ? client
            .from("member_invites")
            .select("*")
            .order("created_at", { ascending: false })
        : Promise.resolve({ data: [], error: null }),
    ]);

  if (profilesError) {
    throw profilesError;
  }

  if (recordsError) {
    throw recordsError;
  }

  if (invitesResult.error) {
    throw invitesResult.error;
  }

  return {
    profiles: (profileRows ?? []).map((row) => mapProfile(row)),
    records: (recordRows ?? []).map((row) => mapRecord(row)),
    invites: (invitesResult.data ?? []).map((row) => mapInvite(row)),
  };
}

async function uploadImages(
  client: SupabaseClient,
  ownerId: string,
  files: File[],
) {
  const urls: string[] = [];

  for (const file of files) {
    const fileName = `${ownerId}/${Date.now()}-${file.name.replace(/\s+/g, "-")}`;
    const { data, error } = await client.storage
      .from(APP_CONFIG.storageBucket)
      .upload(fileName, file, { upsert: false });

    if (error) {
      throw error;
    }

    const { data: publicUrl } = client.storage
      .from(APP_CONFIG.storageBucket)
      .getPublicUrl(data.path);

    urls.push(publicUrl.publicUrl);
  }

  return urls;
}

export function ProgressWallApp() {
  const supabase = useMemo(() => getBrowserSupabaseClient(), []);
  const [session, setSession] = useState<Session | null>(null);
  const [me, setMe] = useState<MemberProfile | null>(null);
  const [profiles, setProfiles] = useState<MemberProfile[]>([]);
  const [records, setRecords] = useState<ProgressRecord[]>(() =>
    supabase ? [] : SAMPLE_RECORDS,
  );
  const [invites, setInvites] = useState<MemberInvite[]>([]);
  const [selectedRecordId, setSelectedRecordId] = useState<string>(() =>
    supabase ? "" : SAMPLE_RECORDS[0].id,
  );
  const [editorOpen, setEditorOpen] = useState(false);
  const [editorValue, setEditorValue] = useState<RecordEditorValue | null>(null);
  const [notice, setNotice] = useState(() =>
    supabase ? "" : "Supabase 配置不可用，当前仅展示本地预览数据。",
  );
  const [emailInput, setEmailInput] = useState(APP_CONFIG.adminEmail);
  const [booting, setBooting] = useState(() => Boolean(supabase));
  const [inviteSaving, startInviteSaving] = useTransition();
  const [recordSaving, startRecordSaving] = useTransition();
  const [authSending, startAuthSending] = useTransition();
  const [profileSaving, startProfileSaving] = useTransition();
  const [inviteDraft, setInviteDraft] = useState<InviteEditorValue>({
    email: "",
    displayNameHint: "",
    colorHint: pickColor("hold-progress-wall"),
    role: "member",
  });

  const selectedRecord =
    records.find((record) => record.id === selectedRecordId) ?? records[0] ?? null;

  const canEditSelectedRecord =
    !!selectedRecord && !!me && (me.role === "admin" || me.id === selectedRecord.ownerId);

  useEffect(() => {
    if (!supabase) {
      return;
    }

    void supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);

      if (!data.session) {
        setMe(null);
        setProfiles([]);
        setInvites([]);
        setRecords(SAMPLE_RECORDS);
        setSelectedRecordId(SAMPLE_RECORDS[0]?.id ?? "");
      }

      setBooting(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);

      if (!nextSession) {
        setMe(null);
        setProfiles([]);
        setInvites([]);
        setRecords(SAMPLE_RECORDS);
        setSelectedRecordId(SAMPLE_RECORDS[0]?.id ?? "");
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [supabase]);

  useEffect(() => {
    if (!supabase || !session) {
      return;
    }

    let active = true;

    const hydrate = async () => {
      try {
        const ensuredProfile = await ensureProfile(supabase, session);

        if (!ensuredProfile) {
          setNotice("当前邮箱不在成员白名单中，请先让管理员添加邮箱。");
          await supabase.auth.signOut();
          return;
        }

        const workspaceData = await loadWorkspaceData(
          supabase,
          ensuredProfile.role === "admin",
        );

        if (!active) {
          return;
        }

        setMe(ensuredProfile);
        setProfiles(workspaceData.profiles);
        setInvites(workspaceData.invites);
        setRecords(workspaceData.records);
        setSelectedRecordId(
          (current) =>
            workspaceData.records.find((record) => record.id === current)?.id ??
            workspaceData.records[0]?.id ??
            "",
        );
        setNotice(
          workspaceData.records.length > 0
            ? "已同步线上记录。新增或编辑后，其他成员会近实时看到变化。"
            : "当前数据库里还没有正式记录，可以先新增一条开发总结。",
        );
      } catch (error) {
        const message = error instanceof Error ? error.message : "同步数据失败";

        if (!active) {
          return;
        }

        setRecords([]);
        setSelectedRecordId("");
        setNotice(`线上数据加载失败：${message}`);
      }
    };

    void hydrate();

    return () => {
      active = false;
    };
  }, [session, supabase]);

  useEffect(() => {
    if (!supabase || !me) {
      return;
    }

    const channel = supabase
      .channel("hold-progress-wall-sync")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "progress_records" },
        () => {
          if (!me) {
            return;
          }

          void loadWorkspaceData(supabase, me.role === "admin").then((data) => {
            setProfiles(data.profiles);
            setInvites(data.invites);
            setRecords(data.records);
          });
        },
      )
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "profiles" },
        () => {
          if (!me) {
            return;
          }

          void loadWorkspaceData(supabase, me.role === "admin").then((data) => {
            setProfiles(data.profiles);
            setInvites(data.invites);
            setRecords(data.records);
          });
        },
      )
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "member_invites" },
        () => {
          if (!me) {
            return;
          }

          void loadWorkspaceData(supabase, me.role === "admin").then((data) => {
            setProfiles(data.profiles);
            setInvites(data.invites);
            setRecords(data.records);
          });
        },
      )
      .subscribe();

    return () => {
      void supabase.removeChannel(channel);
    };
  }, [supabase, me]);

  async function reloadWorkspace(currentProfile: MemberProfile) {
    if (!supabase) {
      return;
    }

    const workspaceData = await loadWorkspaceData(
      supabase,
      currentProfile.role === "admin",
    );
    setProfiles(workspaceData.profiles);
    setInvites(workspaceData.invites);
    setRecords(workspaceData.records);
    setSelectedRecordId(
      workspaceData.records[0]?.id ?? SAMPLE_RECORDS[0]?.id ?? "",
    );
  }

  function openCreateEditor() {
    setEditorValue(makeEmptyRecordDraft());
    setEditorOpen(true);
  }

  function openEditEditor() {
    if (!selectedRecord) {
      return;
    }

    setEditorValue({
      id: selectedRecord.id,
      title: selectedRecord.title,
      details: selectedRecord.details,
      startAt: selectedRecord.startAt,
      endAt: selectedRecord.endAt,
      imageUrls: selectedRecord.imageUrls,
    });
    setEditorOpen(true);
  }

  function handleSignIn() {
    if (!supabase) {
      setNotice("Supabase 未配置，暂时无法登录。");
      return;
    }

    startAuthSending(async () => {
      const { error } = await supabase.auth.signInWithOtp({
        email: emailInput.trim(),
        options: {
          emailRedirectTo:
            typeof window !== "undefined" ? window.location.origin : undefined,
        },
      });

      if (error) {
        setNotice(error.message);
        return;
      }

      setNotice("登录邮件已发送，请去邮箱点开 Magic Link。首次登录前请先加入后台白名单。");
    });
  }

  function handleSignOut() {
    if (!supabase) {
      return;
    }

    void supabase.auth.signOut();
    setNotice("已退出登录。");
  }

  function handleSaveProfile(displayName: string, colorHex: string) {
    if (!supabase || !me) {
      return;
    }

    startProfileSaving(async () => {
      const { error, data } = await supabase
        .from("profiles")
        .update({ display_name: displayName, color_hex: colorHex })
        .eq("id", me.id)
        .select("*")
        .single();

      if (error) {
        setNotice(error.message);
        return;
      }

      const updatedProfile = mapProfile(data);
      setMe(updatedProfile);
      await reloadWorkspace(updatedProfile);
      setNotice("个人名片已更新。之后你新增的记录会自动使用新的昵称和颜色。");
    });
  }

  function handleAddInvite() {
    if (!supabase || !me) {
      return;
    }

    startInviteSaving(async () => {
      const payload = {
        email: inviteDraft.email.trim().toLowerCase(),
        display_name_hint: inviteDraft.displayNameHint.trim(),
        color_hint: inviteDraft.colorHint,
        role: inviteDraft.role,
        enabled: true,
      };

      const { error } = await supabase
        .from("member_invites")
        .upsert(payload, { onConflict: "email" });

      if (error) {
        setNotice(error.message);
        return;
      }

      setInviteDraft({
        email: "",
        displayNameHint: "",
        colorHint: pickColor(String(Date.now())),
        role: "member",
      });
      await reloadWorkspace(me);
      setNotice("成员邮箱已加入白名单。对方现在可以去登录。 ");
    });
  }

  function handleRemoveInvite(inviteId: string) {
    if (!supabase || !me) {
      return;
    }

    startInviteSaving(async () => {
      const { error } = await supabase
        .from("member_invites")
        .delete()
        .eq("id", inviteId);

      if (error) {
        setNotice(error.message);
        return;
      }

      await reloadWorkspace(me);
      setNotice("已移除该白名单邮箱。 ");
    });
  }

  function handleSaveRecord(value: RecordEditorValue, files: File[]) {
    if (!supabase || !me) {
      return;
    }

    startRecordSaving(async () => {
      try {
        const uploadedUrls = await uploadImages(supabase, me.id, files);
        const currentRecord = records.find((record) => record.id === value.id);
        const ownerId = currentRecord?.ownerId ?? me.id;
        const ownerName = currentRecord?.ownerName ?? me.displayName;
        const ownerColor = currentRecord?.ownerColor ?? me.colorHex;

        const payload = {
          id: value.id,
          title: value.title.trim(),
          details: value.details.trim(),
          start_at: value.startAt,
          end_at: value.endAt,
          owner_id: ownerId,
          owner_name: ownerName,
          owner_color: ownerColor,
          image_urls: [...value.imageUrls, ...uploadedUrls],
          updated_at: new Date().toISOString(),
          created_at: currentRecord?.createdAt ?? new Date().toISOString(),
        };

        const { data, error } = await supabase
          .from("progress_records")
          .upsert(payload, { onConflict: "id" })
          .select("*")
          .single();

        if (error) {
          throw error;
        }

        const savedRecord = mapRecord(data);
        await reloadWorkspace(me);
        setSelectedRecordId(savedRecord.id);
        setEditorOpen(false);
        setEditorValue(null);
        setNotice("记录已保存，并同步给其他在线成员。 ");
      } catch (error) {
        setNotice(error instanceof Error ? error.message : "保存记录失败");
      }
    });
  }

  if (booting) {
    return (
      <main className="flex min-h-screen items-center justify-center px-6 py-20">
        <div className="panel-card rounded-[28px] px-8 py-6 text-sm text-[var(--ink-soft)]">
          正在连接 HOLD 进度墙...
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-[1440px] flex-col gap-6 px-4 py-6 md:px-6 md:py-8">
      <header className="panel-card noise-overlay rounded-[32px] px-5 py-6 md:px-8 md:py-7">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="pixel-chip inline-flex rounded-2xl bg-[#fbe0ea] px-3 py-2 text-[11px] font-mono uppercase tracking-[0.22em] text-[#7b506b]">
              dev log wall
            </div>
            <h1 className="mt-4 text-4xl font-bold tracking-tight text-[#47364c] md:text-5xl">
              {APP_CONFIG.siteName}
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-[var(--ink-soft)] md:text-base">
              {APP_CONFIG.subtitle}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {me ? (
              <>
                <div className="flex items-center gap-2 rounded-full bg-white/70 px-4 py-2 text-sm text-[#58485d]">
                  <span
                    className="h-3 w-3 rounded-full"
                    style={{ backgroundColor: me.colorHex }}
                  />
                  {me.displayName}
                </div>
                <button
                  type="button"
                  onClick={openCreateEditor}
                  className="rounded-full bg-[#3f2f43] px-5 py-3 text-sm font-semibold text-white"
                >
                  新增记录
                </button>
                <button
                  type="button"
                  onClick={handleSignOut}
                  className="rounded-full border border-[var(--line)] bg-white/75 px-5 py-3 text-sm text-[#5f4a61]"
                >
                  退出登录
                </button>
              </>
            ) : null}
          </div>
        </div>
      </header>

      {!me ? (
        <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
          <AuthPanel
            email={emailInput}
            loading={authSending}
            notice={notice}
            onEmailChange={setEmailInput}
            onSubmit={handleSignIn}
          />

          <section className="space-y-6">
            <RecordsTimeline
              records={records}
              selectedRecordId={selectedRecordId}
              onSelect={setSelectedRecordId}
            />
            <RecordDetailPanel
              record={selectedRecord}
              canEdit={false}
              onEdit={() => undefined}
            />
          </section>
        </div>
      ) : (
        <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
          <section className="space-y-6">
            <section className="panel-card rounded-[28px] p-5 md:p-6">
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-[#4b3a50]">我的名片</h2>
                  <p className="mt-1 text-sm text-[var(--ink-soft)]">
                    修改昵称和颜色后，你后续新增的记录会自动带上新的显示风格。
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() =>
                    handleSaveProfile(
                      (document.getElementById("profile-name") as HTMLInputElement)
                        ?.value ?? me.displayName,
                      (document.getElementById("profile-color") as HTMLInputElement)
                        ?.value ?? me.colorHex,
                    )
                  }
                  disabled={profileSaving}
                  className="rounded-full bg-[#3f2f43] px-5 py-2.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {profileSaving ? "保存中..." : "保存名片"}
                </button>
              </div>

              <div className="mt-4 grid gap-4 md:grid-cols-[1fr_180px]">
                <input
                  id="profile-name"
                  defaultValue={me.displayName}
                  className="rounded-2xl border border-[var(--line)] bg-white/80 px-4 py-3 outline-none transition focus:border-[#ff8fb1]"
                />
                <input
                  id="profile-color"
                  type="color"
                  defaultValue={me.colorHex}
                  className="h-12 rounded-2xl border border-[var(--line)] bg-white/80 px-2 py-2"
                />
              </div>
            </section>

            <RecordsTimeline
              records={records}
              selectedRecordId={selectedRecordId}
              onSelect={setSelectedRecordId}
            />

            {me.role === "admin" ? (
              <AdminPanel
                inviteDraft={inviteDraft}
                invites={invites}
                profiles={profiles}
                saving={inviteSaving}
                onInviteDraftChange={setInviteDraft}
                onAddInvite={handleAddInvite}
                onRemoveInvite={handleRemoveInvite}
              />
            ) : null}
          </section>

          <section className="space-y-6">
            {notice ? (
              <div className="rounded-[24px] bg-[#fff2f6] px-5 py-4 text-sm text-[#8b4e68]">
                {notice}
              </div>
            ) : null}
            <RecordDetailPanel
              record={selectedRecord}
              canEdit={canEditSelectedRecord}
              onEdit={openEditEditor}
            />
          </section>
        </div>
      )}

      {editorOpen && editorValue ? (
        <RecordEditor
          key={editorValue.id ?? "new-record"}
          initialValue={editorValue}
          saving={recordSaving}
          onClose={() => setEditorOpen(false)}
          onSubmit={handleSaveRecord}
        />
      ) : null}
    </main>
  );
}