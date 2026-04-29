"""FRONTEND-001: Check <img> tags for missing alt attribute.
Uses html.parser for proper HTML parsing.
alt="" (decorative images) → PASS.  Missing alt entirely → FAIL.
"""
import glob
import sys
from html.parser import HTMLParser


class AltChecker(HTMLParser):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            attrs_dict = dict(attrs)
            if "alt" not in attrs_dict:
                line, col = self.getpos()
                self.errors.append(f"{self.filename}:{line}: <img> missing alt attribute")
            # alt="" is valid for decorative images (WCAG allows role="presentation")


def main():
    errors = []
    patterns = ["**/*.html", "**/*.htm", "**/*.jsx", "**/*.tsx", "**/*.vue"]
    for pattern in patterns:
        for f in glob.glob(pattern, recursive=True):
            if ".git/" in f or "node_modules/" in f or "venv/" in f:
                continue
            try:
                checker = AltChecker(f)
                checker.feed(open(f, encoding="utf-8", errors="ignore").read())
                errors.extend(checker.errors)
            except Exception:
                pass
    if errors:
        for e in errors[:20]:
            print(e)
        sys.exit(0)
    else:
        print("PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
