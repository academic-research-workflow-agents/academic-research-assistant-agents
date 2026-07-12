# Subagent_process_data Agent Contract

## Role
`Subagent_process_data` 是论文实证资产构建层。

这一层负责：
- 数据标准化
- provider 驱动的桥接、清洗与拼接
- 机制变量、回归前面板与中间资产构建
- 形成可交给回归层消费的 case-local 数据资产

这一层不负责：
- 直接接管回归会话
- 把某个具体 thesis case 当作顶层默认工作流

## Top-Level Minimal Structure
顶层只保留框架层：

- `AGENTS.md`
- `README.md`
- `contracts/`
- `providers/`
- `scripts/`
- `skills/`
- `examples/`

顶层不保留：
- 顶层 `outputs/`
- 具体 provider catalog 的运行态交付
- 具体 thesis case 默认值
- 直接指向具体 case 输出的稳定运行接口

## Unified Case Architecture
真实 thesis 数据处理工作统一放在：

- `examples/<thesis_case>/<child_case>/`

层级规则：
- `thesis_case` 只是区分不同论文的包裹层
- `child_case` 才是实际工作层
- 所有请求、脚本、资产、输出都只能放在 `child_case` 内

禁止把 `examples/<thesis_case>/` 当作可直接运行的 case。
禁止再新增 flat example case 作为真实 thesis 生产 case。

## Child-Case Skeleton
每个 data-process `child_case` 应收敛到以下最小骨架：

- `AGENTS.md`
- `README.md`
- `assets/`
- `requests/`
- `scripts/`
- `outputs/`

需要额外配置时，可以在 case 内补：
- `config/`

## Provider Framework Rule
`providers/` 是顶层 capability layer，只保留：
- 通用 provider framework
- 通用 loader

具体 provider catalog、demo provider、具体 case 输出暴露合同、具体 case handoff 不应长期停留在顶层 `providers/`。
它们应回到对应 `child_case` 的 `outputs/specs/`。

## Script Contract
顶层 `scripts/` 只允许保留通用框架脚本。

允许：
- 通用 builder
- 通用路径解析
- 通用 schema 校验

不允许：
- 绑定某个具体 thesis case 的 runner
- 硬编码某个具体 thesis case 名称作为默认入口

## Engineering Sources Of Truth
这一层的通用工程来源优先级为：
- `contracts/build_spec.schema.json`
- `providers/registry.py`
- `providers/base.py`

## Case-Local Output Rule
所有构建产物必须写回 active `child_case` 的 `outputs/`。

推荐骨架：
- `outputs/regression_panels/`
- `outputs/regression_panel_reports/`
- `outputs/regression_panel_exceptions/`
- `outputs/regression_panel_manifest/`
- `outputs/specs/`
- `outputs/runtime/`

不要把 case-specific 中间结果、日志或 handoff 写到 subagent 顶层。

## Template Rule
顶层模板只能作为只读模板源。
AI 在具体使用时必须先复制到 active `child_case`，再在 case 内应用。
未经用户明确要求，不得直接修改顶层模板。

## Archive And Legacy Rule
- `archive` 只表示冻结历史快照，推荐放在 `outputs/archive/`
- `legacy` 只表示旧逻辑或旧规格，推荐放在 `scripts/legacy/` 或 `outputs/specs/legacy/`

## Boundaries
这一层可以：
- 解析 build specs
- 标准化与拼接上游资产
- 生成 case-local regression-ready panels 或前置机制资产
- 形成可交给回归层消费的 case-local metadata

这一层不能：
- act as the regression session layer
- 让回归层理解 provider 内部细节
- 把某个私有 thesis case 说成顶层默认入口
