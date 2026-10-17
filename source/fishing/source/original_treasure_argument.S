/* SPDX-License-Identifier: GPL-2.0-only
 * Original instruction used solely for version/preimage verification.
 */
.text
.global original_treasure_argument
.type original_treasure_argument, %function
original_treasure_argument:
    ldrb w5, [x19, #0xc2]
.size original_treasure_argument, .-original_treasure_argument
