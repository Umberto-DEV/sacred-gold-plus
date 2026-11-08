"""Bounded presentation-only edit of the portable PC command's native String."""
import struct

PC_LABEL_ADDRESS = 0x023D4E70
PC_LABEL_PREIMAGE = struct.pack('<HHI8H', 6, 6, 0xB6F8D2EC,
                               0x13C, 0x1C4, 0x1DE, 0x12C, 0x153, 0x15C, 0xFFFF, 0)


def pc_label(encode):
    words = encode('R: PC ')
    if len(words) != 7 or words[-1] != 0xFFFF:
        raise ValueError('native PC label geometry')
    return struct.pack('<HHI8H', 6, 6, 0xB6F8D2EC, *words, 0)


def apply(data, locate, encode):
    at = locate(PC_LABEL_ADDRESS, 24)
    if data[at:at+24] != PC_LABEL_PREIMAGE:
        raise ValueError('portable command String preimage')
    output = bytearray(data); output[at:at+24] = pc_label(encode)
    return bytes(output)

ONBOARDING_ADDRESS, ONBOARDING_BYTES = 0x023DA800, 1008
ONBOARDING_IDS = ('p_titolo p_aiuto_a p_aiuto_b p_bloccato p_rifiutato p_suggerimento '
                  'v0_nome v1_nome v2_nome v3_nome v4_nome x_off x_on x_normale x_plus '
                  'n_norm n_fluido w_0 w_1 w_2 c_titolo c_riga1 c_riga2 c_riga1n '
                  'c_riga2n c_nota c_aiuto @cursore @vuoto').split()


def onboarding_strings(locale):
    import json
    import unicodedata
    from .catalogue import HERE, _pairs
    data = json.loads((HERE/'locales'/locale/'native.json').read_text(), object_pairs_hook=_pairs)
    if (data.keys() != {'schema','language','strings'} or data['schema'] != 1
            or data['language'] != locale or set(data['strings']) != set(ONBOARDING_IDS[:-2])
            or any(not isinstance(v,str) for v in data['strings'].values())):
        raise ValueError('native onboarding catalogue')
    return {k:unicodedata.normalize('NFC',v) for k,v in data['strings'].items()} | {'@cursore':'→','@vuoto':''}


def pack_onboarding(strings, encode, measure):
    output, seen = bytearray(58), {}
    for index, key in enumerate(ONBOARDING_IDS):
        words = encode(strings[key])
        # The live Continue page has 204px after its20px left inset; choices
        # reserve114px for the name and76px for their right-aligned value.
        limit = 114 if key.startswith('v') else 76 if key in ONBOARDING_IDS[11:20] else 204
        if len(words)>64 or words[-1]!=65535 or measure(words)>limit:
            raise ValueError('native onboarding text geometry: '+key)
        raw = struct.pack('<%dH'%len(words),*words)
        if raw not in seen:
            seen[raw]=len(output);output.extend(raw)
        struct.pack_into('<H',output,index*2,seen[raw])
    if len(output)>ONBOARDING_BYTES:
        raise ValueError('native onboarding1008-byte budget')
    return bytes(output)+bytes(ONBOARDING_BYTES-len(output))


def apply_onboarding(data,locate,locale,encode,measure,expected_sha256):
    import hashlib
    at=locate(ONBOARDING_ADDRESS,ONBOARDING_BYTES)
    if hashlib.sha256(data[at:at+ONBOARDING_BYTES]).hexdigest()!=expected_sha256:
        raise ValueError('native onboarding bank preimage')
    bank=pack_onboarding(onboarding_strings(locale),encode,measure)
    output=bytearray(data);output[at:at+ONBOARDING_BYTES]=bank
    return bytes(output)

SUMMARY_ADDRESS, SUMMARY_BYTES = 0x01FF9B70, 1104
SUMMARY_LIMITS = ([160,224,224,224]*3)+[224]*3+[78,70,62,62,62,96]+[24]*3


def summary_strings(locale):
    import json
    import unicodedata
    from .catalogue import HERE, _pairs
    data=json.loads((HERE/'locales'/locale/'summary.json').read_text(),object_pairs_hook=_pairs)
    if (data.keys()!={'schema','language','strings'} or data['schema']!=1 or data['language']!=locale
            or set(data['strings'])!={f's:{i}' for i in range(24)}
            or any(not isinstance(v,str) for v in data['strings'].values())):
        raise ValueError('native Summary guide catalogue')
    return [unicodedata.normalize('NFC',data['strings'][f's:{i}']) for i in range(24)]


def pack_summary(lines,encode,measure):
    if len(lines)!=24:raise ValueError('native Summary guide line count')
    output,seen=bytearray(96),{}
    for index,(text,limit) in enumerate(zip(lines,SUMMARY_LIMITS)):
        words=encode(text);width=measure(words)
        if words[-1]!=65535 or any(not 0<w<=509 for w in words[:-1]) or width>limit:
            raise ValueError('native Summary guide line geometry: '+str(index))
        raw=struct.pack('<%dH'%len(words),*words)
        if raw not in seen:seen[raw]=len(output);output.extend(raw)
        struct.pack_into('<H',output,index*2,seen[raw]);struct.pack_into('<H',output,48+index*2,width)
    if len(output)>SUMMARY_BYTES:raise ValueError('native Summary guide1104-byte budget')
    return bytes(output)+bytes(SUMMARY_BYTES-len(output))


def apply_summary(data,locate,locale,encode,measure,expected_sha256):
    import hashlib
    at=locate(SUMMARY_ADDRESS,SUMMARY_BYTES)
    if hashlib.sha256(data[at:at+SUMMARY_BYTES]).hexdigest()!=expected_sha256:
        raise ValueError('native Summary guide bank preimage')
    output=bytearray(data);output[at:at+SUMMARY_BYTES]=pack_summary(summary_strings(locale),encode,measure)
    return bytes(output)
