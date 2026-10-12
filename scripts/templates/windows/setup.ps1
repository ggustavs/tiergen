# At first logon: the virtio drivers and the QEMU guest agent from the virtio-win CD. Once
# the agent answers, build.py drives the rest through it (provision.ps1).
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force C:\tiergen-build | Out-Null
Start-Transcript -Path C:\tiergen-build\setup.log -Append
$virtio = (Get-Volume | Where-Object FileSystemLabel -like 'virtio-win*').DriveLetter
if (-not $virtio) { throw 'the virtio-win CD is not attached' }
foreach ($msi in "${virtio}:\virtio-win-gt-x64.msi", "${virtio}:\guest-agent\qemu-ga-x86_64.msi") {
    $p = Start-Process msiexec.exe -ArgumentList "/i `"$msi`" /qn /norestart" -Wait -PassThru
    # 3010: installed, a restart completes it.
    if ($p.ExitCode -notin 0, 3010) { throw "$msi exited $($p.ExitCode)" }
    "$msi installed ($($p.ExitCode))"
}
Get-Service QEMU-GA
Stop-Transcript
