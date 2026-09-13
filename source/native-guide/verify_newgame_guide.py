#!/usr/bin/env python3
"""Native Oak controls, original naming and first SAVE from a no-SRAM boot."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import struct
from run_newgame_guide import ROOT, PREFIX, capture, current_build, loaded_code, run_new, sha, require
from newgame_oracle import reader, heap, oak, font, saved_fields, field_hashes, identity

OAK_MAGIC = 0x4F414B31


def position(path):
    view, word, _ = reader(path)
    base = word(0x021D2228)
    header = struct.unpack('<IIIHH', view(base+0x23014+5*16, 16))
    require(header[:2] == (5, 132), 'Location array schema differs')
    return struct.unpack('<5I', view(base+16+header[2], 20))


def continuation():
    historical = (ROOT / 'runtime/inputs/newgame-keyboard.script').read_text()
    text = historical[historical.index('touch 128 154 3\n'):]
    # The historical accent-row sequence leaves EN blank, causing Oak's
    # ordinary random default name. Explicit native TEST keys make the name
    # comparable across fresh runs without changing the game's RNG.
    text = text[:text.index('capture keyboard.ppm\n')+len('capture keyboard.ppm\n')]
    # The inherited introduction leaves one A in IT, while EN is empty.
    # Native Backspace removes it; Backspace on empty EN remains on keyboard.
    text += ('tap B 4 30\ntouch 178 119 4\nrun 30\ntouch 98 100 4\nrun 30\n'
             'touch 162 119 4\nrun 30\ntouch 178 119 4\nrun 30\n')
    text += capture('typed-name') + 'touch 216 72 4\nrun 180\n'
    text += capture('name-ready') + 'touch 190 60 4\nrun 180\n' + capture('name-yes')
    for i in range(48):
        text += 'tap A 4 180\n'
        if (i+1) % 8 == 0:
            text += capture(f'post-name-{i+1}')
    text += 'run 600\n' + capture('world')
    # Native local-field coordinates: start map64 (6,6), staircase entrance
    # map64 (3,4), left into warp -> map63. No RAM teleport or imported save.
    text += 'run 48 LEFT\nrun 32 UP\nrun 16 LEFT\nrun 600 NONE\n' + capture('mother')
    text += 'tap A 4 180\n' * 32
    text += capture('save-ready') + 'sram before-first-save.sav\n'
    text += 'touch 120 75 4\nrun 600\n' + capture('save-prompt')
    text += 'tap A 8 600\n' + capture('save-progress')
    text += 'tap A 8 1600\n' + capture('saved') + 'sram first-save.sav\nstatus\nquit\n'
    return text


def scenario(mode, baseline_delay=0):
    script = PREFIX + 'run 30\n'
    for i in range(12):
        script += capture(f'entry-{i}') + 'run 1\n'
    script += 'run 180\n' + capture('panel1')
    if mode == 'baseline':
        return script + f'run {240+baseline_delay}\n' + capture('continuation') + continuation()
    if mode == 'full':
        script += 'run 120 A\n' + capture('panel2-held') + 'run 4 NONE\n'
        script += 'tap LEFT+RIGHT+A 4 30\n' + capture('back1')
        script += 'touch 16 160 4\nrun 30\n' + capture('disabled-back')
        for x, y in [(95,168), (160,168), (128,159), (128,176)]:
            script += f'touch {x} {y} 4\nrun 12\n'
        script += capture('next-edges') + 'touch 96 160\nrun 100\n' + capture('panel2')
        script += 'release\nrun 4 NONE\ntap RIGHT 4 30\n' + capture('panel3')
        script += 'touch 16 160 4\nrun 30\n' + capture('touch-back')
        script += 'touch 128 168 4\nrun 30\n' + capture('touch-forward')
        script += 'touch 16 160\nrun 4 A+RIGHT\nrelease\nrun 30 NONE\n' + capture('touch-priority')
        script += 'tap RIGHT 4 30\ntouch 128 168\n'
    for i in range(20):
        script += ('run 1 B+LEFT+RIGHT+A\n' if mode == 'skip' else 'run 1 NONE\n')
        script += capture(f'return-{i}')
    script += capture('held-close') + 'release\nrun 4 NONE\n' + capture('released')
    script += 'run 240\n' + capture('continuation') + continuation()
    return script


def verify(rom, observer, out, mode, contract_setup, baseline=None, baseline_delay=0):
    meta = None if mode == 'baseline' else current_build(rom, observer)
    require(meta is None or not meta['pressure_test_instrumentation'], 'Pressure ROM in normal test')
    require(mode == 'baseline' or baseline_delay == 0, 'Timing control is baseline-only')
    command = scenario(mode, baseline_delay)
    result = {'mode': mode, 'runner_sha256': sha(Path(__file__)), 'passed': False,
              'execution': run_new(rom, observer, out, command)}
    try:
        require(position(out / 'world.bin')[:4] == (64, 0xffffffff, 6, 6), 'Initial world not reached')
        require(position(out / 'save-ready.bin')[0] == 63, 'Native mother/menu path not reached')
        untouched = (out / 'before-first-save.sav').read_bytes()
        require(untouched == bytes([255])*524288, 'SRAM was written before first SAVE')
        require(identity(out / 'saved.bin')['save_header'] == [1,1,0], 'First SAVE not completed')
        fields = saved_fields(out / 'save-ready.bin')
        require(struct.unpack_from('<5H', fields['options_profile_coins'],4) ==
                (0x013e,0x012f,0x013d,0x013e,0xffff), 'Explicit native TEST name was not entered')
        require(fields == saved_fields(out / 'saved.bin'), 'First SAVE changed observed identity/progression')
        require(sha(out / 'first-save.sav') != sha(out / 'before-first-save.sav'), 'SRAM still blank')
        cold_script = (ROOT / 'runtime/inputs/cold-reload.script').read_text() + capture('cold') + 'quit\n'
        result['cold_execution'] = run_new(rom, observer, out / 'cold-reload', cold_script, out / 'first-save.sav')
        require(saved_fields(out / 'cold-reload/cold.bin') == fields, 'Cold identity/progression changed')
        require(position(out / 'cold-reload/cold.bin') == position(out / 'saved.bin'), 'Cold location changed')
        require(sha(out / 'cold-reload/reloaded.sav') == sha(out / 'first-save.sav'), 'Cold SRAM roundtrip differs')
        if meta is not None:
            markers = {p.stem: loaded_code(out, p.stem, meta) for p in out.glob('*.itcm')}
            require(all(m[14] == 0 for m in markers.values()), 'Ownership/canary error')
            expected = [('panel1',0)]
            if mode == 'full':
                expected += [('panel2-held',1),('back1',0),('disabled-back',0),('next-edges',0),
                             ('panel2',1),('panel3',2),('touch-back',1),('touch-forward',2),('touch-priority',1)]
            for name, panel in expected:
                require(markers[name][0] == OAK_MAGIC and markers[name][4:6] == (4,panel), 'Wrong Oak panel: ' + name)
                require(font(out / (name+'.bin')) == font(contract_setup), 'Lazy/shared font changed: '+name)
            held = markers['held-close']
            require(held[0] == OAK_MAGIC and held[1:3] == (0,0) and held[4] == 7
                    and held[8:11] == (1,1,0) and held[13] == 1, 'Guide did not cleanly latch after one allocation/free')
            require(heap(out / 'held-close.bin') == heap(contract_setup), 'Heap80 not restored exactly')
            require(oak(out / 'held-close.bin') == oak(contract_setup), 'Oak BG/font/callback not restored')
            require(markers['name-ready'][0] == OAK_MAGIC and markers['name-ready'][4] == 0
                    and markers['name-ready'][8] == 1, 'Guide replayed after native naming')
            require(markers['world'] == (0,)*16, 'Owner/pointer survived Oak Exit')
            cold_marker = loaded_code(out / 'cold-reload','cold',meta)
            require(cold_marker == (0,)*16, 'New Game guide ran on existing-save cold boot')
            setup_root = contract_setup.parent
            setup_name = contract_setup.stem
            require((out/'held-close.vram').read_bytes() == (setup_root/(setup_name+'-vram.bin')).read_bytes(), 'Sub VRAM not restored')
            require((out/'held-close.pal').read_bytes() == (setup_root/(setup_name+'-pal.bin')).read_bytes(), 'Palette changed')
            regs, before = (out/'held-close.regs').read_bytes(), (setup_root/(setup_name+'-regs.bin')).read_bytes()
            for offset, size in [(0x1000,4),(0x1008,2),(0x1050,6),(0x106c,2),(0x006c,2)]:
                require(regs[offset:offset+size] == before[offset:offset+size], 'Visibility/brightness/blend not restored')
            current_build(rom, observer)
            result['markers'] = markers
            result['restoration'] = 'Exact heap80, callback/data, BgConfig/map, fontWork/font0 including lazy glyphReadBuf, colors/LUT, sub VRAM/palette and selected video registers'
            if baseline is not None:
                original = saved_fields(baseline / 'save-ready.bin')
                result['baseline_fields_equal'] = {key: value == original[key] for key,value in fields.items()}
                allowed = {'options_profile_coins': {20,21,22,23,31}, 'vars_flags': {120,121}}
                differences = {key: [i for i,(a,b) in enumerate(zip(original[key],value)) if a != b]
                               for key,value in fields.items()}
                require(all(set(offsets) <= allowed.get(key,set()) for key,offsets in differences.items()),
                        'Progression/name differs beyond measured baseline RNG fields')
                result['baseline_difference_offsets'] = differences
                result['baseline_profile_bytes'] = original['options_profile_coins'].hex()
                result['candidate_profile_bytes'] = fields['options_profile_coins'].hex()
        else:
            itcm = (out / 'panel1.itcm').read_bytes()
            require(struct.unpack_from('<I',itcm,0x1fc0)[0] != OAK_MAGIC, 'Baseline unexpectedly displays Oak guide')
            result['red_guide_absent'] = True
        result.update({'passed': True, 'first_save_sha256': sha(out/'first-save.sav'),
                       'fields_sha256': field_hashes(fields), 'identity': identity(out/'saved.bin'),
                       'position': position(out/'saved.bin'), 'cold_sram_roundtrip': True,
                       'no_input_sram': True, 'no_sram_write_before_save': True,
                       'excluded_fields': 'IGT, array CRC/padding and PC bookkeeping; no RNG was changed.'})
    except Exception as exc:
        result['failure'] = str(exc)
        (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
        raise
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['rom','observer','out','contract-setup']:
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--baseline',type=Path)
    parser.add_argument('--mode',choices=['baseline','skip','full'],required=True)
    parser.add_argument('--baseline-delay',type=int,default=0)
    args=parser.parse_args()
    result=verify(args.rom,args.observer,args.out,args.mode,args.contract_setup,args.baseline,args.baseline_delay)
    print(json.dumps({name:result[name] for name in ['passed','mode','first_save_sha256','position']}))
