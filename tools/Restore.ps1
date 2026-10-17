# SPDX-License-Identifier: GPL-2.0-only
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$SdRoot,
    [Parameter(Mandatory=$true)][string]$BackupDirectory,
    [switch]$CheckOnly
)
. (Join-Path $PSScriptRoot 'Common.ps1')
$sd = Get-SdDirectory $SdRoot
$backup = Get-Directory $BackupDirectory
$record = Get-Content -LiteralPath (Join-Path $backup 'BACKUP.json') -Raw | ConvertFrom-Json
if ($record.schema -ne 1 -or @($record.entries).Count -lt 1 -or @($record.entries).Count -gt 3) { throw 'Invalid backup record.' }
$seen = @{}
foreach ($entry in $record.entries) {
    if ($entry.path -notin $script:AllowedFiles -or $seen.ContainsKey($entry.path)) { throw 'Unsafe backup entry.' }
    $seen[$entry.path] = $true
    $target = Get-ChildPath $sd $entry.path
    if (Test-Path -LiteralPath $target) {
        $actual = Get-Digest $target
        if ($actual -ne $entry.installed_sha256 -and (-not $entry.existed -or $actual -ne $entry.old_sha256)) {
            throw 'A target was changed after installation. Restore stopped to preserve that change.'
        }
    }
    if ($entry.existed) {
        if ($entry.backup_file -notmatch '^files/[0-2]\.bin$') { throw 'Unsafe backup file name.' }
        $saved = Get-ChildPath $backup $entry.backup_file
        if ((Get-Digest $saved) -ne $entry.old_sha256) { throw 'Backup integrity check failed.' }
    }
}
if ($CheckOnly) { Write-Output 'RESTORE_CHECK_PASSED: no files changed.'; return }
Restore-Entries $sd $backup $record.entries
Write-Output 'RESTORED_AND_VERIFIED. Game saves and mod settings were not changed.'
