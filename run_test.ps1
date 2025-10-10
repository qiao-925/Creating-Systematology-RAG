$env:Path = "D:\git repo\Creating-Systematology-RAG\.venv\Scripts;" + $env:Path
python -m pytest tests/unit/test_chat_manager.py::TestChatManager::test_start_session -v --tb=short 2>&1 | Tee-Object -FilePath test_output.txt

