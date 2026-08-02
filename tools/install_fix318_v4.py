#!/usr/bin/env python3
import base64, gzip, hashlib, json, pathlib, shutil, zlib

root = pathlib.Path('.')
locales = ['en','ko','ja','zh-CN','zh-TW','es','fr','de','pt-BR','id','vi','th']
v4_hash = {
'en':'b722bc9da08615686f87ede6e62fa881c98a6a22c97ce805e0e1e7155ea11003',
'ko':'6217aef1abb1ac9492ad1c409a1dee6ee867fca985f673427e386f2cb7d5320e',
'ja':'02b2d3b8ddea5038f4936e91cf59c3b11ba4dadf392f799b5091c0e9ce815819',
'zh-CN':'f80d113e4b4d458cc48afce8358c7daf36f88f3d7bede2228b7f3d21ed10bbb6',
'zh-TW':'a7cedf4e1e5778706909d1e4dbe837f3d8c134a8bd4c472ec7bc9e903feb9182',
'es':'d3ae10ecd98675c60cd90a39892b03061da2a77e0ceedc9dea76f799273d6b68',
'fr':'fc0ca4300e998a8aed659f0649b388fe2aefb57737516571c073b79354a1341c',
'de':'ca61fd5f54dddccf1eb0a3ab3a6b3bef59896d8a52fe3b81d640c29956f50d9c',
'pt-BR':'aa2058775f13fd0dad5060a20699d1fc3c1ea1dce1bf04d45846436e0565112a',
'id':'04f494fa15049d78896669ba88b28f1649a39aff21f71e694015e612d7a33ffa',
'vi':'d036590d40b24d9d86e33e9d4a38d40f4365f9b606af8587a1b97072f2620292',
'th':'9f5d7a592e8261aed7179440e7279bce18b446fe2c1d334e062feb94de5576d1',
}

def load_delta(directory, count, expected_sha):
    direct = root/directory/'full.b64'
    if direct.exists():
        encoded = direct.read_text(encoding='ascii').strip()
    else:
        parts = sorted((root/directory).glob('chunk-*.txt'), key=lambda p:int(p.stem.split('-')[-1]))
        assert len(parts) == count, (directory, len(parts))
        encoded = ''.join(p.read_text(encoding='ascii').strip() for p in parts)
    assert hashlib.sha256(encoded.encode()).hexdigest() == expected_sha, directory
    value = json.loads(zlib.decompress(base64.b64decode(encoded)).decode('utf-8'))
    assert set(value) == set(locales), directory
    return value

base_to_v2 = load_delta('.fix318-base-v2', 4, '72170b32ecc1ccf11a4856b55b5f3aeb6f029ceb7874a0c0255f7b7cecde95ee')
v2_to_v4 = load_delta('.fix318-direct-delta', 8, '2ec3f6dc768d99466a79b237d0b853b242e5b4b1df4bf85306a4eb158cab5245')
old_manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8'))
names = {loc:(old_manifest['languages'][loc]['nativeName'],old_manifest['languages'][loc]['englishName']) for loc in locales}

out = {}
common_keys = None
for loc in locales:
    path = root/f'locales/{loc}.json.gz'
    current = path.read_bytes()
    if hashlib.sha256(current).hexdigest() == v4_hash[loc]:
        raw_gz = current
        pack = json.loads(gzip.decompress(raw_gz).decode('utf-8'))
        raw_json = json.dumps(pack,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
    else:
        pack = json.loads(gzip.decompress(current).decode('utf-8'))
        translations = pack['translations']
        for delta in (base_to_v2[loc], v2_to_v4[loc]):
            for key in delta.get('remove',[]): translations.pop(key,None)
            translations.update(delta.get('set',{}))
        pack['version'] = 4
        raw_json = json.dumps(pack,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
        raw_gz = gzip.compress(raw_json,compresslevel=9,mtime=0)
    translations = pack['translations']
    assert pack['locale'] == loc, loc
    assert pack['version'] == 4, loc
    assert len(translations) == 2329, (loc,len(translations))
    assert all(str(v).strip() for v in translations.values()), loc
    assert hashlib.sha256(raw_gz).hexdigest() == v4_hash[loc], loc
    keys = set(translations)
    common_keys = keys if common_keys is None else common_keys
    assert keys == common_keys, loc
    path.write_bytes(raw_gz)
    native,english = names[loc]
    out[loc] = {'nativeName':native,'englishName':english,'version':4,'file':f'locales/{loc}.json.gz','sha256':v4_hash[loc],'size':len(raw_gz),'translationCount':2329,'encoding':'gzip','uncompressedSize':len(raw_json)}

manifest = {'schemaVersion':1,'defaultLocale':'en','minAppVersionCode':56,'languages':out}
(root/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
for p in ['bundles','.language-pack-patch-v3','.fix318-v4-delta','.fix318-direct-delta','.fix318-base-v2','.fix318-direct-delta','tools/v3-base']:
    shutil.rmtree(root/p,ignore_errors=True)
(root/'tools/v3_base_delta.b64').unlink(missing_ok=True)
print('Verified and published 12 direct v4 packs with 2329 keys each')
