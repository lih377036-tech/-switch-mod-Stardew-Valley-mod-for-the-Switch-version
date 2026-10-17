#include "uiinfo/menu.hpp"
#include "uiinfo/settings.hpp"
#include "uiinfo/aot.hpp"
#include "uiinfo/menu_layout.hpp"
#include "uiinfo/menu_input.hpp"
namespace AutomateLite::UIInfo {
namespace {
using namespace Aot;
bool g_Open{};
unsigned g_Selected{};
bool g_ShortcutAvailable{};
bool g_HammerFocused{};
bool g_EntryBlocked{};
MenuInput::Latch g_ShortcutLatch;
MenuInput::EntryGate g_EntryGate;
constexpr unsigned Options=static_cast<unsigned>(Option::Count);
constexpr unsigned Actions=4, Entries=Options+Actions;
Rectangle Viewport() {
    const auto screen=ScreenSize(2);
    return {0,0,screen.width,screen.height};
}
MenuLayout::Bounds Frame(void* menu) {
    return {Read<int>(menu,0x28),Read<int>(menu,0x2C),Read<int>(menu,0x30),Read<int>(menu,0x34)};
}
Rectangle Panel(void* menu) {
    const auto r=MenuLayout::Body(Frame(menu),ScreenSize(2));
    return {r.x,r.y,r.width,r.height};
}
Rectangle EntryButton(void* menu) {
    const auto r=MenuLayout::Hammer(Frame(menu),ScreenSize(2),g_Open);
    return {r.x,r.y,r.width,r.height};
}
bool Contains(Rectangle r,int x,int y) { return x>=r.x && y>=r.y && x<r.x+r.width && y<r.y+r.height; }
void Label(void* batch,const char16_t* value,int x,int y,float scale=0.75f) {
    TextBuffer<256> text; text.Append(value); Text(batch,text,static_cast<float>(x),static_cast<float>(y),0xFFFFFFFF,scale);
}
void Close() { if(g_Open) SaveSettings(); g_Open=false;g_HammerFocused=false;g_EntryBlocked=false; }
bool CanEnter(void* menu) { return Viewport().height>=360 && Call<bool>(0x16EE120,menu); }
void Enter() { RefreshSettings();g_Open=true;g_Selected=0;g_HammerFocused=false;g_EntryBlocked=false; }
void TryEnter(void* menu) {
    if(!CanEnter(menu)) {g_EntryBlocked=true;return;}
    if(g_EntryGate.Accept(Milliseconds())) Enter();
}
void* Pad() {
    if(!g_ShortcutAvailable) return nullptr;
    void* input=Static<void*>(0xE27F5C0);
    void* pad=input ? reinterpret_cast<void*>(reinterpret_cast<std::uintptr_t>(input)+0x9C) : nullptr;
    return pad && Call<bool>(0xD40D0,pad) ? pad : nullptr;
}
bool Down(void* pad,int button) { return pad && Call<bool>(0xD4220,pad,button); }
void DrawHammer(void* menu,void* batch) {
    const auto r=EntryButton(menu);
    void* texture=Static<void*>(0xE27F558);
    if(!texture) return;
    if(g_HammerFocused && !g_Open) Box(batch,{r.x-4,r.y-4,r.width+8,r.height+8},0xFFFFCC66u);
    // Vanilla mouseCursors sprites also used by the PC mod: tab and hammer.
    NullableRectangle tab{{16,368,16,16},1,{}},hammer{{32,672,16,16},1,{}};
    Call<void>(0xBFF70,batch,texture,r,&tab,0xFFFFFFFFu);
    Call<void>(0xBFF70,batch,texture,Rectangle{r.x+8,r.y+14,48,48},&hammer,0xFFFFFFFFu);
    const int mx=Call<int>(0x13C3920,true),my=Call<int>(0x13C3A40,true);
    if(!g_Open && (g_HammerFocused || Contains(r,mx,my))) {
        TextBuffer<96> hint;hint.Append(u"UI 信息设置");
        hint.Append(g_EntryBlocked ? u"\n请先放回拖动物品，或返回背包页" : u"\n按确认键打开");
        const auto screen=ScreenSize(2);
        TextPanel(batch,hint,r.x-360,r.y+72,480,screen.width,screen.height,0.7f);
    }
}
void Activate(unsigned index) {
    if(index<Options) { Toggle(static_cast<Option>(index)); return; }
    if(index==Options) { SaveSettings(true); return; }
    if(index==Options+3) { Close(); return; }
    if(!Enabled(Option::Calendar)) return;
    // Vanilla GameMenu uses null-this constructors to allocate managed menus.
    // Billboard(bool) invoker/body are independently verified; no custom GC object.
    if(Static<std::uint32_t>(0x1678130)!=0xD10343FFu) return;
    Close();
    void* board=Call<void*>(0x1678130,static_cast<void*>(nullptr),index==Options+2);
    if(board) Call<void>(0x139DCC0,board);
}
void Draw(void* menu,void* batch) {
    if(!g_Open) {
        DrawHammer(menu,batch);
        // Draw the vanilla cursor above the added icon/hover box.
        Call<void>(0x16F2AA0,menu,batch,true,-1);return;
    }
    const auto panel=Panel(menu);
    const unsigned Rows=Typography::SettingsRows(panel.height);
    Box(batch,panel,0xFF302820);
    Label(batch,u"UI Info Suite 2 — 此存档设置",panel.x+20,panel.y+16,0.9f);
    Label(batch,u"方向键选择 · 确认键切换 · 返回键保存关闭",panel.x+20,panel.y+74,0.7f);
    const unsigned page=g_Selected/Rows;
    const int step=(panel.height-220)/Rows;
    for(unsigned i=0;i<Rows;++i) {
        const unsigned index=page*Rows+i;
        if(index>=Entries) break;
        const int y=panel.y+118+static_cast<int>(i)*step;
        if(index==g_Selected) Box(batch,{panel.x+10,y-2,panel.width-20,step-2},0xFF68543A);
        TextBuffer<256> text;
        if(index<Options) {
            text.Append(Enabled(static_cast<Option>(index)) ? u"[开]  " : u"[关]  "); text.Append(OptionLabel(index));
        } else {
            constexpr const char16_t* actions[]={u"将当前设置用于新存档",u"打开日历",u"打开每日委托",u"保存并返回"};
            text.Append(actions[index-Options]);
            if((index==Options+1 || index==Options+2) && !Enabled(Option::Calendar)) text.Append(u"（开关已关闭）");
        }
        Text(batch,text,static_cast<float>(panel.x+24),static_cast<float>(y+4),0xFFFFFFFF,0.75f);
    }
    Label(batch,SettingsStatus(),panel.x+20,panel.y+panel.height-98,0.65f);
    TextBuffer<96> footer; footer.Append(u"◀ 上页    "); footer.AppendNumber(page+1);
    footer.Append(u" / "); footer.AppendNumber((Entries+Rows-1)/Rows); footer.Append(u"    下页 ▶");
    Text(batch,footer,static_cast<float>(panel.x+20),static_cast<float>(panel.y+panel.height-54),0xFFFFFFFF,0.7f);
    DrawHammer(menu,batch);
    Call<void>(0x16F2AA0,menu,batch,true,-1);
}
HOOK_DEFINE_TRAMPOLINE(MenuDrawHook) {
    static void Callback(void* menu,void* batch) {
        RefreshSettings();
        void* pad=Pad();g_ShortcutLatch.Observe(pad!=nullptr,Down(pad,MenuInput::Up));
        Orig(menu,batch);
        Draw(menu,batch);
    }
};
HOOK_DEFINE_TRAMPOLINE(MenuClickHook) {
    static void Callback(void* menu,int x,int y,bool sound) {
        if(Contains(EntryButton(menu),x,y)) {
            // One physical confirm may generate both pad and pointer events.
            // Never immediately close a panel opened by that same event.
            if(g_Open) {if(g_EntryGate.Accept(Milliseconds()))Close();} else TryEnter(menu);
            return;
        }
        g_HammerFocused=false;
        if(!g_Open) {
            // Preserve items held by the current vanilla page before replacing
            // its drawing/input or opening a Billboard (same PC precondition).
            Orig(menu,x,y,sound); return;
        }
        const auto p=Panel(menu); const unsigned Rows=Typography::SettingsRows(p.height);
        // Native tab buttons above the panel stay clickable while settings is open.
        if(y<p.y) { Close();Orig(menu,x,y,sound);return; }
        const int step=(p.height-220)/Rows;
        if(y>=p.y+118 && y<p.y+118+static_cast<int>(Rows)*step && x>=p.x && x<p.x+p.width) {
            const unsigned index=(g_Selected/Rows)*Rows+static_cast<unsigned>((y-p.y-118)/step);
            if(index<Entries) { g_Selected=index; Activate(index); }
        } else if(y>=p.y+p.height-58) {
            const unsigned page=g_Selected/Rows, pages=(Entries+Rows-1)/Rows;
            g_Selected=((x<p.x+p.width/2 ? page+pages-1 : page+1)%pages)*Rows;
        }
    }
};
HOOK_DEFINE_TRAMPOLINE(MenuPadHook) {
    static void Callback(void* menu,int button) {
        // R3 is reserved by the shipped Switch game's chat handling.
        void* pad=Pad();
        g_ShortcutLatch.Observe(pad!=nullptr,Down(pad,MenuInput::Up));
        const bool left=Down(pad,MenuInput::LeftTrigger),right=Down(pad,MenuInput::RightTrigger);
        const bool candidate=!g_Open && button==MenuInput::Up && left && right;
        const auto route=MenuInput::Route(button,left,right,g_Open,candidate && CanEnter(menu),g_ShortcutLatch.down);
        if(route==MenuInput::Action::Open) { g_ShortcutLatch.down=true;TryEnter(menu);return; }
        if(route==MenuInput::Action::Consume) return;
        if(route==MenuInput::Action::Pass) {
            const auto r=EntryButton(menu);
            const int x=Call<int>(0x13C3920,true),y=Call<int>(0x13C3A40,true);
            const bool hover=Contains(r,x,y);
            const bool needsReady=button==MenuInput::Confirm && (g_HammerFocused || hover);
            const auto hammerRoute=MenuInput::RouteHammer(button,g_HammerFocused,hover,
                MenuLayout::BesideHammer({r.x,r.y,r.width,r.height},x,y),needsReady && CanEnter(menu));
            switch(hammerRoute) {
                case MenuInput::HammerAction::Focus:g_HammerFocused=true;g_EntryBlocked=false;return;
                case MenuInput::HammerAction::BlurConsume:g_HammerFocused=false;return;
                case MenuInput::HammerAction::BlurPass:g_HammerFocused=false;Orig(menu,button);return;
                case MenuInput::HammerAction::Open:TryEnter(menu);return;
                case MenuInput::HammerAction::Consume:
                    if(needsReady)g_EntryBlocked=true;
                    return;
                case MenuInput::HammerAction::Pass:Orig(menu,button);return;
            }
        }
        if(button==MenuInput::Confirm && g_EntryGate.Recent(Milliseconds()))return;
        if(button==0x2000 || button==0x10) { Close(); return; }
        if(button==MenuInput::Confirm) { Activate(g_Selected); return; }
        const int direction=MenuInput::Direction(button);
        if(direction==MenuInput::Up) g_Selected=(g_Selected+Entries-1)%Entries;
        if(direction==MenuInput::Down) g_Selected=(g_Selected+1)%Entries;
        const unsigned Rows=Typography::SettingsRows(Panel(menu).height);
        const unsigned page=g_Selected/Rows,pages=(Entries+Rows-1)/Rows;
        if(direction==MenuInput::Left || button==MenuInput::LeftTrigger) g_Selected=((page+pages-1)%pages)*Rows;
        if(direction==MenuInput::Right || button==MenuInput::RightTrigger) g_Selected=((page+1)%pages)*Rows;
    }
};
HOOK_DEFINE_TRAMPOLINE(MenuKeyHook) {
    static void Callback(void* menu,int key) {
        if(!g_Open) { Orig(menu,key); return; }
        if(key==27) Close();
    }
};
HOOK_DEFINE_TRAMPOLINE(MenuRightHook) {
    static void Callback(void* menu,int x,int y,bool sound) {
        if(g_Open) { Close(); return; } Orig(menu,x,y,sound);
    }
};
HOOK_DEFINE_TRAMPOLINE(MenuScrollHook) {
    static void Callback(void* menu,int direction) {
        if(!g_Open) { Orig(menu,direction); return; }
        g_Selected=direction>0 ? (g_Selected+Entries-1)%Entries : (g_Selected+1)%Entries;
    }
};
HOOK_DEFINE_TRAMPOLINE(MenuCleanupHook) {
    static void Callback(void* menu) { Close(); Orig(menu); }
};
}
void InstallMenuHooks() {
    // Hook full GameMenu methods; inventory/ring trampolines remain single-owner.
    if(Static<std::uint32_t>(0x16EE2B0)!=0x6DB63BEFu ||
        Static<std::uint32_t>(0x16ED9A0)!=0xA9BC5FF8u ||
        Static<std::uint32_t>(0x16ED720)!=0xF81D0FF5u ||
        Static<std::uint32_t>(0x16EECA0)!=0xF81B0FF9u ||
        Static<std::uint32_t>(0x16EDE50)!=0xA9BE4FF4u ||
        Static<std::uint32_t>(0x16EDEA0)!=0xA9BE4FF4u ||
        Static<std::uint32_t>(0x16EEE90)!=0xA9BF7BFDu) {
        Logging.Log("[UIInfoSuite2] settings menu fingerprint mismatch"); return;
    }
    MenuDrawHook::InstallAtOffset(0x16EE2B0);
    MenuClickHook::InstallAtOffset(0x16ED9A0);
    MenuPadHook::InstallAtOffset(0x16ED720);
    MenuKeyHook::InstallAtOffset(0x16EECA0);
    MenuRightHook::InstallAtOffset(0x16EDE50);
    MenuScrollHook::InstallAtOffset(0x16EDEA0);
    MenuCleanupHook::InstallAtOffset(0x16EEE90);
    g_ShortcutAvailable=Static<std::uint32_t>(0xD40D0)==0x39400000u &&
        Static<std::uint32_t>(0xD4220)==0xF81E0FF3u && Static<std::uint32_t>(0xD4224)==0xA9017BFDu;
}
}
