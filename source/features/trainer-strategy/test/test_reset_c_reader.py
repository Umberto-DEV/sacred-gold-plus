"""Owned synthetic ELF counterexamples; no retail bytes, compiler or CPU."""
from pathlib import Path
import importlib.util
import struct
import unittest


def owned_elf():
    """Construct one small object with a declared, owned Thumb linkage profile."""
    labels=['','.strtab','.text','.rel.text','.ARM.exidx','.rel.ARM.exidx',
            '.comment','.note.GNU-stack','.ARM.attributes','.llvm_addrsig','.symtab']
    strings=bytearray(b'\0')
    def name(text):
        index=len(strings);strings.extend(text.encode()+b'\0');return index
    names=[0]+[name(x)for x in labels[1:]]
    funcs=['MonSetMoveInSlot','SetMonData','GetMoveMaxPP','MonSetMoveInSlot_ResetPpUp']
    symbols=[(0,0,0,0,0,0),(name('owned.c'),0,0,4,0,0xfff1),(0,0,0,3,0,2)]
    for tag,offset in(('$t',0),('$d',4),('$t',8),('$d',12),('$t',16),('$d',20),('$t',24)):
        symbols.append((name(tag),offset,0,0,0,2))
    for fn,offset,size in zip(funcs,(1,9,17,25),(8,8,8,52)):
        symbols.append((name(fn),offset,size,0x12,0,2))
    text=b''.join(struct.pack('<HHI',0x4b00,0x4718,target)for target in(0x20714e9,0x206ec41,0x207332d))
    # This is an owned finite register/stack program, assembled as integers.
    root=[0xb5fe,0x0014,0x000e,0x0005,0xf7ff,0xfffe,0x2700,0x9701,
          0x0021,0x313e,0xaa01,0x0028,0xf7ff,0xfffe,0x0030,0x0039,
          0xf7ff,0xfffe,0x9002,0x343a,0xaa02,0x0028,0x0021,0xf7ff,0xfffe,0xbdfe]
    text+=struct.pack('<26H',*root)
    rel=b''.join(struct.pack('<II',offset,(symbol<<8)|10)for offset,symbol in((32,10),(48,11),(56,12),(70,11)))
    contents=[b'',bytes(strings),text,rel,struct.pack('<II',24,1),struct.pack('<II',0,(2<<8)|42),
              b'owned test\0',b'',b'A\x00',b'',b''.join(struct.pack('<IIIBBH',*s)for s in symbols)]
    specs=[(0,0,0,0,0,0),(3,0,0,0,1,0),(1,6,0,0,4,0),(9,64,10,2,4,8),
           (0x70000001,130,2,0,4,0),(9,64,10,4,4,8),(1,48,0,0,1,1),
           (1,0,0,0,1,0),(0x70000003,0,0,0,1,0),(0x6fff4c03,0x80000000,10,0,1,0),(2,0,1,10,4,16)]
    blob=bytearray(b'\0'*52);sections=[]
    for index,((kind,flags,link,info,align,entsize),body)in enumerate(zip(specs,contents)):
        if index==0:sections.append((0,)*10);continue
        blob.extend(b'\0'*((-len(blob))%align));offset=len(blob);blob.extend(body)
        sections.append((names[index],kind,flags,0,offset,len(body),link,info,align,entsize))
    blob.extend(b'\0'*((-len(blob))%4));shoff=len(blob)
    blob.extend(b''.join(struct.pack('<10I',*s)for s in sections))
    blob[:16]=b'\x7fELF\x01\x01\x01'+b'\0'*9
    struct.pack_into('<HHIIIIIHHHHHH',blob,16,1,40,1,0,0,shoff,0x5000000,52,0,0,40,len(sections),1)
    return bytes(blob),sections,shoff


class ResetCReaderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).parents[1]/'tools/rileggi_reset_c.py';s=importlib.util.spec_from_file_location('Reset_C_ELF_test',p)
        cls.T=importlib.util.module_from_spec(s);s.loader.exec_module(cls.T)
    def inspect(self,data):return self.T.inspect_elf(data,0x22f1000)
    def test_owned_complete_profile_keeps_duplicate_mapping_symbols(self):
        blob,_,_=owned_elf();linked,r=self.inspect(blob)
        self.assertEqual(len(linked),76);self.assertEqual(r['code_bytes'],64)
        self.assertEqual(r['instruction_count'],28);self.assertEqual(len(r['mapping_symbols']),7)
        self.assertEqual(r['root_frame_bytes'],32);self.assertEqual(r['exidx']['addend'],24)
        self.assertEqual(r['exidx']['descriptor'],1);self.assertFalse(r['exidx']['mapped'])
        self.assertEqual([x['callee']for x in r['calls']],['MonSetMoveInSlot','SetMonData','GetMoveMaxPP','SetMonData'])
    def test_exidx_cannot_be_ignored_by_the_text_loader(self):
        blob,sec,_=owned_elf()
        for offset,value in((sec[4][4],0),(sec[4][4]+4,0),(sec[5][4]+4,(2<<8)|2)):
            bad=bytearray(blob);struct.pack_into('<I',bad,offset,value)
            with self.assertRaises(ValueError):self.inspect(bytes(bad))
    def test_THM_CALL_type_symbol_addend_and_offset_are_all_checked(self):
        blob,sec,_=owned_elf();a=sec[3][4]
        for offset,value in((a+4,(10<<8)|2),(a+4,(11<<8)|10),(a,34),(a+8,32)):
            bad=bytearray(blob);struct.pack_into('<I',bad,offset,value)
            with self.assertRaises(ValueError):self.inspect(bytes(bad))
        bad=bytearray(blob);struct.pack_into('<H',bad,sec[2][4]+34,0xffff)
        with self.assertRaises(ValueError):self.inspect(bytes(bad))
    def test_mapping_symbol_drift_does_not_disappear_in_a_name_dictionary(self):
        blob,sec,_=owned_elf();bad=bytearray(blob)
        struct.pack_into('<I',bad,sec[10][4]+4*16+4,6)
        with self.assertRaises(ValueError):self.inspect(bytes(bad))
    def test_native_target_and_frame_drift_are_rejected(self):
        blob,sec,_=owned_elf()
        for offset,value in((sec[2][4]+4,0x20714b1),(sec[2][4]+12,0x206ec40)):
            bad=bytearray(blob);struct.pack_into('<I',bad,offset,value)
            with self.assertRaises(ValueError):self.inspect(bytes(bad))
        for word in(0xb5f0,0xb081):
            bad=bytearray(blob);struct.pack_into('<H',bad,sec[2][4]+24,word)
            with self.assertRaises(ValueError):self.inspect(bytes(bad))
    def test_external_symbol_and_allocated_metadata_are_rejected(self):
        blob,sec,shoff=owned_elf();bad=bytearray(blob)
        struct.pack_into('<H',bad,sec[10][4]+10*16+14,0)
        with self.assertRaises(ValueError):self.inspect(bytes(bad))
        bad=bytearray(blob);struct.pack_into('<I',bad,shoff+6*40+8,50)
        with self.assertRaises(ValueError):self.inspect(bytes(bad))
    def test_header_section_payload_and_bounds_are_checked(self):
        blob,sec,shoff=owned_elf()
        for bad in(blob[:51],blob[:-1],blob+b'x'*(1024**2),b'X'+blob[1:]):
            with self.assertRaises(ValueError):self.inspect(bad)
        for offset,value in((shoff+2*40+16,0),(shoff+3*40+16,sec[2][4]),(shoff+4*40+20,16)):
            bad=bytearray(blob);struct.pack_into('<I',bad,offset,value)
            with self.assertRaises(ValueError):self.inspect(bytes(bad))


if __name__=='__main__':unittest.main()
