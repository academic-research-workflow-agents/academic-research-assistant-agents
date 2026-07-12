# Release Checklist

Use this checklist before uploading a paid ZIP package to a cloud drive.

1. Run privacy scans for secrets, logs, PDFs, real data, and local private materials.
2. Run the lightweight validation commands documented in `README.md`.
3. Build the paid release package:

   ```powershell
   .\scripts\New-PaidReleasePackage.ps1 -Version 0.1.0
   ```

4. Upload the ZIP and `.sha256.txt` file to the selected cloud drive.
5. Update the public preview repository changelog with the new version number and short release notes.
6. Send buyers the download link, extraction code, SHA256, version number, and installation notes after payment.

## Xianyu Delivery Template

感谢购买 Academic Research Workflow Agents v0.1.0。

下载链接：

提取码：

SHA256：

本版本为个人使用授权。可以用于个人学习、研究、论文写作和学术展示准备；请勿转卖、公开分享、上传到公开仓库或转发给他人。该订单交付当前版本，不默认包含无限后续更新。
