"""Check generated IPS and execute the patched original ARM64 settlement flow.

Requires Unicorn/Capstone and the user's original disassembly package.
This is NOT execution of the whole game or a Switch hardware test.
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import struct
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from patch_format import parse_ips, write_ips32
from reassemble_reference import assemble_reference, BASE
from build import SITE, TREASURE_SITE, BID, OUTPUT_NAME, LEGACY_PATCH_SHA256

def validate(llvm: Path, reference: Path) -> dict:
    from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE, UC_PROT_ALL
    from unicorn.arm64_const import UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2, UC_ARM64_REG_X3, UC_ARM64_REG_X4, UC_ARM64_REG_X5, UC_ARM64_REG_X6, UC_ARM64_REG_X7, UC_ARM64_REG_X19, UC_ARM64_REG_SP, UC_ARM64_REG_LR, UC_ARM64_REG_PC, UC_ARM64_REG_D0
    from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

    out = ROOT / "outputs" / OUTPUT_NAME
    manifest = json.loads((out / "BUILD_INFO.json").read_text(encoding="utf-8"))
    patch_file = out / manifest["patch_relative_path"]
    patch = patch_file.read_bytes()
    assert hashlib.sha256(patch).hexdigest() == manifest["patch_sha256"]
    assert patch_file.stem == BID and len(BID) == 64
    records = parse_ips(patch)
    assert len(records) == 2 and records[0][0] == SITE + 0x100
    assert records[1][0] == TREASURE_SITE + 0x100 and len(records[1][1]) == 4
    assert hashlib.sha256(write_ips32(records[:1])).hexdigest() == LEGACY_PATCH_SHA256
    replacement = records[0][1]
    assert len(replacement) == 52
    asm = ROOT / "work" / "bobber-update-reference.asm"
    with zipfile.ZipFile(reference) as archive:
        data = archive.read("audit/fastanimations-bobber-update.asm")
        assert hashlib.sha256(data).hexdigest() == manifest["evidence"]["asm_sha256"]
        asm.write_bytes(data)
    code = assemble_reference(asm, llvm, ROOT / "work" / "validation")
    assert code[SITE - BASE:SITE - BASE + 52] == bytes.fromhex(manifest["original_site_hex"])
    assert struct.unpack_from("<4I", code) == (0xD103C3FF,0x6D063BEF,0xF90053F9,0x6D0733ED)
    legacy = bytearray(code)
    legacy[SITE - BASE:SITE - BASE + 52] = replacement
    patched = bytearray(legacy)
    patched[TREASURE_SITE-BASE:TREASURE_SITE-BASE+4] = records[1][1]
    for record in manifest["records"]:
        offset,size=record["memory_offset"]-BASE,record["size"]
        assert code[offset:offset+size].hex() == record["original_hex"]
    decoded = list(Cs(CS_ARCH_ARM64, CS_MODE_ARM).disasm(replacement, SITE))
    assert len(decoded) == 13 and decoded[-1].mnemonic == "b"
    assert int(decoded[-1].op_str.lstrip("#"), 16) == 0x167FC54
    extra_instruction=list(Cs(CS_ARCH_ARM64,CS_MODE_ARM).disasm(records[1][1],TREASURE_SITE))
    assert len(extra_instruction)==1 and extra_instruction[0].mnemonic=="ldrb"
    assert extra_instruction[0].op_str=="w5, [x19, #0xc1]"
    allowed_code=set(range(SITE-BASE,SITE-BASE+52))|set(range(TREASURE_SITE-BASE,TREASURE_SITE-BASE+4))
    assert all(patched[i]==code[i] for i in range(len(code)) if i not in allowed_code)
    assert all(patched[i]==legacy[i] for i in range(len(code)) if i not in range(TREASURE_SITE-BASE,TREASURE_SITE-BASE+4))

    count = 0
    baseline_trace = None
    # Full ordinary-success path with synthetic game objects and external APIs.
    # Includes base quality, legend flag, double-catch bait and Challenge Bait counts.
    for quality, size, maximum, boss, double_bait, luck_roll, requested_count, treasure_present, golden, already_caught, variant in itertools.product(
        [0,1,2,4], [10,25], [25], [False,True], [False,True], [0.1,0.9], [0,1,3],
        [False,True], [False,True], [False,True], ["baseline","upgrade"]):
        mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
        mapped = set()
        def page(address):
            base = address & ~0xfff
            if base not in mapped:
                mu.mem_map(base, 0x1000, UC_PROT_ALL)
                mapped.add(base)
        def write(address, value):
            for addr in range(address & ~0xfff, (address+len(value)+0xfff)&~0xfff, 0x1000):
                page(addr)
            mu.mem_write(address, value)
        def ptr(address, value):
            write(address, struct.pack("<Q", value))
        def integer(address, value):
            write(address, struct.pack("<I", value & 0xffffffff))
        def byte(address, value):
            write(address, bytes([value]))
        menu, rod, player, stack, done = 0x20000000,0x20100000,0x20200000,0x30000000,0x40001000
        for addr in (rod, player, stack, stack+0x1000, done): page(addr)
        write(BASE, bytes(legacy if variant=="baseline" else patched))
        # Root metadata and virtual Reposition used by the untouched prologue.
        ptr(0xDECB730,0x21000000); integer(0x21000000,0)
        ptr(menu,0x21001000); ptr(0x21001008,0x21002000)
        ptr(0x210022B0,0x40000000); byte(0x210022B8,0)
        ptr(0xDF0F900,0x21003000); byte(0x21003000,1)
        ptr(0xDF0F908,0x21004000); ptr(0x21004000,0x21005000)
        # Double-catch bait constant, RNG object and rich-presence key.
        ptr(0xDFCE270,0x21006000); ptr(0x21006000,0x21007000)
        ptr(0xDFEF188,0x21008000); ptr(0x21008000,0x21009000)
        ptr(0x21009000,0x2100A000); ptr(0x2100A008,0x2100B000)
        ptr(0x2100B080,0x40000010); byte(0x2100B088,0)
        ptr(0xDFDC370,0x2100C000); ptr(0x2100C000,0x2100D000)
        # Threshold and position cap constants loaded by retained vanilla code.
        write(0xAC772DC,struct.pack("<f",0.9))
        write(0xAC780FC,struct.pack("<f",548.0))
        write(menu+0xA4,struct.pack("<f",0.0)); ptr(menu+0x118,0)
        byte(menu+0xBF,1); byte(menu+0xC0,0); byte(menu+0xC1,int(treasure_present))
        byte(menu+0xC2,int(already_caught)); byte(menu+0xC3,1); byte(menu+0xC4,int(boss))
        byte(menu+0xC5,int(golden)); byte(menu+0xC6,0)
        integer(menu+0xCC,size); integer(menu+0xD0,quality); integer(menu+0xD8,maximum)
        integer(menu+0xE0,requested_count)
        write(menu+0x6C,struct.pack("<f",80.0))
        ptr(menu+0x78,0x2100E000); ptr(menu+0x88,0x2100F000)
        write(menu+0x90,struct.pack("<f",200.0))
        before = bytes(mu.mem_read(menu,0x140))
        calls = []
        rng_calls = []
        reg = [UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X2,UC_ARM64_REG_X3,UC_ARM64_REG_X4,UC_ARM64_REG_X5,UC_ARM64_REG_X6,UC_ARM64_REG_X7]
        apis = {0x139C170:player, 0x1318EC0:rod, 0xAF0:rod,
                0x1A984D0:0x21100000 if double_bait else 0,
                0x150EAE0:0x21101000, 0x3878F0:int(double_bait),
                0x139C3C0:0x21102000,0x1425C80:0x21103000,
                0x139EF00:0,0x13B25D0:0,0x1A98520:0,
                0x40000000:0,0x40000010:0,0x1318710:0}
        for addr in apis: page(addr)
        def hook(emu, address, length, userdata):
            if address == done:
                emu.emu_stop(); return
            if address not in apis:
                return
            if address == 0x1A98520:
                sp = emu.reg_read(UC_ARM64_REG_SP)
                calls.append(("pull",[emu.reg_read(r) for r in reg],bytes(emu.mem_read(sp,0x14))))
            if address == 0x13B25D0: calls.append(("exit",))
            if address == 0x40000010:
                rng_calls.append(luck_roll)
                emu.reg_write(UC_ARM64_REG_D0,struct.unpack("<Q",struct.pack("<d",luck_roll))[0])
            elif address == 0x1318710:
                emu.reg_write(UC_ARM64_REG_D0,0)
            else: emu.reg_write(UC_ARM64_REG_X0,apis[address])
            emu.reg_write(UC_ARM64_REG_PC,emu.reg_read(UC_ARM64_REG_LR))
        mu.hook_add(UC_HOOK_CODE,hook)
        mu.reg_write(UC_ARM64_REG_X0,menu); mu.reg_write(UC_ARM64_REG_X1,0x22200000)
        mu.reg_write(UC_ARM64_REG_SP,stack+0x1800); mu.reg_write(UC_ARM64_REG_LR,done)
        mu.emu_start(BASE,done,count=1500)
        assert mu.reg_read(UC_ARM64_REG_PC) == done, "Failed to return from vanilla update"
        assert [item[0] for item in calls] == ["pull","exit"]
        args, extra = calls[0][1:]
        # Vanilla's csel at 0x167FFD4 uses its explicit positive count first;
        # only a value below one falls back to the double-catch bait roll.
        expected_count = requested_count if requested_count >= 1 else (2 if double_bait and not boss and luck_roll < .25 else 1)
        expected_treasure = int(already_caught if variant=="baseline" else treasure_present)
        assert args == [rod,0x2100E000,size-int(size==maximum),quality,80,expected_treasure,0,0], args
        assert struct.unpack_from("<Q",extra,0)[0] == 0x2100F000
        assert extra[8] == int(boss) and struct.unpack_from("<I",extra,16)[0] == expected_count, (quality,size,boss,double_bait,luck_roll,requested_count,expected_count,extra.hex())
        after = bytes(mu.mem_read(menu,0x140))
        allowed = set([0x68,0xBF,0xC0,0xC3]) | set(range(0xA0,0xA4)) | set(range(0xCC,0xD0)) | set(range(0x128,0x12C))
        assert all(before[i] == after[i] for i in range(len(before)) if i not in allowed)
        assert after[0x68] == 1 and after[0xBF] == 0 and after[0xC0] == 0 and after[0xC3] == 0
        assert struct.unpack_from("<f",after,0xA0)[0] == 0.0
        assert after[0xC1]==int(treasure_present) and after[0xC5]==int(golden)
        assert rng_calls == ([luck_roll] if double_bait and not boss else [])
        if variant=="baseline":
            baseline_trace = (calls,after,rng_calls)
        else:
            baseline_calls,baseline_after,baseline_rng = baseline_trace
            baseline_calls[0][1][5] = int(treasure_present)
            assert calls==baseline_calls and after==baseline_after and rng_calls==baseline_rng
        count += 1
    report = {
        "passed":True,"cases":count,"upgrade_cases":count//2,"baseline_comparison_cases":count//2,"arm64_assembly":"passed",
        "ips32_roundtrip":"passed","nso_header_offset":"0x100",
        "record_memory_ranges":[[hex(SITE),hex(SITE+52)],[hex(TREASURE_SITE),hex(TREASURE_SITE+4)]],
        "vanilla_settlement":"one pullFishFromWater and one exitActiveMenu per case",
        "cases_cover":"quality 0/1/2/4; max/nonmax size; boss/nonboss; double bait/no bait; RNG 0.1/0.9; requested counts 0/1/3; treasure absent/present; golden flag 0/1; old caught flag 0/1; baseline versus upgrade",
        "treasure_argument":"true exactly when vanilla treasure-present flag is true, including before treasure appears on screen",
        "unchanged":"fish ID, quality, generated treasure/golden flags, catch count, RNG call sequence and object memory compared with baseline",
        "golden_treasure_test_scope":"golden flag preservation only; actual golden chest loot generation and UI not executed",
        "baseline_hardware":"user_reported_running_2026-10-16",
        "hardware":"not_run","actual_console_main_verified":False,
        "limitations":"Original ARM64 function reconstructed from supplied audit; synthetic objects and mocked external game APIs; no game, graphics, audio, inventory, consumables or save-file integration test. Multiplayer/festivals not tested.",
    }
    (ROOT / "work" / "validation" / "VALIDATION.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return report

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--llvm",type=Path,required=True)
    p.add_argument("--reference-package",type=Path,required=True)
    args = p.parse_args()
    validate(args.llvm,args.reference_package)
