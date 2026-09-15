"""Confronto ARM dei getter cache con quelli nativi su tutti i dati mosse ROM.

Richiede SGP_ROM_SQUADRA_DOPO. Intercetta solo il trasporto del singolo membro
NARC; i getter nativi e la divisione PP sono istruzioni ARM/Thumb reali.
"""
import json
import os
from pathlib import Path
import sys
import unittest

import ndspy.narc
import ndspy.rom
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_PROT_ALL, UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                               UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC)

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / 'source'))
from sgp12.rom import Arm9, Rom

ROM = Path(os.environ.get('SGP_ROM_SQUADRA_DOPO', ''))
APP, ARGS, BS, CTX = 0x023C1000, 0x023C2000, 0x023C3000, 0x023C4000
STACK, RETURN = 0x023EF000, 0x023EFF00


@unittest.skipUnless(ROM.is_file(), 'serve SGP_ROM_SQUADRA_DOPO')
class NativeMoveDataTest(unittest.TestCase):
    def test_tutti_i_record_e_pp_equivalenti_ai_getter_arm_originali(self):
        arm = Arm9(ROM)
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.uc.mem_map(0x02000000, 0x00400000, UC_PROT_ALL)
        self.uc.mem_map(0x01FF8000, 0x8000, UC_PROT_ALL)
        self.uc.mem_map(0x027E0000, 0x10000, UC_PROT_ALL)
        for addr, off, size in arm.segmenti:
            self.uc.mem_write(addr, bytes(arm.raw[off:off + size]))
        raw = ROM.read_bytes()
        info, _, overlay = Rom(raw).immagine_overlay(12)
        # Literal effettivo passato da BattleContext_New a LoadMoveTbl.
        off = 0x022486A8 - info['ram']
        cache_offset = int.from_bytes(overlay[off:off + 4], 'little')
        self.assertEqual(cache_offset, 0x3DE)
        nds = ndspy.rom.NintendoDSRom(raw)
        self.members = ndspy.narc.NARC(nds.getFileByName('a/0/1/1')).files
        self.assertTrue(all(len(m) == 16 for m in self.members[:468]))
        self.uc.mem_write(CTX + cache_offset, b''.join(self.members[:468]))
        for addr, value in ((APP, ARGS), (ARGS + 8, BS), (BS + 0x30, CTX)):
            self.uc.mem_write(addr, value.to_bytes(4, 'little'))
        self.uc.mem_write(0x023D8703, b'\x02\x5a')
        self.uc.mem_write(0x023D8716, b'\x01')
        build = REPO / 'source/sgp12/build/squadra_lotta'
        man = json.loads((build / 'manifesto.json').read_text())
        self.uc.mem_write(0x023DBE00, (build / 'blob.bin').read_bytes())
        self.uc.hook_add(UC_HOOK_CODE, self._load_member, begin=0x020733B0, end=0x020733B0)
        for move in range(468):
            for attr in range(1, 5):
                expected = self._call(0x02073315, move, attr)
                actual = self._call(int(man['simboli']['sgp_squadra_attr_cache'], 16), move, attr)
                self.assertEqual(actual, expected, (move, attr))
            for ups in (0, 1, 2, 3, 4, 255):
                expected = self._call(0x0207332D, move, ups)
                actual = self._call(int(man['simboli']['sgp_squadra_pp_cache'], 16), move, ups)
                self.assertEqual(actual, expected, (move, ups))

    def _load_member(self, uc, _address, _size, _user):
        move, dest = uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)
        uc.mem_write(dest, bytes(self.members[move]))
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)

    def _call(self, entry, move, attr):
        for reg, value in ((UC_ARM_REG_R0, move), (UC_ARM_REG_R1, attr),
                           (UC_ARM_REG_R2, APP), (UC_ARM_REG_SP, STACK),
                           (UC_ARM_REG_LR, RETURN | 1)):
            self.uc.reg_write(reg, value)
        self.uc.emu_start(entry, RETURN, count=10000)
        self.assertEqual(self.uc.reg_read(UC_ARM_REG_PC), RETURN)
        self.assertEqual(self.uc.reg_read(UC_ARM_REG_SP), STACK)
        return self.uc.reg_read(UC_ARM_REG_R0)


if __name__ == '__main__':
    unittest.main()
