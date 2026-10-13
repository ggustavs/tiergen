# What Windows reports of Kerberos

Processes marked * are an action's process or its descendants.

| action | pid | exit | start | end |
|---|---|---|---|---|
| purge | 744 | 0 | 2026-10-12T17:36:03.4552696Z | 2026-10-12T17:36:04.7208551Z |
| ticket | 1600 | 0 | 2026-10-12T17:36:07.7208740Z | 2026-10-12T17:36:08.7519787Z |
| share | 1364 | 0 | 2026-10-12T17:36:11.7522160Z | 2026-10-12T17:36:12.7832150Z |
| resolve | 4904 | 0 | 2026-10-12T17:36:15.7833605Z | 2026-10-12T17:36:16.8145042Z |
| user | 520 | 0 | 2026-10-12T17:36:16.8145042Z | 2026-10-12T17:36:19.5177173Z |

## Connections to the DC

- 17:36:07.782090 TCP connect 10.10.0.21:49681 -> 10.10.0.10:88 owned by lsass.exe(652)
- 17:36:07.788408 TCP connect 10.10.0.21:49682 -> 10.10.0.10:88 owned by lsass.exe(652)
- 17:36:07.790039 TCP connect 10.10.0.21:49683 -> 10.10.0.10:88 owned by lsass.exe(652)
- 17:36:10.588930 UDP send 10.10.0.21:50841 -> 10.10.0.10:53 owned by svchost.exe(1160)
- 17:36:11.596133 UDP send 10.10.0.21:50841 -> 10.10.0.10:53 owned by svchost.exe(1160)
- 17:36:11.813374 TCP connect 10.10.0.21:49684 -> 10.10.0.10:445 owned by System(4)
- 17:36:11.815489 TCP connect 10.10.0.21:49685 -> 10.10.0.10:88 owned by lsass.exe(652)
- 17:36:11.816534 TCP connect 10.10.0.21:49686 -> 10.10.0.10:88 owned by lsass.exe(652)
- 17:36:11.817197 TCP connect 10.10.0.21:49687 -> 10.10.0.10:88 owned by lsass.exe(652)
- 17:36:11.818289 TCP connect 10.10.0.21:49688 -> 10.10.0.10:88 owned by lsass.exe(652)
- 17:36:12.611618 UDP send 10.10.0.21:50841 -> 10.10.0.10:53 owned by svchost.exe(1160)
- 17:36:14.611609 UDP send 10.10.0.21:50841 -> 10.10.0.10:53 owned by svchost.exe(1160)
- 17:36:15.886280 UDP send 10.10.0.21:60090 -> 10.10.0.10:53 owned by svchost.exe(1160)
- 17:36:17.491015 TCP connect 10.10.0.21:49689 -> 10.10.0.10:49667 owned by lsass.exe(652)
- 17:36:17.499835 TCP connect 10.10.0.21:49690 -> 10.10.0.10:88 owned by lsass.exe(652)
- 17:36:17.504194 TCP connect 10.10.0.21:49691 -> 10.10.0.10:88 owned by lsass.exe(652)
- 17:36:17.505439 TCP connect 10.10.0.21:49692 -> 10.10.0.10:88 owned by lsass.exe(652)
- 17:36:17.582916 TCP connect 10.10.0.21:49693 -> 10.10.0.10:88 owned by lsass.exe(652)
- 17:36:17.587640 TCP connect 10.10.0.21:49694 -> 10.10.0.10:88 owned by lsass.exe(652)
- 17:36:17.589016 TCP connect 10.10.0.21:49695 -> 10.10.0.10:88 owned by lsass.exe(652)
- 17:36:17.596804 TCP connect 10.10.0.21:49696 -> 10.10.0.10:88 owned by lsass.exe(652)
- 17:36:17.600799 TCP connect 10.10.0.21:49697 -> 10.10.0.10:88 owned by lsass.exe(652)
- 17:36:17.601826 TCP connect 10.10.0.21:49698 -> 10.10.0.10:88 owned by lsass.exe(652)
- 17:36:17.613159 TCP connect 10.10.0.21:49699 -> 10.10.0.10:88 owned by lsass.exe(652)
- 17:36:17.928618 TCP connect 10.10.0.21:49700 -> 10.10.0.10:88 owned by lsass.exe(652)
- 17:36:17.930760 TCP connect 10.10.0.21:49701 -> 10.10.0.10:88 owned by lsass.exe(652)
- 17:36:18.626996 UDP send 10.10.0.21:50841 -> 10.10.0.10:53 owned by svchost.exe(1160)
- Sysmon network connection: svchost.exe (2056) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (2056) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (2056) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (2056) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (2056) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (2404) -> 10.10.0.10:389
- Sysmon network connection: svchost.exe (2404) -> 10.10.0.10:389
- Sysmon network connection: svchost.exe (2404) -> 10.10.0.10:389
- Sysmon network connection: svchost.exe (2056) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (2056) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (2056) -> 10.10.0.10:53
- Sysmon network connection: System (4) -> 10.10.0.10:445
- Sysmon network connection: svchost.exe (2056) -> 10.10.0.10:53
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:389
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:88
- Sysmon network connection: svchost.exe (2404) -> 10.10.0.10:389
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:88
- Sysmon network connection: svchost.exe (2404) -> 10.10.0.10:135
- Sysmon network connection: svchost.exe (2404) -> 10.10.0.10:49667
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:389
- Sysmon network connection: svchost.exe (2056) -> 10.10.0.10:53
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:389
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:135
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:135
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:49667
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:49667
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:389
- Sysmon network connection: svchost.exe (2056) -> 10.10.0.10:53
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:389
- Sysmon network connection: dsregcmd.exe (6148) -> 10.10.0.10:135
- Sysmon network connection: dsregcmd.exe (6148) -> 10.10.0.10:49667
- Sysmon network connection: svchost.exe (2056) -> 10.10.0.10:53
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:389
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:389
- Sysmon network connection: svchost.exe (2056) -> 10.10.0.10:53
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:389
- Sysmon network connection: dsregcmd.exe (6148) -> 10.10.0.10:389
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:389
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:389
- Sysmon network connection: lsass.exe (668) -> 10.10.0.10:389
- Sysmon network connection: <unknown process> (6148) -> 10.10.0.10:389
- Sysmon network connection: svchost.exe (6520) -> 10.10.0.10:123
- Sysmon network connection: System (4) -> 10.10.0.10:137
- Sysmon network connection: svchost.exe (1184) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1184) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1184) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1184) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1184) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1184) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1184) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1184) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1184) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1184) -> 10.10.0.10:53
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:389
- Sysmon network connection: svchost.exe (1184) -> 10.10.0.10:53
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:135
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:389
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:135
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:49667
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:49667
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:49667
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:88
- Sysmon network connection: svchost.exe (1592) -> 10.10.0.10:389
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:389
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:88
- Sysmon network connection: System (4) -> 10.10.0.10:445
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:389
- Sysmon network connection: svchost.exe (1184) -> 10.10.0.10:53
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:389
- Sysmon network connection: svchost.exe (1184) -> 10.10.0.10:53
- Sysmon network connection: dsregcmd.exe (2964) -> 10.10.0.10:135
- Sysmon network connection: svchost.exe (2240) -> 10.10.0.10:389
- Sysmon network connection: dsregcmd.exe (2964) -> 10.10.0.10:49667
- Sysmon network connection: dsregcmd.exe (2964) -> 10.10.0.10:389
- Sysmon network connection: dsregcmd.exe (2964) -> 10.10.0.10:389
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:389
- Sysmon network connection: svchost.exe (1184) -> 10.10.0.10:53
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:389
- Sysmon network connection: svchost.exe (424) -> 10.10.0.10:389
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:88
- Sysmon network connection: svchost.exe (424) -> 10.10.0.10:389
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:389
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:389
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:389
- Sysmon network connection: svchost.exe (1184) -> 10.10.0.10:53
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:389
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:389
- Sysmon network connection: taskhostw.exe (4636) -> 10.10.0.10:389
- Sysmon network connection: taskhostw.exe (4636) -> 10.10.0.10:389
- Sysmon network connection: svchost.exe (1184) -> 10.10.0.10:53
- Sysmon network connection: taskhostw.exe (4636) -> 10.10.0.10:389
- Sysmon network connection: taskhostw.exe (4636) -> 10.10.0.10:389
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:88
- Sysmon network connection: svchost.exe (1184) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1184) -> 10.10.0.10:53
- Sysmon network connection: lsass.exe (656) -> 10.10.0.10:88
- Sysmon network connection: svchost.exe (1184) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1184) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1184) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1108) -> 10.10.0.10:123
- Sysmon network connection: System (4) -> 10.10.0.10:137
- Sysmon network connection: svchost.exe (1184) -> 10.10.0.10:5355
- Sysmon network connection: svchost.exe (1184) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:5353
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:53
- Sysmon network connection: System (4) -> 10.10.0.10:137
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:53
- Sysmon network connection: System (4) -> 10.10.0.10:137
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:53
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:53
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:389
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:135
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:49667
- Sysmon network connection: System (4) -> 10.10.0.10:445
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:88
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:53
- Sysmon network connection: System (4) -> 10.10.0.10:445
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:88
- Sysmon network connection: svchost.exe (1160) -> 10.10.0.10:53
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:49667
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:88
- Sysmon network connection: lsass.exe (652) -> 10.10.0.10:88

## Authentication and DNS client events

| provider | id | task | n | logged in | fields naming the DC or a service |
|---|---|---|---|---|---|
|  | 0 |  | 4 | logman.exe(4328), ?(4294967295) |  |
| LsaSrv | 300 |  | 5 | lsass.exe(652) |  |
| LsaSrv | 303 |  | 8 | lsass.exe(652) |  |
| LsaSrv | 6225 | LSA Logon  | 5 | lsass.exe(652) |  |
| LsaSrv | 6226 | LSA Logon  | 5 | lsass.exe(652) |  |
| DNS-Client | 1001 | DnsServerForInterface | 3 | svchost.exe(1160) | Address |
| DNS-Client | 1013 | DnsAllServersTimeout | 1 | svchost.exe(1160) | Address |
| DNS-Client | 1015 | DnsServerTimeout | 4 | svchost.exe(1160) | Address |
| DNS-Client | 3006 |  | 11 | lsass.exe(652), svchost.exe(1160), svchost.exe(2616), PING.EXE(5044)* | QueryName |
| DNS-Client | 3008 |  | 11 | lsass.exe(652), svchost.exe(1160), svchost.exe(2616), PING.EXE(5044)* | QueryName, QueryResults |
| DNS-Client | 3009 |  | 4 | svchost.exe(1160) | DNSServerAddress, QueryName |
| DNS-Client | 3010 |  | 6 | svchost.exe(1160) | DnsServerIpAddress, QueryName |
| DNS-Client | 3011 |  | 2 | svchost.exe(1160) | DnsServerIpAddress, QueryName |
| DNS-Client | 3016 |  | 7 | svchost.exe(1160) | QueryName |
| DNS-Client | 3018 |  | 7 | svchost.exe(1160) | QueryName, QueryResults |
| DNS-Client | 3019 |  | 2 | svchost.exe(1160) | QueryName |
| DNS-Client | 3020 |  | 2 | svchost.exe(1160) | QueryName, QueryResults |
| Unknown | 10 |  | 10 | lsass.exe(652) |  |
| Unknown | 11 |  | 5 | lsass.exe(652) |  |
| Unknown | 12 |  | 9 | lsass.exe(652) |  |
| Unknown | 13 |  | 5 | lsass.exe(652) |  |
| Unknown | 14 |  | 2 | lsass.exe(652) |  |
| Unknown | 15 |  | 3 | lsass.exe(652) |  |
| Unknown | 17 |  | 17 | lsass.exe(652) |  |
| Unknown | 18 |  | 19 | lsass.exe(652) |  |
| Unknown | 19 |  | 25 | lsass.exe(652) |  |
| Unknown | 20 |  | 2 | lsass.exe(652) |  |
| Unknown | 22 |  | 1 | lsass.exe(652) |  |
| Unknown | 23 |  | 8 | lsass.exe(652) |  |
| Unknown | 25 |  | 2 | lsass.exe(652) |  |
| Unknown | 26 |  | 25 | lsass.exe(652) |  |
| Unknown | 27 |  | 12 | lsass.exe(652) |  |
| Unknown | 28 |  | 9 | lsass.exe(652) |  |
| Unknown | 31 |  | 3 | lsass.exe(652) |  |
| Unknown | 33 |  | 2 | lsass.exe(652) |  |
| Unknown | 34 |  | 19 | lsass.exe(652) |  |
| Unknown | 35 |  | 19 | lsass.exe(652) |  |
| Unknown | 36 |  | 8 | lsass.exe(652) |  |
| Unknown | 37 |  | 8 | lsass.exe(652) |  |
| Unknown | 38 |  | 20 | lsass.exe(652) |  |
| Unknown | 40 |  | 3 | lsass.exe(652) |  |
| Unknown | 41 |  | 5 | lsass.exe(652) |  |
| Unknown | 42 |  | 3 | lsass.exe(652) |  |
| Unknown | 43 |  | 34 | lsass.exe(652) |  |
| Unknown | 45 |  | 7 | lsass.exe(652) |  |
| Unknown | 46 |  | 8 | lsass.exe(652) |  |
| Unknown | 47 |  | 5 | lsass.exe(652) |  |
| Unknown | 48 |  | 5 | lsass.exe(652) |  |
| Unknown | 50 |  | 3 | lsass.exe(652) |  |
| Unknown | 52 |  | 3 | lsass.exe(652) |  |
| Unknown | 56 |  | 3 | lsass.exe(652) |  |
| Unknown | 57 |  | 4 | lsass.exe(652) |  |
| Unknown | 58 |  | 4 | lsass.exe(652) |  |
| Unknown | 59 |  | 5 | lsass.exe(652) |  |
| Unknown | 60 |  | 5 | lsass.exe(652) |  |
| Unknown | 61 |  | 19 | lsass.exe(652) |  |
| Unknown | 63 |  | 3 | lsass.exe(652) |  |
| Unknown | 64 |  | 5 | lsass.exe(652) |  |
| Unknown | 68 |  | 8 | lsass.exe(652) |  |
| Unknown | 69 |  | 3 | lsass.exe(652) |  |
| Unknown | 73 |  | 19 | lsass.exe(652) |  |
| Unknown | 74 |  | 4 | lsass.exe(652) |  |
| Unknown | 75 |  | 1 | lsass.exe(652) |  |
| Unknown | 76 |  | 1 | lsass.exe(652) |  |
| Unknown | 77 |  | 12 | lsass.exe(652) |  |
| Unknown | 78 |  | 10 | lsass.exe(652) |  |
| Unknown | 79 |  | 3 | lsass.exe(652) |  |
| Unknown | 83 |  | 1 | lsass.exe(652) |  |
| Unknown | 84 |  | 1 | lsass.exe(652) |  |
| Unknown | 86 |  | 10 | lsass.exe(652) |  |
| Unknown | 88 |  | 4 | lsass.exe(652) |  |
| Unknown | 89 |  | 15 | lsass.exe(652) |  |
| Unknown | 90 |  | 10 | lsass.exe(652) |  |
| Unknown | 91 |  | 3 | lsass.exe(652) |  |
| Unknown | 92 |  | 3 | lsass.exe(652) |  |
| Unknown | 93 |  | 3 | lsass.exe(652) |  |
| Unknown | 96 |  | 5 | lsass.exe(652) |  |
| Unknown | 97 |  | 3 | lsass.exe(652) |  |
| Unknown | 99 |  | 4 | lsass.exe(652) |  |
| Unknown | 100 |  | 4 | lsass.exe(652) |  |
| Unknown | 102 |  | 11 | lsass.exe(652) |  |
| Unknown | 103 |  | 9 | lsass.exe(652) |  |
| Unknown | 106 |  | 3 | lsass.exe(652) |  |
| Unknown | 112 |  | 3 | lsass.exe(652) |  |
| Unknown | 113 |  | 7 | lsass.exe(652) |  |
| Unknown | 114 |  | 7 | lsass.exe(652) |  |
| Unknown | 116 |  | 7 | lsass.exe(652) |  |
| Unknown | 117 |  | 7 | lsass.exe(652) |  |
| Unknown | 118 |  | 2 | lsass.exe(652) |  |
| Unknown | 120 |  | 2 | lsass.exe(652) |  |
| Unknown | 123 |  | 4 | lsass.exe(652) |  |
| Unknown | 129 |  | 1 | lsass.exe(652) |  |
| Unknown | 135 |  | 1 | lsass.exe(652) |  |
| Unknown | 142 |  | 2 | lsass.exe(652) |  |
| Unknown | 143 |  | 1 | lsass.exe(652) |  |
| Unknown | 144 |  | 1 | lsass.exe(652) |  |
| Unknown | 148 |  | 5 | lsass.exe(652) |  |
| Unknown | 155 |  | 9 | lsass.exe(652) |  |
| Unknown | 167 |  | 1 | lsass.exe(652) |  |
| Unknown | 168 |  | 1 | lsass.exe(652) |  |
| Unknown | 181 |  | 7 | lsass.exe(652) |  |
| Unknown | 186 |  | 7 | lsass.exe(652) |  |
| Unknown | 203 |  | 5 | lsass.exe(652) |  |
| Unknown | 220 |  | 12 | lsass.exe(652) |  |
| Unknown | 221 |  | 12 | lsass.exe(652) |  |
| Unknown | 257 |  | 2 | lsass.exe(652) |  |
| Unknown | 258 |  | 4 | lsass.exe(652) |  |
| Unknown | 264 |  | 3 | lsass.exe(652) |  |
| Unknown | 278 |  | 3 | lsass.exe(652) |  |
| Unknown | 283 |  | 3 | lsass.exe(652) |  |
| Unknown | 295 |  | 3 | lsass.exe(652) |  |
| Unknown | 297 |  | 3 | lsass.exe(652) |  |
| Unknown | 298 |  | 3 | lsass.exe(652) |  |
| Unknown | 307 |  | 2 | lsass.exe(652) |  |
| Unknown | 308 |  | 5 | lsass.exe(652) |  |
| Unknown | 310 |  | 3 | lsass.exe(652) |  |
| Unknown | 313 |  | 3 | lsass.exe(652) |  |

## The DC's Kerberos audit

- 4768 TIERGEN-DC$ krbtgt from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST krbtgt from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::1:0 status 0x0
- 4768 TIERGEN-DC$ krbtgt from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::1:0 status 0x0
- 4768 TIERGEN-DC$ krbtgt from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::1:0 status 0x0
- 4768 TIERGEN-DC$ krbtgt from ::1:0 status 0x0
- 4768 TIERGEN-DC$ krbtgt from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST krbtgt from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::1:0 status 0x0
- 4768 TIERGEN-DC$ krbtgt from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::1:0 status 0x0
- 4768 TIERGEN-DC$ krbtgt from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::1:0 status 0x0
- 4768 Administrator krbtgt from ::ffff:10.10.0.21:49675 status 0x0
- 4769 Administrator@HQ.TIERGEN.TEST TIERGEN-DC$ from ::ffff:10.10.0.21:49676 status 0x0
- 4769 Administrator@HQ.TIERGEN.TEST krbtgt from ::ffff:10.10.0.21:49677 status 0x0
- 4768 Administrator krbtgt from ::ffff:10.10.0.21:49680 status 0x0
- 4769 Administrator@HQ.TIERGEN.TEST TIERGEN-DC$ from ::ffff:10.10.0.21:49681 status 0x0
- 4768 TIERGEN-WS$ krbtgt from ::ffff:10.10.0.21:49685 status 0x0
- 4769 TIERGEN-WS$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::ffff:10.10.0.21:49686 status 0x0
- 4769 TIERGEN-WS$@HQ.TIERGEN.TEST krbtgt from ::ffff:10.10.0.21:49687 status 0x0
- 4768 TIERGEN-WS$ krbtgt from ::ffff:10.10.0.21:49694 status 0x0
- 4769 TIERGEN-WS$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::ffff:10.10.0.21:49695 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::1:0 status 0x0
- 4768 TIERGEN-WS$ krbtgt from ::ffff:10.10.0.21:49679 status 0x0
- 4768 TIERGEN-WS$ krbtgt from ::ffff:10.10.0.21:49683 status 0x0
- 4769 TIERGEN-WS$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::ffff:10.10.0.21:49686 status 0x0
- 4769 TIERGEN-WS$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::ffff:10.10.0.21:49685 status 0x0
- 4768 TIERGEN-WS$ krbtgt from ::ffff:10.10.0.21:49688 status 0x0
- 4769 TIERGEN-WS$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::ffff:10.10.0.21:49689 status 0x0
- 4769 TIERGEN-WS$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::ffff:10.10.0.21:49691 status 0x0
- 4769 TIERGEN-WS$@HQ.TIERGEN.TEST krbtgt from ::ffff:10.10.0.21:49692 status 0x0
- 4769 TIERGEN-WS$@HQ.TIERGEN.TEST TIERGEN-WS$ from ::ffff:10.10.0.21:49701 status 0x0
- 4769 TIERGEN-WS$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::ffff:10.10.0.21:49706 status 0x0
- 4769 TIERGEN-WS$@HQ.TIERGEN.TEST krbtgt from ::ffff:10.10.0.21:49707 status 0x0
- 4768 TIERGEN-WS$ krbtgt from ::ffff:10.10.0.21:49713 status 0x0
- 4769 TIERGEN-WS$@HQ.TIERGEN.TEST TIERGEN-WS$ from ::ffff:10.10.0.21:49714 status 0x0
- 4769 TIERGEN-WS$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::ffff:10.10.0.21:49715 status 0x0
- 4768 TIERGEN-DC$ krbtgt from ::1:0 status 0x0
- 4768 TIERGEN-DC$ krbtgt from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST krbtgt from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::1:0 status 0x0
- 4768 TIERGEN-DC$ krbtgt from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::1:0 status 0x0
- 4768 TIERGEN-DC$ krbtgt from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::1:0 status 0x0
- 4768 TIERGEN-WS$ krbtgt from ::ffff:10.10.0.21:49678 status 0x0
- 4769 TIERGEN-WS$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::ffff:10.10.0.21:49679 status 0x0
- 4769 TIERGEN-WS$@HQ.TIERGEN.TEST krbtgt from ::ffff:10.10.0.21:49680 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::1:0 status 0x0
- 4769 TIERGEN-DC$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::1:0 status 0x0
- 4768 TIERGEN-WS$ krbtgt from ::ffff:10.10.0.21:49682 status 0x0
- 4769 TIERGEN-WS$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::ffff:10.10.0.21:49683 status 0x0
- 4768 TIERGEN-WS$ krbtgt from ::ffff:10.10.0.21:49686 status 0x0
- 4769 TIERGEN-WS$@HQ.TIERGEN.TEST TIERGEN-DC$ from ::ffff:10.10.0.21:49687 status 0x0
- 4769 TIERGEN-WS$@HQ.TIERGEN.TEST krbtgt from ::ffff:10.10.0.21:49688 status 0x0
- 4768 Administrator krbtgt from ::ffff:10.10.0.21:49691 status 0x0
- 4769 Administrator@HQ.TIERGEN.TEST TIERGEN-WS$ from ::ffff:10.10.0.21:49692 status 0x0
- 4768 Administrator krbtgt from ::ffff:10.10.0.21:49694 status 0x0
- 4769 Administrator@HQ.TIERGEN.TEST TIERGEN-WS$ from ::ffff:10.10.0.21:49695 status 0x0
- 4768 Administrator krbtgt from ::ffff:10.10.0.21:49697 status 0x0
- 4769 Administrator@HQ.TIERGEN.TEST TIERGEN-WS$ from ::ffff:10.10.0.21:49698 status 0x0
- 4769 Administrator@HQ.TIERGEN.TEST TIERGEN-DC$ from ::ffff:10.10.0.21:49699 status 0x0
- 4769 Administrator@HQ.TIERGEN.TEST TIERGEN-DC$ from ::ffff:10.10.0.21:49700 status 0x0
- 4769 Administrator@HQ.TIERGEN.TEST krbtgt from ::ffff:10.10.0.21:49701 status 0x0

## Each action's events

### purge (pid 744, exit 0)

- 17:36:03.487786 LsaSrv 6225 LSA Logon  in lsass.exe(652): 
- 17:36:03.488366 LsaSrv 300  in lsass.exe(652): TargetUserSid=S-1-5-18; TargetUserName=SYSTEM; TargetDomainName=NT AUTHORITY; TargetLogonId=0x3E7; TargetLogonGuid={00000000-0000-0000-0000-000000000000}; EventOrginal=       1; EventCountTotal=       1; SidList=
		%{S-1-5-18}
		%{S-1-1-0}
		%{S-1-5-32-545}
		
- 17:36:03.488553 Unknown 308  in lsass.exe(652): 
- 17:36:03.488587 LsaSrv 6226 LSA Logon  in lsass.exe(652): 
- 17:36:03.710141 Kernel-Process 1 ProcessStart in cmd.exe(744)*: ProcessID=     824; ProcessSequenceNumber=126; CreateTime=2026-10-12T17:36:03.710119900Z; ParentProcessID=     744; ParentProcessSequenceNumber=125; SessionID=       0; Flags=       0; ProcessTokenElevationType=       1; ProcessTokenIsElevated=       1; Mandat
- 17:36:03.744101 Kernel-Process 1 ProcessStart in cmd.exe(744)*: ProcessID=    1184; ProcessSequenceNumber=127; CreateTime=2026-10-12T17:36:03.744084200Z; ParentProcessID=     744; ParentProcessSequenceNumber=125; SessionID=       0; Flags=       0; ProcessTokenElevationType=       1; ProcessTokenIsElevated=       1; Mandat
- 17:36:03.763618 Unknown 25  in lsass.exe(652): 
- 17:36:03.763620 Unknown 27  in lsass.exe(652): 
- 17:36:03.763621 Unknown 14  in lsass.exe(652): 
- 17:36:03.763627 Unknown 10  in lsass.exe(652): 
- 17:36:03.763795 Unknown 13  in lsass.exe(652): 
- 17:36:03.766780 Kernel-Process 2 ProcessStop in cmd.exe(744)*: ProcessID=     744; ProcessSequenceNumber=125; CreateTime=2026-10-12T17:36:03.698324600Z; ExitTime=2026-10-12T17:36:03.766739300Z; ExitCode=       0; TokenElevationType=       1; HandleCount=      48; CommitCharge=4386816; CommitPeak=4386816; CPUCycleCount=101

### ticket (pid 1600, exit 0)

- 17:36:07.744653 Kernel-Process 1 ProcessStart in cmd.exe(1600)*: ProcessID=    1604; ProcessSequenceNumber=129; CreateTime=2026-10-12T17:36:07.744633700Z; ParentProcessID=    1600; ParentProcessSequenceNumber=128; SessionID=       0; Flags=       0; ProcessTokenElevationType=       1; ProcessTokenIsElevated=       1; Mandat
- 17:36:07.768708 Kernel-Process 1 ProcessStart in cmd.exe(1600)*: ProcessID=    2836; ProcessSequenceNumber=130; CreateTime=2026-10-12T17:36:07.768694600Z; ParentProcessID=    1600; ParentProcessSequenceNumber=128; SessionID=       0; Flags=       0; ProcessTokenElevationType=       1; ProcessTokenIsElevated=       1; Mandat
- 17:36:07.781408 Unknown 28  in lsass.exe(652): 
- 17:36:07.781410 Unknown 102  in lsass.exe(652): 
- 17:36:07.781416 Unknown 116  in lsass.exe(652): 
- 17:36:07.781416 Unknown 117  in lsass.exe(652): 
- 17:36:07.781419 Unknown 17  in lsass.exe(652): 
- 17:36:07.781420 Unknown 18  in lsass.exe(652): 
- 17:36:07.781422 Unknown 19  in lsass.exe(652): 
- 17:36:07.781450 Unknown 28  in lsass.exe(652): 
- 17:36:07.781454 Unknown 45  in lsass.exe(652): 
- 17:36:07.781458 Unknown 26  in lsass.exe(652): 
- 17:36:07.781458 Unknown 33  in lsass.exe(652): 
- 17:36:07.781458 Unknown 18  in lsass.exe(652): 
- 17:36:07.781458 Unknown 11  in lsass.exe(652): 
- 17:36:07.781459 Unknown 17  in lsass.exe(652): 
- 17:36:07.781460 Unknown 18  in lsass.exe(652): 
- 17:36:07.781460 Unknown 19  in lsass.exe(652): 
- 17:36:07.781461 Unknown 203  in lsass.exe(652): 
- 17:36:07.781462 Unknown 46  in lsass.exe(652): 
- 17:36:07.781462 Unknown 47  in lsass.exe(652): 
- 17:36:07.781463 Unknown 48  in lsass.exe(652): 
- 17:36:07.781464 Unknown 59  in lsass.exe(652): 
- 17:36:07.781465 Unknown 60  in lsass.exe(652): 
- 17:36:07.781468 Unknown 26  in lsass.exe(652): 
- 17:36:07.781468 Unknown 27  in lsass.exe(652): 
- 17:36:07.781469 Unknown 19  in lsass.exe(652): 
- 17:36:07.781487 Unknown 86  in lsass.exe(652): 
- 17:36:07.781490 Unknown 89  in lsass.exe(652): 
- 17:36:07.781490 Unknown 61  in lsass.exe(652): 
- 17:36:07.781494 Unknown 73  in lsass.exe(652): 
- 17:36:07.781494 Unknown 35  in lsass.exe(652): 
- 17:36:07.782090 Kernel-Network 12 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49681; mss=1460; sackopt=1; tsopt=0; wsopt=1; rcvwin= 2102400; rcvwinscale=8; sndwinscale=8; seqnum=       0; connid=       0
- 17:36:07.782197 Unknown 34  in lsass.exe(652): 
- 17:36:07.782211 Unknown 38  in lsass.exe(652): 
- 17:36:07.783017 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     241; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49681; startime=    7535; endtime=    7535; seqnum=       0; connid=       0
- 17:36:07.783024 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     223; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49681; seqnum=       0; connid=       0
- 17:36:07.783033 Unknown 43  in lsass.exe(652): 
- 17:36:07.783049 Unknown 90  in lsass.exe(652): 
- 17:36:07.783051 Unknown 43  in lsass.exe(652): 
- 17:36:07.783052 Unknown 96  in lsass.exe(652): 
- 17:36:07.783057 Unknown 43  in lsass.exe(652): 
- 17:36:07.783057 Unknown 10  in lsass.exe(652): 
- 17:36:07.783057 Unknown 43  in lsass.exe(652): 
- 17:36:07.783058 Unknown 103  in lsass.exe(652): 
- 17:36:07.783063 Unknown 26  in lsass.exe(652): 
- 17:36:07.783063 Unknown 27  in lsass.exe(652): 
- 17:36:07.783311 Kernel-Network 13 KERNEL_NETWORK_TASK_TCPIP in lsass.exe(652): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49681; seqnum=       0; connid=       0
- 17:36:07.787528 Unknown 19  in lsass.exe(652): 
- 17:36:07.787537 Unknown 86  in lsass.exe(652): 
- 17:36:07.787539 Unknown 89  in lsass.exe(652): 
- 17:36:07.787540 Unknown 61  in lsass.exe(652): 
- 17:36:07.787544 Unknown 73  in lsass.exe(652): 
- 17:36:07.787544 Unknown 35  in lsass.exe(652): 
- 17:36:07.788408 Kernel-Network 12 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49682; mss=1460; sackopt=1; tsopt=0; wsopt=1; rcvwin= 2102400; rcvwinscale=8; sndwinscale=8; seqnum=       0; connid=       0
- 17:36:07.788423 Unknown 34  in lsass.exe(652): 
- 17:36:07.788430 Unknown 38  in lsass.exe(652): 
- 17:36:07.789463 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     321; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49682; startime=    7536; endtime=    7536; seqnum=       0; connid=       0
- 17:36:07.789466 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=    1708; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49682; seqnum=       0; connid=       0
- 17:36:07.789482 Unknown 43  in lsass.exe(652): 
- 17:36:07.789491 Unknown 90  in lsass.exe(652): 
- 17:36:07.789497 Unknown 12  in lsass.exe(652): 
- 17:36:07.789516 Unknown 148  in lsass.exe(652): 
- 17:36:07.789518 Unknown 68  in lsass.exe(652): 
- 17:36:07.789522 Unknown 26  in lsass.exe(652): 
- 17:36:07.789531 Unknown 10  in lsass.exe(652): 
- 17:36:07.789533 Unknown 181  in lsass.exe(652): 
- 17:36:07.789535 Unknown 155  in lsass.exe(652): 
- 17:36:07.789535 Unknown 77  in lsass.exe(652): 
- 17:36:07.789536 Unknown 78  in lsass.exe(652): 
- 17:36:07.789549 Unknown 220  in lsass.exe(652): 
- 17:36:07.789549 Unknown 221  in lsass.exe(652): 
- 17:36:07.789562 Unknown 61  in lsass.exe(652): 
- 17:36:07.789566 Unknown 73  in lsass.exe(652): 
- 17:36:07.789566 Unknown 35  in lsass.exe(652): 
- 17:36:07.789972 Kernel-Network 13 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49682; seqnum=       0; connid=       0
- 17:36:07.790039 Kernel-Network 12 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49683; mss=1460; sackopt=1; tsopt=0; wsopt=1; rcvwin= 2102400; rcvwinscale=8; sndwinscale=8; seqnum=       0; connid=       0
- 17:36:07.790120 Unknown 34  in lsass.exe(652): 
- 17:36:07.790132 Unknown 38  in lsass.exe(652): 
- 17:36:07.790378 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=    1751; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49683; startime=    7536; endtime=    7536; seqnum=       0; connid=       0
- 17:36:07.790838 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=    1687; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49683; seqnum=       0; connid=       0
- 17:36:07.790939 Unknown 43  in lsass.exe(652): 
- 17:36:07.790996 Unknown 186  in lsass.exe(652): 
- 17:36:07.791023 Unknown 118  in lsass.exe(652): 
- 17:36:07.791025 Unknown 120  in lsass.exe(652): 
- 17:36:07.791113 Kernel-Network 13 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49683; seqnum=       0; connid=       0
- 17:36:07.796036 Kernel-Process 2 ProcessStop in cmd.exe(1600)*: ProcessID=    1600; ProcessSequenceNumber=128; CreateTime=2026-10-12T17:36:07.724061800Z; ExitTime=2026-10-12T17:36:07.795994900Z; ExitCode=       0; TokenElevationType=       1; HandleCount=      47; CommitCharge=4390912; CommitPeak=4390912; CPUCycleCount=990

### share (pid 1364, exit 0)

- 17:36:11.775147 Kernel-Process 1 ProcessStart in cmd.exe(1364)*: ProcessID=    4224; ProcessSequenceNumber=132; CreateTime=2026-10-12T17:36:11.775112600Z; ParentProcessID=    1364; ParentProcessSequenceNumber=131; SessionID=       0; Flags=       0; ProcessTokenElevationType=       1; ProcessTokenIsElevated=       1; Mandat
- 17:36:11.797678 Kernel-Process 1 ProcessStart in cmd.exe(1364)*: ProcessID=    4488; ProcessSequenceNumber=133; CreateTime=2026-10-12T17:36:11.797661600Z; ParentProcessID=    1364; ParentProcessSequenceNumber=131; SessionID=       0; Flags=       0; ProcessTokenElevationType=       1; ProcessTokenIsElevated=       1; Mandat
- 17:36:11.811001 Unknown 25  in lsass.exe(652): 
- 17:36:11.811002 Unknown 27  in lsass.exe(652): 
- 17:36:11.811002 Unknown 14  in lsass.exe(652): 
- 17:36:11.811009 Unknown 10  in lsass.exe(652): 
- 17:36:11.811009 Unknown 40  in lsass.exe(652): 
- 17:36:11.811018 Unknown 13  in lsass.exe(652): 
- 17:36:11.812535 DNS-Client 3006  in svchost.exe(1160): QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=      28; QueryOptions=1208115200; IsNetworkQuery=       0; NetworkQueryIndex=       0; InterfaceIndex=       0; IsAsyncQuery=       0
- 17:36:11.812537 DNS-Client 3006  in svchost.exe(1160): QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=       1; QueryOptions=1207984128; IsNetworkQuery=       0; NetworkQueryIndex=       0; InterfaceIndex=       0; IsAsyncQuery=       0
- 17:36:11.812538 DNS-Client 3008  in svchost.exe(1160): QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=       1; QueryOptions=1207984128; QueryStatus=      87
- 17:36:11.812608 DNS-Client 3009  in svchost.exe(1160): QueryName=TIERGEN-DC.hq.tiergen.test; IsParallelNetworkQuery=       1; NetworkIndex=       0; InterfaceCount=       1; AdapterName=Ethernet 2; LocalAddress=fe80::6dda:5c79:96a0:d04d;10.10.0.21; DNSServerAddress=10.10.0.10
- 17:36:11.812615 DNS-Client 3016  in svchost.exe(1160): QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=       1; QueryOptions=2251801021800448; InterfaceIndex=       0
- 17:36:11.812619 DNS-Client 3018  in svchost.exe(1160): QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=       1; QueryOptions=2251801021800448; Status=       0; QueryResults=10.10.0.10;
- 17:36:11.812620 DNS-Client 3016  in svchost.exe(1160): QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=      28; QueryOptions=2251801021800448; InterfaceIndex=       0
- 17:36:11.812621 DNS-Client 3018  in svchost.exe(1160): QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=      28; QueryOptions=2251801021800448; Status=    9701
- 17:36:11.812641 DNS-Client 3008  in svchost.exe(1160): QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=      28; QueryOptions=2251801021800448; QueryStatus=       0; QueryResults=::ffff:10.10.0.10;
- 17:36:11.812971 SMBClient 30203  in System(4): RemoteAddressLength=      16; RemoteAddress=10.10.0.10:445; VcEndpoint=0xFFFFDC06BC441A30; Socket=0xFFFFDC06DF44D668; ConnectionType=       1
- 17:36:11.813374 Kernel-Network 12 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; mss=1460; sackopt=1; tsopt=0; wsopt=1; rcvwin= 2102400; rcvwinscale=8; sndwinscale=8; seqnum=       0; connid=       0
- 17:36:11.813981 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=      73; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7938; endtime=    7938; seqnum=       0; connid=       0
- 17:36:11.813987 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     252; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.814365 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     264; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7938; endtime=    7938; seqnum=       0; connid=       0
- 17:36:11.814369 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     336; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.814726 Unknown 102  in lsass.exe(652): 
- 17:36:11.814729 Unknown 116  in lsass.exe(652): 
- 17:36:11.814729 Unknown 117  in lsass.exe(652): 
- 17:36:11.814730 Unknown 102  in lsass.exe(652): 
- 17:36:11.814731 Unknown 31  in lsass.exe(652): 
- 17:36:11.814731 Unknown 116  in lsass.exe(652): 
- 17:36:11.814732 Unknown 117  in lsass.exe(652): 
- 17:36:11.814778 Unknown 23  in lsass.exe(652): 
- 17:36:11.814780 Unknown 17  in lsass.exe(652): 
- 17:36:11.814780 Unknown 18  in lsass.exe(652): 
- 17:36:11.814782 Unknown 19  in lsass.exe(652): 
- 17:36:11.814783 Unknown 63  in lsass.exe(652): 
- 17:36:11.814791 Unknown 18  in lsass.exe(652): 
- 17:36:11.814814 Unknown 28  in lsass.exe(652): 
- 17:36:11.814815 Unknown 74  in lsass.exe(652): 
- 17:36:11.814816 Unknown 77  in lsass.exe(652): 
- 17:36:11.814816 Unknown 20  in lsass.exe(652): 
- 17:36:11.814816 Unknown 92  in lsass.exe(652): 
- 17:36:11.814817 Unknown 93  in lsass.exe(652): 
- 17:36:11.814817 Unknown 97  in lsass.exe(652): 
- 17:36:11.814820 Unknown 45  in lsass.exe(652): 
- 17:36:11.814822 Unknown 26  in lsass.exe(652): 
- 17:36:11.814823 Unknown 33  in lsass.exe(652): 
- 17:36:11.814823 Unknown 18  in lsass.exe(652): 
- 17:36:11.814823 Unknown 11  in lsass.exe(652): 
- 17:36:11.814824 Unknown 17  in lsass.exe(652): 
- 17:36:11.814824 Unknown 18  in lsass.exe(652): 
- 17:36:11.814825 Unknown 19  in lsass.exe(652): 
- 17:36:11.814825 Unknown 203  in lsass.exe(652): 
- 17:36:11.814827 Unknown 46  in lsass.exe(652): 
- 17:36:11.814827 Unknown 47  in lsass.exe(652): 
- 17:36:11.814828 Unknown 48  in lsass.exe(652): 
- 17:36:11.814829 Unknown 59  in lsass.exe(652): 
- 17:36:11.814830 Unknown 60  in lsass.exe(652): 
- 17:36:11.814832 Unknown 26  in lsass.exe(652): 
- 17:36:11.814832 Unknown 27  in lsass.exe(652): 
- 17:36:11.814833 Unknown 19  in lsass.exe(652): 
- 17:36:11.814850 Unknown 86  in lsass.exe(652): 
- 17:36:11.814852 Unknown 89  in lsass.exe(652): 
- 17:36:11.814852 Unknown 61  in lsass.exe(652): 
- 17:36:11.814856 Unknown 73  in lsass.exe(652): 
- 17:36:11.814857 Unknown 35  in lsass.exe(652): 
- 17:36:11.815489 Kernel-Network 12 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49685; mss=1460; sackopt=1; tsopt=0; wsopt=1; rcvwin= 2102400; rcvwinscale=8; sndwinscale=8; seqnum=       0; connid=       0
- 17:36:11.815499 Unknown 34  in lsass.exe(652): 
- 17:36:11.815517 Unknown 38  in lsass.exe(652): 
- 17:36:11.816358 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     242; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49685; startime=    7938; endtime=    7938; seqnum=       0; connid=       0
- 17:36:11.816362 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     239; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49685; seqnum=       0; connid=       0
- 17:36:11.816370 Unknown 43  in lsass.exe(652): 
- 17:36:11.816384 Unknown 90  in lsass.exe(652): 
- 17:36:11.816386 Unknown 43  in lsass.exe(652): 
- 17:36:11.816387 Unknown 96  in lsass.exe(652): 
- 17:36:11.816391 Unknown 43  in lsass.exe(652): 
- 17:36:11.816391 Unknown 10  in lsass.exe(652): 
- 17:36:11.816392 Unknown 43  in lsass.exe(652): 
- 17:36:11.816392 Unknown 103  in lsass.exe(652): 
- 17:36:11.816396 Unknown 26  in lsass.exe(652): 
- 17:36:11.816396 Unknown 27  in lsass.exe(652): 
- 17:36:11.816399 Unknown 19  in lsass.exe(652): 
- 17:36:11.816424 Unknown 86  in lsass.exe(652): 
- 17:36:11.816426 Unknown 89  in lsass.exe(652): 
- 17:36:11.816427 Unknown 61  in lsass.exe(652): 
- 17:36:11.816431 Unknown 73  in lsass.exe(652): 
- 17:36:11.816431 Unknown 35  in lsass.exe(652): 
- 17:36:11.816496 Kernel-Network 13 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49685; seqnum=       0; connid=       0
- 17:36:11.816534 Kernel-Network 12 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49686; mss=1460; sackopt=1; tsopt=0; wsopt=1; rcvwin= 2102400; rcvwinscale=8; sndwinscale=8; seqnum=       0; connid=       0
- 17:36:11.816551 Unknown 34  in lsass.exe(652): 
- 17:36:11.816557 Unknown 38  in lsass.exe(652): 
- 17:36:11.816962 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     322; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49686; startime=    7938; endtime=    7938; seqnum=       0; connid=       0
- 17:36:11.816966 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=    1708; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49686; seqnum=       0; connid=       0
- 17:36:11.816981 Unknown 43  in lsass.exe(652): 
- 17:36:11.816997 Unknown 90  in lsass.exe(652): 
- 17:36:11.817004 Unknown 12  in lsass.exe(652): 
- 17:36:11.817029 Unknown 148  in lsass.exe(652): 
- 17:36:11.817031 Unknown 68  in lsass.exe(652): 
- 17:36:11.817034 Unknown 26  in lsass.exe(652): 
- 17:36:11.817043 Unknown 10  in lsass.exe(652): 
- 17:36:11.817044 Unknown 181  in lsass.exe(652): 
- 17:36:11.817046 Unknown 155  in lsass.exe(652): 
- 17:36:11.817046 Unknown 77  in lsass.exe(652): 
- 17:36:11.817048 Unknown 78  in lsass.exe(652): 
- 17:36:11.817068 Unknown 220  in lsass.exe(652): 
- 17:36:11.817068 Unknown 221  in lsass.exe(652): 
- 17:36:11.817076 Kernel-Network 13 KERNEL_NETWORK_TASK_TCPIP in lsass.exe(652): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49686; seqnum=       0; connid=       0
- 17:36:11.817090 Unknown 61  in lsass.exe(652): 
- 17:36:11.817094 Unknown 73  in lsass.exe(652): 
- 17:36:11.817094 Unknown 35  in lsass.exe(652): 
- 17:36:11.817197 Kernel-Network 12 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49687; mss=1460; sackopt=1; tsopt=0; wsopt=1; rcvwin= 2102400; rcvwinscale=8; sndwinscale=8; seqnum=       0; connid=       0
- 17:36:11.817204 Unknown 34  in lsass.exe(652): 
- 17:36:11.817209 Unknown 38  in lsass.exe(652): 
- 17:36:11.817239 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=    1751; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49687; startime=    7938; endtime=    7938; seqnum=       0; connid=       0
- 17:36:11.818042 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=    1687; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49687; seqnum=       0; connid=       0
- 17:36:11.818062 Unknown 43  in lsass.exe(652): 
- 17:36:11.818097 Unknown 186  in lsass.exe(652): 
- 17:36:11.818104 Unknown 106  in lsass.exe(652): 
- 17:36:11.818104 Unknown 56  in lsass.exe(652): 
- 17:36:11.818104 Unknown 41  in lsass.exe(652): 
- 17:36:11.818105 Unknown 26  in lsass.exe(652): 
- 17:36:11.818106 Unknown 155  in lsass.exe(652): 
- 17:36:11.818106 Unknown 77  in lsass.exe(652): 
- 17:36:11.818107 Unknown 78  in lsass.exe(652): 
- 17:36:11.818113 Unknown 220  in lsass.exe(652): 
- 17:36:11.818113 Unknown 221  in lsass.exe(652): 
- 17:36:11.818123 Kernel-Network 13 KERNEL_NETWORK_TASK_TCPIP in lsass.exe(652): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49687; seqnum=       0; connid=       0
- 17:36:11.818142 Unknown 61  in lsass.exe(652): 
- 17:36:11.818145 Unknown 73  in lsass.exe(652): 
- 17:36:11.818145 Unknown 35  in lsass.exe(652): 
- 17:36:11.818289 Kernel-Network 12 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49688; mss=1460; sackopt=1; tsopt=0; wsopt=1; rcvwin= 2102400; rcvwinscale=8; sndwinscale=8; seqnum=       0; connid=       0
- 17:36:11.818297 Unknown 34  in lsass.exe(652): 
- 17:36:11.818315 Unknown 38  in lsass.exe(652): 
- 17:36:11.818335 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=    1549; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49688; startime=    7938; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.818741 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=    1578; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49688; seqnum=       0; connid=       0
- 17:36:11.818758 Unknown 43  in lsass.exe(652): 
- 17:36:11.818793 Kernel-Network 13 KERNEL_NETWORK_TASK_TCPIP in lsass.exe(652): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49688; seqnum=       0; connid=       0
- 17:36:11.818820 Unknown 50  in lsass.exe(652): 
- 17:36:11.818821 Unknown 52  in lsass.exe(652): 
- 17:36:11.818822 Unknown 45  in lsass.exe(652): 
- 17:36:11.818824 Unknown 220  in lsass.exe(652): 
- 17:36:11.818824 Unknown 221  in lsass.exe(652): 
- 17:36:11.818847 Unknown 113  in lsass.exe(652): 
- 17:36:11.818847 Unknown 114  in lsass.exe(652): 
- 17:36:11.818879 SMBClient 30406  in System(4): Count=       0; Command=SESSION ; MessageId=2; SessionId=0; TreeId=       0; MidCharge=1; CreditRequested=33; SendLength=    3479; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.818909 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=    3483; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7939; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.819299 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     260; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.819349 Unknown 23  in lsass.exe(652): 
- 17:36:11.819350 Unknown 17  in lsass.exe(652): 
- 17:36:11.819351 Unknown 18  in lsass.exe(652): 
- 17:36:11.819352 Unknown 19  in lsass.exe(652): 
- 17:36:11.819352 Unknown 28  in lsass.exe(652): 
- 17:36:11.819365 Unknown 264  in lsass.exe(652): 
- 17:36:11.819367 Unknown 142  in lsass.exe(652): 
- 17:36:11.819368 Unknown 112  in lsass.exe(652): 
- 17:36:11.819368 Unknown 12  in lsass.exe(652): 
- 17:36:11.819368 Unknown 113  in lsass.exe(652): 
- 17:36:11.819368 Unknown 114  in lsass.exe(652): 
- 17:36:11.819451 SMBClient 30406  in System(4): Count=       0; Command=TRE_CONN; MessageId=3; SessionId=17592186044429; TreeId=       0; MidCharge=1; CreditRequested=1; SendLength=     138; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.819498 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     142; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7939; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.819502 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=      84; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.819518 SMBClient 30406  in System(4): Count=       0; Command=IOCTL   ; MessageId=4; SessionId=17592186044429; TreeId=       1; MidCharge=1; CreditRequested=1; SendLength=     120; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.819556 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     124; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7939; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.819559 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     420; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.819690 SMBClient 30406  in cmd.exe(1364)*: Count=       0; Command=IOCTL   ; MessageId=5; SessionId=17592186044429; TreeId=       1; MidCharge=1; CreditRequested=1; SendLength=     192; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.820652 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     196; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7939; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.820654 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=      76; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.820828 SMBClient 30406  in System(4): Count=       0; Command=TRE_CONN; MessageId=6; SessionId=17592186044429; TreeId=       0; MidCharge=1; CreditRequested=1; SendLength=     142; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.820893 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     146; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7939; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.820907 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=      84; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.821013 SMBClient 30406  in cmd.exe(1364)*: Count=       0; Command=CREATE  ; MessageId=7; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=1; SendLength=     176; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.821085 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     180; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7939; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.821087 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     244; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.821124 SMBClient 30406  in cmd.exe(1364)*: Count=       0; Command=QRY_INFO; MessageId=8; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=1; SendLength=     104; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.821151 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     108; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7939; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.821153 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     132; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.821176 SMBClient 30406  in cmd.exe(1364)*: Count=       0; Command=QRY_INFO; MessageId=9; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=0; SendLength=     112; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.821177 SMBClient 30406  in cmd.exe(1364)*: Count=       1; Command=QRY_INFO; MessageId=10; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=2; SendLength=     105; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.821212 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     221; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7939; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.821216 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     204; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.821232 SMBClient 30406  in cmd.exe(1364)*: Count=       0; Command=CLOSE   ; MessageId=11; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=1; SendLength=      88; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.821264 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=      92; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7939; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.821266 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     128; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.821359 SMBClient 30406  in cmd.exe(1364)*: Count=       0; Command=CREATE  ; MessageId=12; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=0; SendLength=     176; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.821360 SMBClient 30406  in cmd.exe(1364)*: Count=       1; Command=QRY_INFO; MessageId=13; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=2; SendLength=     104; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.821408 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     284; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7939; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.821412 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     372; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.821436 SMBClient 30406  in cmd.exe(1364)*: Count=       0; Command=QRY_INFO; MessageId=14; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=1; SendLength=     104; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.821473 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     108; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7939; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.821476 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     132; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.821487 SMBClient 30406  in cmd.exe(1364)*: Count=       0; Command=CLOSE   ; MessageId=15; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=1; SendLength=      88; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.821516 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=      92; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7939; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.821518 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     128; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.821575 SMBClient 30406  in cmd.exe(1364)*: Count=       0; Command=CREATE  ; MessageId=16; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=0; SendLength=     176; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.821575 SMBClient 30406  in cmd.exe(1364)*: Count=       1; Command=QRY_INFO; MessageId=17; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=2; SendLength=     104; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.821630 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     284; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7939; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.821633 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     372; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.821645 SMBClient 30406  in cmd.exe(1364)*: Count=       0; Command=QRY_INFO; MessageId=18; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=1; SendLength=     104; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.821673 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     108; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7939; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.821675 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     132; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.821685 SMBClient 30406  in cmd.exe(1364)*: Count=       0; Command=CLOSE   ; MessageId=19; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=1; SendLength=      88; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.821714 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=      92; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7939; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.821716 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     128; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.821822 SMBClient 30406  in cmd.exe(1364)*: Count=       0; Command=CREATE  ; MessageId=20; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=0; SendLength=     176; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.821823 SMBClient 30406  in cmd.exe(1364)*: Count=       1; Command=QRY_INFO; MessageId=21; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=2; SendLength=     104; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.821870 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     284; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7939; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.821873 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     372; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.821916 SMBClient 30406  in cmd.exe(1364)*: Count=       0; Command=CLOSE   ; MessageId=22; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=1; SendLength=      88; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.821951 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=      92; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7939; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.821953 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     128; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.822175 SMBClient 30406  in cmd.exe(1364)*: Count=       0; Command=CREATE  ; MessageId=23; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=1; SendLength=     252; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.822323 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     256; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7939; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.822326 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     324; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.822348 SMBClient 30406  in cmd.exe(1364)*: Count=       0; Command=QRY_INFO; MessageId=24; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=1; SendLength=     104; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.822396 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     108; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7939; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.822398 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     132; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.822415 SMBClient 30406  in cmd.exe(1364)*: Count=       0; Command=QRY_DIR ; MessageId=25; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=0; SendLength=     104; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.822415 SMBClient 30406  in cmd.exe(1364)*: Count=       1; Command=QRY_DIR ; MessageId=26; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=2; SendLength=      98; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.822455 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     206; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7939; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.822459 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     508; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.823164 SMBClient 30406  in cmd.exe(1364)*: Count=       0; Command=CREATE  ; MessageId=27; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=1; SendLength=     332; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.823362 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     336; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7939; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.823365 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     324; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.823386 SMBClient 30406  in cmd.exe(1364)*: Count=       0; Command=QRY_INFO; MessageId=28; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=1; SendLength=     104; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.823416 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     108; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7939; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.823418 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     132; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.823432 SMBClient 30406  in cmd.exe(1364)*: Count=       0; Command=IOCTL   ; MessageId=29; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=1; SendLength=     120; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.823465 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     124; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7939; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.823467 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     240; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.823507 SMBClient 30406  in cmd.exe(1364)*: Count=       0; Command=CLOSE   ; MessageId=30; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=1; SendLength=      88; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.823671 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=      92; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7939; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.823673 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     128; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.823785 SMBClient 30406  in cmd.exe(1364)*: Count=       0; Command=CREATE  ; MessageId=31; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=0; SendLength=     152; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.823786 SMBClient 30406  in cmd.exe(1364)*: Count=       1; Command=QRY_INFO; MessageId=32; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=2; SendLength=     104; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.823936 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     260; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7939; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.823940 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     292; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.824014 SMBClient 30406  in cmd.exe(1364)*: Count=       0; Command=CLOSE   ; MessageId=33; SessionId=17592186044429; TreeId=       5; MidCharge=1; CreditRequested=1; SendLength=      88; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:11.824069 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=      92; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    7939; endtime=    7939; seqnum=       0; connid=       0
- 17:36:11.824071 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     128; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:11.826585 Kernel-Process 2 ProcessStop in cmd.exe(1364)*: ProcessID=    1364; ProcessSequenceNumber=131; CreateTime=2026-10-12T17:36:11.755954900Z; ExitTime=2026-10-12T17:36:11.826532900Z; ExitCode=       0; TokenElevationType=       1; HandleCount=      48; CommitCharge=5095424; CommitPeak=5095424; CPUCycleCount=136
- 17:36:12.611596 DNS-Client 1015 DnsServerTimeout in svchost.exe(1160): QueryName=v10.events.data.microsoft.com; AddressLength=      16; Address=10.10.0.10:53
- 17:36:12.611603 DNS-Client 3010  in svchost.exe(1160): QueryName=v10.events.data.microsoft.com; QueryType=       1; DnsServerIpAddress=10.10.0.10
- 17:36:12.611618 Kernel-Network 42 KERNEL_NETWORK_TASK_UDPIP in svchost.exe(1160): PID=    1160; size=      47; daddr=10.10.0.10; saddr=10.10.0.21; dport=53; sport=50841; seqnum=       0; connid=       0

### resolve (pid 4904, exit 0)

- 17:36:15.804558 Kernel-Process 1 ProcessStart in cmd.exe(4904)*: ProcessID=    4968; ProcessSequenceNumber=135; CreateTime=2026-10-12T17:36:15.804539400Z; ParentProcessID=    4904; ParentProcessSequenceNumber=134; SessionID=       0; Flags=       0; ProcessTokenElevationType=       1; ProcessTokenIsElevated=       1; Mandat
- 17:36:15.833106 Kernel-Process 1 ProcessStart in cmd.exe(4904)*: ProcessID=    4440; ProcessSequenceNumber=136; CreateTime=2026-10-12T17:36:15.833090900Z; ParentProcessID=    4904; ParentProcessSequenceNumber=134; SessionID=       0; Flags=       0; ProcessTokenElevationType=       1; ProcessTokenIsElevated=       1; Mandat
- 17:36:15.873687 Kernel-Process 1 ProcessStart in cmd.exe(4904)*: ProcessID=    5044; ProcessSequenceNumber=137; CreateTime=2026-10-12T17:36:15.873672500Z; ParentProcessID=    4904; ParentProcessSequenceNumber=134; SessionID=       0; Flags=       0; ProcessTokenElevationType=       1; ProcessTokenIsElevated=       1; Mandat
- 17:36:15.885517 DNS-Client 3006  in PING.EXE(5044)*: QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=       1; QueryOptions=1073766400; IsNetworkQuery=       0; NetworkQueryIndex=       0; InterfaceIndex=       0; IsAsyncQuery=       0
- 17:36:15.885519 DNS-Client 3008  in PING.EXE(5044)*: QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=       1; QueryOptions=1073766400; QueryStatus=      87
- 17:36:15.885629 DNS-Client 3006  in PING.EXE(5044)*: QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=      28; QueryOptions=1073897472; IsNetworkQuery=       0; NetworkQueryIndex=       0; InterfaceIndex=       0; IsAsyncQuery=       0
- 17:36:15.886005 DNS-Client 3009  in svchost.exe(1160): QueryName=TIERGEN-DC.hq.tiergen.test; IsParallelNetworkQuery=       1; NetworkIndex=       0; InterfaceCount=       1; AdapterName=Ethernet 2; LocalAddress=fe80::6dda:5c79:96a0:d04d;10.10.0.21; DNSServerAddress=10.10.0.10
- 17:36:15.886012 DNS-Client 3016  in svchost.exe(1160): QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=       1; QueryOptions=2251800887582720; InterfaceIndex=       0
- 17:36:15.886211 DNS-Client 3018  in svchost.exe(1160): QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=       1; QueryOptions=2251800887582720; Status=    9701
- 17:36:15.886219 DNS-Client 3019  in svchost.exe(1160): QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=       1; InterfaceIndex=       0; NetworkIndex=       0
- 17:36:15.886222 DNS-Client 3010  in svchost.exe(1160): QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=       1; DnsServerIpAddress=10.10.0.10
- 17:36:15.886280 Kernel-Network 42 KERNEL_NETWORK_TASK_UDPIP in svchost.exe(1160): PID=    1160; size=      44; daddr=10.10.0.10; saddr=10.10.0.21; dport=53; sport=60090; seqnum=       0; connid=       0
- 17:36:15.887230 DNS-Client 3011  in svchost.exe(1160): QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=       1; DnsServerIpAddress=10.10.0.10; ResponseStatus=       0
- 17:36:15.887245 DNS-Client 3020  in svchost.exe(1160): QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=       1; NetworkIndex=       0; InterfaceIndex=       0; Status=       0; QueryResults=10.10.0.10;
- 17:36:15.887247 DNS-Client 3016  in svchost.exe(1160): QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=      28; QueryOptions=2251800888107008; InterfaceIndex=       0
- 17:36:15.887248 DNS-Client 3018  in svchost.exe(1160): QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=      28; QueryOptions=2251800888107008; Status=    9701
- 17:36:15.887279 DNS-Client 3008  in PING.EXE(5044)*: QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=      28; QueryOptions=2251800887582720; QueryStatus=       0; QueryResults=::ffff:10.10.0.10;
- 17:36:15.895640 Kernel-Process 2 ProcessStop in cmd.exe(4904)*: ProcessID=    4904; ProcessSequenceNumber=134; CreateTime=2026-10-12T17:36:15.786826000Z; ExitTime=2026-10-12T17:36:15.895596100Z; ExitCode=       0; TokenElevationType=       1; HandleCount=      47; CommitCharge=4513792; CommitPeak=4513792; CPUCycleCount=117

### user (pid 520, exit 0)

- 17:36:17.399861 LsaSrv 6225 LSA Logon  in lsass.exe(652): 
- 17:36:17.400004 LsaSrv 300  in lsass.exe(652): TargetUserSid=S-1-5-20; TargetUserName=NETWORK SERVICE; TargetDomainName=NT AUTHORITY; TargetLogonId=0x3E4; TargetLogonGuid={00000000-0000-0000-0000-000000000000}; EventOrginal=       1; EventCountTotal=       1; SidList=
		%{S-1-5-20}
		%{S-1-1-0}
		%{S-1-5-3
- 17:36:17.400011 Unknown 308  in lsass.exe(652): 
- 17:36:17.400038 LsaSrv 6226 LSA Logon  in lsass.exe(652): 
- 17:36:17.490055 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     168; daddr=10.10.0.10; saddr=10.10.0.21; dport=135; sport=49674; startime=    8506; endtime=    8506; seqnum=       0; connid=       0
- 17:36:17.490062 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     268; daddr=10.10.0.10; saddr=10.10.0.21; dport=135; sport=49674; seqnum=       0; connid=       0
- 17:36:17.490100 DNS-Client 3006  in lsass.exe(652): QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=       1; QueryOptions=1073766400; IsNetworkQuery=       0; NetworkQueryIndex=       0; InterfaceIndex=       0; IsAsyncQuery=       0
- 17:36:17.490102 DNS-Client 3008  in lsass.exe(652): QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=       1; QueryOptions=1073766400; QueryStatus=      87
- 17:36:17.490109 DNS-Client 3006  in lsass.exe(652): QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=      28; QueryOptions=1073897472; IsNetworkQuery=       0; NetworkQueryIndex=       0; InterfaceIndex=       0; IsAsyncQuery=       0
- 17:36:17.490167 DNS-Client 3009  in svchost.exe(1160): QueryName=TIERGEN-DC.hq.tiergen.test; IsParallelNetworkQuery=       1; NetworkIndex=       0; InterfaceCount=       1; AdapterName=Ethernet 2; LocalAddress=fe80::6dda:5c79:96a0:d04d;10.10.0.21; DNSServerAddress=10.10.0.10
- 17:36:17.490172 DNS-Client 3016  in svchost.exe(1160): QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=       1; QueryOptions=2251800887582720; InterfaceIndex=       0
- 17:36:17.490177 DNS-Client 3018  in svchost.exe(1160): QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=       1; QueryOptions=2251800887582720; Status=       0; QueryResults=10.10.0.10;
- 17:36:17.490177 DNS-Client 3016  in svchost.exe(1160): QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=      28; QueryOptions=2251800887582720; InterfaceIndex=       0
- 17:36:17.490178 DNS-Client 3018  in svchost.exe(1160): QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=      28; QueryOptions=2251800887582720; Status=    9701
- 17:36:17.490261 DNS-Client 3008  in lsass.exe(652): QueryName=TIERGEN-DC.hq.tiergen.test; QueryType=      28; QueryOptions=2251800887582720; QueryStatus=       0; QueryResults=::ffff:10.10.0.10;
- 17:36:17.491015 Kernel-Network 12 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=49667; sport=49689; mss=1460; sackopt=1; tsopt=0; wsopt=1; rcvwin= 2102400; rcvwinscale=8; sndwinscale=8; seqnum=       0; connid=       0
- 17:36:17.491928 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     219; daddr=10.10.0.10; saddr=10.10.0.21; dport=49667; sport=49689; startime=    8506; endtime=    8506; seqnum=       0; connid=       0
- 17:36:17.491931 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     128; daddr=10.10.0.10; saddr=10.10.0.21; dport=49667; sport=49689; seqnum=       0; connid=       0
- 17:36:17.494703 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     296; daddr=10.10.0.10; saddr=10.10.0.21; dport=49667; sport=49689; startime=    8506; endtime=    8506; seqnum=       0; connid=       0
- 17:36:17.494715 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     312; daddr=10.10.0.10; saddr=10.10.0.21; dport=49667; sport=49689; seqnum=       0; connid=       0
- 17:36:17.496196 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     131; daddr=10.10.0.10; saddr=10.10.0.21; dport=49667; sport=49689; startime=    8506; endtime=    8506; seqnum=       0; connid=       0
- 17:36:17.496210 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=      76; daddr=10.10.0.10; saddr=10.10.0.21; dport=49667; sport=49689; seqnum=       0; connid=       0
- 17:36:17.496860 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     200; daddr=10.10.0.10; saddr=10.10.0.21; dport=49667; sport=49689; startime=    8506; endtime=    8506; seqnum=       0; connid=       0
- 17:36:17.496874 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     344; daddr=10.10.0.10; saddr=10.10.0.21; dport=49667; sport=49689; seqnum=       0; connid=       0
- 17:36:17.497297 LsaSrv 6225 LSA Logon  in lsass.exe(652): 
- 17:36:17.497815 Unknown 258  in lsass.exe(652): 
- 17:36:17.497818 Unknown 41  in lsass.exe(652): 
- 17:36:17.499007 Unknown 15  in lsass.exe(652): 
- 17:36:17.499007 Unknown 42  in lsass.exe(652): 
- 17:36:17.499008 Unknown 278  in lsass.exe(652): 
- 17:36:17.499019 Unknown 17  in lsass.exe(652): 
- 17:36:17.499019 Unknown 18  in lsass.exe(652): 
- 17:36:17.499020 Unknown 19  in lsass.exe(652): 
- 17:36:17.499021 Unknown 203  in lsass.exe(652): 
- 17:36:17.499022 Unknown 46  in lsass.exe(652): 
- 17:36:17.499022 Unknown 47  in lsass.exe(652): 
- 17:36:17.499023 Unknown 48  in lsass.exe(652): 
- 17:36:17.499024 Unknown 59  in lsass.exe(652): 
- 17:36:17.499025 Unknown 60  in lsass.exe(652): 
- 17:36:17.499027 Unknown 26  in lsass.exe(652): 
- 17:36:17.499027 Unknown 27  in lsass.exe(652): 
- 17:36:17.499028 Unknown 19  in lsass.exe(652): 
- 17:36:17.499035 Unknown 86  in lsass.exe(652): 
- 17:36:17.499039 Unknown 89  in lsass.exe(652): 
- 17:36:17.499039 Unknown 61  in lsass.exe(652): 
- 17:36:17.499050 DNS-Client 3006  in lsass.exe(652): QueryType=       1; QueryOptions=140737488355328; IsNetworkQuery=       0; NetworkQueryIndex=       0; InterfaceIndex=       0; IsAsyncQuery=       0
- 17:36:17.499104 DNS-Client 3008  in lsass.exe(652): QueryName=TIERGEN-WS; QueryType=       1; QueryOptions=140737488355328; QueryStatus=       0; QueryResults=10.10.0.21;
- 17:36:17.499145 Unknown 17  in lsass.exe(652): 
- 17:36:17.499146 Unknown 19  in lsass.exe(652): 
- 17:36:17.499147 Unknown 73  in lsass.exe(652): 
- 17:36:17.499147 Unknown 35  in lsass.exe(652): 
- 17:36:17.499835 Kernel-Network 12 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49690; mss=1460; sackopt=1; tsopt=0; wsopt=1; rcvwin=  262800; rcvwinscale=8; sndwinscale=8; seqnum=       0; connid=       0
- 17:36:17.499843 Unknown 34  in lsass.exe(652): 
- 17:36:17.499848 Unknown 38  in lsass.exe(652): 
- 17:36:17.500778 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     217; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49690; startime=    8506; endtime=    8507; seqnum=       0; connid=       0
- 17:36:17.500783 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     175; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49690; seqnum=       0; connid=       0
- 17:36:17.500792 Unknown 43  in lsass.exe(652): 
- 17:36:17.500802 Unknown 90  in lsass.exe(652): 
- 17:36:17.500804 Unknown 43  in lsass.exe(652): 
- 17:36:17.500805 Unknown 96  in lsass.exe(652): 
- 17:36:17.500809 Unknown 43  in lsass.exe(652): 
- 17:36:17.500810 Unknown 10  in lsass.exe(652): 
- 17:36:17.500810 Unknown 43  in lsass.exe(652): 
- 17:36:17.500810 Unknown 103  in lsass.exe(652): 
- 17:36:17.500815 Unknown 26  in lsass.exe(652): 
- 17:36:17.500815 Unknown 27  in lsass.exe(652): 
- 17:36:17.501294 Kernel-Network 13 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49690; seqnum=       0; connid=       0
- 17:36:17.503525 Unknown 19  in lsass.exe(652): 
- 17:36:17.503537 Unknown 86  in lsass.exe(652): 
- 17:36:17.503540 Unknown 89  in lsass.exe(652): 
- 17:36:17.503541 Unknown 61  in lsass.exe(652): 
- 17:36:17.503545 Unknown 73  in lsass.exe(652): 
- 17:36:17.503545 Unknown 35  in lsass.exe(652): 
- 17:36:17.504194 Kernel-Network 12 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49691; mss=1460; sackopt=1; tsopt=0; wsopt=1; rcvwin= 2102400; rcvwinscale=8; sndwinscale=8; seqnum=       0; connid=       0
- 17:36:17.504205 Unknown 34  in lsass.exe(652): 
- 17:36:17.504208 Unknown 38  in lsass.exe(652): 
- 17:36:17.505132 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     297; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49691; startime=    8507; endtime=    8507; seqnum=       0; connid=       0
- 17:36:17.505133 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=    1754; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49691; seqnum=       0; connid=       0
- 17:36:17.505141 Unknown 43  in lsass.exe(652): 
- 17:36:17.505146 Unknown 90  in lsass.exe(652): 
- 17:36:17.505152 Unknown 12  in lsass.exe(652): 
- 17:36:17.505184 Unknown 148  in lsass.exe(652): 
- 17:36:17.505185 Unknown 313  in lsass.exe(652): 
- 17:36:17.505185 Unknown 68  in lsass.exe(652): 
- 17:36:17.505186 Unknown 69  in lsass.exe(652): 
- 17:36:17.505189 Unknown 26  in lsass.exe(652): 
- 17:36:17.505196 Unknown 283  in lsass.exe(652): 
- 17:36:17.505197 Unknown 26  in lsass.exe(652): 
- 17:36:17.505199 Unknown 181  in lsass.exe(652): 
- 17:36:17.505213 Unknown 155  in lsass.exe(652): 
- 17:36:17.505213 Unknown 77  in lsass.exe(652): 
- 17:36:17.505214 Unknown 78  in lsass.exe(652): 
- 17:36:17.505221 Unknown 220  in lsass.exe(652): 
- 17:36:17.505221 Unknown 221  in lsass.exe(652): 
- 17:36:17.505239 Unknown 61  in lsass.exe(652): 
- 17:36:17.505243 Unknown 73  in lsass.exe(652): 
- 17:36:17.505243 Unknown 35  in lsass.exe(652): 
- 17:36:17.505332 Kernel-Network 13 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49691; seqnum=       0; connid=       0
- 17:36:17.505439 Kernel-Network 12 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49692; mss=1460; sackopt=1; tsopt=0; wsopt=1; rcvwin= 2102400; rcvwinscale=8; sndwinscale=8; seqnum=       0; connid=       0
- 17:36:17.505445 Unknown 34  in lsass.exe(652): 
- 17:36:17.505449 Unknown 38  in lsass.exe(652): 
- 17:36:17.505632 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=    1662; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49692; startime=    8507; endtime=    8507; seqnum=       0; connid=       0
- 17:36:17.506324 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=    1689; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49692; seqnum=       0; connid=       0
- 17:36:17.506331 Unknown 43  in lsass.exe(652): 
- 17:36:17.506377 Unknown 186  in lsass.exe(652): 
- 17:36:17.506386 Unknown 91  in lsass.exe(652): 
- 17:36:17.506416 Unknown 36  in lsass.exe(652): 
- 17:36:17.506416 Unknown 37  in lsass.exe(652): 
- 17:36:17.506457 Kernel-Network 13 KERNEL_NETWORK_TASK_TCPIP in lsass.exe(652): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49692; seqnum=       0; connid=       0
- 17:36:17.506486 Unknown 46  in lsass.exe(652): 
- 17:36:17.506677 Unknown 11  in lsass.exe(652): 
- 17:36:17.506684 Unknown 79  in lsass.exe(652): 
- 17:36:17.510207 Unknown 295  in lsass.exe(652): 
- 17:36:17.510208 Unknown 297  in lsass.exe(652): 
- 17:36:17.510208 Unknown 298  in lsass.exe(652): 
- 17:36:17.510332 LsaSrv 300  in lsass.exe(652): TargetUserSid=S-1-5-21-2921435408-891897996-1317750820-500; TargetUserName=Administrator; TargetDomainName=HQ; TargetLogonId=0x56183; TargetLogonGuid={6a41e65e-63d0-1723-05bc-2a3a14c8233e}; EventOrginal=       1; EventCountTotal=       1; SidList=
		%{S-1-5-21
- 17:36:17.510349 Unknown 57  in lsass.exe(652): 
- 17:36:17.510349 Unknown 58  in lsass.exe(652): 
- 17:36:17.510350 Unknown 99  in lsass.exe(652): 
- 17:36:17.512224 LsaSrv 303  in lsass.exe(652): PackageName=CREDSSP; UserName=Administrator; DomainName=HQ; ProtectedUser=       0
- 17:36:17.512228 LsaSrv 303  in lsass.exe(652): PackageName=WDigest; UserName=Administrator; DomainName=HQ; ProtectedUser=       0
- 17:36:17.512231 Unknown 308  in lsass.exe(652): 
- 17:36:17.512232 Unknown 310  in lsass.exe(652): 
- 17:36:17.512232 Unknown 68  in lsass.exe(652): 
- 17:36:17.512700 LsaSrv 6226 LSA Logon  in lsass.exe(652): 
- 17:36:17.520113 Unknown 57  in lsass.exe(652): 
- 17:36:17.520114 Unknown 58  in lsass.exe(652): 
- 17:36:17.522732 Unknown 38  in lsass.exe(652): 
- 17:36:17.522734 Unknown 99  in lsass.exe(652): 
- 17:36:17.522768 LsaSrv 303  in lsass.exe(652): PackageName=CREDSSP; UserName=Administrator; DomainName=HQ; ProtectedUser=       0
- 17:36:17.522771 LsaSrv 303  in lsass.exe(652): PackageName=WDigest; UserName=Administrator; DomainName=HQ; ProtectedUser=       0
- 17:36:17.524234 Unknown 307  in lsass.exe(652): 
- 17:36:17.524234 Unknown 17  in lsass.exe(652): 
- 17:36:17.524235 Unknown 18  in lsass.exe(652): 
- 17:36:17.524236 Unknown 40  in lsass.exe(652): 
- 17:36:17.524242 Unknown 13  in lsass.exe(652): 
- 17:36:17.581331 LsaSrv 6225 LSA Logon  in lsass.exe(652): 
- 17:36:17.581410 Unknown 257  in lsass.exe(652): 
- 17:36:17.581411 Unknown 258  in lsass.exe(652): 
- 17:36:17.581412 Unknown 41  in lsass.exe(652): 
- 17:36:17.582072 Unknown 15  in lsass.exe(652): 
- 17:36:17.582072 Unknown 42  in lsass.exe(652): 
- 17:36:17.582073 Unknown 278  in lsass.exe(652): 
- 17:36:17.582075 Unknown 17  in lsass.exe(652): 
- 17:36:17.582075 Unknown 18  in lsass.exe(652): 
- 17:36:17.582076 Unknown 19  in lsass.exe(652): 
- 17:36:17.582077 Unknown 203  in lsass.exe(652): 
- 17:36:17.582078 Unknown 46  in lsass.exe(652): 
- 17:36:17.582078 Unknown 47  in lsass.exe(652): 
- 17:36:17.582079 Unknown 48  in lsass.exe(652): 
- 17:36:17.582080 Unknown 59  in lsass.exe(652): 
- 17:36:17.582080 Unknown 60  in lsass.exe(652): 
- 17:36:17.582083 Unknown 26  in lsass.exe(652): 
- 17:36:17.582083 Unknown 27  in lsass.exe(652): 
- 17:36:17.582083 Unknown 19  in lsass.exe(652): 
- 17:36:17.582085 Unknown 86  in lsass.exe(652): 
- 17:36:17.582089 Unknown 89  in lsass.exe(652): 
- 17:36:17.582089 Unknown 61  in lsass.exe(652): 
- 17:36:17.582093 Unknown 73  in lsass.exe(652): 
- 17:36:17.582094 Unknown 35  in lsass.exe(652): 
- 17:36:17.582916 Kernel-Network 12 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49693; mss=1460; sackopt=1; tsopt=0; wsopt=1; rcvwin= 2102400; rcvwinscale=8; sndwinscale=8; seqnum=       0; connid=       0
- 17:36:17.582932 Unknown 34  in lsass.exe(652): 
- 17:36:17.582938 Unknown 38  in lsass.exe(652): 
- 17:36:17.584264 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     217; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49693; startime=    8515; endtime=    8515; seqnum=       0; connid=       0
- 17:36:17.584268 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     175; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49693; seqnum=       0; connid=       0
- 17:36:17.584282 Unknown 43  in lsass.exe(652): 
- 17:36:17.584297 Unknown 90  in lsass.exe(652): 
- 17:36:17.584300 Unknown 43  in lsass.exe(652): 
- 17:36:17.584300 Unknown 96  in lsass.exe(652): 
- 17:36:17.584305 Unknown 43  in lsass.exe(652): 
- 17:36:17.584305 Unknown 10  in lsass.exe(652): 
- 17:36:17.584306 Unknown 43  in lsass.exe(652): 
- 17:36:17.584306 Unknown 103  in lsass.exe(652): 
- 17:36:17.584314 Unknown 26  in lsass.exe(652): 
- 17:36:17.584314 Unknown 27  in lsass.exe(652): 
- 17:36:17.584656 Kernel-Network 13 KERNEL_NETWORK_TASK_TCPIP in lsass.exe(652): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49693; seqnum=       0; connid=       0
- 17:36:17.586982 Unknown 19  in lsass.exe(652): 
- 17:36:17.586993 Unknown 86  in lsass.exe(652): 
- 17:36:17.586995 Unknown 89  in lsass.exe(652): 
- 17:36:17.586996 Unknown 61  in lsass.exe(652): 
- 17:36:17.586999 Unknown 73  in lsass.exe(652): 
- 17:36:17.587000 Unknown 35  in lsass.exe(652): 
- 17:36:17.587640 Kernel-Network 12 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49694; mss=1460; sackopt=1; tsopt=0; wsopt=1; rcvwin=  262800; rcvwinscale=8; sndwinscale=8; seqnum=       0; connid=       0
- 17:36:17.587766 Unknown 34  in lsass.exe(652): 
- 17:36:17.587779 Unknown 38  in lsass.exe(652): 
- 17:36:17.588527 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     297; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49694; startime=    8515; endtime=    8516; seqnum=       0; connid=       0
- 17:36:17.588532 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=    1754; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49694; seqnum=       0; connid=       0
- 17:36:17.588598 Unknown 43  in lsass.exe(652): 
- 17:36:17.588626 Unknown 90  in lsass.exe(652): 
- 17:36:17.588633 Unknown 12  in lsass.exe(652): 
- 17:36:17.588653 Unknown 148  in lsass.exe(652): 
- 17:36:17.588654 Unknown 313  in lsass.exe(652): 
- 17:36:17.588655 Unknown 68  in lsass.exe(652): 
- 17:36:17.588655 Unknown 69  in lsass.exe(652): 
- 17:36:17.588659 Unknown 26  in lsass.exe(652): 
- 17:36:17.588679 Unknown 283  in lsass.exe(652): 
- 17:36:17.588681 Unknown 26  in lsass.exe(652): 
- 17:36:17.588682 Unknown 181  in lsass.exe(652): 
- 17:36:17.588684 Unknown 155  in lsass.exe(652): 
- 17:36:17.588684 Unknown 77  in lsass.exe(652): 
- 17:36:17.588685 Unknown 78  in lsass.exe(652): 
- 17:36:17.588693 Unknown 220  in lsass.exe(652): 
- 17:36:17.588693 Unknown 221  in lsass.exe(652): 
- 17:36:17.588706 Unknown 61  in lsass.exe(652): 
- 17:36:17.588709 Unknown 73  in lsass.exe(652): 
- 17:36:17.588709 Unknown 35  in lsass.exe(652): 
- 17:36:17.588955 Kernel-Network 13 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49694; seqnum=       0; connid=       0
- 17:36:17.589016 Kernel-Network 12 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49695; mss=1460; sackopt=1; tsopt=0; wsopt=1; rcvwin=  262800; rcvwinscale=8; sndwinscale=8; seqnum=       0; connid=       0
- 17:36:17.589024 Unknown 34  in lsass.exe(652): 
- 17:36:17.589030 Unknown 38  in lsass.exe(652): 
- 17:36:17.589236 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=    1662; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49695; startime=    8516; endtime=    8516; seqnum=       0; connid=       0
- 17:36:17.590065 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=    1689; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49695; seqnum=       0; connid=       0
- 17:36:17.590081 Unknown 43  in lsass.exe(652): 
- 17:36:17.590124 Unknown 186  in lsass.exe(652): 
- 17:36:17.590131 Unknown 91  in lsass.exe(652): 
- 17:36:17.590147 Unknown 36  in lsass.exe(652): 
- 17:36:17.590156 Unknown 37  in lsass.exe(652): 
- 17:36:17.590166 Kernel-Network 13 KERNEL_NETWORK_TASK_TCPIP in lsass.exe(652): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49695; seqnum=       0; connid=       0
- 17:36:17.590203 Unknown 46  in lsass.exe(652): 
- 17:36:17.590219 Unknown 11  in lsass.exe(652): 
- 17:36:17.590222 Unknown 79  in lsass.exe(652): 
- 17:36:17.593524 Unknown 295  in lsass.exe(652): 
- 17:36:17.593524 Unknown 297  in lsass.exe(652): 
- 17:36:17.593524 Unknown 298  in lsass.exe(652): 
- 17:36:17.593623 LsaSrv 300  in lsass.exe(652): TargetUserSid=S-1-5-21-2921435408-891897996-1317750820-500; TargetUserName=Administrator; TargetDomainName=HQ; TargetLogonId=0x56443; TargetLogonGuid={6a41e65e-63d0-1723-05bc-2a3a14c8233e}; EventOrginal=       1; EventCountTotal=       1; SidList=
		%{S-1-5-21
- 17:36:17.593640 Unknown 57  in lsass.exe(652): 
- 17:36:17.593640 Unknown 58  in lsass.exe(652): 
- 17:36:17.593641 Unknown 99  in lsass.exe(652): 
- 17:36:17.595425 LsaSrv 303  in lsass.exe(652): PackageName=CREDSSP; UserName=Administrator; DomainName=HQ; ProtectedUser=       0
- 17:36:17.595428 LsaSrv 303  in lsass.exe(652): PackageName=WDigest; UserName=Administrator; DomainName=HQ; ProtectedUser=       0
- 17:36:17.595432 Unknown 308  in lsass.exe(652): 
- 17:36:17.595432 Unknown 310  in lsass.exe(652): 
- 17:36:17.595432 Unknown 68  in lsass.exe(652): 
- 17:36:17.595541 LsaSrv 6226 LSA Logon  in lsass.exe(652): 
- 17:36:17.595752 LsaSrv 6225 LSA Logon  in lsass.exe(652): 
- 17:36:17.595798 Unknown 257  in lsass.exe(652): 
- 17:36:17.595799 Unknown 258  in lsass.exe(652): 
- 17:36:17.595799 Unknown 41  in lsass.exe(652): 
- 17:36:17.596363 Unknown 15  in lsass.exe(652): 
- 17:36:17.596364 Unknown 42  in lsass.exe(652): 
- 17:36:17.596364 Unknown 278  in lsass.exe(652): 
- 17:36:17.596366 Unknown 17  in lsass.exe(652): 
- 17:36:17.596366 Unknown 18  in lsass.exe(652): 
- 17:36:17.596367 Unknown 19  in lsass.exe(652): 
- 17:36:17.596367 Unknown 203  in lsass.exe(652): 
- 17:36:17.596368 Unknown 46  in lsass.exe(652): 
- 17:36:17.596369 Unknown 47  in lsass.exe(652): 
- 17:36:17.596369 Unknown 48  in lsass.exe(652): 
- 17:36:17.596370 Unknown 59  in lsass.exe(652): 
- 17:36:17.596371 Unknown 60  in lsass.exe(652): 
- 17:36:17.596373 Unknown 26  in lsass.exe(652): 
- 17:36:17.596373 Unknown 27  in lsass.exe(652): 
- 17:36:17.596373 Unknown 19  in lsass.exe(652): 
- 17:36:17.596375 Unknown 86  in lsass.exe(652): 
- 17:36:17.596378 Unknown 89  in lsass.exe(652): 
- 17:36:17.596378 Unknown 61  in lsass.exe(652): 
- 17:36:17.596381 Unknown 73  in lsass.exe(652): 
- 17:36:17.596381 Unknown 35  in lsass.exe(652): 
- 17:36:17.596804 Kernel-Network 12 KERNEL_NETWORK_TASK_TCPIP in powershell.exe(4376): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49696; mss=1460; sackopt=1; tsopt=0; wsopt=1; rcvwin=  262800; rcvwinscale=8; sndwinscale=8; seqnum=       0; connid=       0
- 17:36:17.596816 Unknown 34  in lsass.exe(652): 
- 17:36:17.596821 Unknown 38  in lsass.exe(652): 
- 17:36:17.597701 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     217; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49696; startime=    8516; endtime=    8516; seqnum=       0; connid=       0
- 17:36:17.597704 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     175; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49696; seqnum=       0; connid=       0
- 17:36:17.597716 Unknown 43  in lsass.exe(652): 
- 17:36:17.597731 Unknown 90  in lsass.exe(652): 
- 17:36:17.597732 Unknown 43  in lsass.exe(652): 
- 17:36:17.597732 Unknown 96  in lsass.exe(652): 
- 17:36:17.597736 Unknown 43  in lsass.exe(652): 
- 17:36:17.597737 Unknown 10  in lsass.exe(652): 
- 17:36:17.597737 Unknown 43  in lsass.exe(652): 
- 17:36:17.597737 Unknown 103  in lsass.exe(652): 
- 17:36:17.597741 Unknown 26  in lsass.exe(652): 
- 17:36:17.597741 Unknown 27  in lsass.exe(652): 
- 17:36:17.597988 Kernel-Network 13 KERNEL_NETWORK_TASK_TCPIP in lsass.exe(652): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49696; seqnum=       0; connid=       0
- 17:36:17.600456 Unknown 19  in lsass.exe(652): 
- 17:36:17.600466 Unknown 86  in lsass.exe(652): 
- 17:36:17.600468 Unknown 89  in lsass.exe(652): 
- 17:36:17.600469 Unknown 61  in lsass.exe(652): 
- 17:36:17.600472 Unknown 73  in lsass.exe(652): 
- 17:36:17.600472 Unknown 35  in lsass.exe(652): 
- 17:36:17.600799 Kernel-Network 12 KERNEL_NETWORK_TASK_TCPIP in lsass.exe(652): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49697; mss=1460; sackopt=1; tsopt=0; wsopt=1; rcvwin=  262800; rcvwinscale=8; sndwinscale=8; seqnum=       0; connid=       0
- 17:36:17.600806 Unknown 34  in lsass.exe(652): 
- 17:36:17.600815 Unknown 38  in lsass.exe(652): 
- 17:36:17.601061 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in lsass.exe(652): PID=     652; size=     297; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49697; startime=    8516; endtime=    8517; seqnum=       0; connid=       0
- 17:36:17.601537 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in lsass.exe(652): PID=     652; size=    1754; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49697; seqnum=       0; connid=       0
- 17:36:17.601544 Unknown 43  in lsass.exe(652): 
- 17:36:17.601558 Unknown 90  in lsass.exe(652): 
- 17:36:17.601563 Unknown 12  in lsass.exe(652): 
- 17:36:17.601581 Unknown 148  in lsass.exe(652): 
- 17:36:17.601582 Unknown 313  in lsass.exe(652): 
- 17:36:17.601583 Unknown 68  in lsass.exe(652): 
- 17:36:17.601583 Unknown 69  in lsass.exe(652): 
- 17:36:17.601586 Unknown 26  in lsass.exe(652): 
- 17:36:17.601600 Unknown 283  in lsass.exe(652): 
- 17:36:17.601601 Unknown 26  in lsass.exe(652): 
- 17:36:17.601602 Unknown 181  in lsass.exe(652): 
- 17:36:17.601604 Unknown 155  in lsass.exe(652): 
- 17:36:17.601604 Unknown 77  in lsass.exe(652): 
- 17:36:17.601605 Unknown 78  in lsass.exe(652): 
- 17:36:17.601612 Unknown 220  in lsass.exe(652): 
- 17:36:17.601612 Unknown 221  in lsass.exe(652): 
- 17:36:17.601624 Unknown 61  in lsass.exe(652): 
- 17:36:17.601627 Unknown 73  in lsass.exe(652): 
- 17:36:17.601627 Unknown 35  in lsass.exe(652): 
- 17:36:17.601726 Kernel-Network 13 KERNEL_NETWORK_TASK_TCPIP in lsass.exe(652): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49697; seqnum=       0; connid=       0
- 17:36:17.601826 Kernel-Network 12 KERNEL_NETWORK_TASK_TCPIP in lsass.exe(652): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49698; mss=1460; sackopt=1; tsopt=0; wsopt=1; rcvwin=  262800; rcvwinscale=8; sndwinscale=8; seqnum=       0; connid=       0
- 17:36:17.601881 Unknown 34  in lsass.exe(652): 
- 17:36:17.601890 Unknown 38  in lsass.exe(652): 
- 17:36:17.602050 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in lsass.exe(652): PID=     652; size=    1662; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49698; startime=    8517; endtime=    8517; seqnum=       0; connid=       0
- 17:36:17.602774 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in lsass.exe(652): PID=     652; size=    1689; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49698; seqnum=       0; connid=       0
- 17:36:17.602822 Unknown 43  in lsass.exe(652): 
- 17:36:17.602868 Unknown 186  in lsass.exe(652): 
- 17:36:17.602875 Unknown 91  in lsass.exe(652): 
- 17:36:17.602890 Unknown 36  in lsass.exe(652): 
- 17:36:17.602891 Unknown 37  in lsass.exe(652): 
- 17:36:17.602926 Unknown 46  in lsass.exe(652): 
- 17:36:17.602944 Unknown 11  in lsass.exe(652): 
- 17:36:17.602947 Unknown 79  in lsass.exe(652): 
- 17:36:17.603144 Kernel-Network 13 KERNEL_NETWORK_TASK_TCPIP in lsass.exe(652): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49698; seqnum=       0; connid=       0
- 17:36:17.606384 Unknown 295  in lsass.exe(652): 
- 17:36:17.606385 Unknown 297  in lsass.exe(652): 
- 17:36:17.606385 Unknown 298  in lsass.exe(652): 
- 17:36:17.606487 LsaSrv 300  in lsass.exe(652): TargetUserSid=S-1-5-21-2921435408-891897996-1317750820-500; TargetUserName=Administrator; TargetDomainName=HQ; TargetLogonId=0x564C9; TargetLogonGuid={6a41e65e-63d0-1723-05bc-2a3a14c8233e}; EventOrginal=       1; EventCountTotal=       1; SidList=
		%{S-1-5-21
- 17:36:17.606504 Unknown 57  in lsass.exe(652): 
- 17:36:17.606504 Unknown 58  in lsass.exe(652): 
- 17:36:17.606505 Unknown 99  in lsass.exe(652): 
- 17:36:17.608335 LsaSrv 303  in lsass.exe(652): PackageName=CREDSSP; UserName=Administrator; DomainName=HQ; ProtectedUser=       0
- 17:36:17.608337 LsaSrv 303  in lsass.exe(652): PackageName=WDigest; UserName=Administrator; DomainName=HQ; ProtectedUser=       0
- 17:36:17.608340 Unknown 308  in lsass.exe(652): 
- 17:36:17.608341 Unknown 310  in lsass.exe(652): 
- 17:36:17.608341 Unknown 68  in lsass.exe(652): 
- 17:36:17.608446 LsaSrv 6226 LSA Logon  in lsass.exe(652): 
- 17:36:17.608456 Unknown 307  in lsass.exe(652): 
- 17:36:17.608456 Unknown 17  in lsass.exe(652): 
- 17:36:17.608456 Unknown 18  in lsass.exe(652): 
- 17:36:17.608457 Unknown 40  in lsass.exe(652): 
- 17:36:17.608462 Unknown 13  in lsass.exe(652): 
- 17:36:17.610229 DNS-Client 3006  in lsass.exe(652): QueryType=       1; QueryOptions=140737488355328; IsNetworkQuery=       0; NetworkQueryIndex=       0; InterfaceIndex=       0; IsAsyncQuery=       0
- 17:36:17.610288 DNS-Client 3008  in lsass.exe(652): QueryName=TIERGEN-WS; QueryType=       1; QueryOptions=140737488355328; QueryStatus=       0; QueryResults=10.10.0.21;
- 17:36:17.611522 DNS-Client 3006  in lsass.exe(652): QueryType=       1; QueryOptions=140737488355328; IsNetworkQuery=       0; NetworkQueryIndex=       0; InterfaceIndex=       0; IsAsyncQuery=       0
- 17:36:17.611563 DNS-Client 3008  in lsass.exe(652): QueryName=TIERGEN-WS; QueryType=       1; QueryOptions=140737488355328; QueryStatus=       0; QueryResults=10.10.0.21;
- 17:36:17.612418 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in lsass.exe(652): PID=     652; size=     168; daddr=10.10.0.10; saddr=10.10.0.21; dport=135; sport=49674; startime=    8518; endtime=    8518; seqnum=       0; connid=       0
- 17:36:17.612426 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in lsass.exe(652): PID=     652; size=     268; daddr=10.10.0.10; saddr=10.10.0.21; dport=135; sport=49674; seqnum=       0; connid=       0
- 17:36:17.612456 Unknown 102  in lsass.exe(652): 
- 17:36:17.612461 Unknown 116  in lsass.exe(652): 
- 17:36:17.612461 Unknown 117  in lsass.exe(652): 
- 17:36:17.612461 Unknown 102  in lsass.exe(652): 
- 17:36:17.612463 Unknown 31  in lsass.exe(652): 
- 17:36:17.612463 Unknown 116  in lsass.exe(652): 
- 17:36:17.612464 Unknown 117  in lsass.exe(652): 
- 17:36:17.612528 Unknown 23  in lsass.exe(652): 
- 17:36:17.612530 Unknown 17  in lsass.exe(652): 
- 17:36:17.612530 Unknown 18  in lsass.exe(652): 
- 17:36:17.612532 Unknown 19  in lsass.exe(652): 
- 17:36:17.612533 Unknown 63  in lsass.exe(652): 
- 17:36:17.612555 Unknown 28  in lsass.exe(652): 
- 17:36:17.612556 Unknown 74  in lsass.exe(652): 
- 17:36:17.612556 Unknown 75  in lsass.exe(652): 
- 17:36:17.612556 Unknown 76  in lsass.exe(652): 
- 17:36:17.612556 Unknown 77  in lsass.exe(652): 
- 17:36:17.612556 Unknown 78  in lsass.exe(652): 
- 17:36:17.612556 Unknown 83  in lsass.exe(652): 
- 17:36:17.612557 Unknown 89  in lsass.exe(652): 
- 17:36:17.612557 Unknown 92  in lsass.exe(652): 
- 17:36:17.612558 Unknown 93  in lsass.exe(652): 
- 17:36:17.612558 Unknown 97  in lsass.exe(652): 
- 17:36:17.612560 Unknown 45  in lsass.exe(652): 
- 17:36:17.612561 Unknown 26  in lsass.exe(652): 
- 17:36:17.612563 Unknown 181  in lsass.exe(652): 
- 17:36:17.612564 Unknown 155  in lsass.exe(652): 
- 17:36:17.612564 Unknown 77  in lsass.exe(652): 
- 17:36:17.612565 Unknown 78  in lsass.exe(652): 
- 17:36:17.612579 Unknown 220  in lsass.exe(652): 
- 17:36:17.612580 Unknown 221  in lsass.exe(652): 
- 17:36:17.612591 Unknown 61  in lsass.exe(652): 
- 17:36:17.612594 Unknown 73  in lsass.exe(652): 
- 17:36:17.612595 Unknown 35  in lsass.exe(652): 
- 17:36:17.613159 Kernel-Network 12 KERNEL_NETWORK_TASK_TCPIP in lsass.exe(652): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49699; mss=1460; sackopt=1; tsopt=0; wsopt=1; rcvwin=  262800; rcvwinscale=8; sndwinscale=8; seqnum=       0; connid=       0
- 17:36:17.613172 Unknown 34  in lsass.exe(652): 
- 17:36:17.613186 Unknown 38  in lsass.exe(652): 
- 17:36:17.613337 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in lsass.exe(652): PID=     652; size=    1836; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49699; startime=    8518; endtime=    8518; seqnum=       0; connid=       0
- 17:36:17.614218 Kernel-Network 18 KERNEL_NETWORK_TASK_TCPIP in lsass.exe(652): PID=     652; size=    1813; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49699; seqnum=       0; connid=       0
- 17:36:17.614225 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in lsass.exe(652): PID=     652; size=    1813; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49699; seqnum=       0; connid=       0
- 17:36:17.614232 Unknown 43  in lsass.exe(652): 
- 17:36:17.614282 Unknown 186  in lsass.exe(652): 
- 17:36:17.614296 Unknown 106  in lsass.exe(652): 
- 17:36:17.614297 Unknown 56  in lsass.exe(652): 
- 17:36:17.614298 Unknown 50  in lsass.exe(652): 
- 17:36:17.614311 Unknown 52  in lsass.exe(652): 
- 17:36:17.614312 Unknown 45  in lsass.exe(652): 
- 17:36:17.614314 Unknown 220  in lsass.exe(652): 
- 17:36:17.614315 Unknown 221  in lsass.exe(652): 
- 17:36:17.614334 Unknown 113  in lsass.exe(652): 
- 17:36:17.614334 Unknown 114  in lsass.exe(652): 
- 17:36:17.614467 Kernel-Network 13 KERNEL_NETWORK_TASK_TCPIP in lsass.exe(652): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49699; seqnum=       0; connid=       0
- 17:36:17.614604 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in NisSrv.exe(3948): PID=     652; size=    2138; daddr=10.10.0.10; saddr=10.10.0.21; dport=49667; sport=49689; startime=    8518; endtime=    8518; seqnum=       0; connid=       0
- 17:36:17.615286 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     256; daddr=10.10.0.10; saddr=10.10.0.21; dport=49667; sport=49689; seqnum=       0; connid=       0
- 17:36:17.615328 Unknown 23  in lsass.exe(652): 
- 17:36:17.615330 Unknown 17  in lsass.exe(652): 
- 17:36:17.615330 Unknown 18  in lsass.exe(652): 
- 17:36:17.615332 Unknown 19  in lsass.exe(652): 
- 17:36:17.615332 Unknown 28  in lsass.exe(652): 
- 17:36:17.615342 Unknown 264  in lsass.exe(652): 
- 17:36:17.615345 Unknown 258  in lsass.exe(652): 
- 17:36:17.615359 Unknown 144  in lsass.exe(652): 
- 17:36:17.615361 Unknown 36  in lsass.exe(652): 
- 17:36:17.615367 Unknown 74  in lsass.exe(652): 
- 17:36:17.615368 Unknown 113  in lsass.exe(652): 
- 17:36:17.615368 Unknown 114  in lsass.exe(652): 
- 17:36:17.615569 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     220; daddr=10.10.0.10; saddr=10.10.0.21; dport=49667; sport=49689; startime=    8518; endtime=    8518; seqnum=       0; connid=       0
- 17:36:17.615571 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     105; daddr=10.10.0.10; saddr=10.10.0.21; dport=49667; sport=49689; seqnum=       0; connid=       0
- 17:36:17.615594 Unknown 23  in lsass.exe(652): 
- 17:36:17.615595 Unknown 17  in lsass.exe(652): 
- 17:36:17.615596 Unknown 18  in lsass.exe(652): 
- 17:36:17.615597 Unknown 19  in lsass.exe(652): 
- 17:36:17.615597 Unknown 28  in lsass.exe(652): 
- 17:36:17.615598 Unknown 143  in lsass.exe(652): 
- 17:36:17.615600 Unknown 37  in lsass.exe(652): 
- 17:36:17.615600 Unknown 64  in lsass.exe(652): 
- 17:36:17.615603 Unknown 84  in lsass.exe(652): 
- 17:36:17.615603 Unknown 112  in lsass.exe(652): 
- 17:36:17.615604 Unknown 12  in lsass.exe(652): 
- 17:36:17.615604 Unknown 113  in lsass.exe(652): 
- 17:36:17.615604 Unknown 114  in lsass.exe(652): 
- 17:36:17.615613 Unknown 17  in lsass.exe(652): 
- 17:36:17.615619 Unknown 19  in lsass.exe(652): 
- 17:36:17.615620 Unknown 129  in lsass.exe(652): 
- 17:36:17.615631 Unknown 135  in lsass.exe(652): 
- 17:36:17.615648 Unknown 88  in lsass.exe(652): 
- 17:36:17.615648 Unknown 89  in lsass.exe(652): 
- 17:36:17.615649 Unknown 36  in lsass.exe(652): 
- 17:36:17.615658 Unknown 100  in lsass.exe(652): 
- 17:36:17.615802 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in MsMpEng.exe(2768): PID=     652; size=     268; daddr=10.10.0.10; saddr=10.10.0.21; dport=49667; sport=49689; startime=    8518; endtime=    8518; seqnum=       0; connid=       0
- 17:36:17.615804 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in MsMpEng.exe(2768): PID=     652; size=     204; daddr=10.10.0.10; saddr=10.10.0.21; dport=49667; sport=49689; seqnum=       0; connid=       0
- 17:36:17.615809 Unknown 102  in lsass.exe(652): 
- 17:36:17.615809 Unknown 103  in lsass.exe(652): 
- 17:36:17.615809 Unknown 37  in lsass.exe(652): 
- 17:36:17.615810 Unknown 64  in lsass.exe(652): 
- 17:36:17.615816 Unknown 123  in lsass.exe(652): 
- 17:36:17.615862 Unknown 88  in lsass.exe(652): 
- 17:36:17.615862 Unknown 89  in lsass.exe(652): 
- 17:36:17.615863 Unknown 36  in lsass.exe(652): 
- 17:36:17.615867 Unknown 100  in lsass.exe(652): 
- 17:36:17.616012 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     252; daddr=10.10.0.10; saddr=10.10.0.21; dport=49667; sport=49689; startime=    8518; endtime=    8518; seqnum=       0; connid=       0
- 17:36:17.616014 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     380; daddr=10.10.0.10; saddr=10.10.0.21; dport=49667; sport=49689; seqnum=       0; connid=       0
- 17:36:17.616018 Unknown 102  in lsass.exe(652): 
- 17:36:17.616018 Unknown 103  in lsass.exe(652): 
- 17:36:17.616018 Unknown 37  in lsass.exe(652): 
- 17:36:17.616019 Unknown 64  in lsass.exe(652): 
- 17:36:17.616025 Unknown 123  in lsass.exe(652): 
- 17:36:17.616034 Unknown 88  in lsass.exe(652): 
- 17:36:17.616034 Unknown 89  in lsass.exe(652): 
- 17:36:17.616034 Unknown 36  in lsass.exe(652): 
- 17:36:17.616038 Unknown 100  in lsass.exe(652): 
- 17:36:17.616130 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     252; daddr=10.10.0.10; saddr=10.10.0.21; dport=49667; sport=49689; startime=    8518; endtime=    8518; seqnum=       0; connid=       0
- 17:36:17.616130 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     348; daddr=10.10.0.10; saddr=10.10.0.21; dport=49667; sport=49689; seqnum=       0; connid=       0
- 17:36:17.616134 Unknown 102  in lsass.exe(652): 
- 17:36:17.616134 Unknown 103  in lsass.exe(652): 
- 17:36:17.616134 Unknown 37  in lsass.exe(652): 
- 17:36:17.616134 Unknown 64  in lsass.exe(652): 
- 17:36:17.616139 Unknown 123  in lsass.exe(652): 
- 17:36:17.616144 Unknown 88  in lsass.exe(652): 
- 17:36:17.616144 Unknown 89  in lsass.exe(652): 
- 17:36:17.616144 Unknown 36  in lsass.exe(652): 
- 17:36:17.616147 Unknown 100  in lsass.exe(652): 
- 17:36:17.616182 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     140; daddr=10.10.0.10; saddr=10.10.0.21; dport=49667; sport=49689; startime=    8518; endtime=    8518; seqnum=       0; connid=       0
- 17:36:17.616183 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=     140; daddr=10.10.0.10; saddr=10.10.0.21; dport=49667; sport=49689; seqnum=       0; connid=       0
- 17:36:17.616186 Unknown 102  in lsass.exe(652): 
- 17:36:17.616186 Unknown 103  in lsass.exe(652): 
- 17:36:17.616186 Unknown 37  in lsass.exe(652): 
- 17:36:17.616187 Unknown 64  in lsass.exe(652): 
- 17:36:17.616190 Unknown 123  in lsass.exe(652): 
- 17:36:17.909049 Kernel-Process 1 ProcessStart in cmd.exe(520)*: ProcessID=     616; ProcessSequenceNumber=140; CreateTime=2026-10-12T17:36:17.909031100Z; ParentProcessID=     520; ParentProcessSequenceNumber=139; SessionID=       0; Flags=       0; ProcessTokenElevationType=       1; ProcessTokenIsElevated=       1; Mandat
- 17:36:17.927748 Unknown 102  in lsass.exe(652): 
- 17:36:17.927753 Unknown 116  in lsass.exe(652): 
- 17:36:17.927754 Unknown 117  in lsass.exe(652): 
- 17:36:17.927758 Unknown 102  in lsass.exe(652): 
- 17:36:17.927759 Unknown 31  in lsass.exe(652): 
- 17:36:17.927759 Unknown 116  in lsass.exe(652): 
- 17:36:17.927760 Unknown 117  in lsass.exe(652): 
- 17:36:17.927819 Unknown 23  in lsass.exe(652): 
- 17:36:17.927821 Unknown 17  in lsass.exe(652): 
- 17:36:17.927822 Unknown 18  in lsass.exe(652): 
- 17:36:17.927824 Unknown 19  in lsass.exe(652): 
- 17:36:17.927824 Unknown 63  in lsass.exe(652): 
- 17:36:17.927826 Unknown 18  in lsass.exe(652): 
- 17:36:17.928098 Unknown 28  in lsass.exe(652): 
- 17:36:17.928100 Unknown 74  in lsass.exe(652): 
- 17:36:17.928100 Unknown 77  in lsass.exe(652): 
- 17:36:17.928101 Unknown 20  in lsass.exe(652): 
- 17:36:17.928101 Unknown 92  in lsass.exe(652): 
- 17:36:17.928102 Unknown 93  in lsass.exe(652): 
- 17:36:17.928102 Unknown 97  in lsass.exe(652): 
- 17:36:17.928106 Unknown 45  in lsass.exe(652): 
- 17:36:17.928110 Unknown 22  in lsass.exe(652): 
- 17:36:17.928111 Unknown 23  in lsass.exe(652): 
- 17:36:17.928111 Unknown 167  in lsass.exe(652): 
- 17:36:17.928112 Unknown 168  in lsass.exe(652): 
- 17:36:17.928112 Unknown 26  in lsass.exe(652): 
- 17:36:17.928113 Unknown 181  in lsass.exe(652): 
- 17:36:17.928115 Unknown 155  in lsass.exe(652): 
- 17:36:17.928116 Unknown 77  in lsass.exe(652): 
- 17:36:17.928117 Unknown 78  in lsass.exe(652): 
- 17:36:17.928141 Unknown 220  in lsass.exe(652): 
- 17:36:17.928141 Unknown 221  in lsass.exe(652): 
- 17:36:17.928154 Unknown 61  in lsass.exe(652): 
- 17:36:17.928158 Unknown 73  in lsass.exe(652): 
- 17:36:17.928158 Unknown 35  in lsass.exe(652): 
- 17:36:17.928618 Kernel-Network 12 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49700; mss=1460; sackopt=1; tsopt=0; wsopt=1; rcvwin=  262800; rcvwinscale=8; sndwinscale=8; seqnum=       0; connid=       0
- 17:36:17.928627 Unknown 34  in lsass.exe(652): 
- 17:36:17.928648 Unknown 38  in lsass.exe(652): 
- 17:36:17.928885 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=    1819; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49700; startime=    8550; endtime=    8550; seqnum=       0; connid=       0
- 17:36:17.930276 Kernel-Network 18 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=    1795; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49700; seqnum=       0; connid=       0
- 17:36:17.930302 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=    1795; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49700; seqnum=       0; connid=       0
- 17:36:17.930308 Unknown 43  in lsass.exe(652): 
- 17:36:17.930360 Unknown 186  in lsass.exe(652): 
- 17:36:17.930367 Unknown 26  in lsass.exe(652): 
- 17:36:17.930369 Unknown 106  in lsass.exe(652): 
- 17:36:17.930370 Unknown 56  in lsass.exe(652): 
- 17:36:17.930370 Unknown 41  in lsass.exe(652): 
- 17:36:17.930371 Unknown 26  in lsass.exe(652): 
- 17:36:17.930372 Unknown 155  in lsass.exe(652): 
- 17:36:17.930372 Unknown 77  in lsass.exe(652): 
- 17:36:17.930374 Unknown 78  in lsass.exe(652): 
- 17:36:17.930385 Unknown 220  in lsass.exe(652): 
- 17:36:17.930386 Unknown 221  in lsass.exe(652): 
- 17:36:17.930405 Unknown 61  in lsass.exe(652): 
- 17:36:17.930408 Unknown 73  in lsass.exe(652): 
- 17:36:17.930409 Unknown 35  in lsass.exe(652): 
- 17:36:17.930642 Kernel-Network 13 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49700; seqnum=       0; connid=       0
- 17:36:17.930760 Kernel-Network 12 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49701; mss=1460; sackopt=1; tsopt=0; wsopt=1; rcvwin=  262800; rcvwinscale=8; sndwinscale=8; seqnum=       0; connid=       0
- 17:36:17.930769 Unknown 34  in lsass.exe(652): 
- 17:36:17.930782 Unknown 38  in lsass.exe(652): 
- 17:36:17.930953 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=    1617; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49701; startime=    8550; endtime=    8550; seqnum=       0; connid=       0
- 17:36:17.931168 Kernel-Network 18 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=    1646; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49701; seqnum=       0; connid=       0
- 17:36:17.931172 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=     652; size=    1646; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49701; seqnum=       0; connid=       0
- 17:36:17.931183 Unknown 43  in lsass.exe(652): 
- 17:36:17.931243 Unknown 50  in lsass.exe(652): 
- 17:36:17.931244 Unknown 52  in lsass.exe(652): 
- 17:36:17.931244 Unknown 45  in lsass.exe(652): 
- 17:36:17.931250 Kernel-Network 13 KERNEL_NETWORK_TASK_TCPIP in lsass.exe(652): PID=     652; size=       0; daddr=10.10.0.10; saddr=10.10.0.21; dport=88; sport=49701; seqnum=       0; connid=       0
- 17:36:17.931260 Unknown 220  in lsass.exe(652): 
- 17:36:17.931260 Unknown 221  in lsass.exe(652): 
- 17:36:17.931278 Unknown 113  in lsass.exe(652): 
- 17:36:17.931278 Unknown 114  in lsass.exe(652): 
- 17:36:17.931320 SMBClient 30406  in System(4): Count=       0; Command=SESSION ; MessageId=34; SessionId=0; TreeId=       0; MidCharge=1; CreditRequested=1; SendLength=    3655; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.931374 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=    3659; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    8550; endtime=    8550; seqnum=       0; connid=       0
- 17:36:17.932406 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     260; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:17.932454 Unknown 23  in lsass.exe(652): 
- 17:36:17.932455 Unknown 17  in lsass.exe(652): 
- 17:36:17.932456 Unknown 18  in lsass.exe(652): 
- 17:36:17.932457 Unknown 19  in lsass.exe(652): 
- 17:36:17.932457 Unknown 28  in lsass.exe(652): 
- 17:36:17.932467 Unknown 264  in lsass.exe(652): 
- 17:36:17.932469 Unknown 142  in lsass.exe(652): 
- 17:36:17.932470 Unknown 112  in lsass.exe(652): 
- 17:36:17.932470 Unknown 12  in lsass.exe(652): 
- 17:36:17.932471 Unknown 113  in lsass.exe(652): 
- 17:36:17.932471 Unknown 114  in lsass.exe(652): 
- 17:36:17.932575 SMBClient 30406  in System(4): Count=       0; Command=TRE_CONN; MessageId=35; SessionId=17592186044433; TreeId=       0; MidCharge=1; CreditRequested=1; SendLength=     138; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.932679 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     142; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    8550; endtime=    8550; seqnum=       0; connid=       0
- 17:36:17.932685 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=      84; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:17.932786 SMBClient 30406  in cmd.exe(520)*: Count=       0; Command=IOCTL   ; MessageId=36; SessionId=17592186044433; TreeId=       1; MidCharge=1; CreditRequested=1; SendLength=     196; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.933448 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     200; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    8550; endtime=    8550; seqnum=       0; connid=       0
- 17:36:17.933455 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=      76; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:17.933714 SMBClient 30406  in System(4): Count=       0; Command=TRE_CONN; MessageId=37; SessionId=17592186044433; TreeId=       0; MidCharge=1; CreditRequested=13; SendLength=     146; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.933929 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     150; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    8550; endtime=    8550; seqnum=       0; connid=       0
- 17:36:17.933934 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=      84; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:17.934082 SMBClient 30406  in cmd.exe(520)*: Count=       0; Command=CREATE  ; MessageId=38; SessionId=17592186044433; TreeId=       5; MidCharge=1; CreditRequested=11; SendLength=     176; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.934182 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     180; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    8550; endtime=    8550; seqnum=       0; connid=       0
- 17:36:17.934185 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     244; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:17.934227 SMBClient 30406  in cmd.exe(520)*: Count=       0; Command=QRY_INFO; MessageId=39; SessionId=17592186044433; TreeId=       5; MidCharge=1; CreditRequested=10; SendLength=     104; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.934297 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     108; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    8550; endtime=    8550; seqnum=       0; connid=       0
- 17:36:17.934299 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     132; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:17.934338 SMBClient 30406  in cmd.exe(520)*: Count=       0; Command=QRY_INFO; MessageId=40; SessionId=17592186044433; TreeId=       5; MidCharge=1; CreditRequested=0; SendLength=     112; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.934338 SMBClient 30406  in cmd.exe(520)*: Count=       1; Command=QRY_INFO; MessageId=41; SessionId=17592186044433; TreeId=       5; MidCharge=1; CreditRequested=17; SendLength=     105; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.934404 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     221; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    8550; endtime=    8550; seqnum=       0; connid=       0
- 17:36:17.934419 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     204; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:17.934434 SMBClient 30406  in cmd.exe(520)*: Count=       0; Command=CLOSE   ; MessageId=42; SessionId=17592186044433; TreeId=       5; MidCharge=1; CreditRequested=7; SendLength=      88; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.934495 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=      92; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    8550; endtime=    8550; seqnum=       0; connid=       0
- 17:36:17.934497 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     128; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:17.934581 SMBClient 30406  in cmd.exe(520)*: Count=       0; Command=CREATE  ; MessageId=43; SessionId=17592186044433; TreeId=       5; MidCharge=1; CreditRequested=0; SendLength=     176; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.934582 SMBClient 30406  in cmd.exe(520)*: Count=       1; Command=QRY_INFO; MessageId=44; SessionId=17592186044433; TreeId=       5; MidCharge=1; CreditRequested=11; SendLength=     104; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.934667 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     284; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    8550; endtime=    8550; seqnum=       0; connid=       0
- 17:36:17.934670 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     372; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:17.934753 SMBClient 30406  in cmd.exe(520)*: Count=       0; Command=QRY_INFO; MessageId=45; SessionId=17592186044433; TreeId=       5; MidCharge=1; CreditRequested=5; SendLength=     104; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.934820 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     108; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    8550; endtime=    8550; seqnum=       0; connid=       0
- 17:36:17.934821 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     132; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:17.934832 SMBClient 30406  in cmd.exe(520)*: Count=       0; Command=CLOSE   ; MessageId=46; SessionId=17592186044433; TreeId=       5; MidCharge=1; CreditRequested=4; SendLength=      88; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.934876 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=      92; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    8550; endtime=    8550; seqnum=       0; connid=       0
- 17:36:17.934877 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     128; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:17.935163 SMBClient 30406  in cmd.exe(520)*: Count=       0; Command=CREATE  ; MessageId=47; SessionId=17592186044433; TreeId=       5; MidCharge=1; CreditRequested=0; SendLength=     176; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.935164 SMBClient 30406  in cmd.exe(520)*: Count=       1; Command=QRY_INFO; MessageId=48; SessionId=17592186044433; TreeId=       5; MidCharge=1; CreditRequested=8; SendLength=     104; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.935275 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in MsMpEng.exe(2768): PID=       4; size=     284; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    8550; endtime=    8550; seqnum=       0; connid=       0
- 17:36:17.935280 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in MsMpEng.exe(2768): PID=       4; size=     372; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:17.935367 SMBClient 30406  in cmd.exe(520)*: Count=       0; Command=QRY_INFO; MessageId=49; SessionId=17592186044433; TreeId=       5; MidCharge=1; CreditRequested=1; SendLength=     104; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.935419 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in MsMpEng.exe(2768): PID=       4; size=     108; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    8550; endtime=    8550; seqnum=       0; connid=       0
- 17:36:17.935423 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in MsMpEng.exe(2768): PID=       4; size=     132; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:17.935438 SMBClient 30406  in cmd.exe(520)*: Count=       0; Command=CLOSE   ; MessageId=50; SessionId=17592186044433; TreeId=       5; MidCharge=1; CreditRequested=1; SendLength=      88; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.935484 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in MsMpEng.exe(2768): PID=       4; size=      92; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    8550; endtime=    8550; seqnum=       0; connid=       0
- 17:36:17.935487 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in MsMpEng.exe(2768): PID=       4; size=     128; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:17.935645 SMBClient 30406  in cmd.exe(520)*: Count=       0; Command=CREATE  ; MessageId=51; SessionId=17592186044433; TreeId=       5; MidCharge=1; CreditRequested=0; SendLength=     176; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.935645 SMBClient 30406  in cmd.exe(520)*: Count=       1; Command=QRY_INFO; MessageId=52; SessionId=17592186044433; TreeId=       5; MidCharge=1; CreditRequested=2; SendLength=     104; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.935725 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     284; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    8550; endtime=    8550; seqnum=       0; connid=       0
- 17:36:17.935729 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     372; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:17.935769 SMBClient 30406  in cmd.exe(520)*: Count=       0; Command=CLOSE   ; MessageId=53; SessionId=17592186044433; TreeId=       5; MidCharge=1; CreditRequested=1; SendLength=      88; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.935825 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=      92; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    8550; endtime=    8550; seqnum=       0; connid=       0
- 17:36:17.935827 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     128; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:17.936024 SMBClient 30406  in cmd.exe(520)*: Count=       0; Command=CREATE  ; MessageId=54; SessionId=17592186044433; TreeId=       5; MidCharge=1; CreditRequested=1; SendLength=     252; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.936385 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     256; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    8550; endtime=    8550; seqnum=       0; connid=       0
- 17:36:17.936390 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     324; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:17.936427 SMBClient 30406  in cmd.exe(520)*: Count=       0; Command=QRY_INFO; MessageId=55; SessionId=17592186044433; TreeId=       5; MidCharge=1; CreditRequested=1; SendLength=     104; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.936556 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     108; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    8550; endtime=    8550; seqnum=       0; connid=       0
- 17:36:17.936558 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     132; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:17.936575 SMBClient 30406  in cmd.exe(520)*: Count=       0; Command=QRY_DIR ; MessageId=56; SessionId=17592186044433; TreeId=       5; MidCharge=1; CreditRequested=0; SendLength=     104; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.936575 SMBClient 30406  in cmd.exe(520)*: Count=       1; Command=QRY_DIR ; MessageId=57; SessionId=17592186044433; TreeId=       5; MidCharge=1; CreditRequested=2; SendLength=      98; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.936655 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     206; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    8550; endtime=    8550; seqnum=       0; connid=       0
- 17:36:17.936669 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     372; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:17.936875 SMBClient 30406  in cmd.exe(520)*: Count=       0; Command=CREATE  ; MessageId=58; SessionId=17592186044433; TreeId=       5; MidCharge=1; CreditRequested=0; SendLength=     152; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.936875 SMBClient 30406  in cmd.exe(520)*: Count=       1; Command=QRY_INFO; MessageId=59; SessionId=17592186044433; TreeId=       5; MidCharge=1; CreditRequested=2; SendLength=     104; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.937096 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     260; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    8550; endtime=    8550; seqnum=       0; connid=       0
- 17:36:17.937100 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     292; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:17.937125 SMBClient 30406  in cmd.exe(520)*: Count=       0; Command=CLOSE   ; MessageId=60; SessionId=17592186044433; TreeId=       5; MidCharge=1; CreditRequested=1; SendLength=      88; VcEndpoint=0xFFFFDC06BC441A30
- 17:36:17.937186 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=      92; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; startime=    8550; endtime=    8550; seqnum=       0; connid=       0
- 17:36:17.937189 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0): PID=       4; size=     128; daddr=10.10.0.10; saddr=10.10.0.21; dport=445; sport=49684; seqnum=       0; connid=       0
- 17:36:17.944154 Kernel-Process 2 ProcessStop in cmd.exe(520)*: ProcessID=     520; ProcessSequenceNumber=139; CreateTime=2026-10-12T17:36:17.903174800Z; ExitTime=2026-10-12T17:36:17.944105000Z; ExitCode=       0; TokenElevationType=       1; HandleCount=      44; CommitCharge=4730880; CommitPeak=4943872; CPUCycleCount=101
- 17:36:18.626976 DNS-Client 1015 DnsServerTimeout in svchost.exe(1160): QueryName=v10.events.data.microsoft.com; AddressLength=      16; Address=10.10.0.10:53
- 17:36:18.626982 DNS-Client 3010  in svchost.exe(1160): QueryName=v10.events.data.microsoft.com; QueryType=       1; DnsServerIpAddress=10.10.0.10
- 17:36:18.626996 Kernel-Network 42 KERNEL_NETWORK_TASK_UDPIP in svchost.exe(1160): PID=    1160; size=      47; daddr=10.10.0.10; saddr=10.10.0.21; dport=53; sport=50841; seqnum=       0; connid=       0

