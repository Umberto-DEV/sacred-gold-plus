"""Independent final-image policy for the fixed UI stage, never receipt authority.

The writer is deliberately not imported. Parsers, write locations, descriptor
layout and seeds are restated here. Recompilation establishes authored bytes;
independent parsing establishes placement, lifecycle roots and preservation.
Static source/compiled correspondence cannot certify runtime late writers.
"""
from pathlib import Path
import hashlib
import json
import struct
import tempfile
import zlib

from ndspy import _common, codeCompression, fnt
from sgp12.blz import ndspy_decomprimi_sicuro
from sgp12.rom import Arm9, Rifiuto, valida_layout_arm9
from sgp13 import event_flags
from . import archives, baseline, cartridge_deltas, reserve, ui_compile, ui_resource_verify, guide_content, guide_retirement


def _need(ok, reason):
    if not ok:
        raise ValueError(reason)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


class Image:
    """Bounds checked cold cartridge view, no writer or ndspy ROM repacking."""
    def __init__(self, raw):
        _need(type(raw) is bytes and len(raw) >= 0x200, 'immutable cartridge bytes')
        self.raw = raw
        self.fnt, self.fnt_bytes, self.fat, self.fat_bytes, self.y9, self.y9_bytes = self.words(0x40, 6)
        _need((self.fat_bytes, self.y9_bytes) == (4104, 4128), 'file/overlay count')
        self.files = [self.words(self.fat + 8*i, 2) for i in range(513)]
        for lo, hi in self.files:
            _need(lo <= hi, 'FAT inverted span')
            self.chunk(lo, hi-lo)
        self.records = [self.words(self.y9 + 32*i, 8) for i in range(129)]
        _need(all(row[0] == i and row[6] == i for i, row in enumerate(self.records)), 'overlay/file ID')
        names = fnt.load(self.chunk(self.fnt, self.fnt_bytes))
        _need(names.idOf('a/0/2/7') == 156 and names.idOf('a/0/3/8') == 167, 'resource file IDs')
        arm_at, _, arm_base, arm_bytes = self.words(0x20, 4)
        _need(arm_base == 0x02000000, 'ARM9 base')
        params = self.words(arm_at + 0xBA0, 9)
        a, b, start, bss, end, compressed = params[:6]
        _need(compressed == 0 and params[7:] == (0xDEC00621, 0x2106C0DE), 'ARM9 module parameters')
        _need(start == bss == 0x02111860 and end == 0x021E5900 and start <= a <= b <= arm_base+arm_bytes
              and (b-a) % 12 == 0, 'ARM9 section boundaries')
        _t0, _t1, _d0, sections, self.mapped = valida_layout_arm9(
            raw, arm_at, arm_base, arm_bytes)
        for address, _length, zero in sections:
            _need(zero == (32 if address == 0x027E0000 else 0), 'autoload BSS')
        _need([(a,n) for a,_,n in self.mapped[1:]] == [(0x01FF8000,8192), (0x027E0000,96), (0x023C8000,98304)],
              'fixed autoload ownership')

    def chunk(self, offset, size):
        _need(0 <= offset <= offset+size <= len(self.raw), 'cartridge range')
        return self.raw[offset:offset+size]

    def words(self, offset, n):
        return struct.unpack('<' + str(n) + 'I', self.chunk(offset, n*4))

    def file(self, identity):
        a, b = self.files[identity]
        return self.chunk(a, b-a)

    def offset(self, address, size):
        found = [o+address-a for a,o,n in self.mapped if a <= address and address+size <= a+n]
        _need(len(found) == 1, 'mapped ARM9 span')
        return found[0]

    def arm(self, address, size):
        return self.chunk(self.offset(address,size), size)

    def overlay(self, identity):
        record = self.records[identity]
        encoded = self.file(record[6])
        try:
            if record[7] & 0x01000000:
                value = ndspy_decomprimi_sicuro(encoded, record[2])
            else:
                value = encoded
        except (ValueError, IndexError, struct.error, Rifiuto) as error:
            raise ValueError('malformed overlay compression') from error
        _need(len(value) == record[2], 'expanded overlay size')
        return bytes(value)


def _branch(site, raw):
    a, b = struct.unpack('<HH', raw)
    _need(a & 0xF800 == 0xF000 and b & 0xF800 == 0xF800, 'Thumb BL opcode')
    delta = ((a & 2047) << 12) | ((b & 2047) << 1)
    if delta & 0x400000:
        delta -= 0x800000
    return site + 4 + delta


def _export(part, name):
    address = part['symbols'][name]
    _need(address & 1 and part['base'] <= address & ~1 < part['base']+len(part['data']), 'export ownership ' + name)
    return address


def _legacy(old):
    # Exact source-to-binary attribution from the two independently recompiled
    # root inventories. Reviewed source pins are enforced by ui_compile.
    pins = [(0x023D9000,3776,'273c30f7d4d7620ae62c18385828f6508aa008b8cd01fd3064b2972c4f6260f1'),
            (0x023CB800,8192,'9370fae4e10445966d444fa62b26668445f740db11ac0347b50788cc845ce141'),
            (0x023D7500,512,'19bdc374a2cae6847d8aefe0541b58fd0acd64e9718b15dbe973b69d36a76ef2'),
            (0x023D7700,384,'a71aa42404b5d8dec7a106c3845d6803c5c7d47425ffbc6fcd94308a678b7636'),
            (0x023D4000,8192,'2f19c042588a613ab26cca40609909a4b7620d3b9fdfed412599dcad5813556e')]
    for address, size, digest in pins:
        _need(_sha(old.arm(address,size)) == digest, 'legacy source/binary attribution')
    _need(struct.unpack('<4I', old.arm(0x020FA354,16)) == (0x021E5901,0x021E5B3D,0x021E5A11,54), 'old Options template')
    _need(_branch(0x021E6820,old.overlay(54)[0xF20:0xF24]) == 0x023D75E0, 'old54 navigation ingress')
    _need(struct.unpack('<I',old.arm(0x023D75D8,4))[0] == 0x023CB801, 'computed navigation base')
    _need(struct.unpack('<4I', old.arm(0x023D7B10,16)) ==
          (0x023D40BD,0x023D4AF5,0x023D4F39,0xFFFFFFFF), 'old Guide template')
    _need(_branch(0x0203BFE4, old.arm(0x0203BFE4,4)) == 0x023D504C, 'old Guide task ingress')
    overlay = old.overlay(27)
    old_guide_edges = [(0x0225A0C6,0x023D51DC),(0x0225A40E,0x023D55C0),
                       (0x0225A856,0x023D55C0),(0x0225A860,0x023D5668)]
    for site, target in old_guide_edges:
        at = site-old.records[27][1]
        _need(_branch(site,overlay[at:at+4]) == target, 'old Guide field ingress')
    _need(struct.unpack_from('<I',overlay,0x0225A184-old.records[27][1])[0] == 0x023D5265,
          'old Guide frame ingress')
    at=0x0225A96E-old.records[27][1]
    _need(_branch(0x0225A96E,overlay[at:at+4]) == 0x0225B4AC,'native field focus preimage')
    # Complete navigation padded image above binds ADD #E0/BLX, not merely its
    # final pointer. The retained plus_button entry is not this dispatcher.
    return {'legacy_inventory_sha256': 'ca7d11520a0734501731da23ba6e09ac3a8fbbbd8f1eb2f1e82e8e6320044573',
            'guide_inventory_sha256': 'afb44edfd4d0f5f045054411dddcf7633985703026861528eaddedcc535ddaeb',
            'old_options_chain': [0x020FA354,0x021E6820,0x023D75E1,0x023D75A1,0x023CB801,0xE0],
            'old_guide_field_edges': old_guide_edges,
            'old_objects': [{'address':a,'bytes':n,'sha256':h} for a,n,h in pins]}


def _retirement(old, new, compiled):
    evidence = _legacy(old)
    # Explicit retained root/context/Continue/NewGame state envelope. No native
    # caller may confuse the checked successor app with old Options layout.
    retained = [(0x023D7500,1536), (0x023D9000,0x1000), (0x023D7C40,704),
                (0x0203EE14,64), (0x0203D320,112), (0x0200724C,224), (0x0203DEEC,1068)]
    for address,size in retained:
        _need(new.arm(address,size) == old.arm(address,size), 'retained native/legacy route')
    forbidden = {0x023D75A1,0x023D75E1,0x023D98F5,0x023D99E1}
    # Supplement to pinned source graph; never the only retirement proof.
    for name in ('scene','shiny','bridge','training','physical','fieldbook'):
        part=compiled[name]; blob=part['data']
        words={struct.unpack_from('<I',blob,i)[0] for i in range(0,len(blob)-3,2)}
        _need(not forbidden & words, 'successor references retained old dispatcher')
    tail=compiled['shiny']; gate=_export(compiled['scene'],'settings_final_check')
    _need(tail['defines']['SGP_SETTINGS_UI_FINAL_CHECK'] == gate, 'Shiny final gate identity')
    callbacks={_export(tail,'sgp_shiny_ui_'+n) for n in ('peek','prepare','commit')}
    # A resident descriptor is discovery metadata, not an unload-safe capability.
    # Only those three words may retain tail exports; no resident code/template
    # gets an asynchronous transaction callback. All unchanged aliasing overlays
    # remain attributed to their own virtual owners, not falsely called edges.
    references=[]
    for address,offset,length in new.mapped:
        for i in range(0,length-3,4):
            value=struct.unpack_from('<I',new.raw,offset+i)[0]
            if value in callbacks:
                references.append(address+i)
    _need(sorted(references) == [0x023CB1B0,0x023CB1B4,0x023CB1B8], 'external Shiny tail callback registration')
    # Reviewed pinned-source closure: owners calls peek/prepare/commit inline;
    # tail calls the gate synchronously and never publishes work/callbacks.
    # Training's resident wrappers only read original_* and generation fields.
    sources=ui_compile.SOURCE
    for relative in ['ui-native/bridge.c','ui-native/module.c','ui-native/persistent.c',
                     'ui-native/fieldbook.c','ui-native/physical.c',
                     'training-native/ui_transaction.c']:
        text=(sources/'features'/relative).read_text()
        _need(not any(name in text for name in ('->shiny_peek','->shiny_prepare','->shiny_commit')), 'resident dynamic transaction caller')
    evidence.update(retained=[{'address':a,'bytes':n,'sha256':_sha(new.arm(a,n))} for a,n in retained],
                    tail_exports=sorted(callbacks), tail_persistent_references=references,
                    synchronous_callers=['settings_owner_capture','settings_apply'],
                    source_graph='pinned owners synchronous calls → Shiny tail → synchronous final gate; pinned Scene/Bridge Exit barriers',
                    status='static source/compiled/root correspondence; runtime retirement pending')
    return evidence


def verify(before: bytes, after: bytes, language: str, charmap: Path, work_dir: Path, receipt=None,
           archive_deltas=(), overlay_deltas=()) -> dict:
    _need(type(before) is bytes and baseline.identify(before) == language, 'canonical input/language')
    audit=reserve.audit(before)
    config=ui_compile.read_config(work_dir)
    implementation={name:_sha((Path(__file__).parent/name).read_bytes())
                    for name in ('ui.py','ui_compile.py','ui_verify.py','archives.py','cartridge_deltas.py','guide_retirement.py','guide_incoming.py','test_ui.py','test_ui_rom.py')}
    pins=ui_compile.check_sources()
    old,new=Image(before),Image(after)
    # Declared member deltas are bound to this exact cartridge first (allowed archive, file id,
    # before hashes); extra archives are appended after the four UI bodies in file id order.
    deltas=archives.check_against(archive_deltas,*archives.from_cartridge(before))
    overlays=cartridge_deltas.check_against(overlay_deltas,before,language,work_dir)
    overlay_ids=tuple(d.file_id for d in overlays)
    extra=[d for d in deltas if d.file_id != archives.GUIDE_FILE]
    extra_ids=tuple(d.file_id for d in extra)
    appended_overlay=sum(len(d.image)+3 for d in overlays)
    appended_extra=sum(len(old.file(d.file_id))+d.total_after_bytes()+16 for d in extra)
    guide_growth=sum(d.total_after_bytes() for d in deltas if d.file_id == archives.GUIDE_FILE)
    _need(len(before) < len(after) <= len(before)+len(old.file(156))+guide_growth+appended_extra+appended_overlay+131072+65540+100916+old.records[27][2]+16, 'bounded appended cartridge')
    _need((new.fat,new.fat_bytes,new.fnt,new.fnt_bytes,new.y9,new.y9_bytes) ==
          (old.fat,old.fat_bytes,old.fnt,old.fnt_bytes,old.y9,old.y9_bytes), 'table relocation forbidden')
    compiled=ui_compile.compile_payloads(config,work_dir)
    resource=ui_compile.resources(before,language,charmap,deltas)
    allowed=[]
    records=[]
    def exact(offset,expected,label):
        _need(new.chunk(offset,len(expected)) == expected, 'postimage '+label)
        allowed.append((offset,offset+len(expected)))
        records.append(dict(label=label,offset=offset,bytes=len(expected),before_sha256=_sha(old.chunk(offset,len(expected))),after_sha256=_sha(expected)))
    def arm(address,expected,label):
        _need(new.offset(address,len(expected)) == old.offset(address,len(expected)), 'ARM9 mapping changed')
        exact(new.offset(address,len(expected)),expected,label)
    with tempfile.TemporaryDirectory(prefix='event-flags-verify-', dir=work_dir) as flag_dir:
        flag_writes, flag_receipt = event_flags.prepare_upgrade(
            Arm9.from_bytes(before), flag_dir, language,
            _export(compiled['training'], 'training_ui_load'))
    for address, value in sorted(flag_writes.items()):
        arm(address, value, 'event flags HF02 ' + hex(address))
    for name,base,cap in [('bridge',0x023CB800,12272),('physical',0x023D6E10,1024),
                          ('training',0x023D6800,1536),('fieldbook',0x023D4000,3072)]:
        part=compiled[name];_need(part['base']==base and 0<len(part['data'])<=cap,'owner capacity')
        arm(base,part['data']+bytes(cap-len(part['data'])),name)
    for address,count in ((0x023D7B20,40),(0x023D7B48,16),(0x023D7210,48),(0x023CB1F0,16)):
        arm(address,bytes(count),'cold zero '+hex(address))
    arm(0x023D4C00,bytes(3776),'retired Guide suffix')
    bridge=compiled['bridge'];training=compiled['training'];shiny=compiled['shiny']
    for address,role in [(0x020FA354,'settings'),(0x023D7B10,'guide')]:
        values=[_export(bridge,'ui_bridge_'+role+'_init'),_export(bridge,'ui_bridge_main'),_export(bridge,'ui_bridge_exit'),0xFFFFFFFF]
        arm(address,struct.pack('<4I',*values),role+' resident template')
    descriptor=struct.pack('<I6H16I',0x31544955,1,80,152,52,3,0,
                          *[_export(shiny,'sgp_shiny_ui_'+n) for n in ('peek','prepare','commit')],
                          *[_export(training,'training_ui_'+n) for n in ('peek','validate','store','load','bind')],
                          0x023D1321,0x023D1A45,0x023D1B1D,0x023CB1F0,0,0,0,0)
    arm(0x023CB1A0,descriptor,'transaction descriptor80')
    for address,name,original in ((0x023CB130,'training_ui_bind',0x023D1A45),):
        _need(struct.unpack('<I',old.arm(address,4))[0] == original,'original Training entry')
        arm(address,struct.pack('<I',_export(training,name)),'Training delegate '+name)
    for address,part,name in ((0x0201A556,'physical','physical_after_native_mapping'),
                               (0x02000DB0,'physical','physical_lid_action'),
                               (0x0203BFE4,'fieldbook','fieldbook_task_input')):
        actual=new.arm(address,4)
        _need(_branch(address,actual) == (_export(compiled[part],name)&~1),'installed branch '+name)
        exact(new.offset(address,4),actual,'hook '+name)
    overlay27=new.overlay(27); old27=old.overlay(27)
    p=new.records[27];q=old.records[27]
    _need(p[:7] == q[:7] and p[7]>>24 == 1 and p[7]&0xFFFFFF == len(new.file(27)), 'overlay27 record')
    differences=[]
    for address,name in [(0x0225A0C6,'fieldbook_create'),(0x0225A40E,'fieldbook_touch'),
                         (0x0225A856,'fieldbook_touch'),(0x0225A860,'fieldbook_dpad'),
                         (0x0225A96E,'fieldbook_focus')]:
        at=address-p[1];_need(_branch(address,overlay27[at:at+4]) == (_export(compiled['fieldbook'],name)&~1),'Fieldbook ingress')
        differences.extend(range(at,at+4))
    at=0x0225A184-p[1]
    _need(struct.unpack_from('<I',overlay27,at)[0] == _export(compiled['fieldbook'],'fieldbook_frame'),'Fieldbook frame callback')
    differences.extend(range(at,at+4))
    mask=set(differences)
    _need(all(a==b or i in mask for i,(a,b) in enumerate(zip(old27,overlay27))), 'foreign overlay27 hook')
    _need(codeCompression.compress(overlay27) == new.file(27),'overlay27 packed bytes')
    exact(new.y9+27*32+28,struct.pack('<I',p[7]),'overlay27 packed length')
    dynamic=compiled['dynamic54']['data'];size=len(dynamic)
    _need(size%4 == 0 and size<=65536 and new.overlay(54)==dynamic,'complete dynamic54 authored image')
    packed=codeCompression.compress(dynamic)
    _need(new.file(54)==packed and ndspy_decomprimi_sicuro(packed,len(dynamic))==dynamic,'dynamic54 compression')
    expected54=(54,0x021E5900,size,0,0x021E5900+size,0x021E5900+size,54,0x01000000|len(packed))
    exact(new.y9+54*32,struct.pack('<8I',*expected54),'dynamic54 record')
    for i in range(129):
        if i not in (27,54,*overlay_ids):
            _need(new.records[i]==old.records[i],'foreign overlay table record')
    for delta in overlays:
        cartridge_deltas.verify_readback(delta,old,new)
        exact(new.y9+126*32,struct.pack("<8I",*delta.row),"rematches overlay126 record")
    # Independent NARC traversal: no dropped old member or arbitrary new data.
    os,on,oi,ob=ui_resource_verify._archive(old.file(156))
    ns,nn,ni,nb=ui_resource_verify._archive(new.file(156))
    if any(d.file_id == archives.GUIDE_FILE for d in deltas):
        # Declared members differ; geometry, padding and the other members are read by the delta loop below.
        _need(len(os)==len(ns)==830 and on==nn, 'Guide member table/names')
    else:
        _need(len(os)==len(ns)==830 and on==nn and os[:829]==ns[:829], 'Guide member table/names')
        _need(ns[829][0]==os[829][0] and ni[:ns[829][0]]==oi[:os[829][0]],'old Guide members/padding')
    ga,gb=ns[829];guide=ni[ga:gb]
    _need(guide==resource['guide'] and ni[gb:]==bytes((-gb)%4), 'Guide payload/hidden suffix')
    guide_content.verify_content(guide,resource['guide_graph'])
    resource_receipt=ui_resource_verify.verify_resource(before,new.file(167),resource['authored'])
    _need(new.file(167)==resource['uir'] and resource_receipt==resource['uir_receipt'],'UIR resource')
    # Append contract: four bodies in fixed order, <=3 zero alignment bytes,
    # old indexed and unindexed data remains in place. No repacking elsewhere.
    cursor=len(before)
    appended=[]
    for fid in (27,54,156,167,*extra_ids,*overlay_ids):
        aligned=(cursor+3)&~3
        _need(new.chunk(cursor,aligned-cursor)==bytes(aligned-cursor),'append alignment')
        a,b=new.files[fid]
        _need(a==aligned and b>a,'append order/overlap')
        exact(new.fat+8*fid,struct.pack('<II',a,b),'FAT '+str(fid))
        appended.append(dict(file_id=fid,start=a,end=b,sha256=_sha(new.file(fid))))
        cursor=b
    _need(cursor==len(after),'unindexed appended bytes')
    for fid in range(513):
        if fid not in (27,54,156,167) and fid not in extra_ids and fid not in overlay_ids:
            _need(new.files[fid]==old.files[fid] and new.file(fid)==old.file(fid),'foreign active file '+str(fid))
    # Every declared delta: independent member traversal and the producer's semantic checker.
    for delta in deltas:
        declared=delta.replacements()
        if delta.file_id == archives.GUIDE_FILE:
            declared={**declared,829:resource['guide']}      # the UI stage's own member
        archives.verify_members(old.file(delta.file_id),new.file(delta.file_id),declared)
        archives.check_semantics(delta,old.file(delta.file_id),new.file(delta.file_id),language)
    offsets=[_export(compiled['scene'],'ui_scene_'+n)-0x021E5900 for n in ('init','main','exit')]
    module=(0x314D4955,2,0,0,54,54,0x021E5900,size,0,0x021E5900+size,0x021E5900+size,
            expected54[7],zlib.crc32(dynamic),*offsets,zlib.crc32(packed),
            zlib.crc32(new.chunk(new.y9,new.y9_bytes)),new.y9,new.y9_bytes,len(after),*new.files[54],129)
    arm(0x023D7B60,struct.pack('<24I',*module),'Module96 final seed')
    arm(0x023D7BC0,bytes.fromhex(resource_receipt['config_hex']),'UIR64 final seed')
    nc,ne=struct.unpack_from('<HH',guide,8)
    guide_config=(0x31435247,1,int(language=='IT'),0,156,*new.files[156],len(after),len(new.file(156)),
                  nb+ga,len(guide),zlib.crc32(guide),nc,ne,0,0)
    arm(0x023D7C00,struct.pack('<16I',*guide_config),'Guide64 final seed')
    exact(0x80,struct.pack('<I',len(after)),'header ROM length')
    exact(0x15E,struct.pack('<H',_common.crc16(after[:0x15E])),'header CRC16')
    _need(len(after)<=128*1024 << before[0x14],'cartridge capacity')
    # Complete complement comparison is the fixed policy, including historical
    # unreachable files, ARM7, FNT, save IDs, native wrappers and owner guards.
    cursor=0
    for lo,hi in sorted(allowed):
        _need(cursor<=lo<hi<=len(before),'overlapping policy writes')
        _need(before[cursor:lo]==after[cursor:lo],'protected cartridge bytes '+hex(cursor))
        cursor=hi
    _need(before[cursor:]==after[cursor:len(before)],'protected cartridge suffix')
    retirement=_retirement(old,new,compiled)
    retirement['guide']=guide_retirement.verify(old,new,compiled,work_dir)
    ui_compile.check_sources()
    _need(ui_compile.read_config(work_dir)==config,'candidate configuration changed during verification')
    _need(implementation == {name:_sha((Path(__file__).parent/name).read_bytes()) for name in implementation},
          'installer implementation changed during verification')
    config_bytes=json.dumps(config,sort_keys=True,separators=(',',':')).encode()
    result=dict(schema=1,stage='ui',validation='static composition; runtime acceptance pending',
                language=language,input_sha256=_sha(before),output_sha256=_sha(after),input_bytes=len(before),output_bytes=len(after),
                config=config,config_sha256=_sha(config_bytes),config_crc32=zlib.crc32(config_bytes),
                policy_sha256=audit['policy_sha256'],source_sha256=pins,implementation_sha256=implementation,
                library_sha256=ui_compile.LIBRARY_PINS,python_version=ui_compile.PYTHON_VERSION,
                charmap_sha256=_sha(Path(charmap).read_bytes()),
                payloads={name:part['receipt'] for name,part in compiled.items() if 'receipt' in part},
                event_flags=flag_receipt,
                dynamic54=dict(bytes=size,sha256=_sha(dynamic),packed_bytes=len(packed),packed_sha256=_sha(packed),
                               scene_bytes=len(compiled['scene']['data']),shiny_tail_base=shiny['base'],bss=0),
                writes=records,appended=appended,retirement=retirement,
                resource=dict(uir=resource_receipt,guide_sha256=_sha(guide),guide_bytes=len(guide)),
                file_count=513,overlay_count=129,all_other_bytes_preserved=True,
                conditional_assignments=[dict(name=name,start=start,bytes=count,capacity=capacity)
                    for name,start,count,capacity in [
                     ('ui.bridge.code',0x023CB800,min(8192,len(bridge['data'])),8192),
                     ('ui.bridge.tail',0x023CD800,max(0,len(bridge['data'])-8192),4080),
                     ('fieldbook.code',0x023D4000,len(compiled['fieldbook']['data']),3072),
                     ('guide.template',0x023D7B10,16,16),('ui.bootstrap',0x023D7B20,40,40),
                     ('ui.control',0x023D7B48,16,16),('ui.module.seed',0x023D7B60,96,96),
                     ('ui.resource.seed',0x023D7BC0,64,64),('ui.guide.seed',0x023D7C00,64,64)]],
                limits=['native installed entry/failure/HOLD and late callbacks untested',
                        'Android timing/display and raw-save Continue/SAVE/cold-restart untested',
                        'test-candidate calibration only; no stage promotion or runtime acceptance'])
    if deltas:   # absent without deltas: receipts of delta-free images keep their historical form
        result['archive_deltas']=[d.record() for d in deltas]
    if overlays:
        result['overlay_deltas']=[d.record() for d in overlays]
    if receipt is not None:
        _need(type(receipt) is dict and json.dumps(receipt,sort_keys=True,allow_nan=False)==json.dumps(result,sort_keys=True,allow_nan=False),
              'receipt differs from independent readback')
    return result
