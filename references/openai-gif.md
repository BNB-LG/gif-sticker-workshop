# OpenAI GIF 能力记录

核对日期：2026-11-06。这里只记录公开文档，不代表当前账户、原生工具或 API 项目已获权限。

| 来源 | 本次核对内容 |
| --- | --- |
| [Images 2.6 发布说明](https://openai.com/index/introducing-images-2-6/) | 发布日期 2026-11-04，介绍 GIF 能力与 Flare / Sunburst |
| [Image generation guide](https://developers.openai.com/api/docs/guides/image-generation) | generation/edit 端点可请求 GIF；参考静态图走 edit；返回动画字节用 `b64_json` 保存 |
| [Images generate API](https://developers.openai.com/api/reference/resources/images/methods/generate) | 明列 `gpt-image-2.6-flare`、`gpt-image-2.6-sunburst`；GIF 需要所选模型的 preview 权限 |

已核对的请求字段：`output_format: "gif"`、`frame_count` 2–16、默认 9；guide 记录 `frame_duration_ms` 20–2000、默认 200，并按 10 ms 对齐。尺寸与总像素预算依模型当前限制，MVP 参数样例用 `size: "auto"`。不将这些接口限制当成微信规则。[Guide](https://developers.openai.com/api/docs/guides/image-generation)

guide 与 reference 对时长上界的描述层次不同：前者列请求推荐范围，后者还描述编码延迟上限。本教程不利用编码上限绕过请求范围；样例固定 200 ms。GIF 不支持 streaming、partial images、自定义 output compression；reference 也排除 masks。透明背景说明指向 PNG/WebP，因此本项目**不声称已验证透明 GIF**。[API Reference](https://developers.openai.com/api/reference/resources/images/methods/generate)

## 调用前必须分别确认

1. 当前原生工具明确支持所需操作，其 schema 允许所用参数。产品发布了能力，不表示每个工具入口都已暴露该参数。
2. 用户授权生成；如走 API，另有明确预算上限、次数及所选模型当前 GIF preview 权限。未获权限不尝试收费探测，也不改用其他付费入口。
3. 用当前官方文档重新核对字段、限制和定价。权限错误、额度错误或响应不明时停止并报告，不盲目重试。

`examples/api-request.plan.json` 仅是不会执行的 JSON 参数计划，不提供 curl、客户端或令牌配置。未来若增加客户端，必须默认 dry-run，且将实际付费调用与再次确认隔离。当前优先使用经授权的手工生成与本地 audit。

## 哪些证据还没有

本次没有调用图像工具、没有发 API 请求、没有验证任何账户的 preview 权限。既有 ChatGPT 示例的生成界面未显示模型 ID；我们只能重新验证其 GIF 文件本身，不能借它给 2.6 生成链路背书。
