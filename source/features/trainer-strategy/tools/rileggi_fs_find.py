#!/usr/bin/env python3
"""Independent FindPath ELF and four-stage ROM lineage readback, without CPU."""
from pathlib import Path
import argparse,gc,importlib.util,mmap,struct


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


L=load('find_lineage_qualified_reader',Path(__file__).with_name('rileggi_fs_read.py'))
C=load('find_lineage_builder',Path(__file__).with_name('compila_fs_find.py'))
P,need,sha=L.P,L.need,L.sha
need(sha(Path(L.__file__).read_bytes())=='f7991b5bf8b38df910470c503f26ff4ccb994b6bcc5f90ebf7a88867f161fd71',
     'Find independent ELF reader drift')
object_text=L.object_text


def analyze(paths,language,recipe_dir=None):
    address,n,digest=C.BODIES['path'];recovered=None if recipe_dir is None else object_text(recipe_dir/'fs-find-path.o',n,digest)
    rows=[];bodies=[]
    for role in('retail','base11','v4','r4'):
        model=P.G.S.SHARED.read_current(paths[role],language)if role=='r4'else P.G.S.SHARED.read_image(paths[role],language,role)
        with paths[role].open('rb')as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ)as raw:
            body=P.G.piece(model['segments'],address,n);bodies.append(body);physical=None
            load_address=int(model['record']['header']['arm9_ram'],16)
            params=struct.unpack('<9I',P.G.piece(model['segments'],load_address+0xBA0,36))
            pointer=struct.unpack_from('<I',body,320)[0]
            need(params[3]<=pointer and pointer+12<=params[4],'Find literal points within declared static BSS')
            if role in('v4','r4'):
                view=P.G.S.SHARED.gifts_audit.Arm9View(raw)
                need(view.read(address,n)==body,'Find independent physical/decoded body agreement');physical=hex(view.offset(address,n))
            calls=[]
            for offset in(0x84,0x134):
                word=struct.unpack_from('<I',body,offset)[0];need(word>>24==0xEB,'Find signed ARM BL opcode')
                delta=word&0xFFFFFF
                if delta&0x800000:delta-=0x1000000
                calls.append(dict(pc=hex(address+offset),target=hex(address+offset+8+4*delta)))
            rows.append(dict(role=role,input=model['record'],component=dict(ram=hex(address),bytes=n,instruction_bytes=320,
                rom_offset=physical,sha256=sha(body),instruction_sha256=sha(body[:320]),equal_to_current=sha(body)==digest,
                equal_to_recipe=None if recovered is None else body==recovered,calls=calls,
                literal=dict(ram=hex(address+320),value=hex(pointer),kind='static BSS',bss_start=hex(params[3]),bss_end=hex(params[4])))))
        del model;gc.collect();L.H.H.R.W.require_host_budget()
    for row,body in zip(rows,bodies):
        component=row['component'];delta=[i for i,(a,b)in enumerate(zip(body,bodies[-1]))if a!=b]
        component.update(equal_instructions_to_current=body[:320]==bodies[-1][:320],
            differing_byte_offsets=delta,delta_scope='none'if not delta else'literal only'if all(i>=320 for i in delta)else'instruction or extent difference')
    need(rows[-1]['component']['equal_to_current'],'Find current body mismatch')
    return dict(schema='native-fs-find-lineage-v1',language=language,images=rows,cpu_executed=False,compiler_invoked=False,
        tool_sha256=sha(Path(__file__).read_bytes()),recipe_object_sha256=None if recipe_dir is None else sha((recipe_dir/'fs-find-path.o').read_bytes()),
        limits=['One finite component; differing revisions retain their own unassigned source links',
                'Literal names BSS; it does not embed a current directory or archive object',
                'Legacy physical offsets are not inferred from decoded addresses/compressed sections',
                'No original compiler history or natural/historical SDK activation established'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('retail','base','v4','rom','json'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--language',choices=('EN','IT'),required=True);p.add_argument('--recipe-dir',type=Path);a=p.parse_args()
    try:L.H.save(a.json,analyze(dict(retail=a.retail,base11=a.base,v4=a.v4,r4=a.rom),a.language,a.recipe_dir))
    except ValueError as error:p.exit(2,str(error)+'\n')
    print(a.language,'FindPath source/ELF/ROM lineage readback verified without CPU')


if __name__=='__main__':main()
