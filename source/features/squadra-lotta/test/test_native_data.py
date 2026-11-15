"""Actual installed Party code against native ARM getters and physical move data.

SGP_ROM_SQUADRA_DOPO supplies a private post-installation image. No payload is
replaced with a repository blob. Only LoadMoveEntry transport is intercepted;
native getters and division execute. Context/pointer setup is synthetic, so this
is an isolated ABI/equivalence proof, not a game-lifetime observation.
"""
import importlib.util
import os
from pathlib import Path
import sys
import unittest

import ndspy.narc
import ndspy.rom
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_PROT_ALL, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
    UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
    UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
    UC_ARM_REG_CPSR, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC)

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / 'source'))
from sgp12.rom import Arm9, Rom

spec = importlib.util.spec_from_file_location('party_attribution',
    REPO / 'source/features/squadra-lotta/tools/attribuisci.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
ROM = Path(os.environ.get('SGP_ROM_SQUADRA_DOPO', ''))
APP, ARGS, BS, CTX = 0x023C1000, 0x023C2000, 0x023C3000, 0x023C4000
STACK, RETURN = 0x023EF000, 0x023EFF00
SAVED = (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
         UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11)


@unittest.skipUnless(ROM.is_file(), 'serve SGP_ROM_SQUADRA_DOPO')
class NativeMoveDataTest(unittest.TestCase):
    def setUp(self):
        arm = Arm9(ROM)
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.uc.mem_map(0x02000000, 0x00400000, UC_PROT_ALL)
        self.uc.mem_map(0x01FF8000, 0x8000, UC_PROT_ALL)
        self.uc.mem_map(0x027E0000, 0x10000, UC_PROT_ALL)
        for addr, off, size in arm.segmenti:
            self.uc.mem_write(addr, bytes(arm.raw[off:off + size]))
        # Validate all 256 installed bytes BEFORE executing; never write them.
        reader.check_block(bytes(self.uc.mem_read(0x023DBE00, 256)),
                           REPO / 'source/sgp12/build/squadra_lotta')
        raw = ROM.read_bytes()
        container = Rom(raw)
        info, _, overlay = container.immagine_overlay(12)
        off = 0x022486A8 - info['ram']
        cache_offset = int.from_bytes(overlay[off:off + 4], 'little')
        self.assertEqual(cache_offset, 0x3DE)
        info, _, overlay = container.immagine_overlay(8)
        for site, target in reader.CALLS:
            offset = site-info['ram']
            reader.check_call(site, overlay[offset:offset+4], target)
        self.uc.mem_write(info['ram'], bytes(overlay))
        nds = ndspy.rom.NintendoDSRom(raw)
        archive = nds.getFileByName('a/0/1/1')
        self.members = ndspy.narc.NARC(archive).files
        _, table = reader.move_table(archive)
        self.uc.mem_write(CTX + cache_offset, table)
        for addr, value in ((APP, ARGS), (ARGS + 8, BS), (BS + 0x30, CTX)):
            self.uc.mem_write(addr, value.to_bytes(4, 'little'))
        self.uc.mem_write(0x023D8703, b'\x02\x5a')
        self.uc.mem_write(0x023D8716, b'\x01')
        self.symbols = reader.SYMBOLS
        self.loads, self.writes = [], []
        self.uc.hook_add(UC_HOOK_CODE, self._load_member, begin=0x020733B0, end=0x020733B0)
        self.uc.hook_add(UC_HOOK_MEM_WRITE, self._write)

    def test_tutti_i_record_e_pp_equivalenti_ai_getter_arm_originali(self):
        for move in range(468):
            for attr in range(1, 5):
                expected = self._call(0x02073315, move, attr)
                actual = self._call(self.symbols['sgp_squadra_attr_cache'], move, attr)
                self.assertEqual(self.loads, [], ('unexpected transport', move, attr))
                self.assertEqual(actual, expected, (move, attr))
            for ups in (0, 1, 2, 3, 4, 255):
                expected = self._call(0x0207332D, move, ups)
                actual = self._call(self.symbols['sgp_squadra_pp_cache'], move, ups)
                self.assertEqual(self.loads, [], ('unexpected transport', move, ups))
                self.assertEqual(actual, expected, (move, ups))

    def test_cinque_bl_reali_passano_app_dallo_stack_e_preservano_abi(self):
        for (site, _), attr in zip(reader.CALLS, (3, 3, 1, 4, 2)):
            native = 0x0207332D if site == 0x0221D3DE else 0x02073315
            expected = self._call(native, 261, attr)
            actual = self._call(site | 1, 261, attr, stop=site+4)
            self.assertEqual(actual, expected, hex(site))
            self.assertEqual(self.loads, [])

    def test_gate_e_pointer_null_usano_getter_nativo_senza_scritture_persistenti(self):
        for addr, width in ((0x023D8703, 1), (0x023D8704, 1), (0x023D8716, 1),
                            (APP, 4), (ARGS+8, 4), (BS+0x30, 4)):
            original = bytes(self.uc.mem_read(addr, width))
            self.uc.mem_write(addr, bytes(width))
            for kind, native in (('attr', 0x02073315), ('pp', 0x0207332D)):
                expected = self._call(native, 261, 3)
                actual = self._call(self.symbols['sgp_squadra_'+kind+'_hook'], 261, 3)
                self.assertEqual(actual, expected, (hex(addr), kind))
                self.assertEqual([x[0] for x in self.loads], [261])
            self.uc.mem_write(addr, original)
        # Additional valid archive records are outside the admitted cache.
        for move, attr in ((468, 3), (470, 3), (261, 0), (261, 5)):
            expected = self._call(0x02073315, move, attr)
            actual = self._call(self.symbols['sgp_squadra_attr_hook'], move, attr)
            self.assertEqual(actual, expected)
            self.assertEqual([x[0] for x in self.loads], [move])

    def test_controprova_offset_3e0_diverge_dal_getter_nativo(self):
        expected = self._call(0x02073315, 1, 2)
        self.assertEqual(bytes(self.uc.mem_read(0x023DBE78, 4)), bytes.fromhex('de030000'))
        # Deliberate guest mutant on an isolated clone, not a ROM modification.
        self.uc.mem_write(0x023DBE78, bytes.fromhex('e0030000'))
        actual = self._call(self.symbols['sgp_squadra_attr_cache'], 1, 2)
        self.assertNotEqual(actual, expected)

    def _load_member(self, uc, _address, _size, _user):
        move, dest = uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)
        self.loads.append((move, dest))
        self.assertTrue(STACK-256 <= dest and dest+16 <= STACK)
        uc.mem_write(dest, bytes(self.members[move]))
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)

    def _write(self, _uc, _access, address, size, _value, _user):
        self.writes.append((address, size))

    def _call(self, entry, move, attr, stop=RETURN):
        self.loads, self.writes = [], []
        saved = tuple(0xA0000000 + i for i in range(8))
        for reg, value in zip(SAVED, saved):
            self.uc.reg_write(reg, value)
        self.uc.mem_write(STACK, APP.to_bytes(4, 'little'))
        for reg, value in ((UC_ARM_REG_R0, move), (UC_ARM_REG_R1, attr),
                           (UC_ARM_REG_R2, APP), (UC_ARM_REG_R3, 0x33333333),
                           (UC_ARM_REG_SP, STACK), (UC_ARM_REG_LR, RETURN | 1)):
            self.uc.reg_write(reg, value)
        self.uc.emu_start(entry, stop, count=10000)
        self.assertEqual(self.uc.reg_read(UC_ARM_REG_PC), stop)
        self.assertEqual(self.uc.reg_read(UC_ARM_REG_SP), STACK)
        self.assertTrue(self.uc.reg_read(UC_ARM_REG_CPSR) & 0x20)
        if (entry & ~1) in (0x023DBEB4, 0x023DBEBE, *(site for site, _ in reader.CALLS)):
            self.assertEqual(self.uc.reg_read(UC_ARM_REG_R3), 0x33333333)
        self.assertEqual(tuple(self.uc.reg_read(r) for r in SAVED), saved)
        self.assertTrue(all(STACK-256 <= addr and addr+n <= STACK for addr,n in self.writes),
                        self.writes)
        return self.uc.reg_read(UC_ARM_REG_R0)


if __name__ == '__main__':
    unittest.main()
