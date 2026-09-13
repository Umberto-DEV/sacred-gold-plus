// Isolated execution of actual ROM instructions in melonDS ARM interpreter.
// GPL-3.0-or-later (links melonDS). This is not a complete DMA/SPI simulation.
#include "NDS.h"
#include "Args.h"
#include "ARMInterpreter.h"
#include <fstream>
#include <vector>
#include <cstdio>
#include <cstring>
#include <memory>

int main(int argc, char** argv) {
    if (argc != 2) { std::fprintf(stderr, "usage: wait_loop_test ROM_OR_DECOMPRESSED_ARM9\n"); return 2; }
    std::ifstream f(argv[1], std::ios::binary | std::ios::ate);
    if (!f) return 2;
    auto size = f.tellg();
    if (size < 0 || size > 512LL * 1024 * 1024) return 2;
    std::vector<unsigned char> bytes(static_cast<size_t>(size));
    f.seekg(0); f.read(reinterpret_cast<char*>(bytes.data()), bytes.size());
    if (!f || bytes.size() < 0xde174) return 2;
    unsigned offset = 0;
    if (bytes.size() > 0x200000) {
        std::memcpy(&offset, bytes.data() + 0x20, 4);
        unsigned length; std::memcpy(&length, bytes.data() + 0x2c, 4);
        if (length != 1122040) { std::fprintf(stderr,"Use decompressed ARM9 for compressed ROMs\n");return 2; }
    }
    if (static_cast<size_t>(offset) > bytes.size() - 0xde174) {
        std::fprintf(stderr, "ARM9 instruction offsets exceed input length\n"); return 2;
    }
    melonDS::NDSArgs args; args.JIT = std::nullopt;
    auto nds = std::make_unique<melonDS::NDS>(std::move(args)); nds->Reset();
    auto& cpu = nds->ARM9;
    int failures = 0;
    std::puts("[");
    int test = 0;
    for (unsigned site : {0x020D3FA8u, 0x020DE16Cu}) {
        unsigned instruction; std::memcpy(&instruction, bytes.data() + offset + site - 0x02000000, 4);
        for (bool busy : {false, true}) {
            cpu.CPSR = 0x13;
            cpu.SetNZ(false, !busy); // Flag resulting from original preceding TST of BUSY.
            cpu.R[0] = busy ? (site == 0x020D3FA8 ? 0x80000000 : 0x80) : 0;
            cpu.R[1] = 0x12345678;
            cpu.R[10] = 0xCAFEBABE;
            cpu.R[15] = site + 8; // ARM pipeline-visible PC at this instruction.
            cpu.CurInstr = instruction;
            if (cpu.CheckCondition(instruction >> 28)) {
                unsigned index = ((instruction >> 4) & 15) | ((instruction >> 16) & 0xff0);
                melonDS::ARMInterpreter::ARMInstrTable[index](&cpu);
            }
            unsigned next = cpu.R[15] == site + 8 ? site + 4 : cpu.R[15] - 4;
            unsigned expected = busy ? site - 8 : site + 4;
            bool ok = next == expected && cpu.R[10] == 0xCAFEBABE;
            failures += !ok;
            std::printf("%s {\"site\":\"%08X\",\"instruction\":\"%08X\",\"busy\":%s,\"next_pc\":\"%08X\",\"expected_pc\":\"%08X\",\"r10\":\"%08X\",\"expected_r10\":\"CAFEBABE\",\"status\":\"%s\"}",
                test++ ? ",\n" : "", site, instruction, busy ? "true" : "false", next, expected, cpu.R[10], ok ? "PASS" : "FAIL");
        }
    }
    std::puts("\n]");
    return failures ? 1 : 0;
}
