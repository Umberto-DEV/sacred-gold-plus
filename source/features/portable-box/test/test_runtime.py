"""Bridge lifecycle on the real V4 ARM9 bytes (Unicorn): inert delegation, request
validation, PC launch/return, party recreation, failure paths. See portable_bench.

Inputs: private V4 ROMs (skip with a reason; SGP_PORTABLE_REQUIRE_INPUTS=1 fails).
"""
import unittest

import portable_bench as pb
from portable_bench import (World, N, TASK, FIELD, OWNER, PARTY, PARTY_CONT, PARTY_TEMPLATE,
                            PC_TEMPLATE, NATIVE_CB, CB_LO)

LANGUAGES = ('EN', 'IT')
ALL_ON = dict(bridge=1, input=1, prompt=1, context_proof=1)
STATE1_REQUEST_EXIT = 0x20
PHASE = dict(IDLE=0, BOUND=1, EXITING=2, PC_RUNNING=3)
_CACHE = {}


def world(test, language, hooked=True, activation=None):
    key = (language, hooked, tuple(sorted((activation or {}).items())))
    if key not in _CACHE:
        _CACHE[key] = World(test, language, hooked, activation)
    w = _CACHE[key]
    w.reset()
    return w


def masked_events(native, hooked, scratch):
    """Event lists with every register that only holds trampoline scratch masked in both runs.

    The trampoline loads r3 (gate / resume literal) and may leave r1-r3 different from the
    native leftovers; AAPCS makes them caller-saved, so only values equal to those
    literals are masked, every other argument is compared exactly.
    """
    assert len(native) == len(hooked), (len(native), len(hooked))
    out = ([], [])
    for a, b in zip(native, hooked):
        if a[0] == 'ext':
            regs_a, regs_b = list(a[2]), list(b[2])
            for k in range(4):
                if regs_b[k] in scratch or (k < 3 and a[1] in (N['get_field'], N['get_env']) and k > 0):
                    regs_a[k] = regs_b[k] = None
            a, b = (a[0], a[1], tuple(regs_a)), (b[0], b[1], tuple(regs_b))
        out[0].append(a)
        out[1].append(b)
    return out


class Cycle:
    """Drive one party -> PC -> party visit the way the start-menu task would."""

    def __init__(self, w, slot=2, count=5, args=None):
        self.w, self.slot, self.count = w, slot, count
        self.args = w.open_party(slot=slot, count=count) if args is None else args

    def rebuilt(self):
        """The party the bridge opened after the PC: same owner, new args (PartyMenu re-created)."""
        w = self.w
        args = w.u32(OWNER + 0x380)
        w.uc.mem_write(PARTY, bytes(0xCB0))
        w.w32(PARTY + 0x654, args)
        w.w8(PARTY + 0xC65, w.u8(args + 0x26))
        w.child_exit()
        return Cycle(w, self.slot, self.count, args)

    def accept_request(self):
        w = self.w
        w.set_state('requested', 1)                       # what the bench probe does
        return w.blob_call('sgp_box_party_main', PARTY)

    def party_exits(self):
        w = self.w
        w.child_exit()
        w.w8(self.args + 0x26, w.u8(PARTY + 0xC65))        # PartyMenuApp_Main exit path

    def callback(self):
        return self.w.callback()

    def pc_exits(self):
        self.w.child_exit()
        return self.w.blob_call('sgp_box_pc_return', TASK)


class InertDelegation(unittest.TestCase):
    def test_inert_delegation_matches_native_registers_stack_and_state(self):
        """With requested=0 every hook is observably the native code, for every callback path."""
        for language in LANGUAGES:
            native = world(self, language, hooked=False)
            for activation in (None, ALL_ON):
                hooked = world(self, language, True, activation)
                self.assertEqual(bytes(hooked.uc.mem_read(CB_LO, 4)).hex(), '004b1847', 'callback hook installed')
                for action in range(0x20):
                    for context in range(0x19):
                        outcome = []
                        for w in (native, hooked):
                            w.reset()
                            args = w.open_party(slot=2)
                            w.w8(args + 0x27, action)
                            w.w8(args + 0x24, context)
                            mark, wmark = len(w.events), len(w.writes)
                            w.isolated = True
                            result = w.callback()
                            w.isolated = False
                            outcome.append((result, w.last_regs, w.last_sp, w.last_preserved,
                                            w.events[mark:], w.writes[wmark:]))
                        scratch = {hooked.symbols['sgp_box_party_return'], pb.CB_LO + 13}
                        masked = masked_events(outcome[0][4], outcome[1][4], scratch)
                        self.assertEqual(outcome[0][:4] + (masked[0], outcome[0][5]),
                                         outcome[1][:4] + (masked[1], outcome[1][5]),
                                         (language, activation, action, context))
                        self.assertTrue(outcome[1][3], 'AAPCS: SP and r4-r11 preserved')
                        self.assertGreaterEqual(hooked.hits.get('sgp_box_party_return', 0), 1, 'gate executed')

    def test_state1_wrapper_returns_the_native_state_unchanged(self):
        for language in LANGUAGES:
            native = world(self, language, hooked=False)
            for activation in (None, ALL_ON):
                hooked = world(self, language, True, activation)
                for value in (0, 1, 5, 32, 33):
                    outcomes = []
                    for w in (native, hooked):
                        w.reset()
                        w.open_party()
                        w.main_normal_return = value
                        mark = len(w.events)
                        entry = N['main_normal'] if w is native else w.entry('sgp_box_party_main')
                        result = w.call(entry, PARTY)
                        outcomes.append((result, w.last_regs, w.last_sp, w.events[mark:]))
                    self.assertEqual(outcomes[0], outcomes[1], (language, activation, value))
                self.assertEqual(hooked.u8(hooked.u32(PARTY + 0x654) + 0x27), 0, 'selectedAction untouched')

    def test_launch_hook_binds_without_changing_the_native_launch(self):
        for language in LANGUAGES:
            native = world(self, language, hooked=False)
            hooked = world(self, language, True, ALL_ON)
            traces = []
            for w in (native, hooked):
                w.reset()
                args = w.open_party(slot=3)
                traces.append((w.args_bytes(args), [e for e in w.events if e[0] != 'ext'], w.launches))
            self.assertEqual(traces[0], traces[1])
            self.assertEqual(hooked.state('generation'), 1, 'bind ran')
            self.assertEqual(hooked.state('phase'), PHASE['BOUND'])
            self.assertEqual((hooked.state('field'), hooked.state('owner')), (FIELD, OWNER))
            self.assertEqual(hooked.state('args'), hooked.args)
            hooked.reset()
            hooked.open_party()
            hooked.child_exit()
            hooked.open_party()
            self.assertEqual(hooked.state('generation'), 2, 'every launch rebinds')

    def test_prompt_wrapper_calls_the_native_print_only_when_inactive(self):
        for language in LANGUAGES:
            for activation in (None, dict(prompt=1)):
                w = world(self, language, True, activation)
                w.open_party()
                w.blob_call('sgp_box_prompt_print', PARTY, PARTY + 0x204, 29, 1)
                prints = [e for e in w.events if e[0] == 'print_ex']
                self.assertEqual(prints, [('print_ex', (PARTY, PARTY + 0x204, 29, 1))])
                if not activation:
                    self.assertEqual([e for e in w.events if e[0] == 'add_printer'], [])


class RequestValidation(unittest.TestCase):
    def test_stale_generation_and_foreign_owner_cancel_request(self):
        for language in LANGUAGES:
            # stale generation: the party was relaunched between accept and callback
            w = world(self, language, True, ALL_ON)
            cycle = Cycle(w)
            self.assertEqual(cycle.accept_request(), STATE1_REQUEST_EXIT)
            self.assertEqual(w.state('phase'), PHASE['EXITING'])
            cycle.party_exits()
            w.open_party(slot=1)                            # new bind, new generation
            w.isolated = True
            w.callback()
            w.isolated = False
            self.assertEqual(w.launches[-1][0], PARTY_TEMPLATE, 'no PC launch for a stale request')
            self.assertEqual(w.state('requested'), 0)
            self.assertEqual(w.state('failures'), 1)
            self.assertEqual(w.u16(OWNER + 0x26), 0x0F, 'native Cancel reached START_MENU_STATE_RETURN')
            # stale generation with the request still raised (e.g. a probe write after a rebind)
            w = world(self, language, True, ALL_ON)
            cycle = Cycle(w)
            cycle.accept_request()
            cycle.party_exits()
            w.set_state('generation', w.state('generation') + 1)
            w.isolated = True
            w.callback()
            w.isolated = False
            self.assertEqual([t for t, _ in w.launches], [PARTY_TEMPLATE], 'generation mismatch: no PC')
            self.assertEqual((w.state('requested'), w.state('failures')), (0, 1))
            self.assertEqual(w.u16(OWNER + 0x26), 0x0F)
            # foreign owner: the callback runs for another start-menu task
            w = world(self, language, True, ALL_ON)
            cycle = Cycle(w)
            cycle.accept_request()
            cycle.party_exits()
            other_task, other_owner = TASK + 0x100, OWNER + 0x800
            w.w32(other_task + 0x18, FIELD)
            w.w32(other_task + 0xC, other_owner)
            w.w32(other_owner + 0x380, cycle.args)
            w.isolated = True
            w.call(CB_LO, other_task)
            w.isolated = False
            self.assertEqual([t for t, _ in w.launches], [PARTY_TEMPLATE])
            self.assertEqual(w.state('requested'), 0)
            self.assertEqual(w.state('failures'), 1)

    def test_foreign_party_never_accepts_a_pending_request(self):
        for language in LANGUAGES:
            w = world(self, language, True, ALL_ON)
            args = w.open_party()
            w.w8(args + 0x24, 3)                           # battle / trade style context
            w.set_state('requested', 1)
            self.assertEqual(w.blob_call('sgp_box_party_main', PARTY), w.main_normal_return)
            self.assertEqual(w.u8(args + 0x27), 0)
            self.assertEqual(w.state('requested'), 0)
            self.assertEqual(w.state('phase'), PHASE['BOUND'])
            self.assertEqual([e for e in w.events if e[0] == 'heap_alloc' and e[1][1] == 12], [])

    def test_request_without_bridge_activation_is_dropped_not_obeyed(self):
        for language in LANGUAGES:
            w = world(self, language, True, None)
            w.open_party()
            w.set_state('requested', 1)
            self.assertEqual(w.blob_call('sgp_box_party_main', PARTY), w.main_normal_return)
            self.assertEqual(w.state('phase'), PHASE['BOUND'])
            self.assertEqual(w.u8(w.args + 0x27), 0)


class IdentityChecks(unittest.TestCase):
    """Recycled addresses and altered fields: the record never trusts a pointer alone."""

    def test_gate_revalidates_every_identity_field(self):
        for language in LANGUAGES:
            edits = {
                'context': lambda w, c: w.w8(c.args + 0x24, 3),
                'selected action': lambda w, c: w.w8(c.args + 0x27, 5),
                'field system': lambda w, c: w.w32(c.args + 0x1C, FIELD + 0x40),
                'owner exit environment': lambda w, c: w.w32(OWNER + 0x380, w.call(N['heap_alloc'], 0x0B, 0x44)),
            }
            for name, edit in edits.items():
                with self.subTest(language=language, edit=name):
                    w = world(self, language, True, ALL_ON)
                    cycle = Cycle(w)
                    cycle.accept_request()
                    cycle.party_exits()
                    edit(w, cycle)
                    w.isolated = True
                    w.callback()
                    w.isolated = False
                    self.assertEqual([t for t, _ in w.launches], [PARTY_TEMPLATE], 'no PC for an altered ' + name)
                    self.assertEqual((w.state('requested'), w.state('failures')), (0, 1))
                    self.assertEqual([e for e in w.events if e[0] == 'heap_alloc' and e[1][1] == 12], [])

    def test_recycled_party_identity_is_not_trusted(self):
        for language in LANGUAGES:
            edits = {
                'check data of another owner': lambda w, a: w.w32(a + 0x18, OWNER + 0x800 + 0x370),
                'field system of another field': lambda w, a: w.w32(a + 0x1C, FIELD + 0x40),
                'environment parked in the owner': lambda w, a: w.w32(OWNER + 0x380, 0x02399990),
                'non-zero context': lambda w, a: w.w8(a + 0x24, 10),
            }
            for name, edit in edits.items():
                with self.subTest(language=language, edit=name):
                    w = world(self, language, True, ALL_ON)
                    cycle = Cycle(w)
                    w.set_state('prompt_shown', 1)
                    edit(w, cycle.args)           # same S->args value, different party underneath
                    w.set_state('requested', 1)
                    w.w8(cycle.args + 0x27, 7)
                    mark = len(w.events)
                    self.assertEqual(w.blob_call('sgp_box_party_main', PARTY), w.main_normal_return)
                    self.assertEqual(w.u8(cycle.args + 0x27), 7, 'selectedAction untouched')
                    self.assertEqual([e for e in w.events[mark:] if e[0] in ('heap_alloc', 'play_se')], [])
            # same address, a newer generation: the old request cannot be satisfied by the new party
            w = world(self, language, True, ALL_ON)
            cycle = Cycle(w)
            cycle.accept_request()
            cycle.party_exits()
            w.child_exit()
            w.open_party(slot=1)                  # the allocator may hand out any address; identity says new generation
            w.w32(OWNER + 0x380, w.args)
            self.assertEqual(w.state('generation'), 2)
            self.assertEqual(w.state('requested'), 0)

    def test_accept_clears_a_stale_selected_action_and_plays_the_sound(self):
        for language in LANGUAGES:
            w = world(self, language, True, ALL_ON)
            cycle = Cycle(w)
            w.w8(cycle.args + 0x27, 5)
            mark = len(w.events)
            self.assertEqual(cycle.accept_request(), STATE1_REQUEST_EXIT)
            self.assertEqual(w.u8(cycle.args + 0x27), 0, 'RETURN_0 written by the accept')
            self.assertEqual([e for e in w.events[mark:] if e[0] == 'play_se'], [('play_se', (1500,))])

    def test_callback_and_pc_return_write_the_start_menu_state(self):
        for language in LANGUAGES:
            w = world(self, language, True, ALL_ON)
            cycle = Cycle(w)
            cycle.accept_request()
            cycle.party_exits()
            w.w16(OWNER + 0x26, 9)
            w.w32(OWNER + 0x354, 0)
            cycle.callback()
            self.assertEqual(w.u16(OWNER + 0x26), 5, 'WAIT_APP set by the gate')
            self.assertEqual(w.u32(OWNER + 0x354), w.symbols['sgp_box_pc_return'])
            w.child_exit()
            w.w16(OWNER + 0x26, 9)
            w.w32(OWNER + 0x354, 0)
            w.blob_call('sgp_box_pc_return', TASK)
            self.assertEqual(w.u16(OWNER + 0x26), 5)
            self.assertEqual(w.u32(OWNER + 0x354), NATIVE_CB)

    def test_unaccepted_request_never_reaches_the_gate(self):
        for language in LANGUAGES:
            w = world(self, language, True, ALL_ON)
            cycle = Cycle(w)
            cycle.party_exits()
            w.set_state('requested', 1)           # a probe write that no state-1 frame ever accepted
            w.set_state('request_generation', w.state('generation'))
            w.isolated = True
            w.callback()
            w.isolated = False
            self.assertEqual([t for t, _ in w.launches], [PARTY_TEMPLATE])
            self.assertEqual((w.state('requested'), w.state('failures')), (0, 1))

    def test_pc_return_with_the_pc_open_but_an_altered_identity_frees_nothing(self):
        for language in LANGUAGES:
            for name in ('environment replaced', 'callback of another owner'):
                with self.subTest(language=language, case=name):
                    w = world(self, language, True, ALL_ON)
                    cycle = Cycle(w)
                    cycle.accept_request()
                    cycle.party_exits()
                    cycle.callback()
                    self.assertEqual(w.state('phase'), PHASE['PC_RUNNING'])
                    w.child_exit()
                    task, owner = TASK, OWNER
                    if name == 'environment replaced':
                        w.w32(OWNER + 0x380, 0x02399990)
                    else:
                        task, owner = TASK + 0x100, OWNER + 0x800
                        w.w32(task + 0x18, FIELD)
                        w.w32(task + 0xC, owner)
                        w.w32(owner + 0x380, w.state('pc_args'))
                    pc_args = w.state('pc_args')
                    mark = len(w.events)
                    w.blob_call('sgp_box_pc_return', task)
                    self.assertEqual([e for e in w.events[mark:] if e[0] == 'heap_free'], [], 'nothing freed on a broken identity')
                    self.assertEqual(sum(1 for e in w.events[mark:] if e[0] == 'load_field'), 1)
                    self.assertEqual(w.u16(owner + 0x26), 0x0F)
                    self.assertEqual((w.state('phase'), w.state('failures')), (PHASE['IDLE'], 1))
                    self.assertEqual([t for t, _ in w.launches], [PARTY_TEMPLATE, PC_TEMPLATE], 'no party relaunch')
                    self.assertIn(pc_args, w.live, 'the PC args stay allocated: this record cannot prove they are its own')

    def test_a_live_party_is_never_bound_while_the_pc_is_open(self):
        for language in LANGUAGES:
            w = world(self, language, True, ALL_ON)
            w.open_party()
            w.set_state('phase', PHASE['PC_RUNNING'])
            generation = w.state('generation')
            w.blob_call('sgp_box_prompt_print', PARTY, PARTY + 0x204, 29, 1)
            self.assertEqual([e for e in w.events if e[0] == 'add_printer'], [])
            self.assertEqual((w.state('phase'), w.state('generation')), (PHASE['PC_RUNNING'], generation))
            w.set_inputs(held=1 << 8, new=1 << 8)
            self.assertEqual(w.blob_call('sgp_box_party_main', PARTY), w.main_normal_return)
            self.assertEqual((w.state('phase'), w.state('generation')), (PHASE['PC_RUNNING'], generation))

    def test_pc_return_for_a_foreign_owner_leaves_foreign_memory_alone(self):
        for language in LANGUAGES:
            w = world(self, language, True, ALL_ON)
            w.open_party()
            w.w32(OWNER + 0x380, 0x02399990)
            before = len(w.events)
            w.blob_call('sgp_box_pc_return', TASK)          # phase is BOUND, not PC_RUNNING
            self.assertEqual([e for e in w.events[before:] if e[0] == 'heap_free'], [], 'never free what is not ours')
            self.assertEqual(sum(1 for e in w.events[before:] if e[0] == 'load_field'), 1)
            self.assertEqual(w.u16(OWNER + 0x26), 0x0F)
            self.assertEqual(w.u32(OWNER + 0x380), 0x02399990, 'foreign environment untouched')


class PcLifecycle(unittest.TestCase):
    def test_one_child_and_single_free(self):
        for language in LANGUAGES:
            w = world(self, language, True, ALL_ON)
            cycle = Cycle(w)
            old_args = cycle.args
            self.assertEqual(cycle.accept_request(), STATE1_REQUEST_EXIT)
            self.assertEqual(w.u8(old_args + 0x27), 0, 'native RETURN_0 / Cancel action')
            cycle.party_exits()
            self.assertEqual(cycle.callback(), 0, 'callback result FALSE')
            self.assertEqual(w.launches[-1][0], PC_TEMPLATE)
            pc_args = w.state('pc_args')
            self.assertEqual((w.u32(pc_args), w.u32(pc_args + 4), w.u32(pc_args + 8)),
                             (pb.SAVEDATA, FIELD + 0x10C, 2), 'SaveData, menu input state, mode 2')
            self.assertEqual(w.u32(OWNER + 0x380), pc_args)
            self.assertEqual(w.u32(OWNER + 0x354), w.symbols['sgp_box_pc_return'] & 0xFFFFFFFF)
            self.assertEqual(w.u16(OWNER + 0x26), 5, 'WAIT_APP')
            self.assertEqual(w.state('phase'), PHASE['PC_RUNNING'])
            native_heap = [e[1][0] for e in w.events if e[0] == 'create_args'][0]
            self.assertEqual(native_heap, 11, 'the native constructor allocates the party args in heap 11')
            module_allocs = [e[1] for e in w.events if e[0] == 'heap_alloc' and e[1][1] == 12]
            self.assertTrue(module_allocs and all(heap == native_heap for heap, _ in module_allocs),
                            'PCBoxArgs use the heap the native code frees them from: %r' % module_allocs)
            order = [e[0] + ':' + str(e[1][-1] if e[0] == 'heap_free' else e[1][1]) for e in w.events
                     if e[0] in ('heap_alloc', 'heap_free')]
            self.assertLess(order.index('heap_alloc:12'), order.index('heap_free:%d' % old_args),
                            'PCBoxArgs allocated before the party args are freed')
            cycle.pc_exits()
            self.assertEqual([t for t, _ in w.launches], [PARTY_TEMPLATE, PC_TEMPLATE, PARTY_TEMPLATE])
            frees = [e[1][0] for e in w.events if e[0] == 'heap_free']
            self.assertEqual(sorted(frees), sorted(set(frees)), 'no block freed twice')
            self.assertIn(old_args, frees)
            self.assertIn(pc_args, frees)
            new_args = w.launches[-1][1]
            self.assertEqual(w.u32(OWNER + 0x380), new_args)
            self.assertEqual(set(w.live), {new_args}, 'only the new party args remain allocated')
            self.assertEqual(w.u32(OWNER + 0x354), NATIVE_CB)
            self.assertEqual(w.u16(OWNER + 0x26), 5)
            self.assertEqual(w.state('phase'), PHASE['BOUND'])
            self.assertEqual(w.state('generation'), 2)
            self.assertEqual(w.state('pc_args'), 0)
            self.assertEqual(w.state('opens'), 1)
            self.assertEqual([e[1][0] for e in w.events if e[0] == 'sub_93070'], [FIELD], 'Bill notification once')

    def test_count_shrink_clamps_selection(self):
        cases = ((5, 3, 2), (4, 6, 4), (1, 3, 1), (7, 4, 0), (6, 4, 0), (0, 1, 0))
        for language in LANGUAGES:
            for slot, new_count, expected in cases:
                with self.subTest(language=language, slot=slot, count=new_count):
                    w = world(self, language, True, ALL_ON)
                    cycle = Cycle(w, slot=min(slot, 5), count=6)
                    w.w8(PARTY + 0xC65, slot)
                    cycle.accept_request()
                    cycle.party_exits()
                    cycle.callback()
                    w.w32(PARTY_CONT + 4, new_count)
                    cycle.pc_exits()
                    self.assertEqual(w.u8(w.launches[-1][1] + 0x26), expected)
                    self.assertEqual(w.state('selection'), expected)

    def test_PC_args_allocation_failure_preserves_native_cancel(self):
        for language in LANGUAGES:
            w = world(self, language, True, ALL_ON)
            cycle = Cycle(w)
            cycle.accept_request()
            cycle.party_exits()
            w.fail_alloc.append(lambda size, heap: size == 12)
            w.isolated = True
            self.assertEqual(cycle.callback(), 0)
            w.isolated = False
            self.assertEqual([t for t, _ in w.launches], [PARTY_TEMPLATE], 'PC never launched')
            self.assertEqual(w.state('requested'), 0)
            self.assertEqual(w.state('phase'), PHASE['IDLE'])
            self.assertEqual(w.state('failures'), 1)
            frees = [e[1][0] for e in w.events if e[0] == 'heap_free']
            self.assertEqual(frees.count(cycle.args), 1, 'party args freed once, by the native callback')
            self.assertEqual(sum(1 for e in w.events if e[0] == 'load_field'), 1)
            self.assertEqual(w.u16(OWNER + 0x26), 0x0F)
            self.assertEqual(w.live, {})

    def test_party_recreation_constructor_null_returns_field_safely(self):
        """SG-BOX-NULL: the real PartyArgs constructor can return NULL.

        The historical preventive probe could succeed and the immediately
        following native CreateArgs allocation could still fail.  The wrapper must not read
        ``args + ARGS_PARTY`` with args == 0; it returns to the field cleanly.
        """
        for language in LANGUAGES:
            with self.subTest(language=language):
                # Use an isolated world because this test replaces the native
                # constructor entry with the exact Thumb ABI `return NULL`
                # stub.  Unicorn does not reliably redirect PC from a code
                # hook once the native basic block has been translated.
                w = World(self, language, True, ALL_ON)
                cycle = Cycle(w)
                cycle.accept_request()
                cycle.party_exits()
                cycle.callback()
                w.uc.hook_del(w.stub_hooks['create_args'])
                w.uc.mem_write(N['create_args'], bytes.fromhex('00207047'))  # movs r0,#0; bx lr
                w.uc.ctl_remove_cache(N['create_args'], N['create_args'] + 4)
                self.assertEqual(cycle.pc_exits(), 0)
                self.assertEqual(w.errors, [])
                self.assertEqual(w.u32(OWNER + 0x380), 0, 'PC args were released before the failed reconstruction')
                self.assertEqual(w.state('phase'), PHASE['IDLE'])
                self.assertEqual(w.state('failures'), 1)
                self.assertIsNone(w.child)

    def test_fifty_cycles_leave_no_residue(self):
        for language in LANGUAGES:
            w = world(self, language, True, ALL_ON)
            cycle = Cycle(w, slot=0, count=5)
            for index in range(50):
                cycle.accept_request()
                cycle.party_exits()
                cycle.callback()
                cycle.pc_exits()
                cycle = cycle.rebuilt()
                self.assertEqual(len(w.live), 1, 'cycle %d: only the live party args remain' % index)
                self.assertEqual(w.state('allocs'), w.state('frees'), 'cycle %d: alloc/free balance' % index)
                self.assertEqual(w.state('opens'), index + 1)
                self.assertEqual(w.state('generation'), index + 2)
                self.assertEqual(w.state('phase'), PHASE['BOUND'])
                self.assertEqual((w.state('requested'), w.state('pc_args'), w.state('failures')), (0, 0, 0))
            self.assertEqual(w.state('allocs'), 50)
            self.assertEqual(w.errors, [])


if __name__ == '__main__':
    unittest.main()
