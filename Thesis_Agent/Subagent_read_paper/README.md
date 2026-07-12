# Subagent_read_paper

这里是文献综述工作流的阅读与证据整理层。

## 何时进入这一层
当 root 已经把你路由到 `reading`，并且你还在做下面这些事时，应该先待在这一层：
- ingest `ref.bib` 或 PDF
- 建立 / 补齐 paper cards
- 整理 evidence ledger
- 围绕某个信息条目做 query 汇总

如果证据底座还没稳定，不要跳过这一层直接写正式章节。

## 你要准备什么
- 一个 active reading `child_case`
- `ref.bib`，或 case-local PDF
- 如有额外任务说明，放到该 `child_case/requests/`

真实工作目录统一使用：

- `examples/<thesis_case>/<child_case>/`

这里要注意：
- `thesis_case` 只是区分不同论文的包裹层
- 真正进入工作的始终是 `child_case`

## 如何开始
如果你要新开一个 reading case，可以说：

```text
读取当前层 AGENTS.md 和 README。请在 examples/<thesis_case>/<child_case>/ 下为我建立或继续一个 reading child_case，并按当前材料自动选择 ingest mode。
```

如果你已经放好 `ref.bib`，可以说：

```text
读取当前层 AGENTS.md 和 README。请在当前 reading child_case 中建立 paper manifest，优先从 ref.bib 的 PDF 附件里找论文。
```

如果你只有 PDF，可以说：

```text
读取当前层 AGENTS.md 和 README。请按 manual_pdf 模式扫描当前 child_case 的 inputs/papers/，并建立 reading 资产。
```

如果你已经有 cards，想做一个聚焦 query，可以说：

```text
读取当前层 AGENTS.md 和 README。请汇总当前 reading child_case 里关于某个信息条目的证据，给我 summary、证据清单和 ref_v2.bib。
```
