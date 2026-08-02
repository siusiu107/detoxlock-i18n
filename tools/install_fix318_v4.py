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
manifest_old = json.loads((root/'manifest.json').read_text(encoding='utf-8'))
names = {loc:(manifest_old['languages'][loc]['nativeName'],manifest_old['languages'][loc]['englishName']) for loc in locales}
parts = sorted((root/'.fix318-direct-delta').glob('chunk-*.txt'), key=lambda p:int(p.stem.split('-')[-1]))
encoded = ''.join(p.read_text(encoding='ascii').strip() for p in parts)
assert len(parts) == 8, len(parts)
assert hashlib.sha256(encoded.encode()).hexdigest() == '2ec3f6dc768d99466a79b237d0b853b242e5b4b1df4bf85306a4eb158cab5245'
delta = json.loads(zlib.decompress(base64.b64decode(encoded)).decode('utf-8'))
assert set(delta) == set(locales)

def encode_pack(pack):
    pack['version'] = 4
    raw = json.dumps(pack,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
    return raw,gzip.compress(raw,compresslevel=9,mtime=0)

out = {}
keyset = None
for loc in locales:
    path = root/f'locales/{loc}.json.gz'
    pack = json.loads(gzip.decompress(path.read_bytes()).decode('utf-8'))
    tr = pack['translations']
    for key in delta[loc].get('remove',[]): tr.pop(key,None)
    tr.update(delta[loc].get('set',{}))
    raw,gz = encode_pack(pack)
    assert pack['locale'] == loc
    assert len(tr) == 2329, (loc,len(tr))
    assert all(str(v).strip() for v in tr.values()), loc
    assert hashlib.sha256(gz).hexdigest() == v4_hash[loc], loc
    path.write_bytes(gz)
    native,english = names[loc]
    out[loc] = {'nativeName':native,'englishName':english,'version':4,'file':f'locales/{loc}.json.gz','sha256':v4_hash[loc],'size':len(gz),'translationCount':2329,'encoding':'gzip','uncompressedSize':len(raw)}
    keys = set(tr)
    keyset = keys if keyset is None else keyset
    assert keys == keyset, loc

manifest = {'schemaVersion':1,'defaultLocale':'en','minAppVersionCode':56,'languages':out}
(root/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
for p in ['bundles','.language-pack-patch-v3','.fix318-v4-delta','.fix318-direct-delta','tools/v3-base']:
    shutil.rmtree(root/p,ignore_errors=True)
(root/'tools/v3_base_delta.b64').unlink(missing_ok=True)
print('Published 12 direct v4 packs with 2329 keys each')
