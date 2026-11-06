"""Bounded HG-T09 machine evidence. Private immutable V4, no output ROM/save.

Native AddIGTSeconds, division helper, tick caller and Training wrapper execute;
only the hardware tick provider and ticks->seconds provider have guarded seams.
"""
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import unittest
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import *
ROOT = next(p for p in Path(__file__).resolve().parents if (p/'source/sgp12/rom.py').is_file())
sys.path.insert(0, str(ROOT/'source'))
from sgp12.rom import Arm9, bl_decode
HERE = Path(__file__).resolve().parent
ENTRY, SITE, STOP, STACK, DATA = 0x0202CDBC, 0x0202CE0E, 0x0271F000, 0x02710000, 0x02701000
CALLER, TIMER, TRAIN = 0x020183B0, 0x021D10E8, 0x023D3000
SHAS = {'EN':'179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90', 'IT':'2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156'}
FUNCTION_SHA = '276a47f980a794aee10600dec8d3a2736ae37263a6dc1cea5c8bb992792cff02'
WRAPPER = bytes.fromhex('f8b50d4a13680d4ca34212d1536b146b002665187341b44667467741f443002fa446664601d1ac466646166300d11c005463034a9047f8bd00303d02524e5431bdcd0202')
CALLER_BYTES = bytes.fromhex('38b50e480068002817d00df09ff80b4a9369d269c01a91410df09cf80d1c0749041c8b68ca68181baa4106d24868e11ab9f35af801488460c56038bde8101d02')
SEAMS = {0x020254FC: bytes.fromhex('004b184789540202'), 0x02025504: bytes.fromhex('08b5820e89011143024a80010023cdf0')}
CALLEE = (UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11)

def sha(b): return hashlib.sha256(b).hexdigest()

class Machine:
    def __init__(self, language, fixed=False):
        self.path=ROOT/f'local/experiments/balance493-2026-10-28/candidate-v4-{language}.nds'
        self.arm=Arm9(self.path)
        assert sha(self.arm.raw)==SHAS[language]
        assert sha(self.arm.leggi(ENTRY,104))==FUNCTION_SHA
        assert self.arm.leggi(CALLER,len(CALLER_BYTES))==CALLER_BYTES
        self.wrapper=bl_decode(0x020183E0,self.arm.leggi(0x020183E0,4))
        assert self.arm.leggi(self.wrapper,len(WRAPPER))==WRAPPER
        self.cpu=Uc(UC_ARCH_ARM,UC_MODE_THUMB)
        self.cpu.mem_map(0x02000000,0x400000)
        self.cpu.mem_map(0x01FF8000,0x4000)
        self.cpu.mem_map(0x027E0000,0x20000)
        self.cpu.mem_map(0x02700000,0x20000)
        for a,o,n in self.arm.segmenti: self.cpu.mem_write(a,bytes(self.arm.raw[o:o+n]))
        if fixed:
            if __package__:
                from sgp131 import igt
            else:
                from sgp131 import igt
            patched=igt.patch_native(self.arm.leggi(ENTRY,104))
            self.cpu.mem_write(ENTRY,patched)
        for a,b in SEAMS.items():
            assert self.arm.leggi(a,len(b))==b
            self.cpu.hook_add(UC_HOOK_CODE,self.seam,None,a,a)
        self.cpu.hook_add(UC_HOOK_CODE,self.observe,None,ENTRY,ENTRY)
        self.cpu.hook_add(UC_HOOK_CODE,self.observe,None,self.wrapper,self.wrapper)
        self.calls=[]
        self.now=0
    def observe(self,cpu,address,size,user): self.calls.append((address,cpu.reg_read(UC_ARM_REG_R0),cpu.reg_read(UC_ARM_REG_R1)))
    def seam(self,cpu,address,size,user):
        self.seams.append(address)
        if address==0x020254FC: result=self.now
        else:
            # Native subtraction and comparison still execute; conversion is
            # the explicit clock seam, with synthetic 1 tick = 1 second.
            value=cpu.reg_read(UC_ARM_REG_R0)|(cpu.reg_read(UC_ARM_REG_R1)<<32)
            assert value==self.now, 'tick-provider subtraction changed'
            result=value
        cpu.reg_write(UC_ARM_REG_R0,result&0xffffffff)
        cpu.reg_write(UC_ARM_REG_R1,result>>32)
        cpu.reg_write(UC_ARM_REG_R2,0xa6a6a6a6)
        cpu.reg_write(UC_ARM_REG_R3,0xa6a6a6a6)
        cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
    def run(self,hms,delta,via='direct',magic=True,played=1000,active=True,old=0):
        cpu=self.cpu;self.calls=[];self.seams=[];self.now=old+delta
        cpu.mem_write(DATA-16,b'\xa5'*16+struct.pack('<HBB',*hms)+b'\x5a'*16)
        cpu.mem_write(TRAIN,b'\xc3'*0x1000)
        cpu.mem_write(TRAIN,struct.pack('<I',0x31544E52 if magic else 0))
        cpu.mem_write(TRAIN+0x30,struct.pack('<Q',played))
        before_train=bytes(cpu.mem_read(TRAIN,0x1000))
        cpu.mem_write(TIMER,struct.pack('<IIQQQ',int(active),DATA,old,0,0))
        before_timer=bytes(cpu.mem_read(TIMER,32))
        cpu.mem_write(STACK-0x100,b'\xa7'*0x40)
        cpu.mem_write(STACK,b'\x7a'*0x40)
        for n,r in enumerate(CALLEE): cpu.reg_write(r,0xb0000000+n)
        cpu.reg_write(UC_ARM_REG_R0,DATA);cpu.reg_write(UC_ARM_REG_R1,delta)
        cpu.reg_write(UC_ARM_REG_SP,STACK);cpu.reg_write(UC_ARM_REG_LR,STOP|1)
        address={'direct':ENTRY,'wrapper':self.wrapper,'caller':CALLER}[via]
        cpu.emu_start(address|1,STOP,count=3000)
        assert cpu.reg_read(UC_ARM_REG_PC)==STOP, 'budget/no return'
        assert cpu.reg_read(UC_ARM_REG_SP)==STACK
        assert [cpu.reg_read(r)for r in CALLEE]==[0xb0000000+n for n in range(8)]
        assert bytes(cpu.mem_read(STACK-0x100,0x40))==b'\xa7'*0x40
        assert bytes(cpu.mem_read(STACK,0x40))==b'\x7a'*0x40
        assert bytes(cpu.mem_read(DATA-16,16))==b'\xa5'*16
        assert bytes(cpu.mem_read(DATA+4,16))==b'\x5a'*16
        expected_played=min(0xffffffffffffffff,played+delta) if via!='direct' and magic and (via!='caller' or active and delta>0) else played
        expected_train=bytearray(before_train);struct.pack_into('<Q',expected_train,0x30,expected_played)
        assert bytes(cpu.mem_read(TRAIN,0x1000))==expected_train, 'Training bytes outside played or wrong played'
        expected_timer=bytearray(before_timer)
        if via=='caller' and active and delta>0:struct.pack_into('<Q',expected_timer,8,self.now)
        assert bytes(cpu.mem_read(TIMER,32))==expected_timer, 'caller timer state'
        if via=='caller' and active and delta>0:
            assert self.calls==[(self.wrapper,DATA,delta),(ENTRY,DATA,delta)], self.calls
            assert self.seams==list(SEAMS),self.seams
        elif via=='caller': assert self.calls==[]
        elif via=='wrapper': assert self.calls==[(self.wrapper,DATA,delta),(ENTRY,DATA,delta)]
        else: assert self.calls==[(ENTRY,DATA,delta)]
        return struct.unpack('<HBB',cpu.mem_read(DATA,4)),expected_played

class IGTTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing = [lang for lang in ('EN','IT') if not (ROOT/f'local/experiments/balance493-2026-10-28/candidate-v4-{lang}.nds').is_file()]
        if missing:
            reason = 'IGT native tests require canonical V4: '+', '.join(missing)
            if os.environ.get('SGP_IGT_REQUIRE_INPUTS') == '1':
                raise AssertionError(reason)
            raise unittest.SkipTest(reason)

    def test_native_red_then_green_boundary_and_controls(self):
        cases = [((0,0,0),0,(0,0,0)), ((0,0,59),1,(0,1,0)),
                 ((997,59,59),1,(998,0,0)), ((998,59,58),1,(998,59,59)),
                 ((998,59,59),1,(999,0,0)), ((998,59,59),61,(999,1,0)),
                 ((999,0,0),1,(999,0,1)), ((999,59,58),1,(999,59,59)),
                 ((999,59,59),1,(999,59,59)), ((999,59,58),2,(999,59,59)),
                 ((998,0,0),7200,(999,59,59))]
        observed=[]
        for language in ('EN','IT'):
            original, fixed=Machine(language),Machine(language,True)
            for via in ('direct','caller'):
                for hms,delta,expected in cases:
                    with self.subTest(language=language,via=via,hms=hms,delta=delta):
                        before=original.run(hms,delta,via)[0]
                        after=fixed.run(hms,delta,via)[0]
                        red=(hms,delta) in (((998,59,59),1),((998,59,59),61))
                        self.assertEqual(before,(999,59,59) if red else expected)
                        self.assertEqual(after,expected)
                        observed.append(dict(language=language,via=via,before=hms,delta=delta,original=before,fixed=after))
            self.assertEqual(sha(original.path.read_bytes()),SHAS[language])
        if os.environ.get('SGP_IGT_REPORT_OUT'):
            with Path(os.environ['SGP_IGT_REPORT_OUT']).open('x') as report:
                report.write(json.dumps(observed,indent=2)+'\n')

    def test_training_counter_and_clock_gates_unchanged(self):
        for language in ('EN','IT'):
            for fixed in (False,True):
                m=Machine(language,fixed)
                for magic in (False,True):
                    for played in (1000,0xfffffffffffffffe):
                        self.assertEqual(m.run((999,59,59),3,'caller',magic,played)[0],(999,59,59))
                self.assertEqual(m.run((998,59,59),1,'caller',active=False)[0],(998,59,59))
                self.assertEqual(m.run((998,59,59),0,'caller')[0],(998,59,59))

    def test_writer_independent_verifier_and_mutants(self):
        if __package__:
            from sgp131 import igt
            from sgp131.igt_verify import verify
        else:
            from sgp131 import igt
            from igt_verify import verify
        for language in ('EN','IT'):
            m=Machine(language);before=bytes(m.arm.raw)
            after,receipt=igt.apply(before,language)
            self.assertTrue(verify(before,after,receipt)['ok'])
            self.assertEqual(after,igt.apply(before,language)[0])
            offset=m.arm.off(SITE,2)
            self.assertEqual([(i,a,b) for i,(a,b) in enumerate(zip(before[offset-4:offset+6],after[offset-4:offset+6])) if a!=b],[(5,0xd3,0xd9)])
            for delta in (-4,-1,0,1,2,5,20):
                broken=bytearray(after);broken[offset+delta]^=1
                with self.assertRaises(ValueError):verify(before,broken,receipt)
            with self.assertRaises(ValueError):igt.apply(after,language)
            native=m.arm.leggi(ENTRY,104)
            for at in (0,0x50,0x52,0x53,103):
                bad=bytearray(native);bad[at]^=1
                with self.assertRaises(ValueError):igt.patch_native(bad)
            with self.assertRaises(ValueError):igt.patch_native(native[:-1])
            with self.assertRaises(ValueError):igt.apply(before,'FR')
            self.assertEqual(sha(m.path.read_bytes()),SHAS[language])

if __name__=='__main__':unittest.main()
