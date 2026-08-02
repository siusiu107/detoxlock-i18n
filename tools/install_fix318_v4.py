#!/usr/bin/env python3
import base64, gzip, hashlib, json, pathlib, shutil, zlib

root = pathlib.Path('.')
locales = ['en','ko','ja','zh-CN','zh-TW','es','fr','de','pt-BR','id','vi','th']
v4_translation_hash = {
    'en':'af6c96c18b6e854c48462da0c3be339b75ede181ba710eb4a4a003d8f01153a6',
    'ko':'c4b7d9cee1c3bcc99d1e398e56b2a19cc1328c0e7295b704943957a15afd24fd',
    'ja':'783108bc3cc33138c21b8b14650c49ae2d0b9ec093a2cf833d31131ab1eea9e2',
    'zh-CN':'971507471da1a74b4a5ed273b41fdd9fcb5ddc48547b13a26066c2cb03ad0191',
    'zh-TW':'ac6c5a1eae8f7c99c188990d87ac955f5c2774e54845699627d1532e19118066',
    'es':'554265ecd0f9eb1bbc5089743940873979631c81de92359fef95b8fd540ea9bf',
    'fr':'7ff3fce7977aeacb2cc68f400b5a923da0cb2423c12dd557a5d0b2650f9b95ee',
    'de':'9cbccb8f74bc7fefc34f10572ebb3b09a3cca5260a4507370d025a189f301e8b',
    'pt-BR':'3d64cbdbb5ee84e8d0f4cd881ce9d24b91a5e18603ae4cc1503c3d1cd43431e0',
    'id':'2f8a66ca0ffe1fc111b9c3d5a203a99d48e84376df0369ef40a22a3f4dd67621',
    'vi':'c14a6b4c28fa141a5c06e73963eecd6e53d74986745c4fc1e8c838bd514824a2',
    'th':'a773a4143d10c16221ba1eac5e49df41d5139f7934a5b4e349cc01b97ed528a6',
}

def load_delta(directory, count, expected_sha):
    parts = sorted((root / directory).glob('chunk-*.txt'), key=lambda p: int(p.stem.split('-')[-1]))
    assert len(parts) == count, (directory, len(parts))
    encoded = ''.join(part.read_text(encoding='ascii').strip() for part in parts)
    assert hashlib.sha256(encoded.encode()).hexdigest() == expected_sha, directory
    value = json.loads(zlib.decompress(base64.b64decode(encoded)).decode('utf-8'))
    assert set(value) == set(locales), directory
    return value

base_to_v2 = load_delta('.fix318-base-v2', 8, '72170b32ecc1ccf11a4856b55b5f3aeb6f029ceb7874a0c0255f7b7cecde95ee')
v2_to_v4 = load_delta('.fix318-direct-delta', 8, '2ec3f6dc768d99466a79b237d0b853b242e5b4b1df4bf85306a4eb158cab5245')
old_manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
names = {loc: (old_manifest['languages'][loc]['nativeName'], old_manifest['languages'][loc]['englishName']) for loc in locales}

out = {}
common_keys = None
for loc in locales:
    path = root / f'locales/{loc}.json.gz'
    current_pack = json.loads(gzip.decompress(path.read_bytes()).decode('utf-8'))
    translations = dict(current_pack['translations'])
    for delta in (base_to_v2[loc], v2_to_v4[loc]):
        for key in delta.get('remove', []):
            translations.pop(key, None)
        translations.update(delta.get('set', {}))
    assert len(translations) == 2329, (loc, len(translations))
    assert all(str(value).strip() for value in translations.values()), loc
    semantic = json.dumps(translations, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    assert hashlib.sha256(semantic).hexdigest() == v4_translation_hash[loc], f'{loc}: translation content mismatch'
    keys = set(translations)
    common_keys = keys if common_keys is None else common_keys
    assert keys == common_keys, loc
    pack = {'locale': loc, 'schemaVersion': 1, 'translations': translations, 'version': 4}
    raw_json = json.dumps(pack, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    raw_gz = gzip.compress(raw_json, compresslevel=9, mtime=0)
    file_sha = hashlib.sha256(raw_gz).hexdigest()
    path.write_bytes(raw_gz)
    native, english = names[loc]
    out[loc] = {
        'nativeName': native,
        'englishName': english,
        'version': 4,
        'file': f'locales/{loc}.json.gz',
        'sha256': file_sha,
        'size': len(raw_gz),
        'translationCount': 2329,
        'encoding': 'gzip',
        'uncompressedSize': len(raw_json),
    }

manifest = {'schemaVersion': 1, 'defaultLocale': 'en', 'minAppVersionCode': 56, 'languages': out}
(root / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
for directory in ['bundles', '.language-pack-patch-v3', '.fix318-v4-delta', '.fix318-direct-delta', '.fix318-base-v2', 'tools/v3-base']:
    shutil.rmtree(root / directory, ignore_errors=True)
(root / 'tools/v3_base_delta.b64').unlink(missing_ok=True)
print('Verified and published 12 direct v4 packs with 2329 keys each')
