#!/usr/bin/env python3
"""Contratto ARM Thumb del blob Borsa in battaglia compilato realmente."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_THUMB, UC_PROT_ALL
from unicorn.arm_const import (
    UC_ARM_REG_CPSR, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0,
    UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4,
    UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_SP,
)

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
COMPILER = REPO / "source/features/squadra-lotta/tools/compila.py"

BASE = 0x023DBE00
APP, ARGS, BS, CTX, CACHE = 0x023C1000, 0x023C2000, 0x023C3000, 0x023C4000, 0x023C5000
STACK, RETURN = 0x023EF000, 0x023EFF00
NATIVE, MAXPP = 0x02073314, 0x0207332C
THUMB = 0x20
CALLEE_SAVED = (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7)
SAVED_VALUES = (0xA4A4A4A4, 0xA5A5A5A5, 0xA6A6A6A6, 0xA7A7A7A7)


class BlobArmContract:
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="squadra-lotta-blob-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.build = Path(cls.temp.name)
        subprocess.run([sys.executable, str(COMPILER), "--uscita", str(cls.build)], check=True)
        import json
        compiled_manifest = json.loads((cls.build / "manifesto.json").read_text())
        compiled_blob = (cls.build / "blob.bin").read_bytes()
        shipped = REPO / "source/sgp12/build/squadra_lotta"
        if not (shipped / "blob.bin").is_file():
            raise AssertionError("bundle pubblico squadra_lotta/blob.bin assente")
        shipped_manifest = json.loads((shipped / "manifesto.json").read_text())
        shipped_blob = (shipped / "blob.bin").read_bytes()
        # Apple clang e il clang Linux della CI possono scegliere istruzioni
        # diverse ma equivalenti. Con la stessa toolchain esigiamo identita';
        # in tutti i casi eseguiamo entrambi i blob contro gli stessi contratti.
        if (compiled_manifest['compilatore'] == shipped_manifest['compilatore']
                and compiled_blob != shipped_blob):
            raise AssertionError("il blob spedito non corrisponde alla sorgente compilata")
        cls.manifest = shipped_manifest if cls.USE_SHIPPED else compiled_manifest
        cls.blob = shipped_blob if cls.USE_SHIPPED else compiled_blob
        cls.cache = int(cls.manifest["simboli"]["sgp_squadra_attr_cache"], 16)
        cls.hook = int(cls.manifest["simboli"]["sgp_squadra_attr_hook"], 16)

    def setUp(self):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.uc.mem_map(0x02000000, 0x00400000, UC_PROT_ALL)
        self.uc.mem_write(BASE, self.blob)
        self.uc.mem_write(RETURN, bytes.fromhex("00be"))
        self._p32(APP, ARGS); self._p32(ARGS + 8, BS); self._p32(BS + 0x30, CTX)
        self.uc.mem_write(CTX + 0x3de + 25 * 16, bytes(range(16)))
        self.uc.mem_write(0x023D8703, b"\x02")
        self.uc.mem_write(0x023D8704, b"\x5a")
        self.uc.mem_write(0x023D8716, b"\x01")
        self.calls = []
        self.mapping, self.count = 12, 513
        for target in (NATIVE, MAXPP):
            self.uc.hook_add(UC_HOOK_CODE, self._code, begin=target, end=target)

    def _p32(self, address, value):
        self.uc.mem_write(address, int(value).to_bytes(4, "little"))

    def _code(self, uc, address, _size, _user):
        args = tuple(uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3))
        self.assertTrue(uc.reg_read(UC_ARM_REG_CPSR) & THUMB, (hex(address), hex(uc.reg_read(UC_ARM_REG_CPSR))))
        self.calls.append((address, args))
        value = 0xFA11BAC0
        uc.reg_write(UC_ARM_REG_R0, value)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)

    def _call(self, entry, item=25, attr=13, heap=0x44, app=APP):
        for reg, value in ((UC_ARM_REG_R0, item), (UC_ARM_REG_R1, attr),
                           (UC_ARM_REG_R2, heap), (UC_ARM_REG_R3, 0x33333333),
                           (UC_ARM_REG_R4, app), (UC_ARM_REG_R5, SAVED_VALUES[1]),
                           (UC_ARM_REG_R6, SAVED_VALUES[2]), (UC_ARM_REG_R7, SAVED_VALUES[3]),
                           (UC_ARM_REG_SP, STACK), (UC_ARM_REG_LR, RETURN | 1)):
            self.uc.reg_write(reg, value)
        self._p32(STACK, app)
        self.uc.emu_start(entry, RETURN, count=10000)
        self.assertEqual(self.uc.reg_read(UC_ARM_REG_PC), RETURN)
        self.assertEqual(self.uc.reg_read(UC_ARM_REG_SP), STACK)
        self.assertTrue(self.uc.reg_read(UC_ARM_REG_CPSR) & THUMB)
        self.assertEqual(tuple(self.uc.reg_read(r) for r in CALLEE_SAVED),
                         (app, *SAVED_VALUES[1:]))
        return self.uc.reg_read(UC_ARM_REG_R0)


    def test_attr_cache_and_abi(self):
        for attr in (1, 2, 3, 4):
            with self.subTest(attr=attr):
                self.assertEqual(self._call(self.hook, attr=attr), attr + 1)
                self.assertEqual(self.calls, [])

    def test_pp_formula_and_clamp(self):
        hook = int(self.manifest['simboli']['sgp_squadra_pp_hook'], 16)
        for pp in range(256):
            self.uc.mem_write(CTX + 0x3de + 25 * 16 + 6, bytes([pp]))
            for ups in (0, 1, 2, 3, 4, 255):
                with self.subTest(pp=pp, ups=ups):
                    self.assertEqual(self._call(hook, attr=ups), (pp + pp * min(ups, 3) // 5) & 255)
        self.assertEqual(self.calls, [])

    def test_fallback_options_and_pointer_guards(self):
        for addr, value, width in ((0x023D8703,0,1),(0x023D8704,0,1),(0x023D8716,0,1),
                                   (APP,0,4),(ARGS+8,0,4),(BS+0x30,0,4)):
            with self.subTest(addr=hex(addr)):
                original = bytes(self.uc.mem_read(addr,width))
                self.uc.mem_write(addr,bytes(width))
                for symbol, native in (('sgp_squadra_attr_hook',NATIVE),('sgp_squadra_pp_hook',MAXPP)):
                    self.calls=[]
                    self.assertEqual(self._call(int(self.manifest['simboli'][symbol],16),attr=3),0xFA11BAC0)
                    self.assertEqual(self.calls[0][0],native)
                    self.assertEqual(self.calls[0][1][:2],(25,3))
                self.uc.mem_write(addr,original)

    def test_unexpected_attr_move_and_null_app_use_native(self):
        for move,attr,app in ((25,0,APP),(25,5,APP),(468,3,APP),(65535,3,APP),(25,3,0)):
            self.calls=[]
            self.assertEqual(self._call(self.hook,item=move,attr=attr,app=app),0xFA11BAC0)
            self.assertEqual(self.calls[0][0],NATIVE)
            self.assertEqual(self.calls[0][1][:2],(move,attr))

    def test_last_valid_move_and_loaded_option(self):
        self.uc.mem_write(0x023D8703,b'\x01')
        self.uc.mem_write(CTX+0x3de+467*16+4,b'\x11')
        self.assertEqual(self._call(self.hook,item=467,attr=3),17)
        self.assertEqual(self.calls,[])

class CompiledContract(BlobArmContract, unittest.TestCase):
    USE_SHIPPED = False

class ShippedContract(BlobArmContract, unittest.TestCase):
    USE_SHIPPED = True

if __name__ == '__main__': unittest.main()
