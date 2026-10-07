"""Attribution for Linux containers: eBPF programs on the capture host.

The collector is a C program built once in its own image against BTF (libbpf, CO-RE) and
run through the daemon as a privileged helper on the host; it prints one event per line
and knows nothing of the scenario. ``LinuxEbpf`` starts it with the run's containers'
cgroups, stops it, and turns its events into ``AttributionRecord``s.
"""
