"""HG-T10: execute the exact V4 ShowPerson object-creation consumer.

The fixture models only the component boundary demonstrated by the private
runtime probe: object-event lookup and flag reads are native-call seams, while
the real 64-byte Thumb consumer decides whether to call the map-object creator.
No ROM or save is written.
"""
import hashlib
import importlib
from pathlib import Path
import unittest

import ndspy.rom

from sgp12.rom import Arm9, bl_decode
from . import archives, gifts_audit, gifts_scripts


ROOT = Path(__file__).resolve().parents[2]
V4_ROOT = ROOT / 'local/experiments/balance493-2026-10-28'
V4 = {
    'EN': ('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90',
           147345256),
    'IT': ('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156',
           153228136),
}

CONSUMER = 0x0205E34C
CONSUMER_SIZE = 0x40
CONSUMER_SHA256 = '54abd9a5af0aca640ec33135238455bcad9c1e1bfcc472935455cca4c0a89a83'
FIND_EVENT = 0x0205FA98
EVENT_FLAG = 0x0205FA08
MANAGER_FIELD = 0x0205F1E4
FLAG_CHECK = 0x020403FC
CREATE_OBJECT = 0x0205E1D0

MANAGER = 0x02200000
FIELD_SYSTEM = 0x02201000
EVENTS = 0x02202000
OBJECTS = 0x02203000
STACK = 0x023F0000
OBJECT_ID = 5

SCRIPT_ARCHIVE = 'a/0/1/2'
SCRIPT_MEMBER = 21
LUGIA_SCRIPT_MEMBER = 104
SCRIPT_PREIMAGE_SHA256 = 'cccdd680958b2d3da9cf700a6fffa4ce079eb4a8664345934fac150da038c609'
LUGIA_PREIMAGE_SHA256 = 'b93052d54381a223435fcb1d35a710ba2c9c1b286c2f90b185cbb611cb0a14e4'
COMMANDS_SHA256 = 'fbfbf438104cfc3735c3144730ed711bb882fca370a8de680db5c1d39ffaca5a'
PRODUCER = 'legendary-scenes-scripts'


def candidate(case, language):
    path = V4_ROOT / ('candidate-v4-%s.nds' % language)
    if not path.is_file():
        case.skipTest('immutable V4 candidate unavailable: ' + str(path))
    data = path.read_bytes()
    case.assertEqual((hashlib.sha256(data).hexdigest(), len(data)), V4[language])
    return data


def script_material(case, language):
    data = candidate(case, language)
    metadata = ROOT / 'local/tools/pokeheartgold/tools/py_scripts/scrcmd.json'
    if not metadata.is_file():
        case.skipTest('pinned script command metadata unavailable: ' + str(metadata))
    commands = gifts_audit.load_commands(metadata)
    case.assertEqual(commands.metadata_sha256, COMMANDS_SHA256)
    rom = ndspy.rom.NintendoDSRom(data)
    archive = bytes(rom.getFileByName(SCRIPT_ARCHIVE))
    members = archives.members(archive)
    case.assertEqual(hashlib.sha256(members[SCRIPT_MEMBER]).hexdigest(),
                     SCRIPT_PREIMAGE_SHA256)
    case.assertEqual(hashlib.sha256(members[LUGIA_SCRIPT_MEMBER]).hexdigest(),
                     LUGIA_PREIMAGE_SHA256)
    return data, archive, members, commands


class NativeShowPersonBench:
    """Bounded Thumb-1 executor for MapObject_CreateFromObjectEventWithId."""

    def __init__(self, rom, map_id, active_ids=()):
        self.arm = Arm9.from_bytes(rom)
        preimage = self.arm.leggi(CONSUMER, CONSUMER_SIZE)
        if hashlib.sha256(preimage).hexdigest() != CONSUMER_SHA256:
            raise ValueError('foreign ShowPerson consumer preimage')
        self.map_id = map_id
        self.active = [{'address': OBJECTS + 0x12C * index,
                        'map_id': map_id, 'object_id': object_id}
                       for index, object_id in enumerate(active_ids)]
        self.event = bytearray(0x20)
        self.event[0:2] = OBJECT_ID.to_bytes(2, 'little')
        self.event[8:10] = (0x242 if map_id == 340 else 0x243).to_bytes(2, 'little')
        self.event[10:12] = (1).to_bytes(2, 'little')
        self.created = []

    def _native_call(self, target, registers):
        if target == FIND_EVENT:
            if (registers[0], registers[1], registers[2]) != (OBJECT_ID, 1, EVENTS):
                raise AssertionError('unexpected object-event lookup ABI')
            event_id = int.from_bytes(self.event[0:2], 'little')
            script_id = int.from_bytes(self.event[10:12], 'little')
            return EVENTS if event_id == OBJECT_ID and script_id != 0xFFFF else 0
        if target == EVENT_FLAG:
            if registers[0] != EVENTS:
                raise AssertionError('event flag read from foreign object event')
            return int.from_bytes(self.event[8:10], 'little')
        if target == MANAGER_FIELD:
            if registers[0] != MANAGER:
                raise AssertionError('field lookup used foreign map-object manager')
            return FIELD_SYSTEM
        if target == FLAG_CHECK:
            if registers[0] != FIELD_SYSTEM:
                raise AssertionError('hide-flag check used foreign field system')
            return 0
        if target == CREATE_OBJECT:
            if (registers[0], registers[1], registers[2]) != (MANAGER, EVENTS,
                                                               self.map_id):
                raise AssertionError('unexpected map-object creation ABI')
            address = OBJECTS + 0x12C * len(self.active)
            item = {'address': address, 'map_id': self.map_id,
                    'object_id': OBJECT_ID}
            self.active.append(item)
            self.created.append(item)
            return address
        raise AssertionError('unexpected native call %#010x' % target)

    def run(self):
        registers = [0] * 16
        registers[0:4] = [MANAGER, OBJECT_ID, 1, self.map_id]
        registers[13] = STACK
        stack = {STACK: EVENTS}
        zero = False
        pc = CONSUMER
        for _step in range(64):
            op = int.from_bytes(self.arm.leggi(pc, 2), 'little')
            if op & 0xFE00 == 0xB400:  # push {...,lr}
                count = (op & 0xFF).bit_count() + ((op >> 8) & 1)
                registers[13] -= count * 4
                pc += 2
                continue
            if op & 0xFE00 == 0xBC00:  # pop {...,pc}: bounded return
                return {
                    'returned_object': registers[0],
                    'created': tuple(self.created),
                    'id5_count': sum(item['map_id'] == self.map_id
                                     and item['object_id'] == OBJECT_ID
                                     for item in self.active),
                }
            if op & 0xFE00 == 0x1C00:  # adds Rd,Rn,#imm3
                rd, rn, immediate = op & 7, (op >> 3) & 7, (op >> 6) & 7
                registers[rd] = (registers[rn] + immediate) & 0xFFFFFFFF
                zero = registers[rd] == 0
                pc += 2
                continue
            if op & 0xF800 == 0x2000:  # movs Rd,#imm8
                rd = (op >> 8) & 7
                registers[rd] = op & 0xFF
                zero = registers[rd] == 0
                pc += 2
                continue
            if op & 0xF800 == 0x9800:  # ldr Rd,[sp,#imm8*4]
                rd = (op >> 8) & 7
                address = registers[13] + (op & 0xFF) * 4
                registers[rd] = stack[address]
                pc += 2
                continue
            if op & 0xF800 == 0x9000:  # str Rd,[sp,#imm8*4]
                rd = (op >> 8) & 7
                address = registers[13] + (op & 0xFF) * 4
                stack[address] = registers[rd]
                pc += 2
                continue
            if op & 0xF800 == 0x2800:  # cmp Rn,#imm8
                rn = (op >> 8) & 7
                zero = registers[rn] == (op & 0xFF)
                pc += 2
                continue
            if op & 0xF000 == 0xD000:  # conditional branch
                condition = (op >> 8) & 0xF
                if condition not in (0, 1):
                    raise AssertionError('unsupported condition %d at %#010x' %
                                         (condition, pc))
                take = zero if condition == 0 else not zero
                offset = op & 0xFF
                if offset & 0x80:
                    offset -= 0x100
                pc = pc + 4 + offset * 2 if take else pc + 2
                continue
            if op & 0xF800 in (0x0000, 0x0800):  # lsls/lsrs immediate
                rd, rs, amount = op & 7, (op >> 3) & 7, (op >> 6) & 0x1F
                if op & 0x0800:
                    registers[rd] = registers[rs] >> (amount or 32)
                else:
                    registers[rd] = (registers[rs] << amount) & 0xFFFFFFFF
                zero = registers[rd] == 0
                pc += 2
                continue
            if op & 0xF800 == 0xF000:  # BL to an authenticated native seam
                target = bl_decode(pc, self.arm.leggi(pc, 4))
                registers[0] = self._native_call(target, registers)
                pc += 4
                continue
            raise AssertionError('unsupported Thumb opcode %#06x at %#010x' %
                                 (op, pc))
        raise AssertionError('ShowPerson consumer did not return within budget')


class LegendaryGuardBench:
    """Execute the decoded local member-21 guard at its script API boundary."""

    def __init__(self, parsed, *, hidden, active):
        starts = [row.off for row in parsed.istruzioni.values()
                  if row.nome == 'CheckFlag' and row.args == [0x242]]
        if len(starts) != 1:
            raise AssertionError('member 21 must contain one decoded Ho-Oh hide-flag guard')
        self.parsed = parsed
        self.start = starts[0]
        self.hidden = hidden
        self.active = active
        self.creates = 0
        self.compare = -1

    def run(self):
        pc = self.start
        for _step in range(12):
            row = self.parsed.istruzioni.get(pc)
            if row is None:
                raise AssertionError('legendary guard left decoded script code')
            if row.nome == 'MakeObjectVisible' and row.args == [OBJECT_ID]:
                return self
            pc = row.fine
            target = row.rami[0][1] if row.rami else None
            if row.nome == 'CheckFlag' and row.args == [0x242]:
                self.compare = 0 if self.hidden else -1
            elif row.nome == 'GoToIf':
                conditions = {
                    0: self.compare < 0, 1: self.compare == 0,
                    2: self.compare > 0, 3: self.compare <= 0,
                    4: self.compare >= 0, 5: self.compare != 0,
                }
                if conditions[row.args[0]]:
                    pc = target
            elif row.nome == 'GoTo':
                pc = target
            elif row.nome == 'ClearFlag' and row.args == [0x242]:
                self.hidden = False
            elif row.nome == 'ShowPerson' and row.args == [OBJECT_ID]:
                # The separately characterized native consumer creates on every
                # call, even if this numeric object ID is already active.
                self.active += 1
                self.creates += 1
            elif row.nome != 'Nop':
                raise AssertionError('unexpected command in legendary guard: ' +
                                     row.nome)
        raise AssertionError('legendary guard did not reach MakeObjectVisible 5')


class LegendarySceneRomTests(unittest.TestCase):
    def test_object_absent_showperson_creates_exactly_one_hooh(self):
        for language in ('EN', 'IT'):
            with self.subTest(language=language):
                result = NativeShowPersonBench(candidate(self, language), 340).run()
                self.assertEqual(result['id5_count'], 1)
                self.assertEqual(len(result['created']), 1)
                self.assertNotEqual(result['returned_object'], 0)

    def test_existing_hooh_showperson_consumer_creates_a_second_id5(self):
        counts = {}
        creates = {}
        for language in ('EN', 'IT'):
            result = NativeShowPersonBench(
                candidate(self, language), 340, active_ids=(OBJECT_ID,)).run()
            counts[language] = result['id5_count']
            creates[language] = len(result['created'])
        self.assertEqual(counts, {'EN': 2, 'IT': 2})
        self.assertEqual(creates, {'EN': 1, 'IT': 1})

    def test_lugia_map244_shared_id_control_creates_exactly_one(self):
        for language in ('EN', 'IT'):
            with self.subTest(language=language):
                result = NativeShowPersonBench(candidate(self, language), 244).run()
                self.assertEqual(result['id5_count'], 1)
                self.assertEqual(len(result['created']), 1)

    def test_foreign_showperson_consumer_preimage_is_rejected(self):
        raw = candidate(self, 'EN')
        damaged = bytearray(raw)
        damaged[Arm9.from_bytes(raw).off(CONSUMER, 1)] ^= 1
        with self.assertRaisesRegex(ValueError, 'foreign ShowPerson consumer preimage'):
            NativeShowPersonBench(bytes(damaged), 340)

    def test_member21_local_guard_is_idempotent_and_preserves_lugia_and_consumer(self):
        fixtures = {language: script_material(self, language)
                    for language in ('EN', 'IT')}
        module_name = 'sgp131.legendary_archives'
        try:
            producer_module = importlib.import_module(module_name)
        except ModuleNotFoundError as error:
            if error.name != module_name:
                raise
            self.fail('legendary-scenes-scripts producer is missing')
        producer = producer_module.PRODUCERS.get(PRODUCER)
        self.assertIsNotNone(producer, 'legendary-scenes-scripts producer is missing')

        for language in ('EN', 'IT'):
            data, archive, before, commands = fixtures[language]
            delta = producer(data, language, None)
            with self.subTest(language=language):
                self.assertEqual((delta.archive, delta.producers()),
                                 (SCRIPT_ARCHIVE, [PRODUCER]))
                self.assertEqual([row.index for row in delta.members],
                                 [SCRIPT_MEMBER])
                patched_archive = archives.apply_members(
                    archive, delta.replacements())
                after = archives.members(patched_archive)
                self.assertEqual(after[LUGIA_SCRIPT_MEMBER],
                                 before[LUGIA_SCRIPT_MEMBER])

                rebuilt = ndspy.rom.NintendoDSRom(data)
                rebuilt.setFileByName(SCRIPT_ARCHIVE, patched_archive)
                rebuilt_data = rebuilt.save()
                self.assertEqual(
                    Arm9.from_bytes(rebuilt_data).leggi(CONSUMER, CONSUMER_SIZE),
                    Arm9.from_bytes(data).leggi(CONSUMER, CONSUMER_SIZE))

                parsed = gifts_scripts.decode(
                    after[SCRIPT_MEMBER], commands, SCRIPT_MEMBER)
                self.assertEqual(parsed.errori, [])

                absent = LegendaryGuardBench(
                    parsed, hidden=True, active=0).run()
                self.assertEqual((absent.creates, absent.active, absent.hidden),
                                 (1, 1, False))
                absent.run()
                self.assertEqual((absent.creates, absent.active, absent.hidden),
                                 (1, 1, False))

                present = LegendaryGuardBench(
                    parsed, hidden=False, active=1).run()
                self.assertEqual((present.creates, present.active,
                                  present.hidden), (0, 1, False))


if __name__ == '__main__':
    unittest.main()
