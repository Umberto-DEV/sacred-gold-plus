// Initial DS hardware clock configuration; no host timezone/normalization.
#pragma once

#include <iomanip>
#include <locale>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>

namespace hg_runtime {
struct RtcConfig {
    int year = 2026, month = 9, day = 5, hour = 12, minute = 0, second = 0;

    static RtcConfig parse(std::string_view text) {
        const auto invalid = []() {
            throw std::invalid_argument("Invalid --rtc: expected a valid 2000..2099 date in YYYY-MM-DDTHH:MM:SS");
        };
        if (text.size() != 19) invalid();
        for (std::size_t i = 0; i < text.size(); ++i) {
            char separator = 0;
            if (i == 4 || i == 7) separator = '-';
            else if (i == 10) separator = 'T';
            else if (i == 13 || i == 16) separator = ':';
            if (separator ? text[i] != separator : text[i] < '0' || text[i] > '9') invalid();
        }
        const auto digits = [&](std::size_t offset, std::size_t count) {
            int value = 0;
            for (std::size_t i = offset; i < offset + count; ++i) value = value * 10 + text[i] - '0';
            return value;
        };
        RtcConfig value{digits(0, 4), digits(5, 2), digits(8, 2),
                        digits(11, 2), digits(14, 2), digits(17, 2)};
        if (value.year < 2000 || value.year > 2099 || value.month < 1 || value.month > 12 ||
            value.hour > 23 || value.minute > 59 || value.second > 59) invalid();
        constexpr int monthDays[] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
        const bool leap = value.year % 4 == 0 && (value.year % 100 != 0 || value.year % 400 == 0);
        const int limit = monthDays[value.month - 1] + (value.month == 2 && leap ? 1 : 0);
        if (value.day < 1 || value.day > limit) invalid();
        return value;
    }

    std::string session_text() const {
        std::ostringstream text;
        text.imbue(std::locale::classic());
        text << std::setfill('0') << std::setw(4) << year << '-'
             << std::setw(2) << month << '-' << std::setw(2) << day << ' '
             << std::setw(2) << hour << ':' << std::setw(2) << minute << ':'
             << std::setw(2) << second;
        return text.str();
    }
};
} // namespace hg_runtime
