"""Physical R and touch on the ordinary party (state 1) on the real V4 ARM9 (Unicorn).

Native keys are the gSystem words the engine itself reads: raw held/new/repeat,
processed new (after the L=A mapping) and the touch words. The bench fills them for
one frame and calls the installed state-1 wrapper, which sits in front of
PartyMenu_Subtask_MainNormal.
"""
import unittest

import portable_bench as pb
from portable_bench import PARTY, N
from test_runtime import world, Cycle, ALL_ON, PHASE, STATE1_REQUEST_EXIT

LANGUAGES = ('EN', 'IT')
A, B, SELECT, START, RIGHT, LEFT, UP, DOWN, R, L, X, Y = (1 << i for i in range(12))
CHORD = START | SELECT | L | R
HITBOX = ((124, 172), (168, 184))   # [x0, x1) x [y0, y1)


def ready(test, language, activation=ALL_ON):
    w = world(test, language, True, activation)
    cycle = Cycle(w)
    w.set_state('prompt_shown', 1)          # the suffix was drawn by the prompt hook
    return w, cycle


def frame(w, **inputs):
    w.set_inputs(**inputs)
    mark = len(w.events)
    result = w.blob_call('sgp_box_party_main', PARTY)
    return result, w.events[mark:]


class PhysicalR(unittest.TestCase):
    def test_new_R_only_and_native_inputs_win(self):
        for language in LANGUAGES:
            w, cycle = ready(self, language)
            result, _ = frame(w, held=R, new=R)
            self.assertEqual(result, STATE1_REQUEST_EXIT, 'new R opens the box')
            self.assertEqual(w.u8(cycle.args + 0x27), 0)
            self.assertEqual(w.state('phase'), PHASE['EXITING'])
            for name, mask in (('A', A), ('B', B), ('RIGHT', RIGHT), ('LEFT', LEFT), ('UP', UP), ('DOWN', DOWN)):
                with self.subTest(language=language, key=name):
                    w, cycle = ready(self, language)
                    result, events = frame(w, held=R | mask, new=R | mask)
                    self.assertEqual(result, w.main_normal_return, 'native input wins over R')
                    self.assertEqual(w.state('phase'), PHASE['BOUND'])
                    self.assertEqual([e for e in events if e[0] == 'heap_alloc'], [])
            # L=A: the processed word carries A for a new L press; raw R stays visible
            w, cycle = ready(self, language)
            result, _ = frame(w, held=L | R, new=L | R, new_processed=A)
            self.assertEqual(result, w.main_normal_return, 'L=A: the mapped A wins')
            w, cycle = ready(self, language)
            result, _ = frame(w, held=L | R, new=R, new_processed=0)
            self.assertEqual(result, STATE1_REQUEST_EXIT, 'L=A with L already held: a new R still opens the box')

    def test_reset_chords_held_R_and_repeat_are_noop(self):
        for language in LANGUAGES:
            cases = {
                'chord': dict(held=CHORD, new=R),
                'held R, no new press': dict(held=R, new=0),
                'repeat only': dict(held=R, new=0, repeat=R),
                'other shoulder only': dict(held=L, new=L, new_processed=0),
                'START': dict(held=START, new=START),
                'no input': dict(),
            }
            for name, inputs in cases.items():
                with self.subTest(language=language, case=name):
                    w, cycle = ready(self, language)
                    result, events = frame(w, **inputs)
                    self.assertEqual(result, w.main_normal_return)
                    self.assertEqual(w.state('phase'), PHASE['BOUND'])
                    self.assertEqual(w.u8(cycle.args + 0x27), 0)
                    self.assertEqual([e for e in events if e[0] in ('heap_alloc', 'play_se')], [])

    def test_input_requires_activation_prompt_and_idle_animation(self):
        for language in LANGUAGES:
            w, cycle = ready(self, language, dict(bridge=1, input=0, prompt=1))
            self.assertEqual(frame(w, held=R, new=R)[0], w.main_normal_return, 'input word off')
            w, cycle = ready(self, language, dict(bridge=0, input=1, prompt=1))
            self.assertEqual(frame(w, held=R, new=R)[0], w.main_normal_return, 'bridge word off')
            w, cycle = ready(self, language)
            w.set_state('prompt_shown', 0)
            self.assertEqual(frame(w, held=R, new=R)[0], w.main_normal_return, 'no suffix on screen, no action')
            w, cycle = ready(self, language)
            w.w32(PARTY + 0xC9C, 1)                         # context button animation running
            self.assertEqual(frame(w, held=R, new=R)[0], w.main_normal_return)
            self.assertEqual(w.state('phase'), PHASE['BOUND'])
            w.w32(PARTY + 0xC9C, 0)
            self.assertEqual(frame(w, held=R, new=R)[0], STATE1_REQUEST_EXIT, 'resumes once idle')


class Touch(unittest.TestCase):
    def test_touch_edges_and_R_touch_coalesce(self):
        (x0, x1), (y0, y1) = HITBOX
        inside = [(x0, y0), (x1 - 1, y1 - 1), (x0, y1 - 1), (x1 - 1, y0), (148, 176)]
        outside = [(x0 - 1, y0), (x1, y0), (x0, y0 - 1), (x0, y1), (x1, y1), (0, 0), (200, 176), (230, 170), (60, 100)]
        for language in LANGUAGES:
            for point in inside:
                with self.subTest(language=language, inside=point):
                    w, cycle = ready(self, language)
                    self.assertEqual(frame(w, touch=point)[0], STATE1_REQUEST_EXIT)
            for point in outside:
                with self.subTest(language=language, outside=point):
                    w, cycle = ready(self, language)
                    result, events = frame(w, touch=point)
                    self.assertEqual(result, w.main_normal_return, 'native touch handling owns it')
                    self.assertEqual(w.state('phase'), PHASE['BOUND'])
                    self.assertEqual([e for e in events if e[0] == 'heap_alloc'], [])
            # R and a box touch in the same frame: one request, one exit
            w, cycle = ready(self, language)
            result, _ = frame(w, held=R, new=R, touch=(148, 176))
            self.assertEqual(result, STATE1_REQUEST_EXIT)
            self.assertEqual((w.state('requested'), w.state('phase')), (1, PHASE['EXITING']))
            self.assertEqual(w.state('request_generation'), w.state('generation'))
            # a second state-1 call in the same session cannot raise another request
            result, events = frame(w, held=R, new=R, touch=(148, 176))
            self.assertEqual(result, w.main_normal_return)
            self.assertEqual([e for e in events if e[0] == 'play_se'], [])
            # touch held from before (no new touch) and R new: the touch owns the frame
            w, cycle = ready(self, language)
            self.assertEqual(frame(w, held=R, new=R, touch_held=True)[0], w.main_normal_return)
            # touch elsewhere and R in the same frame: native touch wins
            w, cycle = ready(self, language)
            self.assertEqual(frame(w, held=R, new=R, touch=(60, 100))[0], w.main_normal_return)
            # A + touch inside the box: native A wins
            w, cycle = ready(self, language)
            self.assertEqual(frame(w, held=A, new=A, touch=(148, 176))[0], w.main_normal_return)

    def test_hitbox_does_not_intersect_native_party_touch_rectangles(self):
        """Rectangles read from the REAL V4 tables (_02110104 and _02110128, {top,bottom,left,right})."""
        for language in LANGUAGES:
            data, segments, mapped = pb.rom(self, language)
            from sgp131 import portable
            (x0, x1), (y0, y1) = HITBOX
            for table, count in ((0x02110104, 9), (0x02110128, 8), (0x02110148, 8)):
                raw = portable.read_ram(data, segments, table, 4 * count)
                for i in range(count):
                    top, bottom, left, right = raw[4 * i:4 * i + 4]
                    if top == 0xFF:
                        break
                    right = right or 256
                    overlap = left < x1 and x0 < right and top < y1 and y0 < bottom
                    self.assertFalse(overlap, (language, hex(table), i, (top, bottom, left, right)))


if __name__ == '__main__':
    unittest.main()
