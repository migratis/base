"""Where a packet is actually allowed to go.

SCOPE_external_data_sources.md@d2de531 §8.1. `routing/views.py` states its own
premise — *"the engine URL still comes from settings and never from the request
(no SSRF)"* — and this feature breaks that premise on purpose, so it has to
replace it rather than inherit it.

Two rules carry the whole module:

* **Validation happens at connect time, not at declaration time.** Validating
  only when the row is saved is worthless: DNS answers can change between the
  save and the call, which is DNS rebinding stated as a sentence. It is also why
  §5.4's probe is a *gate* and not a guarantee.
* **Every address a name resolves to is checked, and the connection then goes to
  the one that was checked.** Checking the first answer and connecting by name
  re-opens the question at a hop nobody validated.
"""
import ipaddress
import socket

# 100.64.0.0/10 — carrier-grade NAT. Neither `is_private` nor `is_reserved` in
# the stdlib's reading, and on a good many hosts it is the provider's own
# network.
_CGNAT = ipaddress.ip_network('100.64.0.0/10')
# The cloud metadata endpoint, named explicitly. It is inside link-local and so
# already refused — it is written out because it is *the* target, and a future
# edit that loosens link-local must trip over this line.
_METADATA = frozenset({
    ipaddress.ip_address('169.254.169.254'),
    ipaddress.ip_address('fd00:ec2::254'),
})


class AddressRefused(Exception):
    """A hostname resolved somewhere a request may not go."""


def is_public(ip):
    """Whether one resolved address is somewhere a user-declared URL may reach."""
    addr = ip if isinstance(ip, (ipaddress.IPv4Address, ipaddress.IPv6Address)) \
        else ipaddress.ip_address(str(ip))
    # An IPv4-mapped IPv6 address (::ffff:127.0.0.1) is the loopback wearing a
    # different type. Unwrap before every other test, or each one is asked about
    # the wrong address.
    if getattr(addr, 'ipv4_mapped', None):
        addr = addr.ipv4_mapped
    if addr in _METADATA:
        return False
    if addr.is_loopback or addr.is_private or addr.is_link_local or \
            addr.is_multicast or addr.is_reserved or addr.is_unspecified:
        return False
    if addr.version == 4 and addr in _CGNAT:
        return False
    if addr.version == 6:
        # 6to4 and Teredo carry an embedded IPv4 address that the tests above
        # cannot see, so a 2002::/16 host can name 127.0.0.1 in its own body.
        packed = addr.packed
        if addr in ipaddress.ip_network('2002::/16'):
            return is_public(ipaddress.IPv4Address(packed[2:6]))
        if addr in ipaddress.ip_network('2001::/32'):
            return is_public(ipaddress.IPv4Address(bytes(b ^ 0xFF for b in packed[12:16])))
    return True


def resolve_public(hostname, port=443):
    """Every address `hostname` answers with, refused unless ALL of them are public.

    All rather than "the first public one": a name that answers with one routable
    address and one loopback is a rebinding attempt wearing a single DNS
    response, and picking the good one would make the attack a matter of which
    entry the resolver happened to order first.

    Returns `[(family, ip_string)]` in the resolver's own order.
    """
    host = (hostname or '').strip()
    if not host:
        raise AddressRefused('no-host')
    # A literal address skips the resolver but not the check.
    try:
        literal = ipaddress.ip_address(host.strip('[]'))
    except ValueError:
        literal = None
    if literal is not None:
        if not is_public(literal):
            raise AddressRefused('private-address')
        return [(socket.AF_INET6 if literal.version == 6 else socket.AF_INET, str(literal))]

    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise AddressRefused('dns-failed') from exc
    if not infos:
        raise AddressRefused('dns-failed')

    resolved = []
    for family, _type, _proto, _canon, sockaddr in infos:
        ip = sockaddr[0]
        try:
            if not is_public(ip):
                raise AddressRefused('private-address')
        except ValueError as exc:
            raise AddressRefused('private-address') from exc
        if (family, ip) not in resolved:
            resolved.append((family, ip))
    return resolved
