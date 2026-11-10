"""Validation-only process guard: reject every attempted network connection."""
import sys

def deny_network(event, args):
    if event in {"socket.connect", "socket.getaddrinfo", "socket.sendto", "socket.sendmsg"}:
        raise RuntimeError("Offline validation blocked network event: " + event)

sys.addaudithook(deny_network)
