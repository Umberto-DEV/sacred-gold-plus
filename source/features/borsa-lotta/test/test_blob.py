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
COMPILER = REPO / "source/features/borsa-lotta/tools/compila.py"

BASE = 0x023DBD00
APP, ARGS, BS, CTX, CACHE = 0x023C1000, 0x023C2000, 0x023C3000, 0x023C4000, 0x023C5000
STACK, RETURN = 0x023EF000, 0x023EFF00
MAP, GETVAR, NATIVE = 0x02077C18, 0x02257E74, 0x02077D88
THUMB = 0x20
CALLEE_SAVED = (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7)
SAVED_VALUES = (0xA4A4A4A4, 0xA5A5A5A5, 0xA6A6A6A6, 0xA7A7A7A7)


class BlobArmContract:
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="borsa-lotta-blob-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.build = Path(cls.temp.name)
        subprocess.run([sys.executable, str(COMPILER), "--uscita", str(cls.build)], check=True)
        import json
        compiled_manifest = json.loads((cls.build / "manifesto.json").read_text())
        compiled_blob = (cls.build / "blob.bin").read_bytes()
        shipped = REPO / "source/sgp12/build/borsa_lotta"
        if not (shipped / "blob.bin").is_file():
            raise AssertionError("bundle pubblico borsa_lotta/blob.bin assente")
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
        cls.cache = int(cls.manifest["simboli"]["sgp_borsa_attr_cache"], 16)
        cls.hook = int(cls.manifest["simboli"]["sgp_borsa_attr_hook"], 16)

    def setUp(self):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.uc.mem_map(0x02000000, 0x00400000, UC_PROT_ALL)
        self.uc.mem_write(BASE, self.blob)
        self.uc.mem_write(RETURN, bytes.fromhex("00be"))
        self._p32(APP, ARGS); self._p32(ARGS, BS); self._p32(BS + 0x30, CTX)
        self._p32(CTX + 0x2120, CACHE)
        self.uc.mem_write(0x023D8703, b"\x02")
        self.uc.mem_write(0x023D8704, b"\x5a")
        self.uc.mem_write(0x023D8716, b"\x01")
        self.calls = []
        self.mapping, self.count = 12, 513
        for target in (MAP, GETVAR, NATIVE):
            self.uc.hook_add(UC_HOOK_CODE, self._code, begin=target, end=target)

    def _p32(self, address, value):
        self.uc.mem_write(address, int(value).to_bytes(4, "little"))

    def _code(self, uc, address, _size, _user):
        args = tuple(uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3))
        self.assertTrue(uc.reg_read(UC_ARM_REG_CPSR) & THUMB, (hex(address), hex(uc.reg_read(UC_ARM_REG_CPSR))))
        self.calls.append((address, args))
        if address == MAP:
            value = self.count if args[0] == 536 else self.mapping
        elif address == GETVAR:
            value = 0xC0DEC0DE
        else:
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
        self.uc.emu_start(entry, RETURN, count=10000)
        self.assertEqual(self.uc.reg_read(UC_ARM_REG_PC), RETURN)
        self.assertEqual(self.uc.reg_read(UC_ARM_REG_SP), STACK)
        self.assertTrue(self.uc.reg_read(UC_ARM_REG_CPSR) & THUMB)
        self.assertEqual(tuple(self.uc.reg_read(r) for r in CALLEE_SAVED),
                         (app, *SAVED_VALUES[1:]))
        return self.uc.reg_read(UC_ARM_REG_R0)

    def _native_only(self, *, item=25, attr=13, heap=0x44, app=APP):
        self.assertEqual(self._call(self.hook, item, attr, heap, app), 0xFA11BAC0)
        self.assertEqual([x[0] for x in self.calls], [NATIVE])
        self.assertEqual(self.calls[0][1][:3], (item, attr, heap))

    def test_hook_preserves_abi_and_uses_cache_with_real_arguments(self):
        self.assertEqual(self._call(self.hook), 0xC0DEC0DE)
        self.assertEqual([x[0] for x in self.calls], [MAP, MAP, GETVAR])
        self.assertEqual(self.calls[0][1][:2], (25, 0))
        self.assertEqual(self.calls[1][1][:2], (536, 0))
        self.assertEqual(self.calls[2][1][:3], (CTX, 25, 13))

    def test_off_and_invalid_load_or_guard_use_native(self):
        for address, value in ((0x023D8716, 0), (0x023D8703, 0),
                               (0x023D8703, 3), (0x023D8704, 0)):
            with self.subTest(address=hex(address), value=value):
                self.uc.mem_write(address, bytes([value]))
                self._native_only()
                self.calls.clear()
                self.uc.mem_write(0x023D8703, b"\x02")
                self.uc.mem_write(0x023D8704, b"\x5a")
                self.uc.mem_write(0x023D8716, b"\x01")

    def test_null_pointer_chain_and_item_over_limit_never_map(self):
        for name, app in (("app", 0),):
            with self.subTest(name=name):
                self._native_only(app=app)
                self.calls.clear()
        for name, address, value in (("args", APP, 0), ("bs", ARGS, 0),
                                     ("ctx", BS + 0x30, 0), ("cache", CTX + 0x2120, 0)):
            with self.subTest(name=name):
                self._p32(address, value)
                self._native_only()
                self.calls.clear()
                self._p32(APP, ARGS); self._p32(ARGS, BS); self._p32(BS + 0x30, CTX); self._p32(CTX + 0x2120, CACHE)
        self._native_only(item=537)

    def test_mapping_bounds_including_item_536_and_zero_count_fall_back(self):
        self.mapping = 513
        self.assertEqual(self._call(self.hook), 0xFA11BAC0)
        self.assertEqual([x[0] for x in self.calls], [MAP, MAP, NATIVE])
        self.calls.clear()
        self.assertEqual(self._call(self.hook, item=536), 0xFA11BAC0)
        self.assertEqual([x[0] for x in self.calls], [MAP, MAP, NATIVE])
        self.calls.clear()
        self.mapping, self.count = 12, 0
        self.assertEqual(self._call(self.hook), 0xFA11BAC0)
        self.assertEqual([x[0] for x in self.calls], [MAP, MAP, NATIVE])

    def test_helper_rejects_a_non_battle_pocket_attribute(self):
        self.assertEqual(self._call(self.cache, attr=12), 0xFA11BAC0)
        self.assertEqual([x[0] for x in self.calls], [NATIVE])
        self.assertEqual(self.calls[0][1][:3], (25, 12, 0x44))


class ShippedBlobArmContract(BlobArmContract, unittest.TestCase):
    USE_SHIPPED = True


class CompiledBlobArmContract(BlobArmContract, unittest.TestCase):
    USE_SHIPPED = False


if __name__ == "__main__":
    unittest.main(verbosity=2)
