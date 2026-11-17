// Optional observation-only instruction counters for the offline HG audit.
#pragma once
#include <cstdint>
#include <cstddef>
#include <type_traits>
#include <initializer_list>
#include <array>
#include <limits>
#include <stdexcept>
namespace melonDS::HGTrace {
struct Counter { std::uint64_t visits=0, executed=0, r10_changes=0; std::uint32_t last_before=0,last_after=0,last_instruction=0; };
inline bool Enabled=false;
inline Counter Counters[2];
inline std::uint64_t MainLoopJumps=0;
inline void Record(std::uint32_t address,bool condition,std::uint32_t before,std::uint32_t after,std::uint32_t instruction) {
    auto& c=Counters[address==0x020D3FA8?0:1];++c.visits;if(condition)++c.executed;if(before!=after)++c.r10_changes;
    c.last_before=before;c.last_after=after;c.last_instruction=instruction;
}
}


// Diagnostic r4 Bag profile. No guest memory accesses, clock, mutation, or JIT.
// Every step is one ARM9 interpreter dispatch, including failed ARM conditions
// and the two halves of a Thumb BL. Counts are not DS cycles or ISA instruction counts.
namespace melonDS::HGTrace {
struct WorkSite {
    std::uint32_t pc,instruction;
    bool span,thumb=true,heapRoot=false;
    std::uint32_t callReturn=0; // pre-call sites use the post-call PC, preserving captured LR
};
// G06: cold direct-boot capture of the admitted native asset paths. Keep
// overlapping FS/overlay activations independent of Work's inclusive stack.
// No memory/clock reads: r0-r7, SP, LR, CPSR and the interpreter PC suffice.
struct AssetEvent {
    std::uint32_t pc=0,first=0,last=0,entryOrder=0,exitOrder=0,lr=0,sp=0,cpsr=0;
    std::array<std::uint32_t,8> args{};
    std::array<std::uint32_t,3> result{};
    std::uint32_t dispatch=0,stores=0;
};
inline WorkSite assetSite(std::uint32_t pc) {
    switch(pc) {
        case 0x020D8104:return {pc,0xE92D40F8,true,false}; // FS read core (sync/async)
        case 0x020D8150:return {pc,0xE1A00007,false,false}; // pos/clamp in r4/r6
        case 0x020D82FC:return {pc,0xE92D41F0,true,false}; // FS wait, result BOOL
        case 0x020D4BF4:return {pc,0xE3A07000,false,false}; // decoder header in r5/r2
        case 0x020DD754:return {pc,0xE92D47F0,false,false}; // CARD read submission, before caching
        case 0x020D4BE8:return {pc,0xE92D40F0,true,false}; // LZ8, r0/r1 advance
        case 0x02000970:return {pc,0xE3500000,true,false}; // backward decoder
        case 0x020D6B94:return {pc,0xE92D4008,true,false}; // FS read command with file handle
        case 0x020D84C4:return {pc,0xE92D4000,true,false}; // native ROM archive read callback
        case 0x020D7EDC:return {pc,0xE92D4070,false,false}; // async result notification
        case 0x020D88C0:return {pc,0xE92D4038,true,false}; // overlay info, target/ID
        case 0x020D89BC:return {pc,0xE92D4070,true,false}; // overlay image async submission
        case 0x020D8A48:return {pc,0xE92D4038,true,false}; // overlay image sync
        case 0x020D8B6C:return {pc,0xE92D4038,true,false}; // overlay start (void)
        case 0x020D8D60:return {pc,0xE92D4000,true,false}; // SDK overlay load
        case 0x020D8DB4:return {pc,0xE92D4000,true,false}; // SDK overlay unload
        case 0x02006F78:return {pc,0x6060,false}; // clear registry active flag
        case 0x02007030:return {pc,0x505D,false}; // registry ID after active write
        case 0x02006F7C:return {pc,0xB510,true}; // unload request; void
        case 0x02006FF8:return {pc,0xB5F8,true}; // game load incl. async wait
        default:return {};
    }
}
template<std::size_t Capacity, std::size_t Pending=24> struct AssetObserver {
    static_assert(Capacity < std::numeric_limits<std::uint32_t>::max()/2);
    std::array<AssetEvent,Capacity> events{};
    std::array<std::size_t,Pending> pending{};
    std::size_t count=0,active=0;
    bool enabled=false,ok=true;
    std::uint32_t errorPC=0,errorFrame=0,order=0;

    void start() { enabled=ok=true;count=active=order=errorPC=errorFrame=0; }
    void fail(std::uint32_t pc,std::uint32_t frame) {
        ok=false;enabled=false;errorPC=pc;errorFrame=frame;
    }
    void stop(std::uint32_t frame=0) {
        if(ok && active)fail(events[pending[active-1]].pc,frame);
        enabled=false;
    }
    void step(std::uint32_t pc,std::uint32_t ins,const std::uint32_t* r,
            std::uint32_t cpsr,std::uint32_t frame) {
        if(!enabled)return;
        const bool thumb=cpsr&32u;
        const std::uint32_t key=pc|std::uint32_t(thumb);
        for(std::size_t i=active;i;) {
            --i;
            auto& e=events[pending[i]];
            if(r && e.lr==key && e.sp==r[13] && (e.cpsr&31u)==(cpsr&31u)) {
                e.last=frame;e.exitOrder=++order;
                for(std::size_t n=0;n<3;++n)e.result[n]=r[n];
                pending[i]=pending[--active];
            } else {
                const bool lz=e.pc==0x020D4BE8;
                const bool backward=e.pc==0x02000970;
                if((lz || backward) && pc>e.pc && pc<(lz?0x020D4CE8u:0x02000A1Cu) &&
                        !thumb && (e.cpsr&31u)==(cpsr&31u) && r) {
                    const auto localStack=lz?20u:16u;
                    if(r[13]!=e.sp && (e.sp<localStack || r[13]!=e.sp-localStack))continue;
                    if(e.dispatch==std::numeric_limits<std::uint32_t>::max()){fail(pc,frame);return;}
                    ++e.dispatch;
                    if(backward && (pc==0x020009B8 || pc==0x020009DC)) {
                        // Unconditional STRB before interpreter dispatch.
                        if(ins!=0xE5620001 || e.stores==std::numeric_limits<std::uint32_t>::max()){fail(pc,frame);return;}
                        ++e.stores;
                    }
                }
            }
        }
        const auto site=assetSite(pc);
        if(!site.pc)return;
        if(!r || thumb!=site.thumb || (thumb?(ins&0xFFFFu):ins)!=site.instruction ||
                count==Capacity || (site.span && active==Pending)) {fail(pc,frame);return;}
        if(site.span) {
            if((r[13]&3u) || r[14]<4 || (!(r[14]&1u) && (r[14]&3u))) {fail(pc,frame);return;}
            for(std::size_t i=0;i<active;++i) {
                const auto& e=events[pending[i]];
                if(e.sp==r[13] && e.lr==r[14] && (e.cpsr&31u)==(cpsr&31u)) {
                    fail(pc,frame);return;
                }
            }
            pending[active++]=count;
        }
        auto& e=events[count++];e={};e.pc=pc;e.first=e.last=frame;e.lr=r[14];e.sp=r[13];
        e.cpsr=cpsr;e.entryOrder=++order;
        for(std::size_t i=0;i<e.args.size();++i)e.args[i]=r[i];
        if(!site.span)e.exitOrder=e.entryOrder;
        if(pc==0x020D4BE8 || pc==0x02000970)e.dispatch=1;
    }
};
inline AssetObserver<98304> Assets;

inline constexpr std::array<WorkSite,74> WorkSites{{
    {0x02223BF4,0xB5F0,true}, {0x023DBD00,0xB5FE,true},
    {0x02077D88,0xB570,true}, {0x02257E74,0xB538,true},
    {0x02007524,0xB510,true}, {0x0200757C,0xB510,true},
    {0x0201AA8C,0xB538,true}, {0x0201AB0C,0xB5F8,true},
    {0x0201AB80,0xB570,true}, {0x022225D4,0xB570,true},
    {0x022227B4,0x4920,false}, {0x02222852,0x492E,false},
    {0x02222E40,0x1C28,false}, {0x02222EBA,0x2001,false},
    {0x020B535C,0xE92D4008,true,false,true},
    {0x020B5394,0xE59FC000,true,false,true},
    {0x020B53A0,0xE92D4008,true,false,true},
    {0x020B53D0,0xE92D43F8,true,false,true},
    {0x020B5530,0xE92D4038,true,false,true},
    {0x020B5594,0xE1D023B4,true,false,true},
    {0x020B4DD0,0xE92D4010,true,false,false},
    {0x020B4E4C,0xE92D4010,true,false,false},
    {0x020205D8,0xB5F8,true}, {0x0202061C,0xB508,true},
    {0x020B634C,0xE92D43F8,true,false}, {0x020B62EC,0xE92D4038,true,false},
    {0x020B61E8,0xE92D4038,true,false}, {0x020B620C,0xE12FFF34,true,false,false,0x020B6210},
    {0x020B62C8,0xE59F2010,true,false}, {0x020CFF04,0xEB00103A,true,false,false,0x020CFF08},
    {0x020CFF18,0xEB00123A,true,false,false,0x020CFF1C},
    {0x02009418,0xB510,true,true,false,0},
    {0x0200B224,0xB508,true,true,false,0},
    {0x0200398C,0xB5F8,true,true,false,0},
    {0x0201EEB4,0xB510,true,true,false,0},
    {0x0201C014,0xB5F8,true,true,false,0},
    {0x0201C130,0xB5F8,true,true,false,0},
    {0x020D3FF4,0xE92D41F0,true,false,false,0},
    {0x020D4064,0xE92D41F0,true,false,false,0},
    {0x020D4808,0xE081C002,true,false,false,0},
    {0x020D47B8,0xE3A0C000,true,false,false,0},
    {0x020D4194,0xE92D41F0,true,false,false,0},
    {0x020D422C,0xE92D4010,true,false,false,0},
    {0x02000E3A,0x4788,true,true,false,0x02000E3D},
    {0x020D08F0,0xEBFFF805,true,false,false,0x020D08F4},
    {0x020D0AAC,0xEBFFF5B7,true,false,false,0x020D0AB0},
    {0x020D0AD8,0xEBFFF790,true,false,false,0x020D0ADC},
    {0x020D0B98,0xEBFFF5F2,true,false,false,0x020D0B9C},
    {0x020D0528,0xEBFFF8E5,true,false,false,0x020D052C},
    {0x020D0658,0xEBFFF661,true,false,false,0x020D065C},
    {0x020D0680,0xEBFFF898,true,false,false,0x020D0684},
    {0x020D0754,0xEBFFF662,true,false,false,0x020D0758},
    {0x020D0778,0xEBFFF87C,true,false,false,0x020D077C},
    {0x020D0814,0xEBFFF7D3,true,false,false,0x020D0818},
    {0x020D0834,0xEBFFF857,true,false,false,0x020D0838},
    {0x020D08D0,0xEBFFF7C4,true,false,false,0x020D08D4},
    // P01: exact r4 Party scan, shims, cache record and native fallbacks.
    {0x0221D184,0xB5F8,true}, {0x023DBEB4,0xB508,true},
    {0x023DBEBE,0xB508,true}, {0x023DBE2C,0xB5B0,true},
    {0x023DBE00,0xB5B0,true}, {0x023DBE7C,0xB5B0,true},
    {0x02073314,0xB510,true}, {0x0207332C,0xB538,true},
    // L5: scheduler/copy-barrier causal boundary only. All sites Thumb.
    {0x02000DD4,0x2800,false}, {0x02000E84,0xB508,true},
    {0x0201F880,0xB570,true}, {0x0201F886,0x2800,false},
    {0x0201F89E,0x2900,false}, {0x0201F8AA,0x4790,true,true,false,0x0201F8AD},
    {0x023DBC9A,0xB513,true}, {0x023DBCA0,0x2C00,false},
    {0x023DBCA8,0x2800,false}, {0x023DB72C,0xB5F0,true}
}};
inline int workSiteIndex(std::uint32_t pc) {
    switch(pc) {
        case 0x02223BF4:return 0;case 0x023DBD00:return 1;
        case 0x02077D88:return 2;case 0x02257E74:return 3;
        case 0x02007524:return 4;case 0x0200757C:return 5;
        case 0x0201AA8C:return 6;case 0x0201AB0C:return 7;
        case 0x0201AB80:return 8;case 0x022225D4:return 9;
        case 0x022227B4:return 10;case 0x02222852:return 11;
        case 0x02222E40:return 12;case 0x02222EBA:return 13;
        case 0x020B535C:return 14;case 0x020B5394:return 15;
        case 0x020B53A0:return 16;case 0x020B53D0:return 17;
        case 0x020B5530:return 18;case 0x020B5594:return 19;
        case 0x020B4DD0:return 20;case 0x020B4E4C:return 21;
        case 0x020205D8:return 22;case 0x0202061C:return 23;
        case 0x020B634C:return 24;case 0x020B62EC:return 25;
        case 0x020B61E8:return 26;case 0x020B620C:return 27;
        case 0x020B62C8:return 28;case 0x020CFF04:return 29;
        case 0x020CFF18:return 30;
        case 0x02009418:return 31;
        case 0x0200B224:return 32;
        case 0x0200398C:return 33;
        case 0x0201EEB4:return 34;
        case 0x0201C014:return 35;
        case 0x0201C130:return 36;
        case 0x020D3FF4:return 37;
        case 0x020D4064:return 38;
        case 0x020D4808:return 39;
        case 0x020D47B8:return 40;
        case 0x020D4194:return 41;
        case 0x020D422C:return 42;
        case 0x02000E3A:return 43;
        case 0x020D08F0:return 44;
        case 0x020D0AAC:return 45;
        case 0x020D0AD8:return 46;
        case 0x020D0B98:return 47;
        case 0x020D0528:return 48;
        case 0x020D0658:return 49;
        case 0x020D0680:return 50;
        case 0x020D0754:return 51;
        case 0x020D0778:return 52;
        case 0x020D0814:return 53;
        case 0x020D0834:return 54;
        case 0x020D08D0:return 55;
        case 0x0221D184:return 56;case 0x023DBEB4:return 57;
        case 0x023DBEBE:return 58;case 0x023DBE2C:return 59;
        case 0x023DBE00:return 60;case 0x023DBE7C:return 61;
        case 0x02073314:return 62;case 0x0207332C:return 63;
        case 0x02000DD4:return 64;case 0x02000E84:return 65;
        case 0x0201F880:return 66;case 0x0201F886:return 67;
        case 0x0201F89E:return 68;case 0x0201F8AA:return 69;
        case 0x023DBC9A:return 70;case 0x023DBCA0:return 71;
        case 0x023DBCA8:return 72;case 0x023DB72C:return 73;
        default:return -1;
    }
}
enum class WorkLayout { R4, H4, NativeHeap, Graphics, Pilot, Assets, Party, Scheduler };
struct WorkEvent {
    std::uint64_t first_frame=0,last_frame=0,start_tick=0,inclusive=0,exclusive=0;
    std::uint64_t entry_order=0,exit_order=0;
    std::array<std::uint32_t,4> args{},aux{};
    std::uint32_t lr=0,sp=0,result=0;
    std::uint32_t parent=0xFFFFFFFFu,entry_cpsr=0,exit_cpsr=0;
    std::uint8_t site=0,mode=0;
    bool complete=false;
};
inline bool recordPilotAux(std::uint32_t pc,std::uint32_t instruction,
    const std::uint32_t* registers,std::uint32_t cpsr,std::uint64_t frame);
inline bool samePilotOwner(std::uint32_t firstSP,std::uint32_t secondSP);
inline int recordPilotCopy(std::uint32_t pc,std::uint32_t instruction,
    const std::uint32_t* registers,std::uint32_t cpsr,std::uint64_t frame,bool inOamRoot);
struct CallbackSample {
    bool used=false;
    std::uint32_t target=0,lastSP=0,lastLR=0,lastArg=0;
    std::uint64_t calls=0,firstFrame=0,lastFrame=0;
};
template<std::size_t Capacity=16384,std::size_t MaxDepth=64> struct WorkObserver {
    bool enabled=false,ok=true;
    bool nativeHeap=false,graphics=false,pilot=false,assets=false,party=false,scheduler=false;
    std::uint16_t helperInstruction=0xB5FE;
    std::uint64_t frame=0,order=0;
    std::array<std::uint64_t,32> ticks{};
    std::array<WorkEvent,Capacity> events{};
    std::array<std::size_t,MaxDepth> stack{};
    std::size_t count=0,depth=0,eventLimit=Capacity;
    std::array<std::uint64_t,2> callbackKnown{};
    std::array<CallbackSample,8> callbackUnknown{};
    std::uint64_t callbackUnknownCalls=0;
    std::uint8_t callbackError=0; // 1 mode, 2 arithmetic, 3 target capacity
    int callbackGate(const std::uint32_t* r,std::uint32_t cpsr) {
        if((cpsr&0x3Fu)!=0x3Fu){callbackError=1;return -1;}
        constexpr std::uint32_t targets[2]={0x02239731,0x022397E5};
        for(std::size_t i=0;i<2;++i)if(r[1]==targets[i]) {
            if(callbackKnown[i]==std::numeric_limits<std::uint64_t>::max()){callbackError=2;return -1;}
            ++callbackKnown[i];return 0;
        }
        CallbackSample* chosen=nullptr;
        for(auto& entry:callbackUnknown)if(entry.used && entry.target==r[1]){chosen=&entry;break;}
        if(!chosen)for(auto& entry:callbackUnknown)if(!entry.used){chosen=&entry;break;}
        if(!chosen){callbackError=3;return -1;}
        if(callbackUnknownCalls==std::numeric_limits<std::uint64_t>::max() ||
                chosen->calls==std::numeric_limits<std::uint64_t>::max()){callbackError=2;return -1;}
        if(!chosen->used){chosen->used=true;chosen->target=r[1];chosen->firstFrame=frame;}
        ++chosen->calls;++callbackUnknownCalls;chosen->lastFrame=frame;
        chosen->lastSP=r[13];chosen->lastLR=r[14];chosen->lastArg=r[0];return 1;
    }
    void fail() { ok=false;enabled=false; }
    void start(bool layout_admitted, WorkLayout layout=WorkLayout::R4) {
        if(!layout_admitted)throw std::invalid_argument("Work observer requires the r4 Bag layout");
        if(layout!=WorkLayout::R4 && layout!=WorkLayout::H4 && layout!=WorkLayout::NativeHeap && layout!=WorkLayout::Graphics && layout!=WorkLayout::Pilot && layout!=WorkLayout::Assets && layout!=WorkLayout::Party && layout!=WorkLayout::Scheduler)
            throw std::invalid_argument("Unknown work observation layout");
        helperInstruction=layout==WorkLayout::H4?0xB5F0:0xB5FE;
        nativeHeap=layout==WorkLayout::NativeHeap;pilot=layout==WorkLayout::Pilot;graphics=layout==WorkLayout::Graphics || pilot;
        assets=layout==WorkLayout::Assets;
        party=layout==WorkLayout::Party;scheduler=layout==WorkLayout::Scheduler;
        if(assets)Assets.start();
        enabled=true;ok=true;frame=0;ticks.fill(0);count=0;depth=0;order=0;
        callbackKnown.fill(0);callbackUnknown={};callbackUnknownCalls=0;callbackError=0;
        const std::size_t profileLimit=pilot?65536:16384;
        eventLimit=Capacity<profileLimit?Capacity:profileLimit;
    }
    void stop() {
        if(assets){Assets.stop(static_cast<std::uint32_t>(frame));if(!Assets.ok)fail();}
        if((nativeHeap || graphics || party || scheduler) && depth)fail();else enabled=false;
    }
    void requireStopped() const {
        if(enabled || !ok)throw std::runtime_error("Unclosed or invalid work trace");
    }
    // This gate closes only the authenticated native allocator call graph.
    // It does not observe arbitrary STR/DMA/ARM7 writers outside these ranges.
    bool nativeContext(std::uint32_t pc,std::uint32_t cpsr,const std::uint32_t* r) const {
        unsigned allowed=0;int common=-1;
        if(pc>=0x020B4DD0 && pc<0x020B4E64)common=pc<0x020B4E4C?20:21;
        else if(pc>=0x020B4E90 && pc<0x020B535C) {
            if(pc<0x020B4EE8)allowed=(1u<<16)|(1u<<17)|(1u<<18); // list links
            else if(pc<0x020B4F14)allowed=(1u<<14)|(1u<<16)|(1u<<17)|(1u<<18);
            else if(pc<0x020B4F88)allowed=1u<<14; // InitExp
            else if(pc<0x020B526C)allowed=1u<<16; // allocate used/head/tail
            else allowed=(1u<<17)|(1u<<18); // recycle
        } else if(pc>=0x020B535C && pc<0x020B556C) {
            const unsigned i=pc<0x020B5394?14:pc<0x020B53A0?15:
                             pc<0x020B53D0?16:pc<0x020B5530?17:18;
            allowed=1u<<i;
        } else if(pc>=0x020B5594 && pc<0x020B55A4)allowed=1u<<19;
        else return true;
        if(cpsr&0x20)return false;
        for(std::size_t d=depth;d;--d) {
            const auto& e=events[stack[d-1]];
            if(e.mode!=(cpsr&31u))continue;
            if(common>=0) {
                if(e.site>=20)return e.site==common && r && !(r[13]&3u) && r[13]<=e.sp && e.sp-r[13]<=128;
            } else if(WorkSites[e.site].heapRoot)return (allowed&(1u<<e.site))!=0 && r &&
                    !(r[13]&3u) && r[13]<=e.sp && e.sp-r[13]<=128;
        }
        return false;
    }
    void step(std::uint32_t pc,std::uint32_t instruction,const std::uint32_t* r,std::uint32_t cpsr) {
        if(!enabled)return;
        if(assets) {
            Assets.step(pc,instruction,r,cpsr,static_cast<std::uint32_t>(frame));
            if(!Assets.ok)fail();
            return;
        }
        int copyDecision=0;
        if(pilot) {
            if(!recordPilotAux(pc,instruction,r,cpsr,frame)){fail();return;}
            bool inOamRoot=false;
            if(pc==0x020D47B8 && r)for(std::size_t d=depth;d;--d) {
                const auto& parent=events[stack[d-1]];
                if(parent.site==32){
                    inOamRoot=parent.mode==31 && (cpsr&31u)==31 && samePilotOwner(parent.sp,r[13]);break;
                }
            }
            copyDecision=recordPilotCopy(pc,instruction,r,cpsr,frame,inOamRoot);
            if(copyDecision<0){fail();return;}
        }
        const auto mode=cpsr&31u;
        if(ticks[mode]==std::numeric_limits<std::uint64_t>::max()){fail();return;}
        if(depth) {
            // SP, mode and Thumb/ARM return address must all match. Tail calls
            // sharing a return unwind together; interrupted frames stay open.
            while(depth) {
                auto& e=events[stack[depth-1]];
                const auto target=WorkSites[e.site].callReturn?WorkSites[e.site].callReturn:e.lr;
                if(e.mode!=mode || pc!=(target&~1u) || !r || r[13]!=e.sp ||
                        bool(cpsr&0x20)!=bool(target&1))break;
                e.inclusive=ticks[mode]-e.start_tick;e.last_frame=frame;e.result=r[0];
                if(order==std::numeric_limits<std::uint64_t>::max()){fail();return;}
                e.exit_order=++order;e.exit_cpsr=cpsr;e.complete=true;--depth;
            }
        }
        int index=workSiteIndex(pc);
        if(index>=0) {
            const bool context=index==0 || (index>=9 && index<14);
            const bool selected=scheduler?index>=64:party?(index>=56 && index<64):nativeHeap?(index>=14 && index<22):
                pilot?((index>=22 && index<=28) || (index>=31 && index<56) || context):
                graphics?((index>=22 && index<=30) || context):index<14;
            if(!selected)index=-1;
        }
        if(pilot && copyDecision>0)index=-1; // no push, but dispatch still reaches ticks below
        if(index>=0) {
            const auto& site=WorkSites[index];
            const auto observed=site.thumb?(instruction&0xFFFF):instruction;
            if(bool(cpsr&0x20)!=site.thumb || observed!=(index==1?helperInstruction:site.instruction) || !r){fail();return;}
            bool keep=true;
            if(pilot && index==43){const auto decision=callbackGate(r,cpsr);if(decision<0){fail();return;}keep=decision==0;}
            if(keep) {
                if(count>=eventLimit || (site.span && depth>=MaxDepth)){fail();return;}
                if(order==std::numeric_limits<std::uint64_t>::max()){fail();return;}
                auto& e=events[count];e={};e.entry_order=++order;e.entry_cpsr=cpsr;
                e.parent=depth?std::uint32_t(stack[depth-1]):0xFFFFFFFFu;e.site=std::uint8_t(index);e.mode=std::uint8_t(mode);
                e.first_frame=e.last_frame=frame;e.start_tick=ticks[mode];e.lr=r[14];e.sp=r[13];
                for(std::size_t i=0;i<4;++i)e.args[i]=r[i];
                if(graphics || party || scheduler)for(std::size_t i=0;i<4;++i)e.aux[i]=r[i+4];
                if(site.span)stack[depth++]=count;
                else { e.result=r[0];e.complete=true;e.exit_order=e.entry_order;e.exit_cpsr=cpsr; }
                ++count;
            }
        }
        if(nativeHeap && !nativeContext(pc,cpsr,r)){fail();return;}
        ++ticks[mode];
        if(depth && events[stack[depth-1]].mode==mode)++events[stack[depth-1]].exclusive;
    }
};
inline WorkObserver<65536> Work;
}

// Raw ARM9 scheduler time partition. No host clock or guest memory accesses.
// Execute residual includes the interpreter model/carry, and is not CPU busy.
namespace melonDS::HGTrace {
enum class ModelBranch : unsigned { GX=0, DMA=1, Execute=2 };
struct ModelBudget {
    bool enabled=false,ok=true,active=false;
    unsigned clockShift=1;
    ModelBranch branch=ModelBranch::Execute;
    std::uint64_t startTS=0,lastTS=0,stepTS=0,skip=0,lastSkipEnd=0,steps=0;
    std::array<std::uint64_t,4> ticks{}; // GX branch, DMA branch, Execute residual, Halt1 skip
    std::int32_t startCarry=0,endCarry=0;
    void fail() { ok=false;enabled=false; }
    void start(std::uint64_t now,unsigned shift,std::int32_t carry) {
        enabled=true;ok=true;active=false;clockShift=shift;startTS=lastTS=now;
        stepTS=skip=lastSkipEnd=steps=0;ticks.fill(0);startCarry=endCarry=carry;
        if(shift!=1)fail(); // first pilot is DS, not a changing-clock DSi session
    }
    void begin(ModelBranch selected,std::uint64_t now,unsigned shift) {
        if(!enabled)return;
        if(active || unsigned(selected)>2 || shift!=clockShift || now!=lastTS){fail();return;}
        active=true;branch=selected;stepTS=lastSkipEnd=now;skip=0;
    }
    void haltSkip(std::uint64_t from,std::uint64_t to,unsigned halted) {
        if(!enabled)return;
        if(!active || branch!=ModelBranch::Execute || halted!=1 || from<lastSkipEnd || to<from ||
                skip>std::numeric_limits<std::uint64_t>::max()-(to-from)){fail();return;}
        skip+=to-from;lastSkipEnd=to;
    }
    std::uint64_t accounted() const {
        std::uint64_t sum=0;
        for(auto n:ticks) {
            if(sum>std::numeric_limits<std::uint64_t>::max()-n)
                throw std::runtime_error("Model budget sum overflow");
            sum+=n;
        }
        return sum;
    }
    void end(std::uint64_t now,unsigned shift,std::int32_t carry) {
        if(!enabled)return;
        if(!active || shift!=clockShift || now<stepTS || skip>now-stepTS || lastSkipEnd>now ||
                steps==std::numeric_limits<std::uint64_t>::max()){fail();return;}
        const auto delta=now-stepTS;
        const auto index=unsigned(branch);
        const auto residual=delta-skip;
        if(ticks[index]>std::numeric_limits<std::uint64_t>::max()-residual ||
                ticks[3]>std::numeric_limits<std::uint64_t>::max()-skip){fail();return;}
        ticks[index]+=residual;ticks[3]+=skip;++steps;lastTS=now;endCarry=carry;active=false;
    }
    void checkpoint(std::uint64_t now,unsigned shift,std::int32_t carry) {
        if(!enabled)return;
        if(active || shift!=clockShift || now!=lastTS || now<startTS){fail();return;}
        try { if(accounted()!=now-startTS){fail();return;} }
        catch(const std::runtime_error&) {fail();return;}
        endCarry=carry;
    }
    void stop(std::uint64_t now,unsigned shift,std::int32_t carry) {
        checkpoint(now,shift,carry);enabled=false;
    }
    void requireStopped() const {
        if(enabled || !ok)throw std::runtime_error("Unclosed or invalid model clock budget");
    }
};
inline ModelBudget Timing;
}

// Fixed four-owner SDK wait observations; no global wait callstack.
// Initial IRQ seeds and pending stop require independent TCB/queue admission.
// Generic Sleep/Yield are entry counts; complete wait frame intervals overlap
// phases and are not exclusive blocked time. No guest reads, logs or clocks.
namespace melonDS::HGTrace::PilotWait {
constexpr std::uint32_t IRQQueue=0x027E0060;
constexpr std::size_t OwnerCount=4, CauseCount=8, SiteCount=9;

struct OwnerConfig {
    std::uint32_t id=0, low=0, high=0;
    bool initialIRQWait=false;
};
using OwnerConfigs=std::array<OwnerConfig,OwnerCount>;

enum class Stage : std::uint8_t {
    Inactive, LeftSeed, InitialFlag, FastGate, BeforeSleep,
    NativeSleepEntry, Sleeping, AfterFlag, FinalReturn
};
enum class Error : std::uint8_t {
    None, Config, Restart, Opcode, Mode, Owner, Registers, Frame,
    State, Stack, Mask, Queue, Flags, CauseCapacity, GenericCapacity,
    Overflow, Lifecycle
};
enum class Site : std::uint8_t {
    Entry, InitialFlag, FastGate, BeforeSleep, Resume,
    AfterFlag, FinalReturn, GenericSleep, Yield
};

struct CauseKey {
    std::uint32_t mask=0, clear=0, caller=0;
    // false explicitly means clear/caller UNKNOWN, not actual zero-valued args.
    bool knownEntry=false;
};
struct GenericKey { std::uint32_t queue=0, caller=0; };

template<class Counter> struct WaitStats {
    Counter entries=0, fastNotTaken=0, beforeSleep=0, resumes=0;
    Counter spuriousWake=0, usefulWake=0, knownCompleted=0;
    Counter leftSeeded=0, leftBound=0, leftCompleted=0, rightCensored=0;
    Counter fastReturns=0, slowReturns=0, genericSleepEntries=0, yields=0;
    Counter latencyFramesSum=0, latencyFramesMax=0;
};
template<class Counter> struct Cause {
    bool used=false;
    CauseKey key{};
    WaitStats<Counter> stats{};
};
template<class Counter> struct GenericCause {
    bool used=false;
    GenericKey key{};
    Counter entries=0;
};
struct PendingWait {
    Stage stage=Stage::Inactive;
    bool knownEntry=false, leftCensored=false, maskKnown=false, flagMatched=false;
    std::uint32_t mask=0, clear=0, caller=0, entrySP=0;
    std::uint64_t entryFrame=0;
    std::size_t causeIndex=CauseCount;
};
template<class Counter> struct OwnerData {
    OwnerConfig config{};
    PendingWait pending{};
    WaitStats<Counter> stats{};
    std::array<Counter,SiteCount> siteHits{};
    std::array<Cause<Counter>,CauseCount> causes{};
    std::array<GenericCause<Counter>,CauseCount> generic{};
};
template<class Counter> struct WaitSnapshot {
    bool enabled=false, ok=true, started=false, stopped=false;
    bool needsFinalBoundary=false;
    Error error=Error::None;
    std::uint32_t errorPC=0;
    std::uint64_t lastFrame=0, errorFrame=0;
    std::array<Counter,SiteCount> siteHits{};
    std::array<OwnerData<Counter>,OwnerCount> owners{};
};

// The counter type is a bounded arithmetic domain; uint64 is the intended
// integration. A smaller unsigned domain permits finite overflow qualification.
template<class Counter=std::uint64_t> class WaitObserver {
    static_assert(std::is_integral<Counter>::value && std::is_unsigned<Counter>::value,
                  "Wait counters require an unsigned integer domain");
    static_assert(!std::is_same<Counter,bool>::value && sizeof(Counter)<=8,
                  "Wait counters require a 1..64-bit unsigned integer domain");
    using Stats=WaitStats<Counter>;
    using Owner=OwnerData<Counter>;
    WaitSnapshot<Counter> state_{};
    bool everStarted_=false;

    bool fail(Error error,std::uint32_t pc=0,std::uint64_t frame=0) {
        if(state_.ok) {state_.error=error;state_.errorPC=pc;state_.errorFrame=frame;}
        state_.ok=false;state_.enabled=false;return false;
    }
    bool add(Counter& value,std::uint64_t amount=1) {
        const auto limit=std::uint64_t(std::numeric_limits<Counter>::max());
        if(amount>limit-std::uint64_t(value))return fail(Error::Overflow);
        value=Counter(std::uint64_t(value)+amount);return true;
    }
    bool bump(Owner& o,Counter Stats::*field,bool cause=true) {
        if(!add(o.stats.*field))return false;
        return !cause || o.pending.causeIndex==CauseCount ||
               add(o.causes[o.pending.causeIndex].stats.*field);
    }
    void pendingFlag() {
        state_.needsFinalBoundary=false;
        for(const auto& o:state_.owners)
            if(o.pending.stage!=Stage::Inactive)state_.needsFinalBoundary=true;
    }
    static int site(std::uint32_t pc) {
        switch(pc) {
            case 0x020D0E6C:return 0;case 0x020D0EAC:return 1;
            case 0x020D0EB0:return 2;case 0x020D0EC4:return 3;
            case 0x020D0EC8:return 4;case 0x020D0ECC:return 5;
            case 0x020D0ED4:return 6;case 0x020D1E7C:return 7;
            case 0x020D1FA0:return 8;default:return -1;
        }
    }
    static std::uint32_t opcode(unsigned s) {
        constexpr std::uint32_t values[SiteCount]={0xE92D4070,0xE1140000,0x18BD8070,
            0xEB0003EC,0xE5960000,0xE1140000,0xE8BD8070,0xE92D4070,0xE92D41F0};
        return values[s];
    }
    int owner(std::uint32_t sp) const {
        if(sp&3)return -1;
        for(std::size_t i=0;i<OwnerCount;++i)
            if(state_.owners[i].config.low<=sp && sp<=state_.owners[i].config.high)
                return int(i);
        return -1;
    }
    static bool room(const Owner& o,std::uint32_t sp,std::uint32_t bytes) {
        return std::uint64_t(sp)>=std::uint64_t(o.config.low)+bytes && sp<=o.config.high;
    }
    bool body(Owner& o,const std::uint32_t* r) {
        if(!o.pending.maskKnown || o.pending.entrySP<16 ||
           r[13]!=o.pending.entrySP-16)return fail(Error::Stack);
        if(r[4]!=o.pending.mask)return fail(Error::Mask);
        return true;
    }
    bool cause(Owner& o) {
        const auto& p=o.pending;
        for(std::size_t i=0;i<CauseCount;++i) {
            const auto& c=o.causes[i];
            if(c.used && c.key.knownEntry==p.knownEntry && c.key.mask==p.mask &&
               c.key.clear==p.clear && c.key.caller==p.caller) {
                o.pending.causeIndex=i;return true;
            }
        }
        for(std::size_t i=0;i<CauseCount;++i)if(!o.causes[i].used) {
            auto& c=o.causes[i];c.used=true;
            c.key={p.mask,p.clear,p.caller,p.knownEntry};
            o.pending.causeIndex=i;return true;
        }
        return fail(Error::CauseCapacity);
    }
    bool generic(Owner& o,std::uint32_t queue,std::uint32_t caller) {
        for(auto& c:o.generic)
            if(c.used && c.key.queue==queue && c.key.caller==caller)return add(c.entries);
        for(auto& c:o.generic)if(!c.used) {
            c.used=true;c.key={queue,caller};return add(c.entries);
        }
        return fail(Error::GenericCapacity);
    }
    bool complete(Owner& o,std::uint64_t frame,bool fast) {
        if(!bump(o,fast?&Stats::fastReturns:&Stats::slowReturns))return false;
        if(o.pending.knownEntry) {
            if(frame<o.pending.entryFrame)return fail(Error::Frame);
            const auto delta=frame-o.pending.entryFrame;
            if(!bump(o,&Stats::knownCompleted) || !add(o.stats.latencyFramesSum,delta))return false;
            auto& c=o.causes[o.pending.causeIndex];
            if(!add(c.stats.latencyFramesSum,delta))return false;
            if(delta>o.stats.latencyFramesMax)o.stats.latencyFramesMax=Counter(delta);
            if(delta>c.stats.latencyFramesMax)c.stats.latencyFramesMax=Counter(delta);
        } else if(!bump(o,&Stats::leftCompleted))return false;
        o.pending=PendingWait{};return true;
    }
    bool handle(Owner& o,Site s,const std::uint32_t* r,
                std::uint32_t cpsr,std::uint64_t frame) {
        auto& p=o.pending;
        if(s==Site::Entry) {
            if(p.stage!=Stage::Inactive)return fail(Error::State);
            if(!room(o,r[13],16))return fail(Error::Stack);
            p={};p.stage=Stage::InitialFlag;p.knownEntry=true;p.maskKnown=true;
            p.mask=r[1];p.clear=r[0];p.caller=r[14];p.entrySP=r[13];p.entryFrame=frame;
            return cause(o) && bump(o,&Stats::entries);
        }
        if(s==Site::GenericSleep) {
            if(!room(o,r[13],16))return fail(Error::Stack);
            const bool irq=r[14]==0x020D0EC8;
            if(irq || p.stage!=Stage::Inactive) {
                if(!irq || p.stage!=Stage::NativeSleepEntry)return fail(Error::State);
                if(!body(o,r))return false;
                if(r[0]!=IRQQueue)return fail(Error::Queue);
                p.stage=Stage::Sleeping;
            }
            return bump(o,&Stats::genericSleepEntries,false) && generic(o,r[0],r[14]);
        }
        if(s==Site::Yield) {
            if(p.stage!=Stage::Inactive)return fail(Error::State);
            if(!room(o,r[13],24))return fail(Error::Stack);
            return bump(o,&Stats::yields,false);
        }
        if(s==Site::Resume && p.stage==Stage::LeftSeed) {
            if(std::uint64_t(r[13])+16>o.config.high)return fail(Error::Stack);
            p.mask=r[4];p.maskKnown=true;p.entrySP=r[13]+16;
            // Caller and clear remain unknown; knownEntry=false is part of the key.
            if(!cause(o) || !bump(o,&Stats::leftBound) ||
               !add(o.causes[p.causeIndex].stats.leftSeeded))return false;
            p.stage=Stage::Sleeping;
        }
        if(!body(o,r))return false;
        switch(s) {
            case Site::InitialFlag:
                if(p.stage!=Stage::InitialFlag)return fail(Error::State);
                p.flagMatched=(r[0]&p.mask)!=0;p.stage=Stage::FastGate;return true;
            case Site::FastGate: {
                if(p.stage!=Stage::FastGate)return fail(Error::State);
                const bool executed=(cpsr&(1u<<30))==0;
                if(executed!=p.flagMatched)return fail(Error::Flags);
                if(executed)return complete(o,frame,true);
                if(!bump(o,&Stats::fastNotTaken))return false;
                p.stage=Stage::BeforeSleep;return true;
            }
            case Site::BeforeSleep:
                if(p.stage!=Stage::BeforeSleep)return fail(Error::State);
                if(r[0]!=IRQQueue)return fail(Error::Queue);
                if(!bump(o,&Stats::beforeSleep))return false;
                p.stage=Stage::NativeSleepEntry;return true;
            case Site::Resume:
                if(p.stage!=Stage::Sleeping)return fail(Error::State);
                if(!bump(o,&Stats::resumes))return false;
                p.stage=Stage::AfterFlag;return true;
            case Site::AfterFlag:
                if(p.stage!=Stage::AfterFlag)return fail(Error::State);
                p.flagMatched=(r[0]&p.mask)!=0;
                if(!bump(o,p.flagMatched?&Stats::usefulWake:&Stats::spuriousWake))return false;
                p.stage=p.flagMatched?Stage::FinalReturn:Stage::BeforeSleep;return true;
            case Site::FinalReturn:
                if(p.stage!=Stage::FinalReturn)return fail(Error::State);
                if(cpsr&(1u<<30))return fail(Error::Flags);
                return complete(o,frame,false);
            default:return fail(Error::State);
        }
    }

public:
    bool start(const OwnerConfigs& config,std::uint64_t frame) {
        if(everStarted_ || state_.stopped || !state_.ok)return fail(Error::Restart);
        everStarted_=true;state_.started=true;state_.lastFrame=frame;
        for(std::size_t i=0;i<OwnerCount;++i) {
            const auto& a=config[i];
            if((a.low|a.high)&3 || a.low==0 || a.high<=a.low ||
               std::uint64_t(a.high)-a.low<16)return fail(Error::Config);
            for(std::size_t j=0;j<i;++j)
                if(a.id==config[j].id || !(a.high<config[j].low || config[j].high<a.low))
                    return fail(Error::Config);
            auto& o=state_.owners[i];o.config=a;
            if(a.initialIRQWait) {
                o.pending.stage=Stage::LeftSeed;o.pending.leftCensored=true;
                o.pending.entryFrame=frame;
                if(!add(o.stats.leftSeeded))return false;
            }
        }
        state_.enabled=true;pendingFlag();return true;
    }
    void step(std::uint32_t pc,std::uint32_t instruction,const std::uint32_t* r,
              std::uint32_t cpsr,std::uint64_t frame) {
        if(!state_.enabled)return;
        const int index=site(pc);if(index<0)return;
        if(instruction!=opcode(unsigned(index))){fail(Error::Opcode,pc,frame);return;}
        if((cpsr&0x3F)!=0x1F){fail(Error::Mode,pc,frame);return;}
        if(!r){fail(Error::Registers,pc,frame);return;}
        if(frame<state_.lastFrame){fail(Error::Frame,pc,frame);return;}
        const int which=owner(r[13]);if(which<0){fail(Error::Owner,pc,frame);return;}
        state_.lastFrame=frame;auto& o=state_.owners[std::size_t(which)];
        if(!add(state_.siteHits[std::size_t(index)]) || !add(o.siteHits[std::size_t(index)])) {
            state_.errorPC=pc;state_.errorFrame=frame;return;
        }
        if(!handle(o,static_cast<Site>(index),r,cpsr,frame)) {
            // Preserve the original error reason, attach its recognized site/frame.
            state_.errorPC=pc;state_.errorFrame=frame;return;
        }
        pendingFlag();
    }
    void checkpoint(std::uint64_t frame) {
        if(!state_.enabled)return;
        if(frame<state_.lastFrame){fail(Error::Frame,0,frame);return;}
        state_.lastFrame=frame;pendingFlag();
    }
    void stop(std::uint64_t frame) {
        if(state_.stopped)return;
        if(!everStarted_){fail(Error::Lifecycle,0,frame);state_.stopped=true;return;}
        checkpoint(frame);
        if(state_.ok)for(auto& o:state_.owners)
            if(o.pending.stage!=Stage::Inactive && !bump(o,&Stats::rightCensored))break;
        state_.enabled=false;state_.stopped=true;pendingFlag();
    }
    const WaitSnapshot<Counter>& snapshot() const noexcept {return state_;}
};
} // namespace melonDS::HGTrace::PilotWait

namespace melonDS::HGTrace { inline PilotWait::WaitObserver<> Waits; }

// Fixed request classification: one primary Kind/Destination row. Reasons and
// aggregate-OAM counts overlap that primary view and are never added as traffic.
// Range knowledge is not payload lifetime or DMA/GPU completion. Caller/TCM
// pins and aggregate-OAM enclosing roots require external admission.
namespace melonDS::HGTrace::PilotCopy {
constexpr std::uint64_t Space32=std::uint64_t(1)<<32;
struct Range {std::uint64_t begin=0,end=0;};
struct Config {
    Range dtcm{},itcm{};
    bool builtinAsyncPinsQualified=false;
};
enum class Decision : std::uint8_t {
    NoSite, KeepGraphic, SkipNonGraphic, AggregateGraphicOAM, Error
};
enum class Kind : std::uint8_t {
    DMA32,DMA16,CPU32,CPU16,Async32,FillDMA32,ClearCPU32,Count
};
enum class DestClass : std::uint8_t {
    Palette,BGMain,BGSub,OBJMain,OBJSub,LCDC,OAM,Geometry,RAM,Other,Invalid,Count
};
enum class Reason : std::uint8_t {
    RetainedGraphic,RAMCopy,RAMClear,OtherDestination,CrossClass,
    SourceOverflow,DestinationOverflow,Unaligned,InvalidChannel,ZeroSize,
    UnqualifiedAsyncCaller,UnknownSource,GraphicFillUnknown,MixedPalette,
    MixedOAM,AggregateOAM,Count
};
enum class Error : std::uint8_t {
    None,Config,Restart,Opcode,Mode,Registers,Frame,Overflow,Lifecycle
};
constexpr unsigned KindCount=static_cast<unsigned>(Kind::Count);
constexpr unsigned DestCount=static_cast<unsigned>(DestClass::Count);
constexpr unsigned ReasonCount=static_cast<unsigned>(Reason::Count);
constexpr std::uint32_t reasonBit(Reason r) {return 1u<<static_cast<unsigned>(r);}
static_assert(ReasonCount<32,"Reason flags must fit their fixed bitmask");

struct Result {
    Decision decision=Decision::NoSite;
    Kind kind=Kind::Count;
    DestClass dest=DestClass::Other,baseDest=DestClass::Other;
    std::uint32_t pc=0,src=0,dst=0,bytes=0,fillValue=0,channel=0xFFFFFFFF;
    std::uint32_t lr=0,sp=0,cpsr=0,flags=0;
    std::uint64_t frame=0;
    std::array<std::uint32_t,4> args{};
    unsigned elementBytes=0;
    bool fill=false,zero=false,sourceRangeKnown=false,knownAsyncCaller=false;
    bool knownOamCaller=false,inOamRoot=false,coverageUnknown=false;
};
template<class Counter> struct Stats {
    Counter calls=0,bytes=0,zero=0,aggregateCalls=0,aggregateBytes=0;
    std::uint32_t modesMask=0;
    bool seen=false,coverageUnknown=false;
    Result first{},last{};
};
template<class Counter> struct Totals {
    Counter calls=0,requestedBytes=0,zeroCalls=0;
    Counter graphicCopyCalls=0,graphicCopyBytes=0,rawKeptCalls=0,rawKeptBytes=0;
    Counter aggregateOamCalls=0,aggregateOamBytes=0;
    Counter ramCopyCalls=0,ramCopyBytes=0,ramFillCalls=0,ramFillBytes=0;
    Counter graphicFillUnknownCalls=0,graphicFillUnknownBytes=0;
    Counter skippedCalls=0,skippedBytes=0;
};
template<class Counter> struct Snapshot {
    bool enabled=false,ok=true,started=false,stopped=false,coverageUnknown=false;
    Error error=Error::None;
    std::uint32_t errorPC=0;
    std::uint64_t firstFrame=0,lastFrame=0,errorFrame=0;
    Config config{};
    Totals<Counter> totals{};
    std::array<std::array<Stats<Counter>,DestCount>,KindCount> rows{};
    std::array<Stats<Counter>,ReasonCount> reasons{};
};

template<class Counter=std::uint64_t> class CopyCollector {
    static_assert(std::is_integral<Counter>::value && std::is_unsigned<Counter>::value &&
                  !std::is_same<Counter,bool>::value && sizeof(Counter)<=8,
                  "Copy counters require a 1..64-bit unsigned integer domain");
    struct GraphicRange {Range range;DestClass dest;};
    inline static constexpr std::array<GraphicRange,8> Graphics{{
        {{0x05000000,0x05000800},DestClass::Palette},
        {{0x06000000,0x06200000},DestClass::BGMain},
        {{0x06200000,0x06400000},DestClass::BGSub},
        {{0x06400000,0x06600000},DestClass::OBJMain},
        {{0x06600000,0x06800000},DestClass::OBJSub},
        {{0x06800000,0x068A4000},DestClass::LCDC},
        {{0x07000000,0x07000800},DestClass::OAM},
        {{0x04000400,0x04000600},DestClass::Geometry}
    }};
    Snapshot<Counter> state_{};
    bool everStarted_=false;

    bool fail(Error e,std::uint32_t pc=0,std::uint64_t frame=0) {
        if(state_.ok){state_.error=e;state_.errorPC=pc;state_.errorFrame=frame;}
        state_.ok=false;state_.enabled=false;return false;
    }
    bool add(Counter& value,std::uint64_t n=1) {
        const auto limit=std::uint64_t(std::numeric_limits<Counter>::max());
        if(n>limit-std::uint64_t(value))return fail(Error::Overflow);
        value=Counter(std::uint64_t(value)+n);return true;
    }
    static bool overlap(Range a,Range b) {
        return a.begin<a.end && b.begin<b.end && a.begin<b.end && b.begin<a.end;
    }
    static bool contains(Range r,std::uint64_t a) {return r.begin<=a && a<r.end;}
    std::array<Range,3> ramRanges() const {
        return {{{0x02000000,0x02400000},state_.config.dtcm,state_.config.itcm}};
    }
    bool ramBase(std::uint64_t a) const {
        for(auto r:ramRanges())if(contains(r,a))return true;
        return false;
    }
    bool ramCovers(std::uint64_t a,std::uint64_t end) const {
        if(end==a)return ramBase(a);
        std::uint64_t cursor=a;
        // Three fixed ranges, including adjacent/overlapping ranges of the SAME class.
        for(unsigned pass=0;pass<3;++pass) {
            auto far=cursor;
            for(auto r:ramRanges())if(contains(r,cursor) && r.end>far)far=r.end;
            if(far>=end)return true;
            if(far==cursor)return false;
            cursor=far;
        }
        return false;
    }
    DestClass base(std::uint32_t dst) const {
        if(ramBase(dst))return DestClass::RAM;
        for(const auto& g:Graphics)if(contains(g.range,dst))return g.dest;
        return DestClass::Other;
    }
    static bool graphic(DestClass d) {return static_cast<unsigned>(d)<8;}
    DestClass destination(std::uint32_t dst,std::uint32_t bytes,
                          DestClass b,std::uint32_t& flags) const {
        const auto end=std::uint64_t(dst)+bytes;
        if(end>Space32){flags|=reasonBit(Reason::DestinationOverflow);return DestClass::Invalid;}
        if(!bytes)return b; // classify BASE only, not an invented touched interval.
        bool fits=false;
        if(b==DestClass::RAM)fits=ramCovers(dst,end);
        else if(graphic(b)) {
            for(const auto& g:Graphics)if(g.dest==b)fits=end<=g.range.end;
        } else {
            const Range touched{dst,end};bool crosses=false;
            for(const auto& g:Graphics)crosses=crosses||overlap(touched,g.range);
            for(auto r:ramRanges())crosses=crosses||overlap(touched,r);
            if(!crosses)return DestClass::Other;
        }
        if(fits)return b;
        flags|=reasonBit(Reason::CrossClass);return DestClass::Invalid;
    }
    static int site(std::uint32_t pc) {
        switch(pc) {
            case 0x020D3FF4:return 0;case 0x020D4064:return 1;
            case 0x020D4808:return 2;case 0x020D47B8:return 3;
            case 0x020D4194:return 4;case 0x020D3F74:return 5;
            case 0x020D47EC:return 6;default:return -1;
        }
    }
    static std::uint32_t opcode(unsigned k) {
        constexpr std::uint32_t value[KindCount]={0xE92D41F0,0xE92D41F0,0xE081C002,
            0xE3A0C000,0xE92D41F0,0xE92D41F0,0xE081C002};
        return value[k];
    }
    static bool armMode(std::uint32_t cpsr) {
        if(cpsr&32)return false;
        switch(cpsr&31) {
            case 16:case 17:case 18:case 19:case 23:case 27:case 31:return true;
            default:return false;
        }
    }
    static bool asyncCaller(std::uint32_t lr) {
        constexpr std::uint32_t values[]={0x020D0A14,0x020D0A60,0x020D0B54,
            0x020D0614,0x020D0710,0x020D07D0,0x020D088C};
        for(auto v:values)if(lr==v)return true;
        return false;
    }
    static bool oamCaller(std::uint32_t lr) {
        constexpr std::uint32_t values[]={0x020B7DA8,0x020B7E5C,0x020B7E6C,0x020B7E7C,0x020B7E8C};
        for(auto v:values)if(lr==v)return true;
        return false;
    }
    Result classify(unsigned k,const std::uint32_t* regs,std::uint32_t pc,
                    std::uint32_t cpsr,std::uint64_t frame,bool inOamRoot) const {
        Result r;r.kind=static_cast<Kind>(k);r.pc=pc;r.cpsr=cpsr;r.frame=frame;
        r.lr=regs[14];r.sp=regs[13];r.inOamRoot=inOamRoot;
        for(unsigned i=0;i<4;++i)r.args[i]=regs[i];
        r.fill=r.kind==Kind::FillDMA32 || r.kind==Kind::ClearCPU32;
        const bool dma=r.kind==Kind::DMA32 || r.kind==Kind::DMA16 ||
                       r.kind==Kind::Async32 || r.kind==Kind::FillDMA32;
        r.elementBytes=(r.kind==Kind::DMA16 || r.kind==Kind::CPU16)?2:4;
        if(dma)r.channel=regs[0];
        if(r.kind==Kind::FillDMA32){r.dst=regs[1];r.fillValue=regs[2];r.bytes=regs[3];}
        else if(r.kind==Kind::ClearCPU32){r.fillValue=regs[0];r.dst=regs[1];r.bytes=regs[2];}
        else if(dma){r.src=regs[1];r.dst=regs[2];r.bytes=regs[3];}
        else {r.src=regs[0];r.dst=regs[1];r.bytes=regs[2];}
        r.zero=r.bytes==0;if(r.zero)r.flags|=reasonBit(Reason::ZeroSize);
        r.baseDest=base(r.dst);r.dest=destination(r.dst,r.bytes,r.baseDest,r.flags);
        const auto sourceEnd=std::uint64_t(r.src)+r.bytes;
        const bool sourceOverflow=!r.fill && sourceEnd>Space32;
        if(sourceOverflow)r.flags|=reasonBit(Reason::SourceOverflow);
        // Zero/fill do not read a source interval. true is vacuous, not address visibility.
        r.sourceRangeKnown=r.fill || r.zero || (!sourceOverflow && ramCovers(r.src,sourceEnd));
        if(!r.fill && !r.zero && !sourceOverflow && !r.sourceRangeKnown)
            r.flags|=reasonBit(Reason::UnknownSource);
        if(dma && r.channel>3)r.flags|=reasonBit(Reason::InvalidChannel);
        if(!r.zero && ((r.dst%r.elementBytes) || (r.bytes%r.elementBytes) ||
                      (!r.fill && r.src%r.elementBytes)))r.flags|=reasonBit(Reason::Unaligned);
        const auto malformed=reasonBit(Reason::SourceOverflow)|reasonBit(Reason::DestinationOverflow)|
            reasonBit(Reason::InvalidChannel)|reasonBit(Reason::Unaligned)|reasonBit(Reason::CrossClass);
        if(r.flags&malformed)r.dest=DestClass::Invalid;
        r.knownAsyncCaller=r.kind==Kind::Async32 && state_.config.builtinAsyncPinsQualified && asyncCaller(r.lr);
        if(r.kind==Kind::Async32 && !r.knownAsyncCaller)r.flags|=reasonBit(Reason::UnqualifiedAsyncCaller);
        r.knownOamCaller=r.kind==Kind::CPU16 && oamCaller(r.lr);
        if(r.dest==DestClass::Palette && !r.zero &&
           (r.dst-0x05000000)/0x200!=(std::uint64_t(r.dst)+r.bytes-1-0x05000000)/0x200)
            r.flags|=reasonBit(Reason::MixedPalette);
        if(r.dest==DestClass::OAM && !r.zero &&
           (r.dst-0x07000000)/0x400!=(std::uint64_t(r.dst)+r.bytes-1-0x07000000)/0x400)
            r.flags|=reasonBit(Reason::MixedOAM);
        r.decision=Decision::SkipNonGraphic; // also means skipped UNKNOWN, not proven nongraphic.
        if(graphic(r.dest)) {
            if(r.fill) {
                // A zero fill has no touched memory/transfer to complete.
                if(!r.zero)r.flags|=reasonBit(Reason::GraphicFillUnknown);
            } else {
                r.flags|=reasonBit(Reason::RetainedGraphic);r.decision=Decision::KeepGraphic;
                if(r.kind==Kind::CPU16 && r.dest==DestClass::OAM &&
                   (r.bytes==2 || r.bytes==6) && r.knownOamCaller && inOamRoot) {
                    r.decision=Decision::AggregateGraphicOAM;r.flags|=reasonBit(Reason::AggregateOAM);
                }
            }
        } else if(r.dest==DestClass::RAM)r.flags|=reasonBit(r.fill?Reason::RAMClear:Reason::RAMCopy);
        else if(r.dest==DestClass::Other)r.flags|=reasonBit(Reason::OtherDestination);
        const auto unknown=reasonBit(Reason::UnknownSource)|reasonBit(Reason::UnqualifiedAsyncCaller)|
            reasonBit(Reason::OtherDestination)|reasonBit(Reason::GraphicFillUnknown);
        r.coverageUnknown=r.dest==DestClass::Invalid || (r.flags&unknown)!=0;
        return r;
    }
    bool record(Stats<Counter>& s,const Result& r) {
        if(!add(s.calls) || !add(s.bytes,r.bytes) || (r.zero && !add(s.zero)))return false;
        if(r.decision==Decision::AggregateGraphicOAM &&
           (!add(s.aggregateCalls) || !add(s.aggregateBytes,r.bytes)))return false;
        s.modesMask|=1u<<(r.cpsr&31);s.coverageUnknown=s.coverageUnknown||r.coverageUnknown;
        if(!s.seen){s.first=r;s.seen=true;}s.last=r;return true;
    }
    bool totals(const Result& r) {
        auto& t=state_.totals;
        if(!add(t.calls) || !add(t.requestedBytes,r.bytes) || (r.zero && !add(t.zeroCalls)))return false;
        if(r.decision==Decision::KeepGraphic || r.decision==Decision::AggregateGraphicOAM) {
            if(!add(t.graphicCopyCalls) || !add(t.graphicCopyBytes,r.bytes))return false;
            if(r.decision==Decision::KeepGraphic) {
                if(!add(t.rawKeptCalls) || !add(t.rawKeptBytes,r.bytes))return false;
            } else if(!add(t.aggregateOamCalls) || !add(t.aggregateOamBytes,r.bytes))return false;
        } else if(!add(t.skippedCalls) || !add(t.skippedBytes,r.bytes))return false;
        if(r.dest==DestClass::RAM) {
            if(r.fill){if(!add(t.ramFillCalls) || !add(t.ramFillBytes,r.bytes))return false;}
            else if(!add(t.ramCopyCalls) || !add(t.ramCopyBytes,r.bytes))return false;
        }
        if(r.flags&reasonBit(Reason::GraphicFillUnknown))
            if(!add(t.graphicFillUnknownCalls) || !add(t.graphicFillUnknownBytes,r.bytes))return false;
        return true;
    }

public:
    bool start(const Config& config,std::uint64_t frame) {
        // In particular, stop-before-start followed by start cannot revive failure.
        if(everStarted_ || state_.stopped || !state_.ok)return fail(Error::Restart,0,frame);
        everStarted_=true;state_.started=true;state_.config=config;
        state_.firstFrame=state_.lastFrame=frame;
        for(auto r:{config.dtcm,config.itcm}) {
            if(r.begin>r.end || r.end>Space32)return fail(Error::Config,0,frame);
            if(r.begin==r.end)continue;
            for(const auto& g:Graphics)if(overlap(r,g.range))return fail(Error::Config,0,frame);
        }
        state_.enabled=true;return true;
    }
    Result observe(std::uint32_t pc,std::uint32_t instruction,const std::uint32_t* regs,
                   std::uint32_t cpsr,std::uint64_t frame,bool inOamRoot=false) {
        if(!state_.enabled)return {};
        const auto index=site(pc);if(index<0)return {};
        Result error;error.decision=Decision::Error;error.kind=static_cast<Kind>(index);
        error.pc=pc;error.frame=frame;
        if(instruction!=opcode(unsigned(index))){fail(Error::Opcode,pc,frame);return error;}
        if(!armMode(cpsr)){fail(Error::Mode,pc,frame);return error;}
        if(!regs){fail(Error::Registers,pc,frame);return error;}
        if(frame<state_.lastFrame){fail(Error::Frame,pc,frame);return error;}
        state_.lastFrame=frame;
        auto r=classify(unsigned(index),regs,pc,cpsr,frame,inOamRoot);
        state_.coverageUnknown=state_.coverageUnknown||r.coverageUnknown;
        if(!totals(r) || !record(state_.rows[unsigned(r.kind)][unsigned(r.dest)],r)) {
            state_.errorPC=pc;state_.errorFrame=frame;r.decision=Decision::Error;return r;
        }
        for(unsigned i=0;i<ReasonCount;++i)if(r.flags&(1u<<i))
            if(!record(state_.reasons[i],r)) {
                state_.errorPC=pc;state_.errorFrame=frame;r.decision=Decision::Error;return r;
            }
        return r;
    }
    void checkpoint(std::uint64_t frame) {
        if(!state_.enabled)return;
        if(frame<state_.lastFrame){fail(Error::Frame,0,frame);return;}
        state_.lastFrame=frame;
    }
    void stop(std::uint64_t frame) {
        if(state_.stopped)return;
        if(!everStarted_){fail(Error::Lifecycle,0,frame);state_.stopped=true;return;}
        checkpoint(frame);state_.enabled=false;state_.stopped=true;
    }
    const Snapshot<Counter>& snapshot() const noexcept {return state_;}
};
} // namespace melonDS::HGTrace::PilotCopy

// Canonical CPU16 OAM-store oracle; independent of copy-entry request counts.
// No RAM reset, DMA, CPU32 or universal OAM-writer coverage is implied.
namespace melonDS::HGTrace::PilotOam {
constexpr std::size_t OwnerCount=4,EngineCount=2,SiteCount=2;
constexpr std::uint32_t PathPC=0x020B7CC4,PathOpcode=0xE3500000;
constexpr std::uint32_t StorePC=0x020D47D4,StoreOpcode=0xE18130BC;
constexpr std::uint32_t OamBegin=0x07000000,OamSub=0x07000400,OamEnd=0x07000800;
struct OwnerConfig {std::uint32_t id=0,low=0,high=0;};
using OwnerConfigs=std::array<OwnerConfig,OwnerCount>;
struct InstanceConfig {std::uint32_t main=0,sub=0;};
enum class Error : std::uint8_t {
    None,Config,Lifecycle,Restart,Opcode,Mode,Registers,Owner,Instance,
    Frame,AddressOverflow,Alignment,Range,Overflow
};
template<class Counter> struct Stats {
    Counter checks=0,fast=0,slow=0,stores=0,bytes=0;
    // checks counts ONLY the flag predicate. Every admitted AL store counts
    // in stores; siteHits[1] tracks the same store hits globally.
    bool seen=false,hasStore=false;
    std::uint64_t firstFrame=0,lastFrame=0;
    std::uint32_t lastDest=0,lastValue16=0;
};
template<class Counter> struct Snapshot {
    bool enabled=false,ok=true,started=false,stopped=false;
    Error error=Error::None;
    std::uint32_t errorPC=0;
    std::uint64_t errorFrame=0,lastFrame=0;
    OwnerConfigs owners{};
    InstanceConfig instances{};
    std::array<std::array<Stats<Counter>,EngineCount>,OwnerCount> stats{};
    std::array<Counter,SiteCount> siteHits{};
};

template<class Counter=std::uint64_t> class OamObserver {
    static_assert(std::is_integral<Counter>::value && std::is_unsigned<Counter>::value,
                  "OAM counters require an unsigned integer domain");
    static_assert(!std::is_same<Counter,bool>::value && sizeof(Counter)<=8,
                  "OAM counters require a 1..64-bit unsigned integer domain");
    Snapshot<Counter> state_{};
    bool everStarted_=false;
    bool fail(Error e,std::uint32_t pc=0,std::uint64_t frame=0) {
        if(state_.ok){state_.error=e;state_.errorPC=pc;state_.errorFrame=frame;}
        state_.ok=false;state_.enabled=false;return false;
    }
    static bool room(Counter value,std::uint64_t amount) {
        return amount<=std::uint64_t(std::numeric_limits<Counter>::max())-std::uint64_t(value);
    }
    int owner(std::uint32_t sp) const {
        if(sp&3)return -1;
        for(std::size_t i=0;i<OwnerCount;++i)
            if(state_.owners[i].low<=sp && sp<=state_.owners[i].high)return int(i);
        return -1;
    }
    static void touch(Stats<Counter>& s,std::uint64_t frame) {
        if(!s.seen){s.seen=true;s.firstFrame=frame;}
        s.lastFrame=frame;
    }
    static bool systemARM(std::uint32_t cpsr) {return (cpsr&0x3F)==0x1F;}
public:
    bool start(const OwnerConfigs& cfg,InstanceConfig instances,std::uint64_t frame) {
        if(everStarted_ || state_.stopped || !state_.ok)return fail(Error::Restart,0,frame);
        everStarted_=true;state_.started=true;state_.lastFrame=frame;
        // This numeric envelope is NOT heap/type authentication: frontend must
        // supply exact live Heap_Alloc object/engine mapping before enabling.
        if((instances.main|instances.sub)&3 || instances.main<0x02000000 ||
           std::uint64_t(instances.main)+60>0x02400000 ||
           std::uint64_t(instances.sub)!=std::uint64_t(instances.main)+0x1C)
            return fail(Error::Config,0,frame);
        for(std::size_t i=0;i<OwnerCount;++i) {
            const auto& a=cfg[i];
            if((a.low|a.high)&3 || !a.low || a.high<=a.low ||
               std::uint64_t(a.high)-a.low<16)return fail(Error::Config,0,frame);
            for(std::size_t j=0;j<i;++j)
                if(a.id==cfg[j].id || !(a.high<cfg[j].low || cfg[j].high<a.low))
                    return fail(Error::Config,0,frame);
        }
        state_.owners=cfg;state_.instances=instances;state_.enabled=true;return true;
    }
    void step(std::uint32_t pc,std::uint32_t instruction,const std::uint32_t* r,
              std::uint32_t cpsr,std::uint64_t frame) {
        if(!state_.enabled)return; // OFF must not read any register, even at a pinned PC
        if(pc!=PathPC && pc!=StorePC)return;
        const unsigned site=pc==PathPC?0u:1u;
        if(instruction!=(site==0?PathOpcode:StoreOpcode)){fail(Error::Opcode,pc,frame);return;}
        if(cpsr&0x20){fail(Error::Mode,pc,frame);return;} // both exact sites are ARM
        if(!r){fail(Error::Registers,pc,frame);return;}
        std::uint32_t dest=0;
        unsigned engine=0;
        if(site==1) {
            // Exact AL STRH r3,[r1,r12]. r7 is deliberately irrelevant here.
            // No wrapped address may turn a non-OAM store into an OAM sample.
            const auto effective=std::uint64_t(r[1])+std::uint64_t(r[12]);
            if(effective>std::numeric_limits<std::uint32_t>::max()) {
                fail(Error::AddressOverflow,pc,frame);return;
            }
            // Noncanonical/mirrored/RAM destinations belong to CopyCensus.
            // Filter before owner/mode attribution: RAM copies in other modes
            // are outside this OAM-only counter, not fictitious OAM failures.
            if(effective<OamBegin || effective>=OamEnd)return;
            if(effective&1){fail(Error::Alignment,pc,frame);return;}
            if(effective+2>OamEnd){fail(Error::Range,pc,frame);return;}
            dest=std::uint32_t(effective);engine=dest<OamSub?0u:1u;
        }
        if(!systemARM(cpsr)){fail(Error::Mode,pc,frame);return;}
        if(frame<state_.lastFrame){fail(Error::Frame,pc,frame);return;}
        const int which=owner(r[13]);
        if(which<0){fail(Error::Owner,pc,frame);return;}
        if(site==0) {
            if(r[7]==state_.instances.main)engine=0;
            else if(r[7]==state_.instances.sub)engine=1;
            else {fail(Error::Instance,pc,frame);return;}
        }
        auto& s=state_.stats[std::size_t(which)][engine];
        // Preflight ALL increments so a failed sample is not half-committed.
        if(!room(state_.siteHits[site],1) ||
           (site==0 && (!room(s.checks,1) || !room(r[0]?s.fast:s.slow,1))) ||
           (site==1 && (!room(s.stores,1) || !room(s.bytes,2)))) {
            fail(Error::Overflow,pc,frame);return;
        }
        ++state_.siteHits[site];
        if(site==0){++s.checks;if(r[0])++s.fast;else ++s.slow;}
        else {++s.stores;s.bytes=Counter(std::uint64_t(s.bytes)+2);
              s.hasStore=true;s.lastDest=dest;s.lastValue16=r[3]&0xFFFFu;}
        touch(s,frame);state_.lastFrame=frame;
    }
    void checkpoint(std::uint64_t frame) {
        if(!state_.enabled)return;
        if(frame<state_.lastFrame){fail(Error::Frame,0,frame);return;}
        state_.lastFrame=frame;
    }
    void stop(std::uint64_t frame) {
        if(state_.stopped)return;
        if(!everStarted_){fail(Error::Lifecycle,0,frame);state_.stopped=true;return;}
        checkpoint(frame);state_.enabled=false;state_.stopped=true;
    }
    void requireStopped() const {
        if(state_.enabled || !state_.ok || !state_.started || !state_.stopped)
            throw std::runtime_error("Unclosed or invalid OAM counter");
    }
    const Snapshot<Counter>& snapshot() const noexcept {return state_;}
};
} // namespace melonDS::HGTrace::PilotOam

namespace melonDS::HGTrace {
inline PilotCopy::CopyCollector<> Copies;
inline PilotOam::OamObserver<> Oam;
}

// Fixed native predicate views, global per CPSR mode. Positive has the named
// site's semantics; the Sleep call is not busy time. OS views overlap Waits.
namespace melonDS::HGTrace::PilotPoll {
constexpr std::size_t SiteCount=17,ModeCount=32;
enum class Kind : std::uint8_t {BitSet,NonZero,BitClear,MaskMissing,Call};
struct Spec {
    std::uint32_t pc,opcode;
    const char* name;
    const char* semantic;
    Kind kind;
    unsigned valueRegister;
    std::uint32_t fixedMask;
    bool diagnosticWaitView;
};
inline constexpr std::array<Spec,SiteCount> Specs{{
 {0x020D4034,0xE3100102,"DMA32_before","DMA_BUSY_BIT31",Kind::BitSet,0,0x80000000,false},
 {0x020D4058,0xE3100102,"DMA32_after","DMA_BUSY_BIT31",Kind::BitSet,0,0x80000000,false},
 {0x020D40A0,0xE3100102,"DMA16_before","DMA_BUSY_BIT31",Kind::BitSet,0,0x80000000,false},
 {0x020D40C4,0xE3100102,"DMA16_after","DMA_BUSY_BIT31",Kind::BitSet,0,0x80000000,false},
 {0x020D4250,0xE3110102,"WaitDma","DMA_BUSY_BIT31",Kind::BitSet,1,0x80000000,false},
 {0x020CF67C,0xE3100302,"GX_ResetBusy","GX_GEOMETRY_BUSY_BIT27",Kind::BitSet,0,0x08000000,false},
 {0x020CF6F0,0xE3100302,"GX_ClearBusy","GX_GEOMETRY_BUSY_BIT27",Kind::BitSet,0,0x08000000,false},
 {0x020D44D4,0xE35C0000,"GX_AsyncBusy","GX_ASYNC_PARAMS_BUSY",Kind::NonZero,12,0,false},
 {0x020D44EC,0xE3100002,"GX_AsyncFifo","GX_FIFO_NOT_UNDERHALF",Kind::BitClear,0,2,false},
 {0x020D46DC,0xE3510000,"GX_AsyncFastBusy","GX_ASYNC_PARAMS_BUSY",Kind::NonZero,1,0,false},
 {0x01FF85B4,0xE3100102,"GXSyncDMA_before","DMA_BUSY_BIT31",Kind::BitSet,0,0x80000000,false},
 {0x01FF8600,0xE3100102,"GXSyncDMA_after","DMA_BUSY_BIT31",Kind::BitSet,0,0x80000000,false},
 {0x020D0EAC,0xE1140000,"OSWaitIrq_fastcheck","OS_IRQ_MASK_UNSATISFIED",Kind::MaskMissing,0,0,true},
 {0x020D0EC4,0xEB0003EC,"OSWaitIrq_sleepcall","CALL_OS_SLEEPTHREAD",Kind::Call,0,0,true},
 {0x020D0ECC,0xE1140000,"OSWaitIrq_recheck","OS_IRQ_MASK_UNSATISFIED",Kind::MaskMissing,0,0,true},
 {0x020CF7C0,0xE3500000,"GX_ResetMtxPV_recheck","GX_MTX_STACK_BUSY_RETURN",Kind::NonZero,0,0,false},
 {0x020CF7D4,0xE3500000,"GX_ResetMtxPJ_recheck","GX_MTX_STACK_BUSY_RETURN",Kind::NonZero,0,0,false}
}};
enum class Error : std::uint8_t {None,Lifecycle,Restart,Opcode,Mode,Registers,Frame,Overflow};
template<class Counter> struct Stats {
    Counter visits=0,positive=0,negative=0;
    bool seen=false;
    std::uint32_t lastValue=0,lastMask=0,lastSP=0,lastLR=0;
    std::uint64_t firstFrame=0,lastFrame=0;
};
template<class Counter> struct Snapshot {
    bool enabled=false,ok=true,started=false,stopped=false;
    Error error=Error::None;
    std::uint32_t errorPC=0;
    std::uint64_t errorFrame=0,lastFrame=0;
    std::array<std::array<Stats<Counter>,ModeCount>,SiteCount> stats{};
};
template<class Counter=std::uint64_t> class PollObserver {
    static_assert(std::is_integral<Counter>::value && std::is_unsigned<Counter>::value,
                  "Poll counters require unsigned integer domains");
    static_assert(!std::is_same<Counter,bool>::value && sizeof(Counter)<=8,
                  "Poll counter domains are1..64bit unsigned non-bool");
    Snapshot<Counter> state_{};
    bool everStarted_=false;
    bool fail(Error e,std::uint32_t pc=0,std::uint64_t frame=0) {
        if(state_.ok){state_.error=e;state_.errorPC=pc;state_.errorFrame=frame;}
        state_.ok=false;state_.enabled=false;return false;
    }
    static int site(std::uint32_t pc) {
        switch(pc) {
            case 0x020D4034:return 0;case 0x020D4058:return 1;
            case 0x020D40A0:return 2;case 0x020D40C4:return 3;
            case 0x020D4250:return 4;case 0x020CF67C:return 5;
            case 0x020CF6F0:return 6;case 0x020D44D4:return 7;
            case 0x020D44EC:return 8;case 0x020D46DC:return 9;
            case 0x01FF85B4:return 10;case 0x01FF8600:return 11;
            case 0x020D0EAC:return 12;case 0x020D0EC4:return 13;
            case 0x020D0ECC:return 14;case 0x020CF7C0:return 15;
            case 0x020CF7D4:return 16;default:return -1;
        }
    }
    static bool validARM(std::uint32_t cpsr) {
        if(cpsr&0x20)return false;
        switch(cpsr&31u) {
            case 0x10:case 0x11:case 0x12:case 0x13:
            case 0x17:case 0x1B:case 0x1F:return true;
            default:return false;
        }
    }
public:
    bool start(std::uint64_t frame) {
        if(everStarted_ || state_.stopped || !state_.ok)return fail(Error::Restart,0,frame);
        everStarted_=true;state_.started=true;state_.lastFrame=frame;
        state_.enabled=true;return true;
    }
    void step(std::uint32_t pc,std::uint32_t instruction,const std::uint32_t* r,
              std::uint32_t cpsr,std::uint64_t frame) {
        if(!state_.enabled)return; // OFF: no register access, counter or clock
        const int index=site(pc);if(index<0)return;
        const auto& spec=Specs[std::size_t(index)];
        if(instruction!=spec.opcode){fail(Error::Opcode,pc,frame);return;}
        if(!validARM(cpsr)){fail(Error::Mode,pc,frame);return;}
        if(!r){fail(Error::Registers,pc,frame);return;}
        if(frame<state_.lastFrame){fail(Error::Frame,pc,frame);return;}
        const auto value=r[spec.valueRegister];
        // NonZero's mask0 means N/A, not an AND-mask. CALL preserves r4 as
        // diagnostic originating IRQ mask, but never tests it as a predicate.
        const auto mask=(spec.kind==Kind::MaskMissing || spec.kind==Kind::Call)?r[4]:spec.fixedMask;
        bool positive=false;
        switch(spec.kind) {
            case Kind::BitSet:positive=(value&mask)!=0;break;
            case Kind::NonZero:positive=value!=0;break;
            case Kind::BitClear:positive=(value&mask)==0;break;
            case Kind::MaskMissing:positive=(value&mask)==0;break;
            case Kind::Call:positive=true;break;
        }
        auto& s=state_.stats[std::size_t(index)][cpsr&31u];
        const auto maximum=std::numeric_limits<Counter>::max();
        if(s.visits==maximum || (positive?s.positive:s.negative)==maximum) {
            fail(Error::Overflow,pc,frame);return;
        }
        // Atomic sample: no half-committed visit if its outcome overflows.
        ++s.visits;if(positive)++s.positive;else ++s.negative;
        if(!s.seen){s.seen=true;s.firstFrame=frame;}
        s.lastValue=value;s.lastMask=mask;s.lastSP=r[13];s.lastLR=r[14];
        s.lastFrame=frame;state_.lastFrame=frame;
    }
    void checkpoint(std::uint64_t frame) {
        if(!state_.enabled)return;
        if(frame<state_.lastFrame){fail(Error::Frame,0,frame);return;}
        state_.lastFrame=frame;
    }
    void stop(std::uint64_t frame) {
        if(state_.stopped)return;
        if(!everStarted_){fail(Error::Lifecycle,0,frame);state_.stopped=true;return;}
        checkpoint(frame);state_.enabled=false;state_.stopped=true;
    }
    void requireStopped() const {
        if(state_.enabled || !state_.ok || !state_.started || !state_.stopped)
            throw std::runtime_error("Unclosed or invalid fixed poll collector");
    }
    const Snapshot<Counter>& snapshot() const noexcept {return state_;}
};
} // namespace melonDS::HGTrace::PilotPoll

namespace melonDS::HGTrace { inline PilotPoll::PollObserver<> Polls; }

namespace melonDS::HGTrace {
// Cumulative frame-boundary views, never a sum of overlapping traffic or wait views.
inline constexpr std::array<const char*,58> PilotFrameNames={{
    "copy_calls",
    "copy_requested_bytes",
    "copy_graphic_calls",
    "copy_graphic_bytes",
    "copy_raw_kept_calls",
    "copy_raw_kept_bytes",
    "copy_aggregate_oam_calls",
    "copy_aggregate_oam_bytes",
    "copy_zero_calls",
    "copy_coverage_unknown",
    "oam_main_stores",
    "oam_sub_stores",
    "poll0_visits",
    "poll0_positive",
    "poll1_visits",
    "poll1_positive",
    "poll2_visits",
    "poll2_positive",
    "poll3_visits",
    "poll3_positive",
    "poll4_visits",
    "poll4_positive",
    "poll5_visits",
    "poll5_positive",
    "poll6_visits",
    "poll6_positive",
    "poll7_visits",
    "poll7_positive",
    "poll8_visits",
    "poll8_positive",
    "poll9_visits",
    "poll9_positive",
    "poll10_visits",
    "poll10_positive",
    "poll11_visits",
    "poll11_positive",
    "poll12_visits",
    "poll12_positive",
    "poll13_visits",
    "poll13_positive",
    "poll14_visits",
    "poll14_positive",
    "poll15_visits",
    "poll15_positive",
    "poll16_visits",
    "poll16_positive",
    "wait_entries",
    "wait_known_completed",
    "wait_left_completed",
    "wait_before_sleep",
    "wait_resumes",
    "wait_spurious_wake",
    "wait_useful_wake",
    "wait_generic_sleep_entries",
    "wait_yields",
    "callback_battle",
    "callback_link",
    "callback_unknown",
}};
inline std::array<std::uint64_t,58> pilotFrameCounters(
    const PilotCopy::Snapshot<std::uint64_t>& c,
    const PilotOam::Snapshot<std::uint64_t>& o,
    const PilotPoll::Snapshot<std::uint64_t>& p,
    const PilotWait::WaitSnapshot<std::uint64_t>& w,
    const std::array<std::uint64_t,2>& known,std::uint64_t unknown) {
    std::array<std::uint64_t,58> result{};std::size_t index=0;
    const auto add=[](std::uint64_t& dst,std::uint64_t value) {
        if(value>std::numeric_limits<std::uint64_t>::max()-dst)
            throw std::runtime_error("Pilot frame counter sum overflow");
        dst+=value;
    };
    const auto& t=c.totals;
    result[index++]=t.calls;result[index++]=t.requestedBytes;
    result[index++]=t.graphicCopyCalls;result[index++]=t.graphicCopyBytes;
    result[index++]=t.rawKeptCalls;result[index++]=t.rawKeptBytes;
    result[index++]=t.aggregateOamCalls;result[index++]=t.aggregateOamBytes;
    result[index++]=t.zeroCalls;result[index++]=c.coverageUnknown;
    for(std::size_t engine=0;engine<2;++engine) {
        for(const auto& owner:o.stats)add(result[index],owner[engine].stores);
        ++index;
    }
    for(const auto& site:p.stats) {
        for(const auto& mode:site) {
            add(result[index],mode.visits);add(result[index+1],mode.positive);
        }
        index+=2;
    }
    for(const auto& owner:w.owners)add(result[index],owner.stats.entries);
    ++index;
    for(const auto& owner:w.owners)add(result[index],owner.stats.knownCompleted);
    ++index;
    for(const auto& owner:w.owners)add(result[index],owner.stats.leftCompleted);
    ++index;
    for(const auto& owner:w.owners)add(result[index],owner.stats.beforeSleep);
    ++index;
    for(const auto& owner:w.owners)add(result[index],owner.stats.resumes);
    ++index;
    for(const auto& owner:w.owners)add(result[index],owner.stats.spuriousWake);
    ++index;
    for(const auto& owner:w.owners)add(result[index],owner.stats.usefulWake);
    ++index;
    for(const auto& owner:w.owners)add(result[index],owner.stats.genericSleepEntries);
    ++index;
    for(const auto& owner:w.owners)add(result[index],owner.stats.yields);
    ++index;
    result[index++]=known[0];result[index++]=known[1];result[index++]=unknown;
    return result;
}
inline bool recordPilotAux(std::uint32_t pc,std::uint32_t instruction,
    const std::uint32_t* registers,std::uint32_t cpsr,std::uint64_t frame) {
    Waits.step(pc,instruction,registers,cpsr,frame);
    Oam.step(pc,instruction,registers,cpsr,frame);
    Polls.step(pc,instruction,registers,cpsr,frame);
    return Waits.snapshot().ok && Oam.snapshot().ok && Polls.snapshot().ok;
}
inline bool samePilotOwner(std::uint32_t firstSP,std::uint32_t secondSP) {
    const auto& w=Waits.snapshot();
    if(!w.started || !w.ok || ((firstSP|secondSP)&3u))return false;
    for(const auto& o:w.owners)if(o.config.low<=firstSP && firstSP<=o.config.high &&
            o.config.low<=secondSP && secondSP<=o.config.high)return true;
    return false;
}
inline int recordPilotCopy(std::uint32_t pc,std::uint32_t instruction,
    const std::uint32_t* registers,std::uint32_t cpsr,std::uint64_t frame,bool inOamRoot) {
    // Avoid constructing a full request record for unrelated dispatches.
    switch(pc) {
        case 0x020D3FF4:case 0x020D4064:case 0x020D4808:case 0x020D47B8:
        case 0x020D4194:case 0x020D3F74:case 0x020D47EC:break;
        default:return 0;
    }
    const auto copy=Copies.observe(pc,instruction,registers,cpsr,frame,inOamRoot);
    if(!Copies.snapshot().ok || copy.decision==PilotCopy::Decision::Error)return -1;
    return copy.decision==PilotCopy::Decision::SkipNonGraphic ||
           copy.decision==PilotCopy::Decision::AggregateGraphicOAM ? 1 : 0;
}
}
