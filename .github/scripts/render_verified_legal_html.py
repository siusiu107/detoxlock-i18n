#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import base64
import gzip
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
LEGAL = ROOT / "legal"
TAGS = ["ja", "zh-CN", "zh-TW", "es", "fr", "de", "pt-BR", "id", "vi", "th"]


def load_verified_documents() -> dict[str, dict[str, str]]:
    manifest = json.loads((LEGAL / "manifest.json").read_text(encoding="utf-8"))
    encoded = bytearray()
    for item in manifest["parts"]:
        raw = (LEGAL / item["file"]).read_bytes()
        assert len(raw) == item["size"], item["file"]
        assert hashlib.sha256(raw).hexdigest() == item["sha256"], item["file"]
        encoded.extend(raw)
    compressed = base64.b64decode(bytes(encoded), validate=False)
    decoded = gzip.decompress(compressed)
    assert len(decoded) == manifest["decodedSize"]
    assert hashlib.sha256(decoded).hexdigest() == manifest["decodedSha256"]
    payload = json.loads(decoded.decode("utf-8"))
    assert payload["schemaVersion"] == 1
    documents = payload["documents"]
    assert sorted(documents) == sorted(TAGS)
    return documents


def main() -> None:
    documents = load_verified_documents()
    output = LEGAL / "html"
    output.mkdir(parents=True, exist_ok=True)
    for old in output.glob("*.html"):
        old.unlink()

    hangul = re.compile(r"[가-힣ㄱ-ㅎㅏ-ㅣ]")
    names = {"privacy": "privacy_policy", "terms": "terms_of_service"}
    for tag in TAGS:
        assert sorted(documents[tag]) == ["privacy", "terms"]
        for kind, base_name in names.items():
            rendered = documents[tag][kind].strip()
            assert rendered.lower().startswith("<!doctype html>")
            rendered = rendered.replace('lang="ko"', f'lang="{tag}"', 1)
            assert f'lang="{tag}"' in rendered[:200]
            assert not hangul.search(rendered), (tag, kind)
            target = output / f"{base_name}.{tag}.html"
            target.write_text(rendered + "\n", encoding="utf-8")
            assert target.stat().st_size > 4000

    files = sorted(output.glob("*.html"))
    assert len(files) == 20, len(files)
    print(f"OK: published {len(files)} verified external legal HTML documents")


if __name__ == "__main__":
    main()
