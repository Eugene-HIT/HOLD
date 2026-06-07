-- 创建时间：2026-06-08
-- 文件职责：初始化 HOLD 进度墙需要的成员资料、白名单、记录与图片存储结构。
-- 使用方式：在 Supabase 的 SQL Editor 中执行整个文件。

create extension if not exists pgcrypto;

create or replace function public.handle_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null unique,
  display_name text not null,
  color_hex text not null default '#ff8fb1',
  role text not null default 'member' check (role in ('admin', 'member')),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.member_invites (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  display_name_hint text not null default '',
  color_hint text not null default '#ff8fb1',
  role text not null default 'member' check (role in ('admin', 'member')),
  enabled boolean not null default true,
  created_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.progress_records (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  details text not null default '',
  start_at timestamptz not null,
  end_at timestamptz not null,
  owner_id uuid not null references public.profiles(id) on delete cascade,
  owner_name text not null,
  owner_color text not null default '#ff8fb1',
  image_urls text[] not null default '{}',
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

drop trigger if exists set_profiles_updated_at on public.profiles;
create trigger set_profiles_updated_at
before update on public.profiles
for each row
execute procedure public.handle_updated_at();

drop trigger if exists set_progress_records_updated_at on public.progress_records;
create trigger set_progress_records_updated_at
before update on public.progress_records
for each row
execute procedure public.handle_updated_at();

alter table public.profiles enable row level security;
alter table public.member_invites enable row level security;
alter table public.progress_records enable row level security;

drop policy if exists profiles_select_authenticated on public.profiles;
create policy profiles_select_authenticated
on public.profiles
for select
to authenticated
using (true);

drop policy if exists profiles_insert_self on public.profiles;
create policy profiles_insert_self
on public.profiles
for insert
to authenticated
with check (auth.uid() = id);

drop policy if exists profiles_update_self_or_admin on public.profiles;
create policy profiles_update_self_or_admin
on public.profiles
for update
to authenticated
using (
  auth.uid() = id
  or exists (
    select 1 from public.profiles p
    where p.id = auth.uid() and p.role = 'admin'
  )
)
with check (
  auth.uid() = id
  or exists (
    select 1 from public.profiles p
    where p.id = auth.uid() and p.role = 'admin'
  )
);

drop policy if exists invites_select_self_or_admin on public.member_invites;
create policy invites_select_self_or_admin
on public.member_invites
for select
to authenticated
using (
  lower(email) = lower(coalesce(auth.jwt()->>'email', ''))
  or exists (
    select 1 from public.profiles p
    where p.id = auth.uid() and p.role = 'admin'
  )
);

drop policy if exists invites_manage_admin on public.member_invites;
create policy invites_manage_admin
on public.member_invites
for all
to authenticated
using (
  exists (
    select 1 from public.profiles p
    where p.id = auth.uid() and p.role = 'admin'
  )
)
with check (
  exists (
    select 1 from public.profiles p
    where p.id = auth.uid() and p.role = 'admin'
  )
);

drop policy if exists records_select_authenticated on public.progress_records;
create policy records_select_authenticated
on public.progress_records
for select
to authenticated
using (true);

drop policy if exists records_insert_owner on public.progress_records;
create policy records_insert_owner
on public.progress_records
for insert
to authenticated
with check (auth.uid() = owner_id);

drop policy if exists records_update_owner_or_admin on public.progress_records;
create policy records_update_owner_or_admin
on public.progress_records
for update
to authenticated
using (
  auth.uid() = owner_id
  or exists (
    select 1 from public.profiles p
    where p.id = auth.uid() and p.role = 'admin'
  )
)
with check (
  auth.uid() = owner_id
  or exists (
    select 1 from public.profiles p
    where p.id = auth.uid() and p.role = 'admin'
  )
);

drop policy if exists records_delete_owner_or_admin on public.progress_records;
create policy records_delete_owner_or_admin
on public.progress_records
for delete
to authenticated
using (
  auth.uid() = owner_id
  or exists (
    select 1 from public.profiles p
    where p.id = auth.uid() and p.role = 'admin'
  )
);

insert into storage.buckets (id, name, public)
values ('record-images', 'record-images', true)
on conflict (id) do nothing;

drop policy if exists record_images_read on storage.objects;
create policy record_images_read
on storage.objects
for select
to authenticated
using (bucket_id = 'record-images');

drop policy if exists record_images_insert on storage.objects;
create policy record_images_insert
on storage.objects
for insert
to authenticated
with check (
  bucket_id = 'record-images'
  and (storage.foldername(name))[1] = auth.uid()::text
);

drop policy if exists record_images_update on storage.objects;
create policy record_images_update
on storage.objects
for update
to authenticated
using (
  bucket_id = 'record-images'
  and (storage.foldername(name))[1] = auth.uid()::text
)
with check (
  bucket_id = 'record-images'
  and (storage.foldername(name))[1] = auth.uid()::text
);

drop policy if exists record_images_delete on storage.objects;
create policy record_images_delete
on storage.objects
for delete
to authenticated
using (
  bucket_id = 'record-images'
  and (storage.foldername(name))[1] = auth.uid()::text
);