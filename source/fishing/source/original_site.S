/* SPDX-License-Identifier: GPL-2.0-only
 * Small preimage used ONLY for version/instruction verification.
 * Reassembled from the user's local package's BobberBar.update audit.
 */
.text
.global original_site
.type original_site, %function
original_site:
    ldrb w8, [x19, #0xbf]
    cbz w8, original_not_fade_in
    adrp x8, original_float_page
    ldr s0, [x19, #0xa0]
    ldr s1, [x8, #0x75c]
    fadd s0, s0, s1
    fmov s1, #1.0
    fcmp s0, s1
    str s0, [x19, #0xa0]
    b.mi original_exit_position
    mov w8, #0x3f800000
    str w8, [x19, #0xa0]
    strb wzr, [x19, #0xbf]
.size original_site, .-original_site
