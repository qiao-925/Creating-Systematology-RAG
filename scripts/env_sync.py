"""
Seamless .env management via encrypted GitHub Gist.

Flow:
  1. init  — Encrypt current .env, push to private Gist, save config
  2. auto  — On project start: if .env missing, pull + decrypt (silent)
  3. push  — Re-encrypt current .env and update Gist
  4. pull  — Force pull from Gist and decrypt to .env

Encryption: PBKDF2 key derivation + HMAC-authenticated XOR stream (stdlib only).
Key derived from: `gh auth token` (GitHub OAuth token).
Gist config stored at: <project_root>/.env.remote  (committed, no secrets)
"""

import base64
import hashlib
import hmac
import json
import os
import struct
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
REMOTE_CONFIG = PROJECT_ROOT / ".env.remote"
GIST_FILENAME = "env.encrypted"


# ── GitHub Auth ────────────────────────────────────────────────

def _get_gh_token() -> str:
    """Get GitHub OAuth token from gh CLI.

    Raises RuntimeError if gh is not installed or not authenticated.
    """
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True, text=True, timeout=10,
        )
    except FileNotFoundError:
        raise RuntimeError(
            "gh CLI not found. Install it: https://cli.github.com/\n"
            "Then run: gh auth login"
        )

    if result.returncode != 0:
        raise RuntimeError(
            "gh not authenticated. Run: gh auth login"
        )

    token = result.stdout.strip()
    if not token:
        raise RuntimeError(
            "gh auth token is empty. Run: gh auth login"
        )
    return token


# ── Crypto (stdlib only) ──────────────────────────────────────

def _derive_key(passphrase: str, salt: bytes, length: int) -> bytes:
    """PBKDF2 key derivation."""
    return hashlib.pbkdf2_hmac("sha256", passphrase.encode(), salt, 100_000, dklen=length)


def _key_stream(key: bytes, length: int) -> bytes:
    """Expand key into a stream via SHA-256 CTR mode."""
    stream = b""
    counter = 0
    while len(stream) < length:
        stream += hashlib.sha256(key + struct.pack(">I", counter)).digest()
        counter += 1
    return stream[:length]


def encrypt(data: bytes, passphrase: str) -> bytes:
    """Encrypt data → base64 blob (salt‖mac‖ciphertext)."""
    salt = os.urandom(16)
    key = _derive_key(passphrase, salt, 32)
    ks = _key_stream(key, len(data))
    ct = bytes(a ^ b for a, b in zip(data, ks))
    mac = hmac.new(key, salt + ct, "sha256").digest()
    return base64.b64encode(salt + mac + ct)


def decrypt(blob: bytes, passphrase: str) -> bytes:
    """Decrypt base64 blob → plaintext bytes."""
    raw = base64.b64decode(blob)
    salt, mac, ct = raw[:16], raw[16:48], raw[48:]
    key = _derive_key(passphrase, salt, 32)
    if not hmac.compare_digest(mac, hmac.new(key, salt + ct, "sha256").digest()):
        raise ValueError("Decryption failed: wrong token or corrupted data")
    ks = _key_stream(key, len(ct))
    return bytes(a ^ b for a, b in zip(ct, ks))


# ── Gist operations ──────────────────────────────────────────

def _gh(args: list[str], input_data: str | None = None) -> str:
    """Run a gh CLI command, return stdout."""
    result = subprocess.run(
        ["gh"] + args,
        capture_output=True, text=True, timeout=30,
        input=input_data,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _gist_create(content: str) -> str:
    """Create a private Gist, return gist ID."""
    result = subprocess.run(
        ["gh", "gist", "create", "--filename", GIST_FILENAME, "-"],
        capture_output=True, text=True, timeout=30,
        input=content,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Gist creation failed: {result.stderr.strip()}")
    url = result.stdout.strip()
    return url.rsplit("/", 1)[-1]


def _gist_update(gist_id: str, content: str) -> None:
    """Update an existing Gist."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".encrypted", delete=False) as f:
        f.write(content)
        tmp_path = f.name
    try:
        _gh(["gist", "edit", gist_id, "--filename", GIST_FILENAME, tmp_path])
    finally:
        os.unlink(tmp_path)


def _gist_read(gist_id: str) -> str:
    """Read Gist content."""
    return _gh(["gist", "view", gist_id, "--filename", GIST_FILENAME, "--raw"])


# ── Config (.env.remote) ─────────────────────────────────────

def _load_config() -> dict:
    if not REMOTE_CONFIG.exists():
        return {}
    return json.loads(REMOTE_CONFIG.read_text())


def _save_config(cfg: dict) -> None:
    REMOTE_CONFIG.write_text(json.dumps(cfg, indent=2) + "\n")


# ── Commands ──────────────────────────────────────────────────

def cmd_init():
    """First-time setup: encrypt .env → private Gist."""
    if not ENV_FILE.exists():
        print(f"ERROR: {ENV_FILE} not found. Create it first, then run init.")
        sys.exit(1)

    token = _get_gh_token()

    # Encrypt
    env_data = ENV_FILE.read_bytes()
    blob = encrypt(env_data, token).decode()

    # Push to Gist
    print("Pushing encrypted .env to private GitHub Gist...")
    gist_id = _gist_create(blob)

    # Save config
    _save_config({"gist_id": gist_id})

    print(f"\n{'='*60}")
    print(f"  Init complete!")
    print(f"  Gist ID : {gist_id}")
    print(f"  Config  : {REMOTE_CONFIG}")
    print(f"{'='*60}")
    print(f"\n  On a new machine, just run:")
    print(f"    gh auth login")
    print(f"    uv run python scripts/env_sync.py pull")
    print()


def cmd_push():
    """Re-encrypt current .env and update Gist."""
    if not ENV_FILE.exists():
        print(f"ERROR: {ENV_FILE} not found.")
        sys.exit(1)

    cfg = _load_config()
    if not cfg.get("gist_id"):
        print("ERROR: Not initialized. Run: python scripts/env_sync.py init")
        sys.exit(1)

    token = _get_gh_token()
    blob = encrypt(ENV_FILE.read_bytes(), token).decode()
    _gist_update(cfg["gist_id"], blob)
    print("Pushed encrypted .env to Gist.")


def cmd_pull():
    """Pull from Gist and decrypt to .env."""
    cfg = _load_config()
    if not cfg.get("gist_id"):
        print("ERROR: Not initialized. Run: python scripts/env_sync.py init")
        sys.exit(1)

    token = _get_gh_token()
    blob = _gist_read(cfg["gist_id"])
    env_data = decrypt(blob.encode(), token)
    ENV_FILE.write_bytes(env_data)
    ENV_FILE.chmod(0o600)
    print(f"Pulled and decrypted .env ({len(env_data)} bytes).")


def cmd_auto():
    """Auto-pull if .env is missing. Designed to be called on startup (silent)."""
    if ENV_FILE.exists():
        return  # Nothing to do — fast path

    cfg = _load_config()
    if not cfg.get("gist_id"):
        return  # Not configured — skip silently

    try:
        token = _get_gh_token()
        blob = _gist_read(cfg["gist_id"])
        env_data = decrypt(blob.encode(), token)
        ENV_FILE.write_bytes(env_data)
        ENV_FILE.chmod(0o600)
        print(f"[env-sync] Auto-pulled .env from Gist ({len(env_data)} bytes)")
    except Exception as e:
        # Never break project startup
        print(f"[env-sync] Auto-pull skipped: {e}", file=sys.stderr)


# ── CLI entry point ───────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "init":
        cmd_init()
    elif cmd == "push":
        cmd_push()
    elif cmd == "pull":
        cmd_pull()
    elif cmd == "auto":
        cmd_auto()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
