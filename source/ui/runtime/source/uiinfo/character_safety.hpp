#pragma once
#include <cstdint>

// Read-only traversal contract, independent of SDK calls so the real crash
// addresses and foreign-but-mapped objects can be replayed without a console.
namespace AutomateLite::UIInfo::CharacterSafety {
inline constexpr unsigned MaximumLocations=4096,MaximumCharacters=2048;
constexpr bool Pointer(std::uintptr_t p) { return p>=0x100000000ULL && (p&7)==0; }
constexpr bool Field(std::uintptr_t p,std::uintptr_t offset,std::uintptr_t& out) {
    if(!Pointer(p) || offset>~std::uintptr_t{}-p)return false;
    out=p+offset;return true;
}
template<class Memory> constexpr bool ObjectType(Memory& memory,std::uintptr_t object,std::uintptr_t& type) {
    type=0;
    std::uintptr_t at{},methods{};
    if(!Pointer(object) || !memory.Read(object,type) || !Field(type,8,at) ||
       !memory.Read(at,methods) || !Pointer(methods) || !memory.Readable(methods,16)) {
        type=0;return false;
    }
    return true;
}
struct Collection { std::uintptr_t object{},type{},items{}; };
template<class Memory> constexpr bool Characters(Memory& memory,std::uintptr_t location,
    std::uintptr_t expectedType,Collection& result) {
    result={};
    std::uintptr_t locationType{},at{},collection{},type{},items{},itemsType{};
    if(!ObjectType(memory,location,locationType) || !Field(location,0xB0,at) ||
       !memory.Read(at,collection) || !ObjectType(memory,collection,type))return false;
    // The token comes from Game1's CURRENT, authoritative GameLocation, not
    // from the heuristic interior decoder. A valid mapping alone is not type proof.
    if(expectedType && type!=expectedType)return false;
    if(!Field(collection,0x48,at) || !memory.Read(at,items) ||
       !ObjectType(memory,items,itemsType))return false;
    result={collection,type,items};return true;
}
template<class Memory> constexpr std::uintptr_t LocationAt(Memory& memory,
    std::uintptr_t data,unsigned count,unsigned index) {
    std::uintptr_t at{},location{};
    if(count>MaximumLocations || index>=count || !Field(data,static_cast<std::uintptr_t>(index)*8,at) ||
       !memory.Read(at,location))return 0;
    return location;
}
constexpr bool ValidCount(int count) { return count>=0 && count<=static_cast<int>(MaximumCharacters); }
}
