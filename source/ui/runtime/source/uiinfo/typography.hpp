#pragma once
#include "uiinfo/text_buffer.hpp"
namespace AutomateLite::UIInfo::Typography {
// Bitmap glyphs should not be squeezed to 0.91x or stretched to 1.05x.
// Keep existing call-site/layout parameters, but render all custom text at the
// game's native 1x glyph scale. This remains larger than the old 0.6-0.75x body.
constexpr float Scale(float) { return 1.0f; }
constexpr float Pixel(float value) {
    return static_cast<float>(static_cast<int>(value>=0 ? value+0.5f : value-0.5f));
}
inline constexpr int ShadowOffset=1,ShadowCount=1;
constexpr int Ceil(float value) { int i=static_cast<int>(value);return i+(value>i); }
// Conservative bounds for the game's localized small font. Text is still drawn
// by the vanilla font renderer; this estimate only reserves background space.
constexpr int LineHeight(float previous) { return Ceil(40*Scale(previous)); }
constexpr int Clamp(int v,int lo,int hi) { return hi<lo ? lo : v<lo ? lo : v>hi ? hi : v; }
struct Bounds { int x,y,width,height; };
struct Size { int width,height; };
// Switch renders this game in landscape. Normalize the two legacy viewport
// getter results so an inverted pair cannot put a bottom button off-screen.
constexpr Size Landscape(int a,int b) {
    if(a<160 || b<160 || a>8192 || b>8192) return {};
    return a>=b ? Size{a,b} : Size{b,a};
}
constexpr Bounds Panel(int x,int y,int preferredWidth,int lines,float previous,int sw,int sh,int padding=12) {
    int width=Clamp(preferredWidth,48,sw-16);
    int height=Clamp(lines*LineHeight(previous)+padding*2,LineHeight(previous)+padding*2,sh-16);
    return {Clamp(x,8,sw-width-8),Clamp(y,8,sh-height-8),width,height};
}
template<std::size_t N> struct Wrapped { TextBuffer<N> text; int lines{1}; bool truncated{}; };
template<std::size_t N> constexpr Wrapped<N> Wrap(const TextBuffer<N>& input,int pixels,float previous,int maxLines) {
    Wrapped<N> out;
    const int maxUnits=Clamp(static_cast<int>(pixels/(16*Scale(previous))),4,4096);
    maxLines=Clamp(maxLines,1,64);
    int used=0;
    for(std::size_t i=0;i<input.Size();++i) {
        const char16_t c=input.Data()[i];
        if(c==u'\r') continue;
        const bool pair=c>=0xD800 && c<=0xDBFF && i+1<input.Size() && input.Data()[i+1]>=0xDC00 && input.Data()[i+1]<=0xDFFF;
        const unsigned count=pair ? 2 : 1;
        const int units=c<128 ? 1 : 2;
        if(c==u'\n' || used+units>maxUnits) {
            if(out.lines>=maxLines) { out.text.Append(u"…");out.truncated=true;break; }
            if(!out.text.Append(u"\n")) { out.truncated=true;break; }
            ++out.lines;used=0;
            if(c==u'\n') continue;
        }
        if((out.lines==maxLines && used+units>maxUnits-2 && i+count<input.Size()) || out.text.Size()+count+2>=N) {
            out.text.Append(u"…");out.truncated=true;break;
        }
        if(!out.text.Append(input.Data()+i,count)) { out.truncated=true;break; }
        used+=units;i+=count-1;
    }
    return out;
}
constexpr int MapRows(int height) {
    // Two NPC text lines, with one extra reserved for a long localized name.
    return Clamp((height-LineHeight(0.65f)-40)/(3*LineHeight(0.65f)),1,8);
}
constexpr unsigned SettingsRows(int panelHeight) {
    return static_cast<unsigned>(Clamp((panelHeight-220)/(LineHeight(0.75f)+10),1,8));
}
}
