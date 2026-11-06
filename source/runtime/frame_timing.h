#pragma once

#include <chrono>
#include <cstdint>

namespace hg_runtime {

struct ObservedFrame {
    std::uint32_t scanlines;
    std::uint64_t host_runframe_ns;
};

template <typename Clock, typename Console>
ObservedFrame runObservedFrame(Console& console) {
    const auto before = Clock::now();
    const auto scanlines = console.RunFrame();
    const auto after = Clock::now();
    const auto elapsed = std::chrono::duration_cast<std::chrono::nanoseconds>(
        after - before).count();
    return {static_cast<std::uint32_t>(scanlines),
            static_cast<std::uint64_t>(elapsed)};
}

}  // namespace hg_runtime
