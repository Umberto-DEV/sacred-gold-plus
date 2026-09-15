"""Inventory preservation across expanded pockets, copies and native cheats."""
import ctypes as C
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
OLD = (165, 40, 24, 101, 64, 12, 30, 50)
NEW = (252, 42, 30, 102, 66, 12, 30, 60)
OLD_OFF = (0, 328, 432, 215, 368, 316, 456, 165)
class Slot(C.Structure):
    _fields_ = [('id', C.c_uint16), ('quantity', C.c_uint16)]
class Bag(C.Structure):
    _fields_ = [('slots', Slot * sum(NEW)), ('registered', C.c_uint16 * 2)]
class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        lib = Path(cls.tmp.name) / 'cap.so'
        subprocess.run([shutil.which('clang') or 'cc', '-shared', '-fPIC', '-O2', '-Wall', '-Wextra', '-Werror', str(ROOT/'sorgenti/core.c'), '-o', str(lib)], check=True, capture_output=True)
        cls.lib = C.CDLL(str(lib))
        cls.lib.cap_pocket.restype = C.POINTER(Slot)
        cls.lib.cap_pocket.argtypes = [C.POINTER(Bag), C.c_uint]
        cls.lib.cap_add.argtypes = [C.POINTER(Bag), C.c_uint, C.c_uint16, C.c_uint16]
        cls.lib.cap_take.argtypes = cls.lib.cap_add.argtypes
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()
    def native(self):
        a = (Slot * 487)()
        for p, (off, size) in enumerate(zip(OLD_OFF, OLD)):
            for i in range(size): a[off+i] = Slot(p*300+i+1, (i % 98)+1)
        a[486] = Slot(500, 501)
        return a
    def test_each_pocket_fills_last_complete_page_and_refuses_next(self):
        b=Bag()
        for p, n in enumerate(NEW):
            for i in range(n): self.assertEqual(self.lib.cap_add(C.byref(b),p,i+1,1),1,(p,i))
            self.assertEqual(self.lib.cap_add(C.byref(b),p,1000,1),0)
            last=self.lib.cap_pocket(C.byref(b),p)[n-1]
            self.assertEqual((last.id,last.quantity),(n,1))
    def test_import_export_is_byte_identical_and_does_not_touch_extra(self):
        native=self.native(); before=bytes(native); b=Bag()
        self.lib.cap_import(C.byref(b),native)
        for p,n in enumerate(NEW):
            pocket=self.lib.cap_pocket(C.byref(b),p)
            for i in range(OLD[p],n): self.assertEqual(pocket[i].id,0)
        out=(Slot*487)(); self.lib.cap_export(C.byref(b),out)
        self.assertEqual(bytes(out),before)
    def test_native_cheat_and_direct_menu_reorder_merge_without_losing_extra(self):
        native=self.native(); snapshot=(Slot*487).from_buffer_copy(bytes(native)); b=Bag()
        self.lib.cap_import(C.byref(b),native)
        pocket=self.lib.cap_pocket(C.byref(b),0)
        pocket[170]=Slot(900,3)
        pocket[2]=Slot(901,2)  # menu mutation, native unchanged
        native[1]=Slot(902,999) # cheat mutation, shadow unchanged
        self.lib.cap_reconcile(C.byref(b),native,snapshot)
        self.assertEqual((pocket[1].id,pocket[1].quantity),(902,999))
        self.assertEqual((native[2].id,native[2].quantity),(901,2))
        self.assertEqual((pocket[170].id,pocket[170].quantity),(900,3))
        self.assertEqual(bytes(native),bytes(snapshot))
    def test_take_last_slot_compacts_across_old_boundary(self):
        b=Bag()
        for i in range(252): self.lib.cap_add(C.byref(b),0,i+1,2)
        self.assertEqual(self.lib.cap_take(C.byref(b),0,1,2),1)
        p=self.lib.cap_pocket(C.byref(b),0)
        self.assertEqual((p[0].id,p[250].id,p[251].id),(2,252,0))
        self.assertEqual(self.lib.cap_take(C.byref(b),0,252,1),1)
        self.assertEqual(p[250].quantity,1)
    def test_quantity_limits_stay_999_and_99(self):
        b=Bag()
        for pocket,cap in ((0,999),(3,99)):
            self.assertEqual(self.lib.cap_add(C.byref(b),pocket,1,cap),1)
            self.assertEqual(self.lib.cap_add(C.byref(b),pocket,1,1),0)
            self.assertEqual(self.lib.cap_pocket(C.byref(b),pocket)[0].quantity,cap)
    def test_battle_copy_preserves_extra_and_is_independent(self):
        field=Bag(); battle=Bag()
        for i in range(252): self.lib.cap_add(C.byref(field),0,i+1,2)
        self.lib.cap_copy(C.byref(field),C.byref(battle))
        self.assertEqual(bytes(field),bytes(battle))
        self.lib.cap_take(C.byref(battle),0,252,1)
        self.assertEqual(self.lib.cap_pocket(C.byref(field),0)[251].quantity,2)
        self.lib.cap_copy(C.byref(battle),C.byref(field))
        self.assertEqual(self.lib.cap_pocket(C.byref(field),0)[251].quantity,1)
    def test_move_first_to_last_and_last_to_first(self):
        b=Bag()
        for i in range(252): self.lib.cap_add(C.byref(b),0,i+1,1)
        p=self.lib.cap_pocket(C.byref(b),0)
        self.lib.cap_move(p,252,0,251)
        self.assertEqual((p[0].id,p[251].id),(2,1))
        self.lib.cap_move(p,252,251,0)
        self.assertEqual([p[i].id for i in range(252)],list(range(1,253)))
if __name__=='__main__': unittest.main()
