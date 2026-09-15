"""252-slot main Bag and full six-cell pages; native save layout remains fixed."""
import hashlib,json,struct,tempfile
from pathlib import Path
from ..rom import Arm9,Rom,Rifiuto,esigi
from ..blz import blz_comprimi,blz_decomprimi
BASE=0x023DBF00
SIZE=0x2C00
HOOKS={0x02078188:'new',0x020781A0:'init',0x020781B4:'copy',
       0x020781C4:'registered1',0x020781D0:'registered2',0x020781DC:'register',
       0x02078208:'unregister',0x02078240:'pocket',0x020784C4:'not_empty',
       0x02078644:'view',0x02078724:'slot',0x0207879C:'get',
       0x02077B5C:'move',0x02027AD4:'load',0x02027C18:'save'}
ANCHORS=((0x02078180,1576,'f4f13f028cd612b621bbdaf7f52fc23f77946aad70444ec62b810834a2cb5a8e'),
         (0x02077B5C,8,'aba8ea49b9ac80cafde3049ef8251fd897ca60d1a7679c62891a5f7fbeef9e22'),
         (0x02027AD4,8,'e758f2b6edf6724389ec1f6896c9837762b2d6321ee19ad258d9b9b334213e01'),
         (0x02027C18,8,'a352395b7fffa7d8a7ffa65af5a4215d8019a3fd490c540c0609f140c6e5bf2f'))
NAME_MOVES=((0x021F9F50,1),(0x021F9FAC,1),(0x021FA00A,6),(0x021FA02A,6),
            (0x021FD746,1),(0x021FF43E,2),(0x021FF45E,2),(0x021FF47A,2),(0x021FF536,2))
def _sha(b):return hashlib.sha256(b).hexdigest()
def _entry(target,preserve_r3=False):
    if preserve_r3:return struct.pack('<6HI',0xB408,0x4B02,0x469C,0xBC08,0x4760,0x46C0,target|1)
    return struct.pack('<HHI',0x4B00,0x4718,target|1)
def _patches():
    out=[]
    def put(a,old,new):out.append({'addr':a,'pre':old,'post':new})
    for a,r in NAME_MOVES:put(a,struct.pack('<H',0x2000|(r<<8)|0x35),struct.pack('<H',0x2000|(r<<8)|0x95))
    for a in (0x021FA022,0x021FA03C):put(a,struct.pack('<H',0x2CA5),struct.pack('<H',0x2CFC))
    for a in (0x021FA004,0x022001C0):put(a,struct.pack('<I',0x6A4),struct.pack('<I',0xD40))
    put(0x021F95F4,struct.pack('<I',0x94C),struct.pack('<I',0xF38))
    old=bytes([165,40,24,101,64,12,30,50]);new=bytes([252,42,30,102,66,12,30,60])
    for a in (0x022008B0,0x022008C8):put(a,old,new)
    return out

def _carica_build(directory):
    directory=Path(directory)
    try:
        names=('blob.bin','manifesto.json','origine.json')
        esigi((directory/'SHA256SUMS').read_text()==''.join(_sha((directory/n).read_bytes())+'  '+n+'\n' for n in names),'CAPACITA: SHA256SUMS mismatch')
        root=Path(__file__).resolve().parents[3]
        paths=sorted((root/'source/features/capacita-borsa/sorgenti').glob('*.[ch]'))+[root/'source/features/capacita-borsa/tools/compila.py']
        origin=json.loads((directory/'origine.json').read_text())
        esigi(origin=={'metodo':'compilazione da sorgenti; nessuna estrazione ROM','sorgenti':{str(p.relative_to(root)):_sha(p.read_bytes()) for p in paths}},'CAPACITA: source provenance mismatch')
        man=json.loads((directory/'manifesto.json').read_text());blob=(directory/'blob.bin').read_bytes()
        esigi(man['blob']=={'byte':len(blob),'sha256':_sha(blob)},'CAPACITA: build fingerprint mismatch')
        esigi(man['schema']==1 and int(man['base'],16)==BASE and man['blocco_byte']==SIZE and 0<len(blob)<=0x1800,'CAPACITA: invalid build allocation')
        esigi(int(man['stato'],16)==BASE+0x1800 and man['capacita']==[252,42,30,102,66,12,30,60] and man['settori']==[48,112] and man['formato_estensione']==1,'CAPACITA: build contract mismatch')
        for name in set(HOOKS.values()):
            v=int(man['simboli']['sgp_cap_'+name],16)
            esigi(v&1 and BASE <= (v&~1) < BASE+len(blob),'CAPACITA: invalid symbol '+name)
        return man,blob
    except (OSError,ValueError,TypeError,KeyError) as exc:
        raise Rifiuto('CAPACITA: malformed build: '+str(exc)) from exc

def applica(rom,build_dir,manifest_path=None):
    rom=bytes(rom);directory=Path(build_dir)
    man,blob=_carica_build(directory)
    if manifest_path is not None:
        blocks=json.loads(Path(manifest_path).read_text())['blocchi']
        own=[b for b in blocks if b['nome']=='sgp.capacita_borsa']
        esigi(len(own)==1 and int(own[0]['base'],16)==BASE and own[0]['bytes']==SIZE,'CAPACITA: missing reserve allocation')
        for b in blocks:
            if b['nome']=='sgp.capacita_borsa':continue
            a=int(b['base'],16);esigi(a>=BASE+SIZE or a+b['bytes']<=BASE,'CAPACITA: overlapping '+b['nome'])
    with tempfile.TemporaryDirectory(prefix='sgp-capacity-') as td:
        path=Path(td)/'in.nds';path.write_bytes(rom);arm=Arm9(path)
        for a,n,h in ANCHORS:esigi(_sha(arm.leggi(a,n))==h,'CAPACITA: native preimage changed at %#x'%a)
        esigi(arm.u32(0x02027B5C)==0x232B4,'CAPACITA: save structure offset changed')
        esigi(arm.leggi(BASE,SIZE)==bytes(SIZE),'CAPACITA: reserve already occupied')
        arm.scrivi(BASE,blob+bytes(SIZE-len(blob)))
        for a,n in HOOKS.items():arm.scrivi(a,_entry(int(man['simboli']['sgp_cap_'+n],16),n in ('pocket','move')))
        interim=bytes(arm.raw)
    patches=_patches()
    container=Rom(interim);info,raw,image=container.immagine_overlay(15)
    edited=bytearray(image)
    for patch in patches:
        off=patch['addr']-info['ram']
        esigi(edited[off:off+len(patch['pre'])]==patch['pre'],'CAPACITA: Bag UI preimage changed at %#x'%patch['addr'])
        edited[off:off+len(patch['post'])]=patch['post']
    # Here the optimal target-size stream crosses its source while decoding.
    # The greedy stream is the ORIGINAL size and passes the in-place decoder.
    encoded=blz_comprimi(edited)
    esigi(len(encoded)==len(raw),'CAPACITA: greedy Bag overlay must retain exact original size')
    esigi(blz_decomprimi(encoded)==edited,'CAPACITA: Bag overlay in-place decompression failed')
    fat=container.voce_fat(info['file_id']);after=bytearray(interim)
    after[fat['inizio']:fat['fine']]=encoded
    after=bytes(after)
    receipt={'overlay':15,'codec':'greedy-exact-size','bytes':len(encoded),
             'immagine_sha256_prima':_sha(image),'immagine_sha256_dopo':_sha(edited),
             'fat_y9_invariati':True}
    esigi(len(after)==len(rom),'CAPACITA: ROM size changed')
    return after,{'strumento':'sgp12.blocchi.capacita_borsa','esito':'applicato','sha256_ingresso':_sha(rom),'sha256_uscita':_sha(after),'blocco_sha256':_sha(blob+bytes(SIZE-len(blob))),'overlay_patch':receipt}

def rileggi(prima,dopo,build_dir):
    import importlib.util
    path=Path(__file__).resolve().parents[2]/'features/capacita-borsa/tools/rileggi.py'
    spec=importlib.util.spec_from_file_location('_capacity_reader',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.rileggi(prima,dopo,build_dir)
