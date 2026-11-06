"""HG-F24 component reproducer on the immutable EN/IT V4 candidates.

The retail report requires GB Sounds to be enabled and the evolution flow to
open Pokemon Summary so that an old move can be selected.  This test does not
pretend to capture PCM or to play that UI.  It authenticates and follows the
real machine-code boundaries which make that report possible:

* the evolution state machine starts ``SEQ_GS_SHINKA`` (1011);
* the GB dispatcher maps it to the dynamically loaded sequence 1223;
* Pokemon Summary enters sound scene 57, which restores sound-heap state 4;
* the evolution state machine has no BGM reload after Summary returns.

The bounded replay records the resulting resource lifetime.  GB-off and a
move learned without opening Summary are negative controls.  ROMs and saves
are read only and no patched image is written.
"""
from dataclasses import dataclass
import hashlib
from pathlib import Path
import unittest

from sgp12.rom import Arm9, bl_decode


ROOT = Path(__file__).resolve().parents[2]
V4_ROOT = ROOT / 'local/experiments/balance493-2026-10-28'
V4 = {
    'EN': ('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90',
           147345256),
    'IT': ('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156',
           153228136),
}

SEQ_GS_SHINKA = 1011
SEQ_GS_P_SHINKA = 1223
GB_TABLE = 0x020F5730
GB_EVOLUTION_PAIR = 5

EVOLUTION_PLAY_SITE = 0x020760F4
EVOLUTION_PLAY_SIZE = 40
EVOLUTION_PLAY_SHA256 = 'e9a5e5c09cf0788a3893a261c55a0e099cf8318f247727e0d06501cafca27a8d'
EVOLUTION_SEQ_LITERAL = 0x02076224
EVOLUTION_START = 0x02075E14
EVOLUTION_END = 0x02076C76
START_SEQUENCE = 0x02005D10
PLAY_BGM = 0x02005D48
STOP_BGM = 0x02005EB4

SUMMARY_FLOW = 0x020766BC
SUMMARY_FLOW_SIZE = 280
SUMMARY_FLOW_SHA256 = '5d822af6973be24dcd4628dcd7b5fe50e6d9c6c62b9561e20b1482510f0c3cf5'
SUMMARY_CONSTRUCTOR = 0x02077394
SUMMARY_RETURN = 0x02076748

PARTY_SCENE_SITE = 0x02078EB8
PARTY_SCENE_SIZE = 48
PARTY_SCENE_SHA256 = '4165fc8506d6aa76db2cd247f1923d3ae1644866439b228499ebdcd6271361ad'
SET_SCENE_AND_PLAY = 0x02004EC4

GB_START = 0x02006C14
GB_START_SIZE = 120
GB_START_SHA256 = '8dd8ea788abaeca3e9da9d8650fedeb114516d8a5a77b14f62a0004cdef616ab'
GB_STATE = 0x02005C18
GB_TRANSLATE = 0x02005C6C
LOAD_SEQ_EX = 0x02004784

SCENE57 = 0x020052C8
SCENE57_SIZE = 28
SCENE57_SHA256 = '8493ada56ea82b0a25411cb421ea1f1c6487b5c9f093478f98775e1813f270cd'
LOAD_STATE4 = 0x02005318
LOAD_STATE4_SIZE = 16
LOAD_STATE4_SHA256 = 'a9b20de7630c0c6cb0655d42a8520796aa3f72973a2d2eb110da462cc1eed855'
STATE_SELECTOR = 0x02005328
STATE_SELECTOR_SIZE = 128
STATE_SELECTOR_SHA256 = '9c68afbac442e8d045ff01fdec7242e559b16383658f14df1a5dcfa0e49aea05'
SOUND_HEAP_LOAD_STATE = 0x02004714


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _calls(arm, start, end):
    """Return decoded Thumb BL sites without interpreting unrelated opcodes."""
    result = []
    for pc in range(start, end, 2):
        raw = arm.leggi(pc, 4)
        if int.from_bytes(raw[:2], 'little') & 0xF800 != 0xF000:
            continue
        try:
            target = bl_decode(pc, raw)
        except ValueError:
            continue
        result.append((pc, target))
    return tuple(result)


def _candidate(case, language):
    path = V4_ROOT / ('candidate-v4-%s.nds' % language)
    if not path.is_file():
        case.skipTest('immutable V4 candidate unavailable: ' + str(path))
    data = path.read_bytes()
    case.assertEqual((_sha(data), len(data)), V4[language])
    return path, data, Arm9.from_bytes(data)


def _implementation(case):
    try:
        from . import gb_sounds_evolution
    except ImportError as error:
        case.fail('HG-F24 producer is not implemented: ' + str(error))
    return gb_sounds_evolution


class WrapperReplay:
    """Small independent Thumb-1 replay for the installed HG-F24 wrapper.

    External calls are boundaries, not mocks of the wrapper: the replay
    decodes their real BL targets and applies their documented return
    contracts.  This avoids treating a host Unicorn SIGILL as evidence while
    still executing every wrapper instruction and its stack operations.
    """

    def __init__(self, code, address, *, gb_state):
        self.code = bytes(code)
        self.address = address
        self.pc = address
        self.sp = 0x02710000
        self.lr = 0x0271F001
        self.regs = [0xA0000000 + index for index in range(13)]
        self.stack = {}
        self.gb_state = gb_state
        self.calls = []

    def _u16(self, address):
        offset = address - self.address
        return int.from_bytes(self.code[offset:offset + 2], 'little')

    def _call(self, target):
        self.calls.append((target, self.regs[0]))
        if target == 0x0203A880:
            self.regs[0] = 0x13579BDF
        elif target == GB_STATE:
            self.regs[0] = self.gb_state
        elif target == START_SEQUENCE:
            if self.regs[0] != SEQ_GS_SHINKA:
                raise AssertionError('wrong sequence passed to StartSequence')
            self.regs[0] = 1
        else:
            raise AssertionError('unexpected external call %#x' % target)

    def run(self):
        initial_callee = tuple(self.regs[4:12])
        initial_sp = self.sp
        while True:
            opcode = self._u16(self.pc)
            if opcode == 0xB508:  # push {r3,lr}
                self.sp -= 8
                self.stack[self.sp] = self.regs[3]
                self.stack[self.sp + 4] = self.lr
                self.pc += 2
            elif opcode & 0xF800 == 0xF000:
                raw = self.code[self.pc - self.address:self.pc - self.address + 4]
                target = bl_decode(self.pc, raw)
                self.lr = (self.pc + 4) | 1
                self._call(target)
                self.pc += 4
            elif opcode == 0x2801:  # cmp r0,#1
                self.zero = self.regs[0] == 1
                self.pc += 2
            elif opcode & 0xFF00 == 0xD100:  # bne
                immediate = opcode & 0xFF
                if immediate & 0x80:
                    immediate -= 0x100
                self.pc = (self.pc + 4 + 2 * immediate
                           if not self.zero else self.pc + 2)
            elif opcode & 0xF800 == 0x4800:  # ldr r0,[pc,#imm]
                literal = ((self.pc + 4) & ~3) + 4 * (opcode & 0xFF)
                offset = literal - self.address
                self.regs[0] = int.from_bytes(self.code[offset:offset + 4], 'little')
                self.pc += 2
            elif opcode == 0xBD08:  # pop {r3,pc}
                self.regs[3] = self.stack[self.sp]
                destination = self.stack[self.sp + 4]
                self.sp += 8
                self.pc = destination & ~1
                break
            else:
                raise AssertionError('unsupported wrapper opcode %#06x at %#x'
                                     % (opcode, self.pc))
        if self.sp != initial_sp:
            raise AssertionError('wrapper changed SP')
        if tuple(self.regs[4:12]) != initial_callee:
            raise AssertionError('wrapper changed a callee-saved register')
        return tuple(self.calls)


@dataclass(frozen=True)
class AudioResult:
    current_sequence: int
    current_resource_present: bool
    audible: bool
    events: tuple


def replay(*, gb_sounds, opens_summary):
    """Replay only the authenticated sound-resource lifetime of HG-F24.

    The DS evolution sequence belongs to the already retained sound material.
    Its GB counterpart is loaded on demand after state 4.  Loading state 4
    therefore removes only the latter.  The authenticated evolution function
    has no subsequent start/play call which could recover it.
    """
    events = ['start:%d' % SEQ_GS_SHINKA]
    sequence = SEQ_GS_SHINKA
    resource_present = True
    dynamically_loaded_after_state4 = False
    if gb_sounds:
        sequence = SEQ_GS_P_SHINKA
        dynamically_loaded_after_state4 = True
        events.extend(('translate:%d->%d' % (SEQ_GS_SHINKA, sequence),
                       'dynamic-load:%d' % sequence))
    else:
        events.append('retain-preloaded:%d' % sequence)

    if opens_summary:
        events.extend(('scene:57', 'load-state:4'))
        if dynamically_loaded_after_state4:
            resource_present = False
            events.append('evict:%d' % sequence)
        else:
            events.append('retain:%d' % sequence)
        events.append('return-without-bgm-reload')
    else:
        events.append('no-summary')

    return AudioResult(sequence, resource_present, resource_present,
                       tuple(events))


class GbSoundsEvolutionRomTests(unittest.TestCase):
    def test_real_candidates_authenticate_the_complete_audio_path(self):
        for language in V4:
            with self.subTest(language=language):
                path, original, arm = _candidate(self, language)
                self.assertEqual(_sha(arm.leggi(EVOLUTION_PLAY_SITE,
                                                EVOLUTION_PLAY_SIZE)),
                                 EVOLUTION_PLAY_SHA256)
                self.assertEqual(_sha(arm.leggi(SUMMARY_FLOW,
                                                SUMMARY_FLOW_SIZE)),
                                 SUMMARY_FLOW_SHA256)
                self.assertEqual(_sha(arm.leggi(PARTY_SCENE_SITE,
                                                PARTY_SCENE_SIZE)),
                                 PARTY_SCENE_SHA256)
                self.assertEqual(_sha(arm.leggi(GB_START, GB_START_SIZE)),
                                 GB_START_SHA256)
                self.assertEqual(_sha(arm.leggi(SCENE57, SCENE57_SIZE)),
                                 SCENE57_SHA256)
                self.assertEqual(_sha(arm.leggi(LOAD_STATE4, LOAD_STATE4_SIZE)),
                                 LOAD_STATE4_SHA256)
                self.assertEqual(_sha(arm.leggi(STATE_SELECTOR,
                                                STATE_SELECTOR_SIZE)),
                                 STATE_SELECTOR_SHA256)

                pair = arm.leggi(GB_TABLE + GB_EVOLUTION_PAIR * 4, 4)
                self.assertEqual(tuple(int.from_bytes(pair[i:i + 2], 'little')
                                       for i in (0, 2)),
                                 (SEQ_GS_SHINKA, SEQ_GS_P_SHINKA))
                self.assertEqual(arm.u32(EVOLUTION_SEQ_LITERAL), SEQ_GS_SHINKA)

                evolution_calls = _calls(arm, EVOLUTION_START, EVOLUTION_END)
                self.assertIn((0x02076104, START_SEQUENCE), evolution_calls)
                self.assertIn((0x02076734, SUMMARY_CONSTRUCTOR), evolution_calls)
                self.assertNotIn(PLAY_BGM,
                                 [target for site, target in evolution_calls
                                  if site >= SUMMARY_RETURN])
                self.assertNotIn(START_SEQUENCE,
                                 [target for site, target in evolution_calls
                                  if site >= SUMMARY_RETURN])
                # Cleanup eventually stops both the DS sequence and its GB
                # mapping.  It cannot restore the resource evicted earlier.
                self.assertIn((0x02076B30, STOP_BGM), evolution_calls)

                party_calls = dict(_calls(arm, PARTY_SCENE_SITE,
                                          PARTY_SCENE_SITE + PARTY_SCENE_SIZE))
                self.assertEqual(party_calls[0x02078ED6], SET_SCENE_AND_PLAY)
                # movs r1,#0; movs r0,#57; movs r2,r1
                self.assertEqual(arm.leggi(0x02078ED0, 6),
                                 bytes.fromhex('002139200a1c'))

                gb_calls = dict(_calls(arm, GB_START, GB_START + GB_START_SIZE))
                self.assertEqual(gb_calls[0x02006C2A], GB_STATE)
                self.assertEqual(gb_calls[0x02006C36], GB_TRANSLATE)
                self.assertEqual(gb_calls[0x02006C66], LOAD_SEQ_EX)

                scene_calls = dict(_calls(arm, SCENE57,
                                           SCENE57 + SCENE57_SIZE))
                self.assertEqual(scene_calls[0x020052CC], LOAD_STATE4)
                state_calls = dict(_calls(arm, LOAD_STATE4,
                                           LOAD_STATE4 + LOAD_STATE4_SIZE))
                self.assertEqual(arm.leggi(LOAD_STATE4 + 2, 2),
                                 bytes.fromhex('0420'))  # movs r0,#4
                self.assertEqual(state_calls[0x0200531C], STATE_SELECTOR)
                self.assertEqual(state_calls[0x02005320],
                                 SOUND_HEAP_LOAD_STATE)
                self.assertEqual(_sha(path.read_bytes()), _sha(original))

    def test_gb_summary_path_loses_the_dynamic_evolution_sequence(self):
        first = replay(gb_sounds=True, opens_summary=True)
        second = replay(gb_sounds=True, opens_summary=True)
        self.assertEqual(first, second)
        self.assertEqual(first.current_sequence, SEQ_GS_P_SHINKA)
        self.assertFalse(first.current_resource_present)
        self.assertFalse(first.audible)
        self.assertIn('evict:1223', first.events)
        self.assertEqual(first.events[-1], 'return-without-bgm-reload')

    def test_negative_controls_keep_music_material_available(self):
        gb_off = replay(gb_sounds=False, opens_summary=True)
        free_move_slot = replay(gb_sounds=True, opens_summary=False)
        self.assertEqual((gb_off.current_sequence, gb_off.audible),
                         (SEQ_GS_SHINKA, True))
        self.assertEqual((free_move_slot.current_sequence,
                          free_move_slot.audible),
                         (SEQ_GS_P_SHINKA, True))
        self.assertNotIn('evict:1223', free_move_slot.events)

    def test_repair_reloads_only_the_evicted_gb_sequence(self):
        fix = _implementation(self)
        for language in V4:
            _, before, _ = _candidate(self, language)
            after, receipt = fix.apply(before, language)
            arm = Arm9.from_bytes(after)
            with self.subTest(language=language, gb='on'):
                calls = WrapperReplay(arm.leggi(fix.SLOT, fix.SLOT_BYTES),
                                      fix.SLOT, gb_state=1).run()
                self.assertEqual(calls,
                                 ((0x0203A880, 0xA0000000),
                                  (GB_STATE, 0x13579BDF),
                                  (START_SEQUENCE, SEQ_GS_SHINKA)))
            with self.subTest(language=language, gb='off'):
                calls = WrapperReplay(arm.leggi(fix.SLOT, fix.SLOT_BYTES),
                                      fix.SLOT, gb_state=0).run()
                self.assertEqual(calls,
                                 ((0x0203A880, 0xA0000000),
                                  (GB_STATE, 0x13579BDF)))
            self.assertEqual(fix.verify(before, after, receipt),
                             receipt['verification'])

    def test_repair_is_confined_and_rejects_foreign_inputs(self):
        fix = _implementation(self)
        _, before, _ = _candidate(self, 'EN')
        after, receipt = fix.apply(before, 'EN')
        changed = {index for index, pair in enumerate(zip(before, after))
                   if pair[0] != pair[1]}
        allowed = set()
        for start, end in fix.spans(before):
            allowed.update(range(start, end))
        self.assertTrue(changed)
        self.assertLessEqual(changed, allowed)
        self.assertEqual(len(before), len(after))
        self.assertTrue(receipt['save_layout_unchanged'])
        self.assertTrue(receipt['rom_geometry_unchanged'])
        with self.assertRaises(ValueError):
            fix.apply(after, 'EN')
        with self.assertRaises(ValueError):
            fix.apply(before, 'IT')


if __name__ == '__main__':
    unittest.main()
