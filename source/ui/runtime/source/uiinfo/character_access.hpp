#pragma once
#include "uiinfo/aot.hpp"
#include "uiinfo/character_safety.hpp"

namespace AutomateLite::UIInfo {
// This cache lives for ONE traversal. It stores mapped ranges, never NPC/map
// objects across callbacks. Query permission before dereferencing every chain.
class CharacterMemory {
    struct Region { std::uintptr_t begin{},end{}; };
    Region regions[8]{};
    unsigned next{};
public:
    bool Readable(std::uintptr_t address,std::uintptr_t bytes) {
        if(!address || !bytes || bytes>~std::uintptr_t{}-address)return false;
        const auto end=address+bytes;
        for(const auto& region:regions)
            if(address>=region.begin && end<=region.end)return true;
        MemoryInfo info{};u32 page{};
        if(R_FAILED(svcQueryMemory(&info,&page,address)) || info.type==MemType_Unmapped ||
           (info.perm&Perm_R)==0 || info.size>~std::uintptr_t{}-info.addr ||
           address<info.addr || end>info.addr+info.size)return false;
        regions[next]={info.addr,info.addr+info.size};next=(next+1)%8;
        return true;
    }
    template<class T> bool Read(std::uintptr_t address,T& value) {
        if(!Readable(address,sizeof(T)))return false;
        __builtin_memcpy(&value,reinterpret_cast<const void*>(address),sizeof(T));return true;
    }
};

class CharacterAccess {
    CharacterMemory memory;
    std::uintptr_t collectionType{};
    void* current{};
    unsigned remaining=4096;
    bool Npc(void* npc) {
        std::uintptr_t type{},methods{},slot{},function{};
        const auto object=reinterpret_cast<std::uintptr_t>(npc);
        if(!CharacterSafety::ObjectType(memory,object,type) || !memory.Read(type+8,methods) ||
           !CharacterSafety::Field(methods,0x110,slot) || !memory.Readable(slot,16) ||
           !memory.Read(slot,function))return false;
        const auto& text=exl::util::GetMainModuleInfo().m_Text;
        return text.m_Size>=4 && function>=text.m_Start && function-text.m_Start<=text.m_Size-4;
    }
public:
    bool Initialize() {
        current=Game::GameState::GetCurrentLocation();
        CharacterSafety::Collection trusted;
        if(!CharacterSafety::Characters(memory,reinterpret_cast<std::uintptr_t>(current),0,trusted))return false;
        collectionType=trusted.type;return true;
    }
    void* Current() const {return current;}
    bool Budget() const {return remaining!=0;}
    void* LocationAt(const Game::LocationCollectionView& view,unsigned index) {
        if(!view.readable)return nullptr;
        return reinterpret_cast<void*>(CharacterSafety::LocationAt(memory,
            reinterpret_cast<std::uintptr_t>(view.locations),view.count,index));
    }
    template<class Visitor> bool Location(void* place,Visitor visitor) {
        if(!collectionType || !remaining)return false;
        --remaining;
        CharacterSafety::Collection collection;
        if(!CharacterSafety::Characters(memory,reinterpret_cast<std::uintptr_t>(place),collectionType,collection))return false;
        void* object=reinterpret_cast<void*>(collection.object);
        const int count=Aot::Call<int>(0x5125A0C,object);
        if(!CharacterSafety::ValidCount(count))return false;
        for(int i=0;i<count && remaining;++i) {
            --remaining;
            void* npc=Aot::Call<void*>(0x5125A20,object,i);
            if(Npc(npc))visitor(npc);
        }
        return true;
    }
};

template<class Visitor> void VisitLoadedNpcs(Visitor visitor) {
    CharacterAccess access;
    if(!access.Initialize())return;
    const auto locations=Game::GameState::GetLoadedLocations();
    if(locations.readable && locations.count<=CharacterSafety::MaximumLocations)
    for(unsigned i=0;i<locations.count && access.Budget();++i) {
        void* place=access.LocationAt(locations,i);
        // Never call the game's interior getter on a rejected root candidate.
        if(!access.Location(place,visitor))continue;
        const auto interiors=Game::GameState::GetInstancedBuildingInteriors(place);
        if(interiors.readable && interiors.count<=CharacterSafety::MaximumLocations)
        for(unsigned j=0;j<interiors.count && access.Budget();++j)
            access.Location(access.LocationAt(interiors,j),visitor);
    }
    access.Location(access.Current(),visitor);
}
}
