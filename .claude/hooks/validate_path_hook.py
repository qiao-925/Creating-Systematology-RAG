#!/usr/bin/env python3
"""File path placement enforcement hook (PreToolUse).

Intercepts Write/Edit tool calls and validates that the target file path
belongs to an allowed zone per .claude/path-rules.yaml.

- Edit on existing files: allowed (historical files not constrained)
- Write on new files: validated against zones and root_files

Reads:  JSON from stdin (Claude Code hook protocol)
Outputs: hookSpecificOutput JSON to stdout for block decisions
Exits:  0 = allow, 2 = block
"""
import json
import os
import sys
from pathlib import Path


def load_rules(config_path: str) -> dict | None:
    """Load path-rules.yaml."""
    try:
        import yaml
        with open(config_path) as f:
            return yaml.safe_load(f)
    except ImportError:
        # PyYAML not available — skip enforcement
        return None
    except Exception:
        return None


def normalize_path(file_path: str, project_root: str) -> str | None:
    """Make file_path relative to project_root. Returns None if outside."""
    p = Path(file_path).resolve()
    try:
        rel = p.relative_to(Path(project_root).resolve())
        # Convert to forward slashes for consistent matching
        return rel.as_posix()
    except ValueError:
        return None


def matches_pattern(rel_path: str, pattern: str) -> bool:
    """Match rel_path against a glob pattern with ** support.

    Handles ** to match zero or more path components.
    """
    path_parts = rel_path.split("/")
    pattern_parts = pattern.split("/")

    return _match_parts(path_parts, pattern_parts)


def _match_parts(path_parts: list[str], pattern_parts: list[str]) -> bool:
    """Recursive helper for matches_pattern."""
    # Both exhausted — match
    if not path_parts and not pattern_parts:
        return True
    # Pattern exhausted but path remains — no match
    if not pattern_parts:
        return False
    # Path exhausted — only match if remaining pattern is all **
    if not path_parts:
        return all(p == "**" for p in pattern_parts)

    pat = pattern_parts[0]

    if pat == "**":
        # ** matches zero or more components
        # Try matching ** against zero components, one component, two, etc.
        for i in range(len(path_parts) + 1):
            if _match_parts(path_parts[i:], pattern_parts[1:]):
                return True
        return False
    else:
        # Single component match using fnmatch
        import fnmatch
        if fnmatch.fnmatch(path_parts[0], pat):
            return _match_parts(path_parts[1:], pattern_parts[1:])
        return False


def matches_zone(rel_path: str, zone: dict) -> bool:
    """Check if rel_path matches any pattern in a zone."""
    for pattern in zone.get("patterns", []):
        if matches_pattern(rel_path, pattern):
            return True
    return False


def find_matching_zone(rel_path: str, rules: dict) -> str | None:
    """Return the name of the first matching zone, or None."""
    for zone in rules.get("zones", []):
        if matches_zone(rel_path, zone):
            return zone["name"]
    return None


def is_root_file(rel_path: str, rules: dict) -> bool:
    """Check if the path is an allowed root-level file."""
    return rel_path in rules.get("root_files", [])


def suggest_zone(rel_path: str) -> str | None:
    """Suggest the most likely correct zone based on file extension."""
    ext = Path(rel_path).suffix.lower()
    ext_hints = {
        ".py": "backend/",
        ".ts": "web/src/",
        ".tsx": "web/src/",
        ".css": "web/src/",
        ".md": "docs/",
        ".sh": "scripts/",
    }
    return ext_hints.get(ext)


def block(reason: str):
    """Output block decision and exit with code 2."""
    print(json.dumps({
        "hookSpecificOutput": {
            "permissionDecision": "deny",
            "reason": reason
        }
    }))
    sys.exit(2)


def main():
    try:
        data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    if tool_name not in ("Write", "Edit"):
        sys.exit(0)

    file_path = data.get("tool_input", {}).get("file_path", "")
    if not file_path:
        sys.exit(0)

    # Edit on existing files — allow (historical files not constrained)
    if tool_name == "Edit" and os.path.exists(file_path):
        sys.exit(0)

    # Determine project root from hook location
    hook_dir = Path(__file__).resolve().parent          # .claude/hooks/
    project_root = hook_dir.parent.parent               # project root

    # Load rules
    config_path = project_root / ".claude" / "path-rules.yaml"
    if not config_path.exists():
        sys.exit(0)  # No rules = no enforcement
    rules = load_rules(str(config_path))
    if rules is None:
        sys.exit(0)

    # Normalize path
    rel_path = normalize_path(file_path, str(project_root))
    if rel_path is None:
        block(f"Path is outside project root: {file_path}")

    # Check zones
    zone = find_matching_zone(rel_path, rules)
    if zone:
        sys.exit(0)

    # Check root files
    if is_root_file(rel_path, rules):
        sys.exit(0)

    # Block — with suggestion
    hint = suggest_zone(rel_path)
    hint_msg = f" Did you mean to put it in {hint}?" if hint else ""
    block(
        f"Path not allowed: '{rel_path}' does not match any "
        f"defined zone in .claude/path-rules.yaml.{hint_msg} "
        f"Add the path pattern to the correct zone in .claude/path-rules.yaml."
    )


if __name__ == "__main__":
    main()
