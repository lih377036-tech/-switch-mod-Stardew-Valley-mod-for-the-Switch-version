#include "uiinfo/menu_layout.hpp"
#include "uiinfo/menu_input.hpp"
#include <initializer_list>
using namespace AutomateLite::UIInfo;
constexpr bool HammerLayout() {
    for(auto screen:{Typography::Size{640,360},Typography::Size{960,540},Typography::Size{1280,720},Typography::Size{1920,1080}}) {
        for(auto frame:{MenuLayout::Bounds{32,48,screen.width-64,screen.height-96},
                       MenuLayout::Bounds{0,0,0,0},MenuLayout::Bounds{-200,-50,1200,600},
                       MenuLayout::Bounds{1200,800,1400,900}}) {
            for(bool selected:{false,true}) {
                auto b=MenuLayout::Hammer(frame,screen,selected);
                if(b.x<8 || b.y<8 || b.x+b.width>screen.width-8 || b.y+b.height>screen.height-8) return false;
                if(!MenuLayout::Contains(b,b.x,b.y) || !MenuLayout::Contains(b,b.x+63,b.y+63)) return false;
                if(MenuLayout::Contains(b,b.x+64,b.y) || MenuLayout::Contains(b,b.x,b.y+64)) return false;
            }
            auto body=MenuLayout::Body(frame,screen);
            if(body.x<8 || body.y<8 || body.x+body.width>screen.width-8 || body.y+body.height>screen.height-8) return false;
        }
    }
    const auto at=MenuLayout::Hammer({100,50,1000,600},{1280,720},false);
    return at.x==935 && at.y==66;
}
constexpr bool ControllerRouting() {
    using namespace MenuInput;
    // Exhaust every modifier/open/held-item/repeat combination for all common
    // native menu buttons. Ordinary single keys always pass to the game.
    for(int button:{1,2,4,8,0x10,0x20,0x40,0x80,0x1000,0x2000,0x4000,0x8000,0x800000,0x400000})
    for(bool left:{false,true})for(bool right:{false,true})for(bool open:{false,true})
    for(bool ready:{false,true})for(bool latched:{false,true}) {
        const auto a=Route(button,left,right,open,ready,latched);
        if(open) { if(a!=Action::Settings)return false;continue; }
        const bool combo=button==Up && left && right;
        if(!combo && a!=Action::Pass)return false;
        if(combo && ready && !latched && a!=Action::Open)return false;
        if(combo && (!ready || latched) && a!=Action::Consume)return false;
    }
    Latch latch{true};latch.Observe(true,true);if(!latch.down)return false;
    latch.Observe(true,false);if(latch.down)return false;
    latch.down=true;latch.Observe(false,true);
    return !latch.down;
}
static_assert(HammerLayout());
static_assert(ControllerRouting());
constexpr bool HammerControllerRegression() {
    using namespace MenuInput;
    // Regression: confirm over the drawn hammer previously always passed to
    // vanilla, which has no custom button in its page navigation list.
    if(RouteHammer(Confirm,false,true,false,true)!=HammerAction::Open)return false;
    if(RouteHammer(Confirm,false,true,false,false)!=HammerAction::Consume)return false;
    // Walk from the adjacent native tab, open, return focus, and leave downward.
    if(RouteHammer(Right,false,false,true,true)!=HammerAction::Focus)return false;
    if(RouteHammer(StickRight,false,false,true,true)!=HammerAction::Focus)return false;
    if(RouteHammer(Confirm,true,false,false,true)!=HammerAction::Open)return false;
    if(RouteHammer(Confirm,true,false,false,false)!=HammerAction::Consume)return false;
    if(RouteHammer(Left,true,false,false,true)!=HammerAction::BlurConsume)return false;
    if(RouteHammer(StickLeft,true,false,false,true)!=HammerAction::BlurConsume)return false;
    if(RouteHammer(Cancel,true,false,false,true)!=HammerAction::BlurConsume)return false;
    if(RouteHammer(Down,true,false,false,true)!=HammerAction::BlurPass)return false;
    if(RouteHammer(StickDown,true,false,false,true)!=HammerAction::BlurPass)return false;
    if(RouteHammer(StickUp,true,false,false,true)!=HammerAction::Consume)return false;
    // Every stick and D-pad direction must produce the same UI action. Native
    // passthrough retains the original raw button in the runtime callback.
    for(bool focused:{false,true})for(bool hover:{false,true})
    for(bool beside:{false,true})for(bool ready:{false,true}) {
        if(RouteHammer(StickLeft,focused,hover,beside,ready)!=RouteHammer(Left,focused,hover,beside,ready))return false;
        if(RouteHammer(StickRight,focused,hover,beside,ready)!=RouteHammer(Right,focused,hover,beside,ready))return false;
        if(RouteHammer(StickUp,focused,hover,beside,ready)!=RouteHammer(Up,focused,hover,beside,ready))return false;
        if(RouteHammer(StickDown,focused,hover,beside,ready)!=RouteHammer(Down,focused,hover,beside,ready))return false;
    }
    for(int button:{Up,Down,Left,Right,Confirm,Cancel,0x10,0x20,0x40,0x80,0x100,0x200,0x800000,0x400000})
        if(RouteHammer(button,false,false,false,true)!=HammerAction::Pass)return false;
    // A physical press dispatched as pad+pointer must open exactly once.
    EntryGate gate;
    if(!gate.Accept(0) || gate.Accept(0) || gate.Accept(249) || !gate.Accept(250))return false;
    if(!gate.Recent(499) || gate.Recent(500))return false;
    const MenuLayout::Bounds hammer{935,66,64,64};
    return MenuLayout::BesideHammer(hammer,903,98) &&
        !MenuLayout::BesideHammer(hammer,935,98) &&
        !MenuLayout::BesideHammer(hammer,800,98) &&
        !MenuLayout::BesideHammer(hammer,903,180);
}
static_assert(HammerControllerRegression());
