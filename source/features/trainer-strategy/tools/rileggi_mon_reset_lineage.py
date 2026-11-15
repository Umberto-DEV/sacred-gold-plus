#!/usr/bin/env python3
"""Locate the new Reset56 in exact retail/base1.1/V4/current images.

Only the newly added caller is reacquired. Actual four BL targets are decoded
from it; preceding component-lineage proofs retain their separate coverage.
"""
from pathlib import Path
import argparse
import importlib.util
import json


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve();SOURCE=HERE.parents[3]
L=load(HERE.with_name('rileggi_mon_reset.py'),'Reset_lineage_current')
P=load(HERE.with_name('rileggi_mon_ppup_lineage.py'),'Reset_retained56_locator')
OLD=P.OLD
R,need,sha=L.R,L.need,L.sha


def inspect(path,identity,current):
    import ndspy.code,ndspy.codeCompression
    path=Path(path);need(path.stat().st_size==identity['bytes']and R.file_sha(path)==identity['sha256'],'exact historical Reset image')
    with path.open('rb')as f:
        h=f.read(512);off,base,size=(R.u32(h,x)for x in(0x20,0x28,0x2c))
        need(0<size<=4*1024**2 and off+size<=path.stat().st_size,'bounded Reset ARM9 owner');f.seek(off);stored=f.read(size)
    expanded=ndspy.codeCompression.decompress(stored);need(len(expanded)<=4*1024**2,'bounded expanded Reset owner')
    compressed=stored!=expanded;sections=ndspy.code.MainCodeFile(stored,base).sections
    metadata=dict(ROM_sha256=identity['sha256'],ROM_bytes=identity['bytes'],game_code=h[12:16].decode('ascii',errors='replace'),revision=h[30],
        ARM9_stored_rom_range=[off,off+size],ARM9_stored_sha256=sha(stored),ARM9_expanded_sha256=sha(expanded),compression='BLZ'if compressed else'plain')
    try:
        address=P.locate(sections,current);blob,owner=OLD.piece(sections,address,56)
        physical=OLD.physical_position(owner,base,off,size,address,56,compressed)
        if physical is not None:
            with path.open('rb')as f:f.seek(physical);direct=f.read(56)
            need(direct==blob,'independent Reset56 physical read')
        targets=[OLD.bl_target(address+i,blob[i:i+4])for i in(10,26,34,48)]
        return dict(**metadata,status='complete bounded readback',located_Reset=address,actual_BL_targets=targets,
            component=dict(ram=address,bytes=56,sha256=sha(blob),physical_plaintext_offset=physical,decoded_owner_ram=owner.ramAddress,
                decoded_owner_bytes=len(owner.data),equal_to_current=blob==current,kind='code'),
            all_components_equal=blob==current)
    except ValueError as e:return dict(**metadata,status='unattributed layout',reason=str(e),component=None,all_components_equal=False)


def analyze(paths,language):
    ids=OLD.identities(language);identity=R.EN if language=='EN'else R.IT
    _,parts=L.read_new(paths['r4'],identity);current=parts['reset']
    rows=[dict(role=role,**inspect(paths[role],ids[role],current))for role in('retail','base11','v4','r4')]
    return dict(schema='native-Mon-Reset56-lineage-v1',language=language,images=rows,
        all_images_attributed=all(r['status']=='complete bounded readback'for r in rows),
        source_sha256={str(p.relative_to(SOURCE)):sha(p.read_bytes())for p in(HERE,Path(L.__file__),Path(P.__file__),Path(OLD.__file__))},
        manifest_sha256={n:sha((SOURCE/n).read_bytes())for n in OLD.OLD.MANIFESTS},CPU_executed=False,compiler_invoked=False,
        scope='New56 caller bytes and encoded four BL targets only; earlier callee witnesses remain separate; no whole-ROM or activation equivalence',
        mapping_limit='BLZ/nonlinear owners retain null physical plaintext offsets; require attribution and component equality')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('retail','base','v4','rom','json'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--language',choices=('EN','IT'),required=True);a=p.parse_args()
    try:
        out=a.json.resolve();need(SOURCE not in out.parents and out!=SOURCE and not out.exists()and not out.is_symlink(),'fresh private Reset lineage output')
        result=analyze(dict(retail=a.retail,base11=a.base,v4=a.v4,r4=a.rom),a.language)
        with out.open('x')as f:json.dump(result,f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print(a.language+' newReset56B lineage recorded; attributed='+str(result['all_images_attributed'])+'; no CPU/compiler')


if __name__=='__main__':main()
