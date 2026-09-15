"""Compile only project-owned ARM code for the expanded Bag."""
from pathlib import Path
import hashlib,json,subprocess,sys,tempfile
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'source/features/caramelle/tools'))
from carica_text import load_text
BASE=0x023DBF00
SIZE=0x2C00
ENTRIES=('get','init','new','copy','registered1','registered2','register','unregister','pocket','not_empty','view','slot','move','load','save','original_load','original_save')
def compila(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    flags=['--target=armv5te-none-eabi','-mcpu=arm946e-s','-mthumb','-Oz','-ffreestanding','-fno-builtin','-fno-stack-protector','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-fno-jump-tables','-Wall','-Wextra','-Werror']
    names=tuple('sgp_cap_'+x for x in ENTRIES)
    with tempfile.TemporaryDirectory() as td:
        obj=Path(td)/'runtime.o'
        subprocess.run(['clang',*flags,'-c',str(HERE.parent/'sorgenti/runtime.c'),'-o',str(obj)],check=True)
        blob,symbols=load_text(obj.read_bytes(),BASE,names)
    if len(blob)>0x1800:raise ValueError('code overlaps inventory state')
    (out/'blob.bin').write_bytes(blob)
    manifest={'schema':1,'base':hex(BASE),'blocco_byte':SIZE,'stato':hex(BASE+0x1800),'blob':{'byte':len(blob),'sha256':hashlib.sha256(blob).hexdigest()},'simboli':{n:hex(symbols[n]) for n in names},'capacita':[252,42,30,102,66,12,30,60],'settori':[48,112],'formato_estensione':1,'opzioni_compilazione':flags,'compilatore':subprocess.check_output(['clang','--version'],text=True).splitlines()[0]}
    (out/'manifesto.json').write_text(json.dumps(manifest,indent=2)+'\n')
    sources=[*sorted((HERE.parent/'sorgenti').glob('*.[ch]')),Path(__file__).resolve()]
    origin={'metodo':'compilazione da sorgenti; nessuna estrazione ROM','sorgenti':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
    (out/'origine.json').write_text(json.dumps(origin,indent=2)+'\n')
    (out/'SHA256SUMS').write_text(''.join(hashlib.sha256((out/n).read_bytes()).hexdigest()+'  '+n+'\n' for n in ('blob.bin','manifesto.json','origine.json')))
    print('capacita-borsa:',len(blob),'bytes compiled')
    return manifest
if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('--uscita',required=True);compila(a.parse_args().uscita)
