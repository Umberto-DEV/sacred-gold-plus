#!/usr/bin/env python3
"""Read the forty-byte SDK Init leaf in exact retail/base/V4/r4 inputs, no CPU.

The optional recovered ELF is read independently by section arithmetic. Reports
contain hashes/addresses only and must stay outside source.
"""
from pathlib import Path
import argparse, gc, importlib.util, json, mmap, struct

spec = importlib.util.spec_from_file_location('fs_init_lineage_parent', Path(__file__).with_name('attribuisci_fs_init.py'))
H = importlib.util.module_from_spec(spec); spec.loader.exec_module(H)
P, need, sha = H.P, H.need, H.sha


def object_text(path):
    raw = path.read_bytes()
    need(raw[:7] == b'\x7fELF\x01\x01\x01' and len(raw) >= 52, 'ELF32 little endian required')
    header = struct.unpack_from('<HHIIIIIHHHHHH', raw, 16)
    need(header[:2] == (1, 40) and header[10] == 40, 'relocatable ARM ELF required')
    offset, count, strings = header[5], header[11], header[12]
    need(offset >= 52 and count > 0 and strings < count and offset + count * 40 <= len(raw), 'ELF section bounds')
    sections = [struct.unpack_from('<10I', raw, offset + 40 * i) for i in range(count)]
    def content(s):
        need(s[4] + s[5] <= len(raw), 'ELF content bounds')
        return raw[s[4]:s[4]+s[5]]
    names = content(sections[strings]); selected = []
    for i, section in enumerate(sections):
        need(section[0] < len(names), 'ELF section name bounds')
        end = names.find(b'\0', section[0]); need(end >= 0, 'ELF section name terminator')
        if names[section[0]:end] == b'.text': selected.append((i, section))
    need(len(selected) == 1, 'single ELF text required')
    index, section = selected[0]
    need(not any(s[1] in (4, 9) and s[7] == index and s[5] for s in sections), 'no text relocations allowed')
    result = content(section)
    need(len(result) == 40 and sha(result) == H.INIT_SHA, 'ELF recovered Init body differs')
    return result


def analyze(paths, language, recipe_object=None):
    rows = []; recovered = object_text(recipe_object) if recipe_object is not None else None
    for role in ('retail', 'base11', 'v4', 'r4'):
        model = P.G.S.SHARED.read_current(paths[role], language) if role == 'r4' else P.G.S.SHARED.read_image(paths[role], language, role)
        with paths[role].open('rb') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as raw:
            body = P.G.piece(model['segments'], H.ENTRY, 40); physical = None
            if role in ('v4', 'r4'):
                view = P.G.S.SHARED.gifts_audit.Arm9View(raw)
                need(view.read(H.ENTRY, 40) == body, 'raw ARM9/decoded section disagreement')
                physical = hex(view.offset(H.ENTRY, 40))
            rows.append(dict(role=role, input=model['record'], ram=hex(H.ENTRY), bytes=40,
                sha256=sha(body), rom_offset=physical, equal_to_current=sha(body) == H.INIT_SHA,
                equal_to_recipe=None if recovered is None else body == recovered))
        del model; gc.collect(); H.R.W.require_host_budget()
    need(rows[-1]['equal_to_current'], 'current Init identity differs')
    return dict(schema='native-fs-init-lineage-v1', language=language, images=rows,
        tool_sha256=sha(Path(__file__).read_bytes()), verifier_sha256=sha(Path(H.__file__).read_bytes()),
        recipe_object_sha256=None if recipe_object is None else sha(recipe_object.read_bytes()),
        cpu_executed=False, compiler_invoked=False,
        limits=['Only this forty-byte leaf at the stated candidate address; differing revisions remain unattributed',
                'Legacy compressed/autoload code uses decoded sections; no direct physical offset inferred',
                'No original native build reconstruction, historical activation, FS Open/card/error-policy proof'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('retail', 'base', 'v4', 'rom', 'json'): parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--language', choices=('EN', 'IT'), required=True)
    parser.add_argument('--recipe-object', type=Path)
    args = parser.parse_args()
    try:
        need(not args.json.exists() and not args.json.is_symlink() and P.SOURCE not in args.json.resolve().parents,
             'fresh private output outside source required')
        result = analyze(dict(retail=args.retail, base11=args.base, v4=args.v4, r4=args.rom), args.language, args.recipe_object)
        payload = (json.dumps(result, indent=2) + '\n').encode(); need(len(payload) <= 1024**2, 'lineage report budget')
        args.json.parent.mkdir(parents=True, exist_ok=True)
        with args.json.open('xb') as f: f.write(payload)
    except ValueError as error: parser.exit(2, str(error) + '\n')
    print(args.language, 'native Init lineage read without CPU')


if __name__ == '__main__': main()
