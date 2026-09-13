// Bounded, offline melonDS test frontend; GPL-3.0-or-later.
#include "Args.h"
#include "NDS.h"
#include "NDSCart.h"
#include "Savestate.h"
#include "hg_trace.h"
#include <algorithm>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <vector>

using namespace melonDS;
namespace fs = std::filesystem;
static std::vector<u8> readFile(const fs::path& p) {
    std::ifstream f(p,std::ios::binary|std::ios::ate);
    if(!f)throw std::runtime_error("Cannot read "+p.string());
    auto len=f.tellg(); if(len<0)throw std::runtime_error("Invalid length");
    std::vector<u8> d(static_cast<size_t>(len)); f.seekg(0);f.read(reinterpret_cast<char*>(d.data()),d.size());
    if(!f)throw std::runtime_error("Short read "+p.string());return d;
}
static u32 number(const std::string& s) { size_t pos=0; auto n=std::stoul(s,&pos,0);if(pos!=s.size()||n>0xffffffff)throw std::runtime_error("Invalid number: "+s);return n; }
static u32 keyMask(std::string text) {
    std::transform(text.begin(),text.end(),text.begin(),[](unsigned char c){return std::toupper(c);});
    if(text.empty()||text=="NONE"||text=="-")return 0xfff;
    std::replace(text.begin(),text.end(),'+',' ');std::replace(text.begin(),text.end(),',',' ');
    const std::map<std::string,int> bits={{"A",0},{"B",1},{"SELECT",2},{"START",3},{"RIGHT",4},{"LEFT",5},{"UP",6},{"DOWN",7},{"R",8},{"L",9},{"X",10},{"Y",11}};
    u32 mask=0xfff;std::istringstream in(text);std::string k;while(in>>k){auto it=bits.find(k);if(it==bits.end())throw std::runtime_error("Unknown key "+k);mask&=~(1u<<it->second);}return mask;
}
struct Watch { std::string name;u32 addr;int width; };
struct Freeze { u32 addr,value;int width; };
class Harness {
public:
    fs::path out;std::unique_ptr<NDS> nds;u64 frames=0;std::vector<Watch> watches;std::vector<Freeze> freezes;
    std::ofstream csv,commands;bool csvHeader=false;
    Harness(const fs::path& rom,const fs::path& dir,const fs::path& save):out(fs::absolute(dir)) {
        fs::create_directories(out);out=fs::weakly_canonical(out);
        csv.open(out/"frames.csv");commands.open(out/"commands.log");
        NDSArgs args;args.JIT=std::nullopt;nds=std::make_unique<NDS>(std::move(args));
        auto data=readFile(rom);auto cart=NDSCart::ParseROM(data.data(),data.size());
        if(data.size()>=16 && std::string(reinterpret_cast<char*>(data.data()+12),4)=="IPKE") {
            watches.push_back({"game_vblank_counter",0x021D1138,4});
            watches.push_back({"game_frame_counter",0x021D113C,4});
        }
        if(!cart)throw std::runtime_error("ROM parse failed");nds->SetNDSCart(std::move(cart));
        nds->Reset();nds->RTC.SetDateTime(2026,9,5,12,0,0);
        if(!save.empty()){auto s=readFile(save);nds->SetNDSSave(s.data(),s.size());}
        nds->SetupDirectBoot(rom.filename().string());nds->SetKeyMask(0xfff);nds->Start();
        std::ofstream meta(out/"session.txt");meta<<"melonDS revision 906e9ebb27da8c6a715cd7abab4abfe8a8d29427\nROM="<<fs::absolute(rom)<<"\nRTC=2026-09-05 12:00:00\nCPU=interpreter\nRenderer=software\nBIOS=FreeBIOS\nFirmware=generated\n";
    }
    fs::path output(const std::string& name) {
        auto p=fs::weakly_canonical(out/name);auto rel=p.lexically_relative(out);
        if(rel.empty()||*rel.begin()=="..")throw std::runtime_error("Output must be inside --out");
        fs::create_directories(p.parent_path());return p;
    }
    void writeFile(const std::string& name,const void* data,size_t len) {
        auto p=output(name);std::ofstream f(p,std::ios::binary);f.write(static_cast<const char*>(data),len);if(!f)throw std::runtime_error("Cannot write "+p.string());
        std::cout<<"WROTE "<<p<<" bytes="<<len<<std::endl;
    }
    u32 read(u32 addr,int width) { if(width==1)return nds->ARM9Read8(addr);if(width==2)return nds->ARM9Read16(addr);if(width==4)return nds->ARM9Read32(addr);throw std::runtime_error("Width must be 1, 2 or 4"); }
    void write(u32 addr,u32 value,int width) { if(width==1)nds->ARM9Write8(addr,value);else if(width==2)nds->ARM9Write16(addr,value);else if(width==4)nds->ARM9Write32(addr,value);else throw std::runtime_error("Width must be 1, 2 or 4"); }
    void row(u32 lines) {
        if(!csvHeader){csv<<"frame,scanlines,arm9_pc,arm7_pc,keymask,render_polygons,geometry_vertices,dma_visits,dma_executed,dma_r10_changes,spi_visits,spi_executed,spi_r10_changes,main_loop_jumps";for(auto& w:watches)csv<<','<<w.name;csv<<'\n';csvHeader=true;}
        csv<<frames<<','<<lines<<",0x"<<std::hex<<nds->GetPC(0)<<",0x"<<nds->GetPC(1)<<",0x"<<nds->KeyInput;
        csv<<std::dec<<','<<nds->GPU.GPU3D.RenderNumPolygons<<','<<nds->GPU.GPU3D.NumVertices;
        for(auto& c:HGTrace::Counters)csv<<','<<c.visits<<','<<c.executed<<','<<c.r10_changes;
        csv<<','<<HGTrace::MainLoopJumps;
        csv<<std::hex;
        for(auto& w:watches)csv<<",0x"<<read(w.addr,w.width);csv<<std::dec<<'\n';
    }
    void status() { std::cout<<"STATUS frame="<<frames<<" running="<<nds->IsRunning()<<" arm9_pc=0x"<<std::hex<<nds->GetPC(0)<<" arm7_pc=0x"<<nds->GetPC(1)<<std::dec<<" sram="<<nds->GetNDSSaveLength()<<" cheats="<<nds->AREngine.Cheats.size()<<" watches="<<watches.size()<<" freezes="<<freezes.size()<<" render_polygons="<<nds->GPU.GPU3D.RenderNumPolygons<<" geometry_vertices="<<nds->GPU.GPU3D.NumVertices<<std::endl;for(int i=0;i<2;++i){auto& c=HGTrace::Counters[i];std::cout<<"TRACE site="<<(i?"spi_020de16c":"dma_020d3fa8")<<" enabled="<<HGTrace::Enabled<<" visits="<<c.visits<<" executed="<<c.executed<<" r10_changes="<<c.r10_changes<<" last_before=0x"<<std::hex<<c.last_before<<" last_after=0x"<<c.last_after<<" last_instruction=0x"<<c.last_instruction<<std::dec<<std::endl;} }
    void run(u32 count) {
        if(count>1000000)throw std::runtime_error("At most 1000000 frames per command");
        auto t=std::chrono::steady_clock::now();s16 audio[8192];
        for(u32 i=0;i<count;++i){if(!nds->IsRunning())throw std::runtime_error("Console stopped");for(auto& f:freezes)write(f.addr,f.value,f.width);u32 lines=nds->RunFrame();++frames;row(lines);while(nds->SPU.GetOutputSize()>0)nds->SPU.ReadOutput(audio,std::min(4096,nds->SPU.GetOutputSize()));}
        csv.flush();double seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-t).count();
        std::cout<<"RAN count="<<count<<" seconds="<<seconds<<" fps="<<(seconds?count/seconds:0)<<std::endl;status();
    }
    void capture(const std::string& name) {
        void* top=nullptr;void* bottom=nullptr;if(!nds->GPU.GetFramebuffers(&top,&bottom))throw std::runtime_error("No RAM framebuffer");
        std::vector<u8> image;std::string header="P6\n256 384\n255\n";image.insert(image.end(),header.begin(),header.end());
        for(void* screen:{top,bottom}){const u32* p=static_cast<const u32*>(screen);for(int i=0;i<256*192;++i){image.push_back(p[i]>>16);image.push_back(p[i]>>8);image.push_back(p[i]);}}
        writeFile(name,image.data(),image.size());
    }
    void save(const std::string& name) { Savestate s;if(!nds->DoSavestate(&s)||s.Error)throw std::runtime_error("Save state failed");writeFile(name,s.Buffer(),s.Length()); }
    void load(const std::string& name) { fs::path p=name;if(p.is_relative())p=out/p;auto d=readFile(p);Savestate s(d.data(),d.size(),false);if(s.Error||!nds->DoSavestate(&s)||s.Error)throw std::runtime_error("Load state failed");nds->Start();std::cout<<"LOADED "<<p<<std::endl; }
    bool command(const std::string& line) {
        commands<<frames<<' '<<line<<'\n';commands.flush();std::istringstream in(line);std::vector<std::string> t;std::string token;while(in>>std::quoted(token))t.push_back(token);
        if(t.empty()||t[0][0]=='#')return true;auto require=[&](size_t n){if(t.size()<n)throw std::runtime_error("Missing command arguments");};auto n=[&](size_t i){require(i+1);return number(t[i]);};
        const auto& c=t[0];
        if(c=="quit"||c=="exit")return false;
        else if(c=="status")status();
        else if(c=="tracepc"){require(2);if(t[1]=="reset"){for(auto& c:HGTrace::Counters)c={};HGTrace::MainLoopJumps=0;}else HGTrace::Enabled=(t[1]=="on");}
        else if(c=="run"){require(2);if(t.size()>2)nds->SetKeyMask(keyMask(t[2]));run(n(1));if(t.size()>2)nds->SetKeyMask(0xfff);}
        else if(c=="key"){require(2);nds->SetKeyMask(keyMask(t[1]));}
        else if(c=="tap"){require(2);nds->SetKeyMask(keyMask(t[1]));run(t.size()>2?n(2):2);nds->SetKeyMask(0xfff);run(t.size()>3?n(3):30);}
        else if(c=="touch"){require(3);nds->TouchScreen(n(1),n(2));if(t.size()>3){run(n(3));nds->ReleaseScreen();}}
        else if(c=="release")nds->ReleaseScreen();
        else if(c=="capture"){require(2);capture(t[1]);}
        else if(c=="save"){require(2);save(t[1]);}
        else if(c=="load"){require(2);load(t[1]);}
        else if(c=="dump"){require(2);writeFile(t[1],nds->MainRAM,0x400000);}
        else if(c=="sram"){require(2);writeFile(t[1],nds->GetNDSSave(),nds->GetNDSSaveLength());}
        else if(c=="read"){require(2);int width=t.size()>2?n(2):4;u32 count=t.size()>3?n(3):1;for(u32 i=0;i<count;++i)std::cout<<"READ 0x"<<std::hex<<(n(1)+i*width)<<" 0x"<<read(n(1)+i*width,width)<<std::dec<<std::endl;}
        else if(c=="write"){require(3);write(n(1),n(2),t.size()>3?n(3):4);}
        else if(c=="freeze"){require(3);freezes.push_back({n(1),n(2),int(t.size()>3?n(3):4)});}
        else if(c=="unfreeze")freezes.clear();
        else if(c=="watch"){require(3);watches.push_back({t[1],n(2),int(t.size()>3?n(3):4)});csvHeader=false;}
        else if(c=="clearwatches"){watches.clear();csvHeader=false;}
        else if(c=="cheat"){require(2);fs::path p=t[1];if(p.is_relative())p=out/p;std::ifstream f(p);if(!f)throw std::runtime_error("Cannot read cheat file");ARCode code{};code.Name=p.filename().string();code.Enabled=true;std::string l;while(std::getline(f,l)){auto comment=l.find('#');if(comment!=std::string::npos)l.resize(comment);std::istringstream words(l);std::string w;while(words>>w)code.Code.push_back(std::stoul(w,nullptr,16));}if(code.Code.size()%2)throw std::runtime_error("Cheat words must be paired");nds->AREngine.Cheats.push_back(std::move(code));}
        else if(c=="clearcheats")nds->AREngine.Cheats.clear();
        else if(c=="help")std::cout<<"run FRAMES [KEYS] | tap KEYS [HOLD=2] [WAIT=30] | key KEYS | touch X Y [FRAMES] | release | capture FILE.ppm | save FILE.state | load FILE | dump FILE.bin | sram FILE.sav | read ADDRESS [WIDTH=4] [COUNT=1] | write ADDRESS VALUE [WIDTH=4] | freeze ADDRESS VALUE [WIDTH=4] | unfreeze | watch LABEL ADDRESS [WIDTH=4] | clearwatches | cheat FILE | clearcheats | status | quit\n";
        else throw std::runtime_error("Unknown command: "+c);
        return true;
    }
};
int main(int argc,char** argv) {
    try {
        fs::path rom,out,script,sram,load;u32 frames=0;bool interactive=false;
        for(int i=1;i<argc;++i){std::string a=argv[i];auto arg=[&](){if(++i>=argc)throw std::runtime_error("Missing value for "+a);return std::string(argv[i]);};if(a=="--rom")rom=arg();else if(a=="--out")out=arg();else if(a=="--script")script=arg();else if(a=="--sram")sram=arg();else if(a=="--load")load=arg();else if(a=="--frames")frames=number(arg());else if(a=="--interactive")interactive=true;else if(a=="--trace-pc")HGTrace::Enabled=true;else throw std::runtime_error("Unknown option "+a);}
        if(rom.empty()||out.empty())throw std::runtime_error("Usage: hg_runtime --rom ROM --out DIR [--frames N] [--script FILE] [--interactive] [--sram FILE] [--load FILE]");
        Harness h(rom,out,sram);if(!load.empty())h.load(load.string());if(frames)h.run(frames);
        if(!script.empty()){std::ifstream f(script);if(!f)throw std::runtime_error("Cannot read script");std::string l;while(std::getline(f,l))if(!h.command(l))break;}
        h.capture("latest.ppm");h.status();
        if(interactive){std::string line;std::cout<<"READY"<<std::endl;while(std::getline(std::cin,line)){try{if(!h.command(line))break;}catch(const std::exception& e){std::cout<<"ERROR "<<e.what()<<std::endl;}std::cout<<"READY"<<std::endl;}}
        h.csv.flush();return 0;
    }catch(const std::exception& e){std::cerr<<"ERROR "<<e.what()<<std::endl;return 1;}
}
