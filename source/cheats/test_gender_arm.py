"""Class B: execute native gender/nature generation using an external ROM."""
import unittest
from gender import gender_code, nature_code, pid_gender

# Optional class B: actual native ARM, with external ROM and JIT permission.
import os
from pathlib import Path


@unittest.skipUnless(Path(os.environ.get('SGP_ROM_GENDER', '')).is_file(),
                     'serve SGP_ROM_GENDER per i contratti ARM nativi')
class NativeGenderTest(unittest.TestCase):
    def test_both_native_generation_paths_all_natures_and_gender_ratios(self):
        import sys
        from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_PROT_ALL, UC_HOOK_CODE
        from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                                       UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5,
                                       UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_SP,
                                       UC_ARM_REG_LR, UC_ARM_REG_PC)
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from sgp12.rom import Arm9
        arm = Arm9(os.environ['SGP_ROM_GENDER'])
        uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        for addr,size in ((0x02000000,0x400000),(0x01FF8000,0x8000),(0x027E0000,0x10000)):
            uc.mem_map(addr,size,UC_PROT_ALL)
        for addr,off,size in arm.segmenti:
            uc.mem_write(addr,bytes(arm.raw[off:off+size]))
        self.assertEqual(arm.leggi(0x0206E108,4),bytes.fromhex('f8b586b0'))
        self.assertEqual(arm.leggi(0x0206E14C,4),bytes.fromhex('f0b589b0'))
        state={'rng':0,'ratio':127,'pid':None}
        def intercept(emu,addr,size,user):
            if addr == 0x0201FD44:
                state['rng']=(state['rng']+1)&65535
                emu.reg_write(UC_ARM_REG_R0,state['rng'])
            elif addr == 0x0206FBE8:
                self.assertEqual(emu.reg_read(UC_ARM_REG_R1),18)
                emu.reg_write(UC_ARM_REG_R0,state['ratio'])
            else:
                sp=emu.reg_read(UC_ARM_REG_SP)
                args=tuple(emu.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3))
                self.assertEqual(args,(0x023C1000,14,19,32))
                self.assertEqual(int.from_bytes(emu.mem_read(sp,4),'little'),1)
                self.assertEqual(bytes(emu.mem_read(sp+8,8)),bytes(8))
                state['pid']=int.from_bytes(emu.mem_read(sp+4,4),'little')
            emu.reg_write(UC_ARM_REG_PC,emu.reg_read(UC_ARM_REG_LR)|1)
        for addr in (0x0201FD44,0x0206FBE8,0x0206DE38):
            uc.hook_add(UC_HOOK_CODE,intercept,begin=addr,end=addr)
        for gender in (None,'male','female'):
            for nature in range(25):
                words=(gender_code(gender,nature) if gender else nature_code(nature)).split()
                for word,value in zip(words[::2],words[1::2]):
                    address=int(word,16)
                    if address >> 28 == 1:
                        uc.mem_write(address & 0x0fffffff,int(value,16).to_bytes(2,'little'))
                uc.ctl_remove_cache(0x0206E108,0x0206E21C)
                for ratio in (0,31,63,127,191,223,254,255):
                    for entry in (0x0206E109,0x0206E14D):
                        state.update(ratio=ratio,pid=None)
                        sp,ret=0x023EF000,0x023EFF00
                        uc.mem_write(sp,(9 if entry==0x0206E109 else 0).to_bytes(4,'little')+(9).to_bytes(4,'little')+bytes(4))
                        for reg,value in ((UC_ARM_REG_R0,0x023C1000),(UC_ARM_REG_R1,14),(UC_ARM_REG_R2,19),
                                          (UC_ARM_REG_R3,32),(UC_ARM_REG_SP,sp),(UC_ARM_REG_LR,ret|1),
                                          (UC_ARM_REG_R4,0x4444),(UC_ARM_REG_R5,0x5555),(UC_ARM_REG_R6,0x6666),(UC_ARM_REG_R7,0x7777)):
                            uc.reg_write(reg,value)
                        uc.emu_start(entry,ret,count=20000)
                        self.assertEqual(uc.reg_read(UC_ARM_REG_PC),ret)
                        self.assertEqual(uc.reg_read(UC_ARM_REG_SP),sp)
                        self.assertEqual(tuple(uc.reg_read(r) for r in (UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7)),(0x4444,0x5555,0x6666,0x7777))
                        pid=state['pid'];self.assertIsNotNone(pid)
                        self.assertEqual(pid%25,nature,(gender,nature,ratio,hex(entry)))
                        expected=pid_gender(0,ratio) if ratio in (0,254,255) else gender
                        if expected is None and entry == 0x0206E14D:
                            expected='male'  # Original fifth argument, unmodified by nature-only.
                        if expected is not None:
                            self.assertEqual(pid_gender(pid,ratio),expected,(gender,nature,ratio,hex(entry)))

if __name__ == "__main__":
    unittest.main()
