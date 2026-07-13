# Subagent_regress_stata

这里是 Stata 实证执行与结构化结果层。

## 进入条件

Root 已路由到 `empirical_analysis`，并且 `Subagent_process_data` 已提供可消费的数据资产，或用户已指定现有 regression child case。

## 允许输出

- baseline、follow-up 和稳健性设定
- `.do` 文件、依赖记录和运行状态
- 系数、标准误、置信区间、样本量及诊断量
- 表、图、排序、manifest 和技术摘要

这一层不把数值转成研究主张、结果解释、发现或结论。

真实工作目录：

```text
examples/<research_case>/<child_case>/
```

如果尚无分析面板，先返回 `../Subagent_process_data/`。
