"""AUTO-FIX-002: Extract hardcoded keys/passwords to .env.example.
Triggered when HARDCODE-001/002/003 returns matches.

Workflow:
1. Scan for hardcoded assignments (API_KEY=, password=, SECRET_KEY=)
2. Extract variable name and placeholder value
3. Write to .env.example (NOT .env — that contains secrets)
4. Report what needs manual replacement in source files
"""
import glob
import os
import re
import sys

# Patterns: (regex, var_group, description)
PATTERNS = [
    (
        r"(?:api[_-]?key|api[_-]?token|secret[_-]?key)\s*=\s*['\"]([^'\"]{8,})['\"]",
        1,
        "API key/token",
    ),
    (
        r"(?:password|passwd|pwd)\s*=\s*['\"]([^'\"]+)['\"]",
        1,
        "password",
    ),
    (
        r"(?:SECRET_KEY|secret_key|FLASK_SECRET_KEY|DJANGO_SECRET_KEY)\s*=\s*['\"]([^'\"]+)['\"]",
        1,
        "secret_key",
    ),
]

# Variable name sanitization map
VAR_MAP = {
    "api_key": "API_KEY",
    "api_token": "API_TOKEN",
    "secret_key": "SECRET_KEY",
    "SECRET_KEY": "SECRET_KEY",
    "FLASK_SECRET_KEY": "FLASK_SECRET_KEY",
    "DJANGO_SECRET_KEY": "DJANGO_SECRET_KEY",
    "password": "PASSWORD",
    "passwd": "PASSWORD",
    "pwd": "PASSWORD",
}


def scan_hardcoded():
    """Scan Python/JS/TS/Sh files for hardcoded secrets."""
    findings = []
    patterns = ["**/*.py", "**/*.js", "**/*.ts", "**/*.sh", "**/*.yml", "**/*.yaml"]
    for pattern in patterns:
        for f in glob.glob(pattern, recursive=True):
            if any(skip in f for skip in [".git/", "node_modules/", "venv/", "__pycache__/"]):
                continue
            try:
                content = open(f, encoding="utf-8", errors="ignore").read()
                for i, line in enumerate(content.splitlines(), 1):
                    for regex, group, desc in PATTERNS:
                        m = re.search(regex, line, re.IGNORECASE)
                        if m:
                            # Skip if already using env var
                            if "os.environ" in line or "os.getenv" in line or "process.env" in line:
                                continue
                            var_match = re.search(
                                r"(\w+)\s*=\s*['\"]", line
                            )
                            if var_match:
                                var_name = var_match.group(1)
                                findings.append(
                                    {
                                        "file": f,
                                        "line": i,
                                        "var_name": var_name,
                                        "description": desc,
                                        "content": line.strip()[:120],
                                    }
                                )
            except Exception:
                pass
    return findings


def main():
    findings = scan_hardcoded()

    if not findings:
        print("PASS: No hardcoded secrets found")
        sys.exit(0)

    # Collect unique env vars to add
    env_vars = {}
    for f in findings:
        var_name = f["var_name"]
        env_key = VAR_MAP.get(var_name, var_name.upper())
        if env_key not in env_vars:
            env_vars[env_key] = f

    # Write .env.example
    env_path = ".env.example"
    existing_vars = set()
    if os.path.exists(env_path):
        for line in open(env_path).readlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                existing_vars.add(line.split("=")[0].strip())

    new_vars = {k: v for k, v in env_vars.items() if k not in existing_vars}

    if not new_vars:
        print("PASS: All hardcoded vars already in .env.example")
        sys.exit(0)

    with open(env_path, "a", encoding="utf-8") as f:
        f.write(f"\n# --- Auto-extracted by code-audit AUTO-FIX-002 ---\n")
        for env_key, finding in new_vars.items():
            f.write(f"# {finding['description']} (found in {finding['file']}:{finding['line']})\n")
            f.write(f"{env_key}=change_me\n")

    # Report
    print(f"EXTRACTED: {len(new_vars)} hardcoded values → {env_path}")
    for env_key, finding in new_vars.items():
        print(f"  {finding['file']}:{finding['line']} — {env_key}")
    print()
    print("Manual steps required:")
    print("  1. Review .env.example and copy values to .env")
    print(f"  2. Replace hardcoded strings with env lookups:")
    for env_key, finding in new_vars.items():
        ext = os.path.splitext(finding["file"])[1]
        if ext in (".py",):
            print(f"     {finding['file']}:{finding['line']} → os.environ.get('{env_key}')")
        elif ext in (".js", ".ts"):
            print(f"     {finding['file']}:{finding['line']} → process.env.{env_key}")
        elif ext in (".sh",):
            print(f"     {finding['file']}:{finding['line']} → ${{{env_key}:-default}}")
    print("  3. Verify .env is in .gitignore")


if __name__ == "__main__":
    main()
