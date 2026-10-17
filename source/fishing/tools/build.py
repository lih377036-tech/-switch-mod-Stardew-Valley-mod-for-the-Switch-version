"""Build the included ARM64 IPS32 source. SPDX-License-Identifier: GPL-2.0-only"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile
from patch_format import write_ips32

ROOT = Path(__file__).resolve().parents[1]
SITE = 0x167FBD4
TREASURE_SITE = 0x167FFE0
PATCH_RANGES = ((SITE, 52), (TREASURE_SITE, 4))
OUTPUT_NAME = "Stardew-Instant-Catch-Treasure-1.6.15.3-v0.2.0-candidate"
LEGACY_PATCH_SHA256 = "16a582c0f8bfd475c6f2ba59221d4610e05a723b5839e37e4433624d8cbe4723"
LEGACY_SKIP_HEX = "68ce40b969da40b91f01096be9179f1a0801094b68ce00b908f0a752682a01b92800805268a201397ffe02397f0e033914000014"
BID = "A5C617C14A7F3F6620B3BC8136965A4822D32B9C" + "00" * 12

def run(args: list[str]) -> str:
    p = subprocess.run(args, check=True, capture_output=True, text=True)
    if p.stderr:
        print(p.stderr.strip())
    return p.stdout

def build(llvm: Path) -> dict:
    work = ROOT / "work" / "build"
    work.mkdir(parents=True, exist_ok=True)
    bindir = llvm / "bin"
    clang = str(bindir / "clang-23.exe")
    lld = str(bindir / "ld.lld.exe")
    objcopy = str(bindir / "llvm-objcopy.exe")
    objdump = str(bindir / "llvm-objdump.exe")
    for name, (address, symbols) in {
        "skip_minigame": (SITE, {"vanilla_settlement": 0x167FC54}),
        "original_site": (SITE, {"original_not_fade_in": 0x167FC1C,
                          "original_float_page": 0xAC77000,
                          "original_exit_position": 0x167FC08}),
        "treasure_argument": (TREASURE_SITE, {}),
        "original_treasure_argument": (TREASURE_SITE, {}),
    }.items():
        obj, elf, binary = (work / f"{name}.{suffix}" for suffix in ("o", "elf", "bin"))
        run([clang, "--target=aarch64-none-elf", "-march=armv8-a", "-c",
             str(ROOT / "source" / f"{name}.S"), "-o", str(obj)])
        run([lld, "-m", "aarch64elf", f"-Ttext={address:#x}", f"--entry={name}",
             *[f"--defsym={key}={value:#x}" for key, value in symbols.items()],
             str(obj), "-o", str(elf)])
        run([objcopy, "-O", "binary", "--only-section=.text", str(elf), str(binary)])
        (work / f"{name}.disassembly.txt").write_text(
            run([objdump, "-d", str(elf)]), encoding="utf-8")
    patch_bytes = (work / "skip_minigame.bin").read_bytes()
    original = (work / "original_site.bin").read_bytes()
    if len(patch_bytes) != 52 or len(original) != 52:
        raise ValueError("Patch must exactly fill 13 original instructions")
    treasure_bytes = (work / "treasure_argument.bin").read_bytes()
    treasure_original = (work / "original_treasure_argument.bin").read_bytes()
    if len(treasure_bytes) != 4 or len(treasure_original) != 4:
        raise ValueError("Treasure argument must replace exactly one instruction")
    if patch_bytes.hex() != LEGACY_SKIP_HEX:
        raise ValueError("The user-tested skip-minigame code must remain unchanged")
    out = ROOT / "outputs" / OUTPUT_NAME
    patch_dir = out / "atmosphere" / "exefs_patches" / "StardewInstantCatch"
    patch_dir.mkdir(parents=True, exist_ok=True)
    patch = write_ips32([(SITE + 0x100, patch_bytes), (TREASURE_SITE + 0x100, treasure_bytes)])
    relative = f"atmosphere/exefs_patches/StardewInstantCatch/{BID}.ips"
    (out / relative).write_bytes(patch)
    manifest = {
        "name": "Stardew Instant Catch + Natural Treasure", "version": "0.2.0-treasure-candidate",
        "status": "rebuild_not_hardware_tested", "game_version": "1.6.15.3",
        "title_id": "0100E65002BB8000", "main_build_id": BID,
        "patch_format": "IPS32", "patch_relative_path": relative,
        "memory_offset": SITE, "ips_offset": SITE + 0x100,
        "size": len(patch_bytes) + len(treasure_bytes), "file_size": len(patch),
        "patch_sha256": hashlib.sha256(patch).hexdigest(),
        "original_site_hex": original.hex(), "replacement_hex": patch_bytes.hex(),
        "records": [
            {"name": "skip_minigame", "memory_offset": SITE, "ips_offset": SITE+0x100,
             "size": len(patch_bytes), "original_hex": original.hex(), "replacement_hex": patch_bytes.hex()},
            {"name": "treasure_argument", "memory_offset": TREASURE_SITE, "ips_offset": TREASURE_SITE+0x100,
             "size": len(treasure_bytes), "original_hex": treasure_original.hex(), "replacement_hex": treasure_bytes.hex()},
        ],
        "baseline": {"version": "0.1.0-candidate", "patch_sha256": LEGACY_PATCH_SHA256,
                     "skip_code_unchanged": True, "hardware_feedback": "user_reported_running",
                     "user_feedback_date": "2026-10-16",
                     "user_feedback": "Original skip-minigame patch reported working",
                     "upgrade_hardware_tested": False},
        "settlement_target": 0x167FC54,
        "scope": {"manual_cast": True, "normal_bite_wait": True,
                  "manual_hook": True, "skip_bobber_minigame": True,
                  "force_perfect": False, "force_quality": False,
                  "auto_treasure": True, "auto_cast": False,
                  "treasure_probability": "vanilla", "treasure_generation_changed": False,
                  "treasure_loot_ui": "vanilla", "auto_transfer_loot": False},
        "evidence": {"kind": "local package disassembly plus public source",
            "package": "fast-animations-singleplayer-merged-v13-1-1.zip",
            "asm_entry": "audit/fastanimations-bobber-update.asm",
            "asm_sha256": (hashlib.sha256((ROOT / "work" / "bobber-update-reference.asm").read_bytes()).hexdigest() if (ROOT / "work" / "bobber-update-reference.asm").exists() else None),
            "actual_console_main_verified": False},
        "validation": {"arm64_assembly": "passed", "hardware": "not_run"},
        "compiler": run([clang, "--version"]).splitlines()[0],
    }
    (out / "BUILD_INFO.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(out), "patch_bytes": len(patch), "sha256": manifest["patch_sha256"]}, indent=2))
    return manifest

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--llvm", type=Path, required=True)
    parser.add_argument("--reference-package", type=Path,
                        help="User-supplied audit ZIP; only reads one named ASM entry")
    args = parser.parse_args()
    if args.reference_package:
        with zipfile.ZipFile(args.reference_package) as archive:
            (ROOT / "work").mkdir(exist_ok=True)
            (ROOT / "work" / "bobber-update-reference.asm").write_bytes(
                archive.read("audit/fastanimations-bobber-update.asm"))
    build(args.llvm)
