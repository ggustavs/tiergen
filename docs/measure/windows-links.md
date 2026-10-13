# What links a request to its traffic

Clock offsets (s to add to a guest's stamps): before {'m/dc[0]': 0.9083423614501953, 'm/ws[0]': 0.1607518196105957}, after {'m/dc[0]': 0.9201862812042236, 'm/ws[0]': 0.15770578384399414}.

| action | pid | exit | start | end |
|---|---|---|---|---|
| fresh | 4564 | 0 | 2026-10-13T12:05:37.3265793Z | 2026-10-13T12:05:37.7171033Z |
| sysvol | 1088 | 0 | 2026-10-13T12:05:40.7171280Z | 2026-10-13T12:05:40.7952021Z |
| netlogon | 1560 | 0 | 2026-10-13T12:05:40.7327569Z | 2026-10-13T12:05:40.7952021Z |
| purge | 3388 | 0 | 2026-10-13T12:05:43.7953985Z | 2026-10-13T12:05:43.8420816Z |
| host-ticket | 4220 | 0 | 2026-10-13T12:05:46.8421177Z | 2026-10-13T12:05:46.9203340Z |
| fqdn-share | 5000 | 0 | 2026-10-13T12:05:46.8577704Z | 2026-10-13T12:05:46.9358272Z |
| server-map | 4824 | 0 | 2026-10-13T12:05:49.9358399Z | 2026-10-13T12:05:50.0608271Z |
| server-list | 1792 | 0 | 2026-10-13T12:05:53.0609651Z | 2026-10-13T12:05:53.1233275Z |
| server-read | 376 | 0 | 2026-10-13T12:05:53.0765888Z | 2026-10-13T12:05:53.1233275Z |
| flush | 1528 | 0 | 2026-10-13T12:05:56.1233423Z | 2026-10-13T12:05:56.2171083Z |
| resolve-dc | 2096 | 0 | 2026-10-13T12:05:59.2171367Z | 2026-10-13T12:05:59.3108278Z |
| resolve-domain | 2272 | 0 | 2026-10-13T12:05:59.2328262Z | 2026-10-13T12:05:59.3108278Z |
| user | 4064 | 0 | 2026-10-13T12:05:59.3108278Z | 2026-10-13T12:06:01.5920781Z |

## SMB: requests logged in a process against the wire

Key: (SessionId, MessageId) of SMBClient 30406 against the SMB2 header.

| logged in | matched | command differs | none | several |
|---|---|---|---|---|
| MsMpEng.exe(2776) | 1 | 0 | 0 | 0 |
| System(4) | 18 | 0 | 0 | 3 |
| fqdn-share | 24 | 0 | 0 | 0 |
| fresh | 28 | 0 | 0 | 0 |
| netlogon | 131 | 0 | 0 | 0 |
| server-list | 38 | 0 | 0 | 0 |
| server-map | 1 | 0 | 0 | 0 |
| server-read | 2 | 0 | 0 | 0 |
| sysvol | 141 | 0 | 0 | 0 |
| user | 17 | 0 | 0 | 0 |

Connections and whose requests they carried:

- tcp:0 10.10.0.10:445 -> 10.10.0.21:49674: System(4)
- tcp:13 10.10.0.10:445 -> 10.10.0.21:49687: System(4), fqdn-share
- tcp:18 10.10.0.53:445 -> 10.10.0.21:49692: MsMpEng.exe(2776), System(4), server-list, server-map, server-read
- tcp:7 10.10.0.10:445 -> 10.10.0.21:49681: System(4), fresh, netlogon, sysvol, user
- requests on the wire no 30406 explains: CLOSE 1, IOCTL 2, NEGOTIATE 4, SESSION_SETUP 4, TREE_CONNECT 1, TREE_DISCONNECT 1

## Kerberos: exchanges, the tickets they handed out, and who used them

- 1791893127.739352 AS-REQ from :49675 cname tiergen-ws$ sname krbtgt/hq.tiergen.test; reply none or an error; DC audit none
- 1791893127.746749 AS-REQ from :49676 cname tiergen-ws$ sname krbtgt/hq.tiergen.test; reply AS-REP; DC audit 4768 TIERGEN-WS$ krbtgt
  - presented in the TGS-REQ for cifs/TIERGEN-DC.hq.tiergen.test
    - presented in an SMB session setup on tcp:0: System(4)
  - presented in the TGS-REQ for krbtgt/HQ.TIERGEN.TEST
    - presented nowhere in the capture
- 1791893127.750188 TGS-REQ from :49677 cname  sname krbtgt/HQ.TIERGEN.TEST/cifs/TIERGEN-DC.hq.tiergen.test; reply TGS-REP; DC audit 4769 TIERGEN-WS$@HQ.TIERGEN.TEST TIERGEN-DC$
  - presented in an SMB session setup on tcp:0: System(4)
- 1791893127.754472 TGS-REQ from :49678 cname  sname krbtgt/HQ.TIERGEN.TEST/krbtgt/HQ.TIERGEN.TEST; reply TGS-REP; DC audit 4769 TIERGEN-WS$@HQ.TIERGEN.TEST krbtgt
  - presented nowhere in the capture
- 1791893137.851130 AS-REQ from :49682 cname tiergen-ws$ sname krbtgt/HQ.TIERGEN.TEST; reply none or an error; DC audit none
- 1791893137.856691 AS-REQ from :49683 cname tiergen-ws$ sname krbtgt/HQ.TIERGEN.TEST; reply AS-REP; DC audit 4768 TIERGEN-WS$ krbtgt
  - presented in the TGS-REQ for cifs/TIERGEN-DC
    - presented in an SMB session setup on tcp:7: System(4), fresh, netlogon, sysvol
  - presented in the TGS-REQ for krbtgt/HQ.TIERGEN.TEST
    - presented nowhere in the capture
- 1791893137.857917 TGS-REQ from :49684 cname  sname krbtgt/HQ.TIERGEN.TEST/cifs/TIERGEN-DC; reply TGS-REP; DC audit 4769 TIERGEN-WS$@HQ.TIERGEN.TEST TIERGEN-DC$
  - presented in an SMB session setup on tcp:7: System(4), fresh, netlogon, sysvol
- 1791893137.859025 TGS-REQ from :49685 cname  sname krbtgt/HQ.TIERGEN.TEST/krbtgt/HQ.TIERGEN.TEST; reply TGS-REP; DC audit 4769 TIERGEN-WS$@HQ.TIERGEN.TEST krbtgt
  - presented nowhere in the capture
- 1791893147.071319 AS-REQ from :49686 cname tiergen-ws$ sname krbtgt/HQ.TIERGEN.TEST; reply none or an error; DC audit none
- 1791893147.072640 AS-REQ from :49688 cname tiergen-ws$ sname krbtgt/HQ.TIERGEN.TEST; reply AS-REP; DC audit 4768 TIERGEN-WS$ krbtgt
  - presented in the TGS-REQ for host/TIERGEN-DC.hq.tiergen.test
    - presented nowhere in the capture
  - presented in the TGS-REQ for cifs/TIERGEN-DC.hq.tiergen.test
    - presented in an SMB session setup on tcp:13: System(4), fqdn-share
  - presented in the TGS-REQ for krbtgt/HQ.TIERGEN.TEST
    - presented nowhere in the capture
- 1791893147.073404 TGS-REQ from :49689 cname  sname krbtgt/HQ.TIERGEN.TEST/host/TIERGEN-DC.hq.tiergen.test; reply TGS-REP; DC audit 4769 TIERGEN-WS$@HQ.TIERGEN.TEST TIERGEN-DC$
  - presented nowhere in the capture
- 1791893147.073807 TGS-REQ from :49690 cname  sname krbtgt/HQ.TIERGEN.TEST/cifs/TIERGEN-DC.hq.tiergen.test; reply TGS-REP; DC audit 4769 TIERGEN-WS$@HQ.TIERGEN.TEST TIERGEN-DC$
  - presented in an SMB session setup on tcp:13: System(4), fqdn-share
- 1791893147.074534 TGS-REQ from :49691 cname  sname krbtgt/HQ.TIERGEN.TEST/krbtgt/HQ.TIERGEN.TEST; reply TGS-REP; DC audit 4769 TIERGEN-WS$@HQ.TIERGEN.TEST krbtgt
  - presented nowhere in the capture
- 1791893159.706030 AS-REQ from :49695 cname Administrator sname krbtgt/HQ; reply none or an error; DC audit none
- 1791893159.710323 AS-REQ from :49696 cname Administrator sname krbtgt/HQ; reply AS-REP; DC audit 4768 Administrator krbtgt
  - presented in the TGS-REQ for host/tiergen-ws.hq.tiergen.test
    - presented nowhere in the capture
- 1791893159.711350 TGS-REQ from :49697 cname  sname krbtgt/HQ.TIERGEN.TEST/host/tiergen-ws.hq.tiergen.test; reply TGS-REP; DC audit 4769 Administrator@HQ.TIERGEN.TEST TIERGEN-WS$
  - presented nowhere in the capture
- 1791893159.783610 AS-REQ from :49698 cname Administrator sname krbtgt/HQ; reply none or an error; DC audit none
- 1791893159.788704 AS-REQ from :49699 cname Administrator sname krbtgt/HQ; reply AS-REP; DC audit 4768 Administrator krbtgt
  - presented in the TGS-REQ for host/tiergen-ws.hq.tiergen.test
    - presented nowhere in the capture
- 1791893159.790422 TGS-REQ from :49700 cname  sname krbtgt/HQ.TIERGEN.TEST/host/tiergen-ws.hq.tiergen.test; reply TGS-REP; DC audit 4769 Administrator@HQ.TIERGEN.TEST TIERGEN-WS$
  - presented nowhere in the capture
- 1791893159.798333 AS-REQ from :49701 cname Administrator sname krbtgt/HQ; reply none or an error; DC audit none
- 1791893159.801671 AS-REQ from :49702 cname Administrator sname krbtgt/HQ; reply AS-REP; DC audit 4768 Administrator krbtgt
  - presented in the TGS-REQ for host/tiergen-ws.hq.tiergen.test
    - presented nowhere in the capture
  - presented in the TGS-REQ for TIERGEN-DC.hq.tiergen.test/hq.tiergen.test
    - presented in AP-REQ to 10.10.0.10:49667
  - presented in the TGS-REQ for cifs/TIERGEN-DC
    - presented in an SMB session setup on tcp:7: System(4), user
  - presented in the TGS-REQ for krbtgt/HQ.TIERGEN.TEST
    - presented nowhere in the capture
- 1791893159.802755 TGS-REQ from :49703 cname  sname krbtgt/HQ.TIERGEN.TEST/host/tiergen-ws.hq.tiergen.test; reply TGS-REP; DC audit 4769 Administrator@HQ.TIERGEN.TEST TIERGEN-WS$
  - presented nowhere in the capture
- 1791893159.815747 TGS-REQ from :49704 cname  sname krbtgt/HQ.TIERGEN.TEST/LDAP/TIERGEN-DC.hq.tiergen.test/hq.tiergen.test; reply TGS-REP; DC audit 4769 Administrator@HQ.TIERGEN.TEST TIERGEN-DC$
  - presented in AP-REQ to 10.10.0.10:49667
- 1791893160.126894 TGS-REQ from :49705 cname  sname krbtgt/HQ.TIERGEN.TEST/cifs/TIERGEN-DC; reply TGS-REP; DC audit 4769 Administrator@HQ.TIERGEN.TEST TIERGEN-DC$
  - presented in an SMB session setup on tcp:7: System(4), user
- 1791893160.128833 TGS-REQ from :49706 cname  sname krbtgt/HQ.TIERGEN.TEST/krbtgt/HQ.TIERGEN.TEST; reply TGS-REP; DC audit 4769 Administrator@HQ.TIERGEN.TEST krbtgt
  - presented nowhere in the capture

## DNS: names a process resolved against the queries on the wire

Each ask (DNS client 3006, in the asking process) against the nearest query of the same name within 0.5 s on the capture's clock; then each query with every ask it was the nearest for.

- svchost.exe(1280) asked tiergen-dc type 28: no query of that name within 0.5 s
- svchost.exe(1280) asked tiergen-dc type 1: no query of that name within 0.5 s
- svchost.exe(2624) asked v10.events.data.microsoft.com type 28: query id 38198
- svchost.exe(2624) asked v10.events.data.microsoft.com type 1: query id 38198
- svchost.exe(1280) asked tiergen-dc.hq.tiergen.test type 28: query id 39056
- svchost.exe(1280) asked tiergen-dc.hq.tiergen.test type 1: query id 39056
- Sysmon64.exe(2744) asked 53.0.10.10.in-addr.arpa type 12: query id 32253
- svchost.exe(1960) asked wpad type 28: no query of that name within 0.5 s
- svchost.exe(1960) asked wpad type 1: no query of that name within 0.5 s
- resolve-domain asked hq.tiergen.test type 1: query id 31898
- resolve-domain asked hq.tiergen.test type 28: query id 31898
- resolve-dc asked tiergen-dc.hq.tiergen.test type 1: query id 51406
- resolve-dc asked tiergen-dc.hq.tiergen.test type 28: query id 51406
- lsass.exe(668) asked tiergen-dc.hq.tiergen.test type 1: query id 51406
- lsass.exe(668) asked tiergen-dc.hq.tiergen.test type 28: query id 51406
- lsass.exe(668) asked tiergen-dc.hq.tiergen.test type 1: query id 51406
- lsass.exe(668) asked tiergen-dc.hq.tiergen.test type 28: query id 51406
- lsass.exe(668) asked (empty) type 1: no query of that name within 0.5 s
- lsass.exe(668) asked (empty) type 1: no query of that name within 0.5 s
- lsass.exe(668) asked (empty) type 1: no query of that name within 0.5 s

Queries on the wire and who asked:

- 1791893078.415 id 41729 255.0.10.10.in-addr.arpa from 10.10.0.21:51525: no ask
- 1791893078.415 id 31701 252.0.0.224.in-addr.arpa from 10.10.0.21:52717: no ask
- 1791893078.415 id 35919 3.0.0.0.1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.2.0.f.f.ip6.arpa from 10.10.0.21:61708: no ask
- 1791893079.025 id 22981 _ldap._tcp.Default-First-Site-Name._sites.hq.tiergen.test from 10.10.0.21:55249: no ask
- 1791893079.353 id 44653 TIERGEN-WS.hq.tiergen.test from 10.10.0.21:64745: no ask
- 1791893080.040 id 22981 _ldap._tcp.Default-First-Site-Name._sites.hq.tiergen.test from 10.10.0.21:55249: no ask
- 1791893081.666 id 30321 dns.msftncsi.com from 10.10.0.21:55610: no ask
- 1791893081.666 id 10028 dns.msftncsi.com from 10.10.0.21:60726: no ask
- 1791893081.704 id 18005 dns.msftncsi.com from 10.10.0.21:51526: no ask
- 1791893081.704 id 57738 v10.events.data.microsoft.com from 10.10.0.21:56089: no ask
- 1791893082.059 id 22981 _ldap._tcp.Default-First-Site-Name._sites.hq.tiergen.test from 10.10.0.21:55249: no ask
- 1791893082.665 id 30321 dns.msftncsi.com from 10.10.0.21:55610: no ask
- 1791893082.665 id 10028 dns.msftncsi.com from 10.10.0.21:60726: no ask
- 1791893082.697 id 57738 v10.events.data.microsoft.com from 10.10.0.21:56089: no ask
- 1791893082.697 id 18005 dns.msftncsi.com from 10.10.0.21:51526: no ask
- 1791893083.353 id 44653 TIERGEN-WS.hq.tiergen.test from 10.10.0.21:64745: no ask
- 1791893083.681 id 10028 dns.msftncsi.com from 10.10.0.21:60726: no ask
- 1791893083.681 id 30321 dns.msftncsi.com from 10.10.0.21:55610: no ask
- 1791893083.712 id 18005 dns.msftncsi.com from 10.10.0.21:51526: no ask
- 1791893083.712 id 57738 v10.events.data.microsoft.com from 10.10.0.21:56089: no ask
- 1791893085.681 id 30321 dns.msftncsi.com from 10.10.0.21:55610: no ask
- 1791893085.681 id 10028 dns.msftncsi.com from 10.10.0.21:60726: no ask
- 1791893085.712 id 57738 v10.events.data.microsoft.com from 10.10.0.21:56089: no ask
- 1791893085.712 id 18005 dns.msftncsi.com from 10.10.0.21:51526: no ask
- 1791893086.056 id 22981 _ldap._tcp.Default-First-Site-Name._sites.hq.tiergen.test from 10.10.0.21:55249: no ask
- 1791893089.697 id 10028 dns.msftncsi.com from 10.10.0.21:60726: no ask
- 1791893089.697 id 30321 dns.msftncsi.com from 10.10.0.21:55610: no ask
- 1791893089.713 id 18005 dns.msftncsi.com from 10.10.0.21:51526: no ask
- 1791893089.713 id 57738 v10.events.data.microsoft.com from 10.10.0.21:56089: no ask
- 1791893090.089 id 13430 _ldap._tcp.Default-First-Site-Name._sites.hq.tiergen.test from 10.10.0.21:50428: no ask
- 1791893091.088 id 13430 _ldap._tcp.Default-First-Site-Name._sites.hq.tiergen.test from 10.10.0.21:50428: no ask
- 1791893092.103 id 13430 _ldap._tcp.Default-First-Site-Name._sites.hq.tiergen.test from 10.10.0.21:50428: no ask
- 1791893093.697 id 56031 dns.msftncsi.com from 10.10.0.21:50447: no ask
- 1791893093.697 id 28281 dns.msftncsi.com from 10.10.0.21:62347: no ask
- 1791893093.729 id 26382 dns.msftncsi.com from 10.10.0.21:55916: no ask
- 1791893094.103 id 13430 _ldap._tcp.Default-First-Site-Name._sites.hq.tiergen.test from 10.10.0.21:50428: no ask
- 1791893094.713 id 28281 dns.msftncsi.com from 10.10.0.21:62347: no ask
- 1791893094.713 id 56031 dns.msftncsi.com from 10.10.0.21:50447: no ask
- 1791893094.744 id 26382 dns.msftncsi.com from 10.10.0.21:55916: no ask
- 1791893095.728 id 28281 dns.msftncsi.com from 10.10.0.21:62347: no ask
- 1791893095.728 id 56031 dns.msftncsi.com from 10.10.0.21:50447: no ask
- 1791893095.759 id 26382 dns.msftncsi.com from 10.10.0.21:55916: no ask
- 1791893096.667 id 16779 wpad.hq.tiergen.test from 10.10.0.21:49980: no ask
- 1791893097.681 id 16779 wpad.hq.tiergen.test from 10.10.0.21:49980: no ask
- 1791893097.728 id 56031 dns.msftncsi.com from 10.10.0.21:50447: no ask
- 1791893097.728 id 28281 dns.msftncsi.com from 10.10.0.21:62347: no ask
- 1791893097.775 id 26382 dns.msftncsi.com from 10.10.0.21:55916: no ask
- 1791893098.119 id 13430 _ldap._tcp.Default-First-Site-Name._sites.hq.tiergen.test from 10.10.0.21:50428: no ask
- 1791893098.697 id 16779 wpad.hq.tiergen.test from 10.10.0.21:49980: no ask
- 1791893099.620 id 39614 TIERGEN-WS.hq.tiergen.test from 10.10.0.21:55556: no ask
- 1791893100.634 id 39614 TIERGEN-WS.hq.tiergen.test from 10.10.0.21:55556: no ask
- 1791893100.697 id 16779 wpad.hq.tiergen.test from 10.10.0.21:49980: no ask
- 1791893101.650 id 39614 TIERGEN-WS.hq.tiergen.test from 10.10.0.21:55556: no ask
- 1791893101.744 id 28281 dns.msftncsi.com from 10.10.0.21:62347: no ask
- 1791893101.744 id 56031 dns.msftncsi.com from 10.10.0.21:50447: no ask
- 1791893101.775 id 26382 dns.msftncsi.com from 10.10.0.21:55916: no ask
- 1791893103.650 id 39614 TIERGEN-WS.hq.tiergen.test from 10.10.0.21:55556: no ask
- 1791893103.752 id 52533 v10.events.data.microsoft.com from 10.10.0.21:50538: no ask
- 1791893104.712 id 16779 wpad.hq.tiergen.test from 10.10.0.21:49980: no ask
- 1791893104.744 id 52533 v10.events.data.microsoft.com from 10.10.0.21:50538: no ask
- 1791893105.744 id 52533 v10.events.data.microsoft.com from 10.10.0.21:50538: no ask
- 1791893107.589 id 37277 hq.tiergen.test from 10.10.0.21:54165: no ask
- 1791893107.589 id 37724 hq.tiergen.test from 10.10.0.21:55522: no ask
- 1791893107.590 id 23733 hq.tiergen.test from 10.10.0.21:63450: no ask
- 1791893107.590 id 13622 hq.tiergen.test from 10.10.0.21:64795: no ask
- 1791893107.744 id 52533 v10.events.data.microsoft.com from 10.10.0.21:50538: no ask
- 1791893111.760 id 52533 v10.events.data.microsoft.com from 10.10.0.21:50538: no ask
- 1791893127.589 id 54261 _ldap._tcp.Default-First-Site-Name._sites.dc._msdcs.hq.tiergen.test from 10.10.0.21:56054: no ask
- 1791893127.590 id 14472 tiergen-dc.hq.tiergen.test from 10.10.0.21:54827: no ask
- 1791893137.847 id 35545 TIERGEN-DC.hq.tiergen.test from 10.10.0.21:51890: no ask
- 1791893146.788 id 38198 v10.events.data.microsoft.com from 10.10.0.21:50932: svchost.exe(2624) (-0.009 s), svchost.exe(2624) (-0.009 s)
- 1791893147.071 id 39056 TIERGEN-DC.hq.tiergen.test from 10.10.0.21:54044: svchost.exe(1280) (-0.009 s), svchost.exe(1280) (-0.009 s)
- 1791893147.791 id 38198 v10.events.data.microsoft.com from 10.10.0.21:50932: no ask
- 1791893148.807 id 38198 v10.events.data.microsoft.com from 10.10.0.21:50932: no ask
- 1791893150.823 id 38198 v10.events.data.microsoft.com from 10.10.0.21:50932: no ask
- 1791893152.213 id 32253 53.0.10.10.in-addr.arpa from 10.10.0.21:62873: Sysmon64.exe(2744) (-0.009 s)
- 1791893153.229 id 32253 53.0.10.10.in-addr.arpa from 10.10.0.21:62873: no ask
- 1791893154.229 id 32253 53.0.10.10.in-addr.arpa from 10.10.0.21:62873: no ask
- 1791893154.838 id 38198 v10.events.data.microsoft.com from 10.10.0.21:50932: no ask
- 1791893156.229 id 32253 53.0.10.10.in-addr.arpa from 10.10.0.21:62873: no ask
- 1791893156.684 id 35569 wpad.hq.tiergen.test from 10.10.0.21:53595: no ask
- 1791893159.452 id 31898 hq.tiergen.test from 10.10.0.21:62547: resolve-domain (-0.008 s), resolve-domain (-0.008 s)
- 1791893159.458 id 51406 TIERGEN-DC.hq.tiergen.test from 10.10.0.21:62367: resolve-dc (-0.008 s), resolve-dc (-0.008 s), lsass.exe(668) (-0.245 s), lsass.exe(668) (-0.245 s), lsass.exe(668) (-0.247 s), lsass.exe(668) (-0.247 s)
- 1791893160.245 id 32253 53.0.10.10.in-addr.arpa from 10.10.0.21:62873: no ask

## Sensor records against the packets of their connection

- suricata dns: DNS query 84, DNS response 56
  - e.g. query 255.0.10.10.in-addr.arpa id 41729 -> DNS query
  - e.g. query TIERGEN-WS.hq.tiergen.test id 44653 -> DNS query
  - e.g. query dns.msftncsi.com id 18005 -> DNS query
- suricata krb5: Kerberos 30 6, Kerberos AS-REP 6, other packet 38
  - e.g. KRB_AS_REQ tiergen-ws$ krbtgt/hq.tiergen.test -> Kerberos 30
  - e.g. KRB_TGS_REQ <empty> krbtgt/HQ.TIERGEN.TEST -> other packet
  - e.g. KRB_AS_REQ tiergen-ws$ krbtgt/HQ.TIERGEN.TEST -> Kerberos AS-REP
- suricata smb: Kerberos AP-REQ 3, SMB2 CLOSE request 60, SMB2 CLOSE response 2, SMB2 CREATE request 13, SMB2 IOCTL request 5, SMB2 LOGOFF request 1, SMB2 NEGOTIATE request 4, SMB2 QUERY_DIRECTORY request 1, SMB2 QUERY_INFO request 109, SMB2 QUERY_INFO response 1, SMB2 SESSION_SETUP request 2, SMB2 TREE_CONNECT request 6, SMB2 TREE_DISCONNECT request 1, no packet 1, other packet 63
  - e.g. tx 1 SMB1_COMMAND_NEGOTIATE_PROTOCOL session 0 tree 0 -> SMB2 NEGOTIATE request
  - e.g. tx 2 SMB2_COMMAND_NEGOTIATE_PROTOCOL session 0 tree 0 -> Kerberos AP-REQ
  - e.g. tx 1 SMB1_COMMAND_NEGOTIATE_PROTOCOL session 0 tree 0 -> SMB2 NEGOTIATE request
- zeek dce_rpc: other packet 13
  - e.g. epmapper ept_map -> other packet
  - e.g. netlogon NetrServerReqChallenge -> other packet
  - e.g. netlogon NetrServerAuthenticate3 -> other packet
- zeek dns: DNS query 82, DNS response 34, no packet 26, other packet 32
  - e.g. * id 44971 -> other packet
  - e.g. 255.0.10.10.in-addr.arpa id 41729 -> DNS query
  - e.g. 252.0.0.224.in-addr.arpa id 31701 -> DNS query
- zeek kerberos: Kerberos AP-REQ 3, Kerberos AS-REQ 12, Kerberos TGS-REQ 13
  - e.g. AS tiergen-ws$/hq.tiergen.test krbtgt/hq.tiergen.test -> Kerberos AS-REQ
  - e.g. AS tiergen-ws$/hq.tiergen.test krbtgt/HQ.TIERGEN.TEST -> Kerberos AS-REQ
  - e.g. TGS TIERGEN-WS$/HQ.TIERGEN.TEST cifs/TIERGEN-DC.hq.tiergen.test -> Kerberos TGS-REQ
- zeek ntlm: SMB2 SESSION_SETUP request 1
  - e.g. tiergen -> SMB2 SESSION_SETUP request
- zeek smb_files: SMB2 CREATE request 7
  - e.g. SMB::FILE_OPEN <share_root> -> SMB2 CREATE request
  - e.g. SMB::FILE_OPEN hq.tiergen.test -> SMB2 CREATE request
  - e.g. SMB::FILE_OPEN hq.tiergen.test -> SMB2 CREATE request
- zeek smb_mapping: SMB2 TREE_CONNECT request 9
  - e.g. \\\\TIERGEN-DC.hq.tiergen.test\\IPC$ -> SMB2 TREE_CONNECT request
  - e.g. \\\\TIERGEN-DC\\IPC$ -> SMB2 TREE_CONNECT request
  - e.g. \\\\TIERGEN-DC\\SYSVOL -> SMB2 TREE_CONNECT request
