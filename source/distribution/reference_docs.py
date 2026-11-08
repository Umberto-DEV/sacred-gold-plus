"""Read exact candidate facts and render localized player reference PDFs.

Only codecs and layouts are public. Cartridge names, tables and Guide prose
remain in memory until the caller explicitly requests player documents.
"""
from __future__ import annotations
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import tempfile
import unicodedata
from xml.sax.saxutils import escape
from ndspy.narc import NARC
from ndspy.rom import NintendoDSRom
from localization.catalogue import load_strings, LOCALES
from localization.guide import evolution_description
from localization.messages import _TEXT
from translation.message_codec import Bank
from sgp131.guide_content import read_content

SOURCE = Path(__file__).resolve().parents[1]
MAP_HEADERS, MAP_COUNT = 0x020F6BE0, 540
LABELS = ('installation news events pokemon locations evolutions items trainers gameplay '
          'species number type stats ability level move before after map method parameter '
          'target item trainer party source page credits originals coverage same_data '
          'candidate_note event_note credits_note cheats_note language_selector none day '
          'night grass water old_rod good_rod super_rod morning minimum maximum '
          'new_game_fix new_languages encounter_note headbutt_note contest_note safari_note').split()
REQUIRED = ({f'd:news:{i}' for i in range(46)} | {f'd:install:{i}' for i in range(15)} |
            {'d:label:' + key for key in LABELS})
FILENAMES = ('Installation','Whats-New','Special-Events','Pokemon-Changes',
             'Pokemon-Locations','Evolutions','Items-TMs','Trainers','Game-Guide')
PLAYER_OVERRIDES = tuple(('install:' + str(i)) for i in (1,2,5,10,11,13)) + (
    'news:31','news:44','label:credits_note','label:originals',
    'label:language_selector','label:new_languages','label:updater_intro')
WALK_KEYS = ('apply_intro', 'backup', 'browser', 'browser_h', 'capture', 'choose', 'copy', 'download', 'extract', 'files', 'firstplay', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'hash_warn', 'help', 'mac', 'mac_h', 'offline', 'offline_h', 'ref_a', 'ref_b', 'save_output', 'select', 'settings', 'sha_what', 'sha_where', 'stop', 'trouble', 'update_note', 'verify', 'windows', 'windows_h')
PLAYER_OVERRIDES += tuple('walk:'+key for key in WALK_KEYS)
PLAYER_REQUIRED = {'p:r2:' + key for key in PLAYER_OVERRIDES}
CLEAN_IDS = {'EN':'clean-us','IT':'clean-it','FR':'clean-fr','ES':'clean-es','DE':'clean-de'}
NAME_BANKS = dict(pokemon=237,item=222,move=750,map=279,ability=720,
                  type=735,trainer=729,**{'class':730},stat=443)
SELECTORS = dict(land=(0x0224768C,12),surf=(0x02247720,5),fish=(0x02247764,5),
                 rock=(0x0224779C,2),headbutt=(0x022477C0,6))


def _need(ok, reason):
    if not ok: raise ValueError(reason)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def validate_documents(values):
    """Refuse missing translations or unexpected formatter placeholders."""
    missing = REQUIRED - set(values)
    _need(not missing,'missing document translations: '+', '.join(sorted(missing)))
    _need(set(values)==REQUIRED and all(isinstance(v,str) and v.strip() for v in values.values()),
          'unexpected/empty document translation')
    for key,value in values.items():
        allowed = {'version'} if key=='d:install:0' else (
            {'version','language','target_sha256'} if key=='d:install:13' else set())
        _need(set(re.findall(r'\{([^{}]+)\}',value))==allowed,'document placeholder '+key)
    return values


def load_documents(locale):
    """Return the unchanged historical document copy, excluding r2 overlays."""
    values=load_strings(locale,'documents')
    return validate_documents({key:value for key,value in values.items() if key not in PLAYER_REQUIRED})


def load_player_documents(locale):
    """Require all explicitly localized r2 overlays without altering old copy."""
    values=load_strings(locale,'documents')
    words=validate_documents({key:value for key,value in values.items() if key not in PLAYER_REQUIRED})
    overlays={key:value for key,value in values.items() if key in PLAYER_REQUIRED}
    _need(set(overlays)==PLAYER_REQUIRED and all(value.strip() for value in overlays.values()),
          'missing/empty player document translations')
    for key,value in overlays.items():
        allowed=({'version','language','target_name','target_bytes','target_sha256'}
                 if key=='p:r2:install:13' else ({'package_revision'} if key=='p:r2:walk:download' else set()))
        _need(set(re.findall(r'\{([^{}]+)\}',value))==allowed,'player document placeholder '+key)
        words['d:'+key.removeprefix('p:r2:')]=value
    return words


def validate_inputs(locale,candidate,reference,contract):
    """Authenticate complete inputs before creating any output."""
    _need(locale in LOCALES and isinstance(candidate,bytes) and isinstance(reference,bytes),'manual arguments')
    target=contract.get('targets',{}).get(locale,{})
    _need((_sha(candidate),len(candidate))==(target.get('sha256'),target.get('bytes')),
          'candidate identity does not match target contract')
    sources=contract.get('sources',[]);ids=set()
    for row in sources:
        identity=row.get('id','')
        _need(isinstance(identity,str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,79}',identity)
              and identity not in ids,'invalid/duplicate source ID')
        ids.add(identity)
        _need(isinstance(row.get('label'),str) and row['label'].strip()
              and re.fullmatch('[0-9a-f]{64}',row.get('sha256',''))
              and type(row.get('bytes')) is int and row['bytes']>0,'source identity fields')
    routes=contract.get('routes_by_target',{}).get(locale,[])
    _need(routes and len(set(routes))==len(routes) and set(routes)<=ids,'target source routes')
    identity=(_sha(reference),len(reference))
    clean_id=CLEAN_IDS[locale]
    _need(any(r['id']==clean_id and identity==(r['sha256'],r['bytes']) for r in sources),
          'reference must be the matching clean retail baseline')
    _need(re.fullmatch(r'[0-9]+(?:\.[0-9]+){1,3}(?:-[A-Za-z0-9.]+)?',contract.get('version','')),'manual version')
    return target


def parse_evolutions(records):
    """Return stable species/slot/method/parameter/target tuples."""
    _need(len(records)>=494,'incomplete evolution archive');result=[]
    for species in range(1,494):
        _need(len(records[species])>=42,'truncated evolution record')
        for slot in range(7):
            method,parameter,target=struct.unpack_from('<3H',records[species],6*slot)
            if not method:continue
            _need(1<=method<=23 and 1<=target<=493,'invalid evolution method/target')
            result.append((species,slot,method,parameter,target))
    return result


def decode_learnset(raw):
    """Read native pairs losslessly, including deliberate repeated moves."""
    _need(raw and len(raw)%2==0,'learnset extent')
    words=struct.unpack('<'+'H'*(len(raw)//2),raw)
    _need(65535 in words,'learnset terminator')
    end=words.index(65535)
    _need(not any(words[end+1:]),'learnset trailing data')
    pairs=tuple((word>>9,word&511) for word in words[:end])
    _need(all(1<=level<=100 and 1<=move<=467 for level,move in pairs),'learnset pair')
    return pairs


def parse_species(personal,learnsets):
    _need(min(len(personal),len(learnsets))>=494,'incomplete species archives');rows=[]
    for number in range(1,494):
        raw=personal[number];_need(len(raw)==44,'personal record extent')
        rows.append(dict(id=number,stats=tuple(raw[:6]),types=tuple(raw[6:8]),
                         abilities=tuple(raw[22:24]),learnset=tuple(decode_learnset(learnsets[number]))))
    return rows


def _fnv(raw):
    value=2166136261
    for byte in raw:value=((value ^ byte)*16777619)&0xffffffff
    return value


def parse_trainers(headers,parties,level_table=None,strategy=None):
    """Read four native formats, exact Plus levels and installed SGT1 move deltas."""
    _need(len(headers)==len(parties),'trainer header/party count')
    _need(level_table is None or len(level_table)==256,'trainer level table')
    changes=defaultdict(list)
    if strategy is not None:
        _need(len(strategy)>=8,'strategy header');magic,nt,nm=struct.unpack_from('<IHH',strategy)
        _need(magic==0x31544753 and nt<=16 and nm<=32 and 8+nt*16+nm*8<=len(strategy),'strategy bounds')
        for i in range(nt):
            trainer,first,old_hash,new_hash,kind,count,size,n=struct.unpack_from('<HHIIBBBB',strategy,8+16*i)
            _need(trainer<len(parties) and kind==3 and count==6 and size==108 and n>0
                  and first+n<=nm,'strategy party contract')
            original=parties[trainer];changed=bytearray(original)
            _need(_fnv(original)==old_hash and len(original)==size,'strategy party preimage')
            for j in range(first,first+n):
                offset,before,after,reserved=struct.unpack_from('<4H',strategy,8+16*nt+8*j)
                _need(not reserved and offset%18 in (8,10,12,14) and offset<size-1 and after<=467
                      and struct.unpack_from('<H',changed,offset)[0]==before,'strategy move preimage')
                struct.pack_into('<H',changed,offset,after);changes[trainer].append((offset,after))
            _need(_fnv(changed)==new_hash,'strategy party result')
    rows=[]
    for identity,(header,raw) in enumerate(zip(headers,parties)):
        _need(len(header)>=20,'trainer header extent');kind,trainer_class,_,count=header[:4]
        _need(kind<=3 and count<=6,'trainer party format');stride=8+(8 if kind&1 else 0)+(2 if kind&2 else 0)
        _need(stride*count<=len(raw)<=stride*6 and len(raw)%stride==0,'trainer party extent');adjusted=bytearray(raw)
        for offset,value in changes[identity]:struct.pack_into('<H',adjusted,offset,value)
        maximum=max((struct.unpack_from('<H',raw,stride*i+2)[0] for i in range(count)),default=0);party=[]
        for slot in range(count):
            at=slot*stride;iv_scale,override,level,packed=struct.unpack_from('<BBHH',raw,at)
            _need(1<=packed&1023<=493 and 1<=level<=100,'trainer species/level');cursor=at+6
            item=struct.unpack_from('<H',raw,cursor)[0] if kind&2 else 0;cursor+=2 if kind&2 else 0
            moves=struct.unpack_from('<4H',raw,cursor) if kind&1 else ()
            plus_moves=struct.unpack_from('<4H',adjusted,cursor) if kind&1 else ()
            plus_level=max(level,min(100,level_table[maximum]-(maximum-level))) if level_table is not None else level
            party.append(dict(slot=slot,species=packed&1023,form=packed>>10,level=level,
                              plus_level=plus_level,item=item,moves=moves,plus_moves=plus_moves,
                              iv_scale=iv_scale,override=override,capsule=struct.unpack_from('<H',raw,at+stride-2)[0]))
        rows.append(dict(id=identity,**{'class':trainer_class},type=kind,party=party,unused_records=len(raw)//stride-count,
                         items=struct.unpack_from('<4H',header,4),ai=struct.unpack_from('<I',header,12)[0]))
    return rows


def parse_encounters(records,headers,swarms=None):
    """Join EncounterData to actual MapHeader mapsec IDs, never translated names.

    Layouts are documented by pret/pokeheartgold map_header.h and wild_encounter.h.
    Methods 6/7 are radio, 8/9/10 outbreaks and 11/12 night fishing overrides.
    """
    _need(len(headers)%24==0,'map header extent');result=[]
    for map_id in range(len(headers)//24):
        bank,section=headers[24*map_id],headers[24*map_id+18]
        if bank==255:continue
        _need(bank<len(records),'encounter bank outside archive');raw=records[bank]
        _need(len(raw)==196,'encounter bank extent')
        def add(method,time,slot,species,low,high,rate):
            if not species or not rate:return
            _need(1<=species<=493 and 1<=low<=high<=100,'encounter species/level')
            result.append((map_id,section,bank,method,time,slot,species,low,high,rate))
        for time in range(3):
            for slot in range(12):
                species=struct.unpack_from('<H',raw,20+24*time+2*slot)[0]
                add(0,time,slot,species,raw[8+slot],raw[8+slot],raw[0])
        for method,offset,number in ((1,0x64,5),(2,0x78,2),(3,0x80,5),(4,0x94,5),(5,0xA8,5)):
            for slot in range(number):
                low,high,species=struct.unpack_from('<BBH',raw,offset+slot*4)
                add(method,-1,slot,species,low,high,raw[method])
        for method,offset in ((6,0x5C),(7,0x60)):
            for pair in range(2):
                species=struct.unpack_from('<H',raw,offset+pair*2)[0]
                for slot in ((2,3) if pair==0 else (4,5)):
                    add(method,-1,slot,species,raw[8+slot],raw[8+slot],raw[0])
        for native,method,offset,slots,base,base_offset in (
                (0,8,0xBC,(0,1),0,None),(1,9,0xBE,(0,),1,0x64),
                (2,10,0xC2,(2,),3,0x80),(2,10,0xC2,(0,2,3),4,0x94),
                (2,10,0xC2,(0,1,2,3,4),5,0xA8)):
            if swarms is not None and (map_id,native) not in swarms:continue
            species=struct.unpack_from('<H',raw,offset)[0]
            for slot in slots:
                if base_offset is None:low=high=raw[8+slot]
                else:low,high=raw[base_offset+4*slot:base_offset+4*slot+2]
                add(method,base if method==10 else -1,slot,species,low,high,raw[base])
        night=struct.unpack_from('<H',raw,0xC0)[0]
        for method,base,offset,slot in ((11,4,0x94,3),(12,5,0xA8,1)):
            low,high=raw[offset+slot*4:offset+slot*4+2]
            add(method,2,slot,night,low,high,raw[base])
    return sorted(set(result))


def _arm_reader(rom):
    sections=rom.loadArm9().sections
    def read(address,size):
        found=[bytes(s.data[address-s.ramAddress:address-s.ramAddress+size]) for s in sections
               if s.ramAddress<=address and address+size<=s.ramAddress+len(s.data)]
        _need(len(found)==1 and len(found[0])==size,'unmapped native fact address')
        return found[0]
    return read


def native_selector_weights(image,base,entries=SELECTORS):
    """Enumerate 100 native selector rolls in bounded, isolated ARM memory.

    Only RNG and unsigned division are service seams. Branches and returns are
    real candidate instructions, so probabilities are never copied from an old
    PDF or inferred from translated labels. This measures ordinary slot weights,
    without lead-ability coercion or other encounter-generation modifiers.
    """
    from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE
    from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_PC,UC_ARM_REG_LR,UC_ARM_REG_SP
    _need(0x02000000<=base and base+len(image)<0x02500000,'selector image extent')
    cpu=Uc(UC_ARCH_ARM,UC_MODE_THUMB);cpu.mem_map(0x02000000,0x500000);cpu.mem_write(base,bytes(image))
    stop,stack=0x02001000,0x024F0000
    def random(mu,address,size,state):
        mu.reg_write(UC_ARM_REG_R0,state['roll']);mu.reg_write(UC_ARM_REG_PC,mu.reg_read(UC_ARM_REG_LR))
    def divide(mu,address,size,state):
        numerator=mu.reg_read(UC_ARM_REG_R0);denominator=mu.reg_read(UC_ARM_REG_R1)
        _need(denominator==100,'selector divisor')
        mu.reg_write(UC_ARM_REG_R0,numerator//denominator);mu.reg_write(UC_ARM_REG_R1,numerator%denominator)
        mu.reg_write(UC_ARM_REG_PC,mu.reg_read(UC_ARM_REG_LR))
    state={'roll':0}
    cpu.hook_add(UC_HOOK_CODE,random,state,begin=0x0201FD44,end=0x0201FD44)
    cpu.hook_add(UC_HOOK_CODE,divide,state,begin=0x020F2998,end=0x020F2998)
    result={}
    for name,(entry,count) in entries.items():
        _need(base<=entry<base+len(image) and 1<=count<=12,'selector entry')
        weights=[0]*count
        for roll in range(100):
            state['roll']=roll;cpu.reg_write(UC_ARM_REG_R0,roll)
            cpu.reg_write(UC_ARM_REG_SP,stack);cpu.reg_write(UC_ARM_REG_LR,stop|1)
            cpu.emu_start(entry|1,stop,count=500)
            slot=cpu.reg_read(UC_ARM_REG_R0)
            _need(cpu.reg_read(UC_ARM_REG_PC)==stop and cpu.reg_read(UC_ARM_REG_SP)==stack
                  and 0<=slot<count,'selector return/slot')
            weights[slot]+=1
        result[name]=tuple(weights)
    return result


def parse_headbutt(records, headers):
    """Read three tree groups and verify the full native coordinate extent."""
    _need(len(records) == len(headers)//24, 'Headbutt map count')
    result=[]
    for map_id,raw in enumerate(records):
        _need(len(raw)>=4, 'Headbutt header')
        regular,secret=struct.unpack_from('<HH',raw)
        if not regular and not secret:
            _need(len(raw)==4,'Headbutt empty member');continue
        _need(len(raw)==76+24*(regular+secret),'Headbutt coordinate extent')
        for group in range(3):
            if (group<2 and not regular) or (group==2 and not secret):continue
            for slot in range(6):
                species,low,high=struct.unpack_from('<HBB',raw,4+24*group+4*slot)
                if not species:continue
                _need(1<=species<=493 and 1<=low<=high<=100,'Headbutt species/level')
                result.append((map_id,headers[map_id*24+18],group,slot,species,low,high))
    return result


def parse_contest(raw):
    """Read pre-National and Tuesday/Thursday/Saturday National contest sets."""
    _need(len(raw)==320,'Bug Contest encounter extent');result=[];previous=100
    for index in range(40):
        if index%10==0:previous=100
        species,low,high,rate,score=struct.unpack_from('<HBBBB',raw,8*index)
        _need(1<=species<=493 and 1<=low<=high<=100 and 0<=rate<previous,'Bug Contest species/level/rate')
        result.append((index//10,index%10,species,low,high,previous-rate,score))
        previous=rate
        if index%10==9:_need(rate==0,'Bug Contest uncovered rolls')
    return result


def parse_safari(records):
    """Read base/bonus rows and object-point gates without simulating saves."""
    result=[]
    for area,raw in enumerate(records):
        _need(len(raw)>=8,'Safari header');offset=8
        for method in range(5):
            count=raw[method];base=offset;bonus=base+120;conditions=bonus+12*count
            end=conditions+4*count
            _need(end<=len(raw),'Safari record extent')
            for is_bonus,number,start in ((0,10,base),(1,count,bonus)):
                for time in range(3):
                    for slot in range(number):
                        species,level=struct.unpack_from('<HH',raw,start+4*(time*number+slot))
                        if not species:continue
                        gate=tuple(raw[conditions+4*slot:conditions+4*slot+4]) if is_bonus else (0,0,0,0)
                        _need(1<=species<=493 and 1<=level<=100,'Safari species/level')
                        _need(not is_bonus or (1<=gate[0]<=4 and gate[2]<=4),'Safari object gate')
                        result.append((area,method,time,slot,is_bonus,species,level,gate))
            offset=end
        _need(offset==len(raw),'Safari trailing bytes')
    return result


def read_facts(candidate,charmap,*,include_guide=True):
    """Read cartridge data in memory without extraction directories or ROM writes."""
    rom=NintendoDSRom(candidate);archive=NARC(rom.getFileByName('a/0/2/7')).files
    chars,commands=_TEXT.load_charmap(charmap)
    def decode(words):
        row=_TEXT.render(list(words),chars,commands)
        _need(not row['controls'] and not row['unknown_codes'] and not row['malformed_controls'],
              'invalid native document name/text')
        return row['text']
    names={kind:[decode(row) for row in Bank(archive[bank]).words] for kind,bank in NAME_BANKS.items()}
    def rows(path):return NARC(rom.getFileByName(path)).files
    facts=dict(names=names,species=parse_species(rows('a/0/0/2'),rows('a/0/3/3')),
               evolutions=parse_evolutions(rows('a/0/3/4')) if include_guide else [],trainers=[],encounters=[],guide=[])
    if not include_guide:return facts
    arm=_arm_reader(rom);table=arm(MAP_HEADERS,MAP_COUNT*24)
    pointer=struct.unpack('<I',arm(0x02097F94,4))[0];sw=struct.unpack('<40H',arm(pointer,80))
    swarms=set(zip(sw[::2],sw[1::2]));_need(all(0<=m<MAP_COUNT and 0<=v<=2 for m,v in swarms),'native swarm mapping')
    facts['encounters']=parse_encounters(rows('a/0/3/7'),table,swarms)
    overlay=rom.loadArm9Overlays([2])[2]
    facts['weights']=native_selector_weights(overlay.data,overlay.ramAddress)
    facts['headbutt']=parse_headbutt(rows('a/2/5/2'),table)
    facts['contest']=parse_contest(rom.getFileByName('data/mushi/mushi_encount.bin'))
    facts['safari']=parse_safari(rows('a/2/3/0'))
    facts['trainers']=parse_trainers(rows('a/0/5/5'),rows('a/0/5/6'),arm(0x023D8500,256),arm(0x023D6600,512))
    _need(len(archive)>829 and archive[829][:4]==b'SGG1','candidate Guide member 829 missing')
    for category in read_content(archive[829]):
        category['title']=decode(category['title'])
        for entry in category['entries']:
            entry['title']=decode(entry['title'])
            for page in entry['pages']:page['lines']=[decode(line) for line in page['lines']]
        facts['guide'].append(category)
    # These native, localized names explain radio and outbreak variants.
    names['radio']=[_TEXT.render(row,chars,commands)['text'] for row in Bank(archive[416]).words]
    names['swarm']=[decode(Bank(archive[171]).words[11])]
    names['safari_area']=[decode(row) for row in Bank(archive[428]).words]
    names['safari_object']=[decode(row) for row in Bank(archive[430]).words[14:38]]
    return facts


def normalized_rows(facts):
    """Return numerical facts independently of translated names or line wrapping."""
    graph=sorted((c['id'],e['id'],tuple(sorted({p['reference'] for p in e['pages']})))
                 for c in facts['guide'] for e in c['entries'])
    return dict(species=facts['species'],evolutions=facts['evolutions'],trainers=facts['trainers'],
                encounters=facts['encounters'],guide=graph,
                **{key:facts.get(key,[]) for key in ('headbutt','contest','safari','weights')})


def _name(facts,kind,number):
    try:return facts['names'][kind][number]
    except (IndexError,KeyError) as exc:raise ValueError(f'native {kind} name missing for {number}') from exc


def _paragraphs(entry):
    """Rejoin screen-wrapped text without inventing paragraph boundaries."""
    paragraphs=[]
    for page in entry['pages']:
        for line in page['lines']:
            if line.startswith('- ') or not paragraphs:paragraphs.append(line)
            else:paragraphs[-1]+=' '+line
    return paragraphs


def pdf_text(text):
    """Expand native PK/MN ligatures and use portable, meaningful sex tokens."""
    return unicodedata.normalize('NFKC',str(text).replace('₧₦','Pokémon').replace('♀','(F)').replace('♂','(M)'))


def render_facts(locale,facts,baseline,contract,output,*,_player_package=False,_shared_guides=False):
    """Render already-read facts; render_manuals authenticates cartridge inputs."""
    import reportlab
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
    from io import BytesIO
    _need(reportlab.Version=='4.4.9','ReportLab 4.4.9 required')
    words=load_player_documents(locale) if (_player_package or _shared_guides) else load_documents(locale);label=lambda key:words['d:label:'+key];output=Path(output)
    if output.exists() or output.is_symlink():raise FileExistsError(output)
    fontroot=Path(reportlab.__file__).parent/'fonts'
    for name,file in [('SGPDoc','Vera.ttf'),('SGPDocBold','VeraBd.ttf')]:
        if name not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont(name,str(fontroot/file)))
    st=getSampleStyleSheet()
    st.add(ParagraphStyle(name='BodyDoc',fontName='SGPDoc',fontSize=9,leading=13,spaceAfter=8,textColor=colors.HexColor('#26343A')))
    st.add(ParagraphStyle(name='CellDoc',parent=st['BodyDoc'],fontSize=7,leading=10,spaceAfter=0))
    st.add(ParagraphStyle(name='MetaDoc',parent=st['BodyDoc'],fontSize=7,leading=10,textColor=colors.HexColor('#52646A')))
    for key in ['Title','Heading1','Heading2']:
        st[key].fontName='SGPDocBold';st[key].textColor=colors.HexColor('#16656B');st[key].keepWithNext=True
    st['Title'].fontSize=25;st['Title'].leading=30;st['Title'].spaceAfter=18
    st['Heading2'].fontSize=13;st['Heading2'].leading=17;st['Heading2'].spaceBefore=10
    def p(text,style='BodyDoc'):
        text=pdf_text(text)
        supported=pdfmetrics.getFont('SGPDoc').face.charToGlyph
        _need(all(c.isspace() or ord(c) in supported for c in text),'unsupported PDF font glyph')
        value=escape(text).replace('\n','<br/>')
        value=re.sub(r'(https://[^\s<>]+)',r'<link href="\1" color="#16656B">\1</link>',value)
        return Paragraph(value,st[style])
    width=A4[0]-84
    def table(headers,rows,weights=None):
        if not rows:return [p(label('none'))]
        weights=weights or [1]*len(headers)
        data=[[p(x,'CellDoc') for x in headers]]+[[p(x,'CellDoc') for x in row] for row in rows]
        t=Table(data,colWidths=[width*x/sum(weights) for x in weights],repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E8F2F2')),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F8F5ED')]),
            ('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),0.7,colors.HexColor('#BC8D27')),
            ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
        return [t,Spacer(1,10)]
    version=contract['version'];target=contract['targets'][locale]
    titles=[label(k) for k in ('installation','news','events','pokemon','locations','evolutions','items','trainers','gameplay')]
    stories=[[p(title,'Title'),p(label('candidate_note'),'MetaDoc')] for title in titles]
    for index in range(14):
        text=words[f'd:install:{index}'].format(version=version,language=locale,target_sha256=target['sha256'],
            target_name=target.get('name',''),target_bytes=target['bytes'])
        stories[0].append(p(text,'Heading2' if index in (0,11,12) else 'BodyDoc'))
        if index==11:
            byid={r['id']:r for r in contract['sources']}
            if _player_package:
                source=byid[CLEAN_IDS[locale]]
                stories[0]+=table([label('source'),'SHA-256','Patch'],
                    [(source['label'],source['sha256'],f'Patch/Sacred-Gold-Plus-{version}-{locale}.xdelta')],[2,4,3])
            else:
                routes=[byid[i] for i in contract['routes_by_target'][locale]]
                stories[0]+=table([label('source'),'SHA-256',label('item')],
                    [(r['label'],r['sha256'],'Patch/'+r['id']+'.xdelta') for r in routes],[2,4,3])
    stories[0].append(p(words['d:install:14']))
    for i in range(46):
        stories[1].append(p(words[f'd:news:{i}'],'Heading2' if i in (0,2,6,11,17,22,25,30,34,38,43) else 'BodyDoc'))
    def write_stories(stories,start=0):
        output.parent.mkdir(parents=True,exist_ok=True)
        paths=[output/(name+'-'+version+'-'+locale+'.pdf') for name in FILENAMES[start:start+len(stories)]]
        with tempfile.TemporaryDirectory(prefix='.manuals-',dir=output.parent) as temp:
            temp=Path(temp)
            for index,path in enumerate(paths):
                def footer(canvas,doc):
                    canvas.setStrokeColor(colors.HexColor('#BC8D27'));canvas.line(42,37,A4[0]-42,37)
                    canvas.setFont('SGPDoc',7);canvas.setFillColor(colors.HexColor('#52646A'))
                    canvas.drawString(42,24,'SACRED GOLD PLUS '+version+' | '+locale)
                    canvas.drawRightString(A4[0]-42,24,label('page')+' '+str(doc.page))
                with (temp/path.name).open('xb') as stream:
                    document=SimpleDocTemplate(stream,pagesize=A4,leftMargin=42,rightMargin=42,topMargin=44,bottomMargin=50,
                        invariant=1,title='Sacred Gold Plus '+version+' - '+titles[start+index],author='Sacred Gold Plus contributors')
                    document.build(stories[index],onFirstPage=footer,onLaterPages=footer)
            output.mkdir(exist_ok=False)
            for path in paths:os.link(temp/path.name,path)
        return paths
    if _player_package:
        from distribution.pack import image_file_bytes
        st.add(ParagraphStyle(name='WalkDoc',parent=st['BodyDoc'],fontSize=10,leading=14,spaceAfter=9))
        st.add(ParagraphStyle(name='CodeDoc',parent=st['BodyDoc'],fontName='Courier',fontSize=8,leading=12))
        def w(key,style='WalkDoc'):
            return p(words['d:walk:'+key].format(package_revision=contract.get('package_revision','r2')),style)
        def picture(name,picture_width):
            stream=BytesIO(image_file_bytes(name));shot=Image(stream)
            shot._sgp_source=stream;shot.drawHeight*=picture_width/shot.drawWidth
            shot.drawWidth=picture_width;shot.hAlign='CENTER'
            return shot
        patch=f'Patch/Sacred-Gold-Plus-{version}-{locale}.xdelta'
        source=next(row for row in contract['sources'] if row['id']==CLEAN_IDS[locale])
        folder=contract.get('locales',{}).get(locale,{}).get('folder',locale)
        walk=[p(titles[0],'Title'),p(words['d:install:0'].format(version=version),'MetaDoc'),
              w('h1','Heading2'),w('download'),
              p('https://github.com/Umberto-DEV/sacred-gold-plus/releases'),w('extract')]
        walk+=table(['',''],[
            ('DIR',folder+'/'),('PDF',f'Installation-{version}-{locale}.pdf'),
            ('PDF',f'Whats-New-{version}-{locale}.pdf'),('DIR','Patch/'),
            ('Patch',patch),('DIR','Cheats/'),('DIR','Credits-and-Licenses/')],[1,8])
        walk += [w('files'),p(words['d:install:3'],'WalkDoc'),w('backup'),
                 PageBreak(),w('h2','Heading2'),w('sha_what'),w('sha_where'),
                 w('browser_h','Heading2'),w('browser'),
                 p('https://emn178.github.io/online-tools/sha256_checksum.html'),w('mac_h','Heading2'),w('mac'),
                 p('shasum -a 256 "/path/to/HeartGold.nds"','CodeDoc'),
                 w('windows_h','Heading2'),w('windows'),
                 p(r"(Get-FileHash -Algorithm SHA256 -LiteralPath 'C:\Games\HeartGold.nds').Hash",'CodeDoc'),
                 w('hash_warn'),PageBreak(),w('h3','Heading2'),w('choose'),
                 w('ref_a','Heading2'),p(source['label'],'WalkDoc'),
                 p('SHA-256: '+source['sha256'],'CodeDoc'),p(patch,'CodeDoc'),w('stop'),
                 p(words['d:install:2'],'WalkDoc'),p(words['d:install:10'],'WalkDoc'),
                 PageBreak(),w('h4','Heading2'),w('apply_intro'),
                 p('https://www.marcrobledo.com/RomPatcher.js/'),w('select'),
                 picture('install-rom-patcher.jpg',390),Spacer(1,9),w('settings'),
                 picture('install-patcher-settings.jpg',220),Spacer(1,7),
                 w('capture','MetaDoc'),w('save_output'),
                 PageBreak(),w('h5','Heading2'),w('verify'),w('ref_b','Heading2'),
                 p(words['d:install:13'].format(version=version,language=locale,
                     target_sha256=target['sha256'],target_name=target['name'],target_bytes=target['bytes']),'WalkDoc'),
                 w('firstplay'),PageBreak(),w('h6','Heading2'),w('copy'),
                 p('SGP-update-test.nds\nSGP-update-test.sav','CodeDoc'),
                 p(words['d:install:7'],'WalkDoc'),p(words['d:install:8'],'WalkDoc'),
                 w('update_note'),p(words['d:install:9'],'WalkDoc'),
                 PageBreak(),w('h7','Heading2'),w('trouble'),w('help'),
                 p('https://github.com/Umberto-DEV/sacred-gold-plus/issues'),
                 w('offline_h','Heading2'),w('offline'),p('https://github.com/jmacd/xdelta'),
                 p(f'xdelta3 -d -D -R -s "source.nds" "{patch}" "patched.nds"','CodeDoc'),
                 p(f'.\\xdelta3.exe -d -D -R -s "source.nds" "{patch}" "patched.nds"','CodeDoc'),
                 Spacer(1,12),p(label('credits'),'Heading2'),
                 p(label('credits_note'),'MetaDoc'),p(words['d:news:45'],'MetaDoc')]
        stories[0]=walk
        return write_stories(stories[:2])
    def guide_section(story,cids):
        for category in facts['guide']:
            if category['id'] not in cids:continue
            story.append(p(category['title'],'Heading1'))
            for entry in sorted(category['entries'],key=lambda row:row['id']):
                story.append(p(entry['title'],'Heading2'));story.extend(p(t) for t in _paragraphs(entry))
    for i,cids in [(2,{3}),(6,{2}),(8,{1,2,3,4})]:
        stories[i].append(p(label('event_note')));guide_section(stories[i],cids)
    for i in (3,4,5,7):stories[i].append(p(label('same_data')))
    original={r['id']:r for r in baseline['species']}
    for row in facts['species']:
        before=original.get(row['id']);_need(before is not None,'reference species row missing')
        if row==before:continue
        stories[3].append(p(f'{row["id"]:03d} '+_name(facts,'pokemon',row['id']),'Heading2'));details=[]
        if row['types']!=before['types']:
            details.append((label('type'),' / '.join(_name(facts,'type',x) for x in before['types']),
                            ' / '.join(_name(facts,'type',x) for x in row['types'])))
        for n,(old,new) in enumerate(zip(before['stats'],row['stats'])):
            if old!=new:details.append((_name(facts,'stat',n),str(old),str(new)))
        if row['abilities']!=before['abilities']:
            details.append((label('ability'),' / '.join(_name(facts,'ability',x) for x in before['abilities'] if x),
                            ' / '.join(_name(facts,'ability',x) for x in row['abilities'] if x)))
        if details:stories[3]+=table([label('parameter'),label('before'),label('after')],details,[2,3,3])
        if row['learnset']!=before['learnset']:
            stories[3]+=table([label('level'),label('move')],[(str(l),_name(facts,'move',m)) for l,m in row['learnset']],[1,4])
    def method_name(method,time):
        native_move=lambda number:_name(facts,'move',number)
        names={0:label('grass'),1:label('water'),2:native_move(249),3:label('old_rod'),4:label('good_rod'),5:label('super_rod')}
        if method in names:return names[method]
        if method in (6,7):return _name(facts,'radio',0)+' '+str(method-5)
        if method in (8,9,10):return _name(facts,'swarm',0)+' / '+names[{8:0,9:1,10:time}[method]]
        return names[4 if method==11 else 5]+' / '+label('night')
    stories[4]+=[p(label('coverage'),'Heading2'),p(label('encounter_note')),p(label('event_note'))]
    for radio in (10,11):
        if len(facts['names'].get('radio',[]))>radio:
            stories[4].append(p(_name(facts,'radio',radio).replace('\\n',' ').replace('\\r',' ')))
    locrows=[]
    for mid,section,bank,method,time,slot,species,low,high,rate in facts['encounters']:
        period=label({0:'morning',1:'day',2:'night'}[time]) if method==0 else ''
        selector=('land' if method in (0,6,7,8) else 'surf' if method in (1,9)
                  else 'rock' if method==2 else 'fish')
        weight=facts['weights'][selector][slot]
        locrows.append((_name(facts,'map',section)+f' #{mid}',method_name(method,time)+((' / '+period) if period else ''),
                        str(slot+1),f'{species:03d} '+_name(facts,'pokemon',species),str(low),str(high),str(weight)))
    stories[4]+=table([label('map'),label('method'),'#',label('species'),
                      label('minimum'),label('maximum'),'%'],locrows,[3,3,0.8,3,1.4,1.4,0.8])
    if facts.get('headbutt'):
        stories[4]+=[p(_name(facts,'move',29),'Heading1'),p(label('headbutt_note'))]
        stories[4]+=table([label('map'),label('method'),'#',label('species'),
                          label('minimum'),label('maximum'),'%'],
            [(_name(facts,'map',section)+f' #{mid}',str(group+1),str(slot+1),_name(facts,'pokemon',species),
              str(low),str(high),str(facts['weights']['headbutt'][slot]))
             for mid,section,group,slot,species,low,high in facts['headbutt']],[3,1.2,0.8,3,1.4,1.4,0.8])
    if facts.get('contest'):
        stories[4]+=[p(_name(facts,'item',499),'Heading1'),p(label('contest_note'))]
        stories[4]+=table([label('method'),label('species'),label('minimum'),label('maximum'),'%'],
            [(str(group),_name(facts,'pokemon',species),str(low),str(high),str(rate))
             for group,slot,species,low,high,rate,score in facts['contest']],[1,3,1,1,1])
    if facts.get('safari'):
        stories[4]+=[p('Safari','Heading1'),p(label('safari_note'))]
        objects=[(str(group+1),' / '.join(_name(facts,'safari_object',i) for i in range(group*3,group*3+3)))
                 for group in range(4)]
        stories[4]+=table([label('number'),label('item')],objects,[1,5])
        for area in sorted({row[0] for row in facts['safari']}):
            stories[4].append(p(_name(facts,'safari_area',area),'Heading2'))
            safari_rows=[]
            # Base duplicate slots may share display rows; bonus priority remains explicit.
            seen=set()
            for a,method,time,slot,bonus,species,level,gate in facts['safari']:
                if a!=area:continue
                key=(method,time,bonus,slot if bonus else 0,species,level,gate)
                if key in seen:continue
                seen.add(key)
                kind=0 if method==0 else (1 if method==1 else method+1)
                period=label({0:'morning',1:'day',2:'night'}[time])
                condition=' + '.join(f'[{gate[i]}] >= {gate[i+1]}' for i in (0,2) if gate[i]) or '-'
                if bonus:condition=f'{slot+1}: '+condition
                safari_rows.append((method_name(kind,-1)+' / '+period,_name(facts,'pokemon',species),str(level),condition))
            stories[4]+=table([label('method'),label('species'),label('level'),label('parameter')],safari_rows,[3,3,1,3])
    guide_section(stories[4],{3})
    evorows=[]
    for species,slot,method,param,target_id in facts['evolutions']:
        names=lambda kind,number:_name(facts,kind,number)
        evorows.append((f'{species:03d} '+names('pokemon',species),evolution_description(method,param,names,locale),
                        f'{target_id:03d} '+names('pokemon',target_id)))
    stories[5]+=table([label('species'),label('parameter'),label('target')],evorows,[2,4,2])
    stories[7].append(p(words['d:news:28']))
    for trainer in facts['trainers']:
        if not trainer['party']:continue
        title=f'{trainer["id"]:03d} '+_name(facts,'class',trainer['class'])+' '+_name(facts,'trainer',trainer['id'])
        stories[7].append(p(title,'Heading2'));team=[]
        for mon in trainer['party']:
            name=_name(facts,'pokemon',mon['species'])+(f' [{mon["form"]}]' if mon['form'] else '')
            moves=' / '.join(_name(facts,'move',m) for m in mon['moves'] if m) or label('level')
            if mon['plus_moves']!=mon['moves']:
                moves+='\nPlus: '+' / '.join(_name(facts,'move',m) for m in mon['plus_moves'] if m)
            team.append((name,f'{mon["level"]} / {mon["plus_level"]}',
                         _name(facts,'item',mon['item']) if mon['item'] else label('none'),moves))
        stories[7]+=table([label('species'),label('level')+' / Plus',label('item'),label('move')],team,[2,1,2,4])
    for index,story in enumerate(stories):
        if index==1:continue  # The news source already contains its full credits.
        story += [Spacer(1,18),p(label('credits'),'Heading2'),p(label('credits_note'),'MetaDoc'),p(words['d:news:45'],'MetaDoc')]
    return write_stories(stories[2:],2) if _shared_guides else write_stories(stories)


def render_manuals(locale: str,candidate: bytes,reference: bytes,charmap: Path,
                   contract: dict,output: Path) -> list[Path]:
    """Authenticate inputs and create nine new PDFs, never replacing existing files."""
    validate_inputs(locale,candidate,reference,contract);load_documents(locale)
    facts=read_facts(candidate,charmap);baseline=read_facts(reference,charmap,include_guide=False)
    return render_facts(locale,facts,baseline,contract,output)



def render_player_documents(locale: str,candidate: bytes,reference: bytes,charmap: Path,
                            contract: dict,output: Path) -> list[Path]:
    """Authenticate and render only r2 installation/news PDFs with one clean route.

    The signature matches render_manuals for callers. No cartridge tables or
    Guide prose are needed, so charmap is intentionally not read in this mode.
    Historical nine-document rendering and its copy remain unchanged.
    """
    target=validate_inputs(locale,candidate,reference,contract)
    name=target.get('name','')
    _need(isinstance(name,str) and re.fullmatch(r'[^/\\\x00-\x1f]+\.nds',name)
          and name not in ('.','..') and contract['version'] in name,'player target filename')
    _need(CLEAN_IDS[locale] in contract['routes_by_target'][locale],'player clean source route')
    load_player_documents(locale)
    return render_facts(locale,None,None,contract,output,_player_package=True)



def render_shared_guides(locale: str,candidate: bytes,reference: bytes,charmap: Path,
                         contract: dict,output: Path) -> list[Path]:
    """Create only the seven shared English guides with current r2 notices."""
    _need(locale=='EN','shared guides must use English')
    validate_inputs(locale,candidate,reference,contract);load_player_documents(locale)
    facts=read_facts(candidate,charmap);baseline=read_facts(reference,charmap,include_guide=False)
    return render_facts(locale,facts,baseline,contract,output,_shared_guides=True)
