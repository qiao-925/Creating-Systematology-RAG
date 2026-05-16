"""Pre-download sentence-transformers models for offline use.

Run once after cloning to avoid first-run download delays.
Usage: uv run python scripts/preload_models.py
"""

from sentence_transformers import SentenceTransformer

MODELS = [
    "all-MiniLM-L6-v2",
]


def main():
    for model_name in MODELS:
        print(f"Downloading {model_name}...")
        SentenceTransformer(model_name)
        print(f"  ✓ {model_name} cached")
    print("\nAll models preloaded. Offline use ready.")


if __name__ == "__main__":
    main()
