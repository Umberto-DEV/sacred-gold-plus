#pragma once
#include <cerrno>
#include <cstring>
#include <filesystem>
#include <stdexcept>
#include <string>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

namespace hg_runtime {
namespace fs = std::filesystem;

inline std::runtime_error outputError(const std::string& action) {
    return std::runtime_error(action + ": " + std::strerror(errno));
}

class SecureFile {
    int fd_ = -1;
    std::string label_;
public:
    SecureFile() = default;
    SecureFile(int fd, std::string label): fd_(fd), label_(std::move(label)) {}
    SecureFile(const SecureFile&) = delete;
    SecureFile& operator=(const SecureFile&) = delete;
    SecureFile(SecureFile&& other) noexcept:
        fd_(other.fd_), label_(std::move(other.label_)) { other.fd_ = -1; }
    SecureFile& operator=(SecureFile&& other) noexcept {
        if (this != &other) {
            if (fd_ >= 0) ::close(fd_);
            fd_ = other.fd_; label_ = std::move(other.label_); other.fd_ = -1;
        }
        return *this;
    }
    ~SecureFile() { if (fd_ >= 0) ::close(fd_); }
    void write(const void* data, size_t length) {
        auto* cursor = static_cast<const unsigned char*>(data);
        while (length) {
            ssize_t amount = ::write(fd_, cursor, length);
            if (amount < 0 && errno == EINTR) continue;
            if (amount <= 0) throw std::runtime_error("Cannot write " + label_);
            cursor += amount; length -= static_cast<size_t>(amount);
        }
    }
    void write(const std::string& text) { write(text.data(), text.size()); }
    void flush() {
        if (::fsync(fd_) != 0) throw std::runtime_error("Cannot flush " + label_);
    }
};

class SecureOutputDir {
    int root_ = -1;
    fs::path path_;
    static void privateDirectory(int fd, const std::string& label) {
        struct stat info {};
        if (::fstat(fd, &info) != 0) throw outputError("Cannot inspect " + label);
        if (!S_ISDIR(info.st_mode) || info.st_uid != ::geteuid() || (info.st_mode & 0077))
            throw std::runtime_error("Output directory is not private/owned: " + label);
    }
    static int directoryAt(int parent, const std::string& name,
                           bool create, bool requirePrivate) {
        int flags = O_RDONLY | O_DIRECTORY | O_CLOEXEC;
#ifdef O_NOFOLLOW
        flags |= O_NOFOLLOW;
#endif
        int fd = ::openat(parent, name.c_str(), flags);
        if (fd < 0 && errno == ENOENT && create) {
            if (::mkdirat(parent, name.c_str(), 0700) != 0 && errno != EEXIST)
                throw outputError("Cannot create output directory " + name);
            fd = ::openat(parent, name.c_str(), flags);
            if (fd >= 0 && ::fchmod(fd, 0700) != 0) {
                int saved = errno; ::close(fd); errno = saved;
                throw outputError("Cannot protect output directory " + name);
            }
        }
        if (fd < 0) throw outputError("Cannot open output directory " + name);
        if (requirePrivate) privateDirectory(fd, name);
        return fd;
    }
    static std::pair<int, std::string> parentFor(int root, const fs::path& relative,
                                                  bool create) {
        if (relative.empty() || relative.is_absolute())
            throw std::runtime_error("Output name must be relative");
        int current = ::dup(root);
        if (current < 0) throw outputError("Cannot duplicate output directory");
        try {
            auto leaf = relative.begin();
            for (auto it = relative.begin(); it != relative.end(); ++it) leaf = it;
            std::string leafName = leaf->string();
            if (leafName.empty() || leafName == "." || leafName == ".."
                    || leafName.find('\0') != std::string::npos)
                throw std::runtime_error("Invalid output name");
            for (auto it = relative.begin(); it != leaf; ++it) {
                std::string component = it->string();
                if (component.empty() || component == "." || component == ".."
                        || component.find('\0') != std::string::npos)
                    throw std::runtime_error("Invalid output path component");
                int next = directoryAt(current, component, create, true);
                ::close(current); current = next;
            }
            return {current, leafName};
        } catch (...) { ::close(current); throw; }
    }
public: // SecureOutputDir
    explicit SecureOutputDir(const fs::path& requested) {
        fs::path absolute = fs::absolute(requested).lexically_normal();
        std::error_code statusError;
        if (fs::is_symlink(fs::symlink_status(absolute, statusError)))
            throw std::runtime_error("Output directory must not be a symlink");
        path_ = fs::weakly_canonical(absolute);
        int current = ::open("/", O_RDONLY | O_DIRECTORY | O_CLOEXEC);
        if (current < 0) throw outputError("Cannot open filesystem root");
        try {
            for (const auto& item : path_) {
                std::string component = item.string();
                if (component == "/" || component.empty()) continue;
                int next = directoryAt(current, component, true, false);
                ::close(current); current = next;
            }
            privateDirectory(current, path_.string());
            root_ = current;
        } catch (...) { ::close(current); throw; }
    }
    SecureOutputDir(const SecureOutputDir&) = delete;
    SecureOutputDir& operator=(const SecureOutputDir&) = delete;
    ~SecureOutputDir() { if (root_ >= 0) ::close(root_); }
    const fs::path& path() const { return path_; }
    void requireAbsent(const fs::path& relative) const {
        auto [parent, leaf] = parentFor(root_, relative, false);
        struct stat info {};
        int result = ::fstatat(parent, leaf.c_str(), &info, AT_SYMLINK_NOFOLLOW);
        int saved = errno; ::close(parent);
        if (result == 0)
            throw std::runtime_error("Output already exists: " + (path_ / relative).string());
        if (saved != ENOENT) { errno = saved; throw outputError("Cannot inspect output"); }
    }
    SecureFile create(const fs::path& relative) const {
        auto [parent, leaf] = parentFor(root_, relative, true);
        int flags = O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC;
#ifdef O_NOFOLLOW
        flags |= O_NOFOLLOW;
#endif
        int fd = ::openat(parent, leaf.c_str(), flags, 0600);
        int saved = errno; ::close(parent);
        if (fd < 0) { errno = saved; throw outputError("Cannot create output " + relative.string()); }
        if (::fchmod(fd, 0600) != 0) {
            saved = errno; ::close(fd); errno = saved;
            throw outputError("Cannot protect output " + relative.string());
        }
        struct stat info {};
        if (::fstat(fd, &info) != 0 || !S_ISREG(info.st_mode)
                || info.st_uid != ::geteuid() || info.st_nlink != 1
                || (info.st_mode & 0077)) {
            ::close(fd);
            throw std::runtime_error("Unsafe output identity: " + relative.string());
        }
        return SecureFile(fd, (path_ / relative).string());
    }
    void writeFile(const fs::path& relative, const void* data, size_t length) const {
        SecureFile file = create(relative);
        file.write(data, length);
        file.flush();
    }
};

} // namespace hg_runtime
