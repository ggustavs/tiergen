"""Capture at the scenario's capture points.

One dumpcap per capture point on the host, over the bridges of the point's segments; pcapng
with one interface per segment; 802.1Q tags inserted afterwards where the point is tagged;
per-host clock offsets beside the files. The scheduler (task 9) drives the same functions
``tiergen capture start`` and ``stop`` call.
"""
