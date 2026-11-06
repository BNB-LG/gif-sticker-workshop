# 外部依赖与许可清单

核对日期：2026-11-06。仓库只分发原创代码、文档、自有示例及其核验产物；没有 vendoring、没有安装或打包下列运行时/库。这里记录直接依赖和本次验证工具，不是操作系统或所有传递依赖的完整 SBOM。

| 项目 | 用途 / 本次版本 | 许可与核对来源 | 是否必需 |
| --- | --- | --- | --- |
| Python | CLI 与 unittest，3.14.3；代码目标 3.10+ | PSF License Version 2；[官方许可](https://docs.python.org/3/license.html) 另列历史及所含组件许可 | 是，运行时 |
| Pillow | GIF 解码、逐帧 PNG 和联系图，12.1.1 | **MIT-CMU**；本机包 metadata 的 `License-Expression` 与 [12.1.1 LICENSE](https://github.com/python-pillow/Pillow/blob/12.1.1/LICENSE) 一致 | 是，唯一第三方 Python 依赖 |
| Node.js | HTML 控件离线 DOM stub 测试，22.23.1 | Node.js 本体 MIT，附属组件各自许可；[官方 LICENSE](https://github.com/nodejs/node/blob/main/LICENSE) | 否，仅 `tests/check_preview.js` |
| Ruby | YAML 校验回退，2.6.10 | Ruby License 或 BSD-2-Clause；[官方许可](https://www.ruby-lang.org/en/about/license.txt) | 否，仅 `tests/check_skill.rb` |
| Psych | 上述 Ruby 自带 YAML 解析器，3.1.0 | MIT；本机 gem metadata 与 [官方 LICENSE](https://github.com/ruby/psych/blob/master/LICENSE) | 否，随可选 YAML 检查使用 |

`requirements.txt` 固定本次实际验证的 Pillow 12.1.1，仅声明依赖，不自动安装。若换版本，应重新跑测试并核对那个版本的许可。Pillow 安装包可能包含其他编解码库，其完整声明随对应发行包 LICENSE 提供；本仓库没有重新分发这些二进制，因此不把所有组件都误标为 MIT-CMU。

官方 skill quick validator 依赖 PyYAML，本机未安装，执行时返回 `ModuleNotFoundError`。没有为了它安装新依赖；仓库改用已有 Ruby/Psych 做 frontmatter 检查。PyYAML 不是本项目的运行依赖，也未被分发。

## 非代码来源

- 参考工作流仓库 `WoYun520/pixel-gif-sticker-pack` 的原始 LICENSE 为 MIT；未复用其代码或素材，见 [参考说明](ACKNOWLEDGEMENTS.md)。
- OpenAI 官方页面只是能力核对来源，没有复制 SDK 或文档正文到代码中。未来调用服务仍受对应账户权限和服务条款约束，本项目的 MIT 不授予服务访问权。
- 自有示例来源与授权范围见 [provenance.json](examples/provenance.json)，不把 AI 样例的模型身份、独占版权或平台审核结果混同为代码许可。

主代理后续公开仓库时，应保留本项目 LICENSE、来源说明和此清单；如果以后打包运行时、字体、图片或第三方库，再补齐其对应分发声明。
