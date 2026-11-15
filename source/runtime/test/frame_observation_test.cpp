#include "buffered_rows.h"
#include "frame_timing.h"
#include "scene_observer.h"
#include "frame_sampler.h"
#include "hg_trace.h"

#include <cassert>
#include <chrono>
#include <cstdint>
#include <map>
#include <stdexcept>
#include <vector>
#include <set>
#include <memory>

struct FakeClock {
    using duration = std::chrono::nanoseconds;
    using rep = duration::rep;
    using period = duration::period;
    using time_point = std::chrono::time_point<FakeClock>;
    static constexpr bool is_steady = true;
    static rep ticks;
    static time_point now() { return time_point(duration(ticks)); }
};
FakeClock::rep FakeClock::ticks = 0;

struct FakeConsole {
    std::uint32_t RunFrame() {
        FakeClock::ticks += 41;
        return 263;
    }
};

struct FakeSink {
    int writes = 0;
    int flushes = 0;
    bool fail_write = false;
    std::string bytes;
    void write(const std::string& value) {
        ++writes;
        if (fail_write) throw std::runtime_error("sink failed");
        bytes += value;
    }
    void flush() { ++flushes; }
};

int main() {
    {
        using namespace melonDS::HGTrace;
        constexpr auto Read=0x020D8104u, LZ=0x020D4BE8u, Ret=0x02008020u;
        std::array<std::uint32_t,16> regs{};
        auto make=[&](std::uint32_t sp, std::uint32_t lr, std::uint32_t a2, std::uint32_t a3) {
            regs={};regs[0]=0x02011440;regs[1]=0x02204600;regs[2]=a2;
            regs[3]=a3;regs[13]=sp;regs[14]=lr;
        };
        auto s=std::make_unique<AssetObserver<4,2>>();
        s->step(Read,0,nullptr,31,1); // OFF cannot inspect even an invalid argument block
        assert(s->ok && s->count==0);
        s->start();
        make(0x023FFC30,Ret|1,100,0);s->step(Read,0xE92D40F8,regs.data(),31,10);
        make(0x023FEF20,Ret|1,0,1);s->step(Read,0xE92D40F8,regs.data(),31,10);
        regs[0]=0;s->step(Ret,0,regs.data(),0x3F,11);
        assert(s->active==1 && s->events[1].result[0]==0);
        regs[13]=0x023FFC30;regs[0]=~0u;
        s->step(Ret,0,regs.data(),31,11); // wrong ISA
        s->step(Ret,0,regs.data(),0x32,11); // wrong mode
        assert(s->active==1 && s->events[0].exitOrder==0);
        s->step(Ret,0,regs.data(),0x3F,12);
        assert(s->active==0 && s->events[0].result[0]==~0u &&
            s->events[0].last==12 && s->events[0].args[2]==100 &&
            s->events[1].exitOrder<s->events[0].exitOrder);
        make(0x023FFC30,Ret,0,0);
        s->step(LZ,0xE92D40F0,regs.data(),31,12);
        regs[13]-=20;
        s->step(LZ+4,0,regs.data(),31,12);
        s->step(LZ+4,0,regs.data(),18,12); // IRQ does not add to decoder dispatch
        s->step(0x020D8080,0,regs.data(),31,12);
        regs[13]+=20;regs[1]+=64;
        s->step(Ret,0,regs.data(),31,12);
        assert(s->events[2].dispatch==2 && s->events[2].result[1]-s->events[2].args[1]==64);
        make(0x023FFC30,Ret,0,0);
        s->step(0x02000970,0xE3500000,regs.data(),31,12);
        regs[13]-=16;
        s->step(0x020009B8,0xE5620001,regs.data(),31,12);
        s->step(0x020009DC,0xE5620001,regs.data(),31,12);
        regs[13]+=16;
        s->step(Ret,0,regs.data(),31,12);
        assert(s->events[3].dispatch==3 && s->events[3].stores==2);
        s->stop();assert(s->ok && !s->enabled);

        s->start();s->step(0x02000970,0xE3500000,regs.data(),31,12);
        s->step(0x020009B8,0,regs.data(),31,12);
        assert(!s->ok && s->errorPC==0x020009B8);
        s->start();s->step(Read,0,regs.data(),31,0);assert(!s->ok && s->errorPC==Read);
        s->start();s->step(Read,0xE92D40F8,nullptr,31,0);assert(!s->ok);
        s->start();s->step(Read,0xE92D40F8,regs.data(),31,0);s->stop();assert(!s->ok);
        s->start();s->step(Read,0xE92D40F8,regs.data(),31,1);
        s->step(Read,0xE92D40F8,regs.data(),31,1);assert(!s->ok); // ambiguous return key
        s->start();
        for(int i=0;i<4;++i) {
            s->step(Read,0xE92D40F8,regs.data(),31,1);
            s->step(Ret,0,regs.data(),31,1);
        }
        assert(s->ok && s->count==4);
        s->step(Read,0xE92D40F8,regs.data(),31,1);assert(!s->ok); // cap
    }

    {
        // Per-frame export sums primary rows only; cause/reason mirrors and
        // OAM oracle traffic stay separate. Mode detail remains in status.
        using namespace melonDS::HGTrace;
        PilotCopy::Snapshot<std::uint64_t> c;
        PilotOam::Snapshot<std::uint64_t> o;
        PilotPoll::Snapshot<std::uint64_t> p;
        PilotWait::WaitSnapshot<std::uint64_t> w;
        c.totals.graphicCopyBytes=12;c.totals.aggregateOamBytes=6;
        o.stats[0][0].stores=2;o.stats[1][0].stores=1;o.stats[3][1].stores=5;
        p.stats[0][31].visits=9;p.stats[0][31].positive=4;
        p.stats[0][18].visits=2;p.stats[0][18].positive=1;
        w.owners[0].stats.knownCompleted=3;w.owners[2].stats.knownCompleted=7;
        w.owners[0].causes[0].stats.knownCompleted=3;
        const auto v=pilotFrameCounters(c,o,p,w,{2,3},4);
        const auto field=[&](const char* name) {
            for(std::size_t i=0;i<v.size();++i)if(std::string(PilotFrameNames[i])==name)return v[i];
            assert(false);return std::uint64_t{0};
        };
        assert(field("copy_graphic_bytes")==12 && field("copy_aggregate_oam_bytes")==6);
        assert(field("oam_main_stores")==3 && field("oam_sub_stores")==5);
        assert(field("poll0_visits")==11 && field("poll0_positive")==5);
        assert(field("wait_known_completed")==10);
        assert(field("callback_battle")==2 && field("callback_link")==3 && field("callback_unknown")==4);
        for(int which=0;which<3;++which) {
            auto overO=o;auto overP=p;auto overW=w;
            if(which==0)overO.stats[1][0].stores=~std::uint64_t{0};
            if(which==1)overP.stats[0][18].visits=~std::uint64_t{0};
            if(which==2)overW.owners[2].stats.knownCompleted=~std::uint64_t{0};
            bool rejected=false;
            try{(void)pilotFrameCounters(c,overO,overP,overW,{0,0},0);}
            catch(const std::runtime_error&){rejected=true;}
            assert(rejected);
        }
    }
    // Clock-budget accounting partitions scheduler advances, not CPU busy time.
    // DMA can trigger GX inside its branch; charge the branch actually selected.
    {
        using B=melonDS::HGTrace::ModelBranch;
        melonDS::HGTrace::ModelBudget b;
        b.start(100,1,7);
        b.begin(B::Execute,100,1);b.haltSkip(108,128,1);b.end(140,1,3);
        b.begin(B::DMA,140,1);b.end(164,1,0);
        b.begin(B::GX,164,1);b.end(175,1,0);
        b.checkpoint(175,1,0);
        assert(b.ok && b.steps==3 && b.ticks[0]==11 && b.ticks[1]==24);
        assert(b.ticks[2]==20 && b.ticks[3]==20 && b.accounted()==75);
        assert(b.startCarry==7 && b.endCarry==0);
        b.stop(175,1,0);assert(b.ok && !b.enabled);b.requireStopped();
        b.start(200,1,0);b.checkpoint(200,1,0);b.stop(200,1,0);b.requireStopped();
        // Two one-tick intervals remain two raw ticks before shift conversion.
        b.start(300,1,0);b.begin(B::GX,300,1);b.end(301,1,0);
        b.begin(B::GX,301,1);b.end(302,1,0);b.stop(302,1,0);
        assert(b.ok && b.accounted()==2 && (b.accounted()>>b.clockShift)==1);
        // A collector failure stays invalid through stop and diagnostics.
        b.start(400,1,0);b.begin(B::Execute,400,1);b.stop(400,1,0);
        assert(!b.ok && !b.enabled);
        try {b.requireStopped();assert(false);}catch(const std::runtime_error&) {}
        const auto invalid=[&](auto action) {
            b.start(100,1,0);action();assert(!b.ok && !b.enabled);
            b.stop(100,1,0);assert(!b.ok && !b.enabled);
        };
        invalid([&]{b.begin(B::GX,101,1);}); // unaccounted gap
        invalid([&]{b.begin(B::GX,99,1);}); // regressed start
        invalid([&]{b.begin(B::GX,100,2);});
        invalid([&]{b.begin(static_cast<B>(3),100,1);});
        invalid([&]{b.begin(B::GX,100,1);b.begin(B::DMA,100,1);});
        invalid([&]{b.end(100,1,0);}); // no open branch
        invalid([&]{b.begin(B::GX,100,1);b.end(99,1,0);});
        invalid([&]{b.begin(B::GX,100,1);b.end(101,2,0);});
        invalid([&]{b.begin(B::GX,100,1);b.haltSkip(100,101,1);});
        invalid([&]{b.haltSkip(100,101,1);});
        invalid([&]{b.begin(B::Execute,100,1);b.haltSkip(100,101,2);}); // DMA stop is not idle
        invalid([&]{b.begin(B::Execute,100,1);b.haltSkip(100,110,1);b.haltSkip(109,120,1);});
        invalid([&]{b.begin(B::Execute,100,1);b.haltSkip(110,109,1);});
        invalid([&]{b.begin(B::Execute,100,1);b.haltSkip(100,120,1);b.end(110,1,0);});
        invalid([&]{b.begin(B::Execute,100,1);b.haltSkip(110,120,1);b.end(115,1,0);});
        invalid([&]{b.begin(B::Execute,100,1);b.skip=UINT64_MAX;b.haltSkip(100,101,1);});
        invalid([&]{b.begin(B::Execute,100,1);b.ticks[3]=UINT64_MAX;b.haltSkip(100,101,1);b.end(101,1,0);});
        invalid([&]{b.begin(B::Execute,100,1);b.haltSkip(90,100,1);});
        invalid([&]{b.checkpoint(101,1,0);});
        invalid([&]{b.checkpoint(100,2,0);});
        invalid([&]{b.begin(B::GX,100,1);b.checkpoint(100,1,0);});
        invalid([&]{b.begin(B::GX,100,1);b.ticks[0]=UINT64_MAX;b.end(101,1,0);});
        invalid([&]{b.begin(B::GX,100,1);b.steps=UINT64_MAX;b.end(100,1,0);});
        invalid([&]{b.ticks[0]=1;b.checkpoint(100,1,0);});
        invalid([&]{b.ticks[0]=UINT64_MAX;b.ticks[1]=1;b.checkpoint(100,1,0);});
        b.start(100,1,0);b.begin(B::Execute,100,1);
        b.haltSkip(100,100,1);b.haltSkip(105,115,1);b.haltSkip(120,130,1);
        b.end(150,1,0);b.stop(150,1,0);
        assert(b.ok && b.accounted()==50 && b.ticks[2]==30 && b.ticks[3]==20);
        b.start(100,2,0);assert(!b.ok && !b.enabled);
        melonDS::HGTrace::ModelBudget off;
        off.begin(B::GX,999,0);off.haltSkip(100,0,2);off.end(0,0,0);off.checkpoint(999,0,0);
        assert(off.ok && !off.enabled && !off.active && off.steps==0 && off.accounted()==0);
    }

    // A larger physical array must not silently enlarge legacy admission.
    {
        using namespace melonDS::HGTrace;
        auto w=std::make_unique<WorkObserver<20000,1>>();
        std::uint32_t r[16]{};w->start(true,WorkLayout::Graphics);
        for(unsigned i=0;i<16384;++i)w->step(0x022227B4,0x4920,r,0x3F);
        assert(w->ok && w->count==16384);w->step(0x022227B4,0x4920,r,0x3F);
        assert(!w->ok && w->count==16384 && "Legacy event cap must remain16384");
        w->start(true,WorkLayout::Pilot);
        for(unsigned i=0;i<20000;++i)w->step(0x022227B4,0x4920,r,0x3F);
        assert(w->ok && w->count==20000);w->step(0x022227B4,0x4920,r,0x3F);
        assert(!w->ok && w->count==20000);
    }

    // Poll operands are guest-loaded registers; an OS call is not a busy test.
    {
        melonDS::HGTrace::PilotPoll::PollObserver<> poll;assert(poll.start(1));
        std::uint32_t r[16]{};r[0]=0x80000000;
        poll.step(0x020D4034,0xE3100102,r,0x1F,1);
        assert(poll.snapshot().stats[0][31].positive==1);
        r[0]=0;r[4]=0;poll.step(0x020D0EC4,0xEB0003EC,r,0x1F,1);
        assert(poll.snapshot().stats[13][31].visits==1 && poll.snapshot().stats[13][31].positive==1);
        poll.stop(1);poll.requireStopped();
    }

    // Unknown callback targets may yield: count them, do not open a global span.
    {
        using namespace melonDS::HGTrace;
        WorkObserver<8,4> w;w.start(true,WorkLayout::Pilot);
        std::uint32_t r[16]{};r[13]=0x1800;r[14]=0x02001001;r[1]=0x02004001;
        w.step(0x02000E3A,0x4788,r,0x3F);
        assert(w.ok && w.count==0 && w.depth==0 && w.ticks[31]==1 && "Unknown callback must not push");
        r[1]=0x02239731;w.step(0x02000E3A,0x4788,r,0x3F);
        assert(w.count==1 && w.depth==1);w.step(0x02000E3C,0,r,0x3F);
        w.stop();w.requireStopped();
        w.start(true,WorkLayout::Pilot);
        for(unsigned i=0;i<8;++i){r[1]=0x02004001+4*i;w.step(0x02000E3A,0x4788,r,0x3F);}
        assert(w.ok && w.callbackUnknownCalls==8 && w.count==0 && w.ticks[31]==8);
        r[1]=0x02008001;w.step(0x02000E3A,0x4788,r,0x3F);
        assert(!w.ok && w.callbackError==3 && w.callbackUnknownCalls==8);
        w.start(true,WorkLayout::Pilot);w.callbackKnown[0]=UINT64_MAX;r[1]=0x02239731;
        w.step(0x02000E3A,0x4788,r,0x3F);assert(!w.ok && w.callbackError==2);
        w.start(true,WorkLayout::Pilot);w.callbackUnknownCalls=UINT64_MAX;r[1]=0x02004001;
        w.step(0x02000E3A,0x4788,r,0x3F);assert(!w.ok && w.callbackError==2);
        w.start(true,WorkLayout::Pilot);r[1]=0x02239731;
        w.step(0x02000E3A,0x4788,r,0x32);assert(!w.ok && w.callbackError==1);
    }

    // Filtering skips raw events, never interpreter dispatches; OAM aggregation
    // is accepted only under a qualified owner/root and checked against stores.
    {
        using namespace melonDS::HGTrace;
        PilotWait::OwnerConfigs wc{{{0,0x1000,0x2000,false},{1,0x3000,0x4000,false},
                                   {2,0x5000,0x6000,false},{3,0x7000,0x8000,false}}};
        assert(Waits.start(wc,1));PilotCopy::Config mc{};assert(Copies.start(mc,1));
        PilotOam::OwnerConfigs oc{{{0,0x1000,0x2000},{1,0x3000,0x4000},{2,0x5000,0x6000},{3,0x7000,0x8000}}};
        assert(Oam.start(oc,{0x02200000,0x0220001C},1));
        WorkObserver<8,4> w;w.start(true,WorkLayout::Pilot);w.frame=1;
        std::uint32_t r[16]{};r[13]=0x1800;r[14]=0x02001001;
        w.step(0x0200B224,0xB508,r,0x3F);r[13]-=8;r[7]=0x02200000;r[0]=0;
        w.step(0x020B7CC4,0xE3500000,r,0x1F);
        r[0]=0x02200000;r[1]=0x07000000;r[2]=6;r[14]=0x020B7DA8;
        w.step(0x020D47B8,0xE3A0C000,r,0x1F);
        assert(w.ok && w.count==1 && w.depth==1 && "OAM copy must aggregate before push");
        for(unsigned i=0;i<6;i+=2){r[12]=i;r[3]=0x1234;r[7]=99;w.step(0x020D47D4,0xE18130BC,r,0x1F);}
        w.step(0x020B7DA8,0,r,0x1F);r[13]+=8;w.step(0x02001000,0,r,0x3F);
        assert(w.ok && w.depth==0 && w.events[0].complete);w.stop();w.requireStopped();
        assert(Copies.snapshot().totals.aggregateOamBytes==6 && Copies.snapshot().totals.rawKeptCalls==0);
        assert(Oam.snapshot().stats[0][0].bytes==6 && Oam.snapshot().stats[0][0].slow==1);
        // A banked IRQ SP may numerically overlap a thread stack. Its mode
        // still differs from the suspended System root: retain this copy span.
        const auto aggregateBefore=Copies.snapshot().totals.aggregateOamCalls;
        w.start(true,WorkLayout::Pilot);w.frame=1;r[13]=0x1800;r[14]=0x02001001;
        w.step(0x0200B224,0xB508,r,0x3F);r[13]-=8;
        r[0]=0x02200000;r[1]=0x07000000;r[2]=2;r[14]=0x020B7DA8;
        w.step(0x020D47B8,0xE3A0C000,r,0x12);
        assert(w.ok && w.count==2 && w.depth==2 && "IRQ must not aggregate under System root");
        assert(Copies.snapshot().totals.aggregateOamCalls==aggregateBefore);
        w.step(0x020B7DA8,0,r,0x12);r[13]+=8;w.step(0x02001000,0,r,0x3F);
        w.stop();w.requireStopped();
        w.start(true,WorkLayout::Pilot);w.frame=1;r[0]=0x02200000;r[1]=0x02200100;r[2]=4;r[13]=0x1800;r[14]=0x02001000;
        w.step(0x020D4808,0xE081C002,r,0x1F);
        assert(w.ok && w.count==0 && w.ticks[31]==1 && "Filtered RAM must still count dispatch");
        w.stop();w.requireStopped();const auto calls=Copies.snapshot().totals.calls;
        w.start(true,WorkLayout::Graphics);w.step(0x020D4808,0,nullptr,0x1F);
        assert(w.ok && w.count==0 && Copies.snapshot().totals.calls==calls);w.stop();w.requireStopped();
        Waits.stop(1);Copies.stop(1);Oam.stop(1);Oam.requireStopped();
    }

    // Copy classification and the OAM store oracle are separate byte views.
    {
        using C=melonDS::HGTrace::PilotCopy::CopyCollector<>;
        using D=melonDS::HGTrace::PilotCopy::Decision;
        C copy;melonDS::HGTrace::PilotCopy::Config config{};assert(copy.start(config,0));
        std::uint32_t r[16]{};r[0]=0x02200000;r[1]=0x05000000;r[2]=4;r[13]=0x1800;
        const auto result=copy.observe(0x020D4808,0xE081C002,r,0x1F,0);
        assert(result.decision==D::KeepGraphic && copy.snapshot().totals.graphicCopyBytes==4);
        copy.stop(0);assert(copy.snapshot().ok && copy.snapshot().stopped);
        melonDS::HGTrace::PilotOam::OamObserver<> oam;
        melonDS::HGTrace::PilotOam::OwnerConfigs owners{{{0,0x1000,0x2000},{1,0x3000,0x4000},
                                                       {2,0x5000,0x6000},{3,0x7000,0x8000}}};
        assert(oam.start(owners,{0x02200000,0x0220001C},0));
        r[0]=0;r[7]=0x02200000;oam.step(0x020B7CC4,0xE3500000,r,0x1F,0);
        r[1]=0x07000000;r[12]=2;r[3]=0x1234;r[7]=99;
        oam.step(0x020D47D4,0xE18130BC,r,0x1F,0);
        assert(oam.snapshot().stats[0][0].slow==1 && oam.snapshot().stats[0][0].bytes==2);
        oam.stop(0);oam.requireStopped();
    }

    // Failure before start must never be cleared by starting a waiter collector.
    {
        using namespace melonDS::HGTrace::PilotWait;
        WaitObserver<> w;OwnerConfigs cfg{{{0,0x1000,0x2000,false},{1,0x3000,0x4000,false},
                                          {2,0x5000,0x6000,false},{3,0x7000,0x8000,false}}};
        w.stop(1);assert(!w.snapshot().ok && !w.snapshot().enabled);
        assert(!w.start(cfg,2));assert(!w.snapshot().enabled);
    }

    // New direct primitive roots belong only to Pilot, preserving E5 selection.
    {
        using Layout=melonDS::HGTrace::WorkLayout;
        melonDS::HGTrace::WorkObserver<4,2> w;w.start(true,Layout::Pilot);
        std::uint32_t r[16]{};r[13]=0x027E3600;r[14]=0x02001000;
        r[0]=3;r[1]=0x02200000;r[2]=0x06600000;r[3]=512;
        w.step(0x020D3FF4,0xE92D41F0,r,0x1F);
        assert(w.ok && w.count==1 && "Pilot direct DMA entry missing");
        w.step(0x02001000,0,r,0x1F);w.stop();w.requireStopped();
        w.start(true,Layout::Graphics);w.step(0x020D3FF4,0,nullptr,0x1F);
        assert(w.ok && w.count==0);w.stop();w.requireStopped();
    }

    // The complete pilot is a separate opt-in selection; Graphics stays E5.
    {
        using Layout=melonDS::HGTrace::WorkLayout;
        melonDS::HGTrace::WorkObserver<4,2> w;bool admitted=false;
        try {w.start(true,static_cast<Layout>(4));admitted=true;}
        catch(const std::invalid_argument&) {}
        assert(admitted && "Pilot profile is not admitted");
        std::uint32_t r[16]{};r[13]=0x027E3600;r[14]=0x02001000;
        w.step(0x020B620C,0xE12FFF34,r,0x1F);
        assert(w.ok && w.count==1);w.step(0x020B6210,0,r,0x1F);
        // Old SubOBJ call edges are replaced by real primitive entries in Pilot.
        w.step(0x020CFF04,0,nullptr,0x1F);assert(w.ok && w.count==1);
        w.stop();w.requireStopped();
    }

    // A separate graphics profile records real enqueue ABI, without enabling
    // fixed Bag/heap sites by accident. Removing profile admission fails here.
    {
        using Layout=melonDS::HGTrace::WorkLayout;
        melonDS::HGTrace::WorkObserver<8,4> gfx;
        bool admitted=false;
        try {gfx.start(true,static_cast<Layout>(3));admitted=true;}
        catch(const std::invalid_argument&) {}
        assert(admitted && "Graphics profile is not admitted");
        std::uint32_t r[16]{};r[13]=0x027E3600;r[14]=0x02001001;
        r[0]=35;r[1]=512;r[2]=0x02200000;r[3]=512;
        r[4]=0x020B61DC;r[5]=0x022D4834;r[6]=123;r[7]=456;
        gfx.frame=10;gfx.step(0x020205D8,0xB5F8,r,0x3F);
        assert(gfx.ok && gfx.count==1 && gfx.depth==1);
        assert(gfx.events[0].args[0]==35 && gfx.events[0].args[2]==0x02200000);
        assert(gfx.events[0].aux[0]==0x020B61DC && gfx.events[0].aux[1]==0x022D4834);
        assert(gfx.events[0].aux[2]==123 && gfx.events[0].aux[3]==456);
        r[0]=1;gfx.step(0x02001000,0,r,0x3F);
        assert(gfx.ok && gfx.depth==0 && gfx.events[0].complete && gfx.events[0].result==1);
        gfx.stop();gfx.requireStopped();
    }
    // BLX is a call edge: its old LR still belongs to DC_FlushRange.
    // Closing on that old LR instead of PC6210 falsely ends the consumer.
    {
        using Layout=melonDS::HGTrace::WorkLayout;
        melonDS::HGTrace::WorkObserver<8,4> gfx;gfx.start(true,static_cast<Layout>(3));
        std::uint32_t r[16]{};r[13]=0x027E3E00;r[14]=0x02001000;r[0]=0x022D4834;
        gfx.step(0x020B61E8,0xE92D4038,r,0x92);
        r[13]-=16;r[14]=0x020B6208;r[0]=0x02201000;r[1]=512;r[2]=512;r[3]=35;
        r[4]=0x020B61DC;r[5]=0x022D4834;
        gfx.step(0x020B620C,0xE12FFF34,r,0x92);
        assert(gfx.ok && gfx.count==2 && gfx.depth==2);
        assert(gfx.events[1].parent==0 && gfx.events[1].lr==0x020B6208);
        assert(gfx.events[1].aux[0]==0x020B61DC && gfx.events[1].aux[1]==0x022D4834);
        gfx.step(0x020B6208,0,r,0x92);
        assert(gfx.depth==2 && !gfx.events[1].complete);
        gfx.step(0x020B6210,0,r,0xB2);assert(gfx.depth==2); // wrong ISA
        r[13]-=4;gfx.step(0x020B6210,0,r,0x92);assert(gfx.depth==2); // wrong SP
        r[13]+=4;gfx.step(0x020B6210,0,r,0x9F);assert(gfx.depth==2); // wrong mode
        gfx.step(0x020B6210,0,r,0x92);
        assert(gfx.ok && gfx.depth==1 && gfx.events[1].complete);
        assert(gfx.events[1].entry_order==2 && gfx.events[1].exit_order==3);
        r[13]+=16;gfx.step(0x02001000,0,r,0x92);
        assert(gfx.ok && gfx.depth==0 && gfx.events[0].complete);
        assert(gfx.events[0].exit_order==4);gfx.stop();gfx.requireStopped();
    }
    // Every graphics site is a pinned function or explicit call edge. Older
    // profiles ignore those sites, and only graphics copies its extra registers.
    {
        using Layout=melonDS::HGTrace::WorkLayout;
        struct Case {std::uint32_t pc,opcode,ret;bool thumb;};
        const Case cases[]{
            {0x020205D8,0xB5F8,0,true},{0x0202061C,0xB508,0,true},
            {0x020B634C,0xE92D43F8,0,false},{0x020B62EC,0xE92D4038,0,false},
            {0x020B61E8,0xE92D4038,0,false},{0x020B620C,0xE12FFF34,0x020B6210,false},
            {0x020B62C8,0xE59F2010,0,false},{0x020CFF04,0xEB00103A,0x020CFF08,false},
            {0x020CFF18,0xEB00123A,0x020CFF1C,false}};
        std::uint32_t r[16]{};r[13]=0x027E3600;r[14]=0x02001001;r[4]=123;
        for(const auto& c:cases) {
            melonDS::HGTrace::WorkObserver<2,2> n;n.start(true,static_cast<Layout>(3));
            n.step(c.pc,c.opcode,r,c.thumb?0x3F:0x1F);
            assert(n.ok && n.count==1 && n.events[0].aux[0]==123);
            const auto ret=c.ret?c.ret:r[14];
            n.step(ret&~1u,0,r,(ret&1)?0x3F:0x1F);assert(n.ok && n.depth==0);
            n.stop();n.requireStopped();
            n.start(true,static_cast<Layout>(3));n.step(c.pc,c.opcode^1,r,c.thumb?0x3F:0x1F);assert(!n.ok);
            n.start(true,static_cast<Layout>(3));n.step(c.pc,c.opcode,r,c.thumb?0x1F:0x3F);assert(!n.ok);
            for(auto layout:{Layout::R4,Layout::H4,Layout::NativeHeap}) {
                n.start(true,layout);n.step(c.pc,0,nullptr,c.thumb?0x3F:0x1F);
                assert(n.ok && n.count==0);n.stop();n.requireStopped();
            }
        }
        melonDS::HGTrace::WorkObserver<2,1> open;open.start(true,static_cast<Layout>(3));
        open.step(0x020B620C,0xE12FFF34,r,0x1F);open.stop();
        assert(!open.ok && !open.enabled && !open.events[0].complete);
        try {open.requireStopped();assert(false);}catch(const std::runtime_error&) {}
    }
    // A native ARM allocation must be observable only in the explicitly
    // selected heap profile, including its mixed ARM -> Thumb return.
    // This fails if native entry admission/32-bit opcode matching is missing.
    {
        melonDS::HGTrace::WorkObserver<8, 4> native;
        bool admitted = false;
        try {
            native.start(true, static_cast<melonDS::HGTrace::WorkLayout>(2));
            admitted = true;
        } catch (const std::invalid_argument&) {}
        assert(admitted && "Native heap observation profile is not admitted");
        std::uint32_t r[16]{};
        r[0]=0x022C020C;r[1]=52;r[2]=4;
        r[13]=0x023F0000;r[14]=0x02001001;
        native.frame=10;
        native.step(0x020B53A0,0xE92D4008,r,0x1F);
        assert(native.ok && native.count==1 && native.depth==1);
        assert(native.events[0].args[0]==0x022C020C && native.events[0].args[1]==52);
        r[0]=0x022D1234;native.frame=11;
        native.step(0x02001000,0x1C00,r,0x3F);
        assert(native.ok && native.depth==0 && native.events[0].complete);
        assert(native.events[0].result==0x022D1234 && native.events[0].last_frame==11);
        assert(native.events[0].entry_order==1 && native.events[0].exit_order==2);
        assert(native.events[0].parent==0xFFFFFFFFu);
        assert(native.events[0].entry_cpsr==0x1F && native.events[0].exit_cpsr==0x3F);
        native.stop();native.requireStopped();
    }
    // Native SDK ranges require a coherent observed transaction in the same
    // CPU mode. Removing this guard admits a hidden free under an allocation.
    {
        using Native=melonDS::HGTrace::WorkObserver<16,8>;
        using Layout=melonDS::HGTrace::WorkLayout;
        std::uint32_t r[16]{};r[13]=0x023F0000;r[14]=0x02001001;
        for(auto orphan: {0x020B4E90u,0x020B5534u,0x020B4DD4u}) {
            Native n;n.start(true,Layout::NativeHeap);
            n.step(orphan,0,r,0x1F);assert(!n.ok && !n.enabled);
        }
        Native n;n.start(true,Layout::NativeHeap);
        n.step(0x020B53A0,0xE92D4008,r,0x1F);
        n.step(0x020B5534,0,r,0x1F);assert(!n.ok); // wrong root kind
        n.start(true,Layout::NativeHeap);
        n.step(0x020B53A0,0xE92D4008,r,0x1F);
        n.step(0x020B4DD4,0,r,0x1F);assert(!n.ok); // missing Common entry
        n.start(true,Layout::NativeHeap);
        n.step(0x020B53A0,0xE92D4008,r,0x1F);
        n.step(0x020B5108,0,r,0x92);assert(!n.ok); // suspended root is not IRQ context
        n.start(true,Layout::NativeHeap);
        n.step(0x020B53A0,0xE92D4008,r,0x1F);
        n.step(0x020B5108,0,r,0x1F);assert(n.ok); // admitted head alloc helper
        n.step(0x020B4F14,0,r,0x1F);assert(!n.ok); // create helper under alloc
        n.start(true,Layout::NativeHeap);
        n.step(0x020B53A0,0xE92D4008,r,0x1F);
        r[13]-=4096;n.step(0x020B5108,0,r,0x1F);assert(!n.ok); // another thread stack
        r[13]+=4096;
        n.start(true,Layout::NativeHeap);
        n.step(0x020B53A0,0xE92D4008,r,0x1F);
        r[13]-=88;n.step(0x020B4F88,0,r,0x1F);assert(n.ok); // real maximum SDK alloc frame
        r[13]+=88;n.step(0x02001000,0,r,0x3F);n.stop();n.requireStopped();
        n.start(true,Layout::NativeHeap);
        n.step(0x020B53A0,0xE82D4008,r,0x1F);assert(!n.ok); // upper opcode differs
        n.start(true,Layout::NativeHeap);
        n.step(0x020B53A0,0xE92D4008,r,0x3F);assert(!n.ok); // incorrect ISA
        n.start(true,Layout::NativeHeap);
        n.step(0x02223BF4,0,r,0x3F);assert(n.ok && n.count==0); // native-only schema
        n.start(true,Layout::R4);
        n.step(0x020B5534,0,nullptr,0x1F);assert(n.ok && n.count==0);
        n.start(true,Layout::H4);
        n.step(0x020B53A0,0,nullptr,0x1F);assert(n.ok && n.count==0);
        n.stop();n.step(0x020B5534,0,nullptr,0x1F);assert(n.ok);
        // Common is also used legitimately by FrameHeap; no ExpHeap root needed.
        n.start(true,Layout::NativeHeap);
        n.step(0x020B4DD0,0xE92D4010,r,0x1F);
        n.step(0x020B4DD4,0,r,0x1F);
        n.step(0x02001000,0,r,0x3F);assert(n.ok && n.depth==0);
        n.stop();n.requireStopped();
        // Destroy tail-calls CommonFinalize with the same SP/LR.
        n.start(true,Layout::NativeHeap);
        n.step(0x020B5394,0xE59FC000,r,0x1F);
        n.step(0x020B4E4C,0xE92D4010,r,0x1F);
        n.step(0x020B4E50,0,r,0x1F);
        n.step(0x02001000,0,r,0x3F);
        assert(n.ok && n.depth==0 && n.events[1].parent==0);
        assert(n.events[0].parent==0xFFFFFFFFu);
        assert(n.events[0].entry_order==1 && n.events[1].entry_order==2);
        assert(n.events[1].exit_order==3 && n.events[0].exit_order==4);
        n.stop();n.requireStopped();
    }
    // A stopped native window may never present an open API as a safe boundary.
    {
        using Layout=melonDS::HGTrace::WorkLayout;
        melonDS::HGTrace::WorkObserver<8,2> n;
        std::uint32_t r[16]{};r[13]=0x023F0000;r[14]=0x02001001;
        for(auto site: {16,20}) {
            n.start(true,Layout::NativeHeap);
            n.step(melonDS::HGTrace::WorkSites[site].pc,
                   melonDS::HGTrace::WorkSites[site].instruction,r,0x1F);
            n.stop();assert(!n.ok && !n.enabled && !n.events[0].complete);
            try { n.requireStopped();assert(false); } catch(const std::runtime_error&) {}
        }
        n.start(true,Layout::NativeHeap);
        n.step(0x020B53A0,0xE92D4008,r,0x1F);
        r[13]-=4;n.step(0x02001000,0,r,0x3F);assert(n.depth==1);
        r[13]+=4;n.step(0x02001000,0,r,0x32);assert(n.depth==1);
        n.step(0x02001000,0,r,0x1F);assert(n.depth==1);
        n.stop();assert(!n.ok);
        n.start(true,Layout::NativeHeap);n.order=UINT64_MAX;
        n.step(0x020B53A0,0xE92D4008,r,0x1F);assert(!n.ok && n.count==0);
        n.start(true,Layout::NativeHeap);
        n.step(0x020B53A0,0xE92D4008,r,0x1F);n.order=UINT64_MAX;
        n.step(0x02001000,0,r,0x3F);assert(!n.ok && !n.events[0].complete);
        n.start(true,Layout::NativeHeap);
        n.step(0x020B53A0,0xE92D4008,r,0x1F);
        n.step(0x020B5530,0xE92D4038,r,0x1F);
        n.step(0x020B5594,0xE1D023B4,r,0x1F);assert(!n.ok);
        melonDS::HGTrace::WorkObserver<1,2> full;full.start(true,Layout::NativeHeap);
        full.step(0x020B53A0,0xE92D4008,r,0x1F);
        full.step(0x02001000,0,r,0x3F);
        full.step(0x020B5530,0xE92D4038,r,0x1F);assert(!full.ok);
    }
    // Work probe: removing the early OFF gate would dereference this null input.
    using Probe=melonDS::HGTrace::WorkObserver<8, 2>;
    Probe work;
    work.step(0x02223BF4, 0xB5F0, nullptr, 0x3F);
    assert(work.count==0 && work.ticks[31]==0);
    std::uint32_t regs[16]{};regs[13]=0x02300000;regs[14]=0x02001001;regs[0]=17;
    work.start(true);work.frame=10;
    work.step(0x02223BF4,0xB5F0,regs,0x3F); // outer instruction 1
    regs[13]-=24;regs[14]=0x02223C35;
    work.step(0x023DBD00,0xB5FE,regs,0x3F); // nested instruction 2
    work.step(0xFFFF0000,0,regs,0x92); // IRQ excluded from both spans
    work.step(0x023DBD02,0,regs,0x3F); // nested instruction 3
    regs[0]=29;work.step(0x02223C34,0,regs,0x3F); // child returns before outer instruction4
    regs[13]=0x02300000;regs[0]=43;
    work.step(0x02001000,0,regs,0x3F); // outer returns before instruction5
    assert(work.count==2 && work.depth==0 && work.ok);
    assert(work.events[0].inclusive==4 && work.events[0].exclusive==2);
    assert(work.events[1].inclusive==2 && work.events[1].exclusive==2);
    assert(work.events[0].args[0]==17 && work.events[0].result==43);
    assert(work.events[1].result==29 && work.ticks[18]==1);
    // Stop must preserve an incomplete call rather than inventing its return.
    regs[14]=0x02001001;work.step(0x02223BF4,0xB5F0,regs,0x3F);
    work.stop();assert(!work.events[2].complete && work.depth==1);
    work.start(true);work.step(0x02223BF4,0xB5F0,regs,0x3F);
    regs[13]-=24;work.step(0x023DBD00,0xB5FE,regs,0x3F);
    regs[13]-=24;work.step(0x02077D88,0xB570,regs,0x3F);
    assert(!work.ok && !work.enabled); // nesting cannot silently overflow
    work.start(true);work.step(0x02223BF4,0,regs,0x3F);
    assert(!work.ok && work.count==0); // wrong layout/instruction rejected
    try { work.start(false);assert(false); } catch(const std::invalid_argument&) {}
    work.start(true);work.step(0x02223BF4,0xB5F0,regs,0x3F);
    work.ticks[31]=UINT64_MAX;
    work.step(0x02300000,0,regs,0x3F);assert(!work.ok && !work.enabled);
    melonDS::HGTrace::WorkObserver<1,2> full;full.start(true);
    full.step(0x022227B4,0x4920,regs,0x3F); // marker, not a call
    assert(full.count==1 && full.events[0].complete && full.depth==0);
    full.step(0x02222852,0x492E,regs,0x3F);assert(!full.ok && !full.enabled);
    // No supplied address is dereferenced; MMIO cannot cause side effects.
    work.start(true);work.step(0x04000100,0,nullptr,0x3F);
    assert(work.ok && work.count==0);
    try { work.requireStopped();assert(false); } catch(const std::runtime_error&) {}
    work.stop();work.requireStopped();
    work.start(true);regs[13]=0x02300000;regs[14]=0x02001001;
    work.step(0x023DBD00,0xB5FE,regs,0x3F);
    work.step(0x02257E74,0xB538,regs,0x3F); // shared LR/SP: tail call
    work.step(0x02001000,0,regs,0x3F);
    assert(work.depth==0 && work.events[0].inclusive==2 && work.events[1].inclusive==1);
    work.start(true);work.step(0x02223BF4,0xB5F0,regs,0x3F);
    regs[13]-=4;work.step(0x02001000,0,regs,0x3F);assert(work.depth==1);
    regs[13]+=4;work.step(0x02001000,0,regs,0x32);assert(work.depth==1);
    work.step(0x02001000,0,regs,0x1F);assert(work.depth==1); // ARM vs Thumb
    work.step(0x02001000,0,regs,0x3F);assert(work.depth==0);
    work.stop();work.requireStopped();
    work.ok=false;
    try { work.requireStopped();assert(false); } catch(const std::runtime_error&) {}
    work.start(true, melonDS::HGTrace::WorkLayout::H4);
    regs[14]=0x02001001;work.step(0x023DBD00,0xB5F0,regs,0x3F);
    work.step(0x02001000,0,regs,0x3F);assert(work.ok && work.events[0].complete);
    work.start(true);work.step(0x023DBD00,0xB5F0,regs,0x3F);assert(!work.ok);
    try { work.start(true, static_cast<melonDS::HGTrace::WorkLayout>(99));assert(false); }
    catch(const std::invalid_argument&) {}


    // Party attribution reuses Work's register-only spans. Old profiles must
    // ignore the new sites, even when a different overlay reuses an address.
    {
        using namespace melonDS::HGTrace;
        using Layout=WorkLayout;
        WorkObserver<8,4> p;
        p.step(0x023DBE00,0,nullptr,0x3F); // OFF cannot inspect registers
        assert(p.count==0 && p.ticks[31]==0);
        p.start(true,static_cast<Layout>(6));
        std::uint32_t r[16]{};r[13]=0x02300000;r[14]=0x0221D3ED;r[0]=261;r[1]=3;r[2]=0x022D0000;r[4]=7;
        p.step(0x023DBEB4,0xB508,r,0x3F);
        r[13]-=8;r[14]=0x023DBEBD;
        p.step(0x023DBE00,0xB5B0,r,0x3F);
        r[13]-=16;r[14]=0x023DBE15;
        p.step(0x023DBE2C,0xB5B0,r,0x3F);
        r[0]=0x022E0000;
        p.step(0x023DBE14,0,r,0x3F);
        r[13]+=16;r[14]=0x023DBEBD;r[0]=10;
        p.step(0x023DBEBC,0,r,0x3F);
        r[13]+=8;r[14]=0x0221D3ED;
        p.step(0x0221D3EC,0,r,0x3F);
        p.stop();p.requireStopped();
        assert(p.count==3 && p.depth==0 && p.events[2].result==0x022E0000);
        assert(p.events[0].result==10 && p.events[1].result==10);
        assert(p.events[0].aux[0]==7 && p.events[1].parent==0 && p.events[2].parent==1);
        p.start(true,static_cast<Layout>(6));p.step(0x023DBEB4,0,r,0x3F);assert(!p.ok);
        p.start(true,static_cast<Layout>(6));p.step(0x023DBEB4,0xB508,nullptr,0x3F);assert(!p.ok);
        p.start(true,static_cast<Layout>(6));p.step(0x023DBEB4,0xB508,r,0x1F);assert(!p.ok);
        p.start(true,static_cast<Layout>(6));p.step(0x023DBEB4,0xB508,r,0x3F);
        r[13]-=4;p.step(0x0221D3EC,0,r,0x3F);assert(p.depth==1);
        p.stop();assert(!p.ok);r[13]+=4;
        WorkObserver<1,1> small;small.start(true,static_cast<Layout>(6));
        small.step(0x023DBEB4,0xB508,r,0x3F);r[13]-=8;
        small.step(0x023DBE00,0xB5B0,r,0x3F);assert(!small.ok);r[13]+=8;
        p.start(true,static_cast<Layout>(6));p.ticks[31]=UINT64_MAX;
        p.step(0x02004000,0,r,0x3F);assert(!p.ok);
        for(unsigned layout=0;layout<6;++layout) {
            p.start(true,static_cast<Layout>(layout));
            p.step(0x023DBE00,0,nullptr,0x3F);
            assert(p.count==0 && p.ok);p.stop();
        }
    }

    std::vector<std::uint32_t> top(256*192,0x00123456), bottom(256*192,0x00654321);
    const hg_runtime::SampleRect rect{1,2,3,4};
    const auto original=hg_runtime::hashFramebuffer(top.data(),bottom.data(),rect);
    top[2*256+1]^=0x01000000; // ignored alpha, like the RGB capture path
    assert(hg_runtime::hashFramebuffer(top.data(),bottom.data(),rect)==original);
    top[2*256+1]^=1;
    const auto changed=hg_runtime::hashFramebuffer(top.data(),bottom.data(),rect);
    assert(changed.top!=original.top && changed.roi!=original.roi && changed.bottom==original.bottom);
    top[0]^=1;
    assert(hg_runtime::hashFramebuffer(top.data(),bottom.data(),rect).roi==changed.roi);
    for (const auto bad: {hg_runtime::SampleRect{0,0,0,1}, {255,0,2,1}, {0,191,1,2}}) {
        try { hg_runtime::hashFramebuffer(top.data(),bottom.data(),bad);assert(false); }
        catch (const std::invalid_argument&) {}
    }
    std::map<std::uint32_t,std::uint8_t> ram;
    std::size_t reads=0;std::set<std::uint32_t> readAddresses;
    const auto readByte=[&](std::uint32_t address){
        assert(address>=0x02000000 && address<0x02400000);++reads;readAddresses.insert(address);return ram[address];
    };
    auto state=hg_runtime::observeAnim2(readByte);
    assert(!state.slots[0].valid);
    const auto word=[&](std::uint32_t a,std::uint32_t v){for(int i=0;i<4;++i)ram[a+i]=(v>>(8*i))&255;};
    word(0x023DBBE0,0x02300000);word(0x023DBBE4,0x02310000);ram[0x023DBBF3]=1;ram[0x02310000]=1;
    ram[0x0231002E]=0xFD;ram[0x0231002F]=0xFF;ram[0x0231005B]=1;
    state=hg_runtime::observeAnim2(readByte);assert(state.slots[0].valid && state.slots[0].y==-3 && state.slots[0].pose==1);
    word(0x023DBBE4,0xFFFFFFFC);state=hg_runtime::observeAnim2(readByte);assert(!state.slots[0].valid);
    word(0x023DBBE0,0);word(0x023DBBE4,0x02310000);state=hg_runtime::observeAnim2(readByte);assert(!state.slots[0].valid);
    assert(reads>0);
    assert(hg_runtime::mainRamRange(0x023FFFFF,1));
    assert(!hg_runtime::mainRamRange(0x023FFFFF,2));
    assert(!hg_runtime::mainRamRange(0xFFFFFFFF,4));
    word(0x023DBBE0,0x02300000);word(0x023DBBE4,0x02310000);
    word(0x023DBBC8,0x02320000);word(0x023DBBF8,0x02320000);
    word(0x02322448,0xDEADBEEF);
    state=hg_runtime::observeAnim2(readByte);
    assert(state.battle_rng_valid && state.battle_rng==0xDEADBEEF);
    word(0x023DBBF8,0x02330000);readAddresses.clear();
    state=hg_runtime::observeAnim2(readByte);
    assert(!state.battle_rng_valid && !readAddresses.count(0x02322448));
    word(0x023DBBF8,0x02320000);ram[0x023DBBF3]=0;readAddresses.clear();
    state=hg_runtime::observeAnim2(readByte);
    assert(!state.slots[0].valid && !readAddresses.count(0x02310000));
    ram[0x023DBBF3]=1;ram[0x02310000]=0;readAddresses.clear();
    state=hg_runtime::observeAnim2(readByte);
    assert(!state.slots[0].valid && !readAddresses.count(0x0231002E));
    word(0x023DBBE4,0x02311000);ram[0x02311000]=1;ram[0x0231102E]=3;
    state=hg_runtime::observeAnim2(readByte);
    assert(state.slots[0].valid && state.slots[0].y==3);
    word(0x023DBBE4,0x02400000-0xAC);ram[0x02400000-0xAC]=1;
    state=hg_runtime::observeAnim2(readByte);assert(state.slots[0].valid);
    word(0x023DBBE4,0x02400000-0xA8);
    state=hg_runtime::observeAnim2(readByte);assert(!state.slots[0].valid);
    try { hg_runtime::hashFramebuffer(nullptr,bottom.data(),rect);assert(false); }
    catch (const std::invalid_argument&) {}
    int sampleCalls=0;
    const auto sample=[&]{++sampleCalls;FakeClock::ticks+=17;return 5;};
    assert(!hg_runtime::runOptionalSample<FakeClock>(false,sample));
    assert(sampleCalls==0);
    const auto timed=hg_runtime::runOptionalSample<FakeClock>(true,sample);
    assert(timed && timed->value==5 && timed->host_ns==17 && sampleCalls==1);
    FakeConsole console;
    const auto frame = hg_runtime::runObservedFrame<FakeClock>(console);
    assert(frame.scanlines == 263);
    assert(frame.host_runframe_ns == 41);

    hg_runtime::BufferedRows rows;
    FakeSink sink;
    rows.append("header\n");
    rows.append("frame\n");
    assert(sink.writes == 0);
    assert(rows.size() == 13);
    rows.runAndFlush(sink, [] {});
    assert(sink.writes == 1);
    assert(sink.flushes == 1);
    assert(sink.bytes == "header\nframe\n");
    assert(rows.size() == 0);

    hg_runtime::BufferedRows interrupted_rows;
    FakeSink interrupted_sink;
    interrupted_rows.append("before failure\n");
    try {
        interrupted_rows.runAndFlush(interrupted_sink, [] {
            throw std::runtime_error("frame failed");
        });
        assert(false);
    } catch (const std::runtime_error& error) {
        assert(std::string(error.what()) == "frame failed");
    }
    assert(interrupted_sink.bytes == "before failure\n");
    assert(interrupted_sink.flushes == 1);
    assert(interrupted_rows.size() == 0);

    hg_runtime::BufferedRows broken_sink_rows;
    FakeSink broken_sink;
    broken_sink.fail_write = true;
    broken_sink_rows.append("still buffered\n");
    try {
        broken_sink_rows.runAndFlush(broken_sink, [] {
            throw std::runtime_error("original failure");
        });
        assert(false);
    } catch (const std::runtime_error& error) {
        assert(std::string(error.what()) == "original failure");
    }
    assert(broken_sink_rows.size() == 15);

    constexpr std::uint32_t local = 0x0227D4A0;
    constexpr std::uint32_t manager = 0x022A1E90;
    constexpr std::uint32_t pool = 0x022A1FDC;
    constexpr std::uint32_t stride = 0x12C;
    std::map<std::uint32_t, std::uint32_t> words = {
        {local, 75}, {local + 8, 167}, {local + 12, 338},
        {manager + 4, 64}, {manager + 0x124, pool},
        {pool, 1}, {pool + stride, 1}, {pool + 2 * stride, 0},
        {pool + 3 * stride, 1},
    };
    const auto read32 = [&](std::uint32_t address) {
        const auto found = words.find(address);
        return found == words.end() ? std::uint32_t{0} : found->second;
    };
    const auto scene = hg_runtime::observeHgScene(read32);
    assert(scene.map == 75);
    assert(scene.x == 167);
    assert(scene.z == 338);
    assert(scene.active_objects == 3);
}
