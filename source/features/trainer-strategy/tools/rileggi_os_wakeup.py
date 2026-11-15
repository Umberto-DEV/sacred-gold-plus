#!/usr/bin/env python3
"""Read recovered Wakeup ELF and retail/base/V4/current bodies without a guest CPU."""
from pathlib import Path
import argparse,gc,importlib.util,mmap


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


L=load('os_wakeup_qualified_elf_reader',Path(__file__).with_name('rileggi_fs_read.py'))
C=load('os_wakeup_recovered_builder',Path(__file__).with_name('compila_os_wakeup.py'))
P,need,sha=L.P,L.need,L.sha
need(sha(Path(L.__file__).read_bytes())=='f7991b5bf8b38df910470c503f26ff4ccb994b6bcc5f90ebf7a88867f161fd71','Wakeup independent ELF reader drift')
object_text=L.object_text


def analyze(paths,language,recipe_dir=None):
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
    address,n,digest=C.BODIES['command'];obj=None if recipe_dir is None else recipe_dir/'os-wakeup-command.o'
    recovered=None if obj is None else object_text(obj,n,digest);rows=[]
    for role in('retail','base11','v4','r4'):
        model=P.G.S.SHARED.read_current(paths[role],language)if role=='r4'else P.G.S.SHARED.read_image(paths[role],language,role)
        with paths[role].open('rb')as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ)as raw:
            body=P.G.piece(model['segments'],address,n);physical=None
            if role in('v4','r4'):
                view=P.G.S.SHARED.gifts_audit.Arm9View(raw);need(view.read(address,n)==body,'Wakeup physical/decoded body agreement')
                physical=hex(view.offset(address,n))
            code=list(Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(body,address))
            need(len(code)==26 and sum(i.size for i in code)==n,'Wakeup complete candidate ARM extent')
            calls=[dict(pc=hex(i.address),mnemonic=i.mnemonic,target=i.op_str)for i in code if i.mnemonic in('bl','blx')]
            rows.append(dict(role=role,input=model['record'],component=dict(ram=hex(address),rom_offset=physical,bytes=n,
                sha256=sha(body),equal_to_current=sha(body)==digest,equal_to_recipe=None if recovered is None else body==recovered,
                ARM_starts=len(code),literal_pool_bytes=0,calls=calls)))
        del model;gc.collect();L.H.H.R.W.require_host_budget()
    need(rows[-1]['component']['equal_to_current'],'Wakeup current body mismatch')
    return dict(schema='native-os-wakeup-lineage-v1',language=language,images=rows,cpu_executed=False,compiler_invoked=False,
        tool_sha256=sha(Path(__file__).read_bytes()),recipe_object_sha256=None if obj is None else sha(obj.read_bytes()),
        limits=['One candidate Wakeup body; a differing revision is not automatically attributed',
                'Legacy decoded addresses do not invent direct compressed/autoload physical offsets',
                'No original compiler, FSArchive initialization or historical/natural activation established'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('retail','base','v4','rom','json'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--language',choices=('EN','IT'),required=True);p.add_argument('--recipe-dir',type=Path);a=p.parse_args()
    try:
        result=analyze(dict(retail=a.retail,base11=a.base,v4=a.v4,r4=a.rom),a.language,a.recipe_dir);L.H.save(a.json,result)
    except ValueError as error:p.exit(2,str(error)+'\n')
    print(a.language,'Wakeup104 lineage verified without guest CPU')


if __name__=='__main__':main()
