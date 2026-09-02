"""Host comparison, done once so both sides compare the same way.

SCOPE_external_data_sources.md@d2de531 §8.1a. A denied host is denied **with its
subdomains, and after normalisation** — `evil.example` that does not also refuse
`api.evil.example` refuses nothing, and an IDN homograph is a different string
to `==` and the same site to a human. An entry may also be an IP or a CIDR, for
a host that answers on a bare address.

This lives in `datasource` rather than in `generator`'s shape module because the
*call-time* check runs here, with no `Application` in sight, and the two must
never be two implementations that agree on the day they were written (§10 item
7). `generator.datasource_shape` **imports** these two functions rather than
restating them — `generator` may import `datasource` and never the reverse, so
the shared rule belongs on the side that owns the runtime.
"""
import ipaddress


def normalise_host(host):
    """Lower-cased, dot-stripped, A-label (punycode) form. '' when unusable."""
    raw = (host or '').strip().strip('.').lower()
    if not raw:
        return ''
    if raw.startswith('[') and raw.endswith(']'):
        raw = raw[1:-1]
    try:
        return raw.encode('idna').decode('ascii').lower()
    except (UnicodeError, UnicodeDecodeError):
        # A bare IPv4/IPv6 literal has no IDN form. Returned as typed so the
        # caller refuses it by some other rule rather than comparing against ''.
        return raw


def host_matches(host, entry):
    """Whether `host` is covered by one policy entry.

    An entry is a hostname (matching it and every label below it), an IP, or a
    CIDR. Anything unparseable matches nothing rather than everything: a typo in
    a denylist must fail open on that line and leave the rest of the list
    working, because the alternative is one bad character switching every source
    off with nothing saying why.
    """
    h = normalise_host(host)
    e = normalise_host(entry)
    if not h or not e:
        return False
    if '/' in e:
        try:
            network = ipaddress.ip_network(e, strict=False)
            return ipaddress.ip_address(h) in network
        except ValueError:
            return False
    return h == e or h.endswith('.' + e)
