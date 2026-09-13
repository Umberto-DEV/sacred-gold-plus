// Optional observation-only instruction counters for the offline HG audit.
#pragma once
#include <cstdint>
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
