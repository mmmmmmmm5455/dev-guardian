"""AUTO-FIX-001: Generate .gitignore based on detected project type.
Triggered when GITIGNORE-001 returns MISSING.
Writes .gitignore.proposed first — user confirms before renaming to .gitignore.
"""
import os
import sys
import glob

TEMPLATES = {
    "python": """# Byte-compiled / __pycache__
__pycache__/
*.py[cod]
*.pyo
*.egg-info/
dist/
build/
*.egg

# Virtual environments
venv/
.venv/
env/
.env
*.env

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
Desktop.ini

# Logs
*.log

# Archives
*.zip
*.tar.gz
*.7z
*.rar

# Database
*.db
*.sqlite
*.sqlite3

# Jupyter
.ipynb_checkpoints/

# Checkpoints
.checkpoints/
""",

    "node": """# Dependencies
node_modules/
.pnp
.pnp.js

# Build output
dist/
build/
.next/
.nuxt/

# Environment
.env
.env*.local
*.env

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Logs
*.log
npm-debug.log*

# Coverage
coverage/
.nyc_output/

# Cache
.eslintcache
.tsbuildinfo

# Checkpoints
.checkpoints/
""",

    "go": """# Binaries
*.exe
*.exe~
*.dll
*.so
*.dylib
*.test
*.out

# Go workspace
go.work

# Dependencies
vendor/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Environment
.env
*.env

# Logs
*.log

# Archives
*.zip
*.tar.gz

# Checkpoints
.checkpoints/
""",

    "rust": """# Build output
target/
debug/
release/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Environment
.env
*.env

# Logs
*.log

# Archives
*.zip
*.tar.gz

# Checkpoints
.checkpoints/
""",

    "generic": """# Environment
.env
*.env

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
Desktop.ini

# Logs
*.log

# Archives
*.zip
*.tar.gz
*.7z

# Checkpoints
.checkpoints/
""",
}


def detect_project_type():
    """Detect project type based on files present."""
    scores = {"python": 0, "node": 0, "go": 0, "rust": 0}

    # Python indicators
    for pattern in ["**/*.py", "requirements*.txt", "pyproject.toml", "setup.py", "setup.cfg", "Pipfile"]:
        if glob.glob(pattern, recursive=True):
            scores["python"] += 1

    # Node.js indicators
    for pattern in ["package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "**/*.js", "**/*.ts"]:
        if glob.glob(pattern, recursive=True):
            scores["node"] += 1

    # Go indicators
    for pattern in ["go.mod", "go.sum", "**/*.go"]:
        if glob.glob(pattern, recursive=True):
            scores["go"] += 1

    # Rust indicators
    for pattern in ["Cargo.toml", "Cargo.lock", "**/*.rs"]:
        if glob.glob(pattern, recursive=True):
            scores["rust"] += 1

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "generic"
    return best


def main():
    project_type = detect_project_type()
    template = TEMPLATES.get(project_type, TEMPLATES["generic"])

    output_path = ".gitignore.proposed"

    if os.path.exists(".gitignore"):
        print(f"SKIP: .gitignore already exists")
        sys.exit(0)

    # Merge with existing entries if .gitignore.proposed exists
    existing = set()
    if os.path.exists(output_path):
        existing = set(
            line.strip()
            for line in open(output_path).readlines()
            if line.strip() and not line.startswith("#")
        )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(template)

    print(f"GENERATED: .gitignore.proposed (type: {project_type})")
    print(f"Review then run: mv .gitignore.proposed .gitignore && git add .gitignore")


if __name__ == "__main__":
    main()
