# HOLD 进度墙

用于 2 到 3 人协作查看彼此开发进展的小型记录网站。

## 当前实现

- 顶部轻量甘特时间轴
- 记录详情与图片侧栏
- 邮箱 Magic Link 登录
- 管理员白名单后台
- 成员昵称与颜色自定义
- 基于 Supabase Realtime 的近实时刷新

## 本地开发

```bash
npm install
npm run dev
```

如果你和当前仓库一样希望把依赖尽量放到 D 盘，可以先把 `node_modules` 建成指向 D 盘的 Junction，再执行安装。

## 环境变量

项目已提供：

- [.env.local.example](.env.local.example)：模板
- [.env.local](.env.local)：当前本地开发值

线上部署到 Vercel 时，请在项目设置里配置：

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`
- `NEXT_PUBLIC_ADMIN_EMAIL`

## Supabase 初始化

1. 打开 Supabase 项目的 SQL Editor。
2. 执行 [supabase/schema.sql](supabase/schema.sql)。
3. 在 Authentication 中确认 Email 登录已开启。
4. 在 URL Configuration 中加入本地地址和后续的 Vercel 地址。
5. 首次使用管理员邮箱登录后，再去后台添加其他成员白名单。

## 目录说明

- `src/app`：页面入口与全局样式
- `src/components`：登录、时间轴、详情、编辑器、后台等页面组件
- `src/lib`：类型、配置、Supabase 客户端与示例数据
- `supabase/schema.sql`：数据库与存储初始化脚本

## 部署建议

1. 将本目录推到 GitHub。
2. 在 Vercel 导入该项目。
3. 配置环境变量。
4. 触发首次部署。
5. 使用管理员邮箱登录并进入后台添加成员。
This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
