#include "uiinfo/typography.hpp"
#include <initializer_list>
using namespace AutomateLite::UIInfo;
namespace T=Typography;
constexpr bool PanelsStayOnScreen() {
    for(const auto screen:{T::Size{320,160},T::Size{640,360},T::Size{960,540},T::Size{1280,720},T::Size{1920,1080}}) {
        for(int x:{-900,0,300,1900}) for(int y:{-300,0,600,1200}) {
            const auto p=T::Panel(x,y,760,6,0.65f,screen.width,screen.height);
            if(p.x<8 || p.y<8 || p.x+p.width>screen.width-8 || p.y+p.height>screen.height-8) return false;
        }
    }
    return true;
}
constexpr bool WrappingAndTruncation() {
    TextBuffer<256> text;
    text.Append(u"阿比盖尔 · 生日\n未交谈 · 未送礼 · 10心\n罗宾\n建筑升级还需三天");
    auto full=T::Wrap(text,720,0.65f,12);
    if(full.truncated || full.lines<4) return false;
    auto narrow=T::Wrap(text,180,0.65f,3);
    if(!narrow.truncated || narrow.lines>3 || narrow.text.Data()[narrow.text.Size()-1]!=u'…') return false;
    TextBuffer<64> emoji;emoji.Append(u"人物 \U0001F600\U0001F600\U0001F600\U0001F600");
    const auto wrapped=T::Wrap(emoji,80,0.75f,8);
    for(std::size_t i=0;i<wrapped.text.Size();++i) {
        auto c=wrapped.text.Data()[i];
        if(c>=0xD800 && c<=0xDBFF) {
            if(i+1>=wrapped.text.Size() || wrapped.text.Data()[i+1]<0xDC00 || wrapped.text.Data()[i+1]>0xDFFF) return false;
            ++i;
        } else if(c>=0xDC00 && c<=0xDFFF) return false;
    }
    return true;
}
// All callers must use native glyph scale and integral positions; bitmap font
// regression previously produced 0.91x, 0.98x, 1.05x and 1.26x glyphs.
static_assert(T::Scale(0.65f)==1.0f && T::Scale(0.75f)==1.0f && T::Scale(0.9f)==1.0f);
static_assert(T::Pixel(0.49f)==0 && T::Pixel(0.5f)==1 && T::Pixel(-0.49f)==0 && T::Pixel(-0.5f)==-1);
static_assert(T::Pixel(212.75f)==213 && T::Pixel(-212.75f)==-213);
static_assert(T::ShadowCount==1 && T::ShadowOffset==1);
static_assert(T::Landscape(720,1280).width==1280 && T::Landscape(1280,720).height==720);
static_assert(T::Landscape(0,0).width==0);
static_assert(PanelsStayOnScreen());
static_assert(WrappingAndTruncation());
static_assert(T::MapRows(720)==5 && T::MapRows(160)==1);
static_assert(T::SettingsRows(672)==8 && T::SettingsRows(492)==5 && T::SettingsRows(312)==1);
