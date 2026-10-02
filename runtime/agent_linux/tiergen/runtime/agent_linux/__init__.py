"""The Linux agent: one process per host, running the instance's projected program.

``tiergen-agent <program.json>`` reads nothing but the program. It starts the services the
instance binds, then runs each behaviour in its own process, and writes what it ran as
``InvocationRecord``s, one per line, beside a log.
"""
