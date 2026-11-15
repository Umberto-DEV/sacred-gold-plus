#pragma once

#include <array>
#include <chrono>
#include <cstdint>
#include <optional>
#include <stdexcept>
#include <type_traits>

namespace hg_runtime {

struct SampleRect { std::uint32_t x,y,width,height; };
struct FrameHashes {
    std::uint64_t top,bottom,roi;
    bool operator==(const FrameHashes& b) const {
        return top==b.top && bottom==b.bottom && roi==b.roi;
    }
};
inline std::uint64_t hashRgbRect(const std::uint32_t* pixels,SampleRect r) {
    std::uint64_t hash=14695981039346656037ull;
    for (std::uint32_t y=r.y;y<r.y+r.height;++y)
        for (std::uint32_t x=r.x;x<r.x+r.width;++x) {
            const auto p=pixels[y*256+x];
            for (int shift:{16,8,0}) { hash^=(p>>shift)&255;hash*=1099511628211ull; }
        }
    return hash;
}
inline FrameHashes hashFramebuffer(const std::uint32_t* top,
                                    const std::uint32_t* bottom,SampleRect r) {
    if (!top || !bottom || !r.width || !r.height || r.x>=256 || r.y>=192
            || r.width>256-r.x || r.height>192-r.y)
        throw std::invalid_argument("Invalid framebuffer rectangle");
    return {hashRgbRect(top,{0,0,256,192}),hashRgbRect(bottom,{0,0,256,192}),hashRgbRect(top,r)};
}
inline bool mainRamRange(std::uint32_t address,std::uint32_t bytes) {
    return address>=0x02000000 && address<0x02400000 && bytes<=0x02400000-address;
}
struct AnimSlotSample {
    std::uint32_t od=0,pic=0,rng=0,bs=0;
    std::uint8_t phase=0,left=0,wait=0,envelope=0,suspended=0,used=0,pose=0,active=0;
    std::int16_t y=0,shadow=0;
    std::uint16_t width=0,height=0,crop=0;
    bool valid=false;
};
struct AnimSample {
    std::uint32_t hits=0,on=0,busy=0,copies=0,bs=0,battle_rng=0;
    bool battle_rng_valid=false;
    std::array<AnimSlotSample,4> slots;
};
template <typename ReadByte> AnimSample observeAnim2(ReadByte read) {
    const auto u16=[&](std::uint32_t a){return std::uint16_t(read(a)|(std::uint32_t(read(a+1))<<8));};
    const auto u32=[&](std::uint32_t a){return std::uint32_t(u16(a))|(std::uint32_t(u16(a+2))<<16);};
    constexpr std::uint32_t state=0x023DBBA0;
    AnimSample out;out.hits=u32(state+4);out.on=u32(state+8);out.busy=u32(state+12);
    out.copies=u32(state+0x20);out.bs=u32(state+0x28);
    for (std::size_t i=0;i<out.slots.size();++i) {
        const auto a=0x023DBBE0+std::uint32_t(i)*32;auto& s=out.slots[i];
        s.od=u32(a);s.pic=u32(a+4);s.rng=u32(a+8);s.bs=u32(a+0x18);
        s.left=read(a+0x10);s.wait=read(a+0x11);s.used=read(a+0x13);
        s.suspended=read(a+0x15);s.phase=read(a+0x16);s.envelope=read(a+0x17);
        if (!s.used || !mainRamRange(s.od,0x1B0) || !mainRamRange(s.pic,0xAC))continue;
        s.active=read(s.pic)&1;if(!s.active)continue;
        s.valid=true;s.y=std::int16_t(u16(s.pic+0x2E));s.width=u16(s.pic+0x34);
        s.height=u16(s.pic+0x36);s.pose=read(s.pic+0x5B);
        s.shadow=std::int16_t(u16(s.pic+0x76));s.crop=u16(s.pic+0x54);
        if (s.bs==out.bs && mainRamRange(out.bs,0x2450))out.battle_rng_valid=true;
    }
    // Current EN/IT ov012 Random at0223BD98 uses offset2448 and literals
    // 41C64E6D/6073. This is read-only state, never a call to the guest RNG.
    if(out.battle_rng_valid)out.battle_rng=u32(out.bs+0x2448);
    return out;
}
template<typename T> struct TimedSample { T value;std::uint64_t host_ns; };
template<typename Clock,typename Sample>
auto runOptionalSample(bool enabled,Sample sample)
        -> std::optional<TimedSample<std::invoke_result_t<Sample>>> {
    if(!enabled)return std::nullopt;
    const auto before=Clock::now();auto value=sample();const auto after=Clock::now();
    return TimedSample<std::invoke_result_t<Sample>>{value,std::uint64_t(
        std::chrono::duration_cast<std::chrono::nanoseconds>(after-before).count())};
}

} // namespace hg_runtime
