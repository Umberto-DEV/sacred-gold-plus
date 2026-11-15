#!/usr/bin/env python3
"""Follow Rage status through native packet construction to PartyMon write requests."""
import importlib.util
import json
from pathlib import Path
import struct

spec=importlib.util.spec_from_file_location('transform_rage',Path(__file__).with_name('attribuisci_rage.py'))
R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
from unicorn.arm_const import (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,
    UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_CPSR)
need,sha=R.need,R.sha
TRANSFORM=1<<21
OPP,MON=0x02390000,0x023A0000
WRAPPER,EMITTER,CONSUMER=0x02250C40,0x02263B4C,0x022591F4
SEND,PARTY,SET,CALC,ACK=0x02262240,0x0223A880,0x0206EC40,0x0206E250,0x0226430C
MASK=0x020726C0
WINDOWS=(
    ('copy_wrapper',WRAPPER,48,44,'1417bf4618b5bfb876a0e3af5a3a59b527869372c6ff951cc120d0289b3f57a2'),
    ('emitter',EMITTER,356,314,'22f11a4696c951b40371c2918e4f31d8fe32726e77684e8f2e25aebaac5c7c2c'),
    ('consumer',CONSUMER,220,220,'6385115c1c5cb9e7b17f043c5739e10581c7a0e84ca6e05ab4d489cfc1a0dca7'),
    ('field_side',0x0223AB1C,22,22,'e5a2331c0fb343e525df7140120f041292275375185f6426a3d2bf29d76fad24'),
    ('battler_type',0x02261258,12,6,'158546468068659cba962ecbdf8708d22430c713db8e6a0141674534e80c86d4'),
    ('clear_command',0x02259928,8,8,'4e87caf783f181f214d9804bca4903f9961d0278515dc2d256ab2c79885a171f'))
ARM9_PINS={MASK:'da266f8eefce9cbb52a195196c3e0897cbc84b5af29871c7bd834fa3e8992a78',
    SET:'6dc0d34389cf1453cfa6905ec51c2f9555dc95d816e8829b30743a9b7d0437d8',
    CALC:'a553a3f0bbe14dfee1ebd062027a90759201de68153e581224894ba268240f24'}


def counter_image(image,variant):
    if variant=='old':return R.counter_image(image,'old')
    result=bytearray(image)
    if variant=='wrong_field':address,before,after=0x02263C1A,bytes.fromhex('0b90'),bytes.fromhex('0d90')
    elif variant=='wrong_gate':address,before,after=0x02259216,bytes.fromhex('0005'),bytes.fromhex('c004')
    else:raise ValueError('explicit Transform counter variant')
    need(R.take(image,address,2)==before,'Transform counter preimage')
    result[address-R.G.T.OVERLAY_BASE:address-R.G.T.OVERLAY_BASE+2]=after
    return bytes(result)


def require_transport(result):need(result['emitter']['status2']==result['rage']['statuses'][0],'Transform packet status2 differs from Rage output')


def require_protection(result):need(not result['consumer']['move_pp_requests'],'Transform failed to block move/PP requests')


class TransportCPU(R.RageCPU):
    def __init__(self,segments,image,*,variant='current'):
        self.phase=None
        super().__init__(segments,image,variant='old' if variant=='old' else 'current')
        self.transport_variant=variant
        need(variant in ('current','old','wrong_field','wrong_gate'),'explicit Transform variant')
        for name,address,size,code,digest in WINDOWS:
            body=bytearray(R.take(image,address,size))
            if variant=='wrong_field' and name=='emitter':
                need(body[206:208]==bytes.fromhex('0d90'),'wrong packet store fixture');body[206:208]=bytes.fromhex('0b90')
            if variant=='wrong_gate' and name=='consumer':
                need(body[34:36]==bytes.fromhex('c004'),'wrong Transform mask fixture');body[34:36]=bytes.fromhex('0005')
            need(sha(body)==digest,'Transform native body '+name)
        need(sha(R.G.piece(segments,MASK,32))==ARM9_PINS[MASK],'native MaskOfFlagNo body')
        self.packet=None;self.native_pending=[]

    def _return(self,value=0):
        self.uc.reg_write(UC_ARM_REG_R0,value);self.uc.reg_write(UC_ARM_REG_PC,self.reg(UC_ARM_REG_LR))

    def _code(self,u,address,size,unused):
        if self.phase is None:return super()._code(u,address,size,unused)
        r=self.current;r['instructions']+=1;need(r['instructions']<=10000,'Transform instruction budget')
        need(self.reg(UC_ARM_REG_CPSR)&32 and size in (2,4),'Transform Thumb ISA')
        sp=self.reg(UC_ARM_REG_SP);r['stack_depth']=max(r['stack_depth'],R.STACK-sp)
        if self.native_pending and address==self.native_pending[-1]['return_pc']:
            call=self.native_pending.pop()
            need(sp==call['sp'] and [self.reg(v) for v in R.G.SAVED]==call.pop('saved'),'Transform native leaf return ABI')
            call['value']=self.reg(UC_ARM_REG_R0)
            if call['name']=='mask':need(call['value']==1<<call['slot'],'actual native mask result')
            if call['name']=='field_side':need(call['value']==self.side,'actual native field side')
            r['native_calls'].append(call)
        if address in (SEND,PARTY,SET,CALC,ACK):
            args=[self.reg(v) for v in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
            call=dict(ram=hex(address),return_pc=hex(self.reg(UC_ARM_REG_LR)&~1),args=args)
            if address==SEND:
                need(self.phase=='emit' and args[:3]==[R.BS,1,0] and self.word(sp)==44 and self.reg(UC_ARM_REG_LR)&~1==0x02263C82,'native EmitPacket ABI')
                need(R.STACK-4096<=args[3] and args[3]+44<=R.STACK,'native packet within stack')
                self.packet=bytes(u.mem_read(args[3],44));call.update(bytes=44,packet_sha256=sha(self.packet))
            elif address==PARTY:
                need(self.phase=='consume' and args[:3]==[R.BS,0,self.party_slot] and call['return_pc']=='0x2259210','PartyMon ownership ABI')
            elif address==SET:
                widths={6:2,160:4,163:2,112:1,10:1,**{54+i:2 for i in range(4)},**{58+i:1 for i in range(4)}}
                need(self.phase=='consume' and args[0]==MON and args[1] in widths,'SetMonData recording ABI')
                offset=args[2]-(OPP+0x94);width=widths[args[1]]
                need(0<=offset and offset+width<=44,'SetMonData pointer outside packet')
                call.update(field=args[1],value=int.from_bytes(u.mem_read(args[2],width),'little'),packet_offset=offset,width=width)
                r['requests'].append(dict(field=call['field'],value=call['value'],packet_offset=offset,width=width))
            elif address==CALC:raise ValueError('stat recalculation outside this Transform contract')
            else:need(self.phase=='consume' and args[:3]==[R.BS,0,0x27] and call['return_pc']=='0x22592c6','native command ACK ABI')
            r['models'].append(call);self._return(MON if address==PARTY else 0);return
        admitted=[w for w in WINDOWS if (self.phase=='emit' and w[0] in ('copy_wrapper','emitter','field_side','battler_type')) or (self.phase=='consume' and w[0] in ('consumer','clear_command'))]
        allowed=any(a<=address and address+size<=a+code for _,a,_,code,_ in admitted)
        allowed|=self.phase=='consume' and MASK<=address and address+size<=MASK+32
        need(allowed,'unexpected Transform code/literal PC '+hex(address));r['code'].add((address,size))
        names={0x0223AB1C:'field_side',0x02261258:'battler_type',MASK:'mask',0x02259928:'clear_command'}
        if address in names:
            call=dict(name=names[address],return_pc=self.reg(UC_ARM_REG_LR)&~1,sp=sp,saved=[self.reg(v) for v in R.G.SAVED])
            if address==MASK:
                call['slot']=self.reg(UC_ARM_REG_R0);need(0<=call['slot']<=5 and call['return_pc'] in (0x02259230,0x02259266),'native mask call ABI')
            elif address==0x0223AB1C:need(self.reg(UC_ARM_REG_R0)==R.BS and self.reg(UC_ARM_REG_R1)==0 and call['return_pc']==0x02263BAC,'native FieldSide ABI')
            elif address==0x02261258:need(self.reg(UC_ARM_REG_R0)==OPP and call['return_pc']==0x0223AB28,'native battler-type ABI')
            else:need(self.reg(UC_ARM_REG_R0)==OPP and call['return_pc']==0x022592CC,'native clear-command ABI')
            self.native_pending.append(call)

    def _read(self,u,access,address,size,value,unused):
        if self.phase is None:return super()._read(u,access,address,size,value,unused)
        if (address,size) in ((R.CTX+0x2DB0,4),(OPP+0xB0,4)):
            self.current['status_reads'].append(dict(pc=hex(self.reg(UC_ARM_REG_PC)),ram=hex(address),value=self.word(address)))

    def _write(self,u,access,address,size,value,unused):
        if self.phase is None:return super()._write(u,access,address,size,value,unused)
        stack=R.STACK-4096<=address and address+size<=R.STACK
        busy=self.phase=='consume' and address==OPP+0x94 and size==1 and self.reg(UC_ARM_REG_PC)==0x0225992C and value==0
        need(stack or busy,'Transform write outside stack/command byte '+hex(address))
        self.current['write_count']+=1

    def execute(self,phase,entry,args):
        u=self.uc;u.mem_write(R.STACK-4104,b'\xA5'*(4104+256))
        for reg,value in zip(R.G.SAVED,R.G.COOKIES):u.reg_write(reg,value)
        for reg,value in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),args):u.reg_write(reg,value)
        u.reg_write(UC_ARM_REG_SP,R.STACK);u.reg_write(UC_ARM_REG_LR,R.STOP|1)
        r=dict(instructions=0,stack_depth=0,models=[],native_calls=[],requests=[],status_reads=[],write_count=0,code=set())
        self.phase=phase;self.current=r;self.native_pending=[]
        before={a:bytes(u.mem_read(a,n)) for a,n in ((R.CTX,0x4000),(R.BS,0x3000),(OPP,0x300),(MON,0x100))}
        try:u.emu_start(entry|1,R.STOP,count=10001)
        finally:self.current=None;self.phase=None
        need(self.reg(UC_ARM_REG_PC)==R.STOP and self.reg(UC_ARM_REG_SP)==R.STACK and self.reg(UC_ARM_REG_CPSR)&32 and [self.reg(v) for v in R.G.SAVED]==R.G.COOKIES,'Transform parent return ABI')
        need(not self.native_pending,'unfinished Transform native leaf')
        for address,data in before.items():
            after=bytes(u.mem_read(address,len(data)))
            required=b'\0'+data[0x95:] if phase=='consume' and address==OPP else None
            if required is not None:need(after[:0x94]==data[:0x94] and after[0x94:]==required,'consumer changed packet/other OpponentData')
            else:need(after==data,'Transform changed context/BS/nominal Pokemon')
        need(bytes(u.mem_read(R.STACK-4104,8))==b'\xA5'*8 and bytes(u.mem_read(R.STACK,256))==b'\xA5'*256,'Transform stack/caller canary')
        need(all(bytes(u.mem_read(a,len(b)))==b for a,b in self.frozen),'Transform changed code/data')
        r['code']=[dict(ram=hex(a),bytes=n) for a,n in sorted(r['code'])];return r

    def transport(self,*,mimic=0,party_slot=0,side=0,selected_move=33):
        need(type(mimic) is int and 0<=mimic<16 and type(party_slot) is int and 0<=party_slot<6 and side in (0,1),'Transform fixture domain')
        self.side=side;self.party_slot=party_slot;u=self.uc
        def put(a,v):u.mem_write(a,struct.pack('<I',v))
        status=self.word(R.CTX+0x2DB0)
        u.mem_write(OPP,b'\xCC'*0x300);u.mem_write(MON,b'\xA5'*0x100)
        put(R.BS+0x34,OPP);u.mem_write(OPP+0x194,bytes((0,side)))
        u.mem_write(R.CTX+0x219C,bytes((party_slot,)));put(R.CTX+0x2DCC,mimic<<2)
        put(R.CTX+0x2D8C,123);u.mem_write(R.CTX+0x2DB8,struct.pack('<H',99));put(R.CTX+0x2DAC,0x12345678)
        u.mem_write(R.CTX+0x2D66,b'\x03\x21');put(R.CTX+0x2140,0)
        moves=(selected_move,20,30,40);pps=(5,6,7,8)
        u.mem_write(R.CTX+0x2D4C,struct.pack('<4H',*moves));u.mem_write(R.CTX+0x2D6C,bytes(pps))
        need(self.word(R.CTX+0x2DB0)==status,'fixture setup changed actual Rage status output')
        self.packet=None;emitter=self.execute('emit',WRAPPER,(R.BS,R.CTX,0,0))
        need(self.packet is not None and [c['ram'] for c in emitter['models']]==[hex(SEND)],'one native packet emission')
        packet=self.packet;need(packet[0]==0x27 and packet[1]==party_slot|(mimic<<4),'native packet command/bitfields')
        need(emitter['status_reads']==[dict(pc='0x2263c18',ram=hex(R.CTX+0x2DB0),value=status)],'actual emitter status2 read')
        need([c['name'] for c in emitter['native_calls']]==['battler_type','field_side'],'actual emitter native leaf sequence')
        emitter.update(packet_sha256=sha(packet),status2=struct.unpack_from('<I',packet,0x1C)[0],party_slot=packet[1]&15,mimic=packet[1]>>4,
            packet_fields=dict(hp=struct.unpack_from('<H',packet,2)[0],status=struct.unpack_from('<I',packet,4)[0],item=struct.unpack_from('<H',packet,12)[0],
                               moves=list(struct.unpack_from('<4H',packet,14)),pps=list(packet[22:26])))
        need(emitter['packet_fields']==dict(hp=123,status=0x12345678&0xFFFFF0FF,item=99,moves=list(moves),pps=list(pps)),'native emitted fixture fields')
        # Exact byte transport, including padding. No reconstruction from scenario flags.
        u.mem_write(OPP+0x94,packet);consumer=self.execute('consume',CONSUMER,(R.BS,OPP,0,0))
        required=[]
        # The named mask counter has an explicit bad-behavior oracle. The normal
        # constructor never admits it; require_protection remains independent.
        protected=bool(emitter['status2']&(TRANSFORM>>1 if self.transport_variant=='wrong_gate' else TRANSFORM))
        if not protected:
            for i in range(4):
                if not mimic&(1<<i):required.extend((dict(field=54+i,value=moves[i],packet_offset=14+2*i,width=2),dict(field=58+i,value=pps[i],packet_offset=22+i,width=1)))
        move_requests=list(required)
        required.extend((dict(field=6,value=99,packet_offset=12,width=2),dict(field=163,value=123,packet_offset=2,width=2),dict(field=160,value=0x12345678&0xFFFFF0FF,packet_offset=4,width=4)))
        need(consumer['requests']==required,'native PartyMon request sequence/values/widths')
        expected_masks=([0,1,2,3] if not protected else [])+[party_slot]
        need([c['slot'] for c in consumer['native_calls'] if c['name']=='mask']==expected_masks,'actual native mask loop/party slot')
        need([c['ram'] for c in consumer['models']]==[hex(PARTY)]+[hex(SET)]*len(required)+[hex(ACK)],'consumer service sequence')
        consumer.update(move_pp_requests=move_requests,busy_after=int(u.mem_read(OPP+0x94,1)[0]),pokemon_canary_unchanged=bytes(u.mem_read(MON,0x100))==b'\xA5'*0x100,
            received_packet_sha256=sha(packet),final_packet_sha256=sha(bytes(u.mem_read(OPP+0x94,44))))
        need(consumer['status_reads']==[dict(pc='0x2259214',ram=hex(OPP+0xB0),value=emitter['status2'])],'actual consumer status2 read')
        need([c['name'] for c in consumer['native_calls']]==['mask']*len(expected_masks)+['clear_command'],'actual consumer native leaf sequence')
        return emitter,consumer


def run_chain(model,status,move,*,mimic=0,party_slot=0,side=0,variant='current'):
    image=model['overlay'] if variant=='current' else counter_image(model['overlay'],variant)
    cpu=TransportCPU(model['segments'],image,variant=variant)
    rage=cpu.observe((status,),(move,));emitter,consumer=cpu.transport(mimic=mimic,party_slot=party_slot,side=side,selected_move=move)
    return dict(variant=variant,rage=rage,emitter=emitter,consumer=consumer)


def windows(model,role):
    base=int(model['record']['overlays'][1]['ram'],16);records=[]
    for name,address,size,code,digest in WINDOWS:
        actual=base+address-R.G.T.OVERLAY_BASE;raw=R.take(model['overlay'],address,size);normalized=bytearray(raw);fields=[]
        if role=='retail' and model['record']['language']=='IT' and name=='consumer':
            from sgp12.rom import bl_thumb
            md=R.G.S.SHARED.capstone.Cs(R.G.S.SHARED.capstone.CS_ARCH_ARM,R.G.S.SHARED.capstone.CS_MODE_THUMB)
            for ins in md.disasm(raw,actual):
                if ins.mnemonic=='bl':
                    target=int(ins.op_str.lstrip('#'),0)
                    if target in ARM9_PINS:
                        need(sha(R.G.piece(model['segments'],target,32))==ARM9_PINS[target],'retail IT ARM9 entry signature')
                        offset=ins.address-actual;normalized[offset:offset+4]=bl_thumb(address+offset,target)
                        fields.append(dict(offset=hex(offset),target=hex(target)))
            need(len(fields)==10,'retail IT consumer ARM9 field count')
        need(sha(normalized)==digest,'entire Transform window '+role+' '+name)
        records.append(dict(name=name,ram=hex(actual),bytes=size,code_bytes=code,sha256=sha(raw),normalized_sha256=sha(normalized),comparison_only_fields=fields))
    return records


def analyze(rom,v4,base,retail,language):
    import gc
    models={name:R.G.S.SHARED.read_image(path,language,name) for name,path in (('retail',retail),('base11',base),('v4',v4),('r4',rom))}
    records=[dict(input=name,windows=windows(m,name)) for name,m in models.items()];current=models['r4']
    caller_windows=[]
    for role,model in models.items():
        raw=R.take(model['overlay'],0x0224B2E0,80)
        need(sha(raw)=='85b0a70482d5ffa999d93835509af80b1d3dd8d7fac288cf525440cc396c0f49','PP-copy caller window '+role)
        base=int(model['record']['overlays'][1]['ram'],16);shift=base-R.G.T.OVERLAY_BASE
        need(R.G.S.SHARED.branch(raw[58:62],0x0224B31A+shift,'bl')==WRAPPER+shift,'actual PP-copy wrapper BL')
        caller_windows.append(dict(input=role,ram=hex(0x0224B2E0+shift),bytes=80,sha256=sha(raw),bl_ram=hex(0x0224B31A+shift),target=hex(WRAPPER+shift),activation='static only'))
    need(R.take(current['overlay'],0x0226D0AC,4)==struct.pack('<I',CONSUMER|1),'current command27 dispatch pointer')
    runs=[]
    cases=[('transform_leave',R.RAGE|TRANSFORM|1<<24,33,{}),('transform_keep_rage',R.RAGE|TRANSFORM,99,{}),('rage_only',R.RAGE,33,{})]
    cases += [('mimic_'+str(mask),R.RAGE,33,dict(mimic=mask,party_slot=5,side=1)) for mask in (1,2,4,8,15)]
    for name,status,move,options in cases:
        result=run_chain(current,status,move,**options);require_transport(result)
        if status&TRANSFORM:require_protection(result)
        runs.append(dict(name=name,result=result));gc.collect()
    counters=[]
    for variant in ('old','wrong_field','wrong_gate'):
        result=run_chain(current,R.RAGE|TRANSFORM|1<<24,33,variant=variant)
        oracle=require_transport if variant=='wrong_field' else require_protection
        try:oracle(result)
        except ValueError:pass
        else:raise ValueError('false Transform chain success')
        counters.append(dict(variant=variant,oracle_rejected=True,same_move_pp_output_as_current=not result['consumer']['move_pp_requests'],result=result));gc.collect()
    return dict(schema='transform-transport-source-rom-v1',language=language,compilation_performed=False,inputs=[m['record'] for m in models.values()],window_records=records,caller_windows=caller_windows,
        dispatch=dict(slot='0x0226d0ac',target=hex(CONSUMER|1),kind='static pointer'),runs=runs,counterproofs=counters,
        source_sha256={str(p.relative_to(R.G.SOURCE)):sha(p.read_bytes()) for p in (Path(__file__),Path(R.__file__),Path(R.G.T.__file__))},
        coverage=dict(positive_chains=len(runs),counter_chains=len(counters),packet_bytes=44,native_mask=True,native_field_side=True),
        limits=['controlled state1 and direct copy wrapper entries, not natural battle/controller timing',
                'one synchronous recording EmitPacket bridge copies exact44bytes, not actual asynchronous transport',
                'PartyMon lookup, SetMonData and ACK are models; no encrypted Pokemon or save mutation',
                'nonzero item avoids TrainerAI clear; form/recalc flags zero; those paths are excluded',
                'inherited code/source reference correspondence, no original native C/compiler rebuild'])


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('rom','v4','base','retail','json'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--language',choices=('EN','IT'),required=True);args=parser.parse_args()
    for path in (args.rom,args.v4,args.base,args.retail):
        if args.json.resolve()==path.resolve() or (args.json.exists() and path.exists() and args.json.samefile(path)):parser.error('--json must not replace an input')
    result=analyze(args.rom,args.v4,args.base,args.retail,args.language)
    args.json.parent.mkdir(parents=True,exist_ok=True);args.json.write_text(json.dumps(result,indent=2)+'\n')
    print(args.language,'Transform:',len(result['runs']),'current +3 counter chains PASS; SetMonData recording only')


if __name__=='__main__':main()
