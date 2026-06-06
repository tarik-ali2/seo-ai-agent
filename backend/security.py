"""
URL validation and SSRF (Server-Side Request Forgery) protection.

Prevents the crawler from being used to probe internal networks,
cloud metadata endpoints, or localhost services.
"""
import socket
import ipaddress
from urllib.parse import urlparse

from fastapi import HTTPException

# RFC-defined private, loopback, link-local, and reserved ranges
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),        # Private class A
    ipaddress.ip_network("172.16.0.0/12"),      # Private class B
    ipaddress.ip_network("192.168.0.0/16"),     # Private class C
    ipaddress.ip_network("127.0.0.0/8"),        # Loopback
    ipaddress.ip_network("169.254.0.0/16"),     # Link-local / AWS metadata
    ipaddress.ip_network("0.0.0.0/8"),          # "This" network
    ipaddress.ip_network("100.64.0.0/10"),      # Shared address space
    ipaddress.ip_network("192.0.0.0/24"),       # IETF protocol assignments
    ipaddress.ip_network("192.0.2.0/24"),       # TEST-NET-1
    ipaddress.ip_network("198.18.0.0/15"),      # Benchmarking
    ipaddress.ip_network("198.51.100.0/24"),    # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),     # TEST-NET-3
    ipaddress.ip_network("240.0.0.0/4"),        # Reserved
    ipaddress.ip_network("255.255.255.255/32"), # Broadcast
    ipaddress.ip_network("::1/128"),            # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),           # IPv6 unique local
    ipaddress.ip_network("fe80::/10"),          # IPv6 link-local
    ipaddress.ip_network("::ffff:0:0/96"),      # IPv4-mapped IPv6
]

# Hostnames that are always blocked regardless of DNS resolution
_BLOCKED_HOSTNAMES = frozenset({
    "localhost",
    "ip6-localhost",
    "ip6-loopback",
    "broadcasthost",
})


def _is_ip_blocked(ip_str: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip_str)
        return any(addr in net for net in _BLOCKED_NETWORKS)
    except ValueError:
        return True  # Unparseable IP → block it


def validate_crawl_url(url: str) -> str:
    """
    Validates that a URL is safe to crawl:
      - Must use http or https scheme
      - Must have a resolvable public hostname
      - Must not resolve to a private/internal IP (SSRF protection)

    Returns the normalized URL string or raises HTTPException 400.
    """
    if not url or not isinstance(url, str):
        raise HTTPException(status_code=400, detail="URL is required.")

    url = url.strip().rstrip("/")

    if not url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=400,
            detail="URL must begin with http:// or https://",
        )

    parsed = urlparse(url)

    if not parsed.netloc:
        raise HTTPException(status_code=400, detail="Invalid URL: no hostname found.")

    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(status_code=400, detail="Invalid URL: cannot parse hostname.")

    # Block well-known internal hostnames
    if hostname.lower() in _BLOCKED_HOSTNAMES:
        raise HTTPException(status_code=400, detail="URL hostname is not permitted.")

    # Block cloud metadata hostnames by prefix
    if hostname.startswith("169.254.") or hostname == "metadata.google.internal":
        raise HTTPException(status_code=400, detail="URL hostname is not permitted.")

    # Resolve ALL addresses for the hostname and block if any is internal
    try:
        addr_infos = socket.getaddrinfo(hostname, None)
        if not addr_infos:
            raise HTTPException(status_code=400, detail=f"Cannot resolve hostname: {hostname}")

        for info in addr_infos:
            ip_str = info[4][0]
            if _is_ip_blocked(ip_str):
                raise HTTPException(
                    status_code=400,
                    detail="URL resolves to a private or reserved IP address.",
                )
    except HTTPException:
        raise
    except OSError:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot resolve hostname: {hostname}",
        )

    return url
