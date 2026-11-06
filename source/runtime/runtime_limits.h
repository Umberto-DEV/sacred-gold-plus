#pragma once

#include <chrono>
#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <string>

namespace hg_runtime {

class RuntimeLimits {
public:
    static constexpr std::uint64_t MaxScriptBytes = 1u << 20;
    static constexpr std::uint64_t MaxRomBytes = 512u << 20;
    static constexpr std::uint64_t MaxSramBytes = 64u << 20;
    static constexpr std::uint64_t MaxSavestateBytes = 32u << 20;
    static constexpr std::uint64_t MaxCommandBytes = 4096;
    static constexpr std::uint64_t MaxCommands = 10000;
    static constexpr std::uint64_t MaxFrames = 1000000;
    static constexpr std::uint64_t MaxReadPerCommand = 4096;
    static constexpr std::uint64_t MaxReads = 65536;
    static constexpr std::uint64_t MaxWatches = 256;
    static constexpr std::uint64_t MaxFreezes = 256;
    static constexpr std::uint64_t MaxCheats = 256;
    static constexpr std::uint64_t MaxCheatBytes = 256u << 10;
    static constexpr std::uint64_t MaxCheatWords = 8192;
    static constexpr std::uint64_t MaxOutputBytes = 256u << 20;
    static constexpr auto MaxElapsed = std::chrono::minutes(30);

    explicit RuntimeLimits(
        std::chrono::steady_clock::time_point start = std::chrono::steady_clock::now())
        : start_(start) {}

    static std::size_t fileSize(std::uint64_t bytes, std::uint64_t limit,
                                const char* label) {
        if (bytes > limit)
            throw std::runtime_error(std::string(label) + " exceeds size limit");
        if (bytes > std::uint64_t(SIZE_MAX))
            throw std::runtime_error(std::string(label) + " does not fit host size_t");
        return static_cast<std::size_t>(bytes);
    }

    void checkTime() const {
        if (std::chrono::steady_clock::now() - start_ > MaxElapsed)
            throw std::runtime_error("Runtime session exceeded 30 minutes");
    }

    void command(std::size_t bytes) {
        checkTime();
        if (bytes > MaxCommandBytes)
            throw std::runtime_error("Command exceeds 4096 bytes");
        add(commands_, 1, MaxCommands, "Runtime session command budget exceeded");
    }

    void frames(std::uint64_t count) {
        checkTime();
        if (count > MaxFrames)
            throw std::runtime_error("Frame request exceeds session budget");
        add(frames_, count, MaxFrames, "Runtime session frame budget exceeded");
    }

    void reads(std::uint32_t start, std::uint32_t width, std::uint64_t count) {
        checkTime();
        if (width != 1 && width != 2 && width != 4)
            throw std::runtime_error("Width must be 1, 2 or 4");
        if (count > MaxReadPerCommand)
            throw std::runtime_error("Read request exceeds 4096 values");
        if (count) {
            const std::uint64_t last = std::uint64_t(start) + (count - 1) * width;
            if (last > 0xffffffffu || last + width > 0x100000000ull)
                throw std::runtime_error("Read address range wraps 32 bits");
        }
        add(reads_, count, MaxReads, "Runtime session read budget exceeded");
    }

    void watch() { add(watches_, 1, MaxWatches, "Too many watches"); }
    void freeze() { add(freezes_, 1, MaxFreezes, "Too many freezes"); }
    void cheat(std::uint64_t fileBytes, std::uint64_t words) {
        if (fileBytes > MaxCheatBytes) throw std::runtime_error("Cheat file exceeds 256 KiB");
        if (words > MaxCheatWords) throw std::runtime_error("Cheat exceeds 8192 words");
        add(cheats_, 1, MaxCheats, "Too many cheats");
    }

    void output(std::uint64_t bytes) {
        add(outputBytes_, bytes, MaxOutputBytes, "Runtime session output budget exceeded");
    }

private:
    static void add(std::uint64_t& value, std::uint64_t amount,
                    std::uint64_t limit, const char* message) {
        if (amount > limit - value) throw std::runtime_error(message);
        value += amount;
    }

    std::chrono::steady_clock::time_point start_;
    std::uint64_t commands_ = 0;
    std::uint64_t frames_ = 0;
    std::uint64_t reads_ = 0;
    std::uint64_t watches_ = 0;
    std::uint64_t freezes_ = 0;
    std::uint64_t cheats_ = 0;
    std::uint64_t outputBytes_ = 0;
};

} // namespace hg_runtime
