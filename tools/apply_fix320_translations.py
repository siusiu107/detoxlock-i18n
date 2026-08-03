#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import gzip
import hashlib
import json
import os
import re

ROOT = Path(__file__).resolve().parents[1]
INPUT = Path(os.environ.get('FIX320_TRANSLATIONS', ROOT / '.fix320/generated_complete_translations.json'))
MANIFEST = ROOT / 'manifest.json'
HANGUL = re.compile(r'[가-힣ㄱ-ㅎㅏ-ㅣ]')

data = json.loads(INPUT.read_text(encoding='utf-8'))
manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
exact = data['exact']
patterns = data['patterns']
required_keys = {'hc.' + item['key'] for item in exact.values()} | {'hc.' + item['key'] for item in patterns.values()}

verification = []
verification.append('DetoxLock FIX320 language-pack verification')
verification.append(f'- exact keys added: {len(exact)}')
verification.append(f'- dynamic pattern keys added: {len(patterns)}')

for tag, metadata in manifest['languages'].items():
    path = ROOT / metadata['file']
    raw = gzip.decompress(path.read_bytes())
    pack = json.loads(raw.decode('utf-8'))
    translations = pack.get('translations')
    if not isinstance(translations, dict):
        raise RuntimeError(f'{tag}: translations object missing')

    for source, item in exact.items():
        value = source if tag == 'ko' else item['translations'].get(tag) or item['translations']['en']
        if tag != 'ko' and HANGUL.search(value):
            raise RuntimeError(f'{tag}: Hangul remains in exact {item["key"]}: {value}')
        translations['hc.' + item['key']] = value

    for regex, item in patterns.items():
        value = regex if tag == 'ko' else item['replacements'].get(tag) or item['replacements']['en']
        if tag != 'ko' and HANGUL.search(value):
            raise RuntimeError(f'{tag}: Hangul remains in pattern {item["key"]}: {value}')
        translations['hc.' + item['key']] = value

    missing = sorted(required_keys.difference(translations))
    if missing:
        raise RuntimeError(f'{tag}: {len(missing)} FIX320 keys missing')
    if any(not str(translations[key]).strip() for key in required_keys):
        raise RuntimeError(f'{tag}: blank FIX320 translation')

    pack['version'] = 5
    rendered = json.dumps(pack, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    output = gzip.compress(rendered, compresslevel=9, mtime=0)
    path.write_bytes(output)

    metadata['version'] = 5
    metadata['sha256'] = hashlib.sha256(output).hexdigest()
    metadata['size'] = len(output)
    metadata['translationCount'] = len(translations)
    metadata['encoding'] = 'gzip'
    metadata['uncompressedSize'] = len(rendered)
    verification.append(f'- {tag}: {len(translations)} translations, sha256={metadata["sha256"]}')

manifest['schemaVersion'] = max(1, int(manifest.get('schemaVersion', 1)))
manifest['minAppVersionCode'] = max(57, int(manifest.get('minAppVersionCode', 0)))
MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')

# Re-open every written file and verify manifest hashes/counts match actual bytes.
for tag, metadata in manifest['languages'].items():
    path = ROOT / metadata['file']
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != metadata['sha256']:
        raise RuntimeError(f'{tag}: manifest hash mismatch')
    pack = json.loads(gzip.decompress(payload).decode('utf-8'))
    translations = pack['translations']
    if len(translations) != metadata['translationCount']:
        raise RuntimeError(f'{tag}: translation count mismatch')
    if not required_keys.issubset(translations):
        raise RuntimeError(f'{tag}: post-write key verification failed')

verification.append('- manifest and all 12 gzip packs verified after write')
(ROOT / 'FIX320_I18N_VERIFICATION.txt').write_text('\n'.join(verification) + '\n', encoding='utf-8')
print('\n'.join(verification[:4]))
