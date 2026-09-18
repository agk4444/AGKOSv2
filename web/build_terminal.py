#!/usr/bin/env python3
"""Build web/terminal.html: compile the AGKOS .agk sources to one Python
bundle, then inject it (JSON-escaped) into web/template.html.

Re-runnable: just run `python3 web/build_terminal.py` from the repo root
(or anywhere — paths are resolved from this file's location).

Note: other workers edit the .agk sources concurrently, so the embedded
bundle is a point-in-time snapshot. Re-run this script to refresh it.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

AGKOS_DIR = Path(__file__).resolve().parent.parent
AGK_BIN = Path.home() / "workspace" / "agk-real" / ".venv" / "bin" / "agk"
TEMPLATE = AGKOS_DIR / "web" / "template.html"
OUT = AGKOS_DIR / "web" / "terminal.html"
PLACEHOLDER = "/*__AGK_BUNDLE__*/"


def main() -> None:
    # 1. Compile the OS to one Python bundle.
    with tempfile.NamedTemporaryFile(
        suffix=".py", prefix="agkos_bundle_", delete=False
    ) as f:
        bundle_path = f.name
    r = subprocess.run(
        [str(AGK_BIN), "build", "boot.agk", "-o", bundle_path],
        cwd=str(AGKOS_DIR),
        capture_output=True,
        text=True,
    )
    sys.stderr.write(r.stderr)
    if r.returncode != 0:
        raise SystemExit(f"agk build failed (exit {r.returncode})")
    src = Path(bundle_path).read_text(encoding="utf-8")
    print(f"bundle: {len(src)} chars -> {bundle_path}")

    # 2. JSON-escape for embedding as a JS string literal.
    escaped = json.dumps(src)
    escaped = escaped.replace("</script", "<\\/script")  # keep </script> out of the page
    escaped = escaped.replace("<!--", "<\\!--")          # avoid HTML comment parsing quirks
    escaped = escaped.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")

    # 3. Inject into the template.
    template = TEMPLATE.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        raise SystemExit(f"placeholder {PLACEHOLDER!r} not found in {TEMPLATE}")
    html = template.replace(PLACEHOLDER, escaped, 1)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
