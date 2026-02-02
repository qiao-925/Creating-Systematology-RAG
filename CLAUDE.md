# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**Creating-Systematology-RAG** is a multi-strategy Retrieval-Augmented Generation (RAG) system built with LlamaIndex, featuring both traditional and agentic RAG modes. The system retrieves information from a knowledge base focused on systematology (系统学) and generates answers with cited sources.

**Tech Stack**: Python 3.12+, LlamaIndex, Streamlit, Chroma Cloud, DeepSeek API, HuggingFace Embeddings

---

## Common Commands

### Development Workflow
```bash
# Install dependencies and run tests (first time setup)
make

# Start the web application
make run

# One-click setup and start
make start

# Run tests
make test                    # All tests
make test-unit              # Unit tests only
make test-integration       # Integration tests only
make test-cov               # Tests with coverage report
make test-fast              # Skip slow tests

# Clean generated files
make clean
```

### Running Single Tests
```bash
# Run a specific test file
uv run --no-sync pytest tests/unit/test_chat_manager.py -v

# Run a specific test function
uv run --no-sync pytest tests/unit/test_chat_manager.py::test_query_with_session -v

# Run with logging output
uv run --no-sync pytest tests/integration/test_github_e2e.py -v -s --log-cli-level=INFO
```

### GPU Configuration (Optional)
```bash
# Manually install CUDA version of PyTorch for GPU acceleration
uv pip install --force-reinstall --index-url https://download.pytorch.org/whl/cu121 torch torchvision torchaudio

# Verify GPU availability
uv run --no-sync python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Note: After installing CUDA PyTorch, avoid running `make install` or `uv sync`
# as it will overwrite with CPU version. Use `make run` (with --no-sync) instead.
```

### Running the Application
```bash
# Start Streamlit web app (default port 8501)
make run

# Or directly with streamlit
uv run --no-sync python -m streamlit run app.py

```

---

## Architecture Overview

### Three-Layer Architecture

The codebase follows a strict three-layer architecture with **unidirectional dependencies**:

```
Frontend Layer (Presentation)
    ↓ (calls)
Business Layer (RAG Engine, Services)
    ↓ (uses)
Infrastructure Layer (Config, LLM, Embedding, Indexer, Observers)
```

**Critical Rules**:
- Frontend ONLY calls Business Layer (RAGService)
- Business Layer ONLY uses Infrastructure Layer
- NO reverse dependencies allowed
- NO cross-layer access (Frontend cannot directly access Infrastructure)

### Directory Structure

```
Creating-Systematology-RAG/
├── app.py                          # Streamlit entry point
├── frontend/                       # Frontend Layer (31 files)
│   ├── main.py                    # Main application entry
│   ├── components/                # UI components
│   │   ├── chat_display.py       # Chat message rendering
│   │   ├── chat_input_with_mode.py # Input with RAG/Chat mode
│   │   ├── config_panel/         # Configuration panel
│   │   │   ├── models.py         # AppConfig data model
│   │   │   ├── llm_presets.py    # LLM preset configurations
│   │   │   └── rag_params.py     # RAG parameter controls
│   │   ├── observability_summary.py # Query metrics display
│   │   ├── keyword_cloud.py      # Keyword visualization
│   │   └── query_handler/        # Query execution handlers
│   └── utils/                     # Frontend utilities
│       ├── state.py              # Session state management
│       └── sources.py            # Source formatting
│
├── backend/                        # Backend code
│   ├── business/                   # Business Layer (43 files)
│   │   ├── rag_engine/            # RAG Engine (49 files)
│   │   │   ├── core/
│   │   │   │   └── engine.py     # ModularQueryEngine (traditional RAG)
│   │   │   ├── agentic/
│   │   │   │   └── engine.py     # AgenticQueryEngine (agentic RAG)
│   │   │   ├── retrieval/        # Retrieval strategies
│   │   │   │   ├── factory.py    # Retriever factory
│   │   │   │   └── strategies/   # vector, bm25, hybrid, grep, multi
│   │   │   ├── reranking/        # Result reranking
│   │   │   ├── routing/          # Query routing
│   │   │   ├── processing/       # Query processing
│   │   │   └── formatting/       # Response formatting
│   │   ├── rag_api/              # RAG API
│   │   │   ├── rag_service.py    # Unified service interface
│   │   │   └── models.py         # API data models
│   │   └── chat/                 # Chat management
│   │       └── manager.py        # ChatManager
│   │
│   └── infrastructure/             # Infrastructure Layer (80+ files)
│       ├── config/                # Configuration management
│       │   ├── settings.py       # Main Config class (100+ options)
│       │   └── models.py         # Pydantic config models
│       ├── indexer/              # Vector index management
│       │   ├── core/
│       │   │   └── manager.py    # IndexManager (Chroma integration)
│       │   ├── build/            # Index building
│       │   └── utils/            # Index utilities
│       ├── data_loader/          # Data loading
│       │   ├── source/           # Data sources (GitHub, local)
│       │   ├── github_sync/      # GitHub synchronization
│       │   └── service.py        # DataImportService
│       ├── embeddings/           # Embedding models
│       │   ├── factory.py        # Embedding factory
│       │   └── local_embedding.py # Local HF embeddings
│       ├── llms/                 # LLM management
│       │   └── factory.py        # LLM factory (LiteLLM)
│       ├── observers/            # Observability
│       │   ├── llama_debug_observer.py # LlamaDebug integration
│       │   └── ragas_evaluator.py # RAGAS evaluation
│       ├── git/                  # Git operations
│       ├── initialization/       # App initialization
│       └── logger_structlog.py   # Structured logging
│
├── tests/                          # Test suite (99 files)
│   ├── fixtures/                  # Reusable test fixtures
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   └── ui/                        # UI tests
│
├── docs/                           # Documentation
│   ├── architecture.md            # Detailed architecture (778 lines)
│   └── quick-start-advanced.md    # Advanced configuration
│
├── data/                           # Data directory
│   └── github_repos/              # Cloned GitHub repositories
│
├── application.yml                 # Main configuration file
├── .env                           # Environment variables (API keys)
├── pyproject.toml                 # Project metadata
└── Makefile                       # Build automation
```

---

## Key Components & Workflows

### 1. Query Processing Flow

```
User Query
    ↓
frontend/main.py → handle_user_queries()
    ↓
RAGService.query(question, session_id)
    ↓
[Engine Selection]
    ├─ use_agentic_rag=True → AgenticQueryEngine
    │   └─ ReActAgent → Tools → Retriever → LLM
    │
    └─ use_agentic_rag=False → ModularQueryEngine
        ↓
        QueryProcessor.process() [intent understanding + rewriting]
        ↓
        create_retriever() [factory pattern]
        ↓
        Retriever.retrieve() [execute retrieval strategy]
        ↓
        [Post-processing] SimilarityCutoff + Reranker (optional)
        ↓
        LLM.generate() [generate answer]
        ↓
        ResponseFormatter.format() [format with citations]
        ↓
        RAGResponse {answer, sources, metadata}
```

### 2. Retrieval Strategies

The system supports 5 retrieval strategies (configured via `RETRIEVAL_STRATEGY`):

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `vector` | Semantic similarity search | General semantic queries |
| `bm25` | Keyword-based retrieval | Exact term matching |
| `hybrid` | Vector + BM25 + RRF fusion | Balance semantic and keyword |
| `grep` | File system text search | Code/filename queries |
| `multi` | Parallel multi-strategy | Complex queries |

**Implementation**: `backend/business/rag_engine/retrieval/factory.py` creates retrievers based on strategy type.

### 3. Index Building Flow

```
Data Source (GitHub/Local)
    ↓
DataImportService.import_from_github() / import_from_directory()
    ↓
GitRepositoryManager.clone() / pull() [if GitHub]
    ↓
GitHubSource / LocalFileSource.load() [get file list]
    ↓
DocumentParser.parse_files() [parse to LlamaDocument]
    ↓
IndexManager.build_index(documents)
    ↓
SentenceSplitter [chunk into Nodes]
    ↓
Embedding.embed_nodes() [generate vectors]
    ↓
ChromaVectorStore [store to Chroma Cloud]
    ↓
VectorStoreIndex [index ready]
```

**Key Files**:
- `backend/infrastructure/indexer/core/manager.py`: IndexManager
- `backend/infrastructure/data_loader/service.py`: DataImportService
- `backend/infrastructure/embeddings/factory.py`: Embedding creation

### 4. Configuration System

**Two-tier configuration**:
1. **YAML** (`application.yml`): Static configuration (100+ options)
2. **Environment Variables** (`.env`): Sensitive data (API keys)

**Key Configuration Areas**:
- LLM models and endpoints (`LLM_MODEL`, `DEEPSEEK_API_KEY`)
- Embedding models (`EMBEDDING_TYPE`, `EMBEDDING_MODEL`)
- Vector store (`CHROMA_CLOUD_API_KEY`, `CHROMA_CLOUD_TENANT`, `CHROMA_CLOUD_DATABASE`)
- Retrieval parameters (`RETRIEVAL_STRATEGY`, `SIMILARITY_TOP_K`, `SIMILARITY_CUTOFF`)
- Reranking (`ENABLE_RERANK`, `RERANKER_TYPE`)
- Observability (`ENABLE_LLAMA_DEBUG`, `ENABLE_RAGAS`)

**Configuration Loading**: `backend/infrastructure/config/settings.py` (Config class)

### 5. RAG Modes

**Traditional RAG** (`use_agentic_rag=False`):
- Fixed retrieval strategy
- Direct query execution
- Faster, more predictable
- Implementation: `backend/business/rag_engine/core/engine.py`

**Agentic RAG** (`use_agentic_rag=True`):
- ReActAgent-based planning
- Dynamic tool selection
- Reasoning chain output
- Implementation: `backend/business/rag_engine/agentic/engine.py`

### 6. Chat Management

**ChatManager** (`backend/business/chat/manager.py`):
- Session-based conversation (in-memory only)
- Memory buffer with token limits
- Streaming and non-streaming support
- Reasoning content preservation

**Usage**:
```python
chat_manager = ChatManager(query_engine, session_id="user123")
response = chat_manager.query("What is systematology?")
```

---

## Important Patterns & Conventions

### 1. Factory Pattern

All major components use factory functions for creation:

```python
# Retriever factory
from backend.business.rag_engine.retrieval.factory import create_retriever
retriever = create_retriever(index, strategy="vector", top_k=5)

# Reranker factory
from backend.business.rag_engine.reranking.factory import create_reranker
reranker = create_reranker(reranker_type="bge", top_n=3)

# Embedding factory
from backend.infrastructure.embeddings.factory import create_embedding
embedding = create_embedding(config)

# LLM factory
from backend.infrastructure.llms.factory import create_llm
llm = create_llm(config)
```

### 2. Dependency Injection

All components receive dependencies via constructor:

```python
# Good: Dependency injection
class RAGService:
    def __init__(self, index_manager: IndexManager, config: Config):
        self.index_manager = index_manager
        self.config = config

# Bad: Global singletons or hidden dependencies
class RAGService:
    def __init__(self):
        self.index_manager = get_global_index_manager()  # ❌ Avoid
```

### 3. Lazy Initialization

RAGService uses lazy initialization for engines:

```python
@property
def modular_engine(self) -> ModularQueryEngine:
    if self._modular_engine is None:
        self._modular_engine = self._create_modular_engine()
    return self._modular_engine
```

This avoids loading all components at startup.

### 4. Structured Logging

Always use structured logging (never `print`):

```python
from backend.infrastructure.logger_structlog import get_logger

logger = get_logger(__name__)

# Good: Structured logging with context
logger.info("query_executed", query=query, duration=duration, results=len(results))

# Bad: Print statements
print(f"Query: {query}")  # ❌ Never use print
```

### 5. Type Hints

All functions must have complete type hints:

```python
# Good: Complete type hints
def query(self, question: str, session_id: Optional[str] = None) -> RAGResponse:
    ...

# Bad: Missing type hints
def query(self, question, session_id=None):  # ❌ Missing types
    ...
```

### 6. Error Handling

Catch specific exceptions and log appropriately:

```python
# Good: Specific exception handling
try:
    result = self.retriever.retrieve(query)
except ValueError as e:
    logger.error("invalid_query", error=str(e), query=query)
    raise
except Exception as e:
    logger.exception("retrieval_failed", error=str(e))
    raise

# Bad: Bare except
try:
    result = self.retriever.retrieve(query)
except:  # ❌ Never use bare except
    pass
```

### 7. File Size Limit

**Hard limit**: Single code file must be ≤ 300 lines. If a file exceeds this, split it into smaller modules.

---

## Testing Guidelines

### Test Organization

```
tests/
├── fixtures/              # Reusable fixtures
│   ├── initialization.py  # App initialization
│   ├── llm.py            # LLM mocks
│   ├── indexer.py        # Index fixtures
│   └── embeddings.py     # Embedding fixtures
├── unit/                 # Unit tests (fast, isolated)
├── integration/          # Integration tests (slower, real components)
└── ui/                   # UI tests
```

### Writing Tests

```python
import pytest
from tests.fixtures.initialization import init_app_for_test

def test_query_execution(init_app_for_test):
    """Test query execution with mocked components."""
    config, index_manager = init_app_for_test

    # Test implementation
    result = query_engine.query("test query")

    assert result.answer is not None
    assert len(result.sources) > 0
```

### Running Tests

```bash
# All tests
make test

# Specific test file
uv run --no-sync pytest tests/unit/test_chat_manager.py -v

# With coverage
make test-cov

# Fast tests only (skip slow tests marked with @pytest.mark.slow)
make test-fast
```

---

## Configuration Reference

### Environment Variables (.env)

```bash
# Required: API Keys
DEEPSEEK_API_KEY=sk-...
OPENAI_API_KEY=sk-...  # Optional, for OpenAI models

# Required: Chroma Cloud
CHROMA_CLOUD_API_KEY=...
CHROMA_CLOUD_TENANT=...
CHROMA_CLOUD_DATABASE=...

# Optional: HuggingFace
HF_TOKEN=hf_...  # For private models
```

### Key YAML Configuration (application.yml)

```yaml
# LLM Configuration
llm:
  model: "deepseek-reasoner"  # or "deepseek-chat", "gpt-4", etc.
  temperature: 0.5
  max_tokens: 4096

# Embedding Configuration
embedding:
  type: "local"  # or "api"
  model: "BAAI/bge-small-zh-v1.5"
  device: "auto"  # "cuda", "cpu", or "auto"

# Retrieval Configuration
retrieval:
  strategy: "vector"  # "vector", "bm25", "hybrid", "grep", "multi"
  top_k: 5
  similarity_cutoff: 0.3
  enable_auto_routing: false

# Reranking Configuration
reranking:
  enable: true
  type: "bge"  # or "sentence_transformer"
  top_n: 3

# Observability
observability:
  enable_llama_debug: true
  enable_ragas: false
```

---

## Common Development Tasks

### Adding a New Retrieval Strategy

1. Create strategy implementation in `backend/business/rag_engine/retrieval/strategies/`
2. Register in `create_retriever()` factory (`retrieval/factory.py`)
3. Add configuration option in `application.yml`
4. Add tests in `tests/unit/test_retrieval_strategies.py`

### Adding a New LLM Model

1. Add model configuration in `application.yml` under `llm.models`
2. Update `backend/infrastructure/llms/factory.py` if needed (LiteLLM handles most models)
3. Test with `uv run --no-sync python -c "from backend.infrastructure.llms.factory import create_llm; ..."`

### Adding a New Frontend Component

1. Create component in `frontend/components/`
2. Import and use in `frontend/main.py`
3. Follow Streamlit native component patterns (prefer `st.dialog()`, `st.chat_input()`, etc.)
4. Ensure Light/Dark theme compatibility

### Modifying Configuration

1. Update `application.yml` for static config
2. Update `.env` for sensitive data
3. Update `backend/infrastructure/config/models.py` for new Pydantic fields
4. Update `backend/infrastructure/config/settings.py` property mapping if needed

---

## Troubleshooting

### GPU Not Detected

```bash
# Check CUDA availability
uv run --no-sync python -c "import torch; print(torch.cuda.is_available())"

# Reinstall CUDA PyTorch
uv pip install --force-reinstall --index-url https://download.pytorch.org/whl/cu121 torch torchvision torchaudio
```

### Chroma Cloud Connection Issues

- Verify environment variables in `.env`
- Check network connectivity
- Ensure API key, tenant, and database are correct

### Import Errors

```bash
# Sync dependencies
uv sync

# Or install specific package
uv pip install <package-name>
```

### Test Failures

```bash
# Run with verbose output
uv run --no-sync pytest tests/unit/test_file.py -v -s

# Run with logging
uv run --no-sync pytest tests/unit/test_file.py -v --log-cli-level=DEBUG
```

---

## Additional Resources

- **Architecture Documentation**: `docs/architecture.md` (778 lines, comprehensive)
- **Advanced Configuration**: `docs/quick-start-advanced.md`
- **Aha Moments**: `aha-moments/` (design insights and technical decisions)
- **Task Logs**: `agent-task-log/` (AI agent task records)
- **Prompts**: `prompts/` (centralized prompt templates)

---

**Last Updated**: 2026-01-31
