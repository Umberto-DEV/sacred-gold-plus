"""Eligibility, refusal of non-ordinary parties and the "R: Box" prompt (Unicorn, real V4 bytes).

The activity data are the words the start menu itself computed (StartMenu_Init variants):
inhibitIconFlags at owner+0x34C and unk_350 at owner+0x350, plus the avatar state.
"""
import struct
import unittest

import portable_bench as pb
from portable_bench import PARTY, FIELD, OWNER, AVATAR, TASK, N
from test_runtime import world, Cycle, ALL_ON, PHASE, STATE1_REQUEST_EXIT

LANGUAGES = ('EN', 'IT')
ELIGIBLE, WRONG_OWNER, BUSY, SPECIAL_ACTIVITY, UNPROVEN_TRAVEL, UNPROVEN_CONTEXT = range(6)
R = 1 << 8
# inhibit flag words produced by the start menu (pret start_menu.c, StartMenu_Init and friends)
NORMAL_FLAGS = (0x180, 0x181, 0x182, 0x184, 0x200 | 0x180, 0x1 | 0x2 | 0x4 | 0x200 | 0x180)
SPECIAL_FLAGS = {
    'safari': 0x10 | 0x80,
    'bug contest': 0x04 | 0x10 | 0x80,
    'pal park': 0x04 | 0x10 | 0x80,
    'battle tower partner room': 0x01 | 0x04 | 0x10 | 0x80 | 0x100 | 0x200,
    'colosseum': 0x01 | 0x10 | 0x80 | 0x100 | 0x200,
    'union room': 0x10 | 0x100,
    'trainer card inhibited': 0x180 | 0x08,
    'options inhibited': 0x180 | 0x20,
    'running shoes inhibited': 0x180 | 0x40,
    'no retire/7 bits': 0x00,
    'only bit 7': 0x80,
    'only the RETIRE bit': 0x100,
    'bits 7 and 9 without RETIRE': 0x80 | 0x200,
}
MSG_CHOOSE = 29


def eligibility(w, field=FIELD, owner=OWNER):
    return w.blob_call('sgp_box_eligibility', field, owner)


class Eligibility(unittest.TestCase):
    def test_special_activity_and_unproven_travel_refuse(self):
        for language in LANGUAGES:
            for flags in NORMAL_FLAGS:
                w = world(self, language, True, ALL_ON)
                w.open_party(flags=flags)
                self.assertEqual(eligibility(w), ELIGIBLE, hex(flags))
            for name, flags in SPECIAL_FLAGS.items():
                with self.subTest(language=language, activity=name):
                    w = world(self, language, True, ALL_ON)
                    w.open_party(flags=flags)
                    self.assertEqual(eligibility(w), SPECIAL_ACTIVITY)
                    self.assertEqual(w.state('reason'), SPECIAL_ACTIVITY, 'decision recorded at bind')
            w = world(self, language, True, ALL_ON)
            w.open_party(unk350=1)
            self.assertEqual(eligibility(w), SPECIAL_ACTIVITY, 'Union Room style unk_350')
            for state, expected in ((0, ELIGIBLE), (1, ELIGIBLE), (2, UNPROVEN_TRAVEL), (3, UNPROVEN_TRAVEL), (7, UNPROVEN_TRAVEL),
                                    (8, UNPROVEN_TRAVEL), (0xFFFFFFFF, UNPROVEN_TRAVEL)):
                with self.subTest(language=language, avatar_state=state):
                    w = world(self, language, True, ALL_ON)
                    w.open_party(avatar_state=state)
                    self.assertEqual(eligibility(w), expected)
            w = world(self, language, True, ALL_ON)
            w.open_party(avatar_state=2)
            w.set_cfg('travel_mask', 0b111)               # Codex enables Surf after the Android proof
            self.assertEqual(eligibility(w), ELIGIBLE)
            w.set_cfg('travel_mask', 0)
            w.w32(AVATAR + 0x18, 0)
            self.assertEqual(eligibility(w), UNPROVEN_TRAVEL, 'mask 0 allows nothing')
            w.w32(FIELD + 0x40, 0)                         # no avatar at all
            self.assertEqual(eligibility(w), UNPROVEN_TRAVEL)

    def test_wrong_owner_and_busy(self):
        for language in LANGUAGES:
            w = world(self, language, True, ALL_ON)
            w.open_party()
            self.assertEqual(eligibility(w, 0, OWNER), WRONG_OWNER)
            self.assertEqual(eligibility(w, FIELD, 0), WRONG_OWNER)
            self.assertEqual(eligibility(w, FIELD + 4, OWNER), WRONG_OWNER)
            self.assertEqual(eligibility(w, FIELD, OWNER + 4), WRONG_OWNER)
            w.w16(OWNER + 0x26, 4)                          # WAIT_FADE: the start menu is not waiting for the app
            self.assertEqual(eligibility(w), BUSY)
            w.w16(OWNER + 0x26, 5)
            self.assertEqual(eligibility(w), ELIGIBLE)
            w.set_state('phase', PHASE['IDLE'])
            self.assertEqual(eligibility(w), WRONG_OWNER)

    def test_nonordinary_party_never_opens(self):
        for language in LANGUAGES:
            for context in range(1, 0x19):
                with self.subTest(language=language, context=context):
                    w = world(self, language, True, ALL_ON)
                    args = w.call(N['create_args'], 0x0B, FIELD, 0, context)
                    w.w32(args + 0x18, OWNER + 0x370)
                    w.w32(OWNER + 0x380, args)
                    w.w16(OWNER + 0x26, 5)
                    w.w32(OWNER + 0x34C, 0x180)
                    w.blob_call('sgp_box_bind', FIELD, args)
                    self.assertEqual(w.state('phase'), PHASE['IDLE'], 'never bound')
                    w.uc.mem_write(PARTY, bytes(0xCB0))
                    w.w32(PARTY + 0x654, args)
                    w.set_state('prompt_shown', 1)
                    w.set_state('requested', 1)
                    w.set_inputs(held=R, new=R)
                    mark = len(w.events)
                    self.assertEqual(w.blob_call('sgp_box_party_main', PARTY), w.main_normal_return)
                    self.assertEqual(w.u8(args + 0x27), 0)
                    self.assertEqual(w.state('requested'), 0)
                    self.assertEqual([e for e in w.events[mark:] if e[0] in ('heap_alloc', 'heap_free', 'play_se')], [])
                    self.assertEqual(w.launches, [])
            # a bound ordinary party whose activity is special: no allocation, no child, nothing changed
            for name, flags in SPECIAL_FLAGS.items():
                with self.subTest(language=language, activity=name):
                    w = world(self, language, True, ALL_ON)
                    cycle = Cycle(w)
                    w.w32(OWNER + 0x34C, flags)
                    w.set_state('prompt_shown', 1)
                    w.set_inputs(held=R, new=R)
                    mark = len(w.events)
                    self.assertEqual(w.blob_call('sgp_box_party_main', PARTY), w.main_normal_return)
                    self.assertEqual(w.state('phase'), PHASE['BOUND'])
                    self.assertEqual([e for e in w.events[mark:] if e[0] in ('heap_alloc', 'heap_free', 'play_se')], [])
                    self.assertEqual(w.u8(cycle.args + 0x27), 0)
                    self.assertEqual(len(w.launches), 1)


class OrdinaryContext(unittest.TestCase):
    """Deny by default: a positive, verified signal of the ordinary field is required."""

    def test_structures_escort_and_link_are_refused_without_allocations(self):
        cases = {
            'battle frontier facility (frontierFsys)': lambda w: w.w32(FIELD + 0xA0, 0x02399990),
            'link battle ruleset': lambda w: w.w32(FIELD + 0xA4, 0x02399990),
            'safari load type': lambda w: w.w32(FIELD + 0x70, 1),
            'union load type': lambda w: w.w32(FIELD + 0x70, 2),
            'colosseum load type': lambda w: w.w32(FIELD + 0x70, 3),
            'battle tower load type': lambda w: w.w32(FIELD + 0x70, 4),
            'load type 5': lambda w: w.w32(FIELD + 0x70, 5),
            'escort / obligatory follower flag': lambda w: setattr(w, 'escort', 1),
        }
        for language in LANGUAGES:
            for name, setup in cases.items():
                with self.subTest(language=language, case=name):
                    w = world(self, language, True, ALL_ON)
                    cycle = Cycle(w)
                    setup(w)
                    self.assertEqual(eligibility(w), SPECIAL_ACTIVITY)
                    w.set_state('prompt_shown', 1)
                    w.set_state('requested', 1)
                    w.set_inputs(held=R, new=R)
                    mark = len(w.events)
                    self.assertEqual(w.blob_call('sgp_box_party_main', PARTY), w.main_normal_return)
                    self.assertEqual([e for e in w.events[mark:] if e[0] in ('heap_alloc', 'heap_free', 'play_se')], [])
                    self.assertEqual(w.u8(cycle.args + 0x27), 0)
                    self.assertEqual(len(w.launches), 1)
                    self.assertEqual(w.state('requested'), 0)

    def test_escort_flag_is_read_through_the_native_accessors_with_the_save_data(self):
        for language in LANGUAGES:
            w = world(self, language, True, ALL_ON)
            w.open_party()
            self.assertEqual(eligibility(w), ELIGIBLE)
            calls = [e[0] for e in w.events if e[0] in ('vars_get', 'check_follower')]
            self.assertEqual(calls, ['vars_get', 'check_follower'])
            self.assertEqual([e[1] for e in w.events if e[0] == 'vars_get'], [(pb.SAVEDATA,)])
            self.assertEqual([e[1] for e in w.events if e[0] == 'check_follower'], [(pb.VARS_FLAGS,)])

    def test_missing_context_proof_denies_everything(self):
        for language in LANGUAGES:
            w = world(self, language, True, ALL_ON)
            cycle = Cycle(w)
            w.set_cfg('context_proof', 0)
            self.assertEqual(eligibility(w), UNPROVEN_CONTEXT)
            w.set_state('prompt_shown', 1)
            w.set_inputs(held=R, new=R)
            mark = len(w.events)
            self.assertEqual(w.blob_call('sgp_box_party_main', PARTY), w.main_normal_return)
            self.assertEqual([e for e in w.events[mark:] if e[0] in ('heap_alloc', 'play_se')], [])
            w.blob_call('sgp_box_prompt_print', PARTY, PARTY + 0x204, MSG_CHOOSE, 1)
            self.assertEqual([e for e in w.events if e[0] == 'add_printer'], [])
            w.set_cfg('context_proof', 2)                      # only the exact installed word counts
            self.assertEqual(eligibility(w), UNPROVEN_CONTEXT)
            w.set_cfg('context_proof', 1)
            self.assertEqual(eligibility(w), ELIGIBLE)

    def test_prompt_requires_bridge_and_input(self):
        for language in LANGUAGES:
            for activation in (dict(prompt=1, context_proof=1), dict(prompt=1, bridge=1, context_proof=1),
                               dict(prompt=1, input=1, context_proof=1)):
                with self.subTest(language=language, activation=activation):
                    w = world(self, language, True, activation)
                    w.open_party()
                    w.blob_call('sgp_box_prompt_print', PARTY, PARTY + 0x204, MSG_CHOOSE, 1)
                    self.assertEqual([e for e in w.events if e[0] == 'add_printer'], [], 'no label for a command that does nothing')


class LiveBinding(unittest.TestCase):
    def test_state_one_binds_an_unbound_party_but_never_trusts_a_request_written_before_it(self):
        for language in LANGUAGES:
            w = world(self, language, True, dict(bridge=1, input=1, context_proof=1))     # no prompt: nothing drew a suffix
            w.open_unbound()
            w.set_state('requested', 1)           # a probe write on a party the record had never bound
            self.assertEqual(w.blob_call('sgp_box_party_main', PARTY), w.main_normal_return)
            self.assertEqual((w.state('phase'), w.state('generation'), w.state('requested'), w.state('failures')),
                             (PHASE['BOUND'], 1, 0, 1), 'bound now; the earlier write is dropped, not obeyed')
            w.set_state('requested', 1)
            self.assertEqual(w.blob_call('sgp_box_party_main', PARTY), STATE1_REQUEST_EXIT, 'a write made after the bind is accepted')

    def test_bag_return_without_item_is_bound_lazily_and_deterministically(self):
        for language in LANGUAGES:
            for trial in range(3):                          # the allocator's addresses must not matter
                w = world(self, language, True, ALL_ON)
                w.heap_next += 0x400 * trial
                w.open_unbound()
                self.assertEqual(w.state('phase'), PHASE['IDLE'], 'no hook ran: nothing bound yet')
                w.blob_call('sgp_box_prompt_print', PARTY, PARTY + 0x204, MSG_CHOOSE, 1)
                self.assertEqual(len([e for e in w.events if e[0] == 'add_printer']), 1, 'suffix shown')
                self.assertEqual((w.state('phase'), w.state('generation')), (PHASE['BOUND'], 1))
                self.assertEqual((w.state('field'), w.state('owner'), w.state('args')), (FIELD, OWNER, w.args))
                w.set_inputs(held=R, new=R)
                self.assertEqual(w.blob_call('sgp_box_party_main', PARTY), STATE1_REQUEST_EXIT)

    def test_swap_declined_party_keeps_a_fixed_behaviour(self):
        for language in LANGUAGES:
            w = world(self, language, True, ALL_ON)
            w.open_unbound(context=10)                       # item-swap flow: not ordinary, never bound
            w.blob_call('sgp_box_prompt_print', PARTY, PARTY + 0x204, MSG_CHOOSE, 1)
            self.assertEqual([e for e in w.events if e[0] == 'add_printer'], [])
            self.assertEqual(w.state('phase'), PHASE['IDLE'])
            w.w8(w.args + 0x24, 0)                           # PartyMenu_SwitchItemsDeclined: context 10 -> 0, state 1
            w.set_inputs(held=R, new=R)
            self.assertEqual(w.blob_call('sgp_box_party_main', PARTY), w.main_normal_return,
                             'no suffix was shown for this prompt, so no command is active')
            w.blob_call('sgp_box_prompt_print', PARTY, PARTY + 0x204, MSG_CHOOSE, 1)     # the next native reprint of message 29
            self.assertEqual(len([e for e in w.events if e[0] == 'add_printer']), 1)
            w.set_inputs(held=R, new=R)
            self.assertEqual(w.blob_call('sgp_box_party_main', PARTY), STATE1_REQUEST_EXIT)

    def test_lazy_bind_needs_the_live_task_environment_and_the_native_callback(self):
        for language in LANGUAGES:
            edits = {
                'task environment is another owner': lambda w: w.w32(TASK + 0xC, OWNER + 0x800),
                'no live task manager': lambda w: w.w32(FIELD + 0x10, 0),
                'exit callback is not the native party callback': lambda w: w.w32(OWNER + 0x354, 0x0203D581),
                'owner not waiting for the application': lambda w: w.w16(OWNER + 0x26, 4),
                'environment parked': lambda w: w.w32(OWNER + 0x380, 0x02399990),
                'foreign field': lambda w: w.w32(w.args + 0x1C, FIELD + 0x40),
                'null field system': lambda w: w.w32(w.args + 0x1C, 0),
            }
            for name, edit in edits.items():
                with self.subTest(language=language, case=name):
                    w = world(self, language, True, ALL_ON)
                    w.open_unbound()
                    edit(w)
                    w.blob_call('sgp_box_prompt_print', PARTY, PARTY + 0x204, MSG_CHOOSE, 1)
                    self.assertEqual([e for e in w.events if e[0] == 'add_printer'], [])
                    self.assertEqual(w.state('phase'), PHASE['IDLE'])

    def test_lazy_bind_never_replaces_a_request_in_flight(self):
        for language in LANGUAGES:
            w = world(self, language, True, ALL_ON)
            cycle = Cycle(w)
            cycle.accept_request()
            self.assertEqual(w.state('phase'), PHASE['EXITING'])
            generation = w.state('generation')
            w.blob_call('sgp_box_prompt_print', PARTY, PARTY + 0x204, MSG_CHOOSE, 1)
            self.assertEqual((w.state('phase'), w.state('generation')), (PHASE['EXITING'], generation))


class Prompt(unittest.TestCase):
    LABEL = (0x013C, 0x01C4, 0x01DE, 0x012C, 0x0153, 0x015C)   # R : space B o x (charmap)

    def printer_calls(self, w):
        return [e for e in w.events if e[0] == 'add_printer']

    def test_choose_prompt_only(self):
        for language in LANGUAGES:
            window = PARTY + 0x204
            w = world(self, language, True, ALL_ON)
            w.open_party()
            w.blob_call('sgp_box_prompt_print', PARTY, window, MSG_CHOOSE, 1)
            printer = self.printer_calls(w)
            self.assertEqual(len(printer), 1, 'exactly one suffix print')
            win, font, text, x, y, speed, callback = printer[0][1]
            self.assertEqual((win, font, x, y, speed, callback), (window, 1, 112, 0, 0xFF, 0))
            maxsize, size, magic = struct.unpack('<HHI', bytes(w.uc.mem_read(text, 8)))
            codes = struct.unpack('<%dH' % (len(self.LABEL) + 1), bytes(w.uc.mem_read(text + 8, 2 * (len(self.LABEL) + 1))))
            self.assertEqual((maxsize, size, magic), (6, 6, 0xB6F8D2EC), 'native String object')
            self.assertEqual(codes, self.LABEL + (0xFFFF,))
            self.assertEqual([e[0] for e in w.events if e[0] in ('print_ex', 'add_printer', 'copy_vram')],
                             ['print_ex', 'add_printer', 'copy_vram'], 'native text first, suffix after, then one transfer')
            self.assertEqual(w.state('prompt_shown'), 1)
            # every other message erases the suffix and draws nothing
            for message in (0, 28, 30, 32, 33, 34, 35, 37, 103, 184, 0xFFFFFFFF):
                w.events.clear()
                w.set_state('prompt_shown', 1)
                w.blob_call('sgp_box_prompt_print', PARTY, window, message, 1)
                self.assertEqual(self.printer_calls(w), [], message)
                self.assertEqual(w.state('prompt_shown'), 0, message)
            # not the prompt window
            w.events.clear()
            w.blob_call('sgp_box_prompt_print', PARTY, window + 0x10, MSG_CHOOSE, 1)
            self.assertEqual(self.printer_calls(w), [])
            # inactive words, refused activity, foreign party, travel: no suffix
            for label, setup in (('prompt word off', lambda x: x.set_cfg('prompt', 0)),
                                 ('safari', lambda x: x.w32(OWNER + 0x34C, 0x90)),
                                 ('surfing', lambda x: x.w32(AVATAR + 0x18, 2)),
                                 ('foreign args', lambda x: x.w32(PARTY + 0x654, 0x02399990)),
                                 ('context', lambda x: x.w8(x.args + 0x24, 3))):
                w = world(self, language, True, ALL_ON)
                w.open_party()
                setup(w)
                w.blob_call('sgp_box_prompt_print', PARTY, window, MSG_CHOOSE, 1)
                self.assertEqual(self.printer_calls(w), [], label)
                self.assertEqual(w.state('prompt_shown'), 0, label)
                self.assertEqual([e for e in w.events if e[0] == 'print_ex'], [('print_ex', (PARTY, window, MSG_CHOOSE, 1))], label)

    def test_prompt_entry_draws_only_when_eligible(self):
        for language in LANGUAGES:
            w = world(self, language, True, ALL_ON)
            w.open_party()
            for reason in (WRONG_OWNER, BUSY, SPECIAL_ACTIVITY, UNPROVEN_TRAVEL, 99, -1):
                w.events.clear()
                w.blob_call('sgp_box_prompt', PARTY, reason)
                self.assertEqual(self.printer_calls(w), [], reason)
            w.blob_call('sgp_box_prompt', PARTY, ELIGIBLE)
            self.assertEqual(len(self.printer_calls(w)), 1)


if __name__ == '__main__':
    unittest.main()
