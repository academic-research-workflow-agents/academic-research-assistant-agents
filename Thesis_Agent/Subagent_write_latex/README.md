# Subagent_write_latex

这里是 integrated thesis 的统一写作层。

## 何时进入这一层
当 root 已经把你路由到 `thesis_writing`，并且你已经有稳定的 reading outputs、tables、figures、summaries、submission bundles 或其他可写作资产时，进入这一层。

这一层负责：
- 搭建论文写作 child_case
- 组织双语稿件
- 生成模板注入所需的章节和表图片段
- 从 thesis-case 专属模板源复制到 case-local worktree 后编译 PDF

如果上游资产还没稳定，应该先回到：
- `../Subagent_read_paper/`
- `../Subagent_process_data/`
- `../Subagent_regress_stata/`

如果你现在还没摸清同一 `thesis_case` 在各层分别对应哪个 `child_case`，应该先回到 `../Subagent_integrate/`。

## 你要准备什么
- 一个 active writing `child_case`
- 已稳定的上游 case outputs
- 如有写作说明、章节安排或稿件片段，放到该 `child_case/requests/` 和 `manuscript/`

真实工作目录统一使用：

- `examples/<thesis_case>/<child_case>/`

这里要注意：
- `thesis_case` 只是区分不同论文的包裹层
- 真正进入工作的始终是 `child_case`

## 如何开始
如果你要先建写作 case，可以说：

```text
读取当前层 AGENTS.md 和 README。请在 examples/<thesis_case>/<child_case>/ 下为我建立或继续一个 writing child_case，并默认使用 markdown 模式。
```

如果你已经知道这次写作要绑定哪些上游 case，可以说：

```text
读取当前层 AGENTS.md 和 README。请先扫描我指定的上游 case outputs，再为当前 writing child_case 生成章节骨架和 asset manifest。
```

如果你已经准备构建 PDF，可以说：

```text
读取当前层 AGENTS.md 和 README。请先 materialize chapters，再从 `thesis_template_source_case` 注入当前 child_case 的 my-thesis 工作副本，并尝试编译论文 PDF。
```

如果你现在只想润色，不想改文件或编译，也可以说：

```text
进入修改模式。
```
