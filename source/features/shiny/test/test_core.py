"""Real host and ARM core contracts; synthetic inputs, no game/save fixtures."""
import ctypes as C
import importlib.util
from pathlib import Path
import random
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from sgp13.shiny_pid import transform_pid

CORE = ROOT / 'features/shiny/core.c'


class Saved(C.Structure):
    _fields_ = [('rng', C.c_uint32), ('target', C.c_uint16),
                ('chain', C.c_uint8), ('mode', C.c_uint8),
                ('initialized', C.c_uint8), ('reserved', C.c_uint8 * 7)]


def state(mode=1, target=25, chain=0, rng=0, initialized=0):
    s = Saved()
    s.mode, s.target, s.chain, s.rng, s.initialized = mode, target, chain, rng, initialized
    return s


class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='sgp-shiny-core-')
        cls.addClassCleanup(cls.temp.cleanup)
        assert CORE.exists(), 'missing native shiny core implementation'
        lib = Path(cls.temp.name) / 'core.dylib'
        subprocess.run(['clang', '-shared', '-fPIC', '-O2', '-std=c99', '-Wall',
                        '-Wextra', '-Werror', str(CORE), '-o', str(lib)], check=True,
                       capture_output=True)
        cls.c = C.CDLL(str(lib))
        p = C.POINTER(Saved)
        for name, args in {
                'valid': [p], 'denominator': [p, C.c_uint32, C.c_uint32],
                'select': [p, C.c_uint32, C.c_uint32],
                'complete': [p, C.c_uint32, C.c_uint32],
                'draw': [p] + [C.c_uint32] * 4 + [C.POINTER(C.c_uint32)] * 2,
                'transform': [C.c_uint32] * 4 + [C.POINTER(C.c_uint32)]}.items():
            getattr(cls.c, 'sgp_shiny_' + name).argtypes = args
        helper = ROOT / 'sgp13/shiny_core.py'
        assert helper.exists(), 'missing bounded Thumb compile helper'
        spec = importlib.util.spec_from_file_location('shiny_core_builder', helper)
        cls.builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.builder)
        cls.blob, cls.symbols = cls.builder.compile_native(cls.temp.name)

    def test_compile_helper_rejects_external_symbols_and_4096_byte_overflow(self):
        original_root = self.builder.ROOT
        with tempfile.TemporaryDirectory(prefix='sgp-shiny-compile-negative-') as tmp:
            root = Path(tmp)
            (root / 'features/shiny').mkdir(parents=True)
            loader = root / 'features/options/tools/carica_text.py'
            loader.parent.mkdir(parents=True)
            loader.write_bytes((ROOT / 'features/options/tools/carica_text.py').read_bytes())
            source = root / 'features/shiny/core.c'
            names = ('valid', 'denominator', 'select', 'complete', 'draw', 'transform')
            try:
                self.builder.ROOT = root
                source.write_text('extern int forbidden(void);\n' + ''.join(
                    'int sgp_shiny_' + name + '(void) { return forbidden(); }\n'
                    for name in names))
                with self.assertRaisesRegex(ValueError, 'esterno'):
                    self.builder.compile_native(root / 'external')
                source.write_text('int sgp_shiny_valid(void) { '
                                  '__asm__ volatile(".rept 2100\\n nop\\n .endr"); return 1; }\n'
                                  + ''.join('int sgp_shiny_' + name + '(void) { return 1; }\n'
                                            for name in names[1:]))
                with self.assertRaisesRegex(ValueError, 'compartment overflow'):
                    self.builder.compile_native(root / 'overflow')
            finally:
                self.builder.ROOT = original_root

    def test_valid_saved_layout_handles_all_targets_and_chain_limits(self):
        self.assertEqual(C.sizeof(Saved), 16)
        for target in range(494):
            for mode in (0, 1):
                for initialized in (0, 1):
                    for chain in (0, 40) if mode and target else (0,):
                        s = state(mode=mode, target=target, chain=chain,
                                  initialized=initialized, rng=0xffffffff if initialized else 0)
                        self.assertEqual(self.c.sgp_shiny_valid(C.byref(s)), 1)

    def test_literal_odds_cover_every_threshold_wrong_species_and_static_base(self):
        for mode, chain, want in ((0, 0, 512), (1, 0, 4096), (1, 9, 4096),
                                  (1, 10, 2048), (1, 19, 2048), (1, 20, 1024),
                                  (1, 39, 1024), (1, 40, 512)):
            s = state(mode=mode, chain=chain)
            self.assertEqual(self.c.sgp_shiny_denominator(C.byref(s), 25, 0), want)
            for species in (1, 24, 26, 493):
                self.assertEqual(self.c.sgp_shiny_denominator(C.byref(s), species, 0),
                                 512 if mode == 0 else 4096)
            self.assertEqual(self.c.sgp_shiny_denominator(C.byref(s), 25, 1),
                             512 if mode == 0 else 4096)
        self.assertEqual(self.c.sgp_shiny_denominator(C.byref(state(target=0)), 25, 0), 4096)

    def test_selection_preserves_rng_and_resets_only_on_actual_change(self):
        s = state(chain=18, rng=0x12345678, initialized=1)
        before = bytes(s)
        self.assertEqual(self.c.sgp_shiny_select(C.byref(s), 1, 25), 0)
        self.assertEqual(bytes(s), before)
        for mode, target in ((1, 493), (0, 493), (0, 0), (1, 0)):
            self.assertEqual(self.c.sgp_shiny_select(C.byref(s), mode, target), 1)
            self.assertEqual((s.mode, s.target, s.chain, s.rng, s.initialized),
                             (mode, target, 0, 0x12345678, 1))

    def test_battle_results_reset_increment_and_saturate(self):
        for result in range(1, 7):
            s = state(chain=39)
            self.assertEqual(self.c.sgp_shiny_complete(C.byref(s), 25, result), 1)
            self.assertEqual(s.chain, 40 if result in (1, 4) else 0)
            self.assertEqual(self.c.sgp_shiny_complete(C.byref(s), 25, result), 0)
        for result in range(1, 7):
            s = state(chain=12)
            self.assertEqual(self.c.sgp_shiny_complete(C.byref(s), 493, result), 1)
            self.assertEqual(s.chain, 0)
            for s in (state(mode=0), state(target=0)):
                self.assertEqual(self.c.sgp_shiny_complete(C.byref(s), 25, result), 0)

    def test_invalid_states_and_arguments_never_mutate_any_output(self):
        bad = [state(target=494), state(chain=41), state(mode=2), state(initialized=2),
               state(rng=1), state(mode=0, chain=1), state(target=0, chain=1)]
        for i in range(7):
            s = state(); s.reserved[i] = 1; bad.append(s)
        for s in bad:
            before = bytes(s)
            self.assertEqual(self.c.sgp_shiny_valid(C.byref(s)), 0)
            self.assertEqual(self.c.sgp_shiny_select(C.byref(s), 1, 25), -1)
            self.assertEqual(self.c.sgp_shiny_complete(C.byref(s), 25, 1), -1)
            self.assertEqual(self.c.sgp_shiny_denominator(C.byref(s), 25, 0), 0)
            shiny, offset = C.c_uint32(77), C.c_uint32(88)
            self.assertEqual(self.c.sgp_shiny_draw(C.byref(s), 1, 2, 25, 0,
                                                 C.byref(shiny), C.byref(offset)), 0)
            self.assertEqual((bytes(s), shiny.value, offset.value), (before, 77, 88))
        for mode, target in ((2, 0), (0, 494), (0xffffffff, 25)):
            s = state(); before = bytes(s)
            self.assertEqual(self.c.sgp_shiny_select(C.byref(s), mode, target), -1)
            self.assertEqual(bytes(s), before)
        for species, base in ((0, 0), (494, 0), (25, 2), (0xffffffff, 1)):
            s = state(); before = bytes(s); shiny, offset = C.c_uint32(77), C.c_uint32(88)
            self.assertEqual(self.c.sgp_shiny_denominator(C.byref(s), species, base), 0)
            self.assertEqual(self.c.sgp_shiny_draw(C.byref(s), 1, 2, species, base,
                                                 C.byref(shiny), C.byref(offset)), 0)
            self.assertEqual((bytes(s), shiny.value, offset.value), (before, 77, 88))
        for species, result in ((0, 1), (494, 1), (25, 0), (25, 7)):
            s = state(chain=20); before = bytes(s)
            self.assertEqual(self.c.sgp_shiny_complete(C.byref(s), species, result), -1)
            self.assertEqual(bytes(s), before)
        for shiny, offset in ((2, 0), (1, 2048), (0xffffffff, 0)):
            out = C.c_uint32(77)
            self.assertEqual(self.c.sgp_shiny_transform(0, 0, shiny, offset, C.byref(out)), 0)
            self.assertEqual(out.value, 77)
        self.assertEqual(self.c.sgp_shiny_valid(None), 0)
        s = state(); before = bytes(s)
        self.assertEqual(self.c.sgp_shiny_draw(C.byref(s), 1, 2, 25, 0, None, None), 0)
        self.assertEqual(bytes(s), before)
        self.assertEqual(self.c.sgp_shiny_transform(0, 0, 1, 0, None), 0)

    def test_saved_prng_resume_uses_explicit_seed_only_once(self):
        # Independently calculated fixed LCG trace, seeded with 12345678/9abcdef0.
        s = state()
        for seed, ot, want_rng, want_shiny, want_offset in (
                (0x12345678, 0x9abcdef0, 0x65a4aac4, 0, 708),
                (0xffffffff, 0, 0xaef9b753, 0, 1875),
                (0, 0, 0x85435496, 0, 1174)):
            shiny, offset = C.c_uint32(), C.c_uint32()
            self.assertEqual(self.c.sgp_shiny_draw(C.byref(s), seed, ot, 25, 0,
                                                 C.byref(shiny), C.byref(offset)), 1)
            self.assertEqual((s.rng, s.initialized, shiny.value, offset.value),
                             (want_rng, 1, want_shiny, want_offset))
            s = Saved.from_buffer_copy(bytes(s))  # raw copied logical state resumes

    def test_all_65536_upper_words_have_exact_literal_lottery_counts(self):
        # Invert the LCG modulo 2^32; no production decision/helper is reused.
        inverse = pow(1664525, -1, 1 << 32)
        for mode, chain, base, species, count in (
                (0, 0, 0, 25, 128), (1, 0, 0, 25, 16),
                (1, 10, 0, 25, 32), (1, 20, 0, 25, 64),
                (1, 40, 0, 25, 128), (1, 40, 1, 25, 16),
                (1, 40, 0, 1, 16)):
            observed = 0
            for word in range(65536):
                output = (word << 16) | (word & 2047)
                prior = ((output - 1013904223) * inverse) & 0xffffffff
                s = state(mode=mode, chain=chain, rng=prior, initialized=1)
                shiny, offset = C.c_uint32(9), C.c_uint32(9)
                self.assertEqual(self.c.sgp_shiny_draw(C.byref(s), 0, 0, species, base,
                                                     C.byref(shiny), C.byref(offset)), 1)
                self.assertEqual((s.rng, offset.value), (output, word & 2047))
                self.assertEqual(shiny.value, int(word < count))
                observed += shiny.value
            self.assertEqual(observed, count)

    def transformed(self, pid, ot, shiny, offset):
        out = C.c_uint32(0xdeadbeef)
        self.assertEqual(self.c.sgp_shiny_transform(pid, ot, shiny, offset, C.byref(out)), 1)
        fold = (ot >> 16) ^ (ot & 65535)
        self.assertEqual(out.value, transform_pid(pid, fold, shiny=bool(shiny), seed=offset))
        self.assertEqual((out.value % 25, out.value & 255), (pid % 25, pid & 255))
        xor = (out.value >> 16) ^ (out.value & 65535) ^ fold
        self.assertTrue(xor < 8 if shiny else xor >= 255)
        return out.value

    def test_modulo_reciprocal_bound_is_exhaustive(self):
        # Byte weights 1,6,11,16 sum to 34: maximum folded sum is 8670.
        for value in range(8671):
            self.assertEqual(value - 25 * ((value * 5243) >> 17), value % 25)

    def test_reduced_gap_proof_exercises_native_transform_for_all_6400_classes(self):
        largest_gap = 0
        self.witnesses = []
        for high in range(256):
            positions = [[] for _ in range(25)]
            for index in range(2048):
                x, low = divmod(index, 8)
                positions[(6*x + 16*(x ^ high) + 11*low) % 25].append(index)
            for nature, hits in enumerate(positions):
                self.assertTrue(hits)
                gap, before, after = max((b-a, a, b) for a, b in
                                        zip(hits, hits[1:] + [hits[0] + 2048]))
                largest_gap = max(largest_gap, gap)
                self.assertLessEqual(gap, 157)
                pid = 256 * (nature * 21 % 25)
                out = self.transformed(pid, high << 8, 1, (before + 1) % 2048)
                self.assertEqual(((out >> 8) & 255)*8 + ((out >> 16) & 7), after % 2048)
        self.assertEqual(largest_gap, 157)

    def test_nonshiny_all_x_ot_boundaries_and_full_width_differential(self):
        for x in range(256):
            for low in (0, 1, 127, 255):
                for fold in (0, 255, 0x1234, 65535):
                    for xor in (0, 7, 8, 254, 255, 256, 65535):
                        pid = ((fold ^ ((x << 8) | low) ^ xor) << 16) | (x << 8) | low
                        self.transformed(pid, fold, 0, 0)
        rng = random.Random(7921)
        for _ in range(2000):
            self.transformed(rng.getrandbits(32), rng.getrandbits(32), rng.randrange(2),
                             rng.randrange(2048))
        self.assertEqual(self.transformed(0, 0x1200, 1, 562), 0x4b065900)
        for pid in (0, 0xffffffff, 0x80000000, 0x12345678):
            for ot in (0, 0xffffffff, 0x12345678):
                for offset in (0, 2047):
                    self.transformed(pid, ot, 1, offset)

    def test_thumb_blob_is_bounded_and_executes_draw_and_worst_pid_search(self):
        from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
        from unicorn import arm_const as R
        self.assertLessEqual(len(self.blob), 4096)
        self.assertGreater(len(self.blob), 0)
        cpu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        cpu.mem_map(0x02000000, 0x400000)
        cpu.mem_write(self.builder.BASE, self.blob)
        data, stack, stop = 0x02280000, 0x023ff000, 0x023ef000
        tally = [0]
        def count(cpu, address, size, user):
            tally[0] += 1
            self.assertTrue(self.builder.BASE <= address < self.builder.BASE + len(self.blob))
        cpu.hook_add(UC_HOOK_CODE, count)
        def call(name, args):
            tally[0] = 0
            for i, value in enumerate(args[:4]): cpu.reg_write(getattr(R, 'UC_ARM_REG_R'+str(i)), value)
            cpu.mem_write(stack, struct.pack('<'+'I'*len(args[4:]), *args[4:]))
            cpu.reg_write(R.UC_ARM_REG_SP, stack); cpu.reg_write(R.UC_ARM_REG_LR, stop | 1)
            for i in range(4, 12):
                cpu.reg_write(getattr(R, 'UC_ARM_REG_R'+str(i)), i * 0x11111111)
            cpu.emu_start(self.symbols['sgp_shiny_'+name], stop, count=20000)
            self.assertEqual(cpu.reg_read(R.UC_ARM_REG_PC), stop)
            self.assertEqual(cpu.reg_read(R.UC_ARM_REG_SP), stack)
            for i in range(4, 12):
                self.assertEqual(cpu.reg_read(getattr(R, 'UC_ARM_REG_R'+str(i))), i * 0x11111111)
            return cpu.reg_read(R.UC_ARM_REG_R0), tally[0]
        worst = 0
        for pid, ot, shiny, offset in ((0, 0x1200, 1, 562), (1, 0, 1, 2047),
                (0xffffffff, 0x12345678, 1, 0), (0, 0, 0, 0), (0xffff0000, 0xffff, 0, 0)):
            cpu.mem_write(data, struct.pack('<I', 77))
            ok, steps = call('transform', [pid, ot, shiny, offset, data])
            self.assertEqual(ok, 1); worst = max(worst, steps)
            self.assertEqual(struct.unpack('<I', cpu.mem_read(data, 4))[0],
                             self.transformed(pid, ot, shiny, offset))
        for mode, chain, species, base in ((0, 0, 25, 0), (1, 0, 25, 0),
                (1, 10, 25, 0), (1, 20, 25, 0), (1, 40, 25, 0), (1, 40, 1, 1)):
            for seed, ot in ((0, 0), (0xffffffff, 0x12345678), (0x12345678, 0x9abcdef0)):
                s = state(mode=mode, chain=chain)
                cpu.mem_write(data, bytes(s)); a, b = C.c_uint32(), C.c_uint32()
                self.assertEqual(self.c.sgp_shiny_draw(C.byref(s), seed, ot, species, base,
                                                     C.byref(a), C.byref(b)), 1)
                ok, steps = call('draw', [data, seed, ot, species, base, data+16, data+20])
                self.assertEqual(ok, 1); worst = max(worst, steps)
                self.assertEqual(bytes(cpu.mem_read(data, 24)), bytes(s)+struct.pack('<II', a.value, b.value))
        # Exercise every reduced class at its largest gap on real Thumb too.
        # A 157-probe loop is the maximum over this exhaustive domain.
        for high in range(256):
            positions = [[] for _ in range(25)]
            for index in range(2048):
                x, low = divmod(index, 8)
                positions[(6*x + 16*(x ^ high) + 11*low) % 25].append(index)
            for nature, hits in enumerate(positions):
                gap, before, after = max((b-a, a, b) for a, b in
                                        zip(hits, hits[1:] + [hits[0] + 2048]))
                pid = 256 * (nature * 21 % 25)
                offset = (before + 1) % 2048
                ok, steps = call('transform', [pid, high << 8, 1, offset, data])
                self.assertEqual(ok, 1)
                self.assertEqual(struct.unpack('<I', cpu.mem_read(data, 4))[0],
                                 transform_pid(pid, high << 8, shiny=True, seed=offset))
                worst = max(worst, steps)
        self.assertLessEqual(worst, 12000)
        print(f'\nshiny core Thumb: {len(self.blob)} bytes; measured max {worst} instructions')


if __name__ == '__main__':
    unittest.main()
