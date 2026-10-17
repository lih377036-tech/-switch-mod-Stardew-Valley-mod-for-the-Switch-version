#pragma once
#include <cstdint>
#include "uiinfo/npc_map_signatures.hpp"
namespace AutomateLite::UIInfo {
struct HookSignature { std::uintptr_t offset; std::uint32_t word; };
inline constexpr HookSignature UiHookSignatures[]{
    {0x13E7C30,0x6DB63BEF}, // HUD
    {0x1321E40,0xD10283FF}, // experience
    {0x16F91B0,0xD10543FF}, // tooltip
    {0x1308D50,0xD10383FF}, {0x11AF830,0xD104C3FF}, // animals/pets
    {0x16EE2B0,0x6DB63BEF}, {0x16ED9A0,0xA9BC5FF8}, // settings
    {0x16ED720,0xF81D0FF5}, {0x16EECA0,0xF81B0FF9},
    {0x16EDE50,0xA9BE4FF4}, {0x16EDEA0,0xA9BE4FF4},
    {0x16EEE90,0xA9BF7BFD},
    {0x1793420,0xD10343FF}, {0x1792840,0xD107C3FF},
    {0x1792380,0xF81C0FF7}, // social
    {0x173C7F0,0xD10603FF}, {0x173DD40,0xD10303FF}, // map
    {0x1782900,0x6DB63BEF} // shop
};
inline constexpr unsigned UiHookCount=sizeof(UiHookSignatures)/sizeof(UiHookSignatures[0]);
static_assert(UiHookCount==18);
template<class ReadWord> constexpr bool MatchAllSignatures(ReadWord read) {
    if(!read(0x12340,0xF81E0FF3)) return false;
    for(const auto& s:UiHookSignatures) if(!read(s.offset,s.word)) return false;
    for(const auto& s:NpcMapSignatures::Entries)
        for(unsigned i=0;i<4;++i) if(!read(s.offset+4*i,s.words[i])) return false;
    return true;
}
bool Preflight();
}
