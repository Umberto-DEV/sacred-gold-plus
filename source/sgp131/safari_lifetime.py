"""Read-only SG-01a/SG-02 reproducer for the Route 47 partner battles.

This module does not patch a cartridge or touch a save.  It authenticates the
current EN/IT manual-test candidates, the native script dispatcher/handlers,
the pinned matching engine source, map 151, script 260 and event 146.  It then
follows four coordinate triggers to their exported script entries and applies
one ownership oracle to the reachable partner-heal paths.  A field message
window must be closed before ``ScrCmd_436`` leaves the field: the authenticated
handler calls the native leave task, whose pinned engine path tears down the
field BG/window owner heap.  Closing that old window after restore is therefore
a source-bound stale-owner operation.

The result demonstrates the component defect only.  It does not claim that a
black/white screen was reproduced in an emulator or on hardware.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

import ndspy.narc
import ndspy.rom

from sgp12.rom import Arm9, sha_file
from sgp131 import gifts_audit, gifts_scripts


SCRIPT_ARCHIVE = 'a/0/1/2'
EVENT_ARCHIVE = 'a/0/3/2'
MAP_HEADER_BASE = 0x020F6BE0
MAP_ID = 151
SCRIPT_MEMBER = 260
EVENT_MEMBER = 146
SCRIPT_SHA256 = '998ab0b338b5b8bf4faea7579f2baa01bb21e54bc4a426fae1e7157c0df0c497'
REPAIRED_SCRIPT_SHA256 = 'bcc71c8ce50440b37fc253f04897ef30e765508162d999c057a7bbe6b7ad01b2'
EVENT_SHA256 = '2640403256c62fe47dc9e1579dfd181f4deb65218765ed075266ed73743a0a66'
COMMANDS_SHA256 = 'fbfbf438104cfc3735c3144730ed711bb882fca370a8de680db5c1d39ffaca5a'
SCRIPT_COMMAND_TABLE = 0x020FAD00
CURRENT_ROM_SHA256 = {
    'EN': '1ad993585702aa4c2ab7878679158c36eb3c1c20a85f5a32f3bf50f8195ad07d',
    'IT': '1f39ede6c638f1ec28cc15886613547776460b1d0f2fbd2c0ebb0e1fb4b7f479',
}

NATIVE_HANDLERS = {
    'CloseMsg': (53, 0x02041169, 0x02041168,
                 '70b5803005680121281cfff7bdf8041c281c0621fff7b8f8061c201c0021cdf7'
                 '19fc201cdcf7c8f9281cd23001784020d235814329700020307070bd'),
    'RestoreOverworld': (150, 0x02042A11, 0x02042A10,
                         '08b580300068006912f044fc012008bd'),
    'ScrCmd_436': (436, 0x02042A21, 0x02042A20,
                   '08b580300068006912f018fc012008bd'),
    'GetPlayerXYZ': (685, 0x02044BE9, 0x02044BE8,
                     'f8b5051c291c80310c68fbf71bf9011c281c80300068fbf7b9fb061c281cfb'
                     'f711f9011c281c80300068fbf7affb071c281cfbf707f98035011c2868fbf7a6'
                     'fb051c206c17f056fd041c1af06ffe3080201c1af073fec10f41184810388020'
                     '1c1af074fe28800020f8bd'),
}
NATIVE_CALLEES = {
    'CallTask_LeaveOverworld': (0x0205525C,
        '38b5051cfbf7f4f9041ce8f789fe002802d1d0f755f938bd201c74f32ff80349'
        '281c0022fbf756f938bdc04645520502'),
    'CallTask_RestoreOverworld': (0x020552A4,
        '38b5051cfbf7d0f9041ce8f765fe002802d0d0f731f938bd201cfbf77ff90349'
        '281c0022fbf732f938bdc0468d520502'),
    'FieldSystem_StopMap': (0x0203DF34, '0021c16670470000'),
    'CoordEvent_XZ_only': (0x0203DE04,
        'f0b583b00090006c019102921ef034fc061c0098006c1ef035fc041c02980027'
        '00281fdd019d69888e4216dbe8880818864212daa9888c420fdb2889081884420'
        'bdae989009802f0affaa989814204d10198390103b0405af0bd02987f1c103587'
        '42e0db014803b0f0bdc046ffff'),
}
SOURCE_MODEL_SHA256 = {
    'src/scrcmd_c.c': '89e769e4a8b2fa05b05c87366b2585b0d490479402eb49d054396e8b5e6d8e70',
    'asm/unk_02055244.s': 'a0c5b16b91acf8711eadb60515c3a1e3b5bd408b77a9e6a9ff05b0e2039b1166',
    'src/field_system.c': 'ff684ca71da8f8655bf6ee72417de46274780a37b5b0b8711e2f1127a9d5773c',
    'src/field/scrcmd_message.c': 'a71db571365c11b78e3e6ed986655c368eeb9f67773a017a85566f6c77e70e5b',
    'src/field/field_3d_object_task.c': '28b7e36c1ba4e72574aac7a723e579fe5d985ef24ade4db4072859de65609d25',
    'src/field/fieldmap.c': '7f616b118728a47d80cec5028d46a23d300f1fee8050a12fc52ede6340ff3c20',
    'asm/unk_0203DB6C.s': 'a7d92c6160788be3bfc6f7319bd38d9b21e43d4f7458a1b52619b0be087fbd2e',
}

# Hand-checked half-open spans in authenticated member 260.  They start at the
# post-battle partner message and end at the path's End command.
PATH_SPANS = {
    'Mira': (0x257, 0x28A),
    'Buck': (0x335, 0x368),
    'Cheryl': (0x47F, 0x4B2),
    'Marley': (0x585, 0x5B8),
}

# insert CloseMsg immediately after NPCMsg; remove its old occurrence at the
# end of the fade/heal/unload sequence.  The half-open rotation includes the
# old two-byte CloseMsg and does not change member length or later offsets.
REPAIR_WINDOWS = {
    'Buck': (0x338, 0x35C),
    'Cheryl': (0x482, 0x4A6),
    'Marley': (0x588, 0x5AC),
}

# SG-02 is the first (Mira) bridge battle.  The native CoordEvent dispatcher
# compares only X/Z, so the same tile column on the lower level can launch the
# upper bridge script.  Keep the original entry at its stable offset and point
# exported script 7 at a small appended wrapper.  The wrapper reads the real
# player height before any BGM, lock or movement side effect; only bridge Y=0
# may jump to the original entry.
MIRA_BATTLE_ENTRY = 0x1BF
MIRA_EXPORT_INDEX = 6
MIRA_EXPECTED_Y = 0
SG02_GUARD_VARS = (0x8004, 0x8005, 0x8006)
SG02_GUARD_SIZE = 23

# Complete coordinate records in authenticated event member 146.  Script IDs
# are one-based indexes into member 260's exported entry table.
COORD_TRIGGERS = {
    'Mira': (1, 7, 141, 397, 1, 1, 0, 0, 24992),
    'Buck': (2, 9, 125, 389, 1, 1, 0, 0, 24991),
    'Cheryl': (3, 14, 125, 384, 1, 1, 0, 0, 24990),
    'Marley': (4, 17, 99, 378, 1, 1, 0, 0, 24889),
}


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def classify_trace(names):
    """Classify a bounded decoded command trace using the window-owner oracle."""
    _need(type(names) in (list, tuple) and all(type(name) is str for name in names),
          'Safari trace must be a list or tuple of command names')
    window_open = False
    owner_stale = False
    for name in names:
        if name == 'OpenMsg':
            window_open = True
            owner_stale = False
        elif name in ('NPCMsg', 'NonNPCMsg') and not window_open:
            # These commands allocate only while SCRIPTENV_FIELD_08 is clear;
            # unlike OpenMsg, they do not re-own an already open stale window.
            window_open = True
            owner_stale = False
        elif name in ('CloseMsg', 'HoldMsg'):
            if window_open and owner_stale:
                return 'stale-window-close'
            window_open = False
            owner_stale = False
        elif name == 'ScrCmd_436' and window_open:
            owner_stale = True
    return 'open-window-after-unload' if owner_stale else 'healthy'


def _native_dispatch(arm):
    handlers = {}
    for name, (command, pointer, address, expected_hex) in NATIVE_HANDLERS.items():
        observed_pointer = struct.unpack(
            '<I', arm.leggi(SCRIPT_COMMAND_TABLE + command * 4, 4))[0]
        expected = bytes.fromhex(expected_hex)
        observed = arm.leggi(address, len(expected))
        _need(observed_pointer == pointer, f'Safari native {name} dispatch differs')
        _need(observed == expected, f'Safari native {name} handler differs')
        handlers[name] = {
            'command': command,
            'pointer': pointer,
            'sha256': hashlib.sha256(observed).hexdigest(),
        }
    callees = {}
    for name, (address, expected_hex) in NATIVE_CALLEES.items():
        expected = bytes.fromhex(expected_hex)
        observed = arm.leggi(address, len(expected))
        _need(observed == expected, f'Safari native {name} differs')
        callees[name] = {'address': address,
                          'sha256': hashlib.sha256(observed).hexdigest()}
    return {'verified': True, 'table': SCRIPT_COMMAND_TABLE,
            'handlers': handlers, 'callees': callees}


def _source_model(metadata_path):
    root = metadata_path.parents[2]
    observed = {}
    for relative, expected in SOURCE_MODEL_SHA256.items():
        path = root / relative
        _need(path.is_file(), f'Safari pinned source missing: {relative}')
        digest = sha_file(path)
        _need(digest == expected, f'Safari pinned source differs: {relative}')
        observed[relative] = digest
    return {'verified': True, 'sha256': observed}


def _map_binding(data):
    arm = Arm9.from_bytes(data)
    header = struct.unpack('<BB11H', arm.leggi(MAP_HEADER_BASE + MAP_ID * 24, 24))
    return {'id': MAP_ID, 'script_member': header[4], 'init_member': header[5],
            'message_member': header[6], 'event_member': header[9]}


def _event_triggers(raw):
    """Decode all four bounded event arrays and return the four coord triggers."""
    _need(type(raw) is bytes, 'Safari event member bytes')
    offset = 0
    groups = []
    for size, fmt in ((20, '<HHiiiH2x'), (32, '<6Hh3HhhHHi'),
                      (12, '<4Hi'), (16, '<8H')):
        _need(offset + 4 <= len(raw), 'Safari event count is truncated')
        count = struct.unpack_from('<I', raw, offset)[0]
        offset += 4
        _need(count <= 1024 and offset + count * size <= len(raw),
              'Safari event record geometry differs')
        groups.append([struct.unpack_from(fmt, raw, offset + row * size)
                       for row in range(count)])
        offset += count * size
    _need(offset == len(raw), 'Safari event member has unparsed trailing bytes')
    _need(tuple(map(len, groups)) == (4, 33, 7, 5),
          'Safari event group counts differ')
    coords = groups[3]
    result = {}
    for name, expected in COORD_TRIGGERS.items():
        row, *record = expected
        _need(row < len(coords) and tuple(coords[row]) == tuple(record),
              f'Safari {name} coordinate trigger differs')
        result[name] = {'row': row, 'script_id': record[0],
                        'x': record[1], 'z': record[2],
                        'w': record[3], 'h': record[4], 'var': record[7]}
    return result


def _reachable(parsed, start):
    pending, seen = [start], set()
    while pending:
        pc = pending.pop()
        if pc in seen:
            continue
        _need(pc in parsed.istruzioni, 'Safari reachable edge is not an instruction')
        seen.add(pc)
        instruction = parsed.istruzioni[pc]
        pending.extend(dest for _, dest, kind in instruction.rami if kind != 'movement')
        if instruction.nome not in ('End', 'Return', 'GoTo'):
            pending.append(instruction.fine)
    return seen


def _decoded_paths(parsed, triggers):
    report = {}
    ordered = sorted(parsed.istruzioni.values(), key=lambda instruction: instruction.off)
    for name, (start, end) in PATH_SPANS.items():
        rows = [instruction for instruction in ordered if start <= instruction.off < end]
        _need(rows and rows[0].nome == 'NPCMsg' and rows[-1].nome == 'End',
              f'Safari {name} path boundaries differ')
        names = [instruction.nome for instruction in rows]
        for required in ('HealParty', 'ScrCmd_436', 'RestoreOverworld', 'CloseMsg'):
            _need(names.count(required) == 1, f'Safari {name} {required} count differs')
        script_id = triggers[name]['script_id']
        _need(1 <= script_id <= len(parsed.entry),
              f'Safari {name} event script ID is outside the export table')
        entry = parsed.entry[script_id - 1]
        reachable = _reachable(parsed, entry)
        _need(rows[0].off in reachable,
              f'Safari {name} trigger does not reach its partner message')
        report[name] = {
            'status': classify_trace(names),
            'script_id': script_id,
            'entry_offset': entry,
            'trigger': triggers[name],
            'trigger_reaches_message': True,
            'message_offset': rows[0].off,
            'close_offset': next(row.off for row in rows if row.nome == 'CloseMsg'),
            'leave_offset': next(row.off for row in rows if row.nome == 'ScrCmd_436'),
            'restore_offset': next(row.off for row in rows if row.nome == 'RestoreOverworld'),
        }
    return report


def _swap_path_commands(script, parsed, path):
    """Swap the real two-byte CloseMsg/leave opcodes without shifting edges."""
    start, end = PATH_SPANS[path]
    rows = [instruction for instruction in parsed.istruzioni.values()
            if start <= instruction.off < end]
    close = next(row for row in rows if row.nome == 'CloseMsg')
    leave = next(row for row in rows if row.nome == 'ScrCmd_436')
    _need(close.fine - close.off == 2 and leave.fine - leave.off == 2,
          f'Safari {path} mutant commands are not two-byte opcodes')
    mutated = bytearray(script)
    mutated[close.off:close.fine], mutated[leave.off:leave.fine] = (
        mutated[leave.off:leave.fine], mutated[close.off:close.fine])
    return bytes(mutated)


def _mutant_status(script, commands, triggers, path):
    original = gifts_scripts.decode(script, commands, SCRIPT_MEMBER)
    mutated = _swap_path_commands(script, original, path)
    parsed = gifts_scripts.decode(mutated, commands, SCRIPT_MEMBER)
    _need(not parsed.errori and parsed.riassembla()[0],
          f'Safari {path} bytecode mutant does not round-trip')
    return _decoded_paths(parsed, triggers)[path]['status']


def _repair_shape(raw, commands):
    _need(type(raw) is bytes, 'Safari script member bytes')
    _need(getattr(commands, 'metadata_sha256', None) == COMMANDS_SHA256,
          'Safari command metadata identity differs')
    parsed = gifts_scripts.decode(raw, commands, SCRIPT_MEMBER)
    _need(not parsed.errori and parsed.riassembla()[0],
          'Safari script member does not decode and round-trip cleanly')
    ordered = sorted(parsed.istruzioni.values(), key=lambda instruction: instruction.off)
    for name, (insert, close_at) in REPAIR_WINDOWS.items():
        start, end = PATH_SPANS[name]
        rows = [row for row in ordered if start <= row.off < end]
        _need(rows and rows[0].nome == 'NPCMsg' and rows[0].fine == insert,
              f'Safari {name} message boundary differs')
        close = [row for row in rows if row.nome == 'CloseMsg']
        _need(len(close) == 1 and close[0].off == close_at
              and raw[close_at:close_at + 2] == b'\x35\x00',
              f'Safari {name} CloseMsg boundary differs')
        _need(not any(row.rami for row in rows if insert <= row.off <= close_at),
              f'Safari {name} repair window contains a branch')
        targets = set(parsed.entry)
        targets.update(destination for row in parsed.istruzioni.values()
                       for _operand, destination, kind in row.rami
                       if kind != 'movement')
        _need(not any(insert <= target < close_at + 2 for target in targets),
              f'Safari {name} repair window has an incoming edge')
    return parsed


def _append_mira_height_guard(raw):
    """Append the SG-02 wrapper and retarget only exported script 7."""
    _need(type(raw) is bytes, 'Safari repaired script bytes')
    wrapper = len(raw)
    x_var, y_var, z_var = SG02_GUARD_VARS
    branch_end = wrapper + 21
    guard = (
        struct.pack('<H3H', 685, x_var, y_var, z_var) +
        struct.pack('<3H', 17, y_var, MIRA_EXPECTED_Y) +
        struct.pack('<HB', 28, 1) +
        struct.pack('<i', MIRA_BATTLE_ENTRY - branch_end) +
        struct.pack('<H', 2)
    )
    _need(len(guard) == SG02_GUARD_SIZE, 'SG-02 guard geometry differs')
    result = bytearray(raw)
    pointer_at = MIRA_EXPORT_INDEX * 4
    old_entry = pointer_at + 4 + struct.unpack_from('<I', result, pointer_at)[0]
    _need(old_entry == MIRA_BATTLE_ENTRY, 'SG-02 Mira export differs')
    struct.pack_into('<I', result, pointer_at, wrapper - (pointer_at + 4))
    result.extend(guard)
    return bytes(result)


def repair_member(before, commands):
    """Repair the three stale closes and guard the first bridge battle.

    This pure member transform is fail-closed on the exact demonstrated V4
    preimage and command metadata.  It never opens or writes a cartridge.
    """
    _need(type(before) is bytes and hashlib.sha256(before).hexdigest() == SCRIPT_SHA256,
          'Safari script preimage identity differs')
    _repair_shape(before, commands)
    after = bytearray(before)
    for _name, (insert, close_at) in sorted(
            REPAIR_WINDOWS.items(), key=lambda item: item[1][0], reverse=True):
        after[insert:close_at + 2] = b'\x35\x00' + after[insert:close_at]
    result = _append_mira_height_guard(bytes(after))
    _need(hashlib.sha256(result).hexdigest() == REPAIRED_SCRIPT_SHA256,
          'Safari script repaired identity differs')
    verify_repair(before, result, commands)
    return result


def verify_repair(before, after, commands):
    """Independent bounded read-back of the SG-01a/SG-02 member repair."""
    _need(type(before) is bytes and hashlib.sha256(before).hexdigest() == SCRIPT_SHA256,
          'Safari script preimage identity differs')
    _need(type(after) is bytes and len(after) == len(before) + SG02_GUARD_SIZE
          and hashlib.sha256(after).hexdigest() == REPAIRED_SCRIPT_SHA256,
          'Safari script postimage identity differs')
    before_parsed = _repair_shape(before, commands)
    expected = bytearray(before)
    for _name, (insert, close_at) in sorted(
            REPAIR_WINDOWS.items(), key=lambda item: item[1][0], reverse=True):
        expected[insert:close_at + 2] = b'\x35\x00' + before[insert:close_at]
    expected = _append_mira_height_guard(bytes(expected))
    _need(after == expected,
          'Safari repair changed bytes outside the rotations and SG-02 guard')

    after_parsed = gifts_scripts.decode(after, commands, SCRIPT_MEMBER)
    _need(not after_parsed.errori and after_parsed.riassembla()[0],
          'Safari repaired member does not decode and round-trip cleanly')
    before_rows = sorted(before_parsed.istruzioni.values(), key=lambda row: row.off)
    after_rows = sorted(after_parsed.istruzioni.values(), key=lambda row: row.off)
    states = {}
    for name, (start, end) in PATH_SPANS.items():
        old_names = [row.nome for row in before_rows if start <= row.off < end]
        new_names = [row.nome for row in after_rows if start <= row.off < end]
        states[name] = {'before': classify_trace(old_names),
                        'after': classify_trace(new_names)}
    _need(states['Mira'] == {'before': 'healthy', 'after': 'healthy'},
          'Safari healthy control changed')
    _need(all(states[name] == {'before': 'stale-window-close', 'after': 'healthy'}
              for name in REPAIR_WINDOWS),
          'Safari affected-path semantic endpoints differ')
    wrapper = after_parsed.entry[MIRA_EXPORT_INDEX]
    guard_rows = []
    cursor = wrapper
    for _ in range(4):
        _need(cursor in after_parsed.istruzioni, 'SG-02 guard edge differs')
        row = after_parsed.istruzioni[cursor]
        guard_rows.append(row)
        cursor = row.fine
    _need([row.nome for row in guard_rows] ==
          ['GetPlayerXYZ', 'CompareVarToValue', 'GoToIf', 'End'],
          'SG-02 guard command sequence differs')
    _need(guard_rows[0].args == list(SG02_GUARD_VARS)
          and guard_rows[1].args == [SG02_GUARD_VARS[1], MIRA_EXPECTED_Y]
          and guard_rows[2].args[0] == 1
          and guard_rows[2].rami == [(1, MIRA_BATTLE_ENTRY, 'script')],
          'SG-02 guard operands or bridge target differ')
    return {
        'member': SCRIPT_MEMBER,
        'before_sha256': SCRIPT_SHA256,
        'after_sha256': REPAIRED_SCRIPT_SHA256,
        'bytes': len(after),
        'paths': states,
        'rotations': {name: {'insert': insert, 'old_close': close}
                      for name, (insert, close) in REPAIR_WINDOWS.items()},
        'sg02': {'wrapper': wrapper, 'battle_entry': MIRA_BATTLE_ENTRY,
                 'expected_y': MIRA_EXPECTED_Y,
                 'vars': list(SG02_GUARD_VARS)},
    }


def audit_rom(path, language, metadata_path):
    """Authenticate and inspect one exact candidate without writing it."""
    path, metadata_path = Path(path), Path(metadata_path)
    _need(language in CURRENT_ROM_SHA256, 'Safari language must be EN or IT')
    before = sha_file(path)
    _need(before == CURRENT_ROM_SHA256[language],
          'Safari candidate identity differs from the current pinned input')
    data = path.read_bytes()
    arm = Arm9.from_bytes(data)
    binding = _map_binding(data)
    _need(binding == {'id': 151, 'script_member': 260, 'init_member': 505,
                      'message_member': 407, 'event_member': 146},
          'Safari Route 47 map binding differs')

    rom = ndspy.rom.NintendoDSRom(data)
    scripts = ndspy.narc.NARC(rom.getFileByName(SCRIPT_ARCHIVE)).files
    events = ndspy.narc.NARC(rom.getFileByName(EVENT_ARCHIVE)).files
    script = bytes(scripts[SCRIPT_MEMBER])
    event = bytes(events[EVENT_MEMBER])
    script_sha = hashlib.sha256(script).hexdigest()
    event_sha = hashlib.sha256(event).hexdigest()
    _need(script_sha == SCRIPT_SHA256, 'Safari script 260 identity differs')
    _need(event_sha == EVENT_SHA256, 'Safari event 146 identity differs')

    commands = gifts_audit.load_commands(metadata_path)
    _need(commands.metadata_sha256 == COMMANDS_SHA256,
          'Safari command metadata identity differs')
    parsed = gifts_scripts.decode(script, commands, SCRIPT_MEMBER)
    _need(not parsed.errori and parsed.riassembla()[0],
          'Safari script 260 does not decode and round-trip cleanly')
    triggers = _event_triggers(event)
    paths = _decoded_paths(parsed, triggers)
    _need(paths['Mira']['status'] == 'healthy', 'Safari healthy control differs')
    _need(all(paths[name]['status'] == 'stale-window-close'
              for name in ('Buck', 'Cheryl', 'Marley')),
          'Safari affected partner paths differ')
    mutants = {
        'Mira_close_moved_after_unload': _mutant_status(
            script, commands, triggers, 'Mira'),
        'Buck_close_moved_before_unload': _mutant_status(
            script, commands, triggers, 'Buck'),
    }
    _need(mutants == {'Mira_close_moved_after_unload': 'stale-window-close',
                      'Buck_close_moved_before_unload': 'healthy'},
          'Safari bytecode mutants are not discriminated')
    native_dispatch = _native_dispatch(arm)
    source_model = _source_model(metadata_path)

    after = sha_file(path)
    return {
        'schema': 1,
        'case': 'SG-01a',
        'language': language,
        'rom_sha256': before,
        'map': binding,
        'script_sha256': script_sha,
        'event_sha256': event_sha,
        'paths': paths,
        'mutants': mutants,
        'native_dispatch': native_dispatch,
        'source_model': source_model,
        'component_status': 'demonstrated',
        'runtime_blackout': 'not-run',
        'input_unchanged': before == after,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--language', choices=sorted(CURRENT_ROM_SHA256), required=True)
    parser.add_argument('--metadata', type=Path, required=True,
                        help='pinned pret tools/py_scripts/scrcmd.json')
    args = parser.parse_args(argv)
    print(json.dumps(audit_rom(args.rom, args.language, args.metadata),
                     sort_keys=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
