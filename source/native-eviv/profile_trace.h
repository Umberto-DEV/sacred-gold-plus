// GPL-3.0-or-later. Host-side observation for a separate interpreter build.
// Never linked into the ROM or the production emulator contribution.
#pragma once
#include <cstdint>
#include <limits>
#include <map>
#include <sstream>
#include <string>

namespace melonDS::HGProfile {
using u32 = std::uint32_t;
using u64 = std::uint64_t;
struct Sample { u64 instructions=0, allocations=0, frees=0, box_reads=0; };
struct Group {
    u64 calls=0, cycles=0, min_cycles=std::numeric_limits<u64>::max(), max_cycles=0;
    Sample total{};
};
inline bool Enabled=false, Active=false;
inline u32 ReturnAddress=0, Stack=0, Keys=0;
inline u64 Started=0, Incomplete=0;
inline Sample Current{};
inline std::map<u32,Group> Groups;

inline void Reset() { Active=false; Incomplete=0; Current={}; Groups.clear(); }
inline void Step(u32 pc,u32 lr,u32 sp,u64 clock,u32 keys) {
    if(!Enabled) return;
    if(Active && pc==ReturnAddress && sp==Stack) {
        auto& g=Groups[Keys]; const u64 elapsed=clock-Started;
        ++g.calls;g.cycles+=elapsed;
        if(elapsed<g.min_cycles)g.min_cycles=elapsed;
        if(elapsed>g.max_cycles)g.max_cycles=elapsed;
        g.total.instructions+=Current.instructions;
        g.total.allocations+=Current.allocations;
        g.total.frees+=Current.frees;g.total.box_reads+=Current.box_reads;
        Active=false;
    }
    if(pc==0x02088B40) {
        if(Active) ++Incomplete;
        Active=true;Started=clock;ReturnAddress=lr&~1u;Stack=sp;Keys=keys;Current={};
    }
    if(!Active) return;
    ++Current.instructions;
    if(pc==0x0201AA8C || pc==0x0201AACC)++Current.allocations;
    if(pc==0x0201AB0C || pc==0x0201AB80)++Current.frees;
    if(pc==0x0206E640)++Current.box_reads;
}
inline std::string Json() {
    std::ostringstream o;
    o<<"{\"kind\":\"ARM9-summary-input-inclusive-cycles\",\"active\":"<<(Active?"true":"false")
     <<",\"incomplete\":"<<Incomplete<<",\"groups\":[";
    bool first=true;
    for(const auto& [keys,g]:Groups) {
        if(!first)o<<',';first=false;
        o<<"{\"new_keys\":"<<keys<<",\"calls\":"<<g.calls<<",\"cycles\":"<<g.cycles
         <<",\"min_cycles\":"<<g.min_cycles<<",\"max_cycles\":"<<g.max_cycles
         <<",\"instructions\":"<<g.total.instructions<<",\"allocations\":"<<g.total.allocations
         <<",\"frees\":"<<g.total.frees<<",\"box_reads\":"<<g.total.box_reads<<'}';
    }
    o<<"]}\n";return o.str();
}
}
