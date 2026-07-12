# Subagent_check Agent Contract

## Role
`Subagent_check` 是 thesis-case 级只读检查层。

这一层负责：
- 只读消费指定 `thesis_case` 的 coordination manifest
- 按论文角色解析本次 `focus_targets`
- 检查路径、manifest、逻辑顺序和旧命名残留
- 汇总已有 audit、handoff、logic_self_audit 线索
- 把检查报告只写回自己的 check case

这一层不负责：
- 修改被检查的 reading、实证或写作 case
- 代替业务 subagent 修 bug
- 把检查状态抬升到 root 顶层

## Top-Level Minimal Structure
顶层只保留：

- `AGENTS.md`
- `README.md`
- `contracts/`
- `scripts/`
- `examples/`

## Child-Case Skeleton
每个 check `child_case` 固定使用：

- `AGENTS.md`
- `README.md`
- `manifests/`
- `requests/`
- `outputs/`
- `scripts/`

## Check Contract
check case 的最小 manifest 固定写在：

- `manifests/thesis_check_manifest.json`

最小字段必须包含：
- `thesis_case`
- `coordination_case_ref`
- `check_scope`
- `focus_targets[]`
- `check_tracks[]`
- `scan_policy`
- `report_preferences`

检查报告固定只写到当前 check case 的：
- `outputs/thesis_check_report.json`
- `outputs/thesis_check_report.md`

`Subagent_check` 不再维护 thesis-wide 的独立 `linked_cases` registry。
thesis-wide case map 以上游 coordination manifest 为准；check 只生成运行时解析出的 target snapshot。

## Output Surface Rule
- `outputs/` 根层只保留当前 live surface，不再堆积历史 audit、maintenance note、一次性方法说明和已结束 patch session。
- 默认 live 入口是 `outputs/thesis_check_report.{json,md}`；若当前 coordination manifest 或固定脚本 contract 还依赖其他说明文件，这些文件可以继续保留在根层，但应保持短摘要形态。
- 一次性审计、历史说明、迁移/维护记录、已完成 patch session 默认进入 `outputs/archive/`。
- 当 case 提供 `outputs/active_surface_index.{json,md}` 时，agent 应优先读取它，再决定是否进入 archive 历史文件。

## Read-Only Patch Guidance Exception
当用户明确要求在 `check` 内模拟 `Subagent_write_latex` 的 `修改模式` 时：

- 只允许面向指定 writing case 记录 read-only patch session
- patch session 只能写回当前 check case 的 `outputs/`
- 只允许记录 patch stub、用户自写新句或用户确认后的 TeX 替换片段、校验意见和状态流转
- 可以为非 prose 的格式/结构问题记录精确 TeX diff stub
- 若 patch 会新增或改写 prose，assistant 只能保留占位 stub，等待用户提供 replacement text
- 当前 active check case 若给出更细的 case-local contract，应以 case-local contract 的 target scope、ledger 文件名和 intake 规则为准
- 不得修改目标 writing case
- 不得由 AI 直接提供 replacement sentence、整段改写稿或自动扩写文本

## Boundaries
这一层可以：
- 检查 coordination-linked target 的 nested case 结构
- 检查旧 workspace 绝对路径
- 检查旧 subagent 名、旧阶段名、flat path 和错误相对层级
- 总结已有 audit/handoff 文件线索
- 在用户明确要求时，为指定 writing case 保存只读 patch session ledger

这一层不能：
- 替用户自动改被检查 case
- 超出 case-local contract 把 patch scope 偷偷扩到 `assets/`、generated outputs 或 target case 内其他目录
- 替用户直接改写正文
- 把 query_or_check 伪装成执行层
- 把自己的 manifest 重新变成 thesis-wide case registry
