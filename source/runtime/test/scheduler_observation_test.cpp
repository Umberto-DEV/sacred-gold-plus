// Owned synthetic instruction observations only; no ROM, CPU or clock execution.
#include "hg_trace.h"
#include <cassert>
#include <iostream>
#include <limits>
#include <array>
using namespace melonDS::HGTrace;
using R=std::array<std::uint32_t,16>;
constexpr std::uint32_t T=0x3f, SP=0x023f0000;
R regs(){R r{};r[13]=SP;r[14]=0x02000def;return r;}
template<class W>void enter(W& w,R& r,std::uint32_t pc){w.step(pc,WorkSites[workSiteIndex(pc)].instruction,r.data(),T);}
int main(){
 unsigned cases=0;
 {WorkObserver<32,8>w;auto r=regs();auto before=r;w.step(0x0201f880,0,nullptr,T);assert(w.ok&&!w.count&&r==before);++cases;}
 {WorkObserver<32,8>w;auto r=regs();w.start(true,WorkLayout::Scheduler);assert(w.scheduler);
  // Old Party site is not selected by the new profile.
  w.step(0x02073314,0,nullptr,T);assert(w.ok&&w.count==0);
  r[0]=0x023bc814;enter(w,r,0x0201f880);assert(w.depth==1);
  r[13]=SP-16;r[0]=0x023d0000;r[1]=0x022cc648;r[2]=0x023dbc9b;r[5]=0x023bc814;r[14]=0x0201f899;
  enter(w,r,0x0201f8aa);assert(w.depth==2);
  r[14]=0x0201f8ad;enter(w,r,0x023dbc9a);assert(w.depth==3);
  r[13]=SP-24;r[14]=0x023dbccd;enter(w,r,0x023db72c);assert(w.depth==4);
  w.step(0x023dbccc,0,r.data(),T);assert(w.depth==3);
  r[13]=SP-16;w.step(0x0201f8ac,0,r.data(),T);assert(w.depth==1);
  assert(w.events[1].complete&&w.events[2].complete&&w.events[1].exit_order>w.events[2].exit_order);
  assert(w.events[1].aux[1]==0x023bc814&&w.events[1].args[2]==0x023dbc9b);
  r[13]=SP;w.step(0x02000dee,0,r.data(),T);assert(!w.depth);w.stop();w.requireStopped();++cases;
 }
 {WorkObserver<32,8>w;auto r=regs();w.start(true,WorkLayout::Scheduler);r[0]=0x023d0000;r[2]=0x023dbc9b;
  enter(w,r,0x0201f8aa); // pre-BLX LR is intentionally not the callback return
  w.step(r[14]&~1u,0,r.data(),T);assert(w.depth==1);
  w.step(0x0201f8ac,0,r.data(),T);assert(!w.depth);w.stop();assert(w.ok);++cases;
 }
 {WorkObserver<32,8>w;auto r=regs();w.start(true,WorkLayout::Scheduler);enter(w,r,0x0201f880);
  r[13]-=4;w.step(0x02000dee,0,r.data(),T);assert(w.depth==1);r[13]+=4;
  w.step(0x02000dee,0,r.data(),31);assert(w.depth==1); // wrong ISA
  w.step(0x02000dee,0,r.data(),0x32);assert(w.depth==1); // wrong mode
  w.stop();assert(!w.ok);++cases;
 }
 for(const auto pc:{0x02000dd4u,0x02000e84u,0x0201f880u,0x0201f886u,0x0201f89eu,0x0201f8aau,0x023dbc9au,0x023dbca0u,0x023dbca8u,0x023db72cu}){
  WorkObserver<4,4>w;auto r=regs();auto saved=r;w.start(true,WorkLayout::Scheduler);enter(w,r,pc);assert(w.ok&&w.count==1&&r==saved);++cases;
  WorkObserver<4,4>bad;bad.start(true,WorkLayout::Scheduler);bad.step(pc,0,r.data(),T);assert(!bad.ok);++cases;
  WorkObserver<4,4>isa;isa.start(true,WorkLayout::Scheduler);isa.step(pc,WorkSites[workSiteIndex(pc)].instruction,r.data(),31);assert(!isa.ok);++cases;
 }
 {WorkObserver<1,2>w;auto r=regs();w.start(true,WorkLayout::Scheduler);enter(w,r,0x02000dd4);enter(w,r,0x02000dd4);assert(!w.ok&&w.count==1);++cases;}
 {WorkObserver<4,1>w;auto r=regs();w.start(true,WorkLayout::Scheduler);enter(w,r,0x0201f880);r[13]-=16;enter(w,r,0x0201f8aa);assert(!w.ok&&w.depth==1);++cases;}
 {WorkObserver<4,2>w;auto r=regs();w.start(true,WorkLayout::Scheduler);w.order=std::numeric_limits<std::uint64_t>::max();enter(w,r,0x02000dd4);assert(!w.ok&&!w.count);++cases;}
 {WorkObserver<4,2>w;auto r=regs();w.start(true,WorkLayout::Scheduler);w.ticks[31]=std::numeric_limits<std::uint64_t>::max();enter(w,r,0x02000dd4);assert(!w.ok&&!w.count);++cases;}
 // Return-order overflow must fail rather than manufacture a complete span.
 {WorkObserver<4,2>w;auto r=regs();w.start(true,WorkLayout::Scheduler);enter(w,r,0x0201f880);w.order=std::numeric_limits<std::uint64_t>::max();w.step(0x02000dee,0,r.data(),T);assert(!w.ok&&!w.events[0].complete);++cases;}
 std::cout<<"scheduler own tests PASS cases="<<cases<<"\n";
}
