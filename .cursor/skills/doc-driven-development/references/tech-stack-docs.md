## 技术栈官方文档映射（用于 MCP / Firecrawl）

| 类别 | 包名 | 版本下限 | 官方文档 URL | 首选获取方式 |
| --- | --- | --- | --- | --- |
| RAG 基础 | llama-index | \>=0.14.3 | https://docs.llamaindex.ai/ | Context7（若不可用用 Firecrawl 首页） |
|  | llama-index-llms-openai | \>=0.2.0 | 同上 | Context7 |
|  | llama-index-llms-deepseek | \>=0.2.0 | 同上 | Context7 |
|  | llama-index-llms-litellm | \>=0.6.0 | 同上 | Context7 |
|  | llama-index-embeddings-huggingface | \>=0.3.0 | 同上 | Context7 |
|  | llama-index-vector-stores-chroma | \>=0.2.0 | 同上 | Context7 |
|  | llama-index-readers-file | \>=0.2.0 | 同上 | Context7 |
|  | llama-index-readers-web | \>=0.2.0 | 同上 | Context7 |
| 前端 | streamlit | \>=1.50.0 | https://docs.streamlit.io/ | Context7；Firecrawl 备用 URL: https://docs.streamlit.io/library/api-reference |
|  | streamlit-iframe-event | \>=0.0.9 | https://pypi.org/project/streamlit-iframe-event/ | Firecrawl（PyPI 页） |
| 向量库 | chromadb | \>=0.5.0 | https://docs.trychroma.com/ | Context7；Firecrawl 备用 URL: https://docs.trychroma.com/usage-guide |
| API | fastapi | \>=0.115.0 | https://fastapi.tiangolo.com/ | Context7；Firecrawl 备用 URL: https://fastapi.tiangolo.com/tutorial/ |
|  | uvicorn | \>=0.30.0 | https://www.uvicorn.org/ | Context7；Firecrawl 备用 URL: https://www.uvicorn.org/settings/ |
| LLM/推理 | openai | \>=1.12.0 | https://platform.openai.com/docs | Context7 |
| 工具 | python-dotenv | \>=1.0.0 | https://pypi.org/project/python-dotenv/ | Firecrawl（PyPI 页） |
|  | pyyaml | \>=6.0.0 | https://pyyaml.org/wiki/PyYAMLDocumentation | Firecrawl |
|  | tqdm | \>=4.66.0 | https://tqdm.github.io/ | Firecrawl |
|  | structlog | \>=24.1.0 | https://www.structlog.org/en/stable/ | Firecrawl |
|  | requests | \>=2.31.0 | https://requests.readthedocs.io/ | Context7 |
|  | pydantic-settings | \>=2.0.0 | https://docs.pydantic.dev/latest/concepts/pydantic_settings/ | Context7 |
| 认证 | python-jose[cryptography] | \>=3.3.0 | https://python-jose.readthedocs.io/ | Firecrawl |
|  | python-multipart | \>=0.0.9 | https://andrew-d.github.io/python-multipart/ | Firecrawl |
|  | passlib[bcrypt] | \>=1.7.4 | https://passlib.readthedocs.io/ | Firecrawl |
| 其他 | huggingface-hub | \>=0.20.0 | https://huggingface.co/docs/hub | Context7 |
|  | pydantic | （见项目锁定） | https://docs.pydantic.dev/ | Context7 |
| 测试 | pytest / pytest-cov / pytest-mock | 见 pyproject | https://docs.pytest.org/ | Context7 |

### Firecrawl 抓取推荐（必要时）
- LlamaIndex: https://docs.llamaindex.ai/ （首页）
- Streamlit API 参考: https://docs.streamlit.io/library/api-reference
- FastAPI 教程索引: https://fastapi.tiangolo.com/tutorial/
- Chroma 使用指南: https://docs.trychroma.com/usage-guide
- Uvicorn 设置: https://www.uvicorn.org/settings/
- 其余包若 Context7 不可用时，优先抓对应官方 docs 或 PyPI 页。
