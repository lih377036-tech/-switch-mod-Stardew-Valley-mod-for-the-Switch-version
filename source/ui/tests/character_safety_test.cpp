#include "uiinfo/character_safety.hpp"
#include <initializer_list>
using namespace AutomateLite::UIInfo;
namespace S=CharacterSafety;
namespace {
using Address=std::uintptr_t;
struct Memory {
    struct Cell {Address address{},value{};} cells[128]{};
    struct Region {Address address{},size{};} regions[96]{};
    unsigned count{},regionCount{},reads{},watchedReads{};
    Address watched{};
    constexpr void Map(Address address,Address size) {regions[regionCount++]={address,size};}
    constexpr void Put(Address address,Address value) {
        for(unsigned i=0;i<count;++i)if(cells[i].address==address){cells[i].value=value;return;}
        cells[count++]={address,value};
    }
    constexpr bool Readable(Address address,Address size) {
        if(!address || !size || size>~Address{}-address)return false;
        for(unsigned i=0;i<regionCount;++i)
            if(address>=regions[i].address && address+size<=regions[i].address+regions[i].size)return true;
        return false;
    }
    constexpr bool Read(Address address,Address& value) {
        ++reads;if(address==watched)++watchedReads;
        if(!Readable(address,8))return false;
        for(unsigned i=0;i<count;++i)if(cells[i].address==address){value=cells[i].value;return true;}
        return false;
    }
    constexpr void Object(Address address,Address type,Address methods,Address bytes=0x200) {
        Map(address,bytes);Map(type,16);Map(methods,0x200);
        Put(address,type);Put(type+8,methods);
    }
};
constexpr Address Current=0x6300001000,LocationType=0x5000001000,LocationMethods=0x5000002000;
constexpr Address Characters=0x6300101000,CharacterType=0x5000101000,CharacterMethods=0x5000102000;
constexpr Address Items=0x6300201000,ListType=0x5000201000,ListMethods=0x5000202000;
constexpr Memory ValidMemory() {
    Memory m;
    m.Object(Current,LocationType,LocationMethods);
    m.Object(Characters,CharacterType,CharacterMethods);
    m.Object(Items,ListType,ListMethods);
    m.Put(Current+0xB0,Characters);m.Put(Characters+0x48,Items);
    return m;
}
constexpr bool ReplayRecordedCrashes() {
    // Exact location register values and invalid collection from BOTH SD logs.
    for(Address place:{Address{0x63D70AA1C0},Address{0x6BA7A2F000}}) {
        auto m=ValidMemory();
        S::Collection trusted,result;
        if(!S::Characters(m,Current,0,trusted))return false;
        m.Object(place,LocationType,LocationMethods);
        constexpr Address bad=0x3F8CCCCD00000000;
        m.Put(place+0xB0,bad);m.watched=bad+0x48;
        // Old code attempts the exact address reported by Atmosphere.
        Address oldPointer{};
        if(!m.Read(place+0xB0,oldPointer) || oldPointer+0x48!=0x3F8CCCCD00000048 ||
           m.Readable(oldPointer+0x48,8))return false;
        if(S::Characters(m,place,trusted.type,result) || result.object || m.watchedReads)return false;
    }
    return true;
}
constexpr bool MappedWrongTypeIsNotAccepted() {
    auto m=ValidMemory();
    constexpr Address other=0x6300301000,otherType=0x5000301000,otherMethods=0x5000302000;
    m.Object(other,otherType,otherMethods);
    m.Put(other+0x48,Items);m.Put(Current+0xB0,other);
    m.watched=other+0x48;
    S::Collection result;
    return !S::Characters(m,Current,CharacterType,result) && !m.watchedReads && !result.object;
}
constexpr bool ValidDerivedLocationAndCollectionSurvive() {
    auto m=ValidMemory();
    constexpr Address inside=0x6300401000,insideType=0x5000401000,insideMethods=0x5000402000;
    constexpr Address otherCollection=0x6300501000;
    m.Object(inside,insideType,insideMethods);m.Object(otherCollection,CharacterType,CharacterMethods);
    m.Put(inside+0xB0,otherCollection);m.Put(otherCollection+0x48,Items);
    S::Collection result;
    return S::Characters(m,inside,CharacterType,result) && result.object==otherCollection &&
        result.type==CharacterType && result.items==Items;
}
constexpr bool InvalidHeadersAndBoundary() {
    auto m=ValidMemory();S::Collection result;
    if(S::Characters(m,0,CharacterType,result) || S::Characters(m,Current+1,CharacterType,result))return false;
    constexpr Address shortObject=0x6300601000;
    m.Object(shortObject,LocationType,LocationMethods,16);
    if(S::Characters(m,shortObject,CharacterType,result))return false;
    constexpr Address data=0x6300701000;
    m.Map(data,16);m.Put(data,Current);m.Put(data+8,shortObject);
    if(S::LocationAt(m,data,2,0)!=Current || S::LocationAt(m,data,2,1)!=shortObject)return false;
    const auto before=m.reads;
    if(S::LocationAt(m,data,0,0) || S::LocationAt(m,data,4097,0) ||
       S::LocationAt(m,data,2,2) || S::LocationAt(m,~Address{}-7,2,1) || m.reads!=before)return false;
    return S::ValidCount(0) && S::ValidCount(2048) && !S::ValidCount(-1) && !S::ValidCount(2049);
}
}
static_assert(ReplayRecordedCrashes());
static_assert(MappedWrongTypeIsNotAccepted());
static_assert(ValidDerivedLocationAndCollectionSurvive());
static_assert(InvalidHeadersAndBoundary());
