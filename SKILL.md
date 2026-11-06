---
name: gif-sticker-workshop
description: Use when planning original character-action GIF stickers, checking a claimed animated GIF, or preparing a reviewable sticker workflow before platform submission rules are verified.
---

# 原创动作 GIF 工作坊

把角色一致性、真实动作和文件核验分开处理。技术通过不是视觉验收，也不是平台批准。

## 先确定边界

- 保留用户已确认的角色和动作，只用自有或明确获授权素材。不要模仿第三方角色、搬运参考仓库素材。
- 先列出角色锚点和 1–2 个试做动作，确认后才扩批。每个动作有准备、执行、收尾与循环衔接，不靠整张静态图摇摆、缩放或旋转冒充原生动作。
- 当前环境的原生图片工具及其调用规则优先。只传工具实际支持的参数，不凭产品名称推测模型 ID 或 GIF 能力。工具不支持 GIF 时停在规划/手工生成指引，明确阻塞；不要静默改成 sprite sheet 合成或换供应商。
- 用户明确禁止生成、收费或联网时，仅处理本地文件和规划。本 skill 不带 API 客户端，不读取密钥，不安装依赖，不自动发布。

## 工作流程

1. 读 [手工教程](references/workflow.md)，写清外形锚点、禁止变化、动作节拍、输出证据和授权状态。可从 [8 个海獭动作规划](manifests/otter-actions.planning.json) 开始；这些不是已生成作品。
2. 获得生成授权后，先做单个原生 GIF 试样。要求主体关节和表情随动作变化，而非后期整图形变。若用户指定 GPT Image 2.6，先读 [官方能力与权限边界](references/openai-gif.md)。产品支持不等于当前工具或账户有权限。
3. API 路径必须另外确认用户预算上限、调用次数和所选模型的当前 GIF preview 权限；没有这三项，不发请求。手工路径也需遵守用户对额度与成本的限制。模型身份只能来自可核对的生成记录，不能从 GIF 像素推断。
4. 保存原始下载文件，不改名冒充格式，不覆盖源文件。在本 skill 目录内运行：

   ```sh
   python3 -B scripts/audit_gif.py audit input.gif --out output/review-01
   ```

   `--out` 必须是新目录。检查 `audit.json`、`contact-sheet.png`、`frames/` 和 `preview.html`。返回码 0 只代表技术检查通过；1 是文件检查失败；2 是输入/输出或命令错误。
5. 逐帧检查角色身份、肢体、裁切与残影，再正常播放核对节奏及首尾衔接。没有播放权限就保留“播放待审”，不勾选通过。distinct 帧数量不能证明 AI 原生生成，也不能证明动作自然。
6. 只有试样获接受才扩批；每个文件单独核验并记录验收。失败时停止扩批、说明缺陷，生成重试需仍在授权和预算内。
7. 微信投稿前必须补齐当前官方规范 profile、版本日期、素材类型、审核要求及人工签核。仓库的 [pending profile](profiles/wechat.pending.json) 不是规则；本 MVP 不执行平台合规判断，始终保持 `submission_ready=false`。不要宣称透明 GIF 能力或未经核实的尺寸/体积限制。

## 交付口径

报告实际格式、帧数、distinct 帧、loop、时长、尺寸、字节数和 SHA256；把“计划 / 已生成 / 技术通过 / 人工审查 / 用户接受 / 平台待验证”分别列出。参考样例证明真多帧 GIF，不证明模型版本。具体字段和限制见 [README](README.md)。
