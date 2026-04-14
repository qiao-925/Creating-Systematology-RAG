"""
Seamless .env management via encrypted GitHub Gist.

Flow:
  1. init  — Encrypt current .env, push to private Gist, save config
  2. auto  — On project start: if .env missing, pull + decrypt (silent)
  3. push  — Re-encrypt current .env and update Gist
  4. pull  — Force pull from Gist and decrypt to .env
  5. setup <passphrase> — Save passphrase on a new machine

Encryption: PBKDF2 key derivation + HMAC-authenticated XOR stream (stdlib only).
Passphrase stored at: ~/.config/cs-rag/passphrase
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
PASSPHRASE_DIR = Path.home() / ".config" / "cs-rag"
PASSPHRASE_FILE = PASSPHRASE_DIR / "passphrase"
GIST_FILENAME = "env.encrypted"


# ── Crypto (stdlib only) ──────────────────────────────────────────

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
        raise ValueError("Decryption failed: wrong passphrase or corrupted data")
    ks = _key_stream(key, len(ct))
    return bytes(a ^ b for a, b in zip(ct, ks))


# ── Passphrase management ────────────────────────────────────────

def _load_passphrase() -> str:
    if not PASSPHRASE_FILE.exists():
        raise FileNotFoundError(
            f"Passphrase not found at {PASSPHRASE_FILE}\n"
            "Run: python scripts/env_sync.py init   (first time)\n"
            "  or: python scripts/env_sync.py setup <passphrase>  (new machine)"
        )
    return PASSPHRASE_FILE.read_text().strip()


def _save_passphrase(passphrase: str) -> None:
    PASSPHRASE_DIR.mkdir(parents=True, exist_ok=True)
    PASSPHRASE_FILE.write_text(passphrase)
    PASSPHRASE_FILE.chmod(0o600)


def _generate_passphrase() -> str:
    return base64.urlsafe_b64encode(os.urandom(24)).decode()


# ── Gist operations ──────────────────────────────────────────────

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
    # gh gist create returns the URL, extract ID
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


# ── Config (.env.remote) ─────────────────────────────────────────

def _load_config() -> dict:
    if not REMOTE_CONFIG.exists():
        return {}
    return json.loads(REMOTE_CONFIG.read_text())


def _save_config(cfg: dict) -> None:
    REMOTE_CONFIG.write_text(json.dumps(cfg, indent=2) + "\n")


# ── Commands ──────────────────────────────────────────────────────

def cmd_init():
    """First-time setup: encrypt .env → private Gist."""
    if not ENV_FILE.exists():
        print(f"ERROR: {ENV_FILE} not found. Create it first, then run init.")
        sys.exit(1)

    # Generate and save passphrase
    passphrase = _generate_passphrase()
    _save_passphrase(passphrase)

    # Encrypt
    env_data = ENV_FILE.read_bytes()
    blob = encrypt(env_data, passphrase).decode()

    # Push to Gist
    print("Pushing encrypted .env to private GitHub Gist...")
    gist_id = _gist_create(blob)

    # Save config
    _save_config({"gist_id": gist_id})

    print(f"\n{'='*60}")
    print(f"  Init complete!")
    print(f"  Gist ID : {gist_id}")
    print(f"  Config  : {REMOTE_CONFIG}")
    print(f"  Key file: {PASSPHRASE_FILE}")
    print(f"{'='*60}")
    print(f"\n  For a new machine, copy the passphrase:")
    print(f"    {passphrase}")
    print(f"  Then run:")
    print(f"    python scripts/env_sync.py setup <passphrase>")
    print(f"\n  After that, .env auto-syncs on project start.\n")


def cmd_push():
    """Re-encrypt current .env and update Gist."""
    if not ENV_FILE.exists():
        print(f"ERROR: {ENV_FILE} not found.")
        sys.exit(1)

    cfg = _load_config()
    if not cfg.get("gist_id"):
        print("ERROR: Not initialized. Run: python scripts/env_sync.py init")
        sys.exit(1)

    passphrase = _load_passphrase()
    blob = encrypt(ENV_FILE.read_bytes(), passphrase).decode()
    _gist_update(cfg["gist_id"], blob)
    print("Pushed encrypted .env to Gist.")


def cmd_pull():
    """Pull from Gist and decrypt to .env."""
    cfg = _load_config()
    if not cfg.get("gist_id"):
        print("ERROR: Not initialized. Run: python scripts/env_sync.py init")
        sys.exit(1)

    passphrase = _load_passphrase()
    blob = _gist_read(cfg["gist_id"])
    env_data = decrypt(blob.encode(), passphrase)
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

    if not PASSPHRASE_FILE.exists():
        return  # No passphrase — skip silently

    try:
        passphrase = _load_passphrase()
        blob = _gist_read(cfg["gist_id"])
        env_data = decrypt(blob.encode(), passphrase)
        ENV_FILE.write_bytes(env_data)
        ENV_FILE.chmod(0o600)
        print(f"[env-sync] Auto-pulled .env from Gist ({len(env_data)} bytes)")
    except Exception as e:
        # Never break project startup
        print(f"[env-sync] Auto-pull skipped: {e}", file=sys.stderr)


def cmd_setup(passphrase: str):
    """Save passphrase on a new machine."""
    _save_passphrase(passphrase)
    print(f"Passphrase saved to {PASSPHRASE_FILE}")
    print("Run the project normally — .env will auto-sync on startup.")


# ── CLI entry point ───────────────────────────────────────────────

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
    elif cmd == "setup" and len(sys.argv) >= 3:
        cmd_setup(sys.argv[2])
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
