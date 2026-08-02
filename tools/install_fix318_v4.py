#!/usr/bin/env python3
import base64, gzip, hashlib, json, pathlib, shutil, zipfile, zlib

root = pathlib.Path('.')
locales = ['en','ko','ja','zh-CN','zh-TW','es','fr','de','pt-BR','id','vi','th']
v3_hash = {
'en':'47b88137ea5542c90794ea1688c7103c942917e3efa17daf3718598acc81624c',
'ko':'192f62010bf261d58b1693ef690d9f556de2f2179ba73661c9629ff67a0a7b7a',
'ja':'0c1f82d2528d8558a1c76ed290abd13daf6735aab13e1ae072aa378d4ba33d8a',
'zh-CN':'6104e9fbf75d0005268b6e8b0c4e80540369cc20810e8291b8dd02a17ca32986',
'zh-TW':'6f374b43c95a8dc75e81386df28bc2c2253584da637a0ba20214de78efbd61ff',
'es':'a2ba821970ef6b63d80ed6dc7f392abbae6f165f3f7beb1d88a1223028acf67f',
'fr':'7b3b3d9ebb872069bdab64e6fdee51e6fce7321d33a46b859622979394f8a936',
'de':'b732d3ad888ff5f245f74e0e0b22e4274f24cecb1b47e9ad3c38ddc914fcddd8',
'pt-BR':'cd87a72a718ae675b511e5c267cf1d2764ff92293a02ea0eb34fcdfd0b27466c',
'id':'32efaeca364a0792bf36222199eb5418b303b28ebaf2985270347ffb572a9f2c',
'vi':'52826151b9e8c64c1028e94a2c0dbbd1aefcb32816bb969e6550f7c57738442e',
'th':'fdd3e07d6e0bfc798afbaffa3516eb15677c004e9b078b29b719dbfab7899696',
}
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
old_manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8'))
names = {loc:(old_manifest['languages'][loc]['nativeName'], old_manifest['languages'][loc]['englishName']) for loc in locales}
complete = json.loads((root/'.language-pack-patch-v3/complete.json').read_text(encoding='utf-8'))
v3_parts = sorted((root/'.language-pack-patch-v3').glob('chunk-*.txt'))
encoded3 = ''.join(p.read_text(encoding='ascii').strip() for p in v3_parts)
assert len(v3_parts) == int(complete['parts'])
assert hashlib.sha256(encoded3.encode()).hexdigest() == complete['sha256']
delta3 = json.loads(zlib.decompress(base64.b64decode(encoded3)).decode('utf-8'))
def canonical_pack(pack, version):
    pack['version'] = version
    raw_json = json.dumps(pack, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return raw_json, gzip.compress(raw_json, compresslevel=9, mtime=0)
v3packs = {}
for loc in locales:
    path = root/f'locales/{loc}.json.gz'
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest == v3_hash[loc]:
        pack = json.loads(gzip.decompress(raw).decode('utf-8'))
    elif digest == complete['baseHashes'][loc]:
        pack = json.loads(gzip.decompress(raw).decode('utf-8'))
        tr = pack['translations']
        for key in delta3[loc].get('remove', []): tr.pop(key, None)
        tr.update(delta3[loc].get('set', {}))
        _, rebuilt = canonical_pack(pack, 3)
        assert hashlib.sha256(rebuilt).hexdigest() == v3_hash[loc], loc
        pack = json.loads(gzip.decompress(rebuilt).decode('utf-8'))
    else:
        bundle = 'bundles/asia-v3.zip' if loc in {'ja','zh-CN','zh-TW'} else 'bundles/europe-v3.zip'
        assert pathlib.Path(bundle).exists(), (loc, digest)
        with zipfile.ZipFile(bundle) as zf:
            candidate = zf.read(f'locales/{loc}.json.gz')
        assert hashlib.sha256(candidate).hexdigest() == v3_hash[loc], loc
        pack = json.loads(gzip.decompress(candidate).decode('utf-8'))
    v3packs[loc] = pack
v4_parts = sorted((root/'.fix318-v4-delta').glob('chunk-*.txt'))
encoded4 = ''.join(p.read_text(encoding='ascii').strip() for p in v4_parts)
assert len(v4_parts) == 9
assert hashlib.sha256(encoded4.encode()).hexdigest() == 'f75d48e10e783b64451b6497587d1d5f334c9bdc43f491b848d5a8b735a5b7d0'
delta4 = json.loads(zlib.decompress(base64.b64decode(encoded4)).decode('utf-8'))
assert set(delta4) == set(locales)
out_languages = {}
key_sets = []
for loc in locales:
    pack = v3packs[loc]
    tr = pack['translations']
    for key in delta4[loc].get('remove', []): tr.pop(key, None)
    tr.update(delta4[loc].get('set', {}))
    raw_json, raw_gz = canonical_pack(pack, 4)
    assert pack['locale'] == loc
    assert len(tr) == 2329, (loc, len(tr))
    assert not any(v is None or str(v).strip() == '' for v in tr.values())
    assert hashlib.sha256(raw_gz).hexdigest() == v4_hash[loc], loc
    (root/f'locales/{loc}.json.gz').write_bytes(raw_gz)
    native, english = names[loc]
    out_languages[loc] = {'nativeName':native,'englishName':english,'version':4,'file':f'locales/{loc}.json.gz','sha256':v4_hash[loc],'size':len(raw_gz),'translationCount':len(tr),'encoding':'gzip','uncompressedSize':len(raw_json)}
    key_sets.append(set(tr))
assert all(s == key_sets[0] for s in key_sets[1:])
manifest = {'schemaVersion':1,'defaultLocale':'en','minAppVersionCode':56,'languages':out_languages}
(root/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, separators=(',', ':'))+'\n', encoding='utf-8')
shutil.rmtree(root/'.fix318-v4-delta')
shutil.rmtree(root/'.language-pack-patch-v3', ignore_errors=True)
shutil.rmtree(root/'bundles', ignore_errors=True)
print('Installed 12 direct v4 packs with 2329 keys each')
