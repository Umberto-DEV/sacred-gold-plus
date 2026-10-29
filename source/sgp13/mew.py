"""Keep each incoming Mew movement inside its owning script task's lifetime."""
from bisect import bisect_right
import hashlib
import importlib.util
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
MEMBER = 115
SITES = (191, 260, 325)
MEMBER_SHA256 = {
    'EN': 'd55e74547e32bc1f89ae2547a4edb6de4b9d64a6b28097a4f205bfa66c26ff08',
    'IT': 'd55e74547e32bc1f89ae2547a4edb6de4b9d64a6b28097a4f205bfa66c26ff08',
}
METADATA_SHA256 = 'fbfbf438104cfc3735c3144730ed711bb882fca370a8de680db5c1d39ffaca5a'
_DECODER = None


def decoder():
    """Use the existing public decoder, with caller-supplied command metadata."""
    global _DECODER
    if _DECODER is None:
        path = ROOT / 'features/borsa/tools/scr_disasm.py'
        spec = importlib.util.spec_from_file_location('mew_script_decoder', path)
        _DECODER = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_DECODER)
    return _DECODER


def load_commands(path):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError('the pinned reference tools/py_scripts/scrcmd.json is required')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != METADATA_SHA256:
        raise ValueError('Mew script metadata SHA-256 does not match the pinned reference')
    return decoder().Comandi(path), digest


def _decode(raw, commands):
    member = decoder().Membro(MEMBER, raw, commands).cammina()
    if (not member.header_valido or not member.entry
            or any(entry < member.header_end for entry in member.entry)
            or member.errori or member.riassembla() != (True, None)):
        raise ValueError('Mew script/movement decoding failed: ' + '; '.join(member.errori))
    return member


def _movement_end(raw, start):
    cursor = start
    while cursor + 2 <= len(raw):
        # FE has no repeat-count operand. A terminator at the final two bytes
        # is valid; reading a mandatory four-byte pair would overrun it.
        if struct.unpack_from('<H', raw, cursor)[0] == 0xFE:
            return cursor + 2
        if cursor + 4 > len(raw):
            break
        cursor += 4
    raise ValueError('Mew movement has no complete FE terminator')


def insert_waits(raw, commands, sites):
    """Relocate the original member once; never insert into already shifted data."""
    sites = tuple(sites)
    if not sites or sites != tuple(sorted(set(sites))):
        raise ValueError('Mew insertion sites must be ordered and unique')
    old = _decode(raw, commands)
    if commands.nome(95) != 'WaitMovement' or commands.arg_list(95, None) != ([], None):
        raise ValueError('Mew WaitMovement metadata does not match')
    for site in sites:
        previous = [ins for ins in old.istruzioni.values() if ins.fine == site]
        if site not in old.istruzioni or len(previous) != 1 or previous[0].nome != 'ApplyMovement':
            raise ValueError('Mew insertion must follow an incoming ApplyMovement')
    movements = {start: _movement_end(raw, start) for start in old.dati_movimento}
    shift = lambda offset: offset + 2 * bisect_right(sites, offset)
    chunks = []
    cursor = 0
    for site in sites:
        chunks.extend((raw[cursor:site], b'\x5f\0'))
        cursor = site
    chunks.append(raw[cursor:])
    result = bytearray(b''.join(chunks))
    for index, entry in enumerate(old.entry):
        struct.pack_into('<I', result, 4 * index, (shift(entry) - (4 * index + 4)) & 0xFFFFFFFF)
    sd = decoder()
    for ins in old.istruzioni.values():
        cursor = ins.off + 2
        for value, kind in zip(ins.args, ins.tipi):
            size = kind if isinstance(kind, int) else sd.ARG_SIZES[kind]
            if kind in sd.RELATIVE:
                destination = (value + cursor + size) & 0xFFFFFFFF
                relative = (shift(destination) - (shift(cursor) + size)) & 0xFFFFFFFF
                struct.pack_into('<I', result, shift(cursor), relative)
            cursor += size
    result = bytes(result)
    new = _decode(result, commands)
    if new.entry != [shift(entry) for entry in old.entry] or len(new.istruzioni) != len(old.istruzioni) + len(sites):
        raise ValueError('Mew script entry/instruction readback')
    for ins in old.istruzioni.values():
        other = new.istruzioni.get(shift(ins.off))
        if other is None or (other.op, other.tipi) != (ins.op, ins.tipi):
            raise ValueError('Mew original opcode readback')
        if other.rami != [(index, shift(destination), kind) for index, destination, kind in ins.rami]:
            raise ValueError('Mew relative target readback')
        if any(a != b for a, b, kind in zip(ins.args, other.args, ins.tipi) if kind not in sd.RELATIVE):
            raise ValueError('Mew original argument readback')
    for site in sites:
        if new.istruzioni[shift(site) - 2].nome != 'WaitMovement':
            raise ValueError('Mew wait readback')
    if new.dati_movimento != {shift(start) for start in movements}:
        raise ValueError('Mew movement target readback')
    for start, end in movements.items():
        if result[shift(start):shift(start) + end - start] != raw[start:end]:
            raise ValueError('Mew movement bytes readback')
    return result


def patch_member(raw, language, commands):
    if language not in MEMBER_SHA256:
        raise ValueError('unsupported Mew script language')
    if hashlib.sha256(raw).hexdigest() != MEMBER_SHA256[language]:
        raise ValueError('Mew member115 preimage does not match; foreign/already patched input')
    return insert_waits(raw, commands, SITES)


def apply(data, language, commands):
    import ndspy.rom
    import ndspy.narc
    from .resources import append_file
    rom = ndspy.rom.NintendoDSRom(data)
    file_id = rom.filenames.idOf('a/0/1/2')
    archive = ndspy.narc.NARC(rom.files[file_id])
    original = bytes(archive.files[MEMBER])
    replacement = patch_member(original, language, commands)
    archive.files[MEMBER] = replacement
    encoded = archive.save()
    if ndspy.narc.NARC(encoded).files != archive.files:
        raise ValueError('Mew NARC readback')
    result = append_file(data, file_id, encoded)
    check = ndspy.rom.NintendoDSRom(result)
    if len(check.files) != len(rom.files) or any(a != b for index, (a, b) in enumerate(zip(rom.files, check.files)) if index != file_id):
        raise ValueError('Mew changed an unrelated NitroFS file')
    if (check.arm9, check.arm7, check.iconBanner) != (rom.arm9, rom.arm7, rom.iconBanner):
        raise ValueError('Mew changed native executable/banner data')
    if ndspy.narc.NARC(check.files[file_id]).files != archive.files:
        raise ValueError('Mew installed member readback')
    return result, {'member': MEMBER, 'wait_sites_original': list(SITES),
                    'input_member_sha256': hashlib.sha256(original).hexdigest(),
                    'output_member_sha256': hashlib.sha256(replacement).hexdigest(),
                    'input_member_bytes': len(original), 'output_member_bytes': len(replacement),
                    'other_files_and_native_executables_unchanged': True}
