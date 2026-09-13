#include "profile_trace.h"
#include <cassert>

int main() {
    using namespace melonDS::HGProfile;
    Step(0x02088B40,0x02010001,0x1000,10,512);
    assert(!Active && Groups.empty());
    Enabled=true;
    Step(0x02088B40,0x02010001,0x1000,100,512);
    Step(0x0201AA8C,0,0xF00,110,0);
    Step(0x0206E640,0,0xF00,120,0);
    // Same PC with a different stack is a nested call, not our return.
    Step(0x02010000,0,0xF00,130,0);
    assert(Active && Groups.empty());
    Step(0x0201AB0C,0,0xF00,140,0);
    Step(0x02010000,0,0x1000,150,0);
    const auto& g=Groups.at(512);
    assert(!Active && g.calls==1 && g.cycles==50 && g.total.instructions==5);
    assert(g.total.allocations==1 && g.total.frees==1 && g.total.box_reads==1);
    assert(g.min_cycles==50 && g.max_cycles==50);
    Reset();
    assert(!Active && Groups.empty() && Incomplete==0);
}
