"""Compare scoped observations across native and LLVM caller implementations.

Per-build full traces/pages are checked first by their own benchmarks. This
second check keeps semantic boundaries, guest Value provenance, callbacks and
caller-preserved ABI; volatile residues and dead stack are deliberately absent.
"""
import struct


def project(B,f,raw,*,compiled):
    F,R,M,need=B.F,B.R,B.M,B.need
    need(raw['observed']is True,'semantic projection requires observed raw')
    child_top=R.TOP-(32 if compiled else 24);push_words=8 if compiled else 4
    zero,pp=F.ZERO_VALUE,F.RESET_PP_VALUE
    stages=[]
    for count in(0,push_words+2245,push_words+2245+1+534,len(raw['stores'])):
        pages=B.replay_prefix(f['pages'],raw['stores'][:count]);mon=M.read(pages,F.BOX,236)
        stages.append(dict(Mon_sha256=R.sha(mon),checksum=struct.unpack_from('<H',mon,6)[0]))
    need(len(stages)==4,'four semantic Mon boundaries')
    calls=[]
    for row in raw['flow']:
        pc,r=row['pc'],row['regs']
        if r[13]!=child_top:continue
        if pc==0x20714f0:
            need(r[:3]==[F.BOX,310,0],'semantic native Box argument provenance')
            calls.append(dict(callee='MonSetMoveInSlot/Box',arguments=['Mon',310,0]))
        elif pc==0x206ec40:
            attr,value=r[1:3];need(r[0]==F.BOX and(attr,value)in((62,zero),(58,pp)),'semantic Mon stack Value provenance')
            calls.append(dict(callee='SetMonData',arguments=['Mon',attr,'ZeroInt'if attr==62 else'PPInt']))
        elif pc==0x207332c:
            need(r[:2]==[310,0],'semantic direct MaxPP no PP-Ups')
            calls.append(dict(callee='GetMoveMaxPP',arguments=[310,0]))
    need([x['callee']for x in calls]==['MonSetMoveInSlot/Box','SetMonData','GetMoveMaxPP','SetMonData'],'four ordered semantic native calls')
    local_destinations={}
    for label,local,dest in(('first',F.LOCAL1,F.DEST1),('second',F.LOCAL2,F.DEST2)):
        local_destinations.update({local+n:label+'.parser+'+str(n)for n in(8,12,16,20)})
        local_destinations[dest]=label+'.PP_buffer'
    callbacks=[]
    for row in raw['flow']:
        if row['pc']!=0x20d7448:continue
        arc,dest,offset,size=row['regs'][:4]
        need(arc==R.ARC and dest in local_destinations,'semantic callback archive/destination owner')
        callbacks.append(dict(archive='memory_NARC',destination=local_destinations[dest],offset=offset,bytes=size))
    need(len(callbacks)==14,'fourteen ordered semantic callbacks')
    pages={x['ram']:bytes.fromhex(x['hex'])for x in raw['final_pages']}
    native_fixture=F.OLD if compiled else F
    ro={'archive':(R.ARC,92),'FAT':(R.FAT,4104),'FNT':(R.FNT,2902),'root':(native_fixture.P.P.ROOT,12)}
    sdk=native_fixture.P.P.SDK
    ro.update({'payload_'+str(i):(sdk.ARCHIVE_BASE+0x1093800+a,n)for i,(a,n)in enumerate(native_fixture.P.P.NARC.WINDOWS)})
    readonly={}
    for name,(a,n)in ro.items():
        value=M.read(pages,a,n);need(value==M.read(f['pages'],a,n),'semantic RO/archive preservation '+name);readonly[name]=R.sha(value)
    need(raw['returned'][4:12]==f['entry_regs'][4:12]and raw['returned'][13]==f['entry_regs'][13],'semantic caller-preserved ABI')
    guards={}
    stack=F.STACK if compiled else F.FRAME
    for name,a,n in(('Mon_before',F.BOX-16,16),('Mon_after',F.BOX+236,16),('stack',R.TOP-stack-F.GUARD,F.GUARD)):
        value=M.read(pages,a,n);need(value==M.read(f['pages'],a,n),'semantic guard preserved '+name);guards[name]=R.sha(value)
    return dict(input_Up=f['input_Up'],move=310,slot=0,PID=0x4000,flags=0,Mon_boundaries=stages,
        native_calls=calls,callbacks=callbacks,readonly_sha256=readonly,guards_sha256=guards,
        preserved_R4_R11=raw['returned'][4:12],preserved_SP=raw['returned'][13],stop_pc=raw['stop_pc'])


def require_equal(need,wire,before,after):
    need(set(before)==set(after)=={'Up3','Up0'},'two observed semantic profiles')
    for profile in before:need(wire(before[profile])==wire(after[profile]),'native versus LLVM scoped semantic equivalence '+profile)
    return dict(observed_profiles=['Up3','Up0'],Mon_boundaries_per_profile=4,ordered_outer_calls=4,ordered_callbacks=14,
        own_full_traces_required=True,whole_C_ROM_reconstructed=False,
        excluded_cross_build_comparisons=['volatile registers/CPSR/LR','code pages','dead stack and FILE preInit residues'],
        scope='Owned Mon236, move310, slot0, flags0, valid checksum, PID4000, Up3 or Up0 only; no natural activation or other inputs')
