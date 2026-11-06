#include "runtime_limits.h"
#include "secure_output.h"
#include "csv_output.h"

#include <cassert>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <functional>
#include <stdexcept>
#include <sys/stat.h>

static void rejects(const std::function<void()>& action) {
    try { action(); } catch (const std::runtime_error&) { return; }
    assert(false && "expected runtime limit rejection");
}

int main(int argc, char** argv) {
    using hg_runtime::RuntimeLimits;
    RuntimeLimits normal;
    normal.command(128);
    normal.frames(9478);
    normal.reads(0x02000000, 4, 16);
    normal.watch();
    normal.freeze();
    normal.cheat(64, 4);
    normal.output(1u << 20);
    assert(RuntimeLimits::fileSize(1024, RuntimeLimits::MaxRomBytes, "ROM") == 1024);
    assert(hg_runtime::safeCsvField("watch") == "watch");
    assert(hg_runtime::safeCsvField("a,b") == "\"a,b\"");
    assert(hg_runtime::safeCsvField("=1+1") == "'=1+1");
    assert(hg_runtime::safeCsvField("x\r\ny") == "x\\x0d\\x0ay");

    rejects([] { RuntimeLimits x; x.command(RuntimeLimits::MaxCommandBytes + 1); });
    rejects([] { RuntimeLimits x; x.reads(0, 4, RuntimeLimits::MaxReadPerCommand + 1); });
    rejects([] { RuntimeLimits x; x.reads(0xfffffffcu, 4, 2); });
    rejects([] { RuntimeLimits x; x.frames(RuntimeLimits::MaxFrames); x.frames(1); });
    rejects([] { RuntimeLimits x; x.output(RuntimeLimits::MaxOutputBytes); x.output(1); });
    rejects([] { RuntimeLimits::fileSize(RuntimeLimits::MaxRomBytes + 1,
                                         RuntimeLimits::MaxRomBytes, "ROM"); });
    rejects([] {
        RuntimeLimits x(std::chrono::steady_clock::now() - RuntimeLimits::MaxElapsed
                        - std::chrono::seconds(1));
        x.checkTime();
    });

    assert(argc == 2);
    namespace fs = std::filesystem;
    fs::path top = argv[1];
    fs::path root = top / "runtime-output";
    hg_runtime::SecureOutputDir outputs(root);
    outputs.writeFile("normal.bin", "safe", 4);
    struct stat info {};
    assert(::lstat((root / "normal.bin").c_str(), &info) == 0);
    assert(S_ISREG(info.st_mode) && (info.st_mode & 0777) == 0600 && info.st_nlink == 1);

    fs::path victim = top / "victim";
    { std::ofstream file(victim); file << "preserve"; }
    fs::create_symlink(victim, root / "live");
    fs::create_symlink(top / "absent", root / "dangling");
    fs::create_hard_link(victim, root / "hard");
    rejects([&] { outputs.writeFile("live", "bad", 3); });
    rejects([&] { outputs.writeFile("dangling", "bad", 3); });
    rejects([&] { outputs.writeFile("hard", "bad", 3); });
    std::ifstream victimInput(victim);
    std::string victimText; victimInput >> victimText;
    assert(victimText == "preserve" && !fs::exists(top / "absent"));
    fs::path nulEscape(std::string("..\0ignored", 10));
    nulEscape /= "escaped.bin";
    rejects([&] { outputs.writeFile(nulEscape, "escape", 6); });
    assert(!fs::exists(top / "escaped.bin"));

    fs::path moved = top / "held-output";
    fs::path outside = top / "outside";
    fs::create_directory(outside); ::chmod(outside.c_str(), 0700);
    fs::rename(root, moved);
    fs::create_directory_symlink(outside, root);
    outputs.writeFile("held.bin", "held", 4);
    assert(fs::exists(moved / "held.bin") && !fs::exists(outside / "held.bin"));
    rejects([&] { hg_runtime::SecureOutputDir redirected(root); });

    fs::path relaxed = top / "relaxed";
    fs::create_directory(relaxed); ::chmod(relaxed.c_str(), 0755);
    rejects([&] { hg_runtime::SecureOutputDir refused(relaxed); });
}
