# Run on the joined workstation by windows_kerberos.py, as SYSTEM through the guest agent.
# Records an ETW session over the providers that could tie a Kerberos exchange (and the DNS
# lookups before it) to the process that caused it, while fresh processes request tickets,
# and packs everything into C:\m\result.zip: the trace as XML, each action's process id and
# times, Sysmon's channel.
param(
    [Parameter(Mandatory)] [string] $Dc,
    [Parameter(Mandatory)] [string] $Domain,
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

$providers = @(
    @('Microsoft-Windows-Security-Kerberos', '0xffffffffffffffff'),
    @('LsaSrv', '0xffffffffffffffff'),
    @('Microsoft-Windows-AuthenticationProvider', '0xffffffffffffffff'),
    # The Kerberos client's own tracing is WPP: no decodable payload, but the header
    # still says which process each event was logged in.
    @('{6B510852-3583-4E2D-AFFE-A67F9F223438}', '0xffffffffffffffff'),
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

function Run([string] $Name, [string] $Command) {
    Start-Sleep -Seconds 3
    $start = [DateTime]::UtcNow.ToString('o')
    $p = Start-Process cmd.exe -ArgumentList "/c $Command > $m\$Name.out 2>&1" `
        -PassThru -Wait -WindowStyle Hidden
    [pscustomobject]@{
        action = $Name; pid = $p.Id; exit = $p.ExitCode
        start = $start; end = [DateTime]::UtcNow.ToString('o')
    }
}

$ran = @(
    # SYSTEM's tickets are the machine account's.
    Run 'purge' 'klist purge'
    Run 'ticket' "klist get cifs/$Dc"
    Run 'share' "klist purge > nul & dir \\$Dc\SYSVOL"
    Run 'resolve' "ipconfig /flushdns > nul & ping -n 1 $Dc"
)

# A domain user's logon: a scheduled task in a session of its own. Its process is found
# afterwards by the marker in its command line.
$marker = 'tiergen-measure-user'
$start = [DateTime]::UtcNow.ToString('o')
$action = New-ScheduledTaskAction -Execute cmd.exe `
    -Argument "/c echo $marker & dir \\$Dc\NETLOGON > $m\user.out 2>&1"
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
klist sessions | Set-Content -Encoding utf8 "$m\sessions.out"
Stop-Transcript
Compress-Archive -Force -Path "$m\*.xml", "$m\*.json", "$m\*.out", "$m\measure.log" `
    -DestinationPath "$m\result.zip"
