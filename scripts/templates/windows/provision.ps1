# Run by build.py through the guest agent, as SYSTEM, from the build CD: Python, the agent's
# third-party wheels and Sysmon, all from the CD, so the build needs no network. Fails on the
# first error; the transcript is C:\tiergen-build\provision.log.
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force C:\tiergen-build | Out-Null
Start-Transcript -Path C:\tiergen-build\provision.log -Append
$cd = (Get-Volume -FileSystemLabel TGBUILD).DriveLetter + ':'
$python = 'C:\Python312\python.exe'

$p = Start-Process "$cd\python-installer.exe" -Wait -PassThru -ArgumentList @(
    '/quiet', 'InstallAllUsers=1', 'PrependPath=1', 'Include_test=0', 'Include_doc=0',
    'Include_launcher=0', 'Shortcuts=0', 'TargetDir=C:\Python312')
if ($p.ExitCode -ne 0) { throw "the Python installer exited $($p.ExitCode)" }
& $python -m pip install --no-index --find-links "$cd\wheels" -r "$cd\wheels\requirements.txt"
if ($LASTEXITCODE -ne 0) { throw "pip exited $LASTEXITCODE" }

Expand-Archive -Path "$cd\Sysmon.zip" -DestinationPath C:\Tools\Sysmon -Force
& C:\Tools\Sysmon\Sysmon64.exe -accepteula -i "$cd\sysmon.xml"
if ($LASTEXITCODE -ne 0) { throw "Sysmon exited $LASTEXITCODE" }

# A clone must boot cold: hibernation and fast startup would resume the build's session.
powercfg /hibernate off
# The first logon's password must not stay in the registry.
Remove-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon' `
    -Name DefaultPassword -ErrorAction SilentlyContinue

& $python -c "import sys, httpx; print('python', sys.version.split()[0], 'httpx', httpx.__version__)"
if ($LASTEXITCODE -ne 0) { throw 'Python cannot import httpx' }
Get-Service Sysmon64, QEMU-GA | ForEach-Object { "$($_.Name) $($_.Status)" }
Stop-Transcript
