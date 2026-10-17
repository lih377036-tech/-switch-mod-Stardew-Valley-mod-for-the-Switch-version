#pragma once
#include "uiinfo/character_access.hpp"
namespace AutomateLite::UIInfo {
// Only callback-local managed references. Includes instantiated interiors;
// does not create maps or characters merely to display information.
template <typename Visitor> void VisitVillagers(Visitor visitor) {
    using namespace Aot;
    void* visited[512]{}; unsigned used{};
    VisitLoadedNpcs([&](void* npc) {
            if(used>=512 || !Virtual<bool>(npc,0x110))return;
            bool duplicate=false;
            for(unsigned j=0;j<used;++j) if(visited[j]==npc) { duplicate=true; break; }
            if(duplicate)return;
            visited[used++]=npc; visitor(npc);
    });
}
}
