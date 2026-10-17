"""Reassemble a user-supplied disassembly for isolated ARM64 tests.

The original game instructions stay in work/ and are not redistributed.
"""
from pathlib import Path
import re
from build import run

BASE, END = 0x167FA90, 0x16817E0

def assemble_reference(path: Path, llvm: Path, work: Path) -> bytes:
    entries = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        match = re.fullmatch(r"(0x[0-9a-f]+)\s+(.+?)\s*", line)
        if match:
            entries.append((int(match[1], 16), match[2]))
    if [addr for addr, _ in entries] != list(range(BASE, END, 4)):
        raise ValueError("Reference must cover the complete known function")
    addresses = {addr for addr, _ in entries}
    external = {}
    lines = [".text", ".global original_update", "original_update:"]
    for addr, instruction in entries:
        mnemonic = instruction.split()[0]
        if mnemonic in {"b", "bl", "cbz", "cbnz", "tbz", "tbnz", "adr", "adrp"} or mnemonic.startswith("b."):
            target = re.search(r"#(0x[0-9a-f]+)$", instruction)
            if not target:
                raise ValueError(f"Unrecognized relocation: {instruction}")
            value = int(target[1], 16)
            name = f"ref_{value:x}"
            if value not in addresses or mnemonic == "adrp":
                external[name] = value
            instruction = instruction[:target.start()] + name
        lines += [f"ref_{addr:x}:", "    " + instruction]
    work.mkdir(parents=True, exist_ok=True)
    source, obj, elf, binary = (work / f"reference.{suffix}" for suffix in ("S", "o", "elf", "bin"))
    source.write_text("\n".join(lines) + "\n", encoding="utf-8")
    run([str(llvm / "bin" / "clang-23.exe"), "--target=aarch64-none-elf", "-march=armv8-a+crc+crypto", "-c", str(source), "-o", str(obj)])
    run([str(llvm / "bin" / "ld.lld.exe"), "-m", "aarch64elf", f"-Ttext={BASE:#x}", "--entry=original_update",
         *[f"--defsym={name}={value:#x}" for name, value in external.items()], str(obj), "-o", str(elf)])
    run([str(llvm / "bin" / "llvm-objcopy.exe"), "-O", "binary", "--only-section=.text", str(elf), str(binary)])
    code = binary.read_bytes()
    if len(code) != END - BASE:
        raise ValueError("Unexpected reconstructed function size")
    return code
