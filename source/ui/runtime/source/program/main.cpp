/* SPDX-License-Identifier: GPL-2.0-only
 * UI-only derivative of zmzhang2022-ai/Switch-StardewValley-Mod.
 * Switch integration 2026-10-16. No gameplay modifiers are installed.
 */
#include "lib.hpp"
#include "uiinfo/ui_info_suite.hpp"
#include "uiinfo/preflight.hpp"

extern "C" void exl_main(void*, void*) {
    // Framework discovery has completed before this module entry runs.
    // Check every UI hook before installing any of them.
    if (!AutomateLite::UIInfo::Preflight()) {
        Logging.Log("[UIInfoSuite2] Version/signature check failed; no UI hooks installed");
        return;
    }
    exl::hook::Initialize();
    AutomateLite::UIInfo::Install();
    Logging.Log("[UIInfoSuite2] Switch UI-only 0.1.5 guarded birthday/NPC traversal for 1.6.15.3");
}
extern "C" NORETURN void exl_exception_entry() {
    EXL_ABORT("UI Info Suite 2 exception handler called");
}
