# What Windows reports of SMB

Processes marked * are an action's process or its descendants.

| action | pid | exit | start | end |
|---|---|---|---|---|
| map | 6904 | 0 | 2026-10-12T16:34:19.0038442Z | 2026-10-12T16:34:20.0664199Z |
| list | 7048 | 0 | 2026-10-12T16:34:23.0818926Z | 2026-10-12T16:34:24.1131390Z |
| read | 6644 | 0 | 2026-10-12T16:34:27.1133148Z | 2026-10-12T16:34:28.1913844Z |
| unmap | 7004 | 0 | 2026-10-12T16:34:31.1914408Z | 2026-10-12T16:34:32.2226223Z |
| list-unmapped | 6048 | 0 | 2026-10-12T16:34:35.2380874Z | 2026-10-12T16:34:36.2693611Z |

## Connections and requests

- TCP connect 10.77.0.21:49673 -> 10.77.0.53:445 at 16:34:19.134347, logged in System(4)
- TCP disconnects in the trace: 0
- Sysmon network connection: System (4) 10.77.0.21:49673 -> 10.77.0.53:445
- Sysmon network connection: System (4) 10.77.0.21:137 -> 10.77.0.53:137
- SMB connection handles (VcEndpoint): 1
- requests sent (SMBClient 30406) in System(4): IOCTL 1, SESSION 2, TRE_CONN 2, TRE_DCON 1; sessions 0, 2051295070
- requests sent (SMBClient 30406) in MsMpEng.exe(2564): READ 1; sessions 2051295070
- requests sent (SMBClient 30406) in cmd.exe(6048)*: CLOSE 2, CREATE 2, QRY_INFO 3; sessions 2051295070
- requests sent (SMBClient 30406) in cmd.exe(6644)*: CREATE 1, QRY_INFO 1; sessions 2051295070
- requests sent (SMBClient 30406) in net.exe(6932)*: IOCTL 1; sessions 2051295070
- requests sent (SMBClient 30406) in cmd.exe(7048)*: CLOSE 2, CREATE 3, IOCTL 1, QRY_DIR 2, QRY_INFO 3; sessions 2051295070

## Per provider and event

| provider | id | task | n | logged in | fields naming the server |
|---|---|---|---|---|---|
|  | 0 |  | 2 | logman.exe(6772) |  |
| Kernel-File | 10 | NameCreate | 2481 | System(4), csrss.exe(528), services.exe(648), svchost.exe(896), svchost.exe(1144), svchost.exe(1308) … | FileName |
| Kernel-File | 11 | NameDelete | 542 | System(4), svchost.exe(1308), powershell.exe(3632), RuntimeBroker.exe(5220), StartMenuExperienceHost.exe(5864), SearchApp.exe(6036) … | FileName |
| Kernel-File | 12 | Create | 24383 | System(4), userinit.exe(8), csrss.exe(444), wininit.exe(512), csrss.exe(528), services.exe(648) … | FileName |
| Kernel-Network | 10 | KERNEL_NETWORK_TASK_TCPIP | 25 | ?(0), System(4), SearchProtocolHost.exe(6376) | daddr |
| Kernel-Network | 11 | KERNEL_NETWORK_TASK_TCPIP | 25 | ?(0), System(4), SearchProtocolHost.exe(6376) | daddr |
| Kernel-Network | 12 | KERNEL_NETWORK_TASK_TCPIP | 1 | System(4) | daddr |
| Kernel-Network | 42 | KERNEL_NETWORK_TASK_UDPIP | 20 | ?(0), svchost.exe(1936), MsMpEng.exe(2564), svchost.exe(3540) | daddr |
| Kernel-Network | 43 | KERNEL_NETWORK_TASK_UDPIP | 14 | MsMpEng.exe(2564), svchost.exe(3540) |  |
| Kernel-Network | 58 | KERNEL_NETWORK_TASK_UDPIP | 4 | svchost.exe(1292), svchost.exe(1936) |  |
| Kernel-Process | 1 | ProcessStart | 25 | services.exe(648), svchost.exe(776), svchost.exe(1532), powershell.exe(3632), explorer.exe(4328), MicrosoftEdgeUpdate.exe(4680) … |  |
| Kernel-Process | 2 | ProcessStop | 24 | userinit.exe(8), mobsync.exe(4168), net.exe(4220)*, conhost.exe(5632)*, cmd.exe(6048)*, taskhostw.exe(6280) … |  |
| SMBClient | 201 |  | 2 | System(4) |  |
| SMBClient | 2000 |  | 24 | cmd.exe(6048)*, net.exe(6932)*, cmd.exe(7048)* |  |
| SMBClient | 20001 |  | 36 | svchost.exe(2192), cmd.exe(6048)*, cmd.exe(6644)*, net.exe(6932)*, cmd.exe(7048)* |  |
| SMBClient | 30103 |  | 10 | System(4), svchost.exe(2192), cmd.exe(6048)*, cmd.exe(7048)* |  |
| SMBClient | 30104 |  | 10 | System(4), cmd.exe(6048)*, cmd.exe(7048)* |  |
| SMBClient | 30110 |  | 1 | System(4) | ServerName |
| SMBClient | 30111 |  | 60 | ?(0), System(4), MsMpEng.exe(2564), cmd.exe(6048)*, SearchProtocolHost.exe(6376), cmd.exe(6644)* … |  |
| SMBClient | 30114 |  | 30 | ?(0), System(4), SearchProtocolHost.exe(6376) |  |
| SMBClient | 30203 |  | 1 | System(4) | RemoteAddress |
| SMBClient | 30204 |  | 1 | System(4) |  |
| SMBClient | 30205 |  | 25 | System(4), MsMpEng.exe(2564), cmd.exe(6048)*, cmd.exe(6644)*, net.exe(6932)*, cmd.exe(7048)* |  |
| SMBClient | 30206 |  | 25 | ?(0), System(4), SearchProtocolHost.exe(6376) |  |
| SMBClient | 30404 |  | 11 | cmd.exe(6048)*, cmd.exe(6644)*, cmd.exe(7048)* |  |
| SMBClient | 30405 |  | 2 | cmd.exe(6048)*, cmd.exe(7048)* |  |
| SMBClient | 30406 |  | 28 | System(4), MsMpEng.exe(2564), cmd.exe(6048)*, cmd.exe(6644)*, net.exe(6932)*, cmd.exe(7048)* |  |
| SMBClient | 30407 |  | 30 | ?(0), System(4), SearchProtocolHost.exe(6376) |  |
| SMBClient | 30410 |  | 65 | logman.exe(6772), logman.exe(6872), logman.exe(6980), logman.exe(7024), logman.exe(7100) |  |
| SMBClient | 30501 |  | 5 | cmd.exe(6048)*, cmd.exe(6644)*, cmd.exe(7048)* |  |
| SMBClient | 30502 |  | 29 | cmd.exe(6048)*, cmd.exe(6644)*, cmd.exe(7048)* |  |
| SMBClient | 30505 |  | 15 | cmd.exe(6048)*, cmd.exe(6644)*, cmd.exe(7048)* |  |
| SMBClient | 30506 |  | 4 | cmd.exe(6048)*, cmd.exe(6644)*, cmd.exe(7048)* |  |
| SMBClient | 30507 |  | 3 | cmd.exe(6048)*, cmd.exe(6644)*, cmd.exe(7048)* |  |
| SMBClient | 30508 |  | 4 | cmd.exe(6644)* |  |
| SMBClient | 30600 |  | 2 | System(4) | ObjectName |
| SMBClient | 30601 |  | 6 | System(4), svchost.exe(2192) | ObjectName |
| SMBClient | 30603 |  | 27 | System(4), cmd.exe(6048)*, cmd.exe(6644)*, cmd.exe(7048)* | ShareName |
| SMBClient | 40000 |  | 43 | ?(0), System(4), MsMpEng.exe(2564), cmd.exe(6048)*, SearchProtocolHost.exe(6376), cmd.exe(6644)* … | PeerAddress |

## Each action's events

### map (pid 6904, exit 0)

- 16:34:19.056443 Kernel-Process 1 ProcessStart in cmd.exe(6904)* act {00000000: ProcessID=    6952; ProcessSequenceNumber=158; CreateTime=2026-10-12T16:34:19.056426000Z; ParentProcessID=    6904; ParentProcessSequenceNumber=157; SessionID=       0; Flags=       0; ProcessTokenElevationType=       1; ProcessTokenIsEleva
- 16:34:19.088151 Kernel-Process 1 ProcessStart in cmd.exe(6904)* act {00000000: ProcessID=    6932; ProcessSequenceNumber=159; CreateTime=2026-10-12T16:34:19.088135500Z; ParentProcessID=    6904; ParentProcessSequenceNumber=157; SessionID=       0; Flags=       0; ProcessTokenElevationType=       1; ProcessTokenIsEleva
- 16:34:19.134141 SMBClient 30203  in System(4) act {00000000: RemoteAddressLength=      16; RemoteAddress=10.77.0.53:445; VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; ConnectionType=       1
- 16:34:19.134347 Kernel-Network 12 KERNEL_NETWORK_TASK_TCPIP in System(4) act {00000000: PID=       4; size=       0; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; mss=1460; sackopt=1; tsopt=0; wsopt=1; rcvwin= 2102400; rcvwinscale=8; sndwinscale=10; seqnum=       0; connid=       0
- 16:34:19.134349 SMBClient 30204  in System(4) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; Status=       0; ConnectionType=       1
- 16:34:19.134396 SMBClient 30110  in System(4) act {00000000: ServerNameLength=11; ServerName=\10.77.0.53; MidWindow=0xFFFFE0023FCF96C0
- 16:34:19.134402 SMBClient 30111  in System(4) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=       1; ThrottlingWindowLimit=       2; OldestPendingMid=0; NextAvailableMid=1; CreditsGranted=0
- 16:34:19.134403 SMBClient 40000  in System(4) act {00000001: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=      69; PacketData=0xFF534D4272000000001853C8000000000000000000000000FFFFFFFE00000000002200024E54204C4D20302E31320002534D4220322E3030320002534D422
- 16:34:19.134403 SMBClient 30205  in System(4) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F945600; SendLength=      73; ConnectionType=       1
- 16:34:19.134474 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in System(4) act {00000000: PID=       4; size=      73; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; startime=    1570; endtime=    1570; seqnum=       0; connid=       0
- 16:34:19.134479 SMBClient 30206  in System(4) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F945600; SendLength=      69; Status=       0; ConnectionType=       1
- 16:34:19.134480 SMBClient 30114  in System(4) act {00000000: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:19.137461 SMBClient 40000  in ?(0) act {00000002: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     202; PacketData=0xFE534D42400000000000000000000100010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
- 16:34:19.137462 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       0; CurrentWindowLimit=       1; ThrottlingWindowLimit=       2; OldestPendingMid=1; NextAvailableMid=1; CreditsGranted=0
- 16:34:19.137463 SMBClient 30407  in ?(0) act {00000000: Command=NEG_MP  ; MessageId=0; AsyncId=0; SessionId=0; TreeId=       0; CreditGranted=1; Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:19.137466 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     206; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; seqnum=       0; connid=       0
- 16:34:19.137476 SMBClient 30111  in System(4) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=       1; ThrottlingWindowLimit=       2; OldestPendingMid=1; NextAvailableMid=2; CreditsGranted=0
- 16:34:19.137477 SMBClient 40000  in System(4) act {00000003: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     228; PacketData=0xFE534D4240000000000000000000000000000000000000000100000000000000FFFE000000000000000000000000000000000000000000000000000000000
- 16:34:19.137488 SMBClient 30205  in System(4) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F9551E0; SendLength=     232; ConnectionType=       1
- 16:34:19.139745 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     232; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; startime=    1570; endtime=    1571; seqnum=       0; connid=       0
- 16:34:19.139747 SMBClient 40000  in ?(0) act {00000004: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     268; PacketData=0xFE534D4240000000000000000000010001000000000000000100000000000000FFFE000000000000000000000000000000000000000000000000000000000
- 16:34:19.139747 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       0; CurrentWindowLimit=       1; ThrottlingWindowLimit=       2; OldestPendingMid=2; NextAvailableMid=2; CreditsGranted=0
- 16:34:19.139748 SMBClient 30407  in ?(0) act {00000000: Command=NEG_MP  ; MessageId=1; AsyncId=0; SessionId=0; TreeId=       0; CreditGranted=1; Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:19.139749 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     272; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; seqnum=       0; connid=       0
- 16:34:19.139750 SMBClient 30206  in ?(0) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023DF153E0; SendLength=     228; Status=       0; ConnectionType=       1
- 16:34:19.139751 SMBClient 30114  in ?(0) act {00000000: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:19.139896 SMBClient 30601  in System(4) act {00000000: Object=0xFFFFE0023F844A30; OldState=1; NewState=3; Status=0x0; NameLength=16; ObjectName=\10.77.0.53\IPC$
- 16:34:19.139899 SMBClient 30103  in System(4) act {7e381306: RxContext=0xFFFFE002399C2220; Exchange=0xFFFFE0023DFF8E40; ListHead=0xFFFFE0023F844B68
- 16:34:19.139901 SMBClient 30600  in System(4) act {00000000: Object=0xFFFFE0023EC32060; OldState=1; NewState=3; Status=0x0; NameLength=11; ObjectName=\10.77.0.53
- 16:34:19.139904 SMBClient 30103  in System(4) act {00000000: RxContext=0x0; Exchange=0xFFFFE0023E1FEA30; ListHead=0xFFFFE0023EC32198
- 16:34:19.142662 SMBClient 201  in System(4) act {00000000: ErrorCode=0x0; Location=537920908; Context=      13
- 16:34:19.142663 SMBClient 30111  in System(4) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=       1; ThrottlingWindowLimit=       2; OldestPendingMid=2; NextAvailableMid=3; CreditsGranted=0
- 16:34:19.142664 SMBClient 30406  in System(4) act {00000000: Count=       0; Command=SESSION ; MessageId=2; SessionId=0; TreeId=       0; MidCharge=1; CreditRequested=33; SendLength=     162; VcEndpoint=0xFFFFE0023F605020
- 16:34:19.142664 SMBClient 40000  in System(4) act {00000005: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     162; PacketData=0xFE534D4240000100000000000100210010000000000000000200000000000000FFFE000000000000000000000000000000000000000000000000000000000
- 16:34:19.142665 SMBClient 30205  in System(4) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F9551E0; SendLength=     166; ConnectionType=       1
- 16:34:19.143398 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     166; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; startime=    1571; endtime=    1571; seqnum=       0; connid=       0
- 16:34:19.143400 SMBClient 40000  in ?(0) act {00000006: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     231; PacketData=0xFE534D4240000100160000C00100010011000000000000000200000000000000FFFE0000000000005E47447A0000000000000000000000000000000000000
- 16:34:19.143401 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       0; CurrentWindowLimit=       1; ThrottlingWindowLimit=       2; OldestPendingMid=3; NextAvailableMid=3; CreditsGranted=0
- 16:34:19.143401 SMBClient 30407  in ?(0) act {00000000: Command=SESSION ; MessageId=2; AsyncId=0; SessionId=2051295070; TreeId=       0; CreditGranted=1; Status=3221225494; VcEndpoint=0xFFFFE0023F605020
- 16:34:19.143405 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     235; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; seqnum=       0; connid=       0
- 16:34:19.143406 SMBClient 30206  in ?(0) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023DF153E0; SendLength=     162; Status=       0; ConnectionType=       1
- 16:34:19.143407 SMBClient 30114  in ?(0) act {00000000: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:19.143984 SMBClient 201  in System(4) act {00000000: ErrorCode=0x0; Location=537920908; Context=      13
- 16:34:19.143985 SMBClient 30111  in System(4) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=       1; ThrottlingWindowLimit=       2; OldestPendingMid=3; NextAvailableMid=4; CreditsGranted=0
- 16:34:19.143985 SMBClient 30406  in System(4) act {00000000: Count=       0; Command=SESSION ; MessageId=3; SessionId=2051295070; TreeId=       0; MidCharge=1; CreditRequested=33; SendLength=     515; VcEndpoint=0xFFFFE0023F605020
- 16:34:19.143986 SMBClient 40000  in System(4) act {00000007: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     515; PacketData=0xFE534D4240000100000000000100210010000000000000000300000000000000FFFE0000000000005E47447A0000000000000000000000000000000000000
- 16:34:19.143986 SMBClient 30205  in System(4) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F95DA60; SendLength=     519; ConnectionType=       1
- 16:34:19.144754 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in SearchProtocolHost.exe(6376) act {00000000: PID=       4; size=     519; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; startime=    1571; endtime=    1571; seqnum=       0; connid=       0
- 16:34:19.144755 SMBClient 40000  in SearchProtocolHost.exe(6376) act {00000008: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     101; PacketData=0xFE534D4240000100000000000100210019000000000000000300000000000000FFFE0000000000005E47447A0000000018C52214A4B1DE77CDCF44B8DE1CB
- 16:34:19.144756 SMBClient 30111  in SearchProtocolHost.exe(6376) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       0; CurrentWindowLimit=      33; ThrottlingWindowLimit=       2; OldestPendingMid=4; NextAvailableMid=4; CreditsGranted=0
- 16:34:19.144756 SMBClient 30407  in SearchProtocolHost.exe(6376) act {00000000: Command=SESSION ; MessageId=3; AsyncId=0; SessionId=2051295070; TreeId=       0; CreditGranted=33; Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:19.144759 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in SearchProtocolHost.exe(6376) act {00000000: PID=       4; size=     105; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; seqnum=       0; connid=       0
- 16:34:19.144760 SMBClient 30206  in SearchProtocolHost.exe(6376) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F9551E0; SendLength=     515; Status=       0; ConnectionType=       1
- 16:34:19.144760 SMBClient 30114  in SearchProtocolHost.exe(6376) act {00000000: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:19.144848 SMBClient 30600  in System(4) act {00000000: Object=0xFFFFE0023EC32060; OldState=3; NewState=0; Status=0x0; NameLength=11; ObjectName=\10.77.0.53
- 16:34:19.144849 SMBClient 30104  in System(4) act {00000000: RxContext=0x0; Exchange=0xFFFFE0023E1FEA30; ExchangeState=       4; ExchangeStatus=       0
- 16:34:19.144855 SMBClient 30111  in System(4) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=      33; ThrottlingWindowLimit=       2; OldestPendingMid=4; NextAvailableMid=5; CreditsGranted=0
- 16:34:19.144869 SMBClient 30406  in System(4) act {00000000: Count=       0; Command=TRE_CONN; MessageId=4; SessionId=2051295070; TreeId=       0; MidCharge=1; CreditRequested=1; SendLength=     106; VcEndpoint=0xFFFFE0023F605020
- 16:34:19.144870 SMBClient 40000  in System(4) act {00000009: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     106; PacketData=0xFE534D4240000100000000000300010018000000000000000400000000000000FFFE0000000000005E47447A00000000EC71E8BDE04228FA4D150923CAEF5
- 16:34:19.144870 SMBClient 30205  in System(4) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023DF153E0; SendLength=     110; ConnectionType=       1
- 16:34:19.145442 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     110; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; startime=    1571; endtime=    1571; seqnum=       0; connid=       0
- 16:34:19.145443 SMBClient 40000  in ?(0) act {0000000a: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=      80; PacketData=0xFE534D4240000100000000000300010019000000000000000400000000000000FFFE0000617799905E47447A000000009E77456E83CF4A1B5136075D74BBD
- 16:34:19.145444 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       0; CurrentWindowLimit=      33; ThrottlingWindowLimit=       2; OldestPendingMid=5; NextAvailableMid=5; CreditsGranted=0
- 16:34:19.145445 SMBClient 30407  in ?(0) act {00000000: Command=TRE_CONN; MessageId=4; AsyncId=0; SessionId=2051295070; TreeId=2425976673; CreditGranted=1; Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:19.145447 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=      84; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; seqnum=       0; connid=       0
- 16:34:19.145449 SMBClient 30206  in ?(0) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F9551E0; SendLength=     106; Status=       0; ConnectionType=       1
- 16:34:19.145449 SMBClient 30114  in ?(0) act {00000000: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:19.145454 SMBClient 30601  in System(4) act {00000000: Object=0xFFFFE0023F844A30; OldState=3; NewState=0; Status=0x0; NameLength=16; ObjectName=\10.77.0.53\IPC$
- 16:34:19.145454 SMBClient 30104  in System(4) act {7e381306: RxContext=0xFFFFE002399C2220; Exchange=0xFFFFE0023DFF8E40; ExchangeState=       4; ExchangeStatus=       0
- 16:34:19.145463 SMBClient 30111  in System(4) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=      33; ThrottlingWindowLimit=       2; OldestPendingMid=5; NextAvailableMid=6; CreditsGranted=0
- 16:34:19.145465 SMBClient 30406  in System(4) act {00000000: Count=       0; Command=IOCTL   ; MessageId=5; SessionId=2051295070; TreeId=2425976673; MidCharge=1; CreditRequested=1; SendLength=     120; VcEndpoint=0xFFFFE0023F605020
- 16:34:19.145465 SMBClient 40000  in System(4) act {0000000b: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     120; PacketData=0xFE534D4240000100000000000B00010018000000000000000500000000000000FFFE0000617799905E47447A00000000345E984FAF95B01EEF22F7FE697F0
- 16:34:19.145466 SMBClient 30205  in System(4) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023EA25920; SendLength=     124; ConnectionType=       1
- 16:34:19.145486 SMBClient 20001  in net.exe(6932)* act {7e381306: CurrentOrNextState=180; Context=       0
- 16:34:19.145486 SMBClient 20001  in net.exe(6932)* act {7e381306: CurrentOrNextState=181; Context=       0
- 16:34:19.145504 SMBClient 30111  in net.exe(6932)* act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       2; CurrentWindowLimit=      33; ThrottlingWindowLimit=       2; OldestPendingMid=5; NextAvailableMid=7; CreditsGranted=0
- 16:34:19.145504 SMBClient 30406  in net.exe(6932)* act {7e381306: Count=       0; Command=IOCTL   ; MessageId=6; SessionId=2051295070; TreeId=2425976673; MidCharge=1; CreditRequested=1; SendLength=     158; VcEndpoint=0xFFFFE0023F605020
- 16:34:19.145505 SMBClient 2000  in net.exe(6932)* act {0000000c: ReassembledEventID=40000; FragmentSize=      40; FragmentData=0x010000001C000000020001BD0A4D0035000000000000000030A8C93F02E0FFFFB074CD3F9E000000
- 16:34:19.145505 SMBClient 2000  in net.exe(6932)* act {0000000c: ReassembledEventID=40000; FragmentSize=     120; FragmentData=0xFE534D4240000100000000000B00010030000000000000000600000000000000FFFE0000617799905E47447A00000000000000000000000000000000000000003900000094010600FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
- 16:34:19.145505 SMBClient 2000  in net.exe(6932)* act {0000000c: ReassembledEventID=40000; FragmentSize=      38; FragmentData=0x04005C00310030002E00370037002E0030002E00350033005C00730068006100720065000000
- 16:34:19.145506 SMBClient 30205  in net.exe(6932)* act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F9464A0; SendLength=     162; ConnectionType=       1
- 16:34:19.145631 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     124; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; startime=    1571; endtime=    1571; seqnum=       0; connid=       0
- 16:34:19.145631 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     162; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; startime=    1571; endtime=    1571; seqnum=       0; connid=       0
- 16:34:19.145632 SMBClient 40000  in ?(0) act {0000000d: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     264; PacketData=0xFE534D4240000100000000000B00010019000000000000000500000000000000FFFE0000617799905E47447A0000000024FB46A4942F8C03EDCE85961F05E
- 16:34:19.145633 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=      33; ThrottlingWindowLimit=       2; OldestPendingMid=6; NextAvailableMid=7; CreditsGranted=0
- 16:34:19.145633 SMBClient 30407  in ?(0) act {00000000: Command=IOCTL   ; MessageId=5; AsyncId=0; SessionId=2051295070; TreeId=2425976673; CreditGranted=1; Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:19.145634 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     268; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; seqnum=       0; connid=       0
- 16:34:19.145635 SMBClient 30206  in ?(0) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F9551E0; SendLength=     120; Status=       0; ConnectionType=       1
- 16:34:19.145635 SMBClient 30114  in ?(0) act {00000000: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:19.145636 SMBClient 30206  in ?(0) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F945600; SendLength=     158; Status=       0; ConnectionType=       1
- 16:34:19.145637 SMBClient 30114  in ?(0) act {7e381306: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:19.145663 SMBClient 40000  in System(4) act {0000000e: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=      73; PacketData=0xFE534D4240000100250200C00B00010031000000000000000600000000000000FFFE0000617799905E47447A0000000000000000000000000000000000000
- 16:34:19.145663 SMBClient 30111  in System(4) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       0; CurrentWindowLimit=      33; ThrottlingWindowLimit=       2; OldestPendingMid=7; NextAvailableMid=7; CreditsGranted=0
- 16:34:19.145663 SMBClient 30407  in System(4) act {7e381306: Command=IOCTL   ; MessageId=6; AsyncId=0; SessionId=2051295070; TreeId=2425976673; CreditGranted=1; Status=3221226021; VcEndpoint=0xFFFFE0023F605020
- 16:34:19.145665 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in System(4) act {00000000: PID=       4; size=      77; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; seqnum=       0; connid=       0
- 16:34:19.146257 SMBClient 30601  in svchost.exe(2192) act {00000000: Object=0xFFFFE0023F9D3D10; OldState=1; NewState=3; Status=0x0; NameLength=17; ObjectName=\10.77.0.53\share
- 16:34:19.146260 SMBClient 30103  in svchost.exe(2192) act {7e381306: RxContext=0xFFFFE0023ECA1A20; Exchange=0xFFFFE0023DFF9E40; ListHead=0xFFFFE0023F9D3E48
- 16:34:19.146267 SMBClient 30111  in System(4) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=      33; ThrottlingWindowLimit=       2; OldestPendingMid=7; NextAvailableMid=8; CreditsGranted=0
- 16:34:19.146269 SMBClient 30406  in System(4) act {00000000: Count=       0; Command=TRE_CONN; MessageId=7; SessionId=2051295070; TreeId=       0; MidCharge=1; CreditRequested=1; SendLength=     108; VcEndpoint=0xFFFFE0023F605020
- 16:34:19.146270 SMBClient 40000  in System(4) act {0000000f: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     108; PacketData=0xFE534D4240000100000000000300010018000000000000000700000000000000FFFE0000000000005E47447A00000000720ADF906C00DE12DCAA161E0D1D7
- 16:34:19.146270 SMBClient 30205  in System(4) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F945530; SendLength=     112; ConnectionType=       1
- 16:34:19.146554 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in SearchProtocolHost.exe(6376) act {00000000: PID=       4; size=     112; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; startime=    1571; endtime=    1571; seqnum=       0; connid=       0
- 16:34:19.146555 SMBClient 40000  in SearchProtocolHost.exe(6376) act {00000010: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=      80; PacketData=0xFE534D4240000100000000000300010019000000000000000700000000000000FFFE000017490D6F5E47447A000000007CB3B05D7FB5EC854CD9B98376FE3
- 16:34:19.146555 SMBClient 30111  in SearchProtocolHost.exe(6376) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       0; CurrentWindowLimit=      33; ThrottlingWindowLimit=       2; OldestPendingMid=8; NextAvailableMid=8; CreditsGranted=0
- 16:34:19.146556 SMBClient 30407  in SearchProtocolHost.exe(6376) act {00000000: Command=TRE_CONN; MessageId=7; AsyncId=0; SessionId=2051295070; TreeId=1863141655; CreditGranted=1; Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:19.146558 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in SearchProtocolHost.exe(6376) act {00000000: PID=       4; size=      84; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; seqnum=       0; connid=       0
- 16:34:19.146560 SMBClient 30206  in SearchProtocolHost.exe(6376) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023CE48890; SendLength=     108; Status=       0; ConnectionType=       1
- 16:34:19.146560 SMBClient 30114  in SearchProtocolHost.exe(6376) act {00000000: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:19.146565 SMBClient 30601  in System(4) act {00000000: Object=0xFFFFE0023F9D3D10; OldState=3; NewState=0; Status=0x0; NameLength=17; ObjectName=\10.77.0.53\share
- 16:34:19.146565 SMBClient 30104  in System(4) act {7e381306: RxContext=0xFFFFE0023ECA1A20; Exchange=0xFFFFE0023DFF9E40; ExchangeState=       4; ExchangeStatus=       0
- 16:34:19.146621 SMBClient 20001  in svchost.exe(2192) act {7e381306: CurrentOrNextState=180; Context=       0
- 16:34:19.146621 SMBClient 20001  in svchost.exe(2192) act {7e381306: CurrentOrNextState=181; Context=       0
- 16:34:19.154012 Kernel-Process 2 ProcessStop in net.exe(6932)* act {00000000: ProcessID=    6932; ProcessSequenceNumber=159; CreateTime=2026-10-12T16:34:19.088135500Z; ExitTime=2026-10-12T16:34:19.153917300Z; ExitCode=       0; TokenElevationType=       1; HandleCount=      70; CommitCharge=1277952; CommitPeak=127795
- 16:34:19.156957 Kernel-Process 2 ProcessStop in cmd.exe(6904)* act {00000000: ProcessID=    6904; ProcessSequenceNumber=157; CreateTime=2026-10-12T16:34:19.033861700Z; ExitTime=2026-10-12T16:34:19.156905100Z; ExitCode=       0; TokenElevationType=       1; HandleCount=      47; CommitCharge=4407296; CommitPeak=440729
- 16:34:19.157422 Kernel-Process 2 ProcessStop in conhost.exe(6952)* act {00000000: ProcessID=    6952; ProcessSequenceNumber=158; CreateTime=2026-10-12T16:34:19.056426000Z; ExitTime=2026-10-12T16:34:19.157312000Z; ExitCode=       0; TokenElevationType=       1; HandleCount=     101; CommitCharge=6578176; CommitPeak=658227
- 16:34:19.316283 Kernel-Network 42 KERNEL_NETWORK_TASK_UDPIP in svchost.exe(3540) act {00000000: PID=    3540; size=     137; daddr=239.255.255.250; saddr=127.0.0.1; dport=1900; sport=64697; seqnum=       0; connid=       0
- 16:34:19.316339 Kernel-Network 43 KERNEL_NETWORK_TASK_UDPIP in svchost.exe(3540) act {00000000: PID=    3540; size=     137; daddr=239.255.255.250; saddr=127.0.0.1; dport=1900; sport=64697; seqnum=       0; connid=       0

### list (pid 7048, exit 0)

- 16:34:23.109877 Kernel-Process 1 ProcessStart in cmd.exe(7048)* act {00000000: ProcessID=    6868; ProcessSequenceNumber=161; CreateTime=2026-10-12T16:34:23.109860700Z; ParentProcessID=    7048; ParentProcessSequenceNumber=160; SessionID=       0; Flags=       0; ProcessTokenElevationType=       1; ProcessTokenIsEleva
- 16:34:23.129077 SMBClient 20001  in cmd.exe(7048)* act {7e381306: CurrentOrNextState=180; Context=       0
- 16:34:23.129077 SMBClient 20001  in cmd.exe(7048)* act {7e381306: CurrentOrNextState=181; Context=       0
- 16:34:23.129093 SMBClient 30111  in cmd.exe(7048)* act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=      33; ThrottlingWindowLimit=       2; OldestPendingMid=8; NextAvailableMid=9; CreditsGranted=0
- 16:34:23.129094 SMBClient 30406  in cmd.exe(7048)* act {7e381306: Count=       0; Command=IOCTL   ; MessageId=8; SessionId=2051295070; TreeId=2425976673; MidCharge=1; CreditRequested=1; SendLength=     158; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.129104 SMBClient 2000  in cmd.exe(7048)* act {00000011: ReassembledEventID=40000; FragmentSize=      40; FragmentData=0x010000001C000000020001BD0A4D0035000000000000000030A8C93F02E0FFFFB074CD3F9E000000
- 16:34:23.129104 SMBClient 2000  in cmd.exe(7048)* act {00000011: ReassembledEventID=40000; FragmentSize=     120; FragmentData=0xFE534D4240000100000000000B00010030000000000000000800000000000000FFFE0000617799905E47447A00000000000000000000000000000000000000003900000094010600FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
- 16:34:23.129104 SMBClient 2000  in cmd.exe(7048)* act {00000011: ReassembledEventID=40000; FragmentSize=      38; FragmentData=0x04005C00310030002E00370037002E0030002E00350033005C00730068006100720065000000
- 16:34:23.129105 SMBClient 30205  in cmd.exe(7048)* act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F956B10; SendLength=     162; ConnectionType=       1
- 16:34:23.129426 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     162; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; startime=    1970; endtime=    1970; seqnum=       0; connid=       0
- 16:34:23.129429 SMBClient 40000  in ?(0) act {00000012: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=      73; PacketData=0xFE534D4240000100250200C00B00010031000000000000000800000000000000FFFE0000617799905E47447A0000000000000000000000000000000000000
- 16:34:23.129430 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       0; CurrentWindowLimit=      33; ThrottlingWindowLimit=       2; OldestPendingMid=9; NextAvailableMid=9; CreditsGranted=0
- 16:34:23.129431 SMBClient 30407  in ?(0) act {7e381306: Command=IOCTL   ; MessageId=8; AsyncId=0; SessionId=2051295070; TreeId=2425976673; CreditGranted=1; Status=3221226021; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.129432 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=      77; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; seqnum=       0; connid=       0
- 16:34:23.129435 SMBClient 30206  in ?(0) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023EA22BA0; SendLength=     158; Status=       0; ConnectionType=       1
- 16:34:23.129435 SMBClient 30114  in ?(0) act {7e381306: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.129609 SMBClient 20001  in cmd.exe(7048)* act {7e381306: CurrentOrNextState=180; Context=       0
- 16:34:23.129614 SMBClient 30505  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023D207C50; Fcb=0xFFFFCD84EAF75050; FileNameLength=0; Status=       0
- 16:34:23.129617 SMBClient 30603  in cmd.exe(7048)* act {00000000: Object=0xFFFFCD84EAE1B2E0; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc74319f-c65a-11f1-a3a8-eea7cd268ff2}; OldState=1; NewState=3; Status=0x0; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=0; Prev
- 16:34:23.129620 SMBClient 30111  in cmd.exe(7048)* act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=      33; ThrottlingWindowLimit=       8; OldestPendingMid=9; NextAvailableMid=10; CreditsGranted=0
- 16:34:23.129620 SMBClient 30406  in cmd.exe(7048)* act {7e381306: Count=       0; Command=CREATE  ; MessageId=9; SessionId=2051295070; TreeId=1863141655; MidCharge=1; CreditRequested=1; SendLength=     176; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.129620 SMBClient 40000  in cmd.exe(7048)* act {00000013: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     176; PacketData=0xFE534D4240000100000000000500010030000000000000000900000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000
- 16:34:23.129621 SMBClient 30205  in cmd.exe(7048)* act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F9464A0; SendLength=     180; ConnectionType=       1
- 16:34:23.133340 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     180; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; startime=    1970; endtime=    1970; seqnum=       0; connid=       0
- 16:34:23.133342 SMBClient 40000  in ?(0) act {00000014: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     240; PacketData=0xFE534D4240000100000000000500010031000000000000000900000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000
- 16:34:23.133342 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       0; CurrentWindowLimit=      33; ThrottlingWindowLimit=       8; OldestPendingMid=10; NextAvailableMid=10; CreditsGranted=0
- 16:34:23.133343 SMBClient 30407  in ?(0) act {7e381306: Command=CREATE  ; MessageId=9; AsyncId=0; SessionId=2051295070; TreeId=1863141655; CreditGranted=1; Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.133344 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     244; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; seqnum=       0; connid=       0
- 16:34:23.133344 SMBClient 30206  in ?(0) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F9464A0; SendLength=     176; Status=       0; ConnectionType=       1
- 16:34:23.133345 SMBClient 30114  in ?(0) act {7e381306: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.133367 SMBClient 30603  in cmd.exe(7048)* act {00000000: Object=0xFFFFCD84EAE1B2E0; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc74319f-c65a-11f1-a3a8-eea7cd268ff2}; OldState=3; NewState=0; Status=0x0; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=0; Prev
- 16:34:23.133368 SMBClient 30506  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023D207C50; Fcb=0xFFFFCD84EAF75050; FileNameLength=0; Status=       0
- 16:34:23.133369 SMBClient 30501  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023D207C50; Fcb=0xFFFFCD84EAF75050; FileNameLength=0; Status=       0
- 16:34:23.133370 SMBClient 20001  in cmd.exe(7048)* act {7e381306: CurrentOrNextState=181; Context=       0
- 16:34:23.133427 SMBClient 30502  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84EAF75050; FileNameLength=0; Status=       0
- 16:34:23.133463 SMBClient 30103  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Exchange=0xFFFFE0023DFF9888; ListHead=0xFFFFDE892C587180
- 16:34:23.133463 SMBClient 30104  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Exchange=0xFFFFE0023DFF9888; ExchangeState=       6; ExchangeStatus=       0
- 16:34:23.133465 SMBClient 30111  in cmd.exe(7048)* act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=      33; ThrottlingWindowLimit=      32; OldestPendingMid=10; NextAvailableMid=11; CreditsGranted=0
- 16:34:23.133465 SMBClient 30111  in cmd.exe(7048)* act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       2; CurrentWindowLimit=      33; ThrottlingWindowLimit=      32; OldestPendingMid=10; NextAvailableMid=12; CreditsGranted=0
- 16:34:23.133465 SMBClient 30406  in cmd.exe(7048)* act {7e381306: Count=       0; Command=QRY_INFO; MessageId=10; SessionId=2051295070; TreeId=1863141655; MidCharge=1; CreditRequested=0; SendLength=     112; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.133466 SMBClient 30406  in cmd.exe(7048)* act {7e381306: Count=       1; Command=QRY_INFO; MessageId=11; SessionId=2051295070; TreeId=1863141655; MidCharge=1; CreditRequested=2; SendLength=     105; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.133466 SMBClient 2000  in cmd.exe(7048)* act {00000015: ReassembledEventID=40000; FragmentSize=      40; FragmentData=0x010000001C000000020001BD0A4D0035000000000000000030A8C93F02E0FFFFB074CD3FD9000000
- 16:34:23.133466 SMBClient 2000  in cmd.exe(7048)* act {00000015: ReassembledEventID=40000; FragmentSize=     105; FragmentData=0xFE534D4240000100000000001000000030000000700000000A00000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000000290002015200000000000000000000000000000000000000
- 16:34:23.133466 SMBClient 2000  in cmd.exe(7048)* act {00000015: ReassembledEventID=40000; FragmentSize=       7; FragmentData=0x00000000000000
- 16:34:23.133467 SMBClient 2000  in cmd.exe(7048)* act {00000015: ReassembledEventID=40000; FragmentSize=     105; FragmentData=0xFE534D4240000100000000001000020034000000000000000B00000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000000290002054C00000000000000000000000000000000000000
- 16:34:23.133467 SMBClient 30205  in cmd.exe(7048)* act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F956700; SendLength=     221; ConnectionType=       1
- 16:34:23.133697 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     221; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; startime=    1970; endtime=    1970; seqnum=       0; connid=       0
- 16:34:23.133698 SMBClient 40000  in ?(0) act {00000016: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     200; PacketData=0xFE534D4240000100000000001000000031000000680000000A00000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000
- 16:34:23.133698 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=      32; ThrottlingWindowLimit=      32; OldestPendingMid=11; NextAvailableMid=12; CreditsGranted=0
- 16:34:23.133698 SMBClient 30407  in ?(0) act {7e381306: Command=QRY_INFO; MessageId=10; AsyncId=0; SessionId=2051295070; TreeId=1863141655; CreditGranted=0; Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.133699 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       0; CurrentWindowLimit=      34; ThrottlingWindowLimit=     128; OldestPendingMid=12; NextAvailableMid=12; CreditsGranted=0
- 16:34:23.133699 SMBClient 30407  in ?(0) act {7e381306: Command=QRY_INFO; MessageId=11; AsyncId=0; SessionId=2051295070; TreeId=1863141655; CreditGranted=3; Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.133699 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     204; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; seqnum=       0; connid=       0
- 16:34:23.133700 SMBClient 30206  in ?(0) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023DF153E0; SendLength=     217; Status=       0; ConnectionType=       1
- 16:34:23.133700 SMBClient 30114  in ?(0) act {7e381306: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.133700 SMBClient 30114  in ?(0) act {7e381306: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.133715 SMBClient 30603  in cmd.exe(7048)* act {00000000: Object=0xFFFFCD84EAE1B2E0; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc74319f-c65a-11f1-a3a8-eea7cd268ff2}; OldState=0; NewState=6; Status=0xC0000128; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=
- 16:34:23.133716 SMBClient 30111  in cmd.exe(7048)* act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=      34; ThrottlingWindowLimit=     128; OldestPendingMid=12; NextAvailableMid=13; CreditsGranted=0
- 16:34:23.133716 SMBClient 30406  in cmd.exe(7048)* act {7e381306: Count=       0; Command=CLOSE   ; MessageId=12; SessionId=2051295070; TreeId=1863141655; MidCharge=1; CreditRequested=12; SendLength=      88; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.133717 SMBClient 40000  in cmd.exe(7048)* act {00000017: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=      88; PacketData=0xFE534D42400001000000000006000C0030000000000000000C00000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000
- 16:34:23.133717 SMBClient 30205  in cmd.exe(7048)* act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023EA22BA0; SendLength=      92; ConnectionType=       1
- 16:34:23.133864 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=      92; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; startime=    1970; endtime=    1970; seqnum=       0; connid=       0
- 16:34:23.133864 SMBClient 40000  in ?(0) act {00000018: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     124; PacketData=0xFE534D42400001000000000006000C0031000000000000000C00000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000
- 16:34:23.133864 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       0; CurrentWindowLimit=      45; ThrottlingWindowLimit=     128; OldestPendingMid=13; NextAvailableMid=13; CreditsGranted=0
- 16:34:23.133865 SMBClient 30407  in ?(0) act {7e381306: Command=CLOSE   ; MessageId=12; AsyncId=0; SessionId=2051295070; TreeId=1863141655; CreditGranted=12; Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.133865 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     128; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; seqnum=       0; connid=       0
- 16:34:23.133865 SMBClient 30206  in ?(0) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F956B10; SendLength=      88; Status=       0; ConnectionType=       1
- 16:34:23.133866 SMBClient 30114  in ?(0) act {7e381306: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.133868 SMBClient 30501  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84EAF75050; FileNameLength=0; Status=       0
- 16:34:23.133960 SMBClient 20001  in cmd.exe(7048)* act {7e381306: CurrentOrNextState=180; Context=       0
- 16:34:23.133962 SMBClient 30505  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E9D92520; FileNameLength=0; Status=       0
- 16:34:23.133963 SMBClient 30502  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E9D92520; FileNameLength=0; Status=       0
- 16:34:23.133968 SMBClient 30603  in cmd.exe(7048)* act {00000000: Object=0xFFFFCD84EAE1AB60; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc7431a0-c65a-11f1-a3a8-eea7cd268ff2}; OldState=1; NewState=1; Status=0x0; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=0; Prev
- 16:34:23.133969 SMBClient 30404  in cmd.exe(7048)* act {7e381306: Fcb=0xFFFFCD84E9D92520; SrvOpen=0xFFFFCD84E9D927F8
- 16:34:23.133969 SMBClient 20001  in cmd.exe(7048)* act {7e381306: CurrentOrNextState=181; Context=       0
- 16:34:23.133987 SMBClient 30502  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E9D92520; FileNameLength=0; Status=       0
- 16:34:23.133992 SMBClient 30502  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E9D92520; FileNameLength=0; Status=       0
- 16:34:23.134052 SMBClient 20001  in cmd.exe(7048)* act {7e381306: CurrentOrNextState=180; Context=       0
- 16:34:23.134052 SMBClient 30505  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84EAF915E0; FileNameLength=0; Status=       0
- 16:34:23.134053 SMBClient 30502  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84EAF915E0; FileNameLength=0; Status=       0
- 16:34:23.134058 SMBClient 30603  in cmd.exe(7048)* act {00000000: Object=0xFFFFCD84EAE1B760; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc7431a1-c65a-11f1-a3a8-eea7cd268ff2}; OldState=1; NewState=1; Status=0x0; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=0; Prev
- 16:34:23.134058 SMBClient 30404  in cmd.exe(7048)* act {7e381306: Fcb=0xFFFFCD84EAF915E0; SrvOpen=0xFFFFCD84EAF918B8
- 16:34:23.134058 SMBClient 20001  in cmd.exe(7048)* act {7e381306: CurrentOrNextState=181; Context=       0
- 16:34:23.134074 SMBClient 30502  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84EAF915E0; FileNameLength=0; Status=       0
- 16:34:23.134077 SMBClient 30502  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84EAF915E0; FileNameLength=0; Status=       0
- 16:34:23.134181 SMBClient 20001  in cmd.exe(7048)* act {7e381306: CurrentOrNextState=180; Context=       0
- 16:34:23.134182 SMBClient 30505  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84EAF925E0; FileNameLength=0; Status=       0
- 16:34:23.134182 SMBClient 30502  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84EAF925E0; FileNameLength=0; Status=       0
- 16:34:23.134187 SMBClient 30603  in cmd.exe(7048)* act {00000000: Object=0xFFFFCD84EAE1B760; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc7431a2-c65a-11f1-a3a8-eea7cd268ff2}; OldState=1; NewState=1; Status=0x0; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=0; Prev
- 16:34:23.134188 SMBClient 30404  in cmd.exe(7048)* act {7e381306: Fcb=0xFFFFCD84EAF925E0; SrvOpen=0xFFFFCD84EAF928B8
- 16:34:23.134188 SMBClient 20001  in cmd.exe(7048)* act {7e381306: CurrentOrNextState=181; Context=       0
- 16:34:23.134204 SMBClient 30502  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84EAF925E0; FileNameLength=0; Status=       0
- 16:34:23.134510 SMBClient 20001  in cmd.exe(7048)* act {7e381306: CurrentOrNextState=180; Context=       0
- 16:34:23.134512 SMBClient 30505  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:23.134513 SMBClient 30502  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:23.134514 SMBClient 30603  in cmd.exe(7048)* act {00000000: Object=0xFFFFCD84EAE191E0; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc7431a3-c65a-11f1-a3a8-eea7cd268ff2}; OldState=1; NewState=3; Status=0x0; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=0; Prev
- 16:34:23.134522 SMBClient 30111  in cmd.exe(7048)* act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=      45; ThrottlingWindowLimit=     128; OldestPendingMid=13; NextAvailableMid=14; CreditsGranted=0
- 16:34:23.134522 SMBClient 30406  in cmd.exe(7048)* act {7e381306: Count=       0; Command=CREATE  ; MessageId=13; SessionId=2051295070; TreeId=1863141655; MidCharge=1; CreditRequested=11; SendLength=     252; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.134523 SMBClient 40000  in cmd.exe(7048)* act {00000019: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     252; PacketData=0xFE534D42400001000000000005000B0030000000000000000D00000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000
- 16:34:23.134523 SMBClient 30205  in cmd.exe(7048)* act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023EA25920; SendLength=     256; ConnectionType=       1
- 16:34:23.135421 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     256; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; startime=    1970; endtime=    1970; seqnum=       0; connid=       0
- 16:34:23.135423 SMBClient 40000  in ?(0) act {0000001a: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     316; PacketData=0xFE534D42400001000000000005000B0031000000000000000D00000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000
- 16:34:23.135424 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       0; CurrentWindowLimit=      55; ThrottlingWindowLimit=     128; OldestPendingMid=14; NextAvailableMid=14; CreditsGranted=0
- 16:34:23.135424 SMBClient 30407  in ?(0) act {7e381306: Command=CREATE  ; MessageId=13; AsyncId=0; SessionId=2051295070; TreeId=1863141655; CreditGranted=11; Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.135425 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     320; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; seqnum=       0; connid=       0
- 16:34:23.135426 SMBClient 30206  in ?(0) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023EA25920; SendLength=     252; Status=       0; ConnectionType=       1
- 16:34:23.135426 SMBClient 30114  in ?(0) act {7e381306: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.135445 SMBClient 30603  in cmd.exe(7048)* act {00000000: Object=0xFFFFCD84EAE191E0; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc7431a3-c65a-11f1-a3a8-eea7cd268ff2}; OldState=3; NewState=0; Status=0x0; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=0; Prev
- 16:34:23.135446 SMBClient 30506  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:23.135447 SMBClient 30501  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:23.135448 SMBClient 20001  in cmd.exe(7048)* act {7e381306: CurrentOrNextState=181; Context=       0
- 16:34:23.135495 SMBClient 30502  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:23.135513 SMBClient 30103  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Exchange=0xFFFFE0023DFF9AC8; ListHead=0xFFFFDE892C586FA0
- 16:34:23.135513 SMBClient 30104  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Exchange=0xFFFFE0023DFF9AC8; ExchangeState=       6; ExchangeStatus=       0
- 16:34:23.135516 SMBClient 30111  in cmd.exe(7048)* act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=      55; ThrottlingWindowLimit=     128; OldestPendingMid=14; NextAvailableMid=15; CreditsGranted=0
- 16:34:23.135516 SMBClient 30111  in cmd.exe(7048)* act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       2; CurrentWindowLimit=      55; ThrottlingWindowLimit=     128; OldestPendingMid=14; NextAvailableMid=16; CreditsGranted=0
- 16:34:23.135517 SMBClient 30406  in cmd.exe(7048)* act {7e381306: Count=       0; Command=QRY_DIR ; MessageId=14; SessionId=2051295070; TreeId=1863141655; MidCharge=1; CreditRequested=0; SendLength=     104; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.135517 SMBClient 30406  in cmd.exe(7048)* act {7e381306: Count=       1; Command=QRY_DIR ; MessageId=15; SessionId=2051295070; TreeId=1863141655; MidCharge=1; CreditRequested=19; SendLength=      98; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.135517 SMBClient 2000  in cmd.exe(7048)* act {0000001b: ReassembledEventID=40000; FragmentSize=      40; FragmentData=0x010000001C000000020001BD0A4D0035000000000000000030A8C93F02E0FFFFB074CD3FCA000000
- 16:34:23.135517 SMBClient 2000  in cmd.exe(7048)* act {0000001b: ReassembledEventID=40000; FragmentSize=      98; FragmentData=0xFE534D4240000100000000000E00000030000000680000000E00000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000000210025000000000080D76C690000000028533A6500000000
- 16:34:23.135518 SMBClient 2000  in cmd.exe(7048)* act {0000001b: ReassembledEventID=40000; FragmentSize=       6; FragmentData=0x000000000000
- 16:34:23.135518 SMBClient 2000  in cmd.exe(7048)* act {0000001b: ReassembledEventID=40000; FragmentSize=      98; FragmentData=0xFE534D4240000100000000000E00130034000000000000000F00000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000000210025000000000080D76C690000000028533A6500000000
- 16:34:23.135518 SMBClient 30205  in cmd.exe(7048)* act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F956700; SendLength=     206; ConnectionType=       1
- 16:34:23.135779 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     206; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; startime=    1970; endtime=    1970; seqnum=       0; connid=       0
- 16:34:23.135780 SMBClient 40000  in ?(0) act {0000001c: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     504; PacketData=0xFE534D4240000100000000000E00000031000000A80100000E00000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000
- 16:34:23.135781 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=      54; ThrottlingWindowLimit=     128; OldestPendingMid=15; NextAvailableMid=16; CreditsGranted=0
- 16:34:23.135781 SMBClient 30407  in ?(0) act {7e381306: Command=QRY_DIR ; MessageId=14; AsyncId=0; SessionId=2051295070; TreeId=1863141655; CreditGranted=0; Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.135782 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       0; CurrentWindowLimit=      73; ThrottlingWindowLimit=     128; OldestPendingMid=16; NextAvailableMid=16; CreditsGranted=0
- 16:34:23.135782 SMBClient 30407  in ?(0) act {7e381306: Command=QRY_DIR ; MessageId=15; AsyncId=0; SessionId=2051295070; TreeId=1863141655; CreditGranted=20; Status=2147483654; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.135782 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     508; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; seqnum=       0; connid=       0
- 16:34:23.135783 SMBClient 30206  in ?(0) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023EA25920; SendLength=     202; Status=       0; ConnectionType=       1
- 16:34:23.135784 SMBClient 30114  in ?(0) act {7e381306: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.135784 SMBClient 30114  in ?(0) act {7e381306: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.135791 SMBClient 30507  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:23.136021 SMBClient 20001  in cmd.exe(7048)* act {7e381306: CurrentOrNextState=180; Context=       0
- 16:34:23.136022 SMBClient 30505  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:23.136023 SMBClient 30502  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:23.136032 SMBClient 30603  in cmd.exe(7048)* act {00000000: Object=0xFFFFCD84EAE1A0E0; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc7431a4-c65a-11f1-a3a8-eea7cd268ff2}; OldState=1; NewState=1; Status=0x0; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=0; Prev
- 16:34:23.136032 SMBClient 30404  in cmd.exe(7048)* act {7e381306: Fcb=0xFFFFCD84E84A6820; SrvOpen=0xFFFFCD84EAF1ADA0
- 16:34:23.136033 SMBClient 20001  in cmd.exe(7048)* act {7e381306: CurrentOrNextState=181; Context=       0
- 16:34:23.136039 SMBClient 30603  in cmd.exe(7048)* act {00000000: Object=0xFFFFCD84EAE1A0E0; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc7431a4-c65a-11f1-a3a8-eea7cd268ff2}; OldState=1; NewState=4; Status=0x0; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=0; Prev
- 16:34:23.136040 SMBClient 30405  in cmd.exe(7048)* act {00000000: Fcb=0xFFFFCD84E84A6820; SrvOpen=0xFFFFCD84EAF1ADA0
- 16:34:23.136041 SMBClient 30103  in cmd.exe(7048)* act {00000000: RxContext=0xFFFFE002399C2220; Exchange=0xFFFFE0023DFF8CF0; ListHead=0xFFFFDE892C586F10
- 16:34:23.136041 SMBClient 30103  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Exchange=0xFFFFE0023DFF9C40; ListHead=0xFFFFDE892C5871A0
- 16:34:23.136041 SMBClient 30104  in cmd.exe(7048)* act {00000000: RxContext=0xFFFFE002399C2220; Exchange=0xFFFFE0023DFF8CF0; ExchangeState=       6; ExchangeStatus=       0
- 16:34:23.136042 SMBClient 30104  in cmd.exe(7048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Exchange=0xFFFFE0023DFF9C40; ExchangeState=       6; ExchangeStatus=       0
- 16:34:23.136045 SMBClient 30111  in cmd.exe(7048)* act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=      73; ThrottlingWindowLimit=     128; OldestPendingMid=16; NextAvailableMid=17; CreditsGranted=0
- 16:34:23.136045 SMBClient 30111  in cmd.exe(7048)* act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       2; CurrentWindowLimit=      73; ThrottlingWindowLimit=     128; OldestPendingMid=16; NextAvailableMid=18; CreditsGranted=0
- 16:34:23.136045 SMBClient 30406  in cmd.exe(7048)* act {00000000: Count=       0; Command=CREATE  ; MessageId=16; SessionId=2051295070; TreeId=1863141655; MidCharge=1; CreditRequested=0; SendLength=     152; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.136045 SMBClient 30406  in cmd.exe(7048)* act {7e381306: Count=       1; Command=QRY_INFO; MessageId=17; SessionId=2051295070; TreeId=1863141655; MidCharge=1; CreditRequested=15; SendLength=     104; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.136046 SMBClient 2000  in cmd.exe(7048)* act {0000001d: ReassembledEventID=40000; FragmentSize=      40; FragmentData=0x010000001C000000020001BD0A4D0035000000000000000030A8C93F02E0FFFFB074CD3F00010000
- 16:34:23.136046 SMBClient 2000  in cmd.exe(7048)* act {0000001d: ReassembledEventID=40000; FragmentSize=     152; FragmentData=0xFE534D4240000100000000000500000010000000980000001000000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000000390000000200000000000000000000000000000000000000
- 16:34:23.136046 SMBClient 2000  in cmd.exe(7048)* act {0000001d: ReassembledEventID=40000; FragmentSize=     104; FragmentData=0xFE534D42400001000000000010000F0034000000000000001100000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000000290002072000000068000000000000000000000000000000
- 16:34:23.136046 SMBClient 30205  in cmd.exe(7048)* act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F956B10; SendLength=     260; ConnectionType=       1
- 16:34:23.136496 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     260; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; startime=    1970; endtime=    1970; seqnum=       0; connid=       0
- 16:34:23.136497 SMBClient 40000  in ?(0) act {0000001e: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     288; PacketData=0xFE534D4240000100000000000500000011000000B80000001000000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000
- 16:34:23.136498 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=      72; ThrottlingWindowLimit=     128; OldestPendingMid=17; NextAvailableMid=18; CreditsGranted=0
- 16:34:23.136498 SMBClient 30407  in ?(0) act {00000000: Command=CREATE  ; MessageId=16; AsyncId=0; SessionId=2051295070; TreeId=1863141655; CreditGranted=0; Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.136499 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       0; CurrentWindowLimit=      87; ThrottlingWindowLimit=     128; OldestPendingMid=18; NextAvailableMid=18; CreditsGranted=0
- 16:34:23.136499 SMBClient 30407  in ?(0) act {7e381306: Command=QRY_INFO; MessageId=17; AsyncId=0; SessionId=2051295070; TreeId=1863141655; CreditGranted=16; Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.136500 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     292; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; seqnum=       0; connid=       0
- 16:34:23.136501 SMBClient 30206  in ?(0) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F956B10; SendLength=     256; Status=       0; ConnectionType=       1
- 16:34:23.136501 SMBClient 30114  in ?(0) act {00000000: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.136501 SMBClient 30114  in ?(0) act {7e381306: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.136512 SMBClient 30603  in System(4) act {00000000: Object=0xFFFFCD84EAE1A0E0; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc7431a4-c65a-11f1-a3a8-eea7cd268ff2}; OldState=4; NewState=0; Status=0x0; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=0; Prev
- 16:34:23.136616 SMBClient 30603  in cmd.exe(7048)* act {00000000: Object=0xFFFFCD84EAE1A0E0; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc7431a4-c65a-11f1-a3a8-eea7cd268ff2}; OldState=0; NewState=6; Status=0xC0000128; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=
- 16:34:23.136617 SMBClient 30111  in cmd.exe(7048)* act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=      87; ThrottlingWindowLimit=     128; OldestPendingMid=18; NextAvailableMid=19; CreditsGranted=0
- 16:34:23.136618 SMBClient 30406  in cmd.exe(7048)* act {7e381306: Count=       0; Command=CLOSE   ; MessageId=18; SessionId=2051295070; TreeId=1863141655; MidCharge=1; CreditRequested=6; SendLength=      88; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.136618 SMBClient 40000  in cmd.exe(7048)* act {0000001f: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=      88; PacketData=0xFE534D4240000100000000000600060030000000000000001200000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000
- 16:34:23.136619 SMBClient 30205  in cmd.exe(7048)* act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F9464A0; SendLength=      92; ConnectionType=       1
- 16:34:23.136810 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=      92; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; startime=    1970; endtime=    1970; seqnum=       0; connid=       0
- 16:34:23.136811 SMBClient 40000  in ?(0) act {00000020: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     124; PacketData=0xFE534D4240000100000000000600060031000000000000001200000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000
- 16:34:23.136812 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       0; CurrentWindowLimit=      92; ThrottlingWindowLimit=     128; OldestPendingMid=19; NextAvailableMid=19; CreditsGranted=0
- 16:34:23.136812 SMBClient 30407  in ?(0) act {7e381306: Command=CLOSE   ; MessageId=18; AsyncId=0; SessionId=2051295070; TreeId=1863141655; CreditGranted=6; Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.136813 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     128; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; seqnum=       0; connid=       0
- 16:34:23.136814 SMBClient 30206  in ?(0) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F945530; SendLength=      88; Status=       0; ConnectionType=       1
- 16:34:23.136814 SMBClient 30114  in ?(0) act {7e381306: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:23.139553 Kernel-Process 2 ProcessStop in cmd.exe(7048)* act {00000000: ProcessID=    7048; ProcessSequenceNumber=160; CreateTime=2026-10-12T16:34:23.086753900Z; ExitTime=2026-10-12T16:34:23.139516300Z; ExitCode=       0; TokenElevationType=       1; HandleCount=      44; CommitCharge=4734976; CommitPeak=494796
- 16:34:23.140152 Kernel-Process 2 ProcessStop in conhost.exe(6868)* act {00000000: ProcessID=    6868; ProcessSequenceNumber=161; CreateTime=2026-10-12T16:34:23.109860700Z; ExitTime=2026-10-12T16:34:23.140069500Z; ExitCode=       0; TokenElevationType=       1; HandleCount=     101; CommitCharge=6569984; CommitPeak=657817
- 16:34:23.160251 Kernel-Network 42 KERNEL_NETWORK_TASK_UDPIP in svchost.exe(3540) act {00000000: PID=    3540; size=     137; daddr=239.255.255.250; saddr=127.0.0.1; dport=1900; sport=64697; seqnum=       0; connid=       0
- 16:34:23.160297 Kernel-Network 43 KERNEL_NETWORK_TASK_UDPIP in svchost.exe(3540) act {00000000: PID=    3540; size=     137; daddr=239.255.255.250; saddr=127.0.0.1; dport=1900; sport=64697; seqnum=       0; connid=       0

### read (pid 6644, exit 0)

- 16:34:27.178647 Kernel-Process 1 ProcessStart in cmd.exe(6644)* act {00000000: ProcessID=    5632; ProcessSequenceNumber=165; CreateTime=2026-10-12T16:34:27.178630100Z; ParentProcessID=    6644; ParentProcessSequenceNumber=164; SessionID=       0; Flags=       0; ProcessTokenElevationType=       1; ProcessTokenIsEleva
- 16:34:27.198637 SMBClient 20001  in cmd.exe(6644)* act {7e381306: CurrentOrNextState=180; Context=       0
- 16:34:27.198639 SMBClient 30505  in cmd.exe(6644)* act {7e381306: RxContext=0xFFFFE0023D207C50; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:27.198641 SMBClient 30502  in cmd.exe(6644)* act {7e381306: RxContext=0xFFFFE0023D207C50; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:27.198653 SMBClient 30603  in cmd.exe(6644)* act {00000000: Object=0xFFFFCD84EAE1A0E0; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc7431aa-c65a-11f1-a3a8-eea7cd268ff2}; OldState=1; NewState=1; Status=0x0; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=0; Prev
- 16:34:27.198653 SMBClient 30404  in cmd.exe(6644)* act {7e381306: Fcb=0xFFFFCD84E84A6820; SrvOpen=0xFFFFCD84EAE03DA0
- 16:34:27.198653 SMBClient 20001  in cmd.exe(6644)* act {7e381306: CurrentOrNextState=181; Context=       0
- 16:34:27.198666 SMBClient 30502  in cmd.exe(6644)* act {7e381306: RxContext=0xFFFFE0023D207C50; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:27.198677 SMBClient 30507  in cmd.exe(6644)* act {7e381306: RxContext=0xFFFFE0023D207C50; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:27.198714 SMBClient 20001  in cmd.exe(6644)* act {7e381306: CurrentOrNextState=180; Context=       0
- 16:34:27.198718 SMBClient 30505  in cmd.exe(6644)* act {7e381306: RxContext=0xFFFFE0023D207C50; Fcb=0xFFFFCD84EAF75050; FileNameLength=10; FileName=\hello.txt; Status=       0
- 16:34:27.198719 SMBClient 30508  in cmd.exe(6644)* act {7e381306: RxContext=0xFFFFE0023D207C50; Fcb=0xFFFFCD84EAF75050; FileNameLength=10; FileName=\hello.txt; Status=       0
- 16:34:27.198719 SMBClient 30502  in cmd.exe(6644)* act {7e381306: RxContext=0xFFFFE0023D207C50; Fcb=0xFFFFCD84EAF75050; FileNameLength=10; FileName=\hello.txt; Status=3221225494
- 16:34:27.198719 SMBClient 30508  in cmd.exe(6644)* act {7e381306: RxContext=0xFFFFE0023D207C50; Fcb=0xFFFFCD84EAF75050; FileNameLength=10; FileName=\hello.txt; Status=       0
- 16:34:27.198726 SMBClient 30603  in cmd.exe(6644)* act {00000000: Object=0xFFFFCD84EAE1ACE0; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc7431ab-c65a-11f1-a3a8-eea7cd268ff2}; OldState=1; NewState=1; Status=0x0; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=10; Obj
- 16:34:27.198726 SMBClient 30404  in cmd.exe(6644)* act {7e381306: Fcb=0xFFFFCD84EAF75050; SrvOpen=0xFFFFCD84EAF75328
- 16:34:27.198726 SMBClient 20001  in cmd.exe(6644)* act {7e381306: CurrentOrNextState=181; Context=       0
- 16:34:27.198745 SMBClient 30502  in cmd.exe(6644)* act {7e381306: RxContext=0xFFFFE0023D207C50; Fcb=0xFFFFCD84EAF75050; FileNameLength=10; FileName=\hello.txt; Status=3221225494
- 16:34:27.198745 SMBClient 30508  in cmd.exe(6644)* act {7e381306: RxContext=0xFFFFE0023D207C50; Fcb=0xFFFFCD84EAF75050; FileNameLength=10; FileName=\hello.txt; Status=       0
- 16:34:27.198750 SMBClient 30502  in cmd.exe(6644)* act {7e381306: RxContext=0xFFFFE0023D207C50; Fcb=0xFFFFCD84EAF75050; FileNameLength=10; FileName=\hello.txt; Status=3221225494
- 16:34:27.198751 SMBClient 30508  in cmd.exe(6644)* act {7e381306: RxContext=0xFFFFE0023D207C50; Fcb=0xFFFFCD84EAF75050; FileNameLength=10; FileName=\hello.txt; Status=       0
- 16:34:27.198807 SMBClient 20001  in cmd.exe(6644)* act {7e381306: CurrentOrNextState=180; Context=       0
- 16:34:27.198808 SMBClient 30505  in cmd.exe(6644)* act {7e381306: RxContext=0xFFFFE0023D207C50; Fcb=0xFFFFCD84E97C7010; FileNameLength=10; FileName=\hello.txt; Status=       0
- 16:34:27.198810 SMBClient 30603  in cmd.exe(6644)* act {00000000: Object=0xFFFFCD84EAE194E0; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc7431ac-c65a-11f1-a3a8-eea7cd268ff2}; OldState=1; NewState=3; Status=0x0; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=10; Obj
- 16:34:27.198814 SMBClient 30111  in cmd.exe(6644)* act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=      92; ThrottlingWindowLimit=     128; OldestPendingMid=19; NextAvailableMid=20; CreditsGranted=0
- 16:34:27.198815 SMBClient 30406  in cmd.exe(6644)* act {7e381306: Count=       0; Command=CREATE  ; MessageId=19; SessionId=2051295070; TreeId=1863141655; MidCharge=1; CreditRequested=5; SendLength=     324; VcEndpoint=0xFFFFE0023F605020
- 16:34:27.198817 SMBClient 40000  in cmd.exe(6644)* act {00000021: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     324; PacketData=0xFE534D4240000100000000000500050030000000000000001300000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000
- 16:34:27.198818 SMBClient 30205  in cmd.exe(6644)* act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023E345470; SendLength=     328; ConnectionType=       1
- 16:34:27.199479 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     328; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; startime=    2377; endtime=    2377; seqnum=       0; connid=       0
- 16:34:27.199491 SMBClient 40000  in ?(0) act {00000022: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     348; PacketData=0xFE534D4240000100000000000500050031000000000000001300000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000
- 16:34:27.199500 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       0; CurrentWindowLimit=      96; ThrottlingWindowLimit=     128; OldestPendingMid=20; NextAvailableMid=20; CreditsGranted=0
- 16:34:27.199501 SMBClient 30407  in ?(0) act {7e381306: Command=CREATE  ; MessageId=19; AsyncId=0; SessionId=2051295070; TreeId=1863141655; CreditGranted=5; Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:27.199502 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     352; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; seqnum=       0; connid=       0
- 16:34:27.199504 SMBClient 30206  in ?(0) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023E345470; SendLength=     324; Status=       0; ConnectionType=       1
- 16:34:27.199505 SMBClient 30114  in ?(0) act {7e381306: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:27.199523 SMBClient 30603  in cmd.exe(6644)* act {00000000: Object=0xFFFFCD84EAE194E0; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc7431ac-c65a-11f1-a3a8-eea7cd268ff2}; OldState=3; NewState=0; Status=0x0; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=10; Obj
- 16:34:27.199524 SMBClient 30506  in cmd.exe(6644)* act {7e381306: RxContext=0xFFFFE0023D207C50; Fcb=0xFFFFCD84E97C7010; FileNameLength=10; FileName=\hello.txt; Status=       0
- 16:34:27.199525 SMBClient 30501  in cmd.exe(6644)* act {7e381306: RxContext=0xFFFFE0023D207C50; Fcb=0xFFFFCD84E97C7010; FileNameLength=10; FileName=\hello.txt; Status=       0
- 16:34:27.199527 SMBClient 20001  in cmd.exe(6644)* act {7e381306: CurrentOrNextState=181; Context=       0
- 16:34:27.199580 SMBClient 30502  in cmd.exe(6644)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E97C7010; FileNameLength=10; FileName=\hello.txt; Status=       0
- 16:34:27.199593 SMBClient 30502  in cmd.exe(6644)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E97C7010; FileNameLength=10; FileName=\hello.txt; Status=3221225494
- 16:34:27.199594 SMBClient 30111  in cmd.exe(6644)* act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=      96; ThrottlingWindowLimit=     128; OldestPendingMid=20; NextAvailableMid=21; CreditsGranted=0
- 16:34:27.199595 SMBClient 30406  in cmd.exe(6644)* act {7e381306: Count=       0; Command=QRY_INFO; MessageId=20; SessionId=2051295070; TreeId=1863141655; MidCharge=1; CreditRequested=5; SendLength=     104; VcEndpoint=0xFFFFE0023F605020
- 16:34:27.199595 SMBClient 40000  in cmd.exe(6644)* act {00000023: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     104; PacketData=0xFE534D4240000100000000001000050030000000000000001400000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000
- 16:34:27.199596 SMBClient 30205  in cmd.exe(6644)* act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F333860; SendLength=     108; ConnectionType=       1
- 16:34:27.199932 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     108; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; startime=    2377; endtime=    2377; seqnum=       0; connid=       0
- 16:34:27.199934 SMBClient 40000  in ?(0) act {00000024: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=      73; PacketData=0xFE534D4240000100220000C01000050031000000000000001400000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000
- 16:34:27.199935 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       0; CurrentWindowLimit=     100; ThrottlingWindowLimit=     128; OldestPendingMid=21; NextAvailableMid=21; CreditsGranted=0
- 16:34:27.199935 SMBClient 30407  in ?(0) act {7e381306: Command=QRY_INFO; MessageId=20; AsyncId=0; SessionId=2051295070; TreeId=1863141655; CreditGranted=5; Status=3221225506; VcEndpoint=0xFFFFE0023F605020
- 16:34:27.199936 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=      77; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; seqnum=       0; connid=       0
- 16:34:27.199937 SMBClient 30206  in ?(0) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F9551E0; SendLength=     104; Status=       0; ConnectionType=       1
- 16:34:27.199937 SMBClient 30114  in ?(0) act {7e381306: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:27.200272 SMBClient 30111  in MsMpEng.exe(2564) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=     100; ThrottlingWindowLimit=     128; OldestPendingMid=21; NextAvailableMid=22; CreditsGranted=0
- 16:34:27.200273 SMBClient 30406  in MsMpEng.exe(2564) act {7e381306: Count=       0; Command=READ    ; MessageId=21; SessionId=2051295070; TreeId=1863141655; MidCharge=1; CreditRequested=4; SendLength=     113; VcEndpoint=0xFFFFE0023F605020
- 16:34:27.200273 SMBClient 40000  in MsMpEng.exe(2564) act {00000025: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     113; PacketData=0xFE534D4240000100000000000800040030000000000000001500000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000
- 16:34:27.200274 SMBClient 30205  in MsMpEng.exe(2564) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F9551E0; SendLength=     117; ConnectionType=       1
- 16:34:27.200887 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     117; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; startime=    2377; endtime=    2377; seqnum=       0; connid=       0
- 16:34:27.200896 SMBClient 40000  in ?(0) act {00000026: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=      86; PacketData=0xFE534D4240000100000000000800040031000000000000001500000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000
- 16:34:27.200900 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       0; CurrentWindowLimit=     103; ThrottlingWindowLimit=     128; OldestPendingMid=22; NextAvailableMid=22; CreditsGranted=0
- 16:34:27.200903 SMBClient 30407  in ?(0) act {7e381306: Command=READ    ; MessageId=21; AsyncId=0; SessionId=2051295070; TreeId=1863141655; CreditGranted=4; Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:27.200908 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=      90; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; seqnum=       0; connid=       0
- 16:34:27.200912 SMBClient 30206  in ?(0) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F9551E0; SendLength=     113; Status=       0; ConnectionType=       1
- 16:34:27.200913 SMBClient 30114  in ?(0) act {7e381306: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:27.204099 SMBClient 30502  in cmd.exe(6644)* act {7e381306: RxContext=0xFFFFE0023D207C50; Fcb=0xFFFFCD84E97C7010; FileNameLength=10; FileName=\hello.txt; Status=       0
- 16:34:27.204781 Kernel-Process 2 ProcessStop in cmd.exe(6644)* act {00000000: ProcessID=    6644; ProcessSequenceNumber=164; CreateTime=2026-10-12T16:34:27.117553800Z; ExitTime=2026-10-12T16:34:27.204741000Z; ExitCode=       0; TokenElevationType=       1; HandleCount=      43; CommitCharge=4227072; CommitPeak=431308
- 16:34:27.205258 Kernel-Process 2 ProcessStop in conhost.exe(5632)* act {00000000: ProcessID=    5632; ProcessSequenceNumber=165; CreateTime=2026-10-12T16:34:27.178630100Z; ExitTime=2026-10-12T16:34:27.205176300Z; ExitCode=       0; TokenElevationType=       1; HandleCount=     101; CommitCharge=6578176; CommitPeak=658636

### unmap (pid 7004, exit 0)

- 16:34:31.215330 Kernel-Process 1 ProcessStart in cmd.exe(7004)* act {00000000: ProcessID=    6516; ProcessSequenceNumber=168; CreateTime=2026-10-12T16:34:31.215311500Z; ParentProcessID=    7004; ParentProcessSequenceNumber=167; SessionID=       0; Flags=       0; ProcessTokenElevationType=       1; ProcessTokenIsEleva
- 16:34:31.234818 Kernel-Process 1 ProcessStart in cmd.exe(7004)* act {00000000: ProcessID=    4220; ProcessSequenceNumber=169; CreateTime=2026-10-12T16:34:31.234803200Z; ParentProcessID=    7004; ParentProcessSequenceNumber=167; SessionID=       0; Flags=       0; ProcessTokenElevationType=       1; ProcessTokenIsEleva
- 16:34:31.245579 Kernel-Process 2 ProcessStop in net.exe(4220)* act {00000000: ProcessID=    4220; ProcessSequenceNumber=169; CreateTime=2026-10-12T16:34:31.234803200Z; ExitTime=2026-10-12T16:34:31.245515400Z; ExitCode=       0; TokenElevationType=       1; HandleCount=      63; CommitCharge=1306624; CommitPeak=130662
- 16:34:31.248159 Kernel-Process 2 ProcessStop in cmd.exe(7004)* act {00000000: ProcessID=    7004; ProcessSequenceNumber=167; CreateTime=2026-10-12T16:34:31.195469800Z; ExitTime=2026-10-12T16:34:31.248121600Z; ExitCode=       0; TokenElevationType=       1; HandleCount=      47; CommitCharge=4403200; CommitPeak=440320
- 16:34:31.248579 Kernel-Process 2 ProcessStop in conhost.exe(6516)* act {00000000: ProcessID=    6516; ProcessSequenceNumber=168; CreateTime=2026-10-12T16:34:31.215311500Z; ExitTime=2026-10-12T16:34:31.248503900Z; ExitCode=       0; TokenElevationType=       1; HandleCount=     101; CommitCharge=6582272; CommitPeak=659046

### list-unmapped (pid 6048, exit 0)

- 16:34:35.238191 SMBClient 30601  in System(4) act {00000000: Object=0xFFFFE0023F844A30; OldState=0; NewState=6; Status=0xC000020C; NameLength=16; ObjectName=\10.77.0.53\IPC$
- 16:34:35.238194 SMBClient 30111  in System(4) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=     103; ThrottlingWindowLimit=     128; OldestPendingMid=22; NextAvailableMid=23; CreditsGranted=0
- 16:34:35.238196 SMBClient 30406  in System(4) act {00000000: Count=       0; Command=TRE_DCON; MessageId=22; SessionId=2051295070; TreeId=2425976673; MidCharge=1; CreditRequested=4; SendLength=      68; VcEndpoint=0xFFFFE0023F605020
- 16:34:35.238213 SMBClient 40000  in System(4) act {00000027: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=      68; PacketData=0xFE534D4240000100000000000400040010000000000000001600000000000000FFFE0000617799905E47447A0000000000000000000000000000000000000
- 16:34:35.238215 SMBClient 30205  in System(4) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F9551E0; SendLength=      72; ConnectionType=       1
- 16:34:35.238872 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=      72; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; startime=    3180; endtime=    3181; seqnum=       0; connid=       0
- 16:34:35.238876 SMBClient 40000  in ?(0) act {00000028: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=      68; PacketData=0xFE534D4240000100000000000400040011000000000000001600000000000000FFFE0000617799905E47447A0000000000000000000000000000000000000
- 16:34:35.238878 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       0; CurrentWindowLimit=     106; ThrottlingWindowLimit=     128; OldestPendingMid=23; NextAvailableMid=23; CreditsGranted=0
- 16:34:35.238878 SMBClient 30407  in ?(0) act {00000000: Command=TRE_DCON; MessageId=22; AsyncId=0; SessionId=2051295070; TreeId=2425976673; CreditGranted=4; Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:35.238880 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=      72; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; seqnum=       0; connid=       0
- 16:34:35.238882 SMBClient 30206  in ?(0) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F956B10; SendLength=      68; Status=       0; ConnectionType=       1
- 16:34:35.238882 SMBClient 30114  in ?(0) act {00000000: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:35.238891 SMBClient 30601  in System(4) act {00000000: Object=0xFFFFE0023F844A30; OldState=6; NewState=9; Status=0xC00000C9; NameLength=16; ObjectName=\10.77.0.53\IPC$
- 16:34:35.262769 Kernel-Process 1 ProcessStart in cmd.exe(6048)* act {00000000: ProcessID=    6504; ProcessSequenceNumber=171; CreateTime=2026-10-12T16:34:35.262749800Z; ParentProcessID=    6048; ParentProcessSequenceNumber=170; SessionID=       0; Flags=       0; ProcessTokenElevationType=       1; ProcessTokenIsEleva
- 16:34:35.282877 SMBClient 20001  in cmd.exe(6048)* act {7e381306: CurrentOrNextState=180; Context=       0
- 16:34:35.282880 SMBClient 30505  in cmd.exe(6048)* act {7e381306: RxContext=0xFFFFE0023D207C50; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:35.282882 SMBClient 30502  in cmd.exe(6048)* act {7e381306: RxContext=0xFFFFE0023D207C50; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=3221225494
- 16:34:35.282883 SMBClient 30603  in cmd.exe(6048)* act {00000000: Object=0xFFFFCD84EAE19360; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc7431b2-c65a-11f1-a3a8-eea7cd268ff2}; OldState=1; NewState=3; Status=0x0; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=0; Prev
- 16:34:35.282888 SMBClient 30111  in cmd.exe(6048)* act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=     106; ThrottlingWindowLimit=     128; OldestPendingMid=23; NextAvailableMid=24; CreditsGranted=0
- 16:34:35.282888 SMBClient 30406  in cmd.exe(6048)* act {7e381306: Count=       0; Command=CREATE  ; MessageId=23; SessionId=2051295070; TreeId=1863141655; MidCharge=1; CreditRequested=3; SendLength=     152; VcEndpoint=0xFFFFE0023F605020
- 16:34:35.282889 SMBClient 40000  in cmd.exe(6048)* act {00000029: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     152; PacketData=0xFE534D4240000100000000000500030030000000000000001700000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000
- 16:34:35.282890 SMBClient 30205  in cmd.exe(6048)* act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F94D8D0; SendLength=     156; ConnectionType=       1
- 16:34:35.283639 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     156; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; startime=    3185; endtime=    3185; seqnum=       0; connid=       0
- 16:34:35.283642 SMBClient 40000  in ?(0) act {0000002a: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     184; PacketData=0xFE534D4240000100000000000500030031000000000000001700000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000
- 16:34:35.283643 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       0; CurrentWindowLimit=     108; ThrottlingWindowLimit=     128; OldestPendingMid=24; NextAvailableMid=24; CreditsGranted=0
- 16:34:35.283644 SMBClient 30407  in ?(0) act {7e381306: Command=CREATE  ; MessageId=23; AsyncId=0; SessionId=2051295070; TreeId=1863141655; CreditGranted=3; Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:35.283645 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     188; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; seqnum=       0; connid=       0
- 16:34:35.283646 SMBClient 30206  in ?(0) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F94D8D0; SendLength=     152; Status=       0; ConnectionType=       1
- 16:34:35.283647 SMBClient 30114  in ?(0) act {7e381306: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:35.283672 SMBClient 30603  in cmd.exe(6048)* act {00000000: Object=0xFFFFCD84EAE19360; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc7431b2-c65a-11f1-a3a8-eea7cd268ff2}; OldState=3; NewState=0; Status=0x0; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=0; Prev
- 16:34:35.283673 SMBClient 30506  in cmd.exe(6048)* act {7e381306: RxContext=0xFFFFE0023D207C50; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:35.283675 SMBClient 30501  in cmd.exe(6048)* act {7e381306: RxContext=0xFFFFE0023D207C50; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:35.283676 SMBClient 20001  in cmd.exe(6048)* act {7e381306: CurrentOrNextState=181; Context=       0
- 16:34:35.283725 SMBClient 30103  in cmd.exe(6048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Exchange=0xFFFFE0023DFF9888; ListHead=0xFFFFDE892ADB2180
- 16:34:35.283726 SMBClient 30104  in cmd.exe(6048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Exchange=0xFFFFE0023DFF9888; ExchangeState=       6; ExchangeStatus=       0
- 16:34:35.283728 SMBClient 30111  in cmd.exe(6048)* act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=     108; ThrottlingWindowLimit=     128; OldestPendingMid=24; NextAvailableMid=25; CreditsGranted=0
- 16:34:35.283728 SMBClient 30111  in cmd.exe(6048)* act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       2; CurrentWindowLimit=     108; ThrottlingWindowLimit=     128; OldestPendingMid=24; NextAvailableMid=26; CreditsGranted=0
- 16:34:35.283729 SMBClient 30406  in cmd.exe(6048)* act {7e381306: Count=       0; Command=QRY_INFO; MessageId=24; SessionId=2051295070; TreeId=1863141655; MidCharge=1; CreditRequested=0; SendLength=     112; VcEndpoint=0xFFFFE0023F605020
- 16:34:35.283729 SMBClient 30406  in cmd.exe(6048)* act {7e381306: Count=       1; Command=QRY_INFO; MessageId=25; SessionId=2051295070; TreeId=1863141655; MidCharge=1; CreditRequested=2; SendLength=     105; VcEndpoint=0xFFFFE0023F605020
- 16:34:35.283729 SMBClient 2000  in cmd.exe(6048)* act {0000002b: ReassembledEventID=40000; FragmentSize=      40; FragmentData=0x010000001C000000020001BD0A4D0035000000000000000030A8C93F02E0FFFFB074CD3FD9000000
- 16:34:35.283730 SMBClient 2000  in cmd.exe(6048)* act {0000002b: ReassembledEventID=40000; FragmentSize=     105; FragmentData=0xFE534D4240000100000000001000000030000000700000001800000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000000290002015200000000000000000000000000000000000000
- 16:34:35.283730 SMBClient 2000  in cmd.exe(6048)* act {0000002b: ReassembledEventID=40000; FragmentSize=       7; FragmentData=0x00000000000000
- 16:34:35.283730 SMBClient 2000  in cmd.exe(6048)* act {0000002b: ReassembledEventID=40000; FragmentSize=     105; FragmentData=0xFE534D4240000100000000001000020034000000000000001900000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000000290002054C00000000000000000000000000000000000000
- 16:34:35.283730 SMBClient 30205  in cmd.exe(6048)* act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F956700; SendLength=     221; ConnectionType=       1
- 16:34:35.284053 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     221; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; startime=    3185; endtime=    3185; seqnum=       0; connid=       0
- 16:34:35.284054 SMBClient 40000  in ?(0) act {0000002c: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     200; PacketData=0xFE534D4240000100000000001000000031000000680000001800000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000
- 16:34:35.284055 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=     107; ThrottlingWindowLimit=     128; OldestPendingMid=25; NextAvailableMid=26; CreditsGranted=0
- 16:34:35.284055 SMBClient 30407  in ?(0) act {7e381306: Command=QRY_INFO; MessageId=24; AsyncId=0; SessionId=2051295070; TreeId=1863141655; CreditGranted=0; Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:35.284056 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       0; CurrentWindowLimit=     109; ThrottlingWindowLimit=     128; OldestPendingMid=26; NextAvailableMid=26; CreditsGranted=0
- 16:34:35.284056 SMBClient 30407  in ?(0) act {7e381306: Command=QRY_INFO; MessageId=25; AsyncId=0; SessionId=2051295070; TreeId=1863141655; CreditGranted=3; Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:35.284057 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     204; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; seqnum=       0; connid=       0
- 16:34:35.284058 SMBClient 30206  in ?(0) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023DF153E0; SendLength=     217; Status=       0; ConnectionType=       1
- 16:34:35.284058 SMBClient 30114  in ?(0) act {7e381306: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:35.284058 SMBClient 30114  in ?(0) act {7e381306: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:35.284080 SMBClient 30603  in cmd.exe(6048)* act {00000000: Object=0xFFFFCD84EAE19360; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc7431b2-c65a-11f1-a3a8-eea7cd268ff2}; OldState=0; NewState=6; Status=0xC0000128; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=
- 16:34:35.284082 SMBClient 30111  in cmd.exe(6048)* act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=     109; ThrottlingWindowLimit=     128; OldestPendingMid=26; NextAvailableMid=27; CreditsGranted=0
- 16:34:35.284082 SMBClient 30406  in cmd.exe(6048)* act {7e381306: Count=       0; Command=CLOSE   ; MessageId=26; SessionId=2051295070; TreeId=1863141655; MidCharge=1; CreditRequested=1; SendLength=      88; VcEndpoint=0xFFFFE0023F605020
- 16:34:35.284082 SMBClient 40000  in cmd.exe(6048)* act {0000002d: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=      88; PacketData=0xFE534D4240000100000000000600010030000000000000001A00000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000
- 16:34:35.284083 SMBClient 30205  in cmd.exe(6048)* act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F956B10; SendLength=      92; ConnectionType=       1
- 16:34:35.284256 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=      92; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; startime=    3185; endtime=    3185; seqnum=       0; connid=       0
- 16:34:35.284257 SMBClient 40000  in ?(0) act {0000002e: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     124; PacketData=0xFE534D4240000100000000000600010031000000000000001A00000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000
- 16:34:35.284257 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       0; CurrentWindowLimit=     109; ThrottlingWindowLimit=     128; OldestPendingMid=27; NextAvailableMid=27; CreditsGranted=0
- 16:34:35.284257 SMBClient 30407  in ?(0) act {7e381306: Command=CLOSE   ; MessageId=26; AsyncId=0; SessionId=2051295070; TreeId=1863141655; CreditGranted=1; Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:35.284258 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     128; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; seqnum=       0; connid=       0
- 16:34:35.284258 SMBClient 30206  in ?(0) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023EA22BA0; SendLength=      88; Status=       0; ConnectionType=       1
- 16:34:35.284258 SMBClient 30114  in ?(0) act {7e381306: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:35.284355 SMBClient 20001  in cmd.exe(6048)* act {7e381306: CurrentOrNextState=180; Context=       0
- 16:34:35.284356 SMBClient 30505  in cmd.exe(6048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:35.284357 SMBClient 30502  in cmd.exe(6048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:35.284363 SMBClient 30603  in cmd.exe(6048)* act {00000000: Object=0xFFFFCD84EAE1B760; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc7431b3-c65a-11f1-a3a8-eea7cd268ff2}; OldState=1; NewState=1; Status=0x0; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=0; Prev
- 16:34:35.284363 SMBClient 30404  in cmd.exe(6048)* act {7e381306: Fcb=0xFFFFCD84E84A6820; SrvOpen=0xFFFFCD84EAE04DA0
- 16:34:35.284363 SMBClient 20001  in cmd.exe(6048)* act {7e381306: CurrentOrNextState=181; Context=       0
- 16:34:35.284370 SMBClient 30502  in cmd.exe(6048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:35.284421 SMBClient 20001  in cmd.exe(6048)* act {7e381306: CurrentOrNextState=180; Context=       0
- 16:34:35.284421 SMBClient 30505  in cmd.exe(6048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:35.284421 SMBClient 30502  in cmd.exe(6048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:35.284426 SMBClient 30603  in cmd.exe(6048)* act {00000000: Object=0xFFFFCD84EAE1AB60; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc7431b4-c65a-11f1-a3a8-eea7cd268ff2}; OldState=1; NewState=1; Status=0x0; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=0; Prev
- 16:34:35.284426 SMBClient 30404  in cmd.exe(6048)* act {7e381306: Fcb=0xFFFFCD84E84A6820; SrvOpen=0xFFFFCD84EAF78DA0
- 16:34:35.284426 SMBClient 20001  in cmd.exe(6048)* act {7e381306: CurrentOrNextState=181; Context=       0
- 16:34:35.284430 SMBClient 30502  in cmd.exe(6048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:35.284511 SMBClient 20001  in cmd.exe(6048)* act {7e381306: CurrentOrNextState=180; Context=       0
- 16:34:35.284512 SMBClient 30505  in cmd.exe(6048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:35.284512 SMBClient 30502  in cmd.exe(6048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:35.284516 SMBClient 30603  in cmd.exe(6048)* act {00000000: Object=0xFFFFCD84EAE1A260; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc7431b5-c65a-11f1-a3a8-eea7cd268ff2}; OldState=1; NewState=1; Status=0x0; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=0; Prev
- 16:34:35.284516 SMBClient 30404  in cmd.exe(6048)* act {7e381306: Fcb=0xFFFFCD84E84A6820; SrvOpen=0xFFFFCD84EAFACD90
- 16:34:35.284516 SMBClient 20001  in cmd.exe(6048)* act {7e381306: CurrentOrNextState=181; Context=       0
- 16:34:35.284730 SMBClient 20001  in cmd.exe(6048)* act {7e381306: CurrentOrNextState=180; Context=       0
- 16:34:35.284731 SMBClient 30505  in cmd.exe(6048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:35.284731 SMBClient 30502  in cmd.exe(6048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:35.284737 SMBClient 30603  in cmd.exe(6048)* act {00000000: Object=0xFFFFCD84EAE1B760; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc7431b6-c65a-11f1-a3a8-eea7cd268ff2}; OldState=1; NewState=1; Status=0x0; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=0; Prev
- 16:34:35.284737 SMBClient 30404  in cmd.exe(6048)* act {7e381306: Fcb=0xFFFFCD84E84A6820; SrvOpen=0xFFFFCD84EAE04DA0
- 16:34:35.284737 SMBClient 20001  in cmd.exe(6048)* act {7e381306: CurrentOrNextState=181; Context=       0
- 16:34:35.284742 SMBClient 30502  in cmd.exe(6048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:35.284748 SMBClient 30507  in cmd.exe(6048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:35.284933 SMBClient 20001  in cmd.exe(6048)* act {7e381306: CurrentOrNextState=180; Context=       0
- 16:34:35.284934 SMBClient 30505  in cmd.exe(6048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:35.284934 SMBClient 30502  in cmd.exe(6048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Fcb=0xFFFFCD84E84A6820; FileNameLength=0; Status=       0
- 16:34:35.284938 SMBClient 30603  in cmd.exe(6048)* act {00000000: Object=0xFFFFCD84EAE1A0E0; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc7431b7-c65a-11f1-a3a8-eea7cd268ff2}; OldState=1; NewState=1; Status=0x0; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=0; Prev
- 16:34:35.284938 SMBClient 30404  in cmd.exe(6048)* act {7e381306: Fcb=0xFFFFCD84E84A6820; SrvOpen=0xFFFFCD84EAE0DDA0
- 16:34:35.284939 SMBClient 20001  in cmd.exe(6048)* act {7e381306: CurrentOrNextState=181; Context=       0
- 16:34:35.284943 SMBClient 30603  in cmd.exe(6048)* act {00000000: Object=0xFFFFCD84EAE1A0E0; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc7431b7-c65a-11f1-a3a8-eea7cd268ff2}; OldState=1; NewState=4; Status=0x0; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=0; Prev
- 16:34:35.284944 SMBClient 30405  in cmd.exe(6048)* act {00000000: Fcb=0xFFFFCD84E84A6820; SrvOpen=0xFFFFCD84EAE0DDA0
- 16:34:35.284945 SMBClient 30103  in cmd.exe(6048)* act {00000000: RxContext=0xFFFFE002399C2220; Exchange=0xFFFFE0023DFF8CF0; ListHead=0xFFFFDE892ADB1F10
- 16:34:35.284946 SMBClient 30103  in cmd.exe(6048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Exchange=0xFFFFE0023DFF9C40; ListHead=0xFFFFDE892ADB21A0
- 16:34:35.284946 SMBClient 30104  in cmd.exe(6048)* act {00000000: RxContext=0xFFFFE002399C2220; Exchange=0xFFFFE0023DFF8CF0; ExchangeState=       6; ExchangeStatus=       0
- 16:34:35.284946 SMBClient 30104  in cmd.exe(6048)* act {7e381306: RxContext=0xFFFFE0023ECA1A20; Exchange=0xFFFFE0023DFF9C40; ExchangeState=       6; ExchangeStatus=       0
- 16:34:35.284949 SMBClient 30111  in cmd.exe(6048)* act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=     109; ThrottlingWindowLimit=     128; OldestPendingMid=27; NextAvailableMid=28; CreditsGranted=0
- 16:34:35.284950 SMBClient 30111  in cmd.exe(6048)* act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       2; CurrentWindowLimit=     109; ThrottlingWindowLimit=     128; OldestPendingMid=27; NextAvailableMid=29; CreditsGranted=0
- 16:34:35.284950 SMBClient 30406  in cmd.exe(6048)* act {00000000: Count=       0; Command=CREATE  ; MessageId=27; SessionId=2051295070; TreeId=1863141655; MidCharge=1; CreditRequested=0; SendLength=     152; VcEndpoint=0xFFFFE0023F605020
- 16:34:35.284950 SMBClient 30406  in cmd.exe(6048)* act {7e381306: Count=       1; Command=QRY_INFO; MessageId=28; SessionId=2051295070; TreeId=1863141655; MidCharge=1; CreditRequested=2; SendLength=     104; VcEndpoint=0xFFFFE0023F605020
- 16:34:35.284951 SMBClient 2000  in cmd.exe(6048)* act {0000002f: ReassembledEventID=40000; FragmentSize=      40; FragmentData=0x010000001C000000020001BD0A4D0035000000000000000030A8C93F02E0FFFFB074CD3F00010000
- 16:34:35.284951 SMBClient 2000  in cmd.exe(6048)* act {0000002f: ReassembledEventID=40000; FragmentSize=     152; FragmentData=0xFE534D4240000100000000000500000010000000980000001B00000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000000390000000200000000000000000000000000000000000000
- 16:34:35.284951 SMBClient 2000  in cmd.exe(6048)* act {0000002f: ReassembledEventID=40000; FragmentSize=     104; FragmentData=0xFE534D4240000100000000001000020034000000000000001C00000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000000290002072000000068000000000000000000000000000000
- 16:34:35.284951 SMBClient 30205  in cmd.exe(6048)* act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023EA25920; SendLength=     260; ConnectionType=       1
- 16:34:35.285538 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     260; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; startime=    3185; endtime=    3185; seqnum=       0; connid=       0
- 16:34:35.285540 SMBClient 40000  in ?(0) act {00000030: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     288; PacketData=0xFE534D4240000100000000000500000011000000B80000001B00000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000
- 16:34:35.285541 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=     108; ThrottlingWindowLimit=     128; OldestPendingMid=28; NextAvailableMid=29; CreditsGranted=0
- 16:34:35.285541 SMBClient 30407  in ?(0) act {00000000: Command=CREATE  ; MessageId=27; AsyncId=0; SessionId=2051295070; TreeId=1863141655; CreditGranted=0; Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:35.285542 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       0; CurrentWindowLimit=     110; ThrottlingWindowLimit=     128; OldestPendingMid=29; NextAvailableMid=29; CreditsGranted=0
- 16:34:35.285542 SMBClient 30407  in ?(0) act {7e381306: Command=QRY_INFO; MessageId=28; AsyncId=0; SessionId=2051295070; TreeId=1863141655; CreditGranted=3; Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:35.285542 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     292; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; seqnum=       0; connid=       0
- 16:34:35.285543 SMBClient 30206  in ?(0) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023EA25920; SendLength=     256; Status=       0; ConnectionType=       1
- 16:34:35.285543 SMBClient 30114  in ?(0) act {00000000: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:35.285544 SMBClient 30114  in ?(0) act {7e381306: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:35.285562 SMBClient 30603  in System(4) act {00000000: Object=0xFFFFCD84EAE1A0E0; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc7431b7-c65a-11f1-a3a8-eea7cd268ff2}; OldState=4; NewState=0; Status=0x0; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=0; Prev
- 16:34:35.285656 SMBClient 30603  in cmd.exe(6048)* act {00000000: Object=0xFFFFCD84EAE1A0E0; PersistentFID=0x0; VolatileFID=0x0; CreateGUID={bc7431b7-c65a-11f1-a3a8-eea7cd268ff2}; OldState=0; NewState=6; Status=0xC0000128; Reason=       0; ShareNameLength=17; ShareName=\10.77.0.53\share; ObjectNameLength=
- 16:34:35.285657 SMBClient 30111  in cmd.exe(6048)* act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       1; CurrentWindowLimit=     110; ThrottlingWindowLimit=     128; OldestPendingMid=29; NextAvailableMid=30; CreditsGranted=0
- 16:34:35.285658 SMBClient 30406  in cmd.exe(6048)* act {7e381306: Count=       0; Command=CLOSE   ; MessageId=29; SessionId=2051295070; TreeId=1863141655; MidCharge=1; CreditRequested=1; SendLength=      88; VcEndpoint=0xFFFFE0023F605020
- 16:34:35.285658 SMBClient 40000  in cmd.exe(6048)* act {00000031: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=      88; PacketData=0xFE534D4240000100000000000600010030000000000000001D00000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000
- 16:34:35.285659 SMBClient 30205  in cmd.exe(6048)* act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F94D8D0; SendLength=      92; ConnectionType=       1
- 16:34:35.285872 Kernel-Network 10 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=      92; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; startime=    3185; endtime=    3185; seqnum=       0; connid=       0
- 16:34:35.285873 SMBClient 40000  in ?(0) act {00000032: ConnectionType=       1; PeerAddressLength=      28; PeerAddress=10.77.0.53:445; PacketSize=     124; PacketData=0xFE534D4240000100000000000600010031000000000000001D00000000000000FFFE000017490D6F5E47447A0000000000000000000000000000000000000
- 16:34:35.285874 SMBClient 30111  in ?(0) act {00000000: MidWindow=0xFFFFE0023FCF96C0; CurrentWindowSize=       0; CurrentWindowLimit=     110; ThrottlingWindowLimit=     128; OldestPendingMid=30; NextAvailableMid=30; CreditsGranted=0
- 16:34:35.285874 SMBClient 30407  in ?(0) act {7e381306: Command=CLOSE   ; MessageId=29; AsyncId=0; SessionId=2051295070; TreeId=1863141655; CreditGranted=1; Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:35.285875 Kernel-Network 11 KERNEL_NETWORK_TASK_TCPIP in ?(0) act {00000000: PID=       4; size=     128; daddr=10.77.0.53; saddr=10.77.0.21; dport=445; sport=49673; seqnum=       0; connid=       0
- 16:34:35.285876 SMBClient 30206  in ?(0) act {00000000: VcEndpoint=0xFFFFE0023F605020; Socket=0xFFFFE002410AC5C8; SendMdl=0xFFFFE0023F945530; SendLength=      88; Status=       0; ConnectionType=       1
- 16:34:35.285876 SMBClient 30114  in ?(0) act {7e381306: Status=       0; VcEndpoint=0xFFFFE0023F605020
- 16:34:35.288058 Kernel-Process 2 ProcessStop in cmd.exe(6048)* act {00000000: ProcessID=    6048; ProcessSequenceNumber=170; CreateTime=2026-10-12T16:34:35.242013800Z; ExitTime=2026-10-12T16:34:35.288022100Z; ExitCode=       0; TokenElevationType=       1; HandleCount=      44; CommitCharge=4730880; CommitPeak=494387
- 16:34:35.288793 Kernel-Process 2 ProcessStop in conhost.exe(6504)* act {00000000: ProcessID=    6504; ProcessSequenceNumber=171; CreateTime=2026-10-12T16:34:35.262749800Z; ExitTime=2026-10-12T16:34:35.288714700Z; ExitCode=       0; TokenElevationType=       1; HandleCount=     101; CommitCharge=6574080; CommitPeak=657817

