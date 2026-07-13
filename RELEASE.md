# 发布与交付清单

## 发布前检查

1. 运行术语与能力边界检查：

   ```powershell
   npm run check:terminology
   ```

2. 运行 public preview 测试并确认 sibling preview 与唯一内容源一致：

   ```powershell
   npm run test:preview
   npm run preview:check
   ```

3. 运行 Python、数据和 presentation 测试。
4. 确认仓库没有 `.env`、API key、日志、PDF、真实数据、私人研究材料、机构模板或绝对路径。
5. 生成单一 private 版本包：

   ```powershell
   npm run release:private -- -Version 0.2.0
   ```

6. 抽查 ZIP：根级说明与七个 subagent 必须存在；public preview 源、同步工具、`outputs/`、缓存、日志、PDF、私有材料和旧产品目录不得出现。
7. 校验 `.sha256.txt` 后再交付。

## Public Preview 同步

`distribution/public-preview/.public-preview-allowlist.json` 是公开文件清单。同步命令会验证：

- private 与 preview 的版本号一致；
- 目标 remote 是 `agents-preview`；
- 执行同步前目标没有 tracked 修改；
- allowlist 文件没有符号链接、路径越界或缺失；
- `.preview-sync-manifest.json` 的逐文件哈希和聚合哈希一致。

每次 private 正式发布前，先运行 `npm run preview:sync` 更新公开仓库，审阅并提交 preview
仓库的受控改动，再运行 `npm run preview:check`。preview 仓库中不在上一份同步 manifest 内的
未跟踪文件不属于同步器管理范围。

## 交付模板

感谢申请 Academic Research Assistant AI Agents。

版本：

下载链接或 private repo：

SHA256：

本版本为个人使用授权，可用于学习、研究辅助、数据分析、用户原文排版和学术演示准备；请勿转卖、公开分享或转发给他人。
