#include "uiinfo/preflight.hpp"
using namespace AutomateLite::UIInfo;
constexpr bool VersionMismatchRejected() {
    unsigned count=0;
    if(!MatchAllSignatures([&](std::uintptr_t,std::uint32_t){++count;return true;})) return false;
    // Damage each fingerprint in turn; none can pass the real matcher.
    for(unsigned bad=0;bad<count;++bad) {
        unsigned at=0;
        if(MatchAllSignatures([&](std::uintptr_t,std::uint32_t){return at++!=bad;})) return false;
    }
    return count>100;
}
static_assert(VersionMismatchRejected());
constexpr bool FishingHooksDoNotOverlap() {
    for(auto s:UiHookSignatures) {
        if(s.offset<0x167FC08 && s.offset+20>0x167FBD4) return false;
        if(s.offset<0x167FFE4 && s.offset+20>0x167FFE0) return false;
    }
    return true;
}
static_assert(FishingHooksDoNotOverlap());
