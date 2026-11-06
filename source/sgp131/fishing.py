"""SG-11: zero means no night override; keep native encounter/RNG/save contracts.

Only two existing Thumb function windows change. Both overlays retain their
logical lengths and original compressed FAT slots. The encounter producer
returns an ArchiveDelta for the UI's one append before its cartridge seeds.
"""
import hashlib
import struct

ARCHIVE = 'a/0/3/7'
PRODUCER = 'fishing-encounters'
ARCHIVE_SHA256 = 'a66f72f48341a1ec3131b521641ab6e671ad890d07676131b00fed2704ec3d4d'
# map -> (encounter bank, reviewed fishSwarm species). No retail nightFish.
BINDINGS = {20: (92, 369), 36: (8, 211), 46: (59, 223), 73: (5, 340)}
SWARMS = {bank: species for bank, species in BINDINGS.values()}
OVERLAYS = {
    2: (0x02245B80, 0xE2A0, 0x02246AD4, 0x02246B00,
        '10426a4a3fe5de0a90c08a5454bbb0847da3b5ee125a1423101f1415aa054c48'),
    101: (0x021E7740, 0x13BC0, 0x021F2E04, 0x021F2E74,
          '326a9f1218d34ef131cc8b554a4831cb5d2b0451b956e233a76d18e388a267af'),
}
# r4=encounters/r7=rod/r5=slots and Super-before-Good keep overlay2's
# canonical BLZ stream within its original slot, including after Lullaby.
WINDOWS = {
    2: (0x02246AD4,
        bytes.fromhex('70b5051c0c1c161ccdf59efec01e01280ad8012c03d1c0352888b06170bd022c02d1c0352888b06070bd0000'),
        bytes.fromhex('b0b5041c0f1c151ccdf59efec01e01280ad8c0342088002806d0022f01d1a860b0bd012f00d1a861b0bd0000')),
    # Reclaim two bytes by an equivalent day1/night2/default-morning land
    # switch in this same function. No entry/exit address or caller changes.
    101: (0x021F2E24,
          bytes.fromhex('0b2d10d1022c03d130a8018820a841842cf686ff0521fff6aeed25a88900023031b0405a78bd002c08d0012c02d0022c02d003e00bac02e011ac00e005ac'),
          bytes.fromhex('0b2d11d1022c04d121a8818f002900d0c1832cf685ff0521fff6aced25a88900023031b0405a78bd012c02d0022c02d003e00bac03e011ac01e005acc046')),
}


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def _need(ok, message):
    if not ok:
        raise ValueError(message)


def _guard(image, overlay):
    _need(overlay in OVERLAYS, 'fishing overlay ID')
    base, size, start, end, pin = OVERLAYS[overlay]
    site, old, new = WINDOWS[overlay]
    _need(type(image) is bytes and len(image) == size, 'fishing overlay size/type')
    _need(len(old) == len(new), 'fishing replacement span')
    _need(image[site-base:site-base+len(old)] == old, 'fishing preimage changed/already patched')
    _need(_sha(image[start-base:end-base]) == pin, 'fishing function preimage hash')


def patch_overlay(image, overlay):
    image = bytes(image)
    _guard(image, overlay)
    base = OVERLAYS[overlay][0]
    site, old, new = WINDOWS[overlay]
    at = site-base
    return image[:at] + new + image[at+len(old):]


def verify_images(before, after, overlay):
    """Independent readback: fixed replacement and its entire complement."""
    _guard(before, overlay)
    base, size, *_ = OVERLAYS[overlay]
    site, old, new = WINDOWS[overlay]
    at = site-base
    _need(type(after) is bytes and len(after) == size, 'fishing output overlay size/type')
    _need(after[at:at+len(new)] == new, 'fishing replacement instructions')
    _need(before[:at] == after[:at] and before[at+len(old):] == after[at+len(new):],
          'fishing bytes outside instruction window')


def _read(data, overlay):
    """Decode using both ndspy and the independently implemented Rom reader."""
    import ndspy.codeCompression
    from sgp12.blz import ndspy_decomprimi_sicuro
    from sgp12.rom import Rom
    base, size, *_ = OVERLAYS[overlay]
    fat, fat_bytes = struct.unpack_from('<II', data, 0x48)
    y9, y9_bytes = struct.unpack_from('<II', data, 0x50)
    _need(y9_bytes >= (overlay+1)*32 and y9+y9_bytes <= len(data), 'fishing y9 bounds')
    row = struct.unpack_from('<8I', data, y9+overlay*32)
    _need(row[0] == overlay and row[1:4] == (base,size,0) and row[6] == overlay,
          'fishing overlay placement')
    _need(fat_bytes >= (overlay+1)*8 and fat+fat_bytes <= len(data), 'fishing FAT bounds')
    start,end = struct.unpack_from('<II',data,fat+overlay*8)
    _need(0 <= start < end <= len(data) and row[7]>>24&1
          and row[7]&0xFFFFFF == end-start, 'fishing compressed slot')
    encoded = bytes(data[start:end])
    image = bytes(ndspy_decomprimi_sicuro(encoded, size))
    _need(image == Rom(data).immagine_overlay(overlay)[2], 'fishing decoders disagree')
    return start,end,image


def apply(data, language):
    from sgp12.blz import blz_comprimi_ottimo
    _need(type(data) is bytes and language in ('EN','IT'), 'fishing arguments')
    out = data
    for overlay in OVERLAYS:
        start,end,image = _read(out,overlay)
        new = patch_overlay(image,overlay)
        stream = blz_comprimi_ottimo(new,bersaglio=end-start)
        _need(len(stream) == end-start, 'fishing overlay does not fit original compressed slot')
        out = out[:start]+stream+out[end:]
    receipt = {'stage':'legacy-fishing','language':language,
               'input_sha256':_sha(data),'output_sha256':_sha(out)}
    receipt['verification'] = verify(data,out,receipt)
    return out,receipt


def verify(before, after, receipt):
    """Re-read both streams, logical complements, whole cartridge complement."""
    from sgp12.blz import blz_comprimi_ottimo
    _need(len(before) == len(after), 'fishing cartridge length')
    spans=[]
    for overlay in OVERLAYS:
        start,end,old = _read(before,overlay)
        ns,ne,new = _read(after,overlay)
        _need((start,end) == (ns,ne), 'fishing cartridge geometry')
        verify_images(old,new,overlay)
        _need(after[start:end] == blz_comprimi_ottimo(new,bersaglio=end-start),
              'fishing noncanonical stream')
        spans.append((start,end))
    cursor=0
    for start,end in sorted(spans):
        _need(before[cursor:start] == after[cursor:start], 'fishing cartridge complement')
        cursor=end
    _need(before[cursor:] == after[cursor:], 'fishing cartridge tail complement')
    _need(isinstance(receipt,dict) and receipt.get('language') in ('EN','IT')
          and receipt.get('input_sha256') == _sha(before)
          and receipt.get('output_sha256') == _sha(after), 'fishing receipt identity')
    return {'ok':True,'slots':[list(s)for s in spans],
            'container_unchanged':True,'decoders_agree':True}


def patch_member(before, index):
    _need(type(before) is bytes and type(index) is int and 0 <= index < 142,
          'fishing member arguments')
    _need(len(before) == 192, 'fishing only truncated members may be replaced')
    return before + struct.pack('<HH',0,SWARMS.get(index,0))


def check_member(index, before, after, language):
    """Independent tail/prefix check, with no writer call or retail copying."""
    _need(language in ('EN','IT') and type(index) is int and 0 <= index < 142,
          'fishing checker arguments')
    _need(type(before) is bytes and type(after) is bytes
          and len(before) == 192 and len(after) == 196, 'fishing member lengths/type')
    _need(after[:192] == before, 'fishing original encounter fields changed')
    night,swarm = struct.unpack_from('<HH',after,192)
    _need(night == 0 and swarm == {5:340,8:211,59:223,92:369}.get(index,0),
          'fishing forbidden tail values')


def derive_fishing_encounters(base, language, charmap=None):
    import ndspy.rom
    from sgp131 import archives
    from sgp131.ui_verify import Image
    _need(type(base) is bytes and language in ('EN','IT'), 'fishing producer arguments')
    rom=ndspy.rom.NintendoDSRom(base)
    fid=rom.filenames.idOf(ARCHIVE)
    raw=bytes(rom.files[fid])
    _need(_sha(raw) == ARCHIVE_SHA256, 'fishing encounter archive preimage')
    old=archives.members(raw)
    _need(len(old) == 142 and sum(len(b)==192 for b in old) == 130
          and sum(len(b)==196 for b in old) == 12, 'fishing member census')
    view=Image(base)
    for map_id,(bank,_) in BINDINGS.items():
        _need(view.arm(0x020F6BE0+24*map_id,1) == bytes([bank]), 'fishing map/bank binding')
    # The native table is independently read, not inferred from map names.
    pointer=struct.unpack('<I',view.arm(0x02097F94,4))[0]
    table=struct.unpack('<40H',view.arm(pointer,80))
    fish_maps={table[i]for i in range(0,40,2)if table[i+1]==2}
    _need(fish_maps == set(BINDINGS), 'fishing native outbreak bindings')
    replacements={i:patch_member(b,i)for i,b in enumerate(old)if len(b)==192}
    _need(set(SWARMS) <= set(replacements), 'fishing swarm members must be truncated')
    return archives.ArchiveDelta.make(ARCHIVE,fid,PRODUCER,raw,replacements,
                                     {'archive_sha256':ARCHIVE_SHA256})


PRODUCERS={PRODUCER:derive_fishing_encounters}
CHECKERS={PRODUCER:check_member}
