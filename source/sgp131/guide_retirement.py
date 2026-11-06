"""Cold-image Guide retirement closure tied to the final installer readback.

Invoke ONLY from ui_verify after its complete complement check and its independent
recompilation. This does not turn a caller receipt/row into installation authority.
Native ambiguous candidates are immutable V4 context, not blanket exceptions.
"""
import hashlib
from pathlib import Path
import struct
import tempfile

OLD_BASE, OLD_BYTES = 0x023D4000, 8192
OLD_SHA = '2f19c042588a613ab26cca40609909a4b7620d3b9fdfed412599dcad5813556e'
# Exact old source-pinned installer roots, independently recompiled callbacks.
ROOTS = ((None,0x0203BFE4,'guide_task_input','fieldbook_task_input','branch'),
         (27,0x0225A0C6,'guide_field_create','fieldbook_create','branch'),
         (27,0x0225A40E,'guide_touch_input','fieldbook_touch','branch'),
         (27,0x0225A856,'guide_touch_input','fieldbook_touch','branch'),
         (27,0x0225A860,'guide_dpad','fieldbook_dpad','branch'),
         (27,0x0225A184,'guide_field_frame','fieldbook_frame','pointer'))
OLD_FLAGS = ['--target=armv5te-none-eabi','-mcpu=arm946e-s','-mthumb','-Oz',
             '-ffreestanding','-fno-builtin','-fno-stack-protector','-fno-unwind-tables',
             '-fno-asynchronous-unwind-tables','-fno-jump-tables','-Wall','-Werror']


def _need(ok, message):
    if not ok:raise ValueError('Guide retirement: '+message)


def _sha(raw):return hashlib.sha256(raw).hexdigest()


def compile_old(work_dir):
    from sgp131 import ui_compile as c
    # Uses the exact original compiler flags and strict ELF loader. All source
    # dependencies already in the independently checked UI source freeze.
    c.check_sources()
    with tempfile.TemporaryDirectory(prefix='guide-retirement-',dir=work_dir) as tmp:
        tmp=Path(tmp);compiler,toolchain=c._toolchain(tmp)
        obj=tmp/'guide.o'
        c._run([compiler,*OLD_FLAGS,'-c',str(c.SOURCE/'features/field-guide/sorgenti/guide.c'),
                '-Xclang','-fno-temp-file','-o',str(obj)],tmp,{'guide.o'})
        loader=c.module(c.SOURCE/'features/options/tools/carica_text.py','guide_retirement_loader')
        blob,symbols=loader.load_text(obj.read_bytes(),OLD_BASE,('guide_init','guide_main','guide_exit'))
        _need(len(blob)==6402 and _sha(blob+bytes(OLD_BYTES-len(blob)))==OLD_SHA,'legacy compiled image attribution')
    c.check_sources()
    return blob,symbols,toolchain


def _read(image,overlay,site,n):
    if overlay is None:return image.arm(site,n)
    blob=image.overlay(overlay);base=image.records[overlay][1]
    _need(base<=site<=site+n<=base+len(blob),'overlay root bounds')
    return blob[site-base:site-base+n]


def _branch(site,raw):
    a,b=struct.unpack('<HH',raw)
    _need(a&0xF800==0xF000 and b&0xF800==0xF800,'root branch opcode')
    d=((a&2047)<<12)|((b&2047)<<1)
    if d&0x400000:d-=0x800000
    return site+4+d


def verify(old,new,compiled,work_dir):
    """Additional closure after ui_verify exact final-image acceptance.

    Preconditions are enforced by the caller's complete protected-byte complement
    check, not supplied receipt assertions. Original native data and inactive ROM
    file copies are never treated as installed executable owners.
    """
    from sgp131 import baseline,ui_compile
    language=baseline.identify(old.raw)
    pins=ui_compile.check_sources()
    blob,symbols,toolchain=compile_old(work_dir)
    _need(old.arm(OLD_BASE,OLD_BYTES)==blob+bytes(OLD_BYTES-len(blob)),'legacy live owner')
    fb=compiled['fieldbook'];bridge=compiled['bridge']
    _need(fb['base']==OLD_BASE and 0<len(fb['data'])<=3072,'successor owner')
    # Erase all executable old suffix. The policy's preserved1344 was already
    # zero in both exact V4s and remains unchanged (not borrowed for capacity).
    _need(old.arm(0x023D5AC0,1344)==bytes(1344),'preserved tail is empty')
    _need(new.arm(OLD_BASE,OLD_BYTES)==fb['data']+bytes(OLD_BYTES-len(fb['data'])),
          'complete old image replacement; suffix/guard still contains code')
    roots=[]
    for overlay,site,before_name,after_name,kind in ROOTS:
        before=_read(old,overlay,site,4);after=_read(new,overlay,site,4)
        source=symbols[before_name];target=fb['symbols'][after_name]
        _need(target&1 and OLD_BASE<=target&~1<OLD_BASE+len(fb['data']),'resident Fieldbook export')
        if kind=='branch':
            _need(_branch(site,before)==source&~1,'legacy ingress '+before_name)
            _need(_branch(site,after)==target&~1,'successor ingress '+after_name)
        else:
            _need(struct.unpack('<I',before)[0]==source,'legacy frame callback')
            _need(struct.unpack('<I',after)[0]==target,'successor frame callback')
        roots.append(dict(overlay=overlay,site=site,before=source,after=target,kind=kind))
    native_callbacks=tuple(symbols['guide_'+n] for n in ('init','main','exit'))+(0xFFFFFFFF,)
    resident_callbacks=tuple(bridge['symbols'][n] for n in ('ui_bridge_guide_init','ui_bridge_main','ui_bridge_exit'))+(0xFFFFFFFF,)
    _need(struct.unpack('<4I',old.arm(0x023D7B10,16))==native_callbacks,'old application template')
    _need(struct.unpack('<4I',new.arm(0x023D7B10,16))==resident_callbacks,'resident callbacks/id-none template')
    for callback in resident_callbacks[:3]:
        _need(callback&1 and bridge['base']<=callback&~1<bridge['base']+len(bridge['data']),
              'Guide callback does not reside in Bridge')
    # Exact old runtime State was never persistent save data. All font handles,
    # task owners and callbacks begin zero at a cold boot; no in-process migration
    # or emulator savestate is accepted by this cartridge-level proof.
    _need(old.arm(0x023D7E00,240)==new.arm(0x023D7E00,240)==bytes(240),'cold field state/font cache ownership')
    for address,size in ((0x023D7B20,40),(0x023D7B48,16)):
        _need(new.arm(address,size)==bytes(size),'cold durable bootstrap/control')
    # Source closure: the original installer installs only the nine roots above
    # (six hook words, three callbacks). Original init/main/exit,font acquire /
    # release and RES loads are exclusively inside the replaced6402B image.
    # Successor Fieldbook publishes only its own launch/return/frame; Bridge
    # owns the template; Scene Exit retires font/resource/BG leases before unload.
    # Every one of these translation units is source pinned and recompiled by
    # ui_verify; compiled exact image checks cover internal computed addresses.
    for name in ('fieldbook','bridge','scene','physical','training','shiny'):
        _need(compiled[name]['receipt']['sources'] and all(pins.get(path)==digest for path,digest in
              compiled[name]['receipt']['sources'].items()),'unfrozen successor source '+name)
    incoming=_native_inventory(old,new,compiled)
    return dict(schema=1,incoming=incoming,language=language,input_sha256=_sha(old.raw),ui_sha256=_sha(new.raw),
                policy_parent='field-guide.code',legacy_code_bytes=len(blob),legacy_padded_sha256=OLD_SHA,
                replaced_bytes=6848,preserved_empty_bytes=1344,fieldbook_sha256=_sha(fb['data']),
                hooks=roots,old_callbacks=list(native_callbacks),resident_callbacks=list(resident_callbacks),
                old_font_exports={n:symbols[n] for n in ('guide_font_acquire','guide_font_release')},
                old_resource=dict(base=0x023D7B40,bytes=196,consumers='inside retired legacy image only'),
                source_sha256={path:pins[path] for path in ('sgp13/guide.py','features/field-guide/sorgenti/guide.c',
                    'features/field-guide/sorgenti/controller.h','features/field-guide/sorgenti/controller_core.h',
                    'features/ui-native/fieldbook.c','features/ui-native/bridge.c','features/ui-native/scene.c',
                    'features/ui-native/font.c','features/ui-native/guide_resource.c')},
                toolchain=toolchain,scope='cold cartridge native+installed source/compiled closure',
                limitations=['no live RAM or savestate migration','runtime late-writer and failure/HOLD campaign pending'])

# Reviewed cross-mode/data candidates. Each24B context is immutable; none is
# an allowlist for future writes. Inspect candidate-disassembly.txt for review.
_FALSE_CANDIDATES = (({'owner': 'arm9:0x2000000',
   'site': '0x204c0f8',
   'kind': 'arm-branch',
   'target': '0x23d4618',
   'domain': 'old-code'},
  None,
  '6753b4e66924ed254c97c8e76d6d05d4676e668c74a18c03e7673deb970ca9d5'),
 ({'owner': 'arm9:0x2000000',
   'site': '0x204c10c',
   'kind': 'arm-branch',
   'target': '0x23d4630',
   'domain': 'old-code'},
  None,
  '0497378efd61aabfddeb2973b7c3f6273f6b2500f28b06f80bf39fc13bbfb87b'),
 ({'owner': 'arm9:0x2000000',
   'site': '0x204c120',
   'kind': 'arm-branch',
   'target': '0x23d4648',
   'domain': 'old-code'},
  None,
  'b931f5f93f1db30d00137237c9ecbc1dea3c795f347f58e1ea4b2d5e67af5e38'),
 ({'owner': 'arm9:0x1ff8000',
   'site': '0x1ff98a0',
   'kind': 'arm-branch',
   'target': '0x23d5d48',
   'domain': 'old-code'},
  None,
  'a73894f933ad4ed2c29a742beae5b315136ef1d8a6ba1585f5455d19ca664314'),
 ({'owner': 'overlay:1',
   'site': '0x2204d84',
   'kind': 'arm-branch',
   'target': '0x23d5810',
   'domain': 'old-code'},
  1,
  'acc3d8002fc3829a6b0eb9149777a6b707a5e2eca11cf7d95af0c92cf7df4f03'),
 ({'owner': 'overlay:1',
   'site': '0x2207d0a',
   'kind': 'literal',
   'target': '0x23d4e27',
   'domain': 'old-code'},
  1,
  '4ee2e95d4d196954e6a4719698dd8d93ef31099e1f045f2b154da13b654ea12f'),
 ({'owner': 'overlay:2',
   'site': '0x224bc54',
   'kind': 'arm-branch',
   'target': '0x23d40f0',
   'domain': 'old-code'},
  2,
  '6112badb89130b166cb8b73c21daeb5756aa90daea27c5cd86906ae3447e367f'),
 ({'owner': 'overlay:2',
   'site': '0x224be8c',
   'kind': 'arm-branch',
   'target': '0x23d45d4',
   'domain': 'old-code'},
  2,
  '8305a647c1fd12f5e6770f2cbecc35c493d729d09471d10c43473cbeea149d0a'),
 ({'owner': 'overlay:2',
   'site': '0x224c12c',
   'kind': 'arm-branch',
   'target': '0x23d4134',
   'domain': 'old-code'},
  2,
  '3f434ee28642613c14022f25192aee85f4f3b4c1e4f7e65da2a671a05c5494b3'),
 ({'owner': 'overlay:2',
   'site': '0x224c998',
   'kind': 'arm-branch',
   'target': '0x23d49a0',
   'domain': 'old-code'},
  2,
  '7e44a83e22b9d32e5f2cb684b464653daabd3fd768a0f72ee4b5eb8fd43ecc05'),
 ({'owner': 'overlay:18',
   'site': '0x21e89dc',
   'kind': 'arm-branch',
   'target': '0x23d5e04',
   'domain': 'old-code'},
  18,
  'b9cbe7d8038c66453fc96f585f1afe5b1661f71384988646774efd1ce06b0e41'),
 ({'owner': 'overlay:18',
   'site': '0x21f1d2c',
   'kind': 'arm-branch',
   'target': '0x23d5d38',
   'domain': 'old-code'},
  18,
  'b8dec91cf250b72235ddb8ecaeabdd8b82b0324cfd03ffc4a3753b98d90a74e5'),
 ({'owner': 'overlay:18',
   'site': '0x21f1f3c',
   'kind': 'arm-branch',
   'target': '0x23d5f48',
   'domain': 'old-code'},
  18,
  'f432d61578254eb0b266fea0d14bfda508177baca95cde8e07092c1ebe1ed550'),
 ({'owner': 'overlay:40',
   'site': '0x223b350',
   'kind': 'arm-branch',
   'target': '0x23d567c',
   'domain': 'old-code'},
  40,
  'c22793aa5868e4a2d229d3403a2f3546e58110757f2d381a2dbc4cafe9d32a84'),
 ({'owner': 'overlay:49',
   'site': '0x2266d60',
   'kind': 'arm-branch',
   'target': '0x23d4188',
   'domain': 'old-code'},
  49,
  '0f06cee6fbb3d7df21953b048b77431d9a5f552c8edba9c031995e7aa0067ec2'),
 ({'owner': 'overlay:49',
   'site': '0x2266ef8',
   'kind': 'arm-branch',
   'target': '0x23d4320',
   'domain': 'old-code'},
  49,
  '77184b89ac952c455717ba4fbb0ba6d5a19463f65060fddf06d57d2a6e6e9701'),
 ({'owner': 'overlay:49',
   'site': '0x22670b8',
   'kind': 'arm-branch',
   'target': '0x23d44e0',
   'domain': 'old-code'},
  49,
  '95c64b9ddd92d3129ecdf7d7cae40fffb4302e534f5cbe09671f667e5a17520a'),
 ({'owner': 'overlay:85',
   'site': '0x21e7400',
   'kind': 'arm-branch',
   'target': '0x23d48e8',
   'domain': 'old-code'},
  85,
  'b3f501fe0fa36c950e7665bcc91e18d4af4c566afd15d8ff81125d604b692084'))


def _native_inventory(old,new,compiled):
    from sgp131.guide_incoming import inventory
    old_rows=inventory(old)
    false_rows=[row for row,overlay,digest in _FALSE_CANDIDATES]
    expected=list(false_rows)
    for overlay,site,old_name,new_name,kind in ROOTS:
        target=(_branch(site,_read(old,overlay,site,4)) if kind=='branch'
                else struct.unpack('<I',_read(old,overlay,site,4))[0])
        expected.append(dict(owner='overlay:'+str(overlay) if overlay is not None else 'arm9:0x2000000',
            site=hex(site),kind='thumb-branch' if kind=='branch' else 'literal',target=hex(target),domain='old-code'))
    for i,target in enumerate(struct.unpack('<3I',old.arm(0x023D7B10,12))):
        expected.append(dict(owner='arm9:0x23c8000',site=hex(0x023D7B10+4*i),kind='literal',target=hex(target),domain='old-code'))
    canonical=lambda rows:sorted(tuple(sorted(row.items())) for row in rows)
    _need(canonical(old_rows)==canonical(expected),'unknown preimage incoming candidate')
    for row,overlay,digest in _FALSE_CANDIDATES:
        site=int(row['site'],16)
        _need(_sha(_read(old,overlay,site-8,24))==digest and
              _read(new,overlay,site-8,24)==_read(old,overlay,site-8,24),'native ambiguity context changed')
    expected=list(false_rows)
    for overlay,site,old_name,new_name,kind in ROOTS:
        target=compiled['fieldbook']['symbols'][new_name]
        expected.append(dict(owner='overlay:'+str(overlay) if overlay is not None else 'arm9:0x2000000',
            site=hex(site),kind='thumb-branch' if kind=='branch' else 'literal',target=hex(target&~1 if kind=='branch' else target),domain='old-code'))
    focus=compiled['fieldbook']['symbols']['fieldbook_focus']
    _need(_branch(0x0225A96E,_read(old,27,0x0225A96E,4))==0x0225B4AC,'native focus preimage')
    _need(_branch(0x0225A96E,_read(new,27,0x0225A96E,4))==focus&~1,'book-aware focus ingress')
    expected.append(dict(owner='overlay:27',site='0x225a96e',kind='thumb-branch',target=hex(focus&~1),domain='old-code'))
    _need(canonical(inventory(new))==canonical(expected),'unknown installed incoming candidate')
    return dict(native_owners=4,overlay_owners=129,old_live_roots=9,retargeted_field_roots=6,
                native_focus_roots=1,
                resident_template_words=4,cross_mode_or_unaligned_data_candidates=len(false_rows),
                immutable_candidate_contexts_sha256=_sha(repr(_FALSE_CANDIDATES).encode()),
                method='source-pinned installer root attribution + exact compiled replacement + complete final-image complement; raw branch/literal inventory supplement')
