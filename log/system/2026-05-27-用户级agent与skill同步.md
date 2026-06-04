# 2026-05-27 用户级 agent 与 skill 同步记录

## 任务名称
将工作区内的通用 agent、prompt 与 skill 同步到用户级目录，支持跨工程复用。

## 修改文件
- c:/Users/LBG/AppData/Roaming/Code/User/prompts/code-architect.agent.md
- c:/Users/LBG/AppData/Roaming/Code/User/prompts/planning-research.agent.md
- c:/Users/LBG/AppData/Roaming/Code/User/prompts/create-code-agent-requirements.prompt.md
- c:/Users/LBG/AppData/Roaming/Code/User/prompts/create-dev-doc-and-log.prompt.md
- c:/Users/LBG/.copilot/skills/engineering-research/SKILL.md
- c:/Users/LBG/.copilot/skills/planning-reference-research/SKILL.md

## 主要变更
- 复制两个工作区级 agent 到 VS Code 用户 prompts 目录
- 复制两个通用 prompt 到 VS Code 用户 prompts 目录
- 复制两个通用 skill 到个人 .copilot/skills 目录
- 保留工作区版本不变，避免影响当前仓库已有使用方式

## 实现思路
- 依据 VS Code customization 参考，将 agent 和 prompt 放置到用户级 prompts 目录
- 依据 skill 参考，将 personal skill 放置到 ~/.copilot/skills 路径
- 采用“新增副本”的方式实现跨项目复用，而不是迁移或替换工作区文件

## 待确认事项
- VS Code 是否需要重载窗口后才会在其他工程中立即发现新加入的 agent / prompt / skill
- 后续如果继续演进这些配置，是否需要建立“工作区版本到用户版本”的同步规范

## 验证结果
- 用户 prompts 目录已出现新增的 4 个文件
- 用户 .copilot/skills 目录已出现新增的 2 个技能目录
- 新增的 Markdown customization 文件未发现诊断错误

## 下一步建议
1. 在 VS Code 中执行一次 Reload Window，确认聊天面板和 / 命令列表已刷新
2. 若后续工作区版本继续演进，建议补一个同步说明文档，避免用户级与工作区级内容漂移