# Run on the joined workstation by windows_links.py, as SYSTEM through the guest agent.
# Records an ETW session over the SMB client, DNS client, Kernel-Network and Kernel-Process
# providers while processes, alone and two at a time, use the DC's shares, a second server's
# share, ask for tickets and resolve names, and while a scheduled task does so as a domain
# user. Packs the trace as XML, each action's process id and times, Sysmon's channel and the
# SMB connections that existed before into C:\m\result.zip.
param(
    [Parameter(Mandatory)] [string] $DcShort,
    [Parameter(Mandatory)] [string] $DcFqdn,
    [Parameter(Mandatory)] [string] $Domain,
    [Parameter(Mandatory)] [string] $Server,
    [Parameter(Mandatory)] [string] $ServerUser,
    [Parameter(Mandatory)] [string] $User,
    [Parameter(Mandatory)] [string] $Password
)
$ErrorActionPreference = 'Stop'
$m = 'C:\m'
New-Item -ItemType Directory -Force $m | Out-Null
Start-Transcript -Path "$m\measure.log"

# The pair boots together, so the workstation looked for its DC before the DC was up and
# will not look again for a while; reset the secure channel until it holds.
$deadline = (Get-Date).AddSeconds(300)
while (-not (Test-ComputerSecureChannel -ErrorAction SilentlyContinue)) {
    if ((Get-Date) -gt $deadline) { throw "no secure channel to $Domain" }
    nltest "/sc_reset:$Domain" | Out-Null
    Start-Sleep -Seconds 5
}
Get-SmbConnection | Format-List * | Out-File -Encoding utf8 "$m\smb-before.out"

$providers = @(
    @('Microsoft-Windows-SMBClient', '0xffffffffffffffff'),
    @('Microsoft-Windows-DNS-Client', '0xffffffffffffffff'),
    @('Microsoft-Windows-Kernel-Network', '0xffffffffffffffff'),
    @('Microsoft-Windows-Kernel-Process', '0x10')
)
$etl = "$m\trace.etl"
logman create trace tgm -ets -o $etl -bs 1024 -nb 16 128 -p $providers[0][0] $providers[0][1] 0xff
if ($LASTEXITCODE -ne 0) { throw "logman create exited $LASTEXITCODE" }
foreach ($p in $providers[1..($providers.Count - 1)]) {
    logman update trace tgm -ets -p $p[0] $p[1] 0xff
    "provider $($p[0]): logman exited $LASTEXITCODE"
}

function Begin([string] $Name, [string] $Command) {
    $start = [DateTime]::UtcNow.ToString('o')
    $p = Start-Process cmd.exe -ArgumentList "/c $Command > $m\$Name.out 2>&1" `
        -PassThru -WindowStyle Hidden
    $null = $p.Handle  # without a handle taken now, ExitCode stays empty after the exit
    [pscustomobject]@{ Name = $Name; Process = $p; Start = $start }
}
function Finish($Begun) {
    $Begun.Process.WaitForExit()
    [pscustomobject]@{
        action = $Begun.Name; pid = $Begun.Process.Id; exit = $Begun.Process.ExitCode
        start = $Begun.Start; end = [DateTime]::UtcNow.ToString('o')
    }
}
function Run([string] $Name, [string] $Command) {
    Start-Sleep -Seconds 3
    Finish (Begin $Name $Command)
}
function Together([string] $NameA, [string] $CommandA, [string] $NameB, [string] $CommandB) {
    Start-Sleep -Seconds 3
    $a = Begin $NameA $CommandA
    $b = Begin $NameB $CommandB
    Finish $a
    Finish $b
}

$sysvol = "\\$DcShort\SYSVOL\$Domain"
$share = "\\$Server\share"
$ran = @(
    # Nothing cached: a name to resolve, a TGT and a service ticket to get, and the short
    # name is one no boot-time connection used.
    Run 'fresh' "ipconfig /flushdns > nul & klist purge > nul & dir \\$DcShort\SYSVOL"
    # Two processes on one connection and one session at once.
    Together 'sysvol' "for /l %i in (1,1,10) do @dir $sysvol" `
        'netlogon' "for /l %i in (1,1,10) do @dir \\$DcShort\NETLOGON"
    # Two processes that each need a ticket, and both the TGT, with nothing cached.
    Run 'purge' 'klist purge'
    Together 'host-ticket' "klist get host/$DcFqdn" 'fqdn-share' "dir \\$DcFqdn\NETLOGON"
    # A second server, NTLM: two processes at once on its connection.
    Run 'server-map' "net use $share /user:$ServerUser $Password"
    Together 'server-list' "for /l %i in (1,1,10) do @dir $share" `
        'server-read' "for /l %i in (1,1,10) do @type $share\hello.txt"
    # Two names resolved at once through the DNS cache service.
    Run 'flush' 'ipconfig /flushdns'
    Together 'resolve-dc' "ping -n 1 $DcFqdn" 'resolve-domain' "ping -n 1 $Domain"
)

# A domain user's logon: a scheduled task in a session of its own, found afterwards by the
# marker in its command line.
$marker = 'tiergen-measure-user'
$start = [DateTime]::UtcNow.ToString('o')
$action = New-ScheduledTaskAction -Execute cmd.exe `
    -Argument "/c echo $marker & dir \\$DcShort\NETLOGON > $m\user.out 2>&1"
Register-ScheduledTask -TaskName $marker -Action $action -User "$User@$Domain" `
    -Password $Password -RunLevel Highest -Force | Out-Null
Start-ScheduledTask -TaskName $marker
$deadline = (Get-Date).AddSeconds(60)
do { Start-Sleep -Seconds 1 } while ((Get-ScheduledTask -TaskName $marker).State -eq 'Running' -and (Get-Date) -lt $deadline)
$info = Get-ScheduledTaskInfo -TaskName $marker
$ran += [pscustomobject]@{
    action = 'user'; pid = 0; exit = $info.LastTaskResult
    start = $start; end = [DateTime]::UtcNow.ToString('o'); marker = $marker
}
Unregister-ScheduledTask -TaskName $marker -Confirm:$false

Start-Sleep -Seconds 3
logman stop tgm -ets
$ran | ConvertTo-Json | Set-Content -Encoding utf8 "$m\actions.json"
tracerpt $etl -o "$m\trace.xml" -of XML -y | Out-Null
wevtutil qe Microsoft-Windows-Sysmon/Operational /f:xml /e:Events | Set-Content -Encoding utf8 "$m\sysmon.xml"
Stop-Transcript
Compress-Archive -Force -Path "$m\*.xml", "$m\*.json", "$m\*.out", "$m\measure.log" `
    -DestinationPath "$m\result.zip"
