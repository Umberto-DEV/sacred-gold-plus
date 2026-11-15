#!/usr/bin/env python3
"""Static ordinary Shell Bell readback, with no compiler or guest execution.

The profile identifies controller37, its consumer and actual item data. It does
not establish a successful caller boundary, healing loss or game correctness.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import mmap
import struct
import subprocess

HERE=Path(__file__).resolve();SOURCE=HERE.parents[3]
PINS={'productive':'cb614ad23449d5852b40321dc409c4143872b35c','heartgold':'6bf138d6035aa6b43d6f8f4132a12df70f86dcec'}
REFERENCE_FILES={'productive': {'src/battle/battle_controller_player.c': 'f7af28b3c492876a56c8a9621c463de71e27d2f04665253bd5abd77b63a7888b', 'include/battle/battle.h': '4842a1f377ddc623a50bf3001f4498864963881c236a3b4c3fad36fe1d04d2ff', 'include/constants/items.h': '20576a5dc04bd40cb1d212f1dad2de8e0083cf966e9535e3c10baac36cbd7193', 'include/constants/battle.h': '87adfe3abd148d74f72a540911ec84aac8ede3477032006878469866b6ade3b0', 'include/constants/moves.h': '72c58ed137cd5737e5c5fb8f43dfe70904f6f09618c75ab7b92b97062444b6d9', 'src/item.c': '6a42fbd23243992fe565d3dfb674aa7d2b3b2cb427fecac9fe26fe5fcbaffff9'}, 'heartgold': {'src/battle/battle_controller_player.c': '18aa8bf286fd80568f8cb8ab521d15ec4715ed46cb399104c196003995e76925', 'include/battle/battle.h': 'e7177c2a2d04ed02f1ecfeb3b6b0d39a4d2cfb98066bfde888b5b1cf4b6159bf', 'include/constants/items.h': '20576a5dc04bd40cb1d212f1dad2de8e0083cf966e9535e3c10baac36cbd7193', 'include/constants/battle.h': 'c5f93c13fef588e4aa7a5e96efd802ce0bda74ea0667ad22cf40900a1d3b5f51', 'include/constants/moves.h': '72c58ed137cd5737e5c5fb8f43dfe70904f6f09618c75ab7b92b97062444b6d9', 'src/item.c': '09e9377f89adc9003711d3dc16a3912e476043a188e3d5c349369cb37f6fda49'}}
DEFINITIONS={'productive': {'TryItemFlinch': {'bytes': 1024, 'sha256': '0de5ec2e43c1110e92f866354ff31c40c8e80785fd046ded2fa2f07a36bd1ed3', 'line': 3825, 'actual_symbol': 'TryItemFlinch'}, 'BattleControllerPlayer_AfterDamage': {'bytes': 4308, 'sha256': 'f3d425e9008f92ef68968caa8c3c66aac4f018789a8b7a8353d4d898031e7bf9', 'line': 2903, 'actual_symbol': 'BattleControllerPlayer_AfterDamage'}, 'BattleControllerPlayer_AfterMoveEffects': {'bytes': 4784, 'sha256': '41c65b77acd96243d0442f730865e859da2e8419dca27bbcddaace1808b2230c', 'line': 3033, 'actual_symbol': 'BattleControllerPlayer_AfterMoveEffects'}, 'BattleControllerPlayer_CheckMultiHit': {'bytes': 1759, 'sha256': 'f21bb36bc0cb79cf2446292da809162a0acfa64e15a82c6b24e7d8c9dfa0982c', 'line': 3166, 'actual_symbol': 'BattleControllerPlayer_CheckMultiHit'}, 'BattleControllerPlayer_FaintAfterMove': {'bytes': 294, 'sha256': '2f67da07cffbb8891399e48042d410fb86743eafa59e2fc9120cbb016168928f', 'line': 3199, 'actual_symbol': 'BattleControllerPlayer_FaintAfterMove'}, 'BattleControllerPlayer_NextMoveTarget': {'bytes': 2771, 'sha256': '610c9bdfb4808efb0ac6443f4bd31a34066c907a1deb54ff47e096b7b10fd2c2', 'line': 3207, 'actual_symbol': 'BattleControllerPlayer_NextMoveTarget'}, 'BattleControllerPlayer_CheckSelfDestruct': {'bytes': 619, 'sha256': 'cbdee15021956e4389eca4b2f09fd99d3320d738a9db653e83b4b9dbd9a8b3b0', 'line': 3261, 'actual_symbol': 'BattleControllerPlayer_CheckSelfDestruct'}, 'BattleControllerPlayer_AfterMoveItems': {'bytes': 235, 'sha256': 'd4d47d02a3ee9a081330de259066558474f199ed48a8e3907c32224a51acf99d', 'line': 3273, 'actual_symbol': 'BattleControllerPlayer_AfterMoveItems'}, 'BattleControllerPlayer_TryAfterMoveItems': {'bytes': 2958, 'sha256': '98a7fd1721d8d9eb1d975e09a9158721a1992aa608474f3b2ef4191a71afa494', 'line': 3870, 'actual_symbol': 'BattleControllerPlayer_TryAfterMoveItems'}, 'TryFaintMon': {'bytes': 1110, 'sha256': '2ba94f20adf3b5405fb0040f065ae2e3dfa6252def466d5c7eaab6c31a65dd4e', 'line': 3658, 'actual_symbol': 'TryFaintMon'}, 'BattleControllerPlayer_UpdateTargetMoveHistory': {'bytes': 3247, 'sha256': '6493bb4ffe4813b2962774d0322ae3299dfb8dab39e0af3fe36d31b1cf4b97b5', 'line': 3705, 'actual_symbol': 'BattleControllerPlayer_UpdateTargetMoveHistory'}}, 'heartgold': {'TryItemFlinch': {'bytes': 1023, 'sha256': '0587015c5be9237f4793240b4465a07db7f920f92bf292fcb49a346ce8699bd4', 'line': 3825, 'actual_symbol': 'TryItemFlinch'}, 'BattleControllerPlayer_AfterDamage': {'bytes': 3928, 'sha256': '81aeba4d4b58302da902b93a12f5a028bcb7b9f106ffa4caf6d251649635e69d', 'line': 2903, 'actual_symbol': 'ov12_0224CAA4'}, 'BattleControllerPlayer_AfterMoveEffects': {'bytes': 4436, 'sha256': '3b18749a0d6f84ca8c17ff301d4cab3698103c7ac465603d6a8db93eb85dddf3', 'line': 3033, 'actual_symbol': 'ov12_0224CC88'}, 'BattleControllerPlayer_CheckMultiHit': {'bytes': 1709, 'sha256': '061af5035262524e66ec13af471d57ba722df58c7f5c8f84a60d49346a9bd128', 'line': 3166, 'actual_symbol': 'ov12_0224CF14'}, 'BattleControllerPlayer_FaintAfterMove': {'bytes': 270, 'sha256': '1c33d43ee4fa7096375f2343894e5d62028fa4b536a2af0e24e749fc69cc4478', 'line': 3199, 'actual_symbol': 'ov12_0224D014'}, 'BattleControllerPlayer_NextMoveTarget': {'bytes': 2560, 'sha256': '778acf7349d5e5a08ffc0f547858e77855e227d8b218132b21f4cbdfd33ecbcd', 'line': 3207, 'actual_symbol': 'ov12_0224D03C'}, 'BattleControllerPlayer_CheckSelfDestruct': {'bytes': 592, 'sha256': '77d1c7abb972265d2b3a25696855ca8faebd7524fbd81e81e1a19491d17e4557', 'line': 3261, 'actual_symbol': 'ov12_0224D1DC'}, 'BattleControllerPlayer_AfterMoveItems': {'bytes': 184, 'sha256': '7d5f57e11483175e8abdd62d3846707e4dc762a0c1648caa4576359d6abcf93b', 'line': 3273, 'actual_symbol': 'ov12_0224D224'}, 'BattleControllerPlayer_TryAfterMoveItems': {'bytes': 2851, 'sha256': 'd5264477099949c1575caa4fac56a0674eb891816424414a69c334b8f72e0360', 'line': 3870, 'actual_symbol': 'ov12_0224E1BC'}, 'TryFaintMon': {'bytes': 1110, 'sha256': '2ba94f20adf3b5405fb0040f065ae2e3dfa6252def466d5c7eaab6c31a65dd4e', 'line': 3658, 'actual_symbol': 'TryFaintMon'}, 'BattleControllerPlayer_UpdateTargetMoveHistory': {'bytes': 3204, 'sha256': '2270feafbdd7e8f36647536c0e7ee4a24e14bdec9141c54d76a4956d48f66759', 'line': 3705, 'actual_symbol': 'ov12_0224DD74'}}}
TABLE=0x226CA90;WRAPPER=0x224D224;CONSUMER=0x224E1BC;END=0x224E384
PROFILE_SHA='16f4fc3e37da48404fea4051c2b27c9905b4fa94c463053306b1343f54aa06be'
CODE_RANGES=((CONSUMER,0x224E20C),(0x224E214,0x224E366))
CONTROLLERS={29:0x224CAA4,31:0x224CC88,32:0x224CF14,34:0x224D014,35:0x224D03C,36:0x224D1DC,37:WRAPPER,39:0x224D23C}


NEUTRAL_SOURCES={'productive': {'src/battle/battle_util.c': {'sha256': '108b7fa3fa8be1f5352f27136ab578e75ea44f7ad8920f053e16223492757f57',
                                             'definitions': {'TrySyncronizeStatus': {'line': 3787,
                                                                                     'bytes': 2827,
                                                                                     'sha256': 'da80de53752105518920491da510c889473d66947a3a9711f9349664d75ecac6',
                                                                                     'symbol': 'TrySyncronizeStatus'},
                                                             'TryUseHeldItem': {'line': 3848,
                                                                                'bytes': 13280,
                                                                                'sha256': '526b83e65f0123c3ec285693a8d198a8ad88722c6c0424dfd899bbc18f4db1dc',
                                                                                'symbol': 'TryUseHeldItem'},
                                                             'CheckUseHeldItem': {'line': 4180,
                                                                                  'bytes': 13104,
                                                                                  'sha256': '6d40c9e34e0638243b71a4231168ef86a10f9a02a787d213358ac01119d92c35',
                                                                                  'symbol': 'CheckUseHeldItem'},
                                                             'CheckItemEffectOnHit': {'line': 4519,
                                                                                      'bytes': 2717,
                                                                                      'sha256': 'b40aebd413aeb275264b2d5559e40e0b77ccc2b3110bc26ac29f64cb423249bf',
                                                                                      'symbol': 'CheckItemEffectOnHit'},
                                                             'Battler_CheckWeatherFormChange': {'line': 5282,
                                                                                                'bytes': 8584,
                                                                                                'sha256': '04bbaa19dd9bd014028c07243058eb5ea4168530de021e2db7724c8aa31d5767',
                                                                                                'symbol': 'Battler_CheckWeatherFormChange'},
                                                             'TryAbilityOnEntry': {'line': 3132,
                                                                                   'bytes': 20416,
                                                                                   'sha256': '6089f016aeb643d8d9eb6c8b792ea3e2ecde921239f3adbe8b21e8434d124d40',
                                                                                   'symbol': 'TryAbilityOnEntry'}}},
                'src/battle/battle_system.c': {'sha256': 'a6d353d6666405029d7adf6280342235c51be2b5daea2af4c977cb5f875739cf',
                                               'definitions': {'BattleSystem_GetMaxBattlers': {'line': 68,
                                                                                               'bytes': 101,
                                                                                               'sha256': '6ce2eea1de72adde37e70d3efd73420e77964ef0b38752731889f1ecb6751640',
                                                                                               'symbol': 'BattleSystem_GetMaxBattlers'},
                                                               'BattleSystem_GetFieldSide': {'line': 273,
                                                                                             'bytes': 158,
                                                                                             'sha256': 'c5fead2649aa3755f6615d0bce2f4bc14544aec1b1575067daf020ce6b904f3a',
                                                                                             'symbol': 'BattleSystem_GetFieldSide'}}},
                'src/battle/battle_controller_player.c': {'sha256': 'f7af28b3c492876a56c8a9621c463de71e27d2f04665253bd5abd77b63a7888b',
                                                          'definitions': {'TryFaintMon': {'line': 3658,
                                                                                          'bytes': 1110,
                                                                                          'sha256': '2ba94f20adf3b5405fb0040f065ae2e3dfa6252def466d5c7eaab6c31a65dd4e',
                                                                                          'symbol': 'TryFaintMon'},
                                                                          'BattleControllerPlayer_UpdateTargetMoveHistory': {'line': 3705,
                                                                                                                             'bytes': 3247,
                                                                                                                             'sha256': '6493bb4ffe4813b2962774d0322ae3299dfb8dab39e0af3fe36d31b1cf4b97b5',
                                                                                                                             'symbol': 'BattleControllerPlayer_UpdateTargetMoveHistory'}}}},
 'heartgold': {'src/battle/overlay_12_0224E4FC.c': {'sha256': 'be2d44db8e4ba6d1ef387798defcbc502e812afc723608b75d35c96ae2fd4958',
                                                    'definitions': {'TrySyncronizeStatus': {'line': 3787,
                                                                                            'bytes': 2815,
                                                                                            'sha256': '483306352938f929511e4c79d85829a068b3f38ce52fd47d938abaa439b4f17d',
                                                                                            'symbol': 'TrySyncronizeStatus'},
                                                                    'TryUseHeldItem': {'line': 3848,
                                                                                       'bytes': 13280,
                                                                                       'sha256': '526b83e65f0123c3ec285693a8d198a8ad88722c6c0424dfd899bbc18f4db1dc',
                                                                                       'symbol': 'TryUseHeldItem'},
                                                                    'CheckUseHeldItem': {'line': 4180,
                                                                                         'bytes': 13104,
                                                                                         'sha256': '6d40c9e34e0638243b71a4231168ef86a10f9a02a787d213358ac01119d92c35',
                                                                                         'symbol': 'CheckUseHeldItem'},
                                                                    'CheckItemEffectOnHit': {'line': 4519,
                                                                                             'bytes': 2716,
                                                                                             'sha256': 'dbfa6f338c7cde25e317ac24fa4fd31f201b8e26c6d9367d45fcae87b445b4bb',
                                                                                             'symbol': 'CheckItemEffectOnHit'},
                                                                    'Battler_CheckWeatherFormChange': {'line': 5282,
                                                                                                       'bytes': 8564,
                                                                                                       'sha256': '12a0feb51897e859826b3e6b2ea92504cb83c9fcc487c05954075ca87405e4d1',
                                                                                                       'symbol': 'Battler_CheckWeatherFormChange'},
                                                                    'TryAbilityOnEntry': {'line': 3132,
                                                                                          'bytes': 20296,
                                                                                          'sha256': '9605cab1884061c36b2a3964db6c2a58f9d05e70dabcd52ebf478f3662451f41',
                                                                                          'symbol': 'TryAbilityOnEntry'}}},
               'src/battle/battle_system.c': {'sha256': 'e64e9a309fac92961a4b37de81754bc891e73577fdae63cc4580be39fa51b70a',
                                              'definitions': {'BattleSystem_GetMaxBattlers': {'line': 68,
                                                                                              'bytes': 101,
                                                                                              'sha256': '6ce2eea1de72adde37e70d3efd73420e77964ef0b38752731889f1ecb6751640',
                                                                                              'symbol': 'BattleSystem_GetMaxBattlers'},
                                                              'BattleSystem_GetFieldSide': {'line': 273,
                                                                                            'bytes': 144,
                                                                                            'sha256': '3cdde8991b8e919dcfae3f08681a4d3e9785200b6ec2082763ef4c378fe195e0',
                                                                                            'symbol': 'BattleSystem_GetFieldSide'}}},
               'src/battle/battle_controller_player.c': {'sha256': '18aa8bf286fd80568f8cb8ab521d15ec4715ed46cb399104c196003995e76925',
                                                         'definitions': {'TryFaintMon': {'line': 3658,
                                                                                         'bytes': 1110,
                                                                                         'sha256': '2ba94f20adf3b5405fb0040f065ae2e3dfa6252def466d5c7eaab6c31a65dd4e',
                                                                                         'symbol': 'TryFaintMon'},
                                                                         'BattleControllerPlayer_UpdateTargetMoveHistory': {'line': 3705,
                                                                                                                            'bytes': 3204,
                                                                                                                            'sha256': '2270feafbdd7e8f36647536c0e7ee4a24e14bdec9141c54d76a4956d48f66759',
                                                                                                                            'symbol': 'ov12_0224DD74'}}}}}
NEUTRAL_PROFILES={'GetMaxBattlers_reused': {'entry': 35891184,
                           'bytes': 4,
                           'sha256': '2640d5fd1ca49974c06fbe29394309f3a9b27280ff43b5c43bf5c93a93e4b1f7',
                           'code_ranges': [[35891184, 35891188]],
                           'scope': 'Existing native4-byte leaf; reads BattleSystem+44, no new execution'},
 'TryFaintMon': {'entry': 35970164,
                 'bytes': 164,
                 'sha256': 'c0acd9a0a49ee5d23ff408e73ef1c389bdf78a0805ad2b86cf887aab89857a00',
                 'code_ranges': [[35970164, 35970314]],
                 'scope': 'Static whole selected profile; faint branch calls LowestFlagNo outside neutral execution '
                          'proposal'},
 'TrySyncronizeStatus': {'entry': 35997056,
                         'bytes': 412,
                         'sha256': 'f38feafc49603dac0fa1077faaca8b51393d2f8cc0f60b34a207e3325ce19811',
                         'code_ranges': [[35997056, 35997456]],
                         'scope': 'Static selected400-code/12-pool profile; weather call may write scratch state'},
 'TryUseHeldItem_effect0_or88': {'entry': 35997468,
                                 'bytes': 1636,
                                 'sha256': '6f1daea4aa514d3ce4512032c52d5c01212a64a944e9ad2dd2deaad606ffd631',
                                 'code_ranges': [[35997468, 35997546], [35999006, 35999012], [35999052, 35999058]]},
 'CheckItemEffectOnHit': {'entry': 36001332,
                          'bytes': 508,
                          'sha256': '982a25ef3c04e17c2458a91c30ed2a3eeb1191ce2609a12c8b79fe1f253e0e69',
                          'code_ranges': [[36001332, 36001808]],
                          'scope': 'Static selected476-code/32-pool profile; no execution or substitute/fieldside '
                                   'model'}}


def need(value,message):
    if not value:raise ValueError(message)


def sha(data):return hashlib.sha256(data).hexdigest()


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def window(image,base,address,size):
    need(type(image)is bytes and len(image)<=512*1024,'bounded byte image')
    need(all(type(v)is int for v in(base,address,size))and 0<=base<=0xffffffff-len(image)
         and 0<=size<=len(image)and base<=address<=address+size<=base+len(image),'nonwrapping image window')
    return image[address-base:address-base+size]


def switch_targets(image,base,table,add_pc,count,starts):
    need(type(count)is int and 1<=count<=16 and type(add_pc)is int and add_pc%2==0,'bounded signed switch')
    need(type(table)is int and table%2==0,'aligned switch halfwords')
    need(type(starts)is set and 0<len(starts)<=4096 and all(type(v)is int and v%2==0 for v in starts),'explicit instruction starts')
    window(image,base,add_pc,2)
    offsets=struct.unpack('<'+'h'*count,window(image,base,table,2*count))
    targets=[add_pc+4+offset for offset in offsets]
    need(all(0<=target<=0xfffffffe and target in starts for target in targets),'switch targets actual instruction starts, never table/pool/BL tail')
    return targets


def literal_word(image,base,pc):
    need(type(pc)is int and pc%2==0,'aligned Thumb literal site')
    half=struct.unpack('<H',window(image,base,pc,2))[0]
    need(half&0xf800==0x4800,'Thumb1 literal LDR')
    address=((pc+4)&~3)+4*(half&255)
    return dict(register=(half>>8)&7,address=address,value=struct.unpack('<I',window(image,base,address,4))[0])


def private_output(path):
    path=Path(path);resolved=path.resolve();source=SOURCE.resolve()
    need(resolved!=source and source not in resolved.parents,'report must be outside source, including resolved parents')
    if path.exists()or path.is_symlink():raise FileExistsError('fresh private JSON path required')
    return resolved


def save_new(path,result):
    with private_output(path).open('x')as output:json.dump(result,output,indent=2);output.write('\n')


def references(reference,heartgold_ref):
    reader=load(SOURCE/'features/trainer-strategy/tools/confronta_box_move_pret.py','ordinary_C_definition_reader')
    definitions={};files={}
    for kind,root in(('productive',reference),('heartgold',heartgold_ref)):
        root=Path(root).resolve()
        def git(*args):return subprocess.check_output(['git','-C',str(root),*args],text=True,timeout=30).strip()
        need(Path(git('rev-parse','--show-toplevel')).resolve()==root and git('rev-parse','HEAD')==PINS[kind]
             and not git('status','--porcelain'),'clean pinned reference '+kind)
        texts={};files[kind]={}
        for file,digest in REFERENCE_FILES[kind].items():
            raw=(root/file).read_bytes();need(sha(raw)==digest,'source dependency '+kind+'/'+file);texts[file]=raw.decode();files[kind][file]=digest
        text=texts['src/battle/battle_controller_player.c'];definitions[kind]={}
        for name,pin in DEFINITIONS[kind].items():
            item=reader.definition(text,pin['actual_symbol'])
            need((item['bytes'],item['sha256'])==(pin['bytes'],pin['sha256']),'complete source definition '+kind+'/'+name)
            definitions[kind][name]={k:item[k]for k in('bytes','sha256','line')}
        consumer=reader.definition(text,DEFINITIONS[kind]['BattleControllerPlayer_TryAfterMoveItems']['actual_symbol'])['text']
        if kind=='productive':old=consumer
        else:
            normalized=old.replace('BattleControllerPlayer_TryAfterMoveItems','ov12_0224E1BC').replace('ctx->attackerAfterMoveState','ctx->unk_30')
            need(normalized==consumer,'consumer alignment with only two explicit identifier substitutions')
    return dict(pins=PINS,files=files,definitions=definitions,
        consumer_identifier_substitutions=['BattleControllerPlayer_TryAfterMoveItems -> ov12_0224E1BC','ctx->attackerAfterMoveState -> ctx->unk_30'],
        scope='Pinned source alignment, not identical raw definitions, original C codegen or ABI proof')


def profile(image):
    blob=window(image,0x22378C0,CONSUMER,END-CONSUMER)
    need(sha(blob)==PROFILE_SHA,'exact selected456-byte consumer profile')
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
    md=Cs(CS_ARCH_ARM,CS_MODE_THUMB);instructions=[]
    for low,high in CODE_RANGES:
        region=window(blob,CONSUMER,low,high-low);decoded=list(md.disasm(region,low))
        need(sum(i.size for i in decoded)==len(region),'complete static code-range disassembly');instructions.extend(decoded)
    starts={i.address for i in instructions};prior=load(HERE.with_name('rileggi_uturn_shellbell.py'),'ordinary_independent_BL_reader')
    calls=[];branches=[];literals=[]
    for ins in instructions:
        data=bytes(ins.bytes);half=struct.unpack_from('<H',data)[0]
        if ins.size==4:
            target=prior.bl_target(data,ins.address);need(ins.mnemonic=='bl'and int(ins.op_str.lstrip('#'),0)==target,'independent BL destination')
            calls.append(dict(pc=ins.address,target=target))
        elif half&0xf800==0x4800:
            literal=literal_word(blob,CONSUMER,ins.address);need(0x224E368<=literal['address']<END,'all profile literals in declared pool');literals.append(dict(pc=ins.address,**literal))
        elif half&0xf800==0xe000 or half&0xf000==0xd000 and (half>>8)&15<14:
            width=11 if half&0xf800==0xe000 else 8;imm=half&((1<<width)-1)
            if imm&(1<<(width-1)):imm-=1<<width
            target=ins.address+4+2*imm;need(target in starts,'direct branch to actual code start');branches.append(dict(pc=ins.address,target=target))
    targets=switch_targets(blob,CONSUMER,0x224E20C,0x224E20A,4,starts)
    need(targets==[0x224E214,0x224E244,0x224E2C4,0x224E348],'four consumer case targets')
    expected={0x224E1C4:0x223A7F0,0x224E1CC:0x2255830,0x224E1D8:0x2255844,0x224E1E6:0x224DC74,0x224E298:0x2253178,0x224E2AE:0x224EB9C,0x224E2CE:0x22527CC,0x224E31C:0x2253178,0x224E332:0x224EB9C}
    need({r['pc']:r['target']for r in calls}==expected,'all selected consumer BLs')
    need(sorted({r['value']for r in literals})==sorted([0x2DB0,0x3044,0xFF7FFFFF,0x213C,0x2D8C,0x215C,0x2D90]),'seven pool values')
    return dict(entry=CONSUMER,profile_end=END,bytes=len(blob),sha256=sha(blob),
        code_ranges=[list(r)for r in CODE_RANGES],code_bytes=sum(b-a for a,b in CODE_RANGES),static_instruction_starts=len(starts),
        switch_table=[0x224E20C,0x224E214],switch_targets=targets,padding=[0x224E366,0x224E368],pool=[0x224E368,END],calls=calls,branches=branches,literals=literals,
        guest_instructions_admitted=False,original_compiler_extent_proven=False,
        scope='Exact static selected profile and code/data partition; no ISA/runtime qualification')


def code_windows(image,base,ranges):
    need(type(ranges)in(list,tuple)and 0<len(ranges)<=32,'bounded explicit code windows')
    result=[];previous=base
    for pair in ranges:
        need(type(pair)in(list,tuple)and len(pair)==2 and all(type(v)is int and v%2==0 for v in pair),'typed halfword code bounds')
        low,high=pair
        need(previous<=low<high,'ordered disjoint nonempty code windows')
        result.append((low,window(image,base,low,high-low)));previous=high
    return result


def neutral_references(reference,heartgold_ref):
    # references() has already authenticated each independent clean Git root.
    reader=load(SOURCE/'features/trainer-strategy/tools/confronta_box_move_pret.py','ordinary_neutral_C_definitions')
    result={}
    for kind,root in(('productive',reference),('heartgold',heartgold_ref)):
        result[kind]={}
        for name,pin in NEUTRAL_SOURCES[kind].items():
            raw=(Path(root)/name).read_bytes();need(sha(raw)==pin['sha256'],'neutral source dependency '+kind+'/'+name)
            definitions={}
            for function,expected in pin['definitions'].items():
                actual=reader.definition(raw.decode(),expected['symbol'])
                need((actual['bytes'],actual['sha256'])==(expected['bytes'],expected['sha256']),'neutral complete definition '+function)
                definitions[function]=expected
            result[kind][name]=dict(sha256=pin['sha256'],definitions=definitions)
    return result


def neutral_profiles(image,base):
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
    decoder=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
    independent=load(HERE.with_name('rileggi_uturn_shellbell.py'),'ordinary_neutral_BL')
    records={}
    for name,pin in NEUTRAL_PROFILES.items():
        entry=pin['entry'];blob=window(image,base,entry,pin['bytes'])
        need(sha(blob)==pin['sha256'],'neutral dependency profile '+name)
        instructions=[]
        for low,part in code_windows(blob,entry,pin['code_ranges']):
            decoded=list(decoder.disasm(part,low));need(sum(i.size for i in decoded)==len(part),'neutral complete selected code disassembly');instructions.extend(decoded)
        starts={i.address for i in instructions};calls=[];branches=[];literals=[]
        for ins in instructions:
            half=struct.unpack_from('<H',bytes(ins.bytes))[0]
            if ins.size==4:
                target=independent.bl_target(bytes(ins.bytes),ins.address)
                need(ins.mnemonic=='bl'and int(ins.op_str.lstrip('#'),0)==target,'neutral raw/Capstone BL agreement');calls.append(dict(pc=ins.address,target=target))
            elif half&0xf800==0x4800:
                literal=literal_word(blob,entry,ins.address)
                need(all(not low<=literal['address']<high for low,high in pin['code_ranges']),'neutral literal is outside selected code');literals.append(dict(pc=ins.address,**literal))
            elif half&0xf800==0xe000 or half&0xf000==0xd000 and (half>>8)&15<14:
                bits=11 if half&0xf800==0xe000 else 8;value=half&((1<<bits)-1)
                if value&(1<<(bits-1)):value-=1<<bits
                target=ins.address+4+2*value;need(target in starts,'neutral direct branch targets admitted static start');branches.append(dict(pc=ins.address,target=target))
        record=dict(**pin,code_bytes=sum(high-low for low,high in pin['code_ranges']),static_instruction_starts=len(starts),calls=calls,branches=branches,literals=literals,guest_admitted=False,executed=False)
        if name=='TryUseHeldItem_effect0_or88':
            offset=struct.unpack('<h',window(blob,entry,0x225476A,2))[0]
            need(0x2254768+4+offset==0x2254D1E and 0x2254D1E in starts,'effect0 switch entry reaches real neutral default')
            need(literal_word(blob,entry,0x2254746)['value']==0x2D8C,'neutral TryUseHeldItem HP field literal')
            record.update(effect_domain=[0,88],effect0_table_target=0x2254D1E,effect88_unsigned_above54_target=0x2254D1E,
                excluded_function_entry=0x2254D80,scope='Only common prefix, item0 switch and item88 default path; remaining held effects and next function are not admitted')
        records[name]=record
    return records



def analyze(rom,language,reference,heartgold_ref,*,include_neutral=False):
    need(type(include_neutral)is bool,"explicit neutral readback option")
    ref=references(reference,heartgold_ref)
    neutral_source=neutral_references(reference,heartgold_ref)if include_neutral else None
    overlay_reader=load(SOURCE/'features/fairy-ai/tools/attribuisci.py','ordinary_overlay_reader')
    narc_reader=load(SOURCE/'features/borsa/tools/attribuisci.py','ordinary_NARC_reader')
    prior=load(HERE.with_name('rileggi_uturn_shellbell.py'),'ordinary_BL_reader')
    pin=json.loads((SOURCE/'distribution/game-1.3.2-r4.json').read_bytes())['targets'][language]
    with Path(rom).open('rb')as stream,mmap.mmap(stream.fileno(),0,access=mmap.ACCESS_READ)as raw:
        need(len(raw)==pin['bytes']and sha(raw)==pin['sha256'],'exact current image identity')
        image,overlay=overlay_reader.overlay(raw,12);ram=int(overlay['ram'],16)
        need(ram==0x22378C0 and len(image)==0x37380,'current overlay12 geometry')
        slots={slot:struct.unpack('<I',window(image,ram,TABLE+4*slot,4))[0]for slot in CONTROLLERS}
        need(slots=={slot:address|1 for slot,address in CONTROLLERS.items()},'native controller dispatch entries')
        wrapper=window(image,ram,WRAPPER,20)
        need(sha(wrapper)=='df45d800acc2a9086f2f44b795c491ffccf04887a0bbe28f9a49b8b53545e624','exact wrapper18code+2padding')
        need(prior.bl_target(wrapper[4:8],WRAPPER+4)==CONSUMER,'controller37 real call to consumer')
        consumer=profile(image)
        items,irec=narc_reader.raw_archive(raw,'a/0/1/7')
        need(irec['file_id']==146 and len(items)==516 and all(len(b)==34 for b in items),'item archive geometry')
        armoff,entry,armram,length=struct.unpack_from('<4I',raw,0x20)
        need((armoff,entry,armram,length)==(0x4000,0x2000800,0x2000000,0x12B8E4),'current plain ARM9 mapping')
        view=overlay_reader.gifts_audit.Arm9View(raw);item_id=253;mapping_ram=0x2100194+8*item_id;mapping_offset=armoff+mapping_ram-armram
        mapping=bytes(raw[mapping_offset:mapping_offset+8]);need(view.read(mapping_ram,8)==mapping,'independent raw/ARM9-view item mapping')
        member=struct.unpack('<4H',mapping)[0];need(member==231,'Shell Bell itemID to member')
        item=items[member];need(sha(item)=='908a7f24f3f913a567fac9eb45d55b4493ab791c6f3e217345c883e8c4dc60d1'and item[2:4]==bytes((88,8)),'exact Shell Bell record/effect/modifier')
        helper=view.read(0x23D5A20,68);need(sha(helper)=='8dfc3389b012ba046fd81df9c4a79119d1ffa4bf044b2462720a1868e0ea7f02','installed flinch helper identity')
        result=dict(schema='sgp-ordinary-ShellBell-static-v1',language=language,ROM=dict(bytes=len(raw),sha256=pin['sha256'],game_code=bytes(raw[12:16]).decode(),revision=raw[30]),source=ref,overlay=overlay,controller_table=TABLE,slots=slots,
            wrapper=dict(entry=WRAPPER,code_end=WRAPPER+18,padding_bytes=2,sha256=sha(wrapper),call_pc=WRAPPER+4,callee=CONSUMER,ABI='R0 BattleSystem*, R1 BattleContext*; FALSE sets command39'),consumer=consumer,
            item=dict(item_id=item_id,map_RAM=mapping_ram,map_ROM_offset=mapping_offset,member=member,file_id=irec['file_id'],archive_sha256=irec['archive_sha256'],member_ROM_offset=irec['member_rom_offsets'][member],raw_bytes=34,sha256=sha(item),effect=item[2],modifier=item[3],cache_stride=36,cache_padding_bytes=2,cache_preloader_executed=False),
            helper=dict(entry=0x23D5A20,ROM_offset=view.offset(0x23D5A20,68),bytes=68,sha256=sha(helper)),
            case1=dict(entry=0x224E244,field_read_pc=0x224E274,damage_field_offset=0x2EC,battler_stride=28,HP_offset=0x2D8C,maxHP_offset=0x2D90,battler_stride_HP=192,HP_comparison='unsigned lower',status_offset=0x213C,success_mask=0x2000,status2_offset=0x2140,UTurn_mask=0x10,state_offset=0x30,state_domain=[0,1,2,3],hpCalc_offset=0x215C,battler_temp_offset=0x118,script_request_pc=0x224E2AE,script_request_ABI='R0=CTX,R1=NARC1,R2=subscript213',request_executed=False),
            CPU_executed=False,compiler_invoked=False,healing_loss_proven=False,
            limits=['Static readback/source alignment only','Ordinary successful controller31..37 boundary and intermediate scripts are not executed','No native item preloader, original C compilation, healing application, natural battle, SAVE or hardware claim'])
    if include_neutral:result['neutral_dependencies']=dict(source=neutral_source,profiles=neutral_profiles(image,ram),scope='Static only; neutral does not mean no state or RNG changes')
    result['tool_sha256']=sha(HERE.read_bytes());return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',required=True,type=Path);p.add_argument('--language',required=True,choices=('EN','IT'))
    p.add_argument('--reference',required=True,type=Path);p.add_argument('--heartgold-ref',required=True,type=Path);p.add_argument('--json',required=True,type=Path)
    p.add_argument('--include-neutral',action='store_true',help='also read static dependency profiles; no CPU or no-state-change claim')
    a=p.parse_args()
    try:
        out=private_output(a.json)
        save_new(out,analyze(a.rom,a.language,a.reference,a.heartgold_ref,include_neutral=a.include_neutral))
    except(ValueError,OSError,subprocess.SubprocessError)as error:p.exit(1,str(error)+'\n')
    print('Static ordinary Shell Bell readback saved; no guest execution or healing-loss claim.')


if __name__=='__main__':main()
