# Stardew Valley Switch Portable Mods — 1.0.1-preview

For Switch Stardew Valley **1.6.15.3**, title `0100E65002BB8000`, main NSO Build ID:
`A5C617C14A7F3F6620B3BC8136965A4822D32B9C000000000000000000000000`.

Includes instant catch after manual casting/hooking, capture of naturally generated treasure with vanilla probability and loot UI, and UI Info Suite's native UI-only adaptation 0.1.5.
No SD, reader serial, drive-letter or console identity binding. The runtime files are unchanged from the component builds.

This is a **preview**: fishing and ordinary treasure were reported working on one Mariko console. The UI birthday-crash guard has local verification but no post-fix console test feedback. Other consoles, firmware/Atmosphere versions, multiplayer and long-term stability have not been validated.

With the game closed and console powered off, connect the SD to a computer. Extract this package onto the computer. On Windows, run from the package root, replacing `E:` with the actual SD drive:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Install.ps1 -SdRoot "E:\" -CheckOnly
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Install.ps1 -SdRoot "E:\"
```

The installer supports Windows PowerShell 5.1/7. It verifies payload hashes, refuses unknown executable/module/NPDM and same-build patch conflicts, backs up the selected overwritten files under `outputs/backups/`, verifies writes and attempts rollback on copy failure. It does not back up live game saves. `-Components Fishing` or `-Components UI` installs one component. `-BackupRoot` selects a computer backup directory outside the SD. An existing `atmosphere` directory is required.

Optional `-GameMain` checks the full Build ID in an exported raw NSO `main`; otherwise the game build is explicitly recorded as unverified. The installer cannot infer it from encrypted SD content.
For manual installation on any computer OS, check compatibility/back up existing files, then merge only the included `atmosphere/` directory into the SD root. Never overwrite another native mod blindly.

UI settings: open the in-game inventory/GameMenu, hold **ZL+ZR**, press **D-pad Up**. The visible hammer still has a known controller-navigation problem. R3 retains vanilla chat. Settings remain under `config/uiinfosuite2/` and are not overwritten.

Restore using `tools/Restore.ps1 -SdRoot "E:\" -BackupDirectory "actual backup directory"`, optionally with `-CheckOnly` first. To uninstall manually, restore prior matching files or remove files newly added by this package. Remove both UI files together; fishing/treasure is one independent IPS. Renaming only an IPS parent directory does not disable the patch.

See [README.md](README.md) for detailed Chinese instructions and limitations, [BUILDING.md](BUILDING.md) for corresponding source/build instructions, and [CREDITS.md](CREDITS.md) for upstream attribution.
GPL-2.0-only for this project, with original third-party notices retained. Redistribution should preserve complete source, licenses and preview status. No game, firmware, keys, personal saves, raw crash logs or device IDs are included. Do not upload generated backups.
