/* SPDX-License-Identifier: GPL-2.0-only */
#include "uiinfo/preflight.hpp"
#include "uiinfo/npc_map_signatures.hpp"
#include "lib.hpp"
namespace AutomateLite::UIInfo {
namespace {
bool Word(std::uintptr_t offset,std::uint32_t expected) {
    const auto& text=exl::util::GetMainModuleInfo().m_Text;
    if(offset>text.m_Size || text.m_Size-offset<4) return false;
    const auto actual=*reinterpret_cast<const std::uint32_t*>(text.m_Start+offset);
    if(actual!=expected) {
        Logging.Log("[UIInfoSuite2] main+0x%llX expected %08X, got %08X",
            static_cast<unsigned long long>(offset),expected,actual);
        return false;
    }
    return true;
}
}
bool Preflight() {
    if(!exl::util::HasModule(exl::util::ModuleIndex::Main)) return false;
    const auto& main=exl::util::GetMainModuleInfo();
    // UI helpers reference static storage in the exact-build main data/BSS.
    if(main.m_Total.m_Size<0xE27FB18) return false;
    // Check the additional ABI fingerprints before *any* hook is patched.
    // This is a multi-site fingerprint, not a claim to read NSO Build ID from RAM.
    if(!MatchAllSignatures(Word)) return false;
    Logging.Log("[UIInfoSuite2] Exact-version multi-site preflight passed; %u hooks",UiHookCount);
    return true;
}
}
