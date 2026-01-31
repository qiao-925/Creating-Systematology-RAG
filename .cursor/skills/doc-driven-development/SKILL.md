---
name: doc-driven-development
description: 文档驱动开发流程；在生成代码或修复 bug 前，优先查阅官方文档/示例以保证实现正确性。
---

# 文档驱动开发规则

> 在生成代码或修复 bug 时，先看官方文档与示例，再动手实现。

---

## ✅ 强制要求
- 在落地新功能、接第三方库 API、或排查 API 报错时，先查官方文档。
- 遇到 `AttributeError` / `TypeError` / 版本变更不确定时，必须验证 API 定义与示例。
- 对项目自带封装的内部 API，可酌情跳过。

## Agent 执行步骤
1) 停止基于猜测的尝试，明确要查的 API/模块名称和版本。
2) 优先使用 `use context7` 抓取官方文档；若 MCP 不可用，改用 Firecrawl 抓取。
3) 依据文档的参数、返回值和示例实现或修复代码。

## 提问/抓取指引
- 在 Cursor 提问时添加：`use context7`，并指明要查的包与页面（如 “Streamlit file_uploader”）。
- 若 Context7 报错或无结果：调用 `firecrawl_scrape <URL>` 抓取表中推荐的官方文档 URL。
- 需要的主要文档 URL 与首选抓取方式参见 `references/tech-stack-docs.md`。

## 参考资料
- `references/when-to-consult.md` - 何时查阅文档
- `references/api-verification.md` - API 校验流程
- `references/tech-stack-docs.md` - 项目技术栈官方文档映射；提问/写代码前先 `use context7` 抓取，若 MCP 不可用按表中 Firecrawl 备用 URL 抓取
