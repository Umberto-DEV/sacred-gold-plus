#!/usr/bin/env python3
"""Read the exact pivot prefix and dispatch order; no compiler or guest CPU.

Static ordering rejects an unsupported late-consumer premise. It neither proves
healing behavior nor fixes the two installed U-turn defects recorded separately.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import mmap
import re
import struct
import subprocess


HERE=Path(__file__).resolve();SOURCE=HERE.parents[3]
PINS={'productive':'cb614ad23449d5852b40321dc409c4143872b35c','heartgold':'6bf138d6035aa6b43d6f8f4132a12df70f86dcec'}
REFERENCE_FILES={'productive': {'src/battle/battle_util.c': '108b7fa3fa8be1f5352f27136ab578e75ea44f7ad8920f053e16223492757f57',
                'src/battle/battle_command.c': '5ccb3c930e9dbb4e40f9fd150e28cc7cf926b573f83001ba179423b60524fffb',
                'asm/overlay_12_battle_command.s': 'aa4c6d072fa8e37c8f09176e4038b8a573ca5cd22812fc3038d3d9cf219ce530',
                'asm/macros/btlcmd.inc': '963af046dfc94d8c84850fc284a162a71f66dc5aa05f5a6d49f548d8fab4d6ad',
                'include/constants/battle_script.h': 'bc0ca40abb72d8b7fa58f39ad2a89372c5b44bc3735b2a048a1355811db49d79',
                'include/constants/battle.h': '87adfe3abd148d74f72a540911ec84aac8ede3477032006878469866b6ade3b0',
                'include/constants/items.h': '20576a5dc04bd40cb1d212f1dad2de8e0083cf966e9535e3c10baac36cbd7193',
                'include/battle/battle_util.h': '315d533bd403b029666940eb30c986b360a826d69b3d171da9b51572fe30ddc5',
                'include/constants/battle_subscript.h': '533a95feb38b9035061fb52f1c802c2a4af9847bfb164ea6310d4fd627b95bf3'},
 'heartgold': {'src/battle/overlay_12_0224E4FC.c': 'be2d44db8e4ba6d1ef387798defcbc502e812afc723608b75d35c96ae2fd4958',
               'src/battle/battle_command.c': '42d3626a67a1d8b7dadb18330b2a8872e2da26b5a50aa4f96af912cf6332ac8e',
               'asm/overlay_12_battle_command.s': '4e9ae08563e7583973020aa1bb24d0629a74495e78d3ae3418d11b80a2744bb3',
               'asm/macros/btlcmd.inc': 'a602c950bef09c3a26f8509f16ceab98ece2e8554bedc36a2bcfd53796f1cbc6',
               'include/constants/battle_script.h': 'bc0ca40abb72d8b7fa58f39ad2a89372c5b44bc3735b2a048a1355811db49d79',
               'include/constants/battle.h': 'c5f93c13fef588e4aa7a5e96efd802ce0bda74ea0667ad22cf40900a1d3b5f51',
               'include/constants/items.h': '20576a5dc04bd40cb1d212f1dad2de8e0083cf966e9535e3c10baac36cbd7193',
               'files/battledata/script/subscript/subscript_0175_PivotMove.s': '8a21e2c1e2dad015a00cced221cbc7e5652eb4bc5ccb2544aae252aec488a19b',
               'files/battledata/script/effect_script/effect_script_0228.s': 'a66c0fda61bda401c471f5e08db31067c00d662697e711c20a7e54e07c0badbd',
               'include/battle/overlay_12_0224E4FC.h': 'cc200e48a3dadc859004615f4e30d061e99921d438acec5727e25e1fce7e6519',
               'include/constants/battle_subscript.h': '533a95feb38b9035061fb52f1c802c2a4af9847bfb164ea6310d4fd627b95bf3'}}
DEFINITIONS={'productive': {'CheckItemEffectOnUTurn': {'file': 'src/battle/battle_util.c',
                                           'bytes': 2615,
                                           'sha256': '402f0c5e02dd1a52194608edc68097d43415a4e6470e288169eb4e022218eabd',
                                           'line': 6171},
                'BtlCmd_CheckItemHoldEffectOnUTurn': {'file': 'src/battle/battle_command.c',
                                                      'bytes': 320,
                                                      'sha256': '77da05c9c5897f64a8b34f80063c03326a22a2fb03b997840973dc42989ac1d9',
                                                      'line': 5616}},
 'heartgold': {'CheckItemEffectOnUTurn': {'file': 'src/battle/overlay_12_0224E4FC.c',
                                          'bytes': 2614,
                                          'sha256': '16d9fc49eeba39e4dc135ff560cb7b105aa62010df4e4603ec27f40c252103e3',
                                          'line': 6171},
               'BtlCmd_CheckItemHoldEffectOnUTurn': {'file': 'src/battle/battle_command.c',
                                                     'bytes': 320,
                                                     'sha256': '77da05c9c5897f64a8b34f80063c03326a22a2fb03b997840973dc42989ac1d9',
                                                     'line': 5614}}}
WIDTHS={200:3,116:4,197:2,61:2,213:2}
JUMP_ARGUMENTS={200:1,116:2,197:0,213:0}
TABLE=0x226c6c8;HANDLER=0x2245228;HANDLER_END=0x224525c;CONSUMER=0x2257fa0
HANDLER_SHA='f1fde9c9eda08a9112b9c1d09c41c66cf949b6910adb20a4acf6674f8070cd72'
LOOKAHEAD_SHA='5cc3fb074a0f3f55b3c2419c637877ce91c9b365dd4b73f21bdbd2ee6218ff4a'
SCRIPT_SHA='eaa254c435e16397b233c8f3e796f1655003358e4252bcc57352f3ca89b58c9a'


def need(value,message):
    if not value:raise ValueError(message)


def sha(data):return hashlib.sha256(data).hexdigest()


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def parse_command_table(text):
    """Bounded single .word table, retaining rows with inline ASM comments."""
    need(type(text)is str and len(text)<=2*1024**2,'bounded assembly table source')
    lines=[line.split(';',1)[0].strip()for line in text.splitlines()]
    starts=[i for i,line in enumerate(lines)if line=='sBattleScriptCommandTable:']
    need(len(starts)==1,'unique actual command table label')
    names=[]
    for line in lines[starts[0]+1:]:
        if not line:continue
        if line.startswith('.public ')or re.fullmatch(r'[A-Za-z_]\w*:',line):break
        match=re.fullmatch(r'\.word\s+(BtlCmd_\w+)',line)
        need(match is not None,'single named function per command-table row')
        names.append(match.group(1));need(len(names)<=512,'bounded command table')
    need(bool(names),'nonempty command table')
    return names


def decode_prefix(words,stop):
    need(type(words)is list and 1<=len(words)<=2048 and all(type(x)is int and 0<=x<=0xffffffff for x in words),'typed bounded script words')
    need(type(stop)is int and 0<stop<len(words)and stop<=64,'bounded prefix endpoint')
    rows=[];cursor=0
    while cursor<stop:
        opcode=words[cursor];need(opcode in WIDTHS,'unsupported prefix opcode')
        width=WIDTHS[opcode];need(cursor+width<=stop,'prefix ends inside a command')
        row=dict(word=cursor,opcode=opcode,arguments=words[cursor+1:cursor+width],next_word=cursor+width)
        if opcode in JUMP_ARGUMENTS:
            value=row['arguments'][JUMP_ARGUMENTS[opcode]];relative=value-(1<<32)if value&(1<<31)else value
            target=cursor+width+relative
            need(cursor<target<len(words),'bounded forward prefix branch')
            row['jump_word']=target
        rows.append(row);cursor+=width
    starts={row['word']for row in rows}|{stop}
    if words[-1]==224:starts.add(len(words)-1)
    need(all(row.get('jump_word',stop)in starts for row in rows),'prefix branch targets command boundaries or final End')
    return rows


def require_order(rows,words,stop,expected_var=43):
    need(type(expected_var)is int and 0<=expected_var<=255,'typed source TEMP_DATA variable')
    selected=[i for i,row in enumerate(rows)if row['opcode']==213]
    need(len(selected)==1,'one real pivot item command, not an operand/script ID')
    index=selected[0];consumer=rows[index]
    need(index+1<len(rows),'item command followed by CallFromVar')
    call=rows[index+1]
    need(call['word']==consumer['next_word']and call['opcode']==61 and call['arguments']==[expected_var]
         and call['next_word']==stop and consumer['jump_word']==stop,'both item-command branches join before snapshot')
    need(words[stop:stop+4]==[50,7,68,1<<16],'project snapshot marker begins after the item request/call')
    return dict(consumer_command_word=consumer['word'],CallFromVar_word=call['word'],snapshot_word=stop,
        false_path_join=consumer['jump_word'],consumer_before_snapshot=True,healing_observed=False,
        scope='Static one-prefix invocation only; CallFromVar transport and whole-pivot lifetime are not executed')


def bl_target(blob,pc):
    need(type(blob)is bytes and len(blob)==4 and type(pc)is int and pc%2==0 and 0<=pc<=0xffffffff,'typed Thumb BL bytes/site')
    hi,lo=struct.unpack('<HH',blob)
    need(hi&0xf800==0xf000 and lo&0xf800==0xf800,'Thumb1 BL, not BLX or data')
    value=((hi&0x7ff)<<12)|((lo&0x7ff)<<1)
    if value&(1<<22):value-=1<<23
    target=pc+4+value;need(0<=target<=0xffffffff,'nonwrapping Thumb BL target')
    return target


def locate_handler(image,base,profile,opcode=213):
    """Locate an exact profile and its consecutive dispatch entries, no shift guess."""
    need(type(image)is bytes and len(image)<=512*1024 and type(profile)is bytes
         and 4<=len(profile)<=128 and len(profile)%2==0,'bounded exact handler search')
    need(type(base)is int and 0<=base<=0xffffffff-len(image)and base%4==0
         and type(opcode)is int and 0<=opcode<=511,'typed legacy overlay geometry')
    offsets=[i for i in range(0,len(image)-len(profile)+1,2)if image[i:i+len(profile)]==profile]
    need(len(offsets)==1,'unique exact legacy handler profile')
    need(offsets[0]+len(profile)+2<=len(image),'legacy successor has an instruction halfword inside overlay')
    entry=base+offsets[0];pair=struct.pack('<II',entry|1,(entry+len(profile))|1)
    pointers=[i for i in range(opcode*4,len(image)-7,4)if image[i:i+8]==pair]
    need(len(pointers)==1,'unique aligned consecutive legacy dispatch pair')
    return dict(handler=entry,table=base+pointers[0]-opcode*4,opcode=opcode,
        bytes=len(profile),sha256=sha(profile),comparison_bytes_normalized=False)


def references(reference,heartgold_ref):
    reader=load(SOURCE/'features/trainer-strategy/tools/confronta_box_move_pret.py','pivot_source_global_definition')
    texts={};defs={};identities={}
    for kind,root in(('productive',reference),('heartgold',heartgold_ref)):
        root=Path(root).resolve();actual=Path(subprocess.check_output(['git','-C',str(root),'rev-parse','--show-toplevel'],text=True).strip()).resolve()
        need(actual==root and subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()==PINS[kind]
             and not subprocess.check_output(['git','-C',str(root),'status','--porcelain']),'clean pinned reference root '+kind)
        texts[kind]={}
        for name,digest in REFERENCE_FILES[kind].items():
            data=(root/name).read_bytes();need(sha(data)==digest,'pinned source file '+kind+'/'+name);texts[kind][name]=data.decode('utf8')
        defs[kind]={}
        for name,expected in DEFINITIONS[kind].items():
            d=reader.definition(texts[kind][expected['file']],name);body=d['text'].encode()
            need((len(body),sha(body))==(expected['bytes'],expected['sha256']),'complete source definition '+kind+'/'+name);defs[kind][name]=d['text']
        identities[kind]=dict(commit=PINS[kind],files=REFERENCE_FILES[kind],definitions=DEFINITIONS[kind])
    name='BtlCmd_CheckItemHoldEffectOnUTurn'
    need(defs['productive'][name]==defs['heartgold'][name],'same handler C body across pinned references')
    name='CheckItemEffectOnUTurn';old=defs['productive'][name];new=defs['heartgold'][name]
    token='ctx->trainerAIData.moveData[ctx->moveNoCur].flags'
    need(old.count(token)==1 and new==old.replace(token,token[:-5]+'unkB',1),'sole consumer drift is StickyBarb flags-to-unkB spelling')
    first=old.index('    if (itemAttacker == HOLD_EFFECT_HP_RESTORE_ON_DMG')
    last=old.index('\n    if (itemAttacker == HOLD_EFFECT_HP_DRAIN_ON_ATK',first)
    need(old[first:last]in new,'unchanged Shell Bell source branch')
    tables={kind:parse_command_table(t['asm/overlay_12_battle_command.s'])for kind,t in texts.items()}
    need(all(len(t)==225 and t[213]=='BtlCmd_CheckItemHoldEffectOnUTurn'for t in tables.values()),'source command213 table binding including commented rows')
    macro='    .macro TriggerHeldItemOnPivotMove jump_no_effect\n    .long 213\n'
    need(all(macro in t['asm/macros/btlcmd.inc']for t in texts.values()),'opcode213 macro identity')
    for t in texts.values():
        for file,name,value in(('include/constants/battle_script.h','BSCRIPT_VAR_TEMP_DATA','43'),
             ('include/constants/battle_subscript.h','BATTLE_SUBSCRIPT_RESTORE_A_LITTLE_HP','213'),
             ('include/constants/items.h','HOLD_EFFECT_HP_RESTORE_ON_DMG','88')):
            need(len(re.findall(r'^#define\s+'+name+r'\s+'+value+r'\s*$',t[file],re.M))==1,'source constant '+name)
    pivot=texts['heartgold']['files/battledata/script/subscript/subscript_0175_PivotMove.s']
    need(pivot.index('TriggerHeldItemOnPivotMove')<pivot.index('DeletePokemon'),'newer PRET item-before-switch source order')
    return dict(references=identities,handler_same_C=True,consumer_whole_C_same=False,
        consumer_drift='Only StickyBarb moveData.flags-to-unkB spelling; not a binary identity claim',
        ShellBell_branch_sha256=sha(old[first:last].encode()),opcode=213,healing_script_ID=213,
        distinct_namespaces=True,TEMP_DATA_variable=43,CPU_executed=False,compiler_invoked=False)


def readback(rom,language):
    # Dependencies are deferred so owned parser tests remain stdlib-only.
    shared=load(SOURCE/'features/fairy-ai/tools/attribuisci.py','pivot_qualified_overlay_readback')
    narc=load(SOURCE/'features/borsa/tools/attribuisci.py','pivot_qualified_NARC_readback')
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
    pins=json.loads((SOURCE/'distribution/game-1.3.2-r4.json').read_bytes())['targets'];pin=pins[language]
    with Path(rom).open('rb')as stream,mmap.mmap(stream.fileno(),0,access=mmap.ACCESS_READ)as raw:
        need(len(raw)==pin['bytes']and sha(raw)==pin['sha256'],'exact current '+language+' ROM identity')
        image,record=shared.overlay(raw,12);base=int(record['ram'],16)
        need(base==0x22378c0 and len(image)==0x37380,'exact overlay12 geometry')
        def take(a,n):
            need(base<=a and a+n<=base+len(image),'overlay readback bounds');return image[a-base:a-base+n]
        entries={op:struct.unpack('<I',take(TABLE+op*4,4))[0]for op in(50,57,59,166,168,213,214,224)}
        expected={50:0x223ec85,57:0x223f61d,59:0x223f895,166:0x224428d,168:0x2244345,213:HANDLER|1,214:HANDLER_END|1,224:0x22454cd}
        need(entries==expected,'raw command table213 and independently qualified anchor entries')
        body=take(HANDLER,HANDLER_END-HANDLER);need(sha(body)==HANDLER_SHA,'exact command213 native handler52')
        instructions=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(body,HANDLER))
        need(len(instructions)==22 and sum(i.size for i in instructions)==52,'complete handler instruction coverage')
        calls=[dict(pc=i.address,target=bl_target(bytes(i.bytes),i.address))for i in instructions if i.mnemonic=='bl']
        need([(c['pc'],c['target'])for c in calls]==[(0x2245232,0x2245508),(0x2245238,0x22454e8),(0x2245248,CONSUMER),(0x2245254,0x2245508)],'four actual handler BLs')
        lookahead=take(CONSUMER,768);need(sha(lookahead)==LOOKAHEAD_SHA,'consumer candidate lookahead identity, not function extent')
        members,nrec=narc.raw_archive(raw,'a/0/0/1');script=members[175]
        need(nrec['file_id']==130 and len(members)==297 and len(script)==800 and sha(script)==SCRIPT_SHA,'exact pivot member175 source-recipe identity')
        words=list(struct.unpack('<200I',script));prefix=decode_prefix(words,15);order=require_order(prefix,words,15)
        return dict(ROM=dict(bytes=len(raw),sha256=pin['sha256'],game_code=bytes(raw[12:16]).decode(),revision=raw[30]),overlay=record,
            dispatch_table=TABLE,command_table_entries=entries,handler=dict(ram=HANDLER,bytes=52,code_bytes=52,instruction_starts=22,
                sha256=HANDLER_SHA,code_hex=body.hex(),calls=calls,script_output='CTX+0x138 (r2)',compiled_C_reconstructed=False),
            consumer_candidate=dict(entry=CONSUMER,lookahead_bytes=768,lookahead_sha256=LOOKAHEAD_SHA,
                unclassified_lookahead_hex=lookahead.hex(),whole_function_extent_proven=False),
            script=dict(file_id=130,member=175,bytes=800,sha256=SCRIPT_SHA,member_ROM_offset=nrec['member_rom_offsets'][175],
                prefix=prefix,order=order,final_command_word=199,final_opcode=words[-1]),
            CPU_executed=False,compiler_invoked=False,ROM_written=False,
            scope='Static source/dispatch/handler/prefix only; no healing request executed or whole pivot replayed')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('rom','reference','heartgold-ref','json'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--it-rom',type=Path);a=p.parse_args()
    try:
        out=a.json.resolve();need(out!=SOURCE and SOURCE not in out.parents and not out.exists()and not a.json.is_symlink(),'fresh private order report')
        source=references(a.reference,a.heartgold_ref);rows={'EN':readback(a.rom,'EN')}
        if a.it_rom:
            rows['IT']=readback(a.it_rom,'IT')
            for key in('handler','consumer_candidate'):
                need(rows['EN'][key]==rows['IT'][key],'selected EN/IT component readback equality '+key)
            need(rows['EN']['script']['prefix']==rows['IT']['script']['prefix'],'selected EN/IT prefix order equality')
        result=dict(schema='native-Uturn-ShellBell-static-order-v1',source=source,rows=rows,CPU_executed=False,compiler_invoked=False,
            new_healing_loss_proven=False,game_fix=False,source_sha256={str(p.relative_to(SOURCE)):sha(p.read_bytes())for p in
                (HERE,SOURCE/'features/trainer-strategy/tools/confronta_box_move_pret.py',SOURCE/'features/fairy-ai/tools/attribuisci.py',SOURCE/'features/borsa/tools/attribuisci.py')},
            conclusion='Installed prefix runs the item command before the snapshot. It does not support a late-consumer-after-flinch-clear premise; no universal healing conclusion.')
        with out.open('x')as f:json.dump(result,f,indent=2);f.write('\n')
    except(ValueError,OSError,KeyError,IndexError,subprocess.CalledProcessError)as e:p.exit(2,str(e)+'\n')
    print('Static pivot item-before-snapshot order checked; no CPU/compiler/game change or observed healing claim')


if __name__=='__main__':main()
