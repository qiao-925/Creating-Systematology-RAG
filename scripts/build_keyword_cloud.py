"""
离线构建词云数据：仅解析目录下 PDF 的标题，输出 keyword_cloud.json 与解析过的文件名列表。

用法：
  uv run python scripts/build_keyword_cloud.py [目录路径]
  不传路径时默认使用同级目录 Creating-Systematology（与计划中分析目录一致）。
"""

import json
import sys
from pathlib import Path

# 项目根
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.business.rag_engine.processing.keyword_extractor import (
    extract_pdf_titles,
    build_keywords_from_titles,
)

# 计划约定：默认分析目录为 .../Creating-Systematology
DEFAULT_INPUT_DIR = ROOT.parent / "Creating-Systematology"


def _default_input_dir() -> Path:
    """默认分析目录：同级 Creating-Systematology；不存在则退回 data/github_repos 下第一个含 PDF 的仓库。"""
    if DEFAULT_INPUT_DIR.is_dir() and any(DEFAULT_INPUT_DIR.rglob("*.pdf")):
        return DEFAULT_INPUT_DIR
    repos = ROOT / "data" / "github_repos"
    if not repos.is_dir():
        return ROOT / "data"
    for org in repos.iterdir():
        if not org.is_dir():
            continue
        for repo in org.iterdir():
            if not repo.is_dir():
                continue
            if any(repo.rglob("*.pdf")):
                return repo
    return ROOT / "data"


def main() -> None:
    input_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else _default_input_dir()
    if not input_dir.is_dir():
        print(f"目录不存在: {input_dir}", file=sys.stderr)
        sys.exit(1)

    title_tuples = extract_pdf_titles(input_dir)
    parsed_filenames = [name for _, name in title_tuples]
    keywords = build_keywords_from_titles(title_tuples)

    out_dir = ROOT / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    cloud_path = out_dir / "keyword_cloud.json"
    files_path = out_dir / "keyword_cloud_parsed_files.json"

    with open(cloud_path, "w", encoding="utf-8") as f:
        json.dump(keywords, f, ensure_ascii=False, indent=2)
    with open(files_path, "w", encoding="utf-8") as f:
        json.dump(parsed_filenames, f, ensure_ascii=False, indent=2)

    print(f"已写入: {cloud_path} ({len(keywords)} 个词)")
    print(f"已写入: {files_path} ({len(parsed_filenames)} 个 PDF)")


if __name__ == "__main__":
    main()
