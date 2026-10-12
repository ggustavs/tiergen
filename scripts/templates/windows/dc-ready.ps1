# Run by build.py through the guest agent: wait until the DC serves its domain, that is its
# directory, KDC and DNS services run and its own DNS finds it as a DC, and, with -Address,
# that it still has its address (a clone's NIC must be the template's, or the static
# configuration stays behind). Exits 0 when ready.
param([Parameter(Mandatory)] [string] $Domain, [string] $Address = '', [int] $Seconds = 900)
$ErrorActionPreference = 'Stop'
$deadline = (Get-Date).AddSeconds($Seconds)
while ($true) {
    try {
        $down = Get-Service NTDS, Kdc, DNS, Netlogon, ADWS | Where-Object Status -ne 'Running'
        if ($Address -and -not (Get-NetIPAddress -IPAddress $Address -ErrorAction SilentlyContinue)) {
            throw "no adapter has ${Address}: $((Get-NetIPAddress -AddressFamily IPv4).IPAddress -join ', ')"
        }
        if (-not $down) {
            Resolve-DnsName "_ldap._tcp.dc._msdcs.$Domain" -Type SRV -DnsOnly | Out-Null
            (Get-ADDomain).DNSRoot
            exit 0
        }
        $last = "not running: $($down.Name -join ', ')"
    } catch {
        $last = $_.Exception.Message
    }
    if ((Get-Date) -gt $deadline) { throw "the DC is not ready: $last" }
    Start-Sleep -Seconds 5
}
