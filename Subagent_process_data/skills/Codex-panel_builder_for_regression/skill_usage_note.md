# Panel Builder

这是一个通用的 panel builder 目录，用来根据构建说明生成回归面板或面板集合。

它不是具体课题的默认入口。真实课题请优先进入对应的 `../../examples/<research_case>/<child_case>/`。

## 推荐入口
优先使用上层命令：

```powershell
python ../../../scripts/build_regression_panels.py --spec-file <spec.json>
```

## 输入类型
这里通常接收的是面板构建说明文件，例如一个 `spec.json`，而不是随意的文字描述。

## 去哪里找具体课题
- 真实 research work：`../../examples/<research_case>/<child_case>/`
- 空白骨架示例：`../../examples/_empty_research_case/_empty_child_case/`
