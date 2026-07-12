# Academic Research Workflow Agents

中文名：学术研究工作流智能体框架

本仓库是付费版源码仓库，用于管理和打包两个可独立使用、也可组合使用的学术工作流 Agent 框架。

This private repository is the paid-source repository for two academic workflow agent frameworks.

## 项目是什么

`Academic Research Workflow Agents` 不是单个论文模板，也不是一次性的 ChatGPT 提示词集合。它是一套面向学术研究流程的 Agent 框架，把论文阅读、数据处理、回归分析、LaTeX 论文写作和 TeX/Beamer 学术汇报制作拆成可复用的子 agent、脚本、契约和示例。

## 两个产品

### Thesis Agent

路径：`Thesis_Agent/`

面向完整论文写作流程：

- 论文阅读与材料整理
- 数据准备与面板数据构造
- Stata 回归与结果整理
- LaTeX 论文初稿、章节整合与润色
- 提交前结构检查

适合需要把“读文献、做实证、写论文、检查提交材料”串成一个可重复流程的用户。

### Slides Agent Tex

路径：`Slides_Agent_Tex/`

面向 TeX/Beamer 学术 PPT 制作：

- Beamer 模板适配
- 学术汇报 deck 内容生成
- 图表、参考文献和素材组织
- 编译、渲染和检查

适合需要用 TeX/Beamer 做课程汇报、论文答辩、学术报告或项目展示的用户。

## 售卖方式

源码在一个私有仓库中维护，但发布和售卖时拆成三个版本包：

- `thesis`：只包含 `Thesis_Agent/`
- `slides`：只包含 `Slides_Agent_Tex/`
- `bundle`：同时包含两个 agent

这样可以保持源码维护一致，同时让用户按自己的需求购买论文写作、PPT 制作或组合包。

## 公开预览

公开介绍和 demo 在：

```text
https://github.com/academic-research-workflow-agents/agents-preview
```

公开仓库只用于说明项目能力、展示 synthetic demo 和提供申请方式，不包含完整付费版 agent。

## 打包

生成组合包：

```powershell
.\scripts\New-PaidReleasePackage.ps1 -Version 0.1.0 -Package bundle
```

生成单独论文写作包：

```powershell
.\scripts\New-PaidReleasePackage.ps1 -Version 0.1.0 -Package thesis
```

生成单独 TeX PPT 包：

```powershell
.\scripts\New-PaidReleasePackage.ps1 -Version 0.1.0 -Package slides
```

一次生成三种包：

```powershell
.\scripts\New-PaidReleasePackage.ps1 -Version 0.1.0 -Package all
```

输出文件包括 ZIP 和对应的 SHA256 校验文件。

## 隐私边界

本仓库只应保存通用框架、脚本、契约、skills 和 synthetic examples。不要提交真实论文、真实数据、机构模板、生成输出、日志、归档运行结果、API keys 或本地私人材料。

## 授权

本仓库和付费发布包不是开源项目。购买者仅获得对应版本的个人使用权。详见 `TERMS.md`。
