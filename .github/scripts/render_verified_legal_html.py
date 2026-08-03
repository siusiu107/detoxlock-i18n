#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import base64
import gzip
import hashlib
import html
import json
import re

ROOT = Path(__file__).resolve().parents[2]
LEGAL = ROOT / "legal"
WORKFLOW = ROOT / ".github" / "workflows" / "publish-legal-html-from-verified-bundle.yml"


def template_from_workflow(variable: str) -> str:
    text = WORKFLOW.read_text(encoding="utf-8")
    match = re.search(rf"^\s*{re.escape(variable)}:\s*'([^']+)'\s*$", text, re.MULTILINE)
    if not match:
        raise RuntimeError(f"Missing embedded template: {variable}")
    return gzip.decompress(base64.b64decode(match.group(1))).decode("utf-8")


def load_verified_translations() -> dict[str, dict[str, str]]:
    manifest = json.loads((LEGAL / "manifest.json").read_text(encoding="utf-8"))
    encoded = bytearray()
    for item in manifest["parts"]:
        raw = (LEGAL / item["file"]).read_bytes()
        assert len(raw) == item["size"], item["file"]
        assert hashlib.sha256(raw).hexdigest() == item["sha256"], item["file"]
        encoded.extend(raw)
    compressed = base64.b64decode(bytes(encoded), validate=False)
    decoded = gzip.decompress(compressed)
    # The manifest's decoded fields describe the uncompressed JSON payload,
    # not the intermediate gzip byte stream.
    assert len(decoded) == manifest["decodedSize"]
    assert hashlib.sha256(decoded).hexdigest() == manifest["decodedSha256"]
    translations = json.loads(decoded.decode("utf-8"))
    assert len(translations["ko"]) == 151
    return translations


def main() -> None:
    translations = load_verified_translations()
    templates = {
        "terms_of_service": template_from_workflow("TERMS_TEMPLATE_GZIP_BASE64"),
        "privacy_policy": template_from_workflow("PRIVACY_TEMPLATE_GZIP_BASE64"),
    }
    dates = {
        "ja": "2026年6月27日",
        "zh-CN": "2026年6月27日",
        "zh-TW": "2026年6月27日",
        "es": "27 de junio de 2026",
        "fr": "27 juin 2026",
        "de": "27. Juni 2026",
        "pt-BR": "27 de junho de 2026",
        "id": "27 Juni 2026",
        "vi": "27 tháng 6 năm 2026",
        "th": "27 มิถุนายน 2026",
    }
    tags = ["ja", "zh-CN", "zh-TW", "es", "fr", "de", "pt-BR", "id", "vi", "th"]
    output = LEGAL / "html"
    output.mkdir(parents=True, exist_ok=True)
    for old in output.glob("*.html"):
        old.unlink()

    placeholder = re.compile(r"\{\{T(\d+)\}\}")
    hangul = re.compile(r"[가-힣ㄱ-ㅎㅏ-ㅣ]")
    for tag in tags:
        assert len(translations[tag]) == 151
        for base_name, template in templates.items():
            rendered = template.replace('lang="ko"', f'lang="{tag}"', 1)

            def replace(match: re.Match[str]) -> str:
                value = translations[tag][match.group(1)].strip()
                value = value.replace("2026년 6월 27일", dates[tag])
                assert value
                return html.escape(value, quote=False)

            rendered = placeholder.sub(replace, rendered)
            assert "{{T" not in rendered
            assert not hangul.search(rendered), (tag, base_name)
            target = output / f"{base_name}.{tag}.html"
            target.write_text(rendered, encoding="utf-8")
            assert target.stat().st_size > 4000

    files = sorted(output.glob("*.html"))
    assert len(files) == 20, len(files)
    print(f"OK: rendered {len(files)} external legal HTML documents")


if __name__ == "__main__":
    main()
