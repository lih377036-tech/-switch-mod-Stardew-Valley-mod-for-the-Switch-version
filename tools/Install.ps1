# SPDX-License-Identifier: GPL-2.0-only
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$SdRoot,
    [ValidateSet('All','Fishing','UI')][string]$Components = 'All',
    [string]$BackupRoot,
    [string]$GameMain,
    [switch]$CheckOnly
)
. (Join-Path $PSScriptRoot 'Common.ps1')
$manifest = Read-Package
$sd = Get-SdDirectory $SdRoot
$buildVerified = $false
if ($GameMain) {
    $stream = [IO.File]::OpenRead((Resolve-Path -LiteralPath $GameMain).ProviderPath)
    try {
        $header = New-Object byte[] 256
        if ($stream.Read($header, 0, 256) -ne 256 -or [Text.Encoding]::ASCII.GetString($header, 0, 4) -ne 'NSO0') {
            throw 'GameMain must be an exported, raw NSO main file.'
        }
        $bid = ([BitConverter]::ToString($header[64..95])).Replace('-','')
        if ($bid -ne $manifest.target.main_build_id) { throw "Unsupported game main Build ID: $bid" }
        $buildVerified = $true
    } finally { $stream.Dispose() }
}
$selected = @($manifest.files | Where-Object { $Components -eq 'All' -or $_.component -eq $Components })
$titleRoot = Get-ChildPath $sd 'atmosphere/contents/0100E65002BB8000'
if (Test-Path -LiteralPath (Get-ChildPath $sd 'atmosphere/contents/0100E65002BB8000/exefs.nsp')) {
    throw 'An exefs.nsp override exists. Check compatibility before installation.'
}
$exefs = Get-ChildPath $sd 'atmosphere/contents/0100E65002BB8000/exefs'
if (Test-Path -LiteralPath $exefs) {
    foreach ($item in Get-ChildItem -LiteralPath $exefs -Force) {
        $null = Get-ChildPath $sd ('atmosphere/contents/0100E65002BB8000/exefs/' + $item.Name)
        if ($item.Name -match '^(main|rtld|sdk)(\.stub)?$|^subsdk[0-9]+(\.stub)?$') {
            if ($item.PSIsContainer -or $item.Name -ne 'subsdk9' -or (Get-Digest $item.FullName) -notin $manifest.known_ui_hashes) {
                throw "Another executable override/module exists: $($item.Name)"
            }
        }
        if ($item.Name -eq 'main.npdm' -and (Get-Digest $item.FullName) -ne $manifest.npdm_sha256) {
            throw 'A different main.npdm exists; permissions must be reviewed before merging.'
        }
    }
}
$patchRoot = Get-ChildPath $sd 'atmosphere/exefs_patches'
$fishPath = @($manifest.files | Where-Object { $_.component -eq 'Fishing' })[0].path
if (Test-Path -LiteralPath $patchRoot) {
    # Reject links before recursively traversing patch directories.
    $queue = New-Object 'System.Collections.Generic.Queue[string]'
    $queue.Enqueue($patchRoot)
    while ($queue.Count -gt 0) {
        $folder = $queue.Dequeue()
        foreach ($item in Get-ChildItem -LiteralPath $folder -Force) {
            $relative = $item.FullName.Substring($sd.TrimEnd([char[]]'\/').Length + 1).Replace('\','/')
            $null = Get-ChildPath $sd $relative
            if ($item.PSIsContainer) { $queue.Enqueue($item.FullName); continue }
            if ($item.Extension -eq '.ips' -and $item.BaseName.TrimEnd('0') -eq $manifest.target.main_build_id.TrimEnd('0')) {
                if ($relative -ne $fishPath) { throw "Another patch targets this game build: $relative" }
                if ((Get-Digest $item.FullName) -notin $manifest.known_fishing_hashes) { throw 'Unknown existing fishing patch.' }
            }
        }
    }
}
$entries = @()
foreach ($entry in $selected) {
    $target = Get-ChildPath $sd $entry.path
    $exists = Test-Path -LiteralPath $target
    if ($exists -and -not (Test-Path -LiteralPath $target -PathType Leaf)) { throw 'A target is not a regular file.' }
    $oldHash = $null
    if ($exists) { $oldHash = Get-Digest $target }
    $entries += [pscustomobject]@{ path=$entry.path; backup_file=('files/' + $entries.Count + '.bin'); existed=$exists; old_sha256=$oldHash; installed_sha256=$entry.sha256 }
}
$preview = [ordered]@{
    schema=1; status='CHECK_ONLY'; components=$Components; sd_root=$sd;
    device_binding=$false; game_main_build_id_verified=$buildVerified;
    target=$manifest.target; entries=$entries; sd_written=$false
}
if (-not $buildVerified) {
    Write-Host 'Game Build ID was NOT read from the SD card. Use -GameMain to check an exported main.'
}
if ($CheckOnly) { $preview | ConvertTo-Json -Depth 12; return }
if (-not $BackupRoot) { $BackupRoot = Join-Path $script:PackageRoot 'outputs/backups' }
$backupBase = [IO.Path]::GetFullPath($BackupRoot).TrimEnd([char[]]'\/')
if ($backupBase -eq $sd.TrimEnd([char[]]'\/') -or $backupBase.StartsWith($sd.TrimEnd([char[]]'\/') + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Backups must be stored on the computer, outside the selected SD directory.'
}
$stamp = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,8)
$backup = Get-ChildPath $backupBase $stamp
$null = New-Item -ItemType Directory -Force -Path $backup
foreach ($entry in $entries) {
    if ($entry.existed) {
        $saved = Get-ChildPath $backup $entry.backup_file
        $null = New-Item -ItemType Directory -Force -Path (Split-Path -Parent $saved)
        Copy-Item -LiteralPath (Get-ChildPath $sd $entry.path) -Destination $saved
        if ((Get-Digest $saved) -ne $entry.old_sha256) { throw 'Backup readback failed; SD has not been changed.' }
    }
}
$record = [ordered]@{ schema=1; bundle_version=$manifest.bundle_version; original_sd_root=$sd; entries=$entries }
Save-Json $record (Join-Path $backup 'BACKUP.json')
try {
    foreach ($entry in $entries) {
        $source = Get-ChildPath $script:PackageRoot $entry.path
        $target = Get-ChildPath $sd $entry.path
        $null = New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target)
        Copy-Item -LiteralPath $source -Destination $target -Force
        if ((Get-Digest $target) -ne $entry.installed_sha256) { throw 'Installed file hash mismatch.' }
    }
    $preview.status = 'INSTALLED_AND_VERIFIED'
    $preview.sd_written = $true
    $preview['backup'] = $backup
    Save-Json $preview (Join-Path $backup 'INSTALL_REPORT.json')
} catch {
    $installFailure = $_
    Restore-Entries $sd $backup $entries
    throw "Installation failed; old files restored. Original error: $installFailure"
}
$preview | ConvertTo-Json -Depth 12
