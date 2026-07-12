# 发布与交付清单

本文件用于从私有源码仓库生成付费版本包。

## 发布前检查

1. 运行隐私扫描，确认没有 `.env`、API key、日志、PDF、真实数据、私人论文、机构模板或本地绝对路径。
2. 运行轻量检查：

   ```powershell
   npm run check-source -- --case Subagent_deck/examples/example_slide/example_beamer_deck
   python -m pytest Thesis_Agent\Subagent_process_data\skills\Codex-panel_builder_for_regression\tests
   ```

3. 生成三种版本包：

   ```powershell
   .\scripts\New-PaidReleasePackage.ps1 -Version 0.1.0 -Package all
   ```

4. 抽查 ZIP 内容：
   - thesis 包只包含 `Thesis_Agent/` 和根说明文件；
   - slides 包只包含 `Slides_Agent_Tex/` 和根说明文件；
   - bundle 包包含两个 agent；
   - 三个包都包含 `README.md`、`TERMS.md`、`VERSION.txt`；
   - 三个包都不包含输出、缓存、日志、PDF、真实数据和私密文件。

5. 上传 ZIP 和 `.sha256.txt` 到交付用网盘或按订单开通私有仓库访问。
6. 更新 public preview 仓库的版本记录和申请说明。

## 邮件申请处理

公开申请邮箱：

```text
qinnrk@163.com
```

邮件标题：

```text
Academic Agents 访问申请 - GitHub用户名
```

邮件中应包含：

- 需要的包：`Thesis Agent` / `Slides Agent Tex` / `Bundle`
- 使用场景
- GitHub username
- 是否需要 private repo 访问或 ZIP 交付

## 交付模板

感谢申请 Academic Research Workflow Agents v0.1.0。

开通/交付内容：

版本包：

下载链接或 private repo：

SHA256：

本版本为个人使用授权，可用于个人学习、研究、论文写作和学术展示准备；请勿转卖、公开分享、上传到公开仓库或转发给他人。该订单交付当前版本，不默认包含无限后续更新。
