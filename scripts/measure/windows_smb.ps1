# Run in the guest by windows_smb.py, as SYSTEM through the guest agent. Gives the NIC its
# address, records an ETW session over the providers that could tie an SMB connection to
# the process that asked for it while fresh processes use the share, and packs everything
# into C:\m\result.zip: the trace as XML, each action's process id and times, Sysmon's and
# the SMB client's own event channels.
param(
    [Parameter(Mandatory)] [string] $Mac,
    [Parameter(Mandatory)] [string] $Address,
    [Parameter(Mandatory)] [int] $Prefix,
    [Parameter(Mandatory)] [string] $Server,
    [Parameter(Mandatory)] [string] $User,
    [Parameter(Mandatory)] [string] $Password
)
$ErrorActionPreference = 'Stop'
$m = 'C:\m'
New-Item -ItemType Directory -Force $m | Out-Null
Start-Transcript -Path "$m\measure.log"

$nic = Get-NetAdapter | Where-Object { $_.MacAddress -eq ($Mac.ToUpper() -replace ':', '-') }
if (-not $nic) { throw "no adapter with MAC $Mac" }
New-NetIPAddress -InterfaceIndex $nic.ifIndex -IPAddress $Address -PrefixLength $Prefix | Out-Null
# A new address is tentative until duplicate detection is done, and a ping from it throws
# rather than failing; wait for it, then for the server.
$deadline = (Get-Date).AddSeconds(90)
while ((Get-NetIPAddress -IPAddress $Address).AddressState -ne 'Preferred') {
    if ((Get-Date) -gt $deadline) { throw "$Address stays $((Get-NetIPAddress -IPAddress $Address).AddressState)" }
    Start-Sleep 1
}
function Answers { try { Test-Connection -ComputerName $Server -Count 1 -Quiet } catch { $false } }
while (-not (Answers)) {
    if ((Get-Date) -gt $deadline) { throw "$Server does not answer" }
    Start-Sleep 2
}

$providers = @(
    @('Microsoft-Windows-SMBClient', '0xffffffffffffffff'),
    @('Microsoft-Windows-Kernel-Network', '0xffffffffffffffff'),
    @('Microsoft-Windows-Kernel-Process', '0x10'),   # process start and stop
    @('Microsoft-Windows-Kernel-File', '0x90'),      # file names and creates
    @('Microsoft-Windows-Security-Kerberos', '0xffffffffffffffff'),
    @('Microsoft-Windows-LSA', '0xffffffffffffffff')
)
$etl = "$m\trace.etl"
logman create trace tgm -ets -o $etl -bs 1024 -nb 16 128 -p $providers[0][0] $providers[0][1] 0xff
if ($LASTEXITCODE -ne 0) { throw "logman create exited $LASTEXITCODE" }
foreach ($p in $providers[1..($providers.Count - 1)]) {
    logman update trace tgm -ets -p $p[0] $p[1] 0xff
    "provider $($p[0]): logman exited $LASTEXITCODE"
}

$share = "\\$Server\share"
$actions = @(
    @('map', "net use $share /user:$User $Password"),
    @('list', "dir $share"),
    @('read', "type $share\hello.txt"),
    @('unmap', "net use $share /delete /y"),
    @('list-unmapped', "dir $share")
)
$ran = foreach ($a in $actions) {
    Start-Sleep -Seconds 3
    $start = [DateTime]::UtcNow.ToString('o')
    $p = Start-Process cmd.exe -ArgumentList "/c $($a[1]) > $m\$($a[0]).out 2>&1" `
        -PassThru -Wait -WindowStyle Hidden
    [pscustomobject]@{
        action = $a[0]; pid = $p.Id; exit = $p.ExitCode
        start = $start; end = [DateTime]::UtcNow.ToString('o')
    }
}
Start-Sleep -Seconds 3
logman stop tgm -ets
$ran | ConvertTo-Json | Set-Content -Encoding utf8 "$m\actions.json"

tracerpt $etl -o "$m\trace.xml" -of XML -y | Out-Null
wevtutil qe Microsoft-Windows-Sysmon/Operational /f:xml /e:Events | Set-Content -Encoding utf8 "$m\sysmon.xml"
foreach ($channel in 'Connectivity', 'Operational', 'Security') {
    wevtutil qe "Microsoft-Windows-SMBClient/$channel" /f:xml /e:Events |
        Set-Content -Encoding utf8 "$m\smbclient-$($channel.ToLower()).xml"
}
Stop-Transcript
Compress-Archive -Force -Path "$m\*.xml", "$m\*.json", "$m\*.out", "$m\measure.log" `
    -DestinationPath "$m\result.zip"
