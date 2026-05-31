#!/usr/bin/env python3
"""Check environment variables before/after importing backend."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    print("\n=== Before importing backend ===")
    print(f"HF_ENDPOINT: {os.getenv('HF_ENDPOINT', 'Not set')}")
    print(f"HUGGINGFACE_HUB_ENDPOINT: {os.getenv('HUGGINGFACE_HUB_ENDPOINT', 'Not set')}")

    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

    # Import backend to trigger __init__ environment setup
    import backend  # noqa: F401

    print("\n=== After importing backend ===")
    print(f"HF_ENDPOINT: {os.getenv('HF_ENDPOINT', 'Not set')}")
    print(f"HUGGINGFACE_HUB_ENDPOINT: {os.getenv('HUGGINGFACE_HUB_ENDPOINT', 'Not set')}")
    print(f"SENTENCE_TRANSFORMERS_HOME: {os.getenv('SENTENCE_TRANSFORMERS_HOME', 'Not set')}")
    print(f"HF_HUB_OFFLINE: {os.getenv('HF_HUB_OFFLINE', 'Not set')}")
    print(f"TRANSFORMERS_OFFLINE: {os.getenv('TRANSFORMERS_OFFLINE', 'Not set')}")

    print("\n=== Config values ===")
    from backend.infrastructure.config import config
    print(f"config.HF_ENDPOINT: {config.HF_ENDPOINT}")
    print(f"config.HF_OFFLINE_MODE: {config.HF_OFFLINE_MODE}")

    print("\nOK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
