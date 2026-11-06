#pragma once
#include <iomanip>
#include <sstream>
#include <string>

namespace hg_runtime {

inline std::string safeCsvField(const std::string& input) {
    std::ostringstream cleaned;
    for (unsigned char byte : input) {
        if (byte < 0x20 || byte == 0x7f)
            cleaned << "\\x" << std::hex << std::setw(2) << std::setfill('0')
                    << static_cast<unsigned>(byte) << std::dec;
        else
            cleaned << static_cast<char>(byte);
    }
    std::string value = cleaned.str();
    if (!value.empty() && (value[0] == '=' || value[0] == '+'
            || value[0] == '-' || value[0] == '@'))
        value.insert(value.begin(), '\'');
    if (value.find_first_of(",\"") == std::string::npos) return value;
    std::string quoted = "\"";
    for (char byte : value) {
        if (byte == '\"') quoted += '\"';
        quoted += byte;
    }
    return quoted + "\"";
}

} // namespace hg_runtime
