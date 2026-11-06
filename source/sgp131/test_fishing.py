"""Focused SG-11 ARM and immutable V4 checks; no ROM output/game/save runs.

Execute outside the sandbox: native Unicorn is SIGILL-blocked inside it.
This private delivery expects both pinned local V4 files, with no skipped tests.
"""
import hashlib
import itertools
import os
from pathlib import Path
import struct
import sys
import unittest
from unittest import mock

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'source/sgp131').is_dir())
sys.path.insert(0,str(ROOT/'source'))
import ndspy.rom
from sgp12.blz import ndspy_load_overlays_sicuri
from sgp131 import archives,lullaby
if __package__:
    from . import fishing as F
    from .fishing_harness import Arm,species,SP,SLOTS,FS,DATA,RET
else:
    import fishing as F
    from fishing_harness import Arm,species,SP,SLOTS,FS,DATA,RET
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import *

PINS={'EN':'179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90',
      'IT':'2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156'}
COUNTS={}

def inputs(language):
    path=Path(os.environ.get('SGP_FISHING_ROM_'+language) or ROOT/f'local/experiments/balance493-2026-10-28/candidate-v4-{language}.nds')
    raw=path.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==PINS[language]
    r=ndspy.rom.NintendoDSRom(raw)
    images={k:bytes(v.data)for k,v in ndspy_load_overlays_sicuri(r,[2,101]).items()}
    records=archives.members(bytes(r.getFileByName('a/0/3/7')))
    return raw,images,records

class Fishing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing = [lang for lang in ('EN','IT') if not Path(os.environ.get('SGP_FISHING_ROM_'+lang) or ROOT/f'local/experiments/balance493-2026-10-28/candidate-v4-{lang}.nds').is_file()]
        if missing:
            reason = 'Fishing native tests require canonical V4: '+', '.join(missing)
            if os.environ.get('SGP_FISHING_REQUIRE_INPUTS') == '1':
                raise AssertionError(reason)
            raise unittest.SkipTest(reason)
        cls.raw,cls.old,cls.records=inputs('EN')
        cls.new={k:F.patch_overlay(v,k)for k,v in cls.old.items()}

    def test_original_red_and_patched_green_battle_and_phone(self):
        old,new=Arm(self.old),Arm(self.new)
        record=self.records[0]
        self.assertEqual(old.battle(record,1,3),[90,170,170,0,170])
        self.assertEqual(new.battle(record,1,3),[90,170,170,170,170])
        self.assertEqual(old.battle(record,2,4),[90,0,130,130,130])
        self.assertEqual(new.battle(record,2,4),[90,171,130,130,130])
        self.assertEqual(old.phone(record),0)
        self.assertEqual(new.phone(record),170)

    def test_all_active_records_rods_five_times_four_swarms(self):
        total=old_zero=new_zero=phone_total=phone_old_zero=0
        for language in ('EN','IT'):
            raw,images,records=inputs(language)
            old=Arm(images);new=Arm({k:F.patch_overlay(v,k)for k,v in images.items()})
            local_total=local_old_zero=0
            for index,record in enumerate(records):
                patched=F.patch_member(record,index)if len(record)==192 else record
                if record[4] or record[5]:
                    for time,slot in itertools.product(range(5),range(5)):
                        got=new.phone(patched,time=time,slot=slot)
                        tail=struct.unpack_from('<H',patched,192)[0]
                        want=tail if time==2 and slot==3 and tail else species(record,1)[slot]
                        self.assertEqual(got,want,(language,index,time,slot))
                        self.assertNotEqual(got,0)
                        phone_old_zero+=old.phone(record,time=time,slot=slot)==0
                        phone_total+=1
                for rod in range(3):
                    if not record[3+rod]:continue
                    for time in range(5):
                        for swarm in ((False,True)if index in (5,8,59,92)else(False,)):
                            before=old.battle(record,rod,time,swarm)
                            got=new.battle(patched,rod,time,swarm)
                            expected=species(record,rod)
                            night=struct.unpack_from('<H',patched,192)[0]
                            if time in (3,4) and rod in(1,2) and night:
                                expected[{1:3,2:1}[rod]]=night
                            if swarm:
                                fish={5:340,8:211,59:223,92:369}[index]
                                for slot in ((2,)if rod==0 else(0,2,3)if rod==1 else range(5)):
                                    expected[slot]=fish
                            self.assertEqual(got,expected,(language,index,rod,time,swarm))
                            self.assertNotIn(0,got)
                            total+=1;local_total+=1;old_zero+=0 in before;local_old_zero+=0 in before;new_zero+=0 in got
            self.assertEqual((local_total,local_old_zero),(1125,340))
        COUNTS['battle']={'cases':total,'original_zero_cases':old_zero,'patched_zero_cases':new_zero}
        COUNTS['phone']={'cases':phone_total,'original_zero_cases':phone_old_zero,'patched_zero_cases':0}

    def test_zero_nonzero_override_every_rod_time_and_phone_slot(self):
        old,new=Arm(self.old),Arm(self.new)
        count=0
        for tail,rod,time in itertools.product((0,90,493),range(3),range(5)):
            record=self.records[0]+struct.pack('<HH',tail,0)
            before=old.battle(record,rod,time)
            after=new.battle(record,rod,time)
            if tail or rod==0 or time not in(3,4):self.assertEqual(before,after)
            else:self.assertEqual(after,species(record,rod))
            count+=1
        for tail,time,slot in itertools.product((0,90,493),range(5),range(5)):
            record=self.records[0]+struct.pack('<HH',tail,0)
            got=new.phone(record,time=time,slot=slot)
            want=tail if tail and time==2 and slot==3 else species(record,1)[slot]
            self.assertEqual(got,want)
            self.assertEqual(new.calls.count(0x0201FD44),1)
            self.assertEqual(new.calls.count(0x020F2998),1)
            if tail or time!=2 or slot!=3:self.assertEqual(got,old.phone(record,time=time,slot=slot))
            count+=1
        COUNTS['override_controls']=count

    def test_phone_full_function_land_times_unknown_default_no_encounters(self):
        old,new=Arm(self.old),Arm(self.new)
        count=0
        for trainer,time,slot in itertools.product((0,10,12,255),(0,1,2,3,4,255),range(12)):
            got=new.phone(self.records[0],trainer,time,slot)
            expected=struct.unpack_from('<H',self.records[0],{1:44,2:68}.get(time,20)+slot*2)[0]
            self.assertEqual(got,expected)
            self.assertEqual(got,old.phone(self.records[0],trainer,time,slot))
            count+=1
        for trainer,time in itertools.product((0,11,255),range(5)):
            self.assertEqual(new.phone(self.records[0],trainer,time,0,False),19)
            self.assertEqual(new.calls,[0x0203B324])
        COUNTS['phone_land_controls']=count

    def test_complete_control91_unchanged_and_oldrod_invalidrod_noops(self):
        old,new=Arm(self.old),Arm(self.new)
        record=self.records[91]
        self.assertEqual(len(record),196)
        for rod,time in itertools.product(range(3),range(5)):
            self.assertEqual(old.battle(record,rod,time),new.battle(record,rod,time))
        for time,slot in itertools.product(range(5),range(5)):
            self.assertEqual(old.phone(record,time=time,slot=slot),new.phone(record,time=time,slot=slot))
        cpu=Arm(self.new)
        for rod in (0,3,255):
            cpu.cpu.mem_write(DATA,(self.records[0]+b'\0'*4))
            cpu.cpu.mem_write(SLOTS,bytes(range(40)))
            cpu.call(0x02246AD4,[DATA,rod,SLOTS])
            self.assertEqual(bytes(cpu.cpu.mem_read(SLOTS,40)),bytes(range(40)))

    def test_native_static_magnet_pull_and_ordinary_ability_controls(self):
        # The original ability gate and species-filter loop run as ARM. Only
        # the external personal-type getter is replaced by these known types.
        # This does not simulate a full lead Pokemon or complete wild battle.
        for images,time in((self.old,1),(self.new,3)):
            cpu=Arm(images)
            got=cpu.battle(self.records[0],1,time)
            self.assertEqual(got,[90,170,170,170,170])
            cpu.state['random']=2
            def personal(u,a,n,x):
                if a==0x0206FBE8:
                    mon,attr=u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1)
                    assert mon in(90,170) and attr in(6,7)
                    value={90:(11,15),170:(11,13)}[mon][attr-6]
                    u.reg_write(UC_ARM_REG_R0,value)
                    u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
            cpu.cpu.hook_add(UC_HOOK_CODE,personal)
            for actual,type_,gate,expected,calls in((9,13,9,1,2),(42,8,42,0,1),(0,13,9,0,0)):
                cpu.cpu.mem_write(FS,bytes(32))
                cpu.cpu.mem_write(FS+14,bytes([actual]))
                cpu.cpu.mem_write(DATA+256,b'\xff')
                cpu.cpu.mem_write(SP,struct.pack('<III',type_,gate,DATA+256))
                self.assertEqual(cpu.call(0x02248150,[0,FS,SLOTS,5]),expected)
                self.assertEqual(cpu.calls.count(0x0201FD44),calls)
                self.assertEqual(bytes(cpu.cpu.mem_read(DATA+256,1)),b'\x03'if expected else b'\xff')

    def test_native_slot_roll_boundaries_preserve_rng_call_count(self):
        for images in(self.old,self.new):
            cpu=Arm(images)
            for roll,expected in((0,0),(39,0),(40,1),(69,1),(70,2),(84,2),(85,3),(94,3),(95,4),(99,4)):
                cpu.state['random']=roll
                self.assertEqual(cpu.call(0x02247764,[1]),expected)
                self.assertEqual(cpu.calls,[0x0201FD44,0x020F2998])

    def test_radio_zero_guard_retains_nonzero_callback(self):
        for images in(self.old,self.new):
            for tail in(0,90,493):
                cpu=Arm(images)
                cpu.cpu.reg_write(UC_ARM_REG_SP,SP)
                cpu.cpu.mem_write(SP+192,struct.pack('<H',tail))
                cpu.cpu.reg_write(UC_ARM_REG_R4,0x1234)
                cpu.cpu.reg_write(UC_ARM_REG_R5,0x5678)
                seen=[]
                def radio(u,a,n,x):
                    if a==0x021F7114:
                        seen.append(tuple(u.reg_read(r)for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)))
                        u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
                cpu.cpu.hook_add(UC_HOOK_CODE,radio)
                cpu.cpu.emu_start(0x021F7265,0x021F7274,count=16)
                self.assertEqual(seen,[(0x5678,0x1234,tail)]if tail else[])

    def test_native_no_bite_zero_rate_and_safari_dispatch_controls(self):
        # Execute real caller entry's zero-rate return; no fishing substitutions
        # are reached. Safari check executes real dispatcher, replacing only
        # downstream full generation, and verifies the distinct target/arguments.
        for images in(self.old,self.new):
            for rod in range(3):
                cpu=Arm(images)
                def rate(u,a,n,x):
                    if a==0x0224802C:
                        u.reg_write(UC_ARM_REG_R0,0);u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
                cpu.cpu.hook_add(UC_HOOK_CODE,rate)
                self.assertEqual(cpu.call(0x02246F70,[FS,rod,DATA]),0)
                self.assertEqual(cpu.calls,[])
            for safari in(0,1):
                cpu=Arm(images);seen=[]
                cpu.cpu.mem_write(SP,struct.pack('<III',0x02303000,2,safari))
                def downstream(u,a,n,x):
                    if a in(0x02247DA0,0x02247B64):
                        seen.append((a,tuple(u.reg_read(r)for r in(UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3))))
                        u.reg_write(UC_ARM_REG_R0,1);u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
                cpu.cpu.hook_add(UC_HOOK_CODE,downstream)
                self.assertEqual(cpu.call(0x02247514,[FS,DATA,0x02304000,SLOTS]),1)
                self.assertEqual(seen[0][0],0x02247DA0 if safari else 0x02247B64)
                self.assertEqual(seen[0][1],(FS,DATA,2,0x02303000)if safari else(DATA,2,0x02303000,SLOTS))

    def test_exact_overlay_complements_and_instruction_branches(self):
        import capstone
        for overlay in(2,101):
            F.verify_images(self.old[overlay],self.new[overlay],overlay)
            base,size,start,end,pin=F.OVERLAYS[overlay]
            site,before,after=F.WINDOWS[overlay]
            for at in(0,site-base,site-base+1,site-base+len(after)-1,size-1):
                altered=bytearray(self.new[overlay]);altered[at]^=1
                with self.assertRaises(ValueError):F.verify_images(self.old[overlay],bytes(altered),overlay)
            with self.assertRaises(ValueError):F.patch_overlay(self.new[overlay],overlay)
            ins=list(capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_THUMB).disasm(after,site))
            self.assertEqual(sum(i.size for i in ins),len(after))
            self.assertTrue(all(i.address%2==0 for i in ins))
            if overlay==101:
                calls=[(i.mnemonic,i.op_str)for i in ins if i.mnemonic in('bl','blx')]
                self.assertEqual(calls,[('bl','#0x201fd44'),('blx','#0x20f2998')])

    def test_delta_exact130_prefix_tail_complete_complement_and_mutants(self):
        for language in('EN','IT'):
            raw,images,records=inputs(language)
            delta=F.derive_fishing_encounters(raw,language)
            self.assertEqual((delta.archive,delta.file_id,delta.producers()),('a/0/3/7',166,['fishing-encounters']))
            self.assertEqual(len(delta.members),130)
            replacement=delta.replacements()
            self.assertEqual(set(replacement),{i for i,b in enumerate(records)if len(b)==192})
            for row in delta.members:
                F.check_member(row.index,records[row.index],row.after,language)
                self.assertEqual(row.after[:192],records[row.index])
                self.assertEqual(struct.unpack_from('<HH',row.after,192),(0,{5:340,8:211,59:223,92:369}.get(row.index,0)))
                for at in(0,191,192,194,195):
                    altered=bytearray(row.after);altered[at]^=1
                    with self.assertRaises(ValueError):F.check_member(row.index,records[row.index],bytes(altered),language)
            # Use existing generic owner in-memory; registry admission is ROOT's
            # integration responsibility, not a bypass performed by this module.
            import ndspy.rom
            r=ndspy.rom.NintendoDSRom(raw);old=bytes(r.getFileByName(F.ARCHIVE))
            new=archives.apply_members(old,replacement)
            archives.verify_members(old,new,replacement)
            got=archives.members(new)
            self.assertEqual(len(got),142)
            for index in set(range(142))-set(replacement):self.assertEqual(got[index],records[index])
            self.assertEqual([len(b)for b in got],[196]*142)

    def test_both_language_slots_lullaby_composition_both_orders_and_receipt_mutants(self):
        slots={}
        for language in('EN','IT'):
            raw,images,records=inputs(language)
            lfirst,lr=lullaby.apply(raw,language)
            a,ar=F.apply(lfirst,language)
            ffirst,fr=F.apply(raw,language)
            b,br=lullaby.apply(ffirst,language)
            self.assertEqual(a,b)
            slots[language]=ar['verification']['slots']
            self.assertEqual([e-s for s,e in slots[language]],[42700,53576])
            bad=dict(ar,output_sha256='0'*64)
            with self.assertRaises(ValueError):F.verify(lfirst,a,bad)
            mutated=bytearray(a);mutated[0x15E]^=1
            with self.assertRaises(ValueError):F.verify(lfirst,bytes(mutated),ar)
            self.assertEqual(hashlib.sha256(raw).hexdigest(),PINS[language])
        COUNTS['compressed_slots']=slots

if __name__=='__main__':
    import json
    result=unittest.main(exit=False,verbosity=2).result
    print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'coverage':COUNTS},sort_keys=True))
    sys.exit(not result.wasSuccessful())
