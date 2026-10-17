# SPDX-License-Identifier: GPL-2.0-only
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:PackageRoot = Split-Path -Parent $PSScriptRoot
$script:AllowedFiles = @(
    'atmosphere/contents/0100E65002BB8000/exefs/subsdk9',
    'atmosphere/contents/0100E65002BB8000/exefs/main.npdm',
    'atmosphere/exefs_patches/StardewInstantCatch/A5C617C14A7F3F6620B3BC8136965A4822D32B9C000000000000000000000000.ips'
)
function Get-Digest([string]$Path) {
    $stream = [IO.File]::OpenRead($Path)
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-','').ToLowerInvariant() }
    finally { $sha.Dispose(); $stream.Dispose() }
}
function Get-Directory([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    if (-not $item.PSIsContainer) { throw "Not a directory: $Path" }
    $full = [IO.Path]::GetFullPath($item.FullName)
    if ($full -eq [IO.Path]::GetPathRoot($full)) { return $full }
    return $full.TrimEnd([char[]]'\/')
}
function Get-ChildPath([string]$Root, [string]$Relative) {
    if ([IO.Path]::IsPathRooted($Relative) -or $Relative -match '(^|[\\/])\.\.([\\/]|$)|:') {
        throw "Unsafe relative path: $Relative"
    }
    $base = [IO.Path]::GetFullPath($Root).TrimEnd([char[]]'\/')
    $prefix = $base + [IO.Path]::DirectorySeparatorChar
    $child = [IO.Path]::GetFullPath((Join-Path $prefix $Relative))
    if (-not $child.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Path escapes its selected directory.'
    }
    $cursor = $child
    while ($cursor -and $cursor.Length -ge $base.Length) {
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Linked paths are not supported: $cursor"
            }
        }
        if ($cursor.TrimEnd([char[]]'\/') -eq $base) { break }
        $cursor = Split-Path -Parent $cursor
    }
    return $child
}
function Get-SdDirectory([string]$Path) {
    $root = Get-Directory $Path
    $null = Get-ChildPath $root 'atmosphere'
    if (-not (Test-Path -LiteralPath (Join-Path $root 'atmosphere') -PathType Container)) {
        throw 'Select the SD root containing an existing atmosphere directory.'
    }
    if ($root -match '^([A-Za-z]):') {
        if ($env:SystemDrive -and $Matches[1] -eq $env:SystemDrive.TrimEnd(':')) {
            throw 'The Windows system drive is not an SD installation target.'
        }
        # Reject system partitions, without binding to hardware or other data partitions.
        $letter = $root.Substring(0, 1)
        $partitions = @(Get-Partition -DriveLetter $letter -ErrorAction SilentlyContinue)
        foreach ($part in $partitions) {
            if ($part.IsBoot -or $part.IsSystem) { throw 'A boot/system volume is not an SD installation target.' }
        }
    }
    $prefix = $root.TrimEnd([char[]]'\/') + [IO.Path]::DirectorySeparatorChar
    if ($script:PackageRoot.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase) -or $root -eq $script:PackageRoot) {
        throw 'Extract this package on the computer before running the installer.'
    }
    return $root
}
function Read-Package {
    $manifest = Get-Content -LiteralPath (Join-Path $script:PackageRoot 'manifest.json') -Raw | ConvertFrom-Json
    if ($manifest.schema -ne 1 -or @($manifest.files).Count -ne 3) { throw 'Unsupported package manifest.' }
    $seen = @{}
    foreach ($entry in $manifest.files) {
        if ($entry.path -notin $script:AllowedFiles -or $seen.ContainsKey($entry.path)) { throw 'Unexpected payload path.' }
        $seen[$entry.path] = $true
        $path = Get-ChildPath $script:PackageRoot $entry.path
        if ((Get-Item -LiteralPath $path).Length -ne $entry.bytes -or (Get-Digest $path) -ne $entry.sha256) {
            throw "Package integrity check failed: $($entry.path)"
        }
    }
    return $manifest
}
function Save-Json($Value, [string]$Path) {
    $Value | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $Path -Encoding UTF8
}
function Restore-Entries([string]$SdRoot, [string]$BackupRoot, $Entries) {
    foreach ($entry in $Entries) {
        $target = Get-ChildPath $SdRoot $entry.path
        if ($entry.existed) {
            $saved = Get-ChildPath $BackupRoot $entry.backup_file
            if ((Get-Digest $saved) -ne $entry.old_sha256) { throw 'Backup integrity check failed.' }
            $null = New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target)
            Copy-Item -LiteralPath $saved -Destination $target -Force
            if ((Get-Digest $target) -ne $entry.old_sha256) { throw 'Restore readback failed.' }
        } elseif (Test-Path -LiteralPath $target) {
            Remove-Item -LiteralPath $target -Force
        }
    }
}
