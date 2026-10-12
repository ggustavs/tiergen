# Run by build.py through the guest agent on the DC build, after provision.ps1: the address
# the scenario pins, AD DS, and a new forest. The reboot that completes it is build.py's.
# The transcript is C:\tiergen-build\promote.log.
param(
    [Parameter(Mandatory)] [string] $Address,
    [Parameter(Mandatory)] [int] $Prefix,
    [Parameter(Mandatory)] [string] $Domain,
    [Parameter(Mandatory)] [string] $NetBios,
    [Parameter(Mandatory)] [string] $Password
)
$ErrorActionPreference = 'Stop'
Start-Transcript -Path C:\tiergen-build\promote.log -Append

# The template's one NIC keeps this address in every run: the backend bootstraps agent
# hosts only, and a DC's address is in its own DNS zone.
$nic = Get-NetAdapter | Select-Object -First 1
Set-NetIPInterface -InterfaceIndex $nic.ifIndex -Dhcp Disabled
Get-NetIPAddress -InterfaceIndex $nic.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Remove-NetIPAddress -Confirm:$false
New-NetIPAddress -InterfaceIndex $nic.ifIndex -IPAddress $Address -PrefixLength $Prefix | Out-Null
Set-DnsClientServerAddress -InterfaceIndex $nic.ifIndex -ServerAddresses 127.0.0.1

Install-WindowsFeature AD-Domain-Services -IncludeManagementTools | Out-Null
Import-Module ADDSDeployment
$safe = ConvertTo-SecureString $Password -AsPlainText -Force
$result = Install-ADDSForest -DomainName $Domain -DomainNetbiosName $NetBios `
    -SafeModeAdministratorPassword $safe -InstallDns -Force -NoRebootOnCompletion
if ($result.Status -ne 'Success') { throw "Install-ADDSForest: $($result.Status) $($result.Message)" }
"forest $Domain created; a reboot completes it"
Stop-Transcript
