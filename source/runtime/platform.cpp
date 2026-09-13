// Offline frontend glue for melonDS; GPL-3.0-or-later.
#include "Platform.h"
#include <chrono>
#include <condition_variable>
#include <cstdarg>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <mutex>
#include <thread>
#include <dlfcn.h>

namespace melonDS::Platform {
struct FileHandle { FILE* f; };
struct Thread { std::thread t; };
struct Semaphore { std::mutex m; std::condition_variable cv; int count = 0; };
struct Mutex { std::mutex m; };
struct DynamicLibrary { void* lib; };

void SignalStop(StopReason reason, void*) { fprintf(stderr,"STOP reason=%d\n", reason); }
std::string GetLocalFilePath(const std::string& name) { return name; }
FileHandle* OpenFile(const std::string& path, FileMode mode) {
    if ((mode & NoCreate) && !std::filesystem::exists(path)) return nullptr;
    const char* m = "rb";
    if (mode & Write) {
        if (mode & Append) m = (mode & Read) ? "a+b" : "ab";
        else if (mode & Preserve) m = std::filesystem::exists(path) ? "r+b" : "w+b";
        else m = (mode & Read) ? "w+b" : "wb";
    }
    FILE* f = fopen(path.c_str(),m); return f ? new FileHandle{f} : nullptr;
}
FileHandle* OpenLocalFile(const std::string& p,FileMode m) { return OpenFile(p,m); }
bool FileExists(const std::string& p) { return std::filesystem::exists(p); }
bool LocalFileExists(const std::string& p) { return FileExists(p); }
bool CheckFileWritable(const std::string& p) { auto f=OpenFile(p,FileMode(Write|Preserve)); return f ? CloseFile(f):false; }
bool CheckLocalFileWritable(const std::string& p) { return CheckFileWritable(p); }
bool CloseFile(FileHandle* f) { bool ok=fclose(f->f)==0; delete f; return ok; }
bool IsEndOfFile(FileHandle* f) { return feof(f->f); }
bool FileReadLine(char* s,int n,FileHandle* f) { return fgets(s,n,f->f)!=nullptr; }
u64 FilePosition(FileHandle* f) { return ftello(f->f); }
bool FileSeek(FileHandle* f,s64 o,FileSeekOrigin origin) { return fseeko(f->f,o,origin==FileSeekOrigin::Start?SEEK_SET:origin==FileSeekOrigin::Current?SEEK_CUR:SEEK_END)==0; }
void FileRewind(FileHandle* f) { rewind(f->f); }
u64 FileRead(void* d,u64 s,u64 c,FileHandle* f) { return fread(d,s,c,f->f); }
bool FileFlush(FileHandle* f) { return fflush(f->f)==0; }
u64 FileWrite(const void* d,u64 s,u64 c,FileHandle* f) { return fwrite(d,s,c,f->f); }
u64 FileWriteFormatted(FileHandle* f,const char* fmt,...) { va_list v; va_start(v,fmt); int r=vfprintf(f->f,fmt,v); va_end(v); return r<0?0:r; }
u64 FileLength(FileHandle* f) { auto old=ftello(f->f); fseeko(f->f,0,SEEK_END); auto len=ftello(f->f); fseeko(f->f,old,SEEK_SET); return len<0?0:len; }
void Log(LogLevel level,const char* fmt,...) { if(level==Debug)return; va_list v;va_start(v,fmt);vfprintf(stderr,fmt,v);va_end(v); }
Thread* Thread_Create(std::function<void()> fn) { return new Thread{std::thread(std::move(fn))}; }
void Thread_Wait(Thread* t) { if(t && t->t.joinable())t->t.join(); }
void Thread_Free(Thread* t) { Thread_Wait(t);delete t; }
Semaphore* Semaphore_Create() { return new Semaphore; }
void Semaphore_Free(Semaphore* s) { delete s; }
void Semaphore_Reset(Semaphore* s) { std::lock_guard<std::mutex> l(s->m);s->count=0; }
void Semaphore_Wait(Semaphore* s) { std::unique_lock<std::mutex> l(s->m);s->cv.wait(l,[&]{return s->count>0;});s->count--; }
bool Semaphore_TryWait(Semaphore* s,int ms) { std::unique_lock<std::mutex> l(s->m); if(!s->cv.wait_for(l,std::chrono::milliseconds(ms),[&]{return s->count>0;}))return false;s->count--;return true; }
void Semaphore_Post(Semaphore* s,int count) { {std::lock_guard<std::mutex> l(s->m);s->count+=count;}s->cv.notify_all(); }
Mutex* Mutex_Create() { return new Mutex; }
void Mutex_Free(Mutex* m) { delete m; }
void Mutex_Lock(Mutex* m) { m->m.lock(); }
void Mutex_Unlock(Mutex* m) { m->m.unlock(); }
bool Mutex_TryLock(Mutex* m) { return m->m.try_lock(); }
void Sleep(u64 us) { std::this_thread::sleep_for(std::chrono::microseconds(us)); }
u64 GetUSCount() { return std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::steady_clock::now().time_since_epoch()).count(); }
u64 GetMSCount() { return GetUSCount()/1000; }
// Saves remain in emulated memory until the explicit SRAM export command.
void WriteNDSSave(const u8*,u32,u32,u32,void*) {}
void WriteGBASave(const u8*,u32,u32,u32,void*) {}
void WriteFirmware(const Firmware&,u32,u32,void*) {}
void WriteDateTime(int,int,int,int,int,int,void*) {}
void MP_Begin(void*) {}
void MP_End(void*) {}
int MP_SendPacket(u8*,int,u64,void*) { return 0; }
int MP_RecvPacket(u8*,u64*,void*) { return 0; }
int MP_SendCmd(u8*,int,u64,void*) { return 0; }
int MP_SendReply(u8*,int,u64,u16,void*) { return 0; }
int MP_SendAck(u8*,int,u64,void*) { return 0; }
int MP_RecvHostPacket(u8*,u64*,void*) { return 0; }
u16 MP_RecvReplies(u8*,u64,u16,void*) { return 0; }
int Net_SendPacket(u8*,int,void*) { return 0; }
int Net_RecvPacket(u8*,void*) { return 0; }
void Camera_Start(int,void*) {}
void Camera_Stop(int,void*) {}
void Camera_CaptureFrame(int,u32* f,int w,int h,bool,void*) { memset(f,0,w*h*4); }
void Mic_Start(void*) {}
void Mic_Stop(void*) {}
int Mic_ReadInput(s16* d,int n,void*) { memset(d,0,n*sizeof(s16));return n; }
AACDecoder* AAC_Init() { return nullptr; }
void AAC_DeInit(AACDecoder*) {}
bool AAC_Configure(AACDecoder*,int,int) { return false; }
bool AAC_DecodeFrame(AACDecoder*,const void*,int,void*,int) { return false; }
bool Addon_KeyDown(KeyType,void*) { return false; }
void Addon_RumbleStart(u32,void*) {}
void Addon_RumbleStop(void*) {}
float Addon_MotionQuery(MotionQueryType,void*) { return 0; }
DynamicLibrary* DynamicLibrary_Load(const char* name) { void* p=dlopen(name,RTLD_LAZY);return p?new DynamicLibrary{p}:nullptr; }
void DynamicLibrary_Unload(DynamicLibrary* lib) { if(lib){dlclose(lib->lib);delete lib;} }
void* DynamicLibrary_LoadFunction(DynamicLibrary* lib,const char* name) { return lib?dlsym(lib->lib,name):nullptr; }
}
