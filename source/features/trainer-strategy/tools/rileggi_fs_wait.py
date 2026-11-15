#!/usr/bin/env python3
"""Independent ELF/ROM readback of Wait and two IRQ leaves, no CPU/compiler.

Legacy compression/autoload uses decoded sections; direct offsets are stated
only when independently resolved for V4/current. Reports remain private.
"""
from pathlib import Path
import argparse,gc,importlib.util,json,mmap,struct


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


L=load('wait_lineage_read_parent',Path(__file__).with_name('rileggi_fs_read.py'))
C=load('wait_lineage_builder',Path(__file__).with_name('compila_fs_wait.py'))
P,need,sha=L.P,L.need,L.sha
need(sha(Path(L.__file__).read_bytes())=='f7991b5bf8b38df910470c503f26ff4ccb994b6bcc5f90ebf7a88867f161fd71','qualified independent ELF parent drift')
object_text=L.object_text


def analyze(paths, language, recipe_dir=None):
    rows=[]; recovered={role:object_text(recipe_dir/('fs-wait-'+role+'.o'),n,digest)
        for role,(address,n,digest) in C.BODIES.items()} if recipe_dir else {}
    for role in ('retail','base11','v4','r4'):
        model=P.G.S.SHARED.read_current(paths[role],language) if role=='r4' else P.G.S.SHARED.read_image(paths[role],language,role)
        with paths[role].open('rb') as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ) as raw:
            components={}
            for name,(address,n,digest) in C.BODIES.items():
                body=P.G.piece(model['segments'],address,n); physical=None
                if role in ('v4','r4'):
                    view=P.G.S.SHARED.gifts_audit.Arm9View(raw)
                    need(view.read(address,n)==body,'Wait/IRQ raw/decoded section agreement')
                    physical=hex(view.offset(address,n))
                calls=[];literal=None
                if name=='core':
                    for offset in (0x0C,0x54,0x74,0x94,0xA4):
                        word=struct.unpack_from('<I',body,offset)[0];need(word>>24==0xEB,'Wait ARM BL encoding')
                        delta=word&0xFFFFFF
                        if delta&0x800000:delta-=0x1000000
                        calls.append(dict(site=hex(address+offset),target=hex(address+offset+8+4*delta)))
                else:literal=None
                components[name]=dict(ram=hex(address),rom_offset=physical,bytes=n,sha256=sha(body),
                    equal_to_current=sha(body)==digest,equal_to_recipe=None if not recovered else body==recovered[name],
                    ARM_calls=calls,literal_target=literal)
            rows.append(dict(role=role,input=model['record'],components=components))
        del model;gc.collect();L.H.H.R.W.require_host_budget()
    need(all(c['equal_to_current'] for c in rows[-1]['components'].values()),'current Wait/IRQ bodies differ')
    return dict(schema='native-fs-wait-lineage-v1',language=language,images=rows,cpu_executed=False,compiler_invoked=False,
        tool_sha256=sha(Path(__file__).read_bytes()),recipe_objects={} if not recipe_dir else {
            role:sha((recipe_dir/('fs-wait-'+role+'.o')).read_bytes()) for role in C.BODIES},
        limits=['Two finite candidate components only; differing revisions remain unattributed',
            'Legacy decoded addresses do not infer compressed/autoload physical offsets',
            'No original compiler provenance or historical/natural SDK activation'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('retail','base','v4','rom','json'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--language',choices=('EN','IT'),required=True);p.add_argument('--recipe-dir',type=Path)
    a=p.parse_args()
    try:
        r=analyze(dict(retail=a.retail,base11=a.base,v4=a.v4,r4=a.rom),a.language,a.recipe_dir);L.H.save(a.json,r)
    except ValueError as e:p.exit(2,str(e)+'\n')
    print(a.language,'Wait and IRQ leaves lineage verified without CPU')


if __name__=='__main__':main()
