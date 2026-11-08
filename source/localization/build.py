"""Compose reviewed retail presentation around an exact common Plus executable.

Only explicit resource members, accent rows and presentation descriptors may
change. Regional executables, scripts, game identity and save layouts are never
transplanted. EN/IT continue to use their guarded sgp131 build chain.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib

from ndspy.narc import NARC
from ndspy.rom import NintendoDSRom
from sgp131 import guide_content, ui, ui_compile, ui_copy, ui_resource
from translation.message_codec import Bank, unpack_name
from translation.rom_container import append_files
from translation.ui_resource import normalize_donor
from . import badges, keyboard, native_text, summary_labels
from . import geometry as field_geometry
from .catalogue import HERE, load_strings, ui_catalogue
from .guide import compile_guide
from .inventory import LANGUAGES, check_layout, identify, sha
from .messages import _TEXT, translate_messages

ASSET_SHA256 = '96490ff4d596a9c21f4a8d8ac7a42a4c7c57834bbfbcd8a7ef0b2a0aed14e102'


def _retail(data, locale):
    registry = json.loads(LANGUAGES.read_text())['languages']
    if identify(data, {k: row['retail'] for k, row in registry.items()}) != locale:
        raise ValueError('retail locale mismatch')
    check_layout(data)


def read_recipe(locale):
    if locale not in ('FR', 'ES', 'DE'):
        raise ValueError('regional composition supports FR/ES/DE only')
    recipe = json.loads((HERE / 'locales' / locale / 'recipe.json').read_text())
    if recipe['schema'] != 1 or recipe['language'] != locale:
        raise ValueError('recipe schema/locale')
    return recipe


def graphics(core, donor, recipe):
    """Apply guarded member substitutions, retaining every unlisted member."""
    replacements, proof = {}, []
    for row in recipe['graphics']:
        path, member = row['file'], row['member']
        if (path in ('a/0/4/6', 'a/1/1/2')
                or path=='a/0/6/8' and member in (12,13,14,35,57,58,65,66,123)
                or path=='a/0/0/8' and member in (46,61,62,63,74,236)):
            raise ValueError('protected archive in graphical recipe')
        before = NARC(core.getFileByName(path))
        native = NARC(donor.getFileByName(path))
        if len(before.files) != row['core_member_count'] or len(native.files) != row['donor_member_count']:
            raise ValueError('graphical archive member-count guard')
        if sha(before.files[member]) != row['before_sha256'] or sha(native.files[member]) != row['donor_sha256']:
            raise ValueError('graphical member preimage: ' + path + ':' + str(member))
        for dependency in row.get('preserve_identical_dependencies',[]):
            index=dependency['member']; expected=dependency['sha256']
            if sha(before.files[index])!=expected or sha(native.files[index])!=expected:
                raise ValueError('graphical companion dependency guard')
        archive = replacements.setdefault(path, before)
        if any(p['file'] == path and p['member'] == member for p in proof):
            raise ValueError('duplicate graphical recipe member')
        value = normalize_donor(before.files[member], native.files[member], row.get('transform'))
        archive.files[member] = value
        proof.append(dict(file=path, member=member, sha256=sha(value)))
    return {path: archive.save() for path, archive in replacements.items()}, proof


def compose(core, reference, donor, locale, charmap):
    """Return immutable ROM bytes and a static receipt; runtime acceptance is separate."""
    recipe = read_recipe(locale)
    if type(core) is not bytes or sha(core) != recipe['core_sha256'] or len(core) != recipe['core_bytes']:
        raise ValueError('exact reviewed common core required')
    check_layout(core); _retail(reference, 'EN'); _retail(donor, locale)
    if sha(Path(charmap).read_bytes()) != guide_content.CHARMAP_SHA256:
        raise ValueError('charmap identity')
    if core[:16] != b'POKEMON SG\0\0IPKE':
        raise ValueError('common Plus game identity')
    chars, commands = _TEXT.load_charmap(charmap)
    codec = ui_compile.module(ui_compile.SOURCE / 'features/options/tools/codifica_testo.py', 'localization_codec')
    table, _ = codec.carica_charmap(charmap)
    encode = lambda text: codec.codifica(text, table)
    game, retail, native = map(NintendoDSRom, (core, reference, donor))
    strings = load_strings(locale)
    messages, message_receipt = translate_messages(game.getFileByName('a/0/2/7'), retail.getFileByName('a/0/2/7'),
                                                   native.getFileByName('a/0/2/7'), strings, chars, commands)
    field_context = field_geometry.context_from_rom(core,charmap,messages=messages)
    messages, message_receipt = translate_messages(game.getFileByName('a/0/2/7'),retail.getFileByName('a/0/2/7'),
        native.getFileByName('a/0/2/7'),strings,chars,commands,
        layout=lambda bank,text,index:field_geometry.layout(bank,text,field_context,message=index))
    presented = NintendoDSRom(core)
    presented.setFileByName('a/0/2/7', messages)
    guide, guide_receipt = compile_guide(presented.save(), locale, strings, charmap)
    messages, guide_offset = ui._replace_guide(messages, guide)
    font = bytes(NARC(game.getFileByName('a/0/1/6')).files[0])
    font_metrics = ui_compile.module(ui_compile.SOURCE/'quality-audit/misura_larghezza.py','native_copy_metrics')
    native_widths = font_metrics.extract_width_table(font)
    measure = lambda words: font_metrics.measure(native_widths, words)['max_width_px']
    widths = font[struct.unpack_from('<I', font, 4)[0]:]
    assets = bytes(NARC(game.getFileByName('a/0/3/8')).files[51][128:48448])
    if sha(assets) != ASSET_SHA256:
        raise ValueError('shared native UI assets')
    authored, geometry = ui_copy.encode_catalogue(ui_catalogue(), locale, encode, widths)
    names = Bank(NARC(messages).files[237]).words
    species = {i: tuple(unpack_name(names[i])) for i in range(1, 494)}
    member = ui_resource._pack_member(locale, assets, species, authored, zlib.crc32(widths))
    frame_source = retail.getFileByName('a/0/3/8')
    frames = ui_resource._append_member(frame_source, member)
    uir_receipt = ui_resource._receipt(frames, locale, assets, species, authored, zlib.crc32(widths))
    replacements, graphic_receipt = graphics(game, native, recipe)
    for (path, index), value in badges.localize_badges(core, locale).items():
        archive = NARC(replacements.get(path, game.getFileByName(path)))
        archive.files[index] = value
        replacements[path] = archive.save()
        graphic_receipt.append(dict(file=path, member=index, sha256=sha(value), authored=True))
    replacements.update({'a/0/2/7': messages, 'a/0/3/8': frames})
    output, extents = append_files(core, replacements)
    locate = ui._arm_map(core)
    output = keyboard.apply(output, locate, locale, encode)
    output = native_text.apply(output, locate, encode)
    output = native_text.apply_onboarding(output,locate,locale,encode,measure,recipe['native_bank_sha256'])
    output = native_text.apply_summary(output,locate,locale,encode,measure,recipe['summary_bank_sha256'])
    output = bytearray(summary_labels.apply(output,locate,locale))
    struct.pack_into('<I', output, locate(0x023D7B60 + 20 * 4, 4), len(output))
    output[locate(0x023D7BC0, 64):locate(0x023D7BC0, 64)+64] = bytes.fromhex(uir_receipt['config_hex'])
    archive_extent = next(row for row in extents if row['file'] == 'a/0/2/7')
    cats, entries = struct.unpack_from('<HH', guide, 8)
    language = ui_resource.LANGUAGE_IDS[locale]
    config = [0x31435247, 1, language, 0, 156, archive_extent['new_start'], archive_extent['new_end'], len(output),
              len(messages), guide_offset, len(guide), zlib.crc32(guide), cats, entries, 0, 0]
    struct.pack_into('<16I', output, locate(0x023D7C00, 64), *config)
    output = bytes(output)
    from .verify import verify
    verification = verify(core, output, donor, reference, locale, recipe, charmap)
    return output, dict(schema=1, language=locale, core_sha256=sha(core), donor_sha256=sha(donor),
                        output_sha256=sha(output), output_bytes=len(output), messages=message_receipt,
                        guide=guide_receipt, ui=uir_receipt, geometry=geometry, graphics=graphic_receipt,
                        replaced_files=extents, verification=verification, source_sha256={str(path.relative_to(HERE.parent)):sha(path.read_bytes()) for path in sorted([HERE/name for name in ('__init__.py','build.py','verify.py','inventory.py','catalogue.py','messages.py','guide.py','keyboard.py','native_text.py','summary_labels.py','badges.py','geometry.py','languages.json')]+[HERE/'locales'/locale/(name+'.json') for name in ('messages','ui','guide','evolution','native','summary','recipe')])},
                        status='static-verified')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('core', 'reference', 'donor', 'charmap', 'output', 'receipt'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--language', choices=('FR', 'ES', 'DE'), required=True)
    args = parser.parse_args()
    paths = [getattr(args, k).resolve() for k in ('core', 'reference', 'donor', 'output', 'receipt')]
    if len(set(paths)) != len(paths) or args.output.exists() or args.receipt.exists():
        raise ValueError('inputs/outputs must be distinct; outputs must be new')
    data, report = compose(args.core.read_bytes(), args.reference.read_bytes(), args.donor.read_bytes(), args.language, args.charmap)
    with args.output.open('xb') as handle: handle.write(data)
    with args.receipt.open('x') as handle: json.dump(report, handle, indent=2); handle.write('\n')
    print(report['output_sha256'], report['output_bytes'], args.language)


if __name__ == '__main__': main()
