# Run by build.py through the guest agent after the join's reboot: the workstation is in
# the domain and its secure channel to the DC works. Exits 0 when both hold.
param([Parameter(Mandatory)] [string] $Domain, [int] $Seconds = 300)
$ErrorActionPreference = 'Stop'
$system = Get-CimInstance Win32_ComputerSystem
if (-not $system.PartOfDomain -or $system.Domain -ne $Domain) {
    throw "in $($system.Domain), not $Domain"
}
$deadline = (Get-Date).AddSeconds($Seconds)
while (-not (Test-ComputerSecureChannel -ErrorAction SilentlyContinue)) {
    if ((Get-Date) -gt $deadline) { throw 'no secure channel to the DC' }
    Start-Sleep -Seconds 5
}
"$($system.Name) in $Domain, secure channel up"
