# FAQ

## 这是开源项目吗？

不是。public preview 用于展示能力边界、synthetic 契约记录和极小演示；完整 private 产品属于专有材料。

## 公开版本能运行什么？

公开版本可以检查一个 synthetic presentation manifest，并将配套 Beamer 源码渲染为 PDF 或 PNG。它不包含完整 agent、skills 或 private 工作流。

## 为什么演示需要来源 manifest？

manifest 把每个 slide 与已登记材料连接起来，并声明 `verbatim`、`extract`、`compress` 或 `layout` 变换。来源缺失或 frame 未登记时，检查必须失败。

## 数据与技术结果会自动给出研究解释吗？

不会。相关能力只保留数据资产、模型设定、数值、表图、诊断和运行元数据。研究主张、解释与结论由使用者本人负责。

## 长文档排版会改变正文吗？

不会。排版能力只处理 manifest 中明确登记的用户源文件，并记录哈希和转换方式。

## 如何获得完整 private 产品？

发送邮件到 `qinnrk@163.com`，提供 GitHub username、使用场景和希望的交付方式。详情见 [BUY.md](BUY.md)。

## 可以分享给同学或团队吗？

个人授权不允许转卖、公开分享、上传或二次分发。团队、课程或机构使用需要单独确认授权。
