# 2026-05-22 Agent 要求补充与 Prompt 创建

## 任务名称
补充代码开发专用 agent 要求，并创建可复用 prompt

## 修改文件
- .github/agents/code-architect.agent.md
- .github/prompts/create-code-agent-requirements.prompt.md

## 主要变更
- 为现有 custom agent 补充“开发前先查看相关 log”的要求
- 细化代码头部中文注释内容，要求包含创建时间、主要职责、核心函数输入输出、最后更改时间、累加式更改日志、注意事项等字段
- 细化 log 记录要求，强调严格标注日期、按模块分类、开发前查看与开发后更新
- 新增一个工作区级 prompt，用于后续重复生成或完善同类代码开发 agent 的要求描述

## 实现思路
- 将长期稳定约束写入 agent 文件，保证被直接调用时行为一致
- 将“生成这类 agent 要求”的流程沉淀为 prompt，便于后续重复复用
- prompt 中保留了对工作区级 agent、日志规范、资料检索、不确定项澄清等核心约束

## 待确认事项
- 文件头注释中的“累加式更改日志”是否需要固定模板
- prompt 后续是否还要扩展为支持用户级 agent 生成
- log 子目录是否最终固定为 firmware、sensors、system、integration、docs 五类

## 验证结果
- .github/prompts/create-code-agent-requirements.prompt.md 已成功创建
- .github/agents/code-architect.agent.md 已成功补充要求
- 本次修改已记录到 log/system

## 下一步建议
1. 在聊天面板中通过 / 选择 prompt，验证其是否可被发现
2. 在 agent 选择器中确认 Code Architect CN 是否可正常使用
3. 如需更强约束，可继续增加专门的 instructions 文件来固定注释模板和 log 模板
