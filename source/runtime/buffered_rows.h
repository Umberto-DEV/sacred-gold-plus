#pragma once

#include <cstddef>
#include <string>

namespace hg_runtime {

class BufferedRows {
public:
    void append(const std::string& row) { bytes_ += row; }
    std::size_t size() const { return bytes_.size(); }

    template <typename Sink>
    void flush(Sink& sink) {
        if (bytes_.empty()) return;
        sink.write(bytes_);
        bytes_.clear();
    }

    template <typename Sink, typename Work>
    void runAndFlush(Sink& sink, Work work) {
        try {
            work();
        } catch (...) {
            try {
                flush(sink);
                sink.flush();
            } catch (...) {
                // Preserve the frame/core failure; unwritten bytes stay buffered.
            }
            throw;
        }
        flush(sink);
        sink.flush();
    }

private:
    std::string bytes_;
};

}  // namespace hg_runtime
