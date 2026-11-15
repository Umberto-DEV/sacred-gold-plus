#!/usr/bin/env python3
"""Read the108-byte SDK Seek wrapper in exact retail/base/V4/r4 images, no CPU.

Uses an independently parsed recovered ELF section and authenticated ROM inputs.
Outputs only hashes, offsets and decoded branch targets; keep reports private.
"""
from pathlib import Path
import argparse, gc, json, mmap, struct, types
import importlib.util


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


H=load('seek_lineage_caller',Path(__file__).with_name('attribuisci_fs_seek.py'))
L=load('seek_lineage_elf_parent',Path(__file__).with_name('rileggi_fs_init.py'))
P,need,sha=H.P,H.need,H.sha
ELF_PARENT_SHA='b975e73b5baac4ca11be70a2a9b2138aeb9aacef936c5789d9f1011e0c62d5ec'
scope={**vars(H.H.H.H.H.O.H.X.A),'PINS':{'fs_init_lineage':ELF_PARENT_SHA}}
rewrite=types.FunctionType(H.H.H.H.H.O.H.X.A.rewrite.__code__,scope)
object_text,ELF_RECIPE=rewrite(L,'object_text',[
    ('len(result) == 40','len(result) == 108',1),('H.INIT_SHA','SEEK_SHA',1),
    ('ELF recovered Init body differs','ELF recovered Seek body differs',1)],
    dict(__source_kind__='fs_init_lineage',SEEK_SHA=H.SEEK_SHA))


def analyze(paths,language,recipe_object=None):
    rows=[];recovered=object_text(recipe_object)if recipe_object else None
    for role in ('retail','base11','v4','r4'):
        model=P.G.S.SHARED.read_current(paths[role],language)if role=='r4'else P.G.S.SHARED.read_image(paths[role],language,role)
        with paths[role].open('rb')as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)as raw:
            body=P.G.piece(model['segments'],H.ENTRY,108);physical=None;calls=[]
            if role in ('v4','r4'):
                view=P.G.S.SHARED.gifts_audit.Arm9View(raw);need(view.read(H.ENTRY,108)==body,'Seek raw/decoded agreement')
                physical=hex(view.offset(H.ENTRY,108))
            for offset in ():
                word=struct.unpack_from('<I',body,offset)[0];need(word>>24==0xEB,'Seek candidate ARM BL encoding')
                delta=word&0xFFFFFF
                if delta&0x800000:delta-=0x1000000
                calls.append(dict(site=hex(H.ENTRY+offset),target=hex(H.ENTRY+offset+8+4*delta)))
            rows.append(dict(role=role,input=model['record'],ram=hex(H.ENTRY),bytes=108,sha256=sha(body),
                rom_offset=physical,equal_to_current=sha(body)==H.SEEK_SHA,
                equal_to_recipe=None if recovered is None else body==recovered,ARM_calls=calls))
        del model;gc.collect();H.R.W.require_host_budget()
    need(rows[-1]['equal_to_current'],'current Seek identity differs')
    return dict(schema='native-fs-seek-lineage-v1',language=language,images=rows,cpu_executed=False,
        compiler_invoked=False,tool_sha256=sha(Path(__file__).read_bytes()),verifier_sha256=sha(Path(H.__file__).read_bytes()),
        independent_ELF_parent_sha256=ELF_PARENT_SHA,ELF_recipe=ELF_RECIPE,
        recipe_object_sha256=None if recipe_object is None else sha(recipe_object.read_bytes()),
        limits=['Only this108-byte wrapper; differing candidates remain unattributed',
                'Legacy compressed/autoload physical offsets not inferred from decoded addresses',
                'No original compiler provenance, historical activation or lower native SDK execution'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('retail','base','v4','rom','json'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--language',choices=('EN','IT'),required=True)
    parser.add_argument('--recipe-object',type=Path)
    args=parser.parse_args()
    try:
        need(not args.json.exists()and not args.json.is_symlink()and P.SOURCE not in args.json.resolve().parents,
             'fresh private output outside source required')
        result=analyze(dict(retail=args.retail,base11=args.base,v4=args.v4,r4=args.rom),args.language,args.recipe_object)
        payload=(json.dumps(result,indent=2)+'\n').encode();need(len(payload)<=1024**2,'Seek lineage report budget')
        args.json.parent.mkdir(parents=True,exist_ok=True)
        with args.json.open('xb')as f:f.write(payload)
    except ValueError as error:parser.exit(2,str(error)+'\n')
    print(args.language,'Seek wrapper lineage read without CPU')


if __name__=='__main__':main()
