"""Build a private 1.3 development ROM from an exact supported 1.2.5 input.

Every stage is guarded and read back. The original input and any existing output
are never overwritten. This pipeline does not publish a release or touch saves.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

from . import space


def source_snapshot():
    root = Path(__file__).resolve().parents[1]
    paths = []
    for folder in ('sgp13', 'sgp12', 'features/options', 'features/training',
                   'features/training-native', 'features/field-guide',
                   'features/trainer-strategy', 'features/plus-ui', 'features/save-ui',
                   'features/shiny', 'features/event-flags'):
        paths.extend(p for p in (root / folder).rglob('*')
                     if p.suffix in ('.py', '.c', '.h', '.json'))
    paths.extend(root / name for name in ('quality-audit/hgss_text.py',
                 'quality-audit/misura_larghezza.py', 'translation/message_codec.py',
                 'features/borsa/tools/scr_disasm.py'))
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths)}


def write_new(path, data):
    """Publish completed bytes atomically without replacing an existing file."""
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.' + path.name + '.', delete=False) as f:
            temporary = Path(f.name)
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.link(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def build(base, output, charmap, work_dir, report_path=None):
    from . import training, caught, teams, plus_ui, content, guide, title, mew, learnsets, save_ui, species, shiny, event_flags
    base, output, charmap, work_dir = map(Path, (base, output, charmap, work_dir))
    if output.exists() or (report_path and Path(report_path).exists()):
        raise FileExistsError('choose a new development output/report; existing files are preserved')
    data = base.read_bytes()
    language = space.identify(data)
    if not charmap.is_file():
        raise FileNotFoundError('the private reference charmap is required')
    command_path = charmap.parent / 'tools/py_scripts/scrcmd.json'
    commands, command_hash = mew.load_commands(command_path)
    sources = source_snapshot()
    charmap_hash = hashlib.sha256(charmap.read_bytes()).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='sgp13-', dir=work_dir) as scratch_dir:
        scratch = Path(scratch_dir)
        stages = []

        def record(name, path, details):
            stages.append({'stage': name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                           'bytes': path.stat().st_size, 'details': details})

        expanded = scratch / '01-space.nds'
        expanded.write_bytes(space.expand_rom(data))
        record('space', expanded, {'arena_base': hex(space.RESERVE_BASE), 'original_file_ids_preserved': True})
        trained = scratch / '02-training.nds'
        training_report = training.install(expanded, trained, language, charmap, scratch / 'training')
        record('training', trained, training_report)
        from sgp12.rom import Arm9
        flag_arm = Arm9(trained)
        flags_report = event_flags.install(flag_arm, language,
            training_report['symbols']['training_load'], scratch / 'event-flags')
        flagged = scratch / '02a-event-flags.nds'
        flagged.write_bytes(bytes(flag_arm.raw))
        record('event-flags', flagged, flags_report)
        marker = scratch / '03-caught.nds'
        titled, title_report = title.apply(flagged.read_bytes())
        titled_path = scratch / '02b-title.nds'
        titled_path.write_bytes(titled)
        record('title', titled_path, title_report)
        mew_data, mew_report = mew.apply(titled, language, commands)
        mew_path = scratch / '02c-mew.nds'
        mew_path.write_bytes(mew_data)
        record('mew', mew_path, mew_report)
        save_ui_data, save_ui_report = save_ui.apply(mew_data, language, charmap)
        save_ui_path = scratch / '02d-save-ui.nds'
        save_ui_path.write_bytes(save_ui_data)
        record('save-ui', save_ui_path, save_ui_report)
        marked, marker_report = caught.apply(save_ui_data)
        marker.write_bytes(marked)
        record('caught', marker, marker_report)
        strategic = scratch / '04-teams.nds'
        record('teams', strategic, teams.install(marker, strategic, scratch / 'teams'))
        balanced = scratch / '04b-learnsets.nds'
        balanced_data, learnset_report = learnsets.apply(strategic.read_bytes())
        balanced.write_bytes(balanced_data)
        record('learnsets', balanced, learnset_report)
        personal = scratch / '04c-species.nds'
        personal_data, species_report = species.apply(balanced_data)
        personal.write_bytes(personal_data)
        record('species', personal, species_report)
        styled = scratch / '05-plus-ui.nds'
        plus_report = plus_ui.install(personal, styled, language, charmap, scratch / 'plus-ui')
        record('plus-ui', styled, plus_report)
        shiny_path = scratch / '05b-shiny.nds'
        shiny_data, shiny_report = shiny.install(styled.read_bytes(), language,
            training_report['symbols'], plus_report['symbols'], scratch / 'shiny')
        shiny_path.write_bytes(shiny_data)
        record('shiny', shiny_path, shiny_report)
        resource, resource_report = content.build_from_rom(shiny_path, language, charmap)
        (scratch / 'guide-content.bin').write_bytes(resource)
        guided = scratch / '06-guide.nds'
        guide_report = guide.install(shiny_path, guided, resource, language, charmap, scratch / 'guide')
        record('guide', guided, {**guide_report, 'source_content': resource_report})
        final = scratch / '07-identity.nds'
        branded, banner_report = title.apply_banner(guided.read_bytes())
        final.write_bytes(branded)
        record('identity', final, banner_report)
        # Final compositional invariants: every untouched FAT file, both native
        # executable components, original settings IDs and all boundary guards.
        composition = verify_composition(data, final, save_ui_receipt=save_ui_report)
        composition['shiny'] = shiny.verify(final.read_bytes(), language, shiny_report, scratch / 'shiny-final')
        from sgp12.rom import Arm9
        final_arm = Arm9(final)
        composition['event_flags'] = event_flags.verify(final_arm, flags_report, scratch / 'event-flags-final')
        event_flags.guard_reservation_archives(final_arm.raw)
        for address, size, digest in ((plus_ui.EXT_BASE, plus_ui.EXT_SIZE, plus_report['extended_sha256']),
                                      (plus_ui.EXT_TEXT, plus_ui.EXT_TEXT_SIZE, plus_report['shiny_text_sha256'])):
            if hashlib.sha256(final_arm.leggi(address, size)).hexdigest() != digest:
                raise ValueError('Plus extension changed after verified installation')
        composition['plus_extension_preserved_after_later_stages'] = True
        if (sources != source_snapshot()
                or charmap_hash != hashlib.sha256(charmap.read_bytes()).hexdigest()
                or command_hash != hashlib.sha256(command_path.read_bytes()).hexdigest()):
            raise ValueError('source changed during build; output was not published')
        result = {'version': plus_ui.VERSION, 'language': language,
                  'input_sha256': hashlib.sha256(data).hexdigest(),
                  'output_sha256': stages[-1]['sha256'], 'output_bytes': stages[-1]['bytes'],
                  'stages': stages, 'composition': composition,
                  'source_sha256': sources, 'charmap_sha256': charmap_hash,
                  'scrcmd_sha256': command_hash,
                  'validation': 'build guards/readback only; runtime acceptance is separate'}
        payload = final.read_bytes()
        write_new(output, payload)
        if hashlib.sha256(output.read_bytes()).hexdigest() != result['output_sha256']:
            raise ValueError('final output readback')
        if report_path:
            write_new(report_path, (json.dumps(result, indent=2) + '\n').encode())
        return result


def verify_composition(before, after_path, *, save_ui_receipt):
    import ndspy.narc
    import ndspy.rom
    from sgp12.rom import Arm9, Rom
    from . import learnsets, species, title
    original = ndspy.rom.NintendoDSRom(before)
    updated = ndspy.rom.NintendoDSRom.fromFile(after_path)
    if len(original.files) != len(updated.files):
        raise ValueError('file IDs changed')
    allowed = {original.filenames.idOf(name) for name in
               ('a/0/0/2', 'a/0/1/2', 'a/0/1/7', 'a/0/1/8', 'a/0/2/7', 'a/0/3/2', 'a/0/3/3', 'a/0/4/6', 'a/0/8/1')}
    for oid in (1, 2, 12, 27, 30, 54, 101):
        allowed.add(Rom(before).immagine_overlay(oid)[0]['file_id'])
    changed = {i for i, (a, b) in enumerate(zip(original.files, updated.files)) if a != b}
    if changed - allowed:
        raise ValueError('unexpected changed FAT files: ' + str(sorted(changed - allowed)))
    if original.arm7 != updated.arm7 or title.update_banner(original.iconBanner) != updated.iconBanner:
        raise ValueError('unexpected ARM7/banner change')
    arm = Arm9(after_path)
    if arm.u32(space.ARENA) != space.RESERVE_BASE:
        raise ValueError('arena boundary changed')
    import struct
    if arm.leggi(space.RESERVE_BASE, 16) != struct.pack('<4I', *range(0xCA5A1900, 0xCA5A1904)):
        raise ValueError('shiny lower guard changed')
    if arm.leggi(0x023CFF00, 256) != b''.join(struct.pack('<I', 0xCA5A1A00 | i) for i in range(64)):
        raise ValueError('shiny upper guard changed')
    if arm.leggi(space.BASE, 16) != struct.pack('<4I', *range(0xCA5A1700, 0xCA5A1704)):
        raise ValueError('lower guard changed')
    expected = b''.join(struct.pack('<I', 0xCA5A1800 | i) for i in range(64))
    if arm.leggi(0x023D7F00, 256) != expected:
        raise ValueError('upper guard changed')
    for name in ('a/0/5/5', 'a/0/5/6', 'a/0/3/4'):
        if original.getFileByName(name) != updated.getFileByName(name):
            raise ValueError('trainer/evolution source archive changed')
    specification = learnsets.load_specification()
    expected_learnsets, _ = learnsets.patch_archive(
        original.getFileByName(learnsets.ARCHIVE), specification['changes'],
        specification['preimages'][learnsets.ARCHIVE])
    if updated.getFileByName(learnsets.ARCHIVE) != expected_learnsets:
        raise ValueError('learnset changes differ from the guarded specification')
    species_spec = species.load_specification()
    expected_personal, _ = species.patch_archive(
        original.getFileByName(species.ARCHIVE), species_spec['changes'],
        species_spec['preimages'][species.ARCHIVE])
    if updated.getFileByName(species.ARCHIVE) != expected_personal:
        raise ValueError('species changes differ from the guarded specification')
    # Later content/UI stages must preserve the already independently read-back
    # save correction, including its load metadata and appended message bank.
    save_rec, save_packed, save_image = Rom(arm.raw).immagine_overlay(30)
    save_entry = bytes(arm.raw[save_rec['offset_voce']:save_rec['offset_voce'] + 32])
    save_bank = ndspy.narc.NARC(updated.getFileByName('a/0/2/7')).files[40]
    for key, payload in (('overlay_sha256', save_image),
                         ('overlay_compressed_sha256', save_packed),
                         ('overlay_table_sha256', save_entry),
                         ('message_bank_sha256', save_bank)):
        if hashlib.sha256(payload).hexdigest() != save_ui_receipt[key]:
            raise ValueError('save UI changed after verified installation: ' + key)
    return {'changed_file_ids': sorted(changed), 'unchanged_files': len(original.files) - len(changed),
            'trainer_and_evolution_archives_unchanged': True, 'reserve_guards_intact': True,
            'learnsets_match_guarded_specification': True,
            'species_match_guarded_specification': True,
            'save_ui_preserved_after_later_stages': True}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--charmap', required=True, type=Path)
    parser.add_argument('--work-dir', required=True, type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args(argv)
    try:
        result = build(args.base, args.out, args.charmap, args.work_dir, args.report)
    except (ValueError, OSError) as exc:
        parser.exit(1, str(exc) + '\n')
    print(json.dumps({key: result[key] for key in ('version', 'language', 'output_sha256', 'output_bytes')}, indent=2))


if __name__ == '__main__':
    main()
