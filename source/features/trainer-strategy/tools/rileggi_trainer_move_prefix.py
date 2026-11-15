#!/usr/bin/env python3
"""Read the type3 first-move prefix, veneer and exact trainer31 record.

Reuses qualified complete-caller resources and the Bag raw/ndspy NARC reader.
The branch at the stop gate is authenticated separately, never admitted as an
executed instruction. No constructor, service model, CPU or compiler runs.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import mmap
import struct
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve();SOURCE=HERE.parents[3]
C=load(HERE.with_name('rileggi_box_move_caller.py'),'prefix_complete_Box_resources')
R,need,sha=C.R,C.need,C.sha
NEW_THUMB={
 'trainer_prefix':(0x2073a22,30,14,'f0cf7e6ea2bf9a23e10a5b15407e73ab7332565696bacc9113991561a2a28a9c'),
 'mon_veneer':(0x20714e8,4,2,'8bdadb00ad3389fd9d10292c291d2b47f6d30d0531c80bbc0dbfbd0813d70c8c')}
NEW_DATA={'mon_target':(0x20714ec,4,'1546a4580bb2146c10d9a99c44c9a226821a7cf8955b67aa4b3437ac10536a15')}
GATE=(0x2073a40,2,'33b2105ff852e91db7fe48ade9b9bd8e231b1be0e90301c59b2adb9c36dcbe78')
THUMB={**C.THUMB,**NEW_THUMB};DATA={**C.DATA,**NEW_DATA}
CODE_SPANS,SDK_CODE_SPANS=C.CODE_SPANS,C.SDK_CODE_SPANS
BAG_TOOL=HERE.parents[2]/'borsa/tools/attribuisci.py'
BAG_SHA='1f99c1ed839de26ad101bb98f1bf8f7d2a1af46bd905a2e156e665063f911a16'
HEADER_SHA='db2e0fa9e4d0b97a0d1721e878001bcddafe1e379827adccc37844cdbce13fff'
MEMBER_SHA='2096c9d5a3943dca51dec0ea9b0b006387f2fb5b0d6778a49f58c2803806395c'
FIRST_SHA='d8633b3decabc64d9098784c47c1b1b3bc07843a67661a07df1bf24378e8fdfa'
ARCHIVES={55:(184,20716,'4de9e541894f6573c5b52e338de911a71fcf82c206ebf041bccb81e817c13299'),
          56:(185,31286,'964a3efd40d83ecb196035f257264ba0e76a55818ed0d13aadde15b890451da9')}
read_new=types.FunctionType(C.BOX.read.__code__,{**C.BOX.read.__globals__,'THUMB':NEW_THUMB,'DATA':{**NEW_DATA,'prefix_gate':GATE,**{n:C.DATA[n]for n in('wrapper_pool','lcg_pool')}}},argdefs=C.BOX.read.__defaults__)


def record_layout(header,member,*,authenticate=True):
    need(type(authenticate)is bool and type(header)is bytes and type(member)is bytes,'typed prefix record/header/authentication')
    need(len(header)==20 and header[0]==3 and header[1]==72 and header[3]==6 and len(member)==108,'exact type3 six-by18 layout without trailer')
    if authenticate:need(sha(header)==HEADER_SHA and sha(member)==MEMBER_SHA and sha(member[:18])==FIRST_SHA,'exact trainer31 header/party/first-record identity')
    level,species,item,move=struct.unpack_from('<4H',member,2)
    return dict(format=3,count=6,stride=18,bytes=108,trailing_bytes=0,first_level=level,first_species=species&1023,
        first_form=species>>10,first_item=item,first_move=move,move_offset=8,move_bytes=2,
        header_sha256=sha(header),member_sha256=sha(member),first_record_sha256=sha(member[:18]),authenticated=authenticate)


def read_records(rom):
    import ndspy.code
    need(sha(BAG_TOOL.read_bytes())==BAG_SHA,'qualified Bag NARC reader identity')
    bag=load(BAG_TOOL,'prefix_qualified_Bag_NARC_readback')
    with Path(rom).open('rb')as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)as raw:
        off,base,size=(R.u32(raw,x)for x in(0x20,0x28,0x2c));need(size<=4*1024**2,'bounded prefix ARM9 route owner')
        sections=ndspy.code.MainCodeFile(raw[off:off+size],base).sections;routes={};payloads={}
        def read(a,n):
            need(base<=a and a+n<=base+size,'prefix native route initialized range')
            b=bytes(raw[off+a-base:off+a-base+n]);owners=[s for s in sections if s.ramAddress<=a and a+n<=s.ramAddress+len(s.data)]
            need(len(owners)==1,'one decoded prefix route owner');s=owners[0]
            need(b==s.data[a-s.ramAddress:a-s.ramAddress+n],'physical/ndspy native trainer route')
            return b,dict(ram=a,bytes=n,rom_offset=off+a-base,sha256=sha(b))
        pool,pool_receipt=read(0x2007520,4);table=struct.unpack('<I',pool)[0];need(table==0x210f210,'native NARC table base')
        for narc in(55,56):
            row,row_receipt=read(table+4*narc,4);path_address=struct.unpack('<I',row)[0];path_raw,path_receipt=read(path_address,8)
            need(path_raw==('a/0/5/'+str(narc-50)).encode()+b'\0','actual native trainer NARC path')
            path=path_raw[:-1].decode('ascii');members,receipt=bag.raw_archive(raw,path)
            need((receipt['file_id'],receipt['archive_bytes'],receipt['archive_sha256'])==ARCHIVES[narc]and len(members)==738,'exact trainer source archive')
            member=bytes(members[31]);physical=receipt['member_rom_offsets'][31]
            need(bytes(raw[physical:physical+len(member)])==member,'independent direct trainer31 member read')
            routes[str(narc)]=dict(native_pool=pool_receipt,native_row=row_receipt,native_path=path_receipt,path=path,
                file_id=receipt['file_id'],archive_bytes=receipt['archive_bytes'],archive_sha256=receipt['archive_sha256'],members=len(members),
                member=31,member_rom_offset=physical,member_bytes=len(member),member_sha256=sha(member))
            payloads[narc]=member
    layout=record_layout(payloads[55],payloads[56]);need((layout['first_level'],layout['first_species'],layout['first_item'],layout['first_move'])==(27,355,0,310),'first type3 move310 input')
    return dict(routes=routes,layout=layout,qualified_Bag_reader_sha256=BAG_SHA),{'trainer_header':payloads[55],'trainer_record':payloads[56]}


def thumb_code(parts):
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
    code=C.thumb_code(parts)
    for name,(a,n,count,digest)in NEW_THUMB.items():
        b=parts[name];need(type(b)is bytes and len(b)==n and sha(b)==digest,'exact prefix/veneer code '+name)
        instructions=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(b,a))
        need(len(instructions)==count and sum(i.size for i in instructions)==n,'complete first-slot code starts '+name)
        for i in instructions:need(i.address not in code,'disjoint first-slot Thumb starts');code[i.address]=bytes(i.bytes)
    need(len(code)==436 and sum(len(b)for b in code.values())==958 and GATE[0]not in code,'436starts/958bytes with branch gate excluded')
    return code


def prepare(rom,it_rom=None):
    parent,parts=C.prepare(rom,it_rom);extra,new=read_new(rom,R.EN);records,record_parts=read_records(rom)
    if it_rom:
        it,other=read_new(it_rom,R.IT);it_records,it_parts=read_records(it_rom)
        need(other==new and it_parts==record_parts and it_records==records,'fresh Italian prefix/record identity');extra['Italian_readback']=it
    for name in('wrapper_pool','lcg_pool'):
        need(new.pop(name)==parts[name],'qualified reader retained cipher literal agreement '+name)
    combined=C.merge_unique(parts,new,record_parts);code=thumb_code(combined)
    need(int.from_bytes(combined['mon_target'],'little')==0x20714f1 and combined['mon_veneer']==bytes.fromhex('004b1847'),'actual veneer target and instructions')
    need(combined['prefix_gate']==bytes.fromhex('f2db'),'actual excluded first-loop BLT gate word')
    gate_target=GATE[0]+4+2*int.from_bytes(combined['prefix_gate'][:1],'little',signed=True)
    need(gate_target==0x2073a28,'static first-loop backward branch target')
    regions={n:item[:2]for n,item in{**THUMB,**DATA}.items()};regions['excluded_gate']=GATE[:2]
    regions.update({'sdk_'+n:item[:2]for n,item in C.F87.SDK.COMPONENTS.items()});regions['division']=C.MX.DIV[:2];R.require_disjoint(regions)
    return dict(schema='native-trainer-first-move-prefix-resources-v1',parent=parent,new_components=extra,trainer=records,
        Thumb_starts=len(code),Thumb_bytes=958,gate=dict(ram=GATE[0],bytes=2,sha256=GATE[2],branch_target=gate_target,executed=False),
        source_sha256={str(p.relative_to(SOURCE)):sha(p.read_bytes())for p in(HERE,Path(C.__file__),BAG_TOOL)},
        original_C_codegen_reconstructed=False,CPU_executed=False,compiler_invoked=False,
        scope='Current prefix/veneer/record readback; synthetic prefix entry required, no lossless historical context or whole trainer activation'),combined


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('rom','json'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--it-rom',type=Path);a=p.parse_args()
    try:
        out=a.json.resolve();need(out!=SOURCE and SOURCE not in out.parents and not out.exists()and not out.is_symlink(),'fresh private first-move resource output')
        receipt,_=prepare(a.rom,a.it_rom)
        with out.open('x')as f:json.dump(receipt,f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Type3 first-slot prefix/veneer/record108 authenticated; excluded branch gate, no CPU/compiler')


if __name__=='__main__':main()
