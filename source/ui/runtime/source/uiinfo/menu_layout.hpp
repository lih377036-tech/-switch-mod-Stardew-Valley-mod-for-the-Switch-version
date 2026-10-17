#pragma once
#include "uiinfo/typography.hpp"
namespace AutomateLite::UIInfo::MenuLayout {
using Bounds=Typography::Bounds;
using Size=Typography::Size;
constexpr bool Contains(Bounds r,int x,int y) {
    return x>=r.x && y>=r.y && x<r.x+r.width && y<r.y+r.height;
}
constexpr bool ValidFrame(Bounds f) {
    return f.width>=320 && f.width<=8192 && f.height>=200 && f.height<=8192 &&
        f.x>=-8192 && f.x<=8192 && f.y>=-8192 && f.y<=8192;
}
constexpr Bounds Hammer(Bounds frame,Size screen,bool selected) {
    // UIInfoSuite2's original PC button is at menu.x+width-165,
    // menu.y+16 (selected +24). Keep draw and hit bounds identical.
    if(!ValidFrame(frame))frame={12,32,screen.width-24,screen.height-64};
    return {Typography::Clamp(frame.x+frame.width-165,8,screen.width-72),
        Typography::Clamp(frame.y+(selected ? 24 : 16),8,screen.height-72),64,64};
}
constexpr Bounds Body(Bounds frame,Size screen) {
    if(!ValidFrame(frame))frame={12,32,screen.width-24,screen.height-64};
    const int x=Typography::Clamp(frame.x+8,8,screen.width-328);
    const int y=Typography::Clamp(frame.y+88,88,screen.height-272);
    const int w=Typography::Clamp(frame.width-16,320,screen.width-x-8);
    const int h=Typography::Clamp(frame.height-100,264,screen.height-y-8);
    return {x,y,w,h};
}
constexpr bool BesideHammer(Bounds hammer,int x,int y) {
    // Continue right from the native tab immediately left of the added icon.
    // This uses the same UI-coordinate cursor as drawing/clicking; no guessed
    // managed GameMenu fields, fake pages or unrooted components are needed.
    return x>=hammer.x-80 && x<hammer.x && y>=hammer.y-16 && y<hammer.y+80;
}
}
