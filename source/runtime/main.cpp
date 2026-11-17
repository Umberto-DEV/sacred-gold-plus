// Bounded, offline melonDS test frontend; GPL-3.0-or-later.
#include "Args.h"
#include "buffered_rows.h"
#include "csv_output.h"
#include "frame_timing.h"
#include "frame_sampler.h"
#include "NDS.h"
#include "NDSCart.h"
#include "Savestate.h"
#include "hg_trace.h"
#include "rtc_config.h"
#include "runtime_limits.h"
#include "scene_observer.h"
#include "secure_output.h"
#include <algorithm>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <vector>

using namespace melonDS;
namespace fs = std::filesystem;
static std::vector<u8> readFile(const fs::path& p,size_t limit,const char* label) {
    std::ifstream f(p,std::ios::binary|std::ios::ate);
    if(!f)throw std::runtime_error("Cannot read "+p.string());
    auto len=f.tellg(); if(len<0)throw std::runtime_error("Invalid length");
    size_t size=hg_runtime::RuntimeLimits::fileSize(static_cast<uint64_t>(len),limit,label);
    std::vector<u8> d(size); f.seekg(0);f.read(reinterpret_cast<char*>(d.data()),d.size());
    if(!f)throw std::runtime_error("Short read "+p.string());return d;
}
struct OwnedFile { std::unique_ptr<u8[]> data;u32 size; };
static OwnedFile readRom(const fs::path& p) {
    std::ifstream f(p,std::ios::binary|std::ios::ate);
    if(!f)throw std::runtime_error("Cannot read "+p.string());
    auto len=f.tellg();if(len<0)throw std::runtime_error("Invalid length");
    size_t size=hg_runtime::RuntimeLimits::fileSize(static_cast<uint64_t>(len),hg_runtime::RuntimeLimits::MaxRomBytes,"ROM");
    if(size>0xffffffffu)throw std::runtime_error("ROM exceeds melonDS u32 length");
    auto data=std::make_unique<u8[]>(size);f.seekg(0);f.read(reinterpret_cast<char*>(data.get()),size);
    if(!f)throw std::runtime_error("Short read "+p.string());return {std::move(data),static_cast<u32>(size)};
}
static bool boundedLine(std::istream& input,std::string& line,size_t limit) {
    line.clear();char byte;
    while(input.get(byte)) {
        if(byte=='\n') {
            if(!line.empty()&&line.back()=='\r')line.pop_back();
            return true;
        }
        if(line.size()>=limit)throw std::runtime_error("Input line exceeds 4096 bytes");
        line.push_back(byte);
    }
    return !line.empty();
}
static u32 number(const std::string& s) { size_t pos=0; auto n=std::stoul(s,&pos,0);if(pos!=s.size()||n>0xffffffff)throw std::runtime_error("Invalid number: "+s);return n; }
static u32 keyMask(std::string text) {
    std::transform(text.begin(),text.end(),text.begin(),[](unsigned char c){return std::toupper(c);});
    if(text.empty()||text=="NONE"||text=="-")return 0xfff;
    std::replace(text.begin(),text.end(),'+',' ');std::replace(text.begin(),text.end(),',',' ');
    const std::map<std::string,int> bits={{"A",0},{"B",1},{"SELECT",2},{"START",3},{"RIGHT",4},{"LEFT",5},{"UP",6},{"DOWN",7},{"R",8},{"L",9},{"X",10},{"Y",11}};
    u32 mask=0xfff;std::istringstream in(text);std::string k;while(in>>k){auto it=bits.find(k);if(it==bits.end())throw std::runtime_error("Unknown key "+k);mask&=~(1u<<it->second);}return mask;
}
struct Watch { std::string name;u32 addr;int width; };
struct Freeze { u32 addr,value;int width; };
class Harness {
public:
    fs::path out;hg_runtime::SecureOutputDir outputDir;std::unique_ptr<NDS> nds;u64 frames=0;std::vector<Watch> watches;std::vector<Freeze> freezes;hg_runtime::RuntimeLimits limits;bool hgScene=false;
    hg_runtime::SecureFile csv,commands;hg_runtime::BufferedRows pendingCsv;bool csvHeader=false;
    hg_runtime::SecureFile samples;hg_runtime::BufferedRows pendingSamples;
    bool sampleEnabled=false,sampleFile=false;
    hg_runtime::SecureFile workFile;bool workStarted=false,workReported=false,stateLoaded=false;
    hg_runtime::SecureFile modelFile;hg_runtime::BufferedRows pendingModel;
    bool modelStarted=false,modelReported=false;
    HGTrace::PilotWait::OwnerConfigs pilotOwners{};
    u32 pilotOamMain=0,pilotOamSub=0,pilotITCMLimit=0,pilotDTCMBase=0,pilotDTCMEnd=0;
    hg_runtime::SampleRect sampleRect{0,0,256,160};
    Harness(const fs::path& rom,const fs::path& dir,const fs::path& save,const hg_runtime::RtcConfig& rtc):out(fs::absolute(dir).lexically_normal()),outputDir(dir) {
        NDSArgs args;args.JIT=std::nullopt;nds=std::make_unique<NDS>(std::move(args));
        auto data=readRom(rom);bool ipke=data.size>=16 && std::string(reinterpret_cast<char*>(data.data.get()+12),4)=="IPKE";hgScene=ipke;
        auto cart=NDSCart::ParseROM(std::move(data.data),data.size);
        if(ipke) {
            limits.watch();limits.watch();
            watches.push_back({"game_vblank_counter",0x021D1138,4});
            watches.push_back({"game_frame_counter",0x021D113C,4});
        }
        if(!cart)throw std::runtime_error("ROM parse failed");nds->SetNDSCart(std::move(cart));
        nds->Reset();nds->RTC.SetDateTime(rtc.year,rtc.month,rtc.day,rtc.hour,rtc.minute,rtc.second);
        if(!save.empty()){size_t expected=nds->GetNDSSaveLength();size_t cap=expected?expected:hg_runtime::RuntimeLimits::MaxSramBytes;auto s=readFile(save,cap,"SRAM");nds->SetNDSSave(s.data(),s.size());}
        nds->SetupDirectBoot(rom.filename().string());nds->SetKeyMask(0xfff);nds->Start();
        for(const char* name:{"frames.csv","commands.log","session.txt"})outputDir.requireAbsent(name);
        csv=outputDir.create("frames.csv");commands=outputDir.create("commands.log");
        std::ostringstream text;text<<"melonDS revision 906e9ebb27da8c6a715cd7abab4abfe8a8d29427\nROM="<<fs::absolute(rom)<<"\nRTC="<<rtc.session_text()<<"\nCPU=interpreter\nRenderer=software\nBIOS=FreeBIOS\nFirmware=generated\nFrameTiming=RunFrame-only\nSceneObserver="<<(hgScene?"HG-IPKE":"disabled")<<"\nTracePCInitial="<<(HGTrace::Enabled?"on":"off")<<"\n";
        auto meta=outputDir.create("session.txt");meta.write(text.str());meta.flush();
    }
    void writeFile(const std::string& name,const void* data,size_t len) {
        limits.output(len);outputDir.writeFile(name,data,len);
        std::cout<<"WROTE "<<(out/name)<<" bytes="<<len<<std::endl;
    }
    u32 read(u32 addr,int width) { if(width==1)return nds->ARM9Read8(addr);if(width==2)return nds->ARM9Read16(addr);if(width==4)return nds->ARM9Read32(addr);throw std::runtime_error("Width must be 1, 2 or 4"); }
    void write(u32 addr,u32 value,int width) { if(width==1)nds->ARM9Write8(addr,value);else if(width==2)nds->ARM9Write16(addr,value);else if(width==4)nds->ARM9Write32(addr,value);else throw std::runtime_error("Width must be 1, 2 or 4"); }
    void row(u32 lines,u64 hostRunFrameNs) {
        std::ostringstream line;
        if(!csvHeader){line<<"frame,scanlines,host_runframe_ns,scene_map,scene_x,scene_z,active_objects,arm9_pc,arm7_pc,keymask,render_polygons,geometry_vertices,dma_visits,dma_executed,dma_r10_changes,spi_visits,spi_executed,spi_r10_changes,main_loop_jumps";for(auto& w:watches)line<<','<<hg_runtime::safeCsvField(w.name);line<<'\n';csvHeader=true;}
        const auto scene=hgScene?hg_runtime::observeHgScene([&](u32 address){return read(address,4);}):hg_runtime::HgScene{};
        line<<frames<<','<<lines<<','<<hostRunFrameNs<<','<<scene.map<<','<<scene.x<<','<<scene.z<<','<<scene.active_objects<<",0x"<<std::hex<<nds->GetPC(0)<<",0x"<<nds->GetPC(1)<<",0x"<<nds->KeyInput;
        line<<std::dec<<','<<nds->GPU.GPU3D.RenderNumPolygons<<','<<nds->GPU.GPU3D.NumVertices;
        for(auto& c:HGTrace::Counters)line<<','<<c.visits<<','<<c.executed<<','<<c.r10_changes;
        line<<','<<HGTrace::MainLoopJumps<<std::hex;
        for(auto& w:watches)line<<",0x"<<read(w.addr,w.width);line<<std::dec<<'\n';
        auto text=line.str();limits.output(text.size());pendingCsv.append(text);
    }
    void status() { std::cout<<"STATUS frame="<<frames<<" running="<<nds->IsRunning()<<" arm9_pc=0x"<<std::hex<<nds->GetPC(0)<<" arm7_pc=0x"<<nds->GetPC(1)<<std::dec<<" sram="<<nds->GetNDSSaveLength()<<" cheats="<<nds->AREngine.Cheats.size()<<" watches="<<watches.size()<<" freezes="<<freezes.size()<<" render_polygons="<<nds->GPU.GPU3D.RenderNumPolygons<<" geometry_vertices="<<nds->GPU.GPU3D.NumVertices<<std::endl;for(int i=0;i<2;++i){auto& c=HGTrace::Counters[i];std::cout<<"TRACE site="<<(i?"spi_020de16c":"dma_020d3fa8")<<" enabled="<<HGTrace::Enabled<<" visits="<<c.visits<<" executed="<<c.executed<<" r10_changes="<<c.r10_changes<<" last_before=0x"<<std::hex<<c.last_before<<" last_after=0x"<<c.last_after<<" last_instruction=0x"<<c.last_instruction<<std::dec<<std::endl;}
        if(HGTrace::Work.nativeHeap) {
            std::size_t roots=0;
            for(std::size_t i=0;i<HGTrace::Work.depth;++i)
                if(HGTrace::WorkSites[HGTrace::Work.events[HGTrace::Work.stack[i]].site].heapRoot)++roots;
            std::cout<<"HEAP_TRACE_STATE schema=1 frame="<<frames<<" enabled="<<HGTrace::Work.enabled
                <<" valid="<<HGTrace::Work.ok<<" active_native="<<HGTrace::Work.depth<<" active_roots="<<roots
                <<" order="<<HGTrace::Work.order<<" events="<<HGTrace::Work.count
                <<" safe="<<(HGTrace::Work.enabled && HGTrace::Work.ok && HGTrace::Work.depth==0)
                <<" arm9_cpsr="<<nds->ARM9.CPSR<<" arm9_sp="<<nds->ARM9.R[13]
                <<" arm9_lr="<<nds->ARM9.R[14]<<" arm9_halted="<<unsigned(nds->ARM9.Halted)<<std::endl;
        }
        if(HGTrace::Work.graphics) {
            std::cout<<"GRAPHICS_TRACE_STATE schema=1 frame="<<frames<<" enabled="<<HGTrace::Work.enabled
                <<" valid="<<HGTrace::Work.ok<<" active_spans="<<HGTrace::Work.depth
                <<" order="<<HGTrace::Work.order<<" events="<<HGTrace::Work.count
                <<" safe="<<(HGTrace::Work.enabled && HGTrace::Work.ok && HGTrace::Work.depth==0)
                <<" arm9_cpsr="<<nds->ARM9.CPSR<<" arm9_sp="<<nds->ARM9.R[13]
                <<" arm9_lr="<<nds->ARM9.R[14]<<" arm9_halted="<<unsigned(nds->ARM9.Halted)<<std::endl;
        }
        if(modelStarted) {
            if(!modelReported)HGTrace::Waits.checkpoint(frames);
            const auto& w=HGTrace::Waits.snapshot();
            std::cout<<"WAIT_TRACE_STATE schema=1 frame="<<frames<<" enabled="<<w.enabled<<" valid="<<w.ok
                <<" started="<<w.started<<" stopped="<<w.stopped<<" needs_final_boundary="<<w.needsFinalBoundary
                <<" error="<<unsigned(w.error)<<" error_pc="<<w.errorPC<<" error_frame="<<w.errorFrame;
            for(std::size_t i=0;i<w.siteHits.size();++i)std::cout<<" site"<<i<<'='<<w.siteHits[i];
            std::cout<<std::endl;
            const auto printStats=[](const auto& v) {
                std::cout<<" entries="<<v.entries;
                std::cout<<" fastNotTaken="<<v.fastNotTaken;
                std::cout<<" beforeSleep="<<v.beforeSleep;
                std::cout<<" resumes="<<v.resumes;
                std::cout<<" spuriousWake="<<v.spuriousWake;
                std::cout<<" usefulWake="<<v.usefulWake;
                std::cout<<" knownCompleted="<<v.knownCompleted;
                std::cout<<" leftSeeded="<<v.leftSeeded;
                std::cout<<" leftBound="<<v.leftBound;
                std::cout<<" leftCompleted="<<v.leftCompleted;
                std::cout<<" rightCensored="<<v.rightCensored;
                std::cout<<" fastReturns="<<v.fastReturns;
                std::cout<<" slowReturns="<<v.slowReturns;
                std::cout<<" genericSleepEntries="<<v.genericSleepEntries;
                std::cout<<" yields="<<v.yields;
                std::cout<<" latencyFramesSum="<<v.latencyFramesSum;
                std::cout<<" latencyFramesMax="<<v.latencyFramesMax;
            };
            for(std::size_t i=0;i<w.owners.size();++i) {
                const auto& o=w.owners[i];const auto& p=o.pending;
                std::cout<<"WAIT_OWNER schema=1 frame="<<frames<<" slot="<<i<<" id="<<o.config.id
                    <<" low="<<o.config.low<<" high="<<o.config.high<<" stage="<<unsigned(p.stage)
                    <<" known_entry="<<p.knownEntry<<" left_censored="<<p.leftCensored<<" mask_known="<<p.maskKnown
                    <<" mask="<<p.mask<<" clear="<<p.clear<<" caller="<<p.caller<<" entry_sp="<<p.entrySP
                    <<" entry_frame="<<p.entryFrame<<" cause_index="<<p.causeIndex;
                printStats(o.stats);
                for(std::size_t j=0;j<o.siteHits.size();++j)std::cout<<" site"<<j<<'='<<o.siteHits[j];
                std::cout<<std::endl;
                for(std::size_t j=0;j<o.causes.size();++j)if(o.causes[j].used) {
                    const auto& c=o.causes[j];std::cout<<"WAIT_CAUSE schema=1 frame="<<frames<<" id="<<o.config.id<<" slot="<<j
                        <<" known_entry="<<c.key.knownEntry<<" mask="<<c.key.mask<<" clear="<<c.key.clear<<" caller="<<c.key.caller;
                    printStats(c.stats);std::cout<<std::endl;
                }
                for(std::size_t j=0;j<o.generic.size();++j)if(o.generic[j].used) {
                    const auto& c=o.generic[j];std::cout<<"WAIT_GENERIC schema=1 frame="<<frames<<" id="<<o.config.id<<" slot="<<j
                        <<" queue="<<c.key.queue<<" caller="<<c.key.caller<<" entries="<<c.entries<<std::endl;
                }
            }
            if(!modelReported){HGTrace::Copies.checkpoint(frames);HGTrace::Oam.checkpoint(frames);HGTrace::Polls.checkpoint(frames);}
            const auto& c=HGTrace::Copies.snapshot();
            std::cout<<"COPY_TRACE_STATE schema=1 frame="<<frames<<" enabled="<<c.enabled<<" valid="<<c.ok
                <<" started="<<c.started<<" stopped="<<c.stopped<<" coverage_unknown="<<c.coverageUnknown
                <<" error="<<unsigned(c.error)<<" error_pc="<<c.errorPC<<" error_frame="<<c.errorFrame;
            std::cout<<" calls="<<c.totals.calls;
            std::cout<<" requestedBytes="<<c.totals.requestedBytes;
            std::cout<<" zeroCalls="<<c.totals.zeroCalls;
            std::cout<<" graphicCopyCalls="<<c.totals.graphicCopyCalls;
            std::cout<<" graphicCopyBytes="<<c.totals.graphicCopyBytes;
            std::cout<<" rawKeptCalls="<<c.totals.rawKeptCalls;
            std::cout<<" rawKeptBytes="<<c.totals.rawKeptBytes;
            std::cout<<" aggregateOamCalls="<<c.totals.aggregateOamCalls;
            std::cout<<" aggregateOamBytes="<<c.totals.aggregateOamBytes;
            std::cout<<" ramCopyCalls="<<c.totals.ramCopyCalls;
            std::cout<<" ramCopyBytes="<<c.totals.ramCopyBytes;
            std::cout<<" ramFillCalls="<<c.totals.ramFillCalls;
            std::cout<<" ramFillBytes="<<c.totals.ramFillBytes;
            std::cout<<" graphicFillUnknownCalls="<<c.totals.graphicFillUnknownCalls;
            std::cout<<" graphicFillUnknownBytes="<<c.totals.graphicFillUnknownBytes;
            std::cout<<" skippedCalls="<<c.totals.skippedCalls;
            std::cout<<" skippedBytes="<<c.totals.skippedBytes;
            std::cout<<std::endl;
            const auto printCopySample=[](const char* prefix,const auto& v) {
                std::cout<<' '<<prefix<<"_pc="<<v.pc;
                std::cout<<' '<<prefix<<"_src="<<v.src;
                std::cout<<' '<<prefix<<"_dst="<<v.dst;
                std::cout<<' '<<prefix<<"_bytes="<<v.bytes;
                std::cout<<' '<<prefix<<"_fillValue="<<v.fillValue;
                std::cout<<' '<<prefix<<"_channel="<<v.channel;
                std::cout<<' '<<prefix<<"_lr="<<v.lr;
                std::cout<<' '<<prefix<<"_sp="<<v.sp;
                std::cout<<' '<<prefix<<"_cpsr="<<v.cpsr;
                std::cout<<' '<<prefix<<"_flags="<<v.flags;
                std::cout<<' '<<prefix<<"_frame="<<v.frame;
                std::cout<<' '<<prefix<<"_elementBytes="<<v.elementBytes;
                std::cout<<' '<<prefix<<"_fill="<<v.fill;
                std::cout<<' '<<prefix<<"_zero="<<v.zero;
                std::cout<<' '<<prefix<<"_sourceRangeKnown="<<v.sourceRangeKnown;
                std::cout<<' '<<prefix<<"_knownAsyncCaller="<<v.knownAsyncCaller;
                std::cout<<' '<<prefix<<"_knownOamCaller="<<v.knownOamCaller;
                std::cout<<' '<<prefix<<"_inOamRoot="<<v.inOamRoot;
                std::cout<<' '<<prefix<<"_coverageUnknown="<<v.coverageUnknown;
                std::cout<<' '<<prefix<<"_decision="<<unsigned(v.decision)<<' '<<prefix<<"_kind="<<unsigned(v.kind)
                    <<' '<<prefix<<"_dest="<<unsigned(v.dest)<<' '<<prefix<<"_base_dest="<<unsigned(v.baseDest);
                for(std::size_t i=0;i<v.args.size();++i)std::cout<<' '<<prefix<<"_arg"<<i<<'='<<v.args[i];
            };
            const auto printCopyStats=[&](const auto& row) {
                std::cout<<" calls="<<row.calls<<" bytes="<<row.bytes<<" zero="<<row.zero
                    <<" aggregate_calls="<<row.aggregateCalls<<" aggregate_bytes="<<row.aggregateBytes
                    <<" modes_mask="<<row.modesMask<<" coverage_unknown="<<row.coverageUnknown;
                printCopySample("first",row.first);printCopySample("last",row.last);std::cout<<std::endl;
            };
            for(std::size_t i=0;i<c.rows.size();++i)for(std::size_t j=0;j<c.rows[i].size();++j)if(c.rows[i][j].seen) {
                std::cout<<"COPY_ROW schema=1 frame="<<frames<<" kind="<<i<<" dest="<<j;printCopyStats(c.rows[i][j]);
            }
            for(std::size_t i=0;i<c.reasons.size();++i)if(c.reasons[i].seen) {
                std::cout<<"COPY_REASON schema=1 frame="<<frames<<" reason="<<i;printCopyStats(c.reasons[i]);
            }
            const auto& oam=HGTrace::Oam.snapshot();
            std::cout<<"OAM_TRACE_STATE schema=1 frame="<<frames<<" enabled="<<oam.enabled<<" valid="<<oam.ok
                <<" started="<<oam.started<<" stopped="<<oam.stopped<<" error="<<unsigned(oam.error)
                <<" error_pc="<<oam.errorPC<<" error_frame="<<oam.errorFrame
                <<" path_hits="<<oam.siteHits[0]<<" store_hits="<<oam.siteHits[1]<<std::endl;
            for(std::size_t i=0;i<oam.stats.size();++i)for(std::size_t j=0;j<oam.stats[i].size();++j) {
                const auto& v=oam.stats[i][j];if(!v.seen)continue;
                std::cout<<"OAM_ROW schema=1 frame="<<frames<<" owner="<<oam.owners[i].id<<" engine="<<j
                    <<" checks="<<v.checks<<" fast="<<v.fast<<" slow="<<v.slow<<" stores="<<v.stores<<" bytes="<<v.bytes
                    <<" first_frame="<<v.firstFrame<<" last_frame="<<v.lastFrame<<" has_store="<<v.hasStore
                    <<" last_dest="<<v.lastDest<<" last_value16="<<v.lastValue16<<std::endl;
            }
            const auto& poll=HGTrace::Polls.snapshot();
            std::cout<<"POLL_TRACE_STATE schema=1 frame="<<frames<<" enabled="<<poll.enabled<<" valid="<<poll.ok
                <<" started="<<poll.started<<" stopped="<<poll.stopped<<" error="<<unsigned(poll.error)
                <<" error_pc="<<poll.errorPC<<" error_frame="<<poll.errorFrame<<std::endl;
            for(std::size_t i=0;i<poll.stats.size();++i)for(std::size_t j=0;j<poll.stats[i].size();++j) {
                const auto& v=poll.stats[i][j];if(!v.seen)continue;const auto& spec=HGTrace::PilotPoll::Specs[i];
                std::cout<<"POLL_ROW schema=1 frame="<<frames<<" site="<<i<<" pc="<<spec.pc<<" mode="<<j
                    <<" visits="<<v.visits<<" positive="<<v.positive<<" negative="<<v.negative
                    <<" last_value="<<v.lastValue<<" last_mask="<<v.lastMask<<" last_sp="<<v.lastSP<<" last_lr="<<v.lastLR
                    <<" first_frame="<<v.firstFrame<<" last_frame="<<v.lastFrame
                    <<" diagnostic_wait="<<spec.diagnosticWaitView<<" semantic="<<spec.semantic<<std::endl;
            }
            std::cout<<"PILOT_CALLBACK_STATE schema=1 frame="<<frames<<" event_limit="<<HGTrace::Work.eventLimit
                <<" known_battle="<<HGTrace::Work.callbackKnown[0]<<" known_link="<<HGTrace::Work.callbackKnown[1]
                <<" unknown_calls="<<HGTrace::Work.callbackUnknownCalls<<" error="<<unsigned(HGTrace::Work.callbackError)<<std::endl;
            for(std::size_t i=0;i<HGTrace::Work.callbackUnknown.size();++i)if(HGTrace::Work.callbackUnknown[i].used) {
                const auto& v=HGTrace::Work.callbackUnknown[i];
                std::cout<<"PILOT_CALLBACK_UNKNOWN schema=1 frame="<<frames<<" slot="<<i<<" target="<<v.target<<" calls="<<v.calls
                    <<" first_frame="<<v.firstFrame<<" last_frame="<<v.lastFrame<<" last_sp="<<v.lastSP
                    <<" last_lr="<<v.lastLR<<" last_arg="<<v.lastArg<<std::endl;
            }
            std::cout<<"PILOT_DISPATCH_STATE frame="<<frames;
            for(std::size_t i=0;i<HGTrace::Work.ticks.size();++i)std::cout<<" mode"<<i<<'='<<HGTrace::Work.ticks[i];
            std::cout<<std::endl;
            auto& b=HGTrace::Timing;
            if(!modelReported)b.checkpoint(nds->ARM9Timestamp,nds->ARM9ClockShift,nds->ARM9.Cycles);
            std::cout<<"MODEL_CLOCK_STATE schema=1 frame="<<frames<<" enabled="<<b.enabled
                <<" valid="<<b.ok<<" active="<<b.active<<" clock_shift="<<b.clockShift
                <<" start_ts="<<b.startTS<<" end_ts="<<b.lastTS<<" steps="<<b.steps
                <<" gx="<<b.ticks[0]<<" dma="<<b.ticks[1]<<" execute_residual="<<b.ticks[2]
                <<" halt_skip="<<b.ticks[3]<<" carry_start="<<b.startCarry<<" carry_end="<<b.endCarry<<std::endl;
        }
    }
    u32 pilotWord(u32 address) const {
        if((address&3u) || address<0x02000000 || address>0x023FFFFC)
            throw std::runtime_error("Pilot metadata outside MainRAM");
        const auto i=address-0x02000000;
        return u32(nds->MainRAM[i]) | (u32(nds->MainRAM[i+1])<<8) |
            (u32(nds->MainRAM[i+2])<<16) | (u32(nds->MainRAM[i+3])<<24);
    }
    HGTrace::PilotWait::OwnerConfigs configurePilotOwners() {
        const auto& cpu=nds->ARM9;
        std::cout<<std::dec<<"PILOT_TCM_ATTEMPT frame="<<frames<<" control="<<cpu.CP15Control
            <<" dtcm_base="<<cpu.DTCMBase<<" dtcm_mask="<<cpu.DTCMMask<<" itcm_limit="<<cpu.ITCMSize<<std::endl;
        if(cpu.DTCMBase!=0x027E0000 || cpu.DTCMMask!=0xFFFFC000 ||
                cpu.ITCMSize<0x01FFA000 || cpu.ITCMSize>0x02000000 ||
                (cpu.CP15Control&0xF0000u)!=0x50000u)
            throw std::runtime_error("Unqualified pilot TCM mapping");
        pilotITCMLimit=cpu.ITCMSize;pilotDTCMBase=cpu.DTCMBase;pilotDTCMEnd=cpu.DTCMBase+0x4000;
        const auto info=pilotWord(0x023FFFA0);
        if(info<0x02000000 || info>0x023FFFF0 || pilotWord(info)!=0 || pilotWord(info+12)!=0)
            throw std::runtime_error("Pilot thread boundary is not quiescent");
        const auto current=pilotWord(info+4);auto node=pilotWord(info+8);
        HGTrace::PilotWait::OwnerConfigs config{};unsigned count=0,ids=0;bool idle=false;
        constexpr u32 priorities[4]={16,32,20,4};
        while(node) {
            if(count==4 || (node&3u) || node<0x02000000 || node>0x023FFF40)
                throw std::runtime_error("Pilot thread list outside four-owner contract");
            const auto id=pilotWord(node+0x6C),priority=pilotWord(node+0x70);
            const auto low=pilotWord(node+0x90),high=pilotWord(node+0x94);
            const auto savedSP=pilotWord(node+0x38),state=pilotWord(node+0x64),queue=pilotWord(node+0x78);
            const auto savedCPSR=pilotWord(node),savedLR=pilotWord(node+0x3C),savedPC=pilotWord(node+0x40);
            if(id>=4 || (ids&(1u<<id)) || priority!=priorities[id] || (low|high|savedSP)&3u ||
                    low>=high || savedSP<low || savedSP>high || (savedCPSR&0x3Fu)!=0x1Fu ||
                    !((0x02000000<=low && high<=0x02400000) || (0x027E0000<=low && high<=0x027E4000)))
                throw std::runtime_error("Unqualified pilot owner or stack");
            ids|=1u<<id;
            if(node==current) {
                if(id!=1 || state!=1 || cpu.Halted!=1 || (cpu.CPSR&0x3Fu)!=0x1Fu ||
                        nds->GetPC(0)!=0x020D3F64 || cpu.R[14]!=0x020D21F8 ||
                        cpu.R[13]<low || cpu.R[13]>high)
                    throw std::runtime_error("Pilot current thread is not admitted idle");
                idle=true;
            } else if(state!=0 || savedLR!=0x020D1920 || savedPC!=0x020D2320 ||
                    !(savedCPSR&0x80u) || (id==0?queue!=HGTrace::PilotWait::IRQQueue:queue!=0))
                throw std::runtime_error("Pilot initial waiter context is not admitted");
            config[count++]={id,low,high,node!=current && queue==HGTrace::PilotWait::IRQQueue};
            std::cout<<std::dec<<"PILOT_OWNER_CONFIG frame="<<frames<<" id="<<id<<" tcb="<<node
                <<" low="<<low<<" high="<<high<<" state="<<state<<" queue="<<queue
                <<" initial_irq_wait="<<config[count-1].initialIRQWait
                <<" saved_pc_plus4="<<savedPC<<" saved_lr="<<savedLR<<std::endl;
            node=pilotWord(node+0x68);
        }
        if(count!=4 || ids!=15 || !idle)throw std::runtime_error("Incomplete pilot owner set");
        pilotOamMain=pilotWord(0x021D0EB0);
        if((pilotOamMain&3u) || pilotOamMain<0x02000000 || pilotOamMain>0x023FFFC4 ||
                pilotWord(pilotOamMain)!=0 || pilotWord(pilotOamMain+0x1C)!=1)
            throw std::runtime_error("Unqualified pilot OAM manager");
        pilotOamSub=pilotOamMain+0x1C;
        std::cout<<std::dec<<"PILOT_MEMORY frame="<<frames<<" cp15_control="<<cpu.CP15Control
            <<" dtcm_setting="<<cpu.DTCMSetting<<" itcm_setting="<<cpu.ITCMSetting
            <<" dtcm_base="<<pilotDTCMBase<<" dtcm_mask="<<cpu.DTCMMask<<" itcm_limit="<<pilotITCMLimit
            <<" oam_main="<<pilotOamMain<<" oam_sub="<<pilotOamSub
            <<" oam_main_fast="<<pilotWord(pilotOamMain+0x14)<<" oam_sub_fast="<<pilotWord(pilotOamSub+0x14)<<std::endl;
        return config;
    }
    void modelRow() {
        if(!modelStarted || modelReported)return;
        auto& b=HGTrace::Timing;
        if(!b.enabled && b.ok)throw std::runtime_error("Model clock budget unexpectedly inactive");
        b.checkpoint(nds->ARM9Timestamp,nds->ARM9ClockShift,nds->ARM9.Cycles);
        HGTrace::Waits.checkpoint(frames);HGTrace::Copies.checkpoint(frames);
        HGTrace::Oam.checkpoint(frames);HGTrace::Polls.checkpoint(frames);
        if(!HGTrace::Copies.snapshot().ok || !HGTrace::Oam.snapshot().ok || !HGTrace::Polls.snapshot().ok) {
            std::cerr<<"PILOT_COUNTER_ERROR frame="<<frames
                <<" copy="<<unsigned(HGTrace::Copies.snapshot().error)<<" copy_pc="<<HGTrace::Copies.snapshot().errorPC
                <<" oam="<<unsigned(HGTrace::Oam.snapshot().error)<<" oam_pc="<<HGTrace::Oam.snapshot().errorPC
                <<" poll="<<unsigned(HGTrace::Polls.snapshot().error)<<" poll_pc="<<HGTrace::Polls.snapshot().errorPC<<std::endl;
            throw std::runtime_error("Invalid bounded pilot counter");
        }
        if(!HGTrace::Waits.snapshot().ok) {
            const auto& w=HGTrace::Waits.snapshot();
            std::cerr<<"WAIT_ERROR code="<<unsigned(w.error)<<" pc="<<w.errorPC<<" frame="<<w.errorFrame<<std::endl;
            throw std::runtime_error("Invalid pilot wait observation");
        }
        if(nds->ARM9.DTCMBase!=pilotDTCMBase || nds->ARM9.DTCMMask!=0xFFFFC000 ||
                nds->ARM9.ITCMSize!=pilotITCMLimit || (nds->ARM9.CP15Control&0xF0000u)!=0x50000u)
            throw std::runtime_error("Pilot TCM mapping changed");
        std::ostringstream row;
        row<<frames<<','<<b.clockShift<<','<<b.startTS<<','<<b.lastTS;
        for(auto ticks:b.ticks)row<<','<<ticks;
        row<<','<<b.steps<<','<<b.startCarry<<','<<b.endCarry<<','<<b.ok;
        const auto counters=HGTrace::pilotFrameCounters(HGTrace::Copies.snapshot(),HGTrace::Oam.snapshot(),
            HGTrace::Polls.snapshot(),HGTrace::Waits.snapshot(),HGTrace::Work.callbackKnown,HGTrace::Work.callbackUnknownCalls);
        for(auto value:counters)row<<','<<value;
        row<<'\n';
        const auto text=row.str();limits.output(text.size());pendingModel.append(text);
        if(!b.ok)throw std::runtime_error("Invalid ARM9 model clock partition");
        if(!HGTrace::Work.ok)throw std::runtime_error("Invalid bounded pilot work graph");
    }
    void sampleFrame() {
        struct Visual { hg_runtime::FrameHashes hashes;hg_runtime::AnimSample anim; };
        const auto observed=hg_runtime::runOptionalSample<std::chrono::steady_clock>(sampleEnabled,[&]{
            void* top=nullptr;void* bottom=nullptr;
            if(!nds->GPU.GetFramebuffers(&top,&bottom))throw std::runtime_error("No RAM framebuffer");
            auto hashes=hg_runtime::hashFramebuffer(static_cast<const u32*>(top),static_cast<const u32*>(bottom),sampleRect);
            // observeAnim2 bounds-checks indirect pointers. Raw main RAM reads
            // cannot trigger guest MMIO, filesystem work or RNG calls.
            auto anim=hgScene?hg_runtime::observeAnim2([&](u32 a){return nds->MainRAM[a-0x02000000];}):hg_runtime::AnimSample{};
            return Visual{hashes,anim};
        });
        if(!observed)return;
        const auto& a=observed->value.anim;const auto& h=observed->value.hashes;
        std::ostringstream line;line<<frames<<','<<observed->host_ns<<','<<std::hex<<h.top<<','<<h.bottom<<','<<h.roi<<std::dec;
        line<<','<<a.hits<<','<<a.on<<','<<a.busy<<','<<a.copies<<','<<a.bs<<','<<a.battle_rng_valid<<','<<a.battle_rng;
        for(const auto& s:a.slots)line<<','<<s.od<<','<<s.pic<<','<<s.rng<<','<<s.bs<<','<<s.valid<<','<<unsigned(s.used)<<','<<unsigned(s.phase)<<','<<unsigned(s.left)<<','<<unsigned(s.wait)<<','<<unsigned(s.envelope)<<','<<unsigned(s.suspended)<<','<<s.y<<','<<s.width<<','<<s.height<<','<<unsigned(s.pose)<<','<<s.shadow<<','<<s.crop;
        line<<'\n';auto text=line.str();limits.output(text.size());pendingSamples.append(text);
    }
    void reportAssets() {
        const auto& a=HGTrace::Assets;
        std::string header="pc,first_frame,last_frame,entry_order,exit_order,lr,sp,cpsr";
        for(unsigned i=0;i<8;++i)header+=",r"+std::to_string(i);
        header+=",return_r0,return_r1,return_r2,decoder_dispatch,backward_stores\n";
        limits.output(header.size());workFile.write(header);
        hg_runtime::BufferedRows rows;
        rows.runAndFlush(workFile,[&]{
            for(std::size_t i=0;i<a.count;++i) {
                const auto& e=a.events[i];std::ostringstream line;
                line<<e.pc<<','<<e.first<<','<<e.last<<','<<e.entryOrder<<','<<e.exitOrder<<','<<e.lr<<','<<e.sp<<','<<e.cpsr;
                for(const auto v:e.args)line<<','<<v;
                for(const auto v:e.result)line<<','<<v;
                line<<','<<e.dispatch<<','<<e.stores<<'\n';
                const auto bytes=line.str();limits.output(bytes.size());rows.append(bytes);
            }
        });
        workFile.flush();workReported=true;
        std::cout<<"ASSET_TRACE_STATE schema=1 frame="<<frames<<" valid="<<a.ok
            <<" pending="<<a.active<<" events="<<a.count<<" error_pc="<<a.errorPC
            <<" error_frame="<<a.errorFrame<<std::endl;
        if(!a.ok)throw std::runtime_error("Invalid bounded asset observation");
    }
    void workTrace(bool enabled, HGTrace::WorkLayout layout=HGTrace::WorkLayout::R4) {
#ifndef HG_WORK_OBSERVER
        (void)enabled;(void)layout;
        throw std::runtime_error("Build the explicit HG_WORK_OBSERVER variant first");
#else
        if(enabled) {
            if(workStarted)throw std::runtime_error("Work trace can start only once per process");
            if(layout==HGTrace::WorkLayout::Assets) {
                // The external manifest authenticates the exact ROM and route.
                if(!hgScene || nds->ConsoleType!=0 || frames || stateLoaded)
                    throw std::runtime_error("Asset observer requires the admitted DS direct boot before frame 1");
                workFile=outputDir.create("asset-events.csv");
                HGTrace::Work.start(true,layout);workStarted=true;
                return;
            }
            const bool pilot=layout==HGTrace::WorkLayout::Pilot;
#ifndef HG_MODEL_BUDGET
            if(pilot)throw std::runtime_error("Build the explicit HG_MODEL_BUDGET variant first");
#endif
            if(pilot && (nds->ConsoleType!=0 || nds->ARM9ClockShift!=1))
                throw std::runtime_error("Model clock pilot requires DS/interpreter clock shift1");
            // Full ROM identity belongs to the external authenticated run manifest.
            // This extra live signature rejects a missing r4 helper, not every ROM.
            const auto word=[&](u32 a){return nds->MainRAM[a-0x02000000] |
                (u32(nds->MainRAM[a-0x02000000+1])<<8);};
            const bool native=layout==HGTrace::WorkLayout::NativeHeap || layout==HGTrace::WorkLayout::Graphics || pilot;
            const bool h4=layout==HGTrace::WorkLayout::H4 || (native && word(0x023DBD00)==0xB5F0);
            const bool party=layout==HGTrace::WorkLayout::Party;
            const bool scheduler=layout==HGTrace::WorkLayout::Scheduler;
            bool schedulerSignature=true;
            if(scheduler)for(std::size_t i=64;i<HGTrace::WorkSites.size();++i) {
                const auto& site=HGTrace::WorkSites[i];
                if(word(site.pc)!=site.instruction)schedulerSignature=false;
            }
            const bool admitted=hgScene && (scheduler?schedulerSignature:(party?
                (word(0x023DBE00)==0xB5B0 && word(0x023DBEB4)==0xB508 && word(0x023DBEBE)==0xB508):
                (word(0x023DBD00)==(h4?0xB5F0:0xB5FE) && word(h4?0x023DBD9C:0x023DBD98)==0xB508)));
            if(!admitted)throw std::runtime_error("Missing admitted work helper signature");
            if(pilot) {
                pilotOwners=configurePilotOwners();
                if(!HGTrace::Waits.start(pilotOwners,frames))throw std::runtime_error("Invalid pilot wait configuration");
                // Full image and caller-window authentication remains external.
                const HGTrace::PilotCopy::Config memory{{pilotDTCMBase,pilotDTCMEnd},{0,pilotITCMLimit},true};
                HGTrace::PilotOam::OwnerConfigs owners{};
                for(std::size_t i=0;i<owners.size();++i)owners[i]={pilotOwners[i].id,pilotOwners[i].low,pilotOwners[i].high};
                if(!HGTrace::Copies.start(memory,frames) || !HGTrace::Oam.start(owners,{pilotOamMain,pilotOamSub},frames) ||
                        !HGTrace::Polls.start(frames))throw std::runtime_error("Invalid pilot counter configuration");
            }
            workFile=outputDir.create("work-events.csv");
            if(pilot) {
                modelFile=outputDir.create("model-timing.csv");
                std::string header="frame,clock_shift,start_ts,end_ts,gx_ticks,dma_ticks,execute_residual_ticks,halt_skip_ticks,branches,carry_start,carry_end,valid";
                for(const auto* name:HGTrace::PilotFrameNames){header+=',';header+=name;}
                header+='\n';
                limits.output(header.size());modelFile.write(header);modelFile.flush();
                HGTrace::Timing.start(nds->ARM9Timestamp,nds->ARM9ClockShift,nds->ARM9.Cycles);
                modelStarted=true;
            }
            HGTrace::Work.start(true,layout);HGTrace::Work.frame=frames;workStarted=true;
        } else {
            if(!workStarted || workReported || (!HGTrace::Work.enabled && HGTrace::Work.ok))
                throw std::runtime_error("Work trace is not active");
            HGTrace::Work.stop();
            if(HGTrace::Work.assets){reportAssets();return;}
            if(modelStarted) {
                HGTrace::Timing.stop(nds->ARM9Timestamp,nds->ARM9ClockShift,nds->ARM9.Cycles);
                HGTrace::Waits.stop(frames);HGTrace::Copies.stop(frames);HGTrace::Oam.stop(frames);
                HGTrace::Polls.stop(frames);modelReported=true;
            }
            std::ostringstream text;
            text<<"event,site,first_frame,last_frame,mode,lr,sp,arg0,arg1,arg2,arg3,result,complete,inclusive_dispatch,exclusive_dispatch";
            if(HGTrace::Work.nativeHeap || HGTrace::Work.graphics || HGTrace::Work.party || HGTrace::Work.scheduler)text<<",entry_order,exit_order,parent,entry_cpsr,exit_cpsr";
            if(HGTrace::Work.graphics || HGTrace::Work.party || HGTrace::Work.scheduler)text<<",aux_r4,aux_r5,aux_r6,aux_r7";
            text<<'\n';
            for(std::size_t i=0;i<HGTrace::Work.count;++i) {
                const auto& e=HGTrace::Work.events[i];
                text<<i<<','<<HGTrace::WorkSites[e.site].pc<<','<<e.first_frame<<','<<e.last_frame<<','<<unsigned(e.mode)<<','<<e.lr<<','<<e.sp;
                for(const auto a:e.args)text<<','<<a;
                text<<','<<e.result<<','<<e.complete<<','<<e.inclusive<<','<<e.exclusive;
                if(HGTrace::Work.nativeHeap || HGTrace::Work.graphics || HGTrace::Work.party || HGTrace::Work.scheduler)text<<','<<e.entry_order<<','<<e.exit_order<<','<<e.parent<<','<<e.entry_cpsr<<','<<e.exit_cpsr;
                if(HGTrace::Work.graphics || HGTrace::Work.party || HGTrace::Work.scheduler)for(const auto a:e.aux)text<<','<<a;
                text<<'\n';
            }
            const auto bytes=text.str();limits.output(bytes.size());workReported=true;workFile.write(bytes);workFile.flush();
            if(modelStarted){pendingModel.flush(modelFile);modelFile.flush();}
            std::cout<<"WORK events="<<HGTrace::Work.count<<" depth="<<HGTrace::Work.depth<<" ok="<<HGTrace::Work.ok;
            for(std::size_t i=0;i<HGTrace::Work.ticks.size();++i)if(HGTrace::Work.ticks[i])std::cout<<" mode"<<i<<'='<<HGTrace::Work.ticks[i];
            std::cout<<std::endl;
            if(!HGTrace::Work.ok)throw std::runtime_error("Invalid work observation: layout or bounded counter/stack/buffer failure");
            if(modelStarted && !HGTrace::Timing.ok)throw std::runtime_error("Invalid ARM9 model clock partition");
            if(modelStarted && !HGTrace::Waits.snapshot().ok)throw std::runtime_error("Invalid pilot wait observation");
            if(modelStarted && (!HGTrace::Copies.snapshot().ok || !HGTrace::Oam.snapshot().ok || !HGTrace::Polls.snapshot().ok))
                throw std::runtime_error("Invalid bounded pilot counter");
        }
#endif
    }
    void finishWork() {
        try {
            HGTrace::Work.requireStopped();
            if(modelStarted) {
                HGTrace::Timing.requireStopped();
                const auto& w=HGTrace::Waits.snapshot();
                const auto& c=HGTrace::Copies.snapshot();
                if(!w.ok || !w.stopped)throw std::runtime_error("Unclosed or invalid pilot wait observation");
                if(!c.ok || !c.started || !c.stopped)throw std::runtime_error("Unclosed or invalid pilot copy census");
                HGTrace::Oam.requireStopped();HGTrace::Polls.requireStopped();
            }
        } catch(...) {
            if(workStarted && !workReported)workTrace(false);
            throw;
        }
    }
    void sampling(bool enabled,hg_runtime::SampleRect rect) {
        if(enabled) {
            if(!rect.width || !rect.height || rect.x>=256 || rect.y>=192 || rect.width>256-rect.x || rect.height>192-rect.y)
                throw std::runtime_error("Invalid framebuffer rectangle");
            if(!sampleFile) {
                samples=outputDir.create("frame-samples.csv");sampleFile=true;
                std::ostringstream header;header<<"frame,host_sample_ns,top_rgb_fnv64,bottom_rgb_fnv64,roi_rgb_fnv64,hits,on,busy,copies,bs,battle_rng_valid,battle_rng";
                for(int i=0;i<4;++i)for(const char* field:{"od","pic","rng","bs","valid","used","phase","left","wait","envelope","suspended","y","width","height","pose","shadow","crop"})header<<",s"<<i<<'_'<<field;
                header<<'\n';const auto text=header.str();limits.output(text.size());samples.write(text);samples.flush();
            }
            sampleRect=rect;
        }
        sampleEnabled=enabled;
    }
    void run(u32 count) {
        limits.frames(count);
        auto t=std::chrono::steady_clock::now();s16 audio[8192];
        const auto loop=[&]{for(u32 i=0;i<count;++i){if((i&1023)==0)limits.checkTime();if(!nds->IsRunning())throw std::runtime_error("Console stopped");for(auto& f:freezes)write(f.addr,f.value,f.width);HGTrace::Work.frame=frames+1;auto observed=hg_runtime::runObservedFrame<std::chrono::steady_clock>(*nds);++frames;row(observed.scanlines,observed.host_runframe_ns);modelRow();sampleFrame();while(nds->SPU.GetOutputSize()>0)nds->SPU.ReadOutput(audio,std::min(4096,nds->SPU.GetOutputSize()));}};
        const auto modelLoop=[&]{if(modelStarted && !modelReported)pendingModel.runAndFlush(modelFile,loop);else loop();};
        try {pendingCsv.runAndFlush(csv,[&]{if(sampleFile)pendingSamples.runAndFlush(samples,modelLoop);else modelLoop();});}
        catch(...) {
            if(modelStarted) {
                try {if(workStarted && !workReported)workTrace(false);}catch(...) {}
                try {status();}catch(...) {}
            }
            throw;
        }
        double seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-t).count();
        std::cout<<"RAN count="<<count<<" seconds="<<seconds<<" fps="<<(seconds?count/seconds:0)<<std::endl;status();
    }
    void capture(const std::string& name) {
        void* top=nullptr;void* bottom=nullptr;if(!nds->GPU.GetFramebuffers(&top,&bottom))throw std::runtime_error("No RAM framebuffer");
        std::vector<u8> image;std::string header="P6\n256 384\n255\n";image.insert(image.end(),header.begin(),header.end());
        for(void* screen:{top,bottom}){const u32* p=static_cast<const u32*>(screen);for(int i=0;i<256*192;++i){image.push_back(p[i]>>16);image.push_back(p[i]>>8);image.push_back(p[i]);}}
        writeFile(name,image.data(),image.size());
    }
    void save(const std::string& name) { Savestate s;if(!nds->DoSavestate(&s)||s.Error)throw std::runtime_error("Save state failed");writeFile(name,s.Buffer(),s.Length()); }
    void load(const std::string& name) { if(HGTrace::Work.assets)throw std::runtime_error("Cannot load state during an asset observation session");stateLoaded=true;fs::path p=name;if(p.is_relative())p=out/p;auto d=readFile(p,hg_runtime::RuntimeLimits::MaxSavestateBytes,"savestate");Savestate s(d.data(),d.size(),false);if(s.Error||!nds->DoSavestate(&s)||s.Error)throw std::runtime_error("Load state failed");nds->Start();std::cout<<"LOADED "<<p<<std::endl; }
    bool command(const std::string& line) {
        limits.command(line.size());limits.output(line.size()+32);std::ostringstream logged;logged<<frames<<' '<<line<<'\n';commands.write(logged.str());commands.flush();std::istringstream in(line);std::vector<std::string> t;std::string token;while(in>>std::quoted(token))t.push_back(token);
        if(t.empty()||t[0][0]=='#')return true;auto require=[&](size_t n){if(t.size()<n)throw std::runtime_error("Missing command arguments");};auto n=[&](size_t i){require(i+1);return number(t[i]);};
        const auto& c=t[0];
        if(c=="quit"||c=="exit")return false;
        else if(c=="status")status();
        else if(c=="tracepc"){require(2);if(t[1]=="reset"){for(auto& c:HGTrace::Counters)c={};HGTrace::MainLoopJumps=0;}else HGTrace::Enabled=(t[1]=="on");}
        else if(c=="run"){require(2);if(t.size()>2)nds->SetKeyMask(keyMask(t[2]));run(n(1));if(t.size()>2)nds->SetKeyMask(0xfff);}
        else if(c=="key"){require(2);nds->SetKeyMask(keyMask(t[1]));}
        else if(c=="tap"){require(2);nds->SetKeyMask(keyMask(t[1]));run(t.size()>2?n(2):2);nds->SetKeyMask(0xfff);run(t.size()>3?n(3):30);}
        else if(c=="touch"){require(3);nds->TouchScreen(n(1),n(2));if(t.size()>3){run(n(3));nds->ReleaseScreen();}}
        else if(c=="release")nds->ReleaseScreen();
        else if(c=="work"){require(2);if(t[1]=="on"){if(t.size()>3 || (t.size()==3 && t[2]!="h4" && t[2]!="heap" && t[2]!="graphics" && t[2]!="pilot" && t[2]!="assets" && t[2]!="party" && t[2]!="scheduler"))throw std::runtime_error("work on expects optional h4, heap, graphics, pilot, assets, party or scheduler layout");workTrace(true,t.size()==2?HGTrace::WorkLayout::R4:t[2]=="h4"?HGTrace::WorkLayout::H4:t[2]=="heap"?HGTrace::WorkLayout::NativeHeap:t[2]=="graphics"?HGTrace::WorkLayout::Graphics:t[2]=="pilot"?HGTrace::WorkLayout::Pilot:t[2]=="party"?HGTrace::WorkLayout::Party:t[2]=="scheduler"?HGTrace::WorkLayout::Scheduler:HGTrace::WorkLayout::Assets);}else if(t[1]=="off")workTrace(false);else throw std::runtime_error("work expects on or off");}
        else if(c=="sample"){require(2);if(t[1]=="off")sampling(false,sampleRect);else if(t[1]=="on"){require(6);sampling(true,{n(2),n(3),n(4),n(5)});}else throw std::runtime_error("sample expects on or off");}
        else if(c=="capture"){require(2);capture(t[1]);}
        else if(c=="save"){require(2);save(t[1]);}
        else if(c=="load"){require(2);load(t[1]);}
        else if(c=="dump"){require(2);writeFile(t[1],nds->MainRAM,0x400000);}
        else if(c=="sram"){require(2);writeFile(t[1],nds->GetNDSSave(),nds->GetNDSSaveLength());}
        else if(c=="read"){require(2);u32 start=n(1);u32 width=t.size()>2?n(2):4;u32 count=t.size()>3?n(3):1;limits.reads(start,width,count);for(u32 i=0;i<count;++i){u32 addr=start+i*width;std::cout<<"READ 0x"<<std::hex<<addr<<" 0x"<<read(addr,width)<<std::dec<<std::endl;}}
        else if(c=="write"){require(3);write(n(1),n(2),t.size()>3?n(3):4);}
        else if(c=="freeze"){require(3);limits.freeze();freezes.push_back({n(1),n(2),int(t.size()>3?n(3):4)});}
        else if(c=="unfreeze")freezes.clear();
        else if(c=="watch"){require(3);limits.watch();watches.push_back({t[1],n(2),int(t.size()>3?n(3):4)});csvHeader=false;}
        else if(c=="clearwatches"){watches.clear();csvHeader=false;}
        else if(c=="cheat"){require(2);fs::path p=t[1];if(p.is_relative())p=out/p;auto data=readFile(p,hg_runtime::RuntimeLimits::MaxCheatBytes,"cheat file");std::string text(reinterpret_cast<const char*>(data.data()),data.size());std::istringstream f(text);ARCode code{};code.Name=p.filename().string();code.Enabled=true;std::string l;while(boundedLine(f,l,hg_runtime::RuntimeLimits::MaxCommandBytes)){auto comment=l.find('#');if(comment!=std::string::npos)l.resize(comment);std::istringstream words(l);std::string w;while(words>>w){if(code.Code.size()>=hg_runtime::RuntimeLimits::MaxCheatWords)throw std::runtime_error("Cheat exceeds 8192 words");code.Code.push_back(std::stoul(w,nullptr,16));}}if(code.Code.size()%2)throw std::runtime_error("Cheat words must be paired");limits.cheat(data.size(),code.Code.size());nds->AREngine.Cheats.push_back(std::move(code));}
        else if(c=="clearcheats")nds->AREngine.Cheats.clear();
        else if(c=="help")std::cout<<"run FRAMES [KEYS] | tap KEYS [HOLD=2] [WAIT=30] | key KEYS | touch X Y [FRAMES] | release | work on [h4|heap|graphics|pilot|assets|party|scheduler] / work off | sample on X Y W H | sample off | capture FILE.ppm | save FILE.state | load FILE | dump FILE.bin | sram FILE.sav | read ADDRESS [WIDTH=4] [COUNT=1] | write ADDRESS VALUE [WIDTH=4] | freeze ADDRESS VALUE [WIDTH=4] | unfreeze | watch LABEL ADDRESS [WIDTH=4] | clearwatches | cheat FILE | clearcheats | status | quit\n";
        else throw std::runtime_error("Unknown command: "+c);
        return true;
    }
};
int main(int argc,char** argv) {
    try {
        fs::path rom,out,script,sram,load;u32 frames=0;bool interactive=false;
        hg_runtime::RtcConfig rtc;bool rtcSet=false;
        for(int i=1;i<argc;++i){std::string a=argv[i];auto arg=[&](){if(++i>=argc)throw std::runtime_error("Missing value for "+a);return std::string(argv[i]);};if(a=="--rom")rom=arg();else if(a=="--out")out=arg();else if(a=="--script")script=arg();else if(a=="--sram")sram=arg();else if(a=="--load")load=arg();else if(a=="--frames")frames=number(arg());else if(a=="--interactive")interactive=true;else if(a=="--trace-pc")HGTrace::Enabled=true;else if(a=="--rtc"){if(rtcSet)throw std::runtime_error("Duplicate --rtc");rtc=hg_runtime::RtcConfig::parse(arg());rtcSet=true;}else throw std::runtime_error("Unknown option "+a);}
        if(rom.empty()||out.empty())throw std::runtime_error("Usage: hg_runtime --rom ROM --out DIR [--frames N] [--script FILE] [--interactive] [--sram FILE] [--load FILE] [--rtc YYYY-MM-DDTHH:MM:SS]");
        std::vector<u8> scriptData;if(!script.empty())scriptData=readFile(script,hg_runtime::RuntimeLimits::MaxScriptBytes,"script");
        Harness h(rom,out,sram,rtc);if(!load.empty())h.load(load.string());if(frames)h.run(frames);
        if(!script.empty()){std::string text(reinterpret_cast<const char*>(scriptData.data()),scriptData.size());std::istringstream f(text);std::string l;while(boundedLine(f,l,hg_runtime::RuntimeLimits::MaxCommandBytes))if(!h.command(l))break;}
        h.capture("latest.ppm");h.status();
        if(interactive){std::string line;std::cout<<"READY"<<std::endl;while(boundedLine(std::cin,line,hg_runtime::RuntimeLimits::MaxCommandBytes)){try{if(!h.command(line))break;}catch(const std::exception& e){std::cout<<"ERROR "<<e.what()<<std::endl;}std::cout<<"READY"<<std::endl;}}
        h.finishWork();h.csv.flush();return 0;
    }catch(const std::exception& e){std::cerr<<"ERROR "<<e.what()<<std::endl;return 1;}
}
