"""Read-only checks for existing mods that may conflict with this candidate."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from build import BID, PATCH_RANGES
from patch_format import parse_ips

def check(root: Path) -> dict:
    root = root.resolve(strict=True)
    if not (root / "atmosphere").is_dir():
        raise ValueError("The selected folder is not a Switch Atmosphere SD root")
    conflicts, relevant = [], []
    game = root / "atmosphere" / "contents" / "0100E65002BB8000"
    for replacement in (game / "exefs.nsp", game / "exefs" / "main"):
        if replacement.exists(): conflicts.append(f"Executable replacement: {replacement}")
    if (game / "exefs").is_dir():
        for module in (game / "exefs").glob("subsdk*"):
            if module.is_file() and not module.name.endswith(".stub"):
                conflicts.append(f"Existing injected module needs review: {module}")
    patch_root = root / "atmosphere" / "exefs_patches"
    for folder in patch_root.iterdir() if patch_root.is_dir() else []:
        if not folder.is_dir(): continue
        for file in folder.glob("*.ips"):
            try:
                matches = file.stem.upper().ljust(64,"0") == BID
                if not matches: continue
                records = parse_ips(file.read_bytes())
                relevant.append(str(file))
                if folder.name == "StardewInstantCatch": continue
                if any(offset < address+0x100+size and address+0x100 < offset+len(blob)
                       for offset,blob in records for address,size in PATCH_RANGES):
                    conflicts.append(f"Overlapping IPS patch: {file}")
            except (OSError,ValueError) as error:
                conflicts.append(f"Patch could not be checked: {file}: {error}")
    return {"sd_root":str(root),"passed":not conflicts,"conflicts":conflicts,
            "patches_for_same_build":relevant,
            "build_id_verified":False,"changes_written":False}

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("sd_root",type=Path)
    args = p.parse_args()
    try: result = check(args.sd_root)
    except (OSError,ValueError) as error:
        print(f"SD check failed: {error}"); raise SystemExit(2)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result["passed"] else 2)
