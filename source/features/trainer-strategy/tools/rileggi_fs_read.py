#!/usr/bin/env python3
"""Independently read recovered Read ELF sections and retail/base/V4/r4 ROMs, no CPU.

ELF section arithmetic derives from the qualified Init reader b975e73b...62d5ec;
no relocation loader is used by this readback. Local reports may contain metadata.
"""
from pathlib import Path
import argparse, gc, importlib.util, json, mmap, struct

s=importlib.util.spec_from_file_location('read_lineage_parent',Path(__file__).with_name('attribuisci_fs_read.py'))
H=importlib.util.module_from_spec(s);s.loader.exec_module(H)
P,need,sha=H.H.P,H.need,H.sha


def object_text(path, length, digest):
    raw = path.read_bytes()
    need(raw[:7] == b'\x7fELF\x01\x01\x01' and len(raw) >= 52, 'ELF32 little endian required')
    header = struct.unpack_from('<HHIIIIIHHHHHH', raw, 16)
    need(header[:2] == (1, 40) and header[10] == 40, 'relocatable ARM ELF required')
    offset, count, strings = header[5], header[11], header[12]
    need(offset >= 52 and count > 0 and strings < count and offset + count * 40 <= len(raw), 'ELF section bounds')
    sections = [struct.unpack_from('<10I', raw, offset + 40 * i) for i in range(count)]
    def content(s):
        need(s[4] + s[5] <= len(raw), 'ELF content bounds')
        return raw[s[4]:s[4]+s[5]]
    names = content(sections[strings]); selected = []
    for i, section in enumerate(sections):
        need(section[0] < len(names), 'ELF section name bounds')
        end = names.find(b'\0', section[0]); need(end >= 0, 'ELF section name terminator')
        if names[section[0]:end] == b'.text': selected.append((i, section))
    need(len(selected) == 1, 'single ELF text required')
    index, section = selected[0]
    need(not any(s[1] in (4, 9) and s[7] == index and s[5] for s in sections), 'no text relocations allowed')
    result = content(section)
    need(len(result) == length and sha(result) == digest, 'ELF recovered Read body differs')
    return result



def analyze(paths, language, recipe_dir=None):
    rows=[]; recovered={role:object_text(recipe_dir/('fs-read-'+role+'.o'),n,digest)
        for role,(address,n,digest) in H.C.BODIES.items()} if recipe_dir else {}
    for role in ('retail','base11','v4','r4'):
        model=P.G.S.SHARED.read_current(paths[role],language) if role=='r4' else P.G.S.SHARED.read_image(paths[role],language,role)
        with paths[role].open('rb') as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ) as raw:
            components={}
            for name,(address,n,digest) in H.C.BODIES.items():
                body=P.G.piece(model['segments'],address,n); physical=None
                if role in ('v4','r4'):
                    view=P.G.S.SHARED.gifts_audit.Arm9View(raw)
                    need(view.read(address,n)==body,'Read raw/decoded section agreement')
                    physical=hex(view.offset(address,n))
                calls=[];literal=None
                if name=='core':
                    for offset in (0x50,0x60):
                        word=struct.unpack_from('<I',body,offset)[0];need(word>>24==0xEB,'Read ARM BL encoding')
                        delta=word&0xFFFFFF
                        if delta&0x800000:delta-=0x1000000
                        calls.append(dict(site=hex(address+offset),target=hex(address+offset+8+4*delta)))
                else:literal=hex(struct.unpack_from('<I',body,12)[0])
                components[name]=dict(ram=hex(address),rom_offset=physical,bytes=n,sha256=sha(body),
                    equal_to_current=sha(body)==digest,equal_to_recipe=None if not recovered else body==recovered[name],
                    ARM_calls=calls,literal_target=literal)
            rows.append(dict(role=role,input=model['record'],components=components))
        del model;gc.collect();H.H.R.W.require_host_budget()
    need(all(c['equal_to_current'] for c in rows[-1]['components'].values()),'current Read bodies differ')
    return dict(schema='native-fs-read-lineage-v1',language=language,images=rows,cpu_executed=False,compiler_invoked=False,
        tool_sha256=sha(Path(__file__).read_bytes()),recipe_objects={} if not recipe_dir else {
            role:sha((recipe_dir/('fs-read-'+role+'.o')).read_bytes()) for role in H.C.BODIES},
        limits=['Two finite candidate components only; differing revisions remain unattributed',
            'Legacy decoded addresses do not infer compressed/autoload physical offsets',
            'No original compiler provenance or historical/natural SDK activation'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('retail','base','v4','rom','json'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--language',choices=('EN','IT'),required=True);p.add_argument('--recipe-dir',type=Path)
    a=p.parse_args()
    try:
        r=analyze(dict(retail=a.retail,base11=a.base,v4=a.v4,r4=a.rom),a.language,a.recipe_dir);H.save(a.json,r)
    except ValueError as e:p.exit(2,str(e)+'\n')
    print(a.language,'Read core and veneer lineage verified without CPU')


if __name__=='__main__':main()
