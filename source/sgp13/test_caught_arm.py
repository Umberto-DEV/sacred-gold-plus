"""Run the real HUD dispatcher and marker renderer from private base ROMs.

Other graphics transfers are intercepted at native API boundaries; the marker
component selection and bytes, register preservation, and unrelated dispatch
are observed. This is CPU coverage, not an emulator screenshot test.
"""
import os, struct, unittest
from pathlib import Path
from sgp12.rom import Rom, Arm9
from sgp13 import caught as patch
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE
from unicorn.arm_const import *
ROOT=Path(os.environ.get('SGP13_BASE_DIR', '.'))
GFX={0x2264dcc,0x22657e4,0x2265474,0x2265500,0x22652d0,0x2265354,0x226516c,0x2264e34,0x22655b0,0x22655f0,0x22656cc}
BATTLES={'wild':0,'trainer_single':1,'trainer_double':3,'link_no_trainer':4,'link_trainer':5,'frontier_trainer':0x81,'partner_trainer':0x4b,'partner_without_trainer':0x4a,'roamer':0x100,'safari':0x20,'palpark':0x200}

@unittest.skipUnless(os.environ.get('SGP13_BASE_DIR'), 'needs private 1.2.5 inputs and executable JIT')
class NativeCaughtTests(unittest.TestCase):
 def test_real_dispatch_and_marker_for_both_languages(self):
  rows=[];summ=[]
  for lang in ['EN','IT']:
   p=ROOT/f'sgp-1.2.5-{lang}.nds';rom=Rom(p.read_bytes());v,_,ov=rom.immagine_overlay(12);a=Arm9(p)
   for variant in ['baseline','nop_trainer_mask']:
    u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.mem_map(0x2000000,0x400000);u.mem_map(0x1ff0000,0x10000);u.mem_map(0x27e0000,0x20000);u.mem_map(0x6400000,0x10000)
    for start,off,n in a.segmenti:u.mem_write(start,bytes(a.raw[off:off+n]))
    u.mem_write(v['ram'],ov if variant=='baseline' else patch.patch_image(ov,v['ram']))
    stop=0x23f0000;bs=0x2380000;hp=0x2381000;obj=0x2382000;spr=0x2382100;proxy=0x2382200;sp=0x23ff000
    log=[];getter=[];copies=[]
    def hook(uc,address,size,data):
     if address in GFX:
      log.append([hex(address),uc.reg_read(UC_ARM_REG_R1)])
      uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
     elif address==0x2265b58:getter.append(uc.reg_read(UC_ARM_REG_R0))
     elif address==0x2024b1c:
      uc.reg_write(UC_ARM_REG_R0,proxy);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
     elif address==0x20d47b8:
      src=uc.reg_read(UC_ARM_REG_R0);dst=uc.reg_read(UC_ARM_REG_R1);n=uc.reg_read(UC_ARM_REG_R2)
      copies.append([hex(src),hex(dst),n]);uc.mem_write(dst,bytes(uc.mem_read(src,n)))
      uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
    u.hook_add(UC_HOOK_CODE,hook)
    for name,btype in BATTLES.items():
     for bartype in range(8):
      for caught in [0,1]:
       for req in [0x200,0xffff,0xfdff]:
        log.clear();getter.clear();copies.clear();u.mem_write(hp,bytes(0x80));u.mem_write(bs,bytes(0x100));u.mem_write(obj,struct.pack('<I',spr));u.mem_write(proxy,struct.pack('<II',0,0x1000))
        u.mem_write(hp+4,struct.pack('<I',obj));u.mem_write(hp+0xc,struct.pack('<I',bs));u.mem_write(hp+0x25,bytes([bartype]));u.mem_write(hp+0x4b,bytes([caught]));u.mem_write(bs+0x2c,struct.pack('<I',btype))
        u.reg_write(UC_ARM_REG_R0,hp);u.reg_write(UC_ARM_REG_R1,23);u.reg_write(UC_ARM_REG_R2,req);u.reg_write(UC_ARM_REG_SP,sp);u.reg_write(UC_ARM_REG_LR,stop|1)
        for reg in [UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7]:u.reg_write(reg,0xa5a5a5a5)
        u.emu_start(0x226498d,stop,count=2000)
        assert u.reg_read(UC_ARM_REG_SP)==sp
        assert all(u.reg_read(reg)==0xa5a5a5a5 for reg in [UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7])
        expected=bool(req&0x200 and bartype in [1,3,5] and (variant!='baseline' or not btype&1))
        assert bool(getter)==expected,(lang,variant,name,bartype,caught,hex(req),getter)
        if getter:
         assert getter==[59 if caught else 38]
         assert copies==[[hex(0x226d6e0+32*(59 if caught else 38)),hex(0x6401420),32]],copies
        rows.append({'language':lang,'variant':variant,'battle':name,'battle_flags':hex(btype),'bar_type':bartype,'caught':caught,'request':hex(req),'components':getter.copy(),'other_calls':log.copy(),'copies':copies.copy()})
  # Same non-icon component dispatch and arguments before/after for every case.
  for lang in ['EN','IT']:
   left=[r for r in rows if r['language']==lang and r['variant']=='baseline'];right=[r for r in rows if r['language']==lang and r['variant']!='baseline']
   assert len(left)==len(right)
   for a,b in zip(left,right):assert a['other_calls']==b['other_calls'],(a,b)
   summ.append({'language':lang,'cases_per_variant':len(left),'cases_total':len(left)+len(right),'native_icon_matrix_matches_expected':True,'non_icon_dispatch_identical':True,'stack_and_r4_r7_preserved':True})

if __name__ == '__main__':
 unittest.main()
