# Run by build.py through the guest agent on the workstation clone of a join: an address on
# the DC's network, the DC as name server, and the join. The reboot that completes it is
# build.py's. The transcript is C:\tiergen-build\join.log.
param(
    [Parameter(Mandatory)] [string] $Address,
    [Parameter(Mandatory)] [int] $Prefix,
    [Parameter(Mandatory)] [string] $Dns,
    [Parameter(Mandatory)] [string] $Domain,
    [Parameter(Mandatory)] [string] $User,
    [Parameter(Mandatory)] [string] $Password
)
$ErrorActionPreference = 'Stop'
Start-Transcript -Path C:\tiergen-build\join.log -Append
$nic = Get-NetAdapter | Select-Object -First 1
Set-NetIPInterface -InterfaceIndex $nic.ifIndex -Dhcp Disabled
Get-NetIPAddress -InterfaceIndex $nic.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Remove-NetIPAddress -Confirm:$false
New-NetIPAddress -InterfaceIndex $nic.ifIndex -IPAddress $Address -PrefixLength $Prefix | Out-Null
Set-DnsClientServerAddress -InterfaceIndex $nic.ifIndex -ServerAddresses $Dns
$deadline = (Get-Date).AddSeconds(120)
while ($true) {
    try { Resolve-DnsName "_ldap._tcp.dc._msdcs.$Domain" -Type SRV -DnsOnly | Out-Null; break }
    catch { if ((Get-Date) -gt $deadline) { throw "no DC for $Domain through $Dns" } }
    Start-Sleep -Seconds 2
}
$credential = New-Object System.Management.Automation.PSCredential(
    "$User@$Domain", (ConvertTo-SecureString $Password -AsPlainText -Force))
Add-Computer -DomainName $Domain -Credential $credential -Force
"joined $Domain; a reboot completes it"
Stop-Transcript
