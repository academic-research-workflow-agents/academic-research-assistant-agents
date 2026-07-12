# Subagent_integrate

这里是 thesis-case 级统筹层。

## 何时进入这一层
当 root 已经把你路由到 `integration`，或者你虽然要做论文，但还没摸清当前 `thesis_case` 在各层分别有哪些 `child_case` 时，进入这一层。

这一层适合做的事：
- 新论文刚开工时，先确认应该建立哪些 case
- 用户已经建了一部分 case，但还没摸清全局映射
- 同一 `thesis_case` 需要跨 reading、实证、写作多层协同
- 想先拿到一个推荐顺序，再进入具体 subagent 执行

## 你要准备什么
- 一个明确的 `thesis_case`
- 如果已经存在 child_case，尽量说明你已知的 case 名
- 如果你还没建任何 case，也可以直接从这里开始

## 如何开始
如果你还没建好任何 case，可以说：

```text
读取当前层 AGENTS.md 和 README。请以当前 thesis_case 为目标，告诉我应该先建立哪些 child_case，并按推荐顺序排好。
```

如果你已经建好部分 case，可以说：

```text
读取当前层 AGENTS.md 和 README。请扫描当前 thesis_case 在四个业务 subagent 下已经有哪些 child_case，并更新 coordination manifest。
```

如果你想让它给出下一步入口，可以说：

```text
读取当前层 AGENTS.md 和 README。请根据当前 thesis_case 的 linked cases、readiness gates 和 blockers，告诉我下一步先进入哪个 subagent。
```
