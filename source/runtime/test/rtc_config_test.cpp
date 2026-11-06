// ROM-free tests of the actual C++17 clock parser and default configuration.
#include "../rtc_config.h"
#include <array>
#include <iostream>
#include <stdexcept>
#include <string>

using hg_runtime::RtcConfig;
static int checks = 0;
static void check(bool condition, const std::string& label) {
    ++checks;
    if (!condition) throw std::runtime_error(label);
}
static void fields(const RtcConfig& value, std::array<int, 6> expected) {
    check(std::array<int, 6>{value.year, value.month, value.day, value.hour,
                            value.minute, value.second} == expected,
          "wrong six RTC fields");
}
static void rejects(const std::string& text) {
    try { (void)RtcConfig::parse(text); }
    catch (const std::invalid_argument&) { ++checks; return; }
    throw std::runtime_error("accepted invalid RTC: " + text);
}
int main() {
    try {
        // Catches accidental default changes and dropped/reordered fields.
        fields(RtcConfig{}, {2026, 9, 5, 12, 0, 0});
        check(RtcConfig{}.session_text() == "2026-09-05 12:00:00", "default metadata");
        fields(RtcConfig::parse("2026-09-05T12:00:00"), {2026, 9, 5, 12, 0, 0});
        fields(RtcConfig::parse("2000-02-29T00:00:00"), {2000, 2, 29, 0, 0, 0});
        fields(RtcConfig::parse("2099-12-31T23:59:59"), {2099, 12, 31, 23, 59, 59});
        fields(RtcConfig::parse("2024-06-17T03:04:05"), {2024, 6, 17, 3, 4, 5});
        check(RtcConfig::parse("2024-06-17T03:04:05").session_text() ==
              "2024-06-17 03:04:05", "selected metadata and zero padding");
        // Literal calendar boundaries, independent of production month logic.
        for (const char* date : {"2025-01-31", "2025-02-28", "2025-03-31",
             "2025-04-30", "2025-05-31", "2025-06-30", "2025-07-31",
             "2025-08-31", "2025-09-30", "2025-10-31", "2025-11-30",
             "2025-12-31", "2004-02-29", "2024-02-29", "2096-02-29"}) {
            std::string text = std::string(date) + "T12:00:00";
            auto expected = text; expected[10] = ' ';
            check(RtcConfig::parse(text).session_text() == expected, "valid boundary: " + text);
        }
        for (const char* date : {"2025-01-32", "2025-02-29", "2025-03-32",
             "2025-04-31", "2025-05-32", "2025-06-31", "2025-07-32",
             "2025-08-32", "2025-09-31", "2025-10-32", "2025-11-31",
             "2025-12-32", "2000-02-30", "2001-02-29", "2099-02-29",
             "1999-12-31", "2100-01-01", "0000-01-01", "2026-00-01",
             "2026-13-01", "2026-09-00"}) rejects(std::string(date) + "T12:00:00");
        // Catches normalization, non-ASCII digits, loose separators and tails.
        for (const char* text : {"", "2026-09-05", "2026-09-05T12:00:0",
             "2026-09-05T12:00:000", "2026-09-05T24:00:00", "2026-09-05T12:60:00",
             "2026-09-05T12:00:60", "2026-09-05 12:00:00", "2026-09-05t12:00:00",
             "2026/09-05T12:00:00", "2026-09/05T12:00:00", "2026-09-05T12-00:00",
             "2026-09-05T12:00-00", "2026-09-05T12:00:00Z", "2026-09-05T12:00:00.0",
             "2026-09-05T12:00:00+00:00", " 2026-09-05T12:00:00", "2026-09-05T12:00:00\n",
             "+026-09-05T12:00:00", "2026-+9-05T12:00:00", "2026-09--5T12:00:00",
             "2026-09-05T-1:00:00", "2026-09-05T12:0a:00", "2026-09-05T12:00: 0",
             "２０２６-09-05T12:00:00"}) rejects(text);
        rejects(std::string("2026-09-05T12:00:00") + '\0');
        auto nonascii = std::string("2026-09-05T12:00:00"); nonascii[0] = char(0xff);
        rejects(nonascii);
        std::cout << "PASS " << checks << " RTC checks\n";
    } catch (const std::exception& error) {
        std::cerr << "FAIL " << error.what() << '\n'; return 1;
    }
}
