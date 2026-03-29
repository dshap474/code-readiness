from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from code_readiness_template.app import app

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "api" / "openapi.yaml"


def render_openapi() -> str:
    return yaml.safe_dump(app.openapi(), sort_keys=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    rendered = render_openapi()
    output = args.output

    if args.check:
        if not output.exists():
            print(f"Missing generated OpenAPI document: {output.relative_to(ROOT)}")
            return 1
        current = output.read_text(encoding="utf-8")
        if current != rendered:
            print(
                f"OpenAPI drift detected in {output.relative_to(ROOT)}. "
                "Run `just docs-generate` to refresh it."
            )
            return 1
        print(f"OpenAPI document is current: {output.relative_to(ROOT)}")
        return 0

    output.write_text(rendered, encoding="utf-8")
    print(f"Wrote OpenAPI document to {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
