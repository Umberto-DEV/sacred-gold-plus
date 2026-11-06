"""Native EN/IT component regression for HG-F16 Giratina PC form statistics."""
import hashlib
import json
from pathlib import Path
import struct
import unittest

from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1

from sgp12.rom import Rom
from .test_azurill_gender_rom import (
    ARGS, CREATE_MON, GET_MON, SET_MON, NativeEvolutionBench, input_image,
    unicorn_works,
)


ROOT = Path(__file__).resolve().parents[2]
V4_ROOT = ROOT / 'local/experiments/balance493-2026-10-28'
V4 = {
    'EN': ('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90',
           147345256),
    'IT': ('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156',
           153228136),
}

OV_BASE = 0x021E5900
PC_EXIT = 0x021E5988
PC_FORM_HELPER = 0x021E64D0
MON_UPDATE_GIRATINA = 0x02071CA0
OVERLAY_GET_DATA = 0x02007290
PC_STORAGE_SET_ACTIVE_BOX = 0x02073E84
OVERLAY_FREE_DATA = 0x02007294
HEAP_DESTROY = 0x0201A9C4

TEMP_MON = 0x022C0000
MANAGER = 0x022D2000
WORK = 0x022D3000
PARTY = 0x022D4000
STORAGE = 0x022D8000
MON_BYTES = 0xEC
FIELDS = (112, 163, 164, 165, 166, 167, 168, 169)
ALTERED = [0, 225, 225, 120, 126, 110, 120, 154]
ORIGIN = [1, 225, 225, 140, 108, 110, 140, 132]


def implementation(case):
    try:
        from . import giratina_pc_form
    except ImportError as error:
        case.fail('HG-F16 producer is not implemented: ' + str(error))
    return giratina_pc_form


def candidate(case, language):
    path = V4_ROOT / ('candidate-v4-%s.nds' % language)
    if not path.is_file():
        case.skipTest('immutable V4 candidate unavailable: ' + str(path))
    data = path.read_bytes()
    case.assertEqual((hashlib.sha256(data).hexdigest(), len(data)), V4[language])
    return data


class PcExitBench:
    """Actual ARM9/overlay 14; only manager cleanup services are test seams."""
    def __init__(self, case, rom, language):
        arm, archives = input_image(case, language)
        self.native = NativeEvolutionBench(arm, archives)
        v, _stream, image = Rom(rom).immagine_overlay(14)
        case.assertEqual((v['ram'], len(image)), (OV_BASE, 0x13A80))
        self.native.cpu.mem_write(OV_BASE, image)
        self.events = []
        self.native.cpu.hook_add(UC_HOOK_CODE, self._manager_seams)

    def _manager_seams(self, cpu, address, _size, _user):
        r0 = cpu.reg_read(UC_ARM_REG_R0)
        r1 = cpu.reg_read(UC_ARM_REG_R1)
        if address == OVERLAY_GET_DATA:
            self.events.append(['get_data', r0])
            self.native.ret(WORK)
        elif address == PC_STORAGE_SET_ACTIVE_BOX:
            self.events.append(['set_active', r0, r1])
            self.native.ret(0)
        elif address == OVERLAY_FREE_DATA:
            self.events.append(['free_data', r0])
            self.native.ret(0)
        elif address == HEAP_DESTROY:
            self.events.append(['heap_destroy', r0])
            self.native.ret(0)

    def create(self, address, species):
        self.native.call(CREATE_MON, TEMP_MON, species, 50, 31, 1,
                         0x12345678, 1, 0x10203040)
        self.native.cpu.mem_write(
            address, bytes(self.native.cpu.mem_read(TEMP_MON, MON_BYTES)))

    def party(self, species=(487, 150)):
        self.native.cpu.mem_write(PARTY, struct.pack('<II', 6, len(species)))
        for index, item in enumerate(species):
            self.create(PARTY + 8 + MON_BYTES * index, item)
        self.native.cpu.mem_write(WORK + 4, struct.pack('<I', STORAGE))
        self.native.cpu.mem_write(WORK + 8, struct.pack('<I', PARTY))
        self.native.cpu.mem_write(WORK + 0x1F, b'\x03')

    def set_item(self, mon, item):
        self.native.put(ARGS, item)
        self.native.call(SET_MON, mon, 6, ARGS)

    def stats(self, mon):
        return [self.native.call(GET_MON, mon, field, 0) for field in FIELDS]

    def bytes(self, mon):
        return bytes(self.native.cpu.mem_read(mon, MON_BYTES))

    def exit(self):
        return self.native.call(PC_EXIT, MANAGER, 0)


class GiratinaPcFormNativeTests(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        if not unicorn_works():
            self.skipTest('local Unicorn engine unavailable before guest execution')

    def test_pc_party_change_is_red_on_v4_and_green_after_exit_repair(self):
        """Catches omitting the party reconciliation or calling it after work is freed."""
        G = implementation(self)
        rows = []
        for language in V4:
            before = candidate(self, language)
            after, receipt = G.apply(before, language)
            for phase, rom in (('retail', before), ('fixed', after)):
                bench = PcExitBench(self, rom, language)
                bench.party()
                giratina = PARTY + 8
                other = giratina + MON_BYTES
                other_before = bench.bytes(other)
                bench.set_item(giratina, 112)
                self.assertEqual(bench.native.call(PC_FORM_HELPER, giratina), 1)
                stale = bench.stats(giratina)
                exit_result = bench.exit()
                result = {
                    'language': language, 'phase': phase,
                    'stale': stale, 'after': bench.stats(giratina),
                    'other_unchanged': bench.bytes(other) == other_before,
                    'events': bench.events, 'exit': exit_result,
                    'assertions': bench.native.assertions,
                }
                rows.append(result)
                with self.subTest(language=language, phase=phase):
                    self.assertEqual(stale, [1] + ALTERED[1:])
                    self.assertEqual(result['after'],
                                     [1] + (ALTERED[1:] if phase == 'retail'
                                            else ORIGIN[1:]))
                    self.assertTrue(result['other_unchanged'])
                    self.assertEqual(exit_result, 1)
                    self.assertEqual(bench.events, [
                        ['get_data', MANAGER], ['set_active', STORAGE, 3],
                        ['free_data', MANAGER], ['heap_destroy', 9],
                    ])
                    self.assertEqual(bench.native.assertions, 0)
                    self.assertEqual(G.verify(before, after, receipt),
                                     receipt['verification'])
        self.assertEqual(hashlib.sha256(json.dumps(
            rows, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
            'f9b8be87cc849a441fd61739b2c0c0b2fa948e47a243a0f2a7db49c5f72ad352')

    def test_reverse_change_and_open_without_item_change_are_stable(self):
        """Catches force_origin=1 and regressions when the PC closes without a change."""
        G = implementation(self)
        for language in V4:
            before = candidate(self, language)
            after, _receipt = G.apply(before, language)

            reverse = PcExitBench(self, after, language)
            reverse.party()
            giratina = PARTY + 8
            reverse.set_item(giratina, 112)
            reverse.native.call(MON_UPDATE_GIRATINA, giratina)
            self.assertEqual(reverse.stats(giratina), ORIGIN)
            reverse.set_item(giratina, 0)
            reverse.native.call(PC_FORM_HELPER, giratina)
            self.assertEqual(reverse.stats(giratina), [0] + ORIGIN[1:])
            reverse.exit()
            with self.subTest(language=language, case='remove-orb'):
                self.assertEqual(reverse.stats(giratina), ALTERED)

            no_change = PcExitBench(self, after, language)
            no_change.party()
            giratina = PARTY + 8
            other = giratina + MON_BYTES
            giratina_before = no_change.bytes(giratina)
            other_before = no_change.bytes(other)
            stats_before = no_change.stats(giratina)
            no_change.exit()
            with self.subTest(language=language, case='open-close'):
                self.assertEqual(stats_before, ALTERED)
                self.assertEqual(no_change.stats(giratina), ALTERED)
                self.assertEqual(no_change.bytes(giratina), giratina_before)
                self.assertEqual(no_change.bytes(other), other_before)
                self.assertEqual(no_change.native.assertions, 0)


if __name__ == '__main__':
    unittest.main()
