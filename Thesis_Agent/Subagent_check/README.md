# Subagent_check

这里是 thesis-case 级只读检查层。

## 何时进入这一层
当 root 已经把你路由到 `query_or_check`，或者你要做全流程自检、写前检查、提交流程检查、路径/manifest 体检时，进入这一层。

这一层适合做的事：
- 基于 coordination manifest 检查同一 `thesis_case` 的 child-case 结构是否完整
- 检查旧路径、旧命名和错误相对层级
- 检查 readiness gate 是否越级
- 汇总已有 audit / handoff / logic_self_audit 痕迹
- 在用户明确要求时，承接只读的 TeX patch ledger，对指定 writing case 做格式/结构级 patch 记录

## 你要准备什么
- 一个明确的 `thesis_case`
- 一个有效的 coordination case

## 如何开始
如果你想做一次完整检查，可以说：

```text
读取当前层 AGENTS.md 和 README。请对当前 thesis_case 做一次只读检查，并把报告写回当前 check child_case。
```

如果你已经有 coordination case，可以说：

```text
读取当前层 AGENTS.md 和 README。请基于我指定的 coordination case，按 focus_targets 和 check_tracks 做路径、逻辑和历史残留检查。
```

如果你要在 `check` 内只读模拟 `writing_latex` 的 TeX patch：

```text
读取当前层 AGENTS.md 和 README。请把这个线程当作 Subagent_check 的只读 TeX patch session，只记录到当前 check case 的 outputs/writing_patch_session.{md,json}。
```
