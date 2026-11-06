#include "buffered_rows.h"
#include "frame_timing.h"
#include "scene_observer.h"

#include <cassert>
#include <chrono>
#include <cstdint>
#include <map>
#include <stdexcept>

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
