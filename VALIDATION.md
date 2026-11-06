# MVP 验证与交接

核对日期：2026-11-06。本文记录代码与素材验证，不将源码发布等同于模型实测或微信审核。离线工具没有网络请求、密钥读取或计费调用。维护账号为 BNB-LG。

## 自动验证

```sh
python3 -B -m unittest discover -s tests -v
node tests/check_preview.js
ruby tests/check_skill.rb
```

- 初始 14 项 CLI 测试在未实现脚本时全部失败，完成实现后通过。
- 最终 20 项 unittest 覆盖假 GIF、单帧、真实多帧、重复解码帧、损坏/截断、缺失输入、零时长、有限/缺失 loop、真实格式识别、资源限额、源文件不变、拒绝覆盖、HTML 转义及字节一致性。
- 仓库检查覆盖 JSON 可解析、8 个动作仍为规划、API 参数例子禁止执行、平台 profile 不可认证、Markdown 本地链接、公开文件敏感标记扫描。扫描排除 `.git/` 与已 gitignore 的 `__pycache__/`；Python 缓存可能带本机编译路径，不应使用强制添加发布它们。敏感扫描是启发式检测，不替代发布前人工检查。
- Node 检查前后帧、首尾索引、滑块、定时推进和暂停。它是 DOM stub，不是浏览器渲染/播放验收。主代理尝试本地 HTML 时遇到浏览器安全拒绝；未改用 localhost 或其他路径绕过，浏览器播放继续标为未验收。
- 系统 `quick_validate.py` 因缺少 PyYAML 未运行成功；未安装依赖。`tests/check_skill.rb` 使用真实 YAML 解析器验证 frontmatter 与字段，不能声称官方 validator 已通过。
- 本轮无可用子代理入口，未完成独立 agent 的技能压力测试。对“静态图冒充动作 / 无预算调用 API / 从样例推断 2.6 / 无 profile 宣称投稿包”的处理规则已写入 skill，但不将文档阅读视为 agent 行为验证。

## 自有样例

执行：`python3 -B scripts/audit_gif.py audit examples/otter-wave-gif-test.gif --out examples/qa`

实际结果：GIF89a，363 × 363，12 帧，12 distinct，每帧 200 ms，总时长 2400 ms，523723 字节，loop=0，无限循环。SHA256：

```text
661dbf829292b61849211d3b97710c24834638dc595bd017177b5c13acf9716f
```

已用 `shasum -a 256` 比对授权源文件与仓库副本，两者哈希均与上述值相同。核验产物见 `examples/qa/`。联系图已由助手静态检查：12 个画面可读，手爪有不同姿态，不是 12 份同一静态图；这不证明生成模型，不代替原尺寸逐帧形体结构审查、正常播放及首尾衔接验收。整体视觉接受状态仍待定。

## 保留的验证缺口

1. 浏览器播放未验收：本地文件协议遭安全拒绝，主代理决定本轮不再做 HTML 浏览器验收。静态结构与离线脚本结果不能替代这项，也不改用其他入口绕过。
2. 主代理已独立复跑 20 项 Python 测试、Node 交互逻辑测试和 Ruby YAML 检查，均通过；已读回代码与权利说明。此验证不包含真实浏览器播放。
3. 若实际制作新表情，先确认生成入口、预算和必要权限；如声明微信投稿包，另补经核对的官方 profile 与完整人工验收。

## 全部新增文件

```text
.gitignore
ACKNOWLEDGEMENTS.md
DEPENDENCIES.md
LICENSE
README.md
SKILL.md
VALIDATION.md
requirements.txt
scripts/audit_gif.py
tests/test_audit.py
tests/test_repository.py
tests/check_preview.js
tests/check_skill.rb
references/workflow.md
references/openai-gif.md
manifests/otter-actions.planning.json
profiles/wechat.pending.json
examples/api-request.plan.json
examples/provenance.json
examples/otter-wave-gif-test.gif
examples/qa/audit.json
examples/qa/contact-sheet.png
examples/qa/preview.html
examples/qa/frames/frame-000.png
examples/qa/frames/frame-001.png
examples/qa/frames/frame-002.png
examples/qa/frames/frame-003.png
examples/qa/frames/frame-004.png
examples/qa/frames/frame-005.png
examples/qa/frames/frame-006.png
examples/qa/frames/frame-007.png
examples/qa/frames/frame-008.png
examples/qa/frames/frame-009.png
examples/qa/frames/frame-010.png
examples/qa/frames/frame-011.png
```

另有本地 `.git/` 元数据，不作为作品文件。测试临时几何夹具在仓库内创建并由 unittest 清理，没有混入样例成品目录。
