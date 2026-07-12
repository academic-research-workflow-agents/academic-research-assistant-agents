# Subagent_regress_stata

这里是回归消费层。

## 何时进入这一层
当 root 已经把你路由到 `empirical_asset_building`，并且你已经有可供回归消费的数据资产，或者已经明确要继续某个回归 child_case 时，进入这一层。

这一层负责：
- 扫描当前 regression child_case 的数据资产
- 帮你确认模型设计
- 跑 baseline 和 follow-up
- 输出表、图、摘要和提交包

如果你还没有准备好可回归面板，应该先回到 `../Subagent_process_data/`。

## 你要准备什么
- 一个 active regression `child_case`
- 已放进该 `child_case/data/` 的回归输入
- 如有设计说明、规格说明或任务说明，放进该 `child_case/config/` 和 `requests/`

真实工作目录统一使用：

- `examples/<thesis_case>/<child_case>/`

这里要注意：
- `thesis_case` 只是区分不同论文的包裹层
- 真正进入工作的始终是 `child_case`

## 如何开始
如果你还没选数据，可以说：

```text
读取当前层 AGENTS.md 和 README。请先扫描当前 regression child_case 的 data/，告诉我这次可以直接做什么、还缺什么确认项。
```

如果你已经知道要继续哪个 case，可以说：

```text
读取当前层 AGENTS.md 和 README。请继续当前 regression child_case 的 baseline、follow-up 或结果汇总。
```

如果你需要外部审核可复现的提交包，可以说：

```text
读取当前层 AGENTS.md 和 README。请把当前 regression child_case 的结果整理成 debug do + clean do 的提交包。
```
