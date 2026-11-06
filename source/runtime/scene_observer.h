#pragma once

#include <cstdint>

namespace hg_runtime {

struct HgScene {
    std::uint32_t map;
    std::int32_t x;
    std::int32_t z;
    std::uint32_t active_objects;
};

template <typename Read32>
HgScene observeHgScene(Read32 read32) {
    constexpr std::uint32_t localField = 0x0227D4A0;
    constexpr std::uint32_t manager = 0x022A1E90;
    constexpr std::uint32_t mainRamStart = 0x02000000;
    constexpr std::uint32_t mainRamEnd = 0x02400000;
    constexpr std::uint32_t objectSize = 0x12C;
    constexpr std::uint32_t objectCapacity = 64;

    HgScene scene {
        read32(localField),
        static_cast<std::int32_t>(read32(localField + 8)),
        static_cast<std::int32_t>(read32(localField + 12)),
        0,
    };
    const auto count = read32(manager + 4);
    const auto pool = read32(manager + 0x124);
    if (count != objectCapacity || pool < mainRamStart ||
        pool > mainRamEnd - objectCapacity * objectSize) {
        return scene;
    }
    for (std::uint32_t slot = 0; slot < count; ++slot) {
        if (read32(pool + slot * objectSize) & 1) ++scene.active_objects;
    }
    return scene;
}

}  // namespace hg_runtime
