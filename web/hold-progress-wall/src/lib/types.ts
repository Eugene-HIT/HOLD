/*
 * 创建时间：2026-06-08
 * 文件职责：集中定义进度墙业务类型，避免页面层散落匿名结构。
 * 主要输入：无。
 * 主要输出：成员、邀请、记录、表单等类型定义。
 * 最后更改：2026-06-08
 * 变更记录：
 * - 2026-06-08 初始创建类型定义。
 */

export type MemberRole = "admin" | "member";

export interface MemberProfile {
  id: string;
  email: string;
  displayName: string;
  colorHex: string;
  role: MemberRole;
  createdAt?: string;
}

export interface MemberInvite {
  id: string;
  email: string;
  displayNameHint: string;
  colorHint: string;
  role: MemberRole;
  enabled: boolean;
  createdAt?: string;
}

export interface ProgressRecord {
  id: string;
  title: string;
  details: string;
  startAt: string;
  endAt: string;
  ownerId: string;
  ownerName: string;
  ownerColor: string;
  imageUrls: string[];
  createdAt?: string;
  updatedAt?: string;
}

export interface RecordEditorValue {
  id?: string;
  title: string;
  details: string;
  startAt: string;
  endAt: string;
  imageUrls: string[];
}

export interface InviteEditorValue {
  email: string;
  displayNameHint: string;
  colorHint: string;
  role: MemberRole;
}