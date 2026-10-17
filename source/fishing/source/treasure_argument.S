/* SPDX-License-Identifier: GPL-2.0-only
 * Stardew Valley Switch 1.6.15.3, exact main Build ID in BUILD_INFO.json.
 * Change only the treasure argument at main+0x167FFE0 (one instruction).
 * The original call reads treasureCaught (+0xC2). During instant catch the
 * minigame has not collected it, so forward vanilla's treasure-present flag
 * (+0xC1) instead. This does not write to either flag or reroll a chest.
 * Fish/quality/Perfect/count arguments and the original loot UI stay intact.
 */
.text
.global treasure_argument
.type treasure_argument, %function
treasure_argument:
    ldrb w5, [x19, #0xc1]
.size treasure_argument, .-treasure_argument
