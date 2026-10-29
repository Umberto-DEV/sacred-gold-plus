"""Private-input composition proof: another feature owns every byte of the gap."""
import os,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from sgp13.guide import install,build_content
from sgp12.rom import Arm9

class InstallerCompositionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  root=os.environ.get('SGP_GUIDE_BASE_DIR');pret=os.environ.get('SGP_PRET_SOURCE')
  if not root or not pret:raise unittest.SkipTest('set SGP_GUIDE_BASE_DIR and SGP_PRET_SOURCE for private EN/IT composition proof')
  cls.root=Path(root);cls.charmap=Path(pret)/'charmap.txt'
  for lang in ('EN','IT'):
   if not (cls.root/('sgp-1.3-space-v2-'+lang+'.nds')).is_file():raise unittest.SkipTest('expanded '+lang+' input absent')
 def test_entire_nonempty_foreign_gap_survives_en_and_it_install_and_readback(self):
  content=build_content([{'id':1,'title':'Guide','entries':[{'id':1,'title':'Entry','pages':[['Test.']]}]}],lambda s:[ord(c) for c in s]+[65535],lambda s:len(s)*6)
  sentinel=bytes((i*37+11)%255+1 for i in range(0x1b00))
  for lang in ('EN','IT'):
   with self.subTest(language=lang),tempfile.TemporaryDirectory() as d:
    d=Path(d);arm=Arm9(self.root/('sgp-1.3-space-v2-'+lang+'.nds'))
    boundary=arm.leggi(0x023d7f00,256)
    arm.scrivi(0x023d6000,sentinel);arm.salva(d/'input.nds')
    result=install(d/'input.nds',d/'output.nds',content,lang,self.charmap,d/'build')
    readback=Arm9(d/'output.nds')
    # Independent original file offset: archive append must not move ARM9.
    gap_offset=arm.off(0x023d6000,len(sentinel))
    self.assertEqual((d/'output.nds').read_bytes()[gap_offset:gap_offset+len(sentinel)],sentinel)
    self.assertEqual(readback.leggi(0x023d6000,0x1b00),sentinel)
    self.assertEqual(readback.leggi(0x023d7f00,256),boundary)
    self.assertLessEqual(result['code_bytes'],0x2000)
    # The lower-layer icon depends on the exact native background/palettes.
    import ndspy.rom,ndspy.narc
    from sgp13.resources import append_file
    raw=(d/'input.nds').read_bytes();rom=ndspy.rom.NintendoDSRom(raw)
    fid=rom.filenames.idOf('a/0/1/4')
    for member in (7,8,9,14):
     archive=ndspy.narc.NARC(rom.files[fid]);changed=bytearray(archive.files[member]);changed[-1]^=1;archive.files[member]=bytes(changed)
     source=d/f'changed-{member}.nds';output=d/f'rejected-{member}.nds'
     source.write_bytes(append_file(raw,fid,archive.save()))
     with self.assertRaisesRegex(ValueError,'field graphics guard '+str(member)):
      install(source,output,content,lang,self.charmap,d/f'build-{member}')
     self.assertFalse(output.exists())
if __name__=='__main__':unittest.main()
