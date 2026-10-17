/* SPDX-License-Identifier: GPL-2.0-only
 * Stardew Valley Switch 1.6.15.3, main A5C617C14A7F3F6620B3BC8136965A4822D32B9C.
 * Replaces only main+0x167FBD4..0x167FC08 (52 bytes).
 * Entered after vanilla's prologue, type initialization and menu housekeeping.
 * x19 is BobberBar. The existing settlement path preserves the game's ABI,
 * fish selection, bait-dependent catch count, pull animation and menu cleanup.
 */
.text
.global skip_minigame
.type skip_minigame, %function
skip_minigame:
    // Ordinary success applies vanilla's one-unit max-size adjustment.
    ldr w8, [x19, #0xcc]       // fishSize
    ldr w9, [x19, #0xd8]       // maxFishSize
    cmp w8, w9
    cset w9, eq
    sub w8, w8, w9
    str w8, [x19, #0xcc]

    mov w8, #0x3f800000
    str w8, [x19, #0x128]     // distanceFromCatching = 1.0f
    mov w8, #1
    strb w8, [x19, #0x68]     // handledFishResult, NOT fadeOut
    strb wzr, [x19, #0xbf]    // fadeIn = false
    strb wzr, [x19, #0xc3]    // ordinary catch, no forced Perfect bonus
    b vanilla_settlement     // main+0x167FC54; clears scale/fadeOut itself
.size skip_minigame, .-skip_minigame
