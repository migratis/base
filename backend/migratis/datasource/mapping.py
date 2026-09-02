"""Payload → slots → this application's fields. Two hops, two pure functions.

SCOPE_external_data_sources.md@d2de531 §6, written to `computed.py`'s rules:
**no Django imports**, never raises, one meaning shared by the sandbox and by a
generated app. Adding a coercion is one entry in `_COERCERS`.

Splitting the two hops is not tidiness. It is what lets the adapter's half be
tested against a recorded provider payload with **no application in sight**, and
the binding's half be tested with **no network in sight** — which is the same
seam §5.1 cut so that half a declaration could be published and half could not.

A path that does not resolve yields **absent, never a fabricated empty string**.
A missing synopsis must leave the field untouched so the required-field check
still fires on the ordinary write path, rather than filling it with `""` and
satisfying the check with nothing.
"""
from dataclasses import dataclass, field as dc_field
from datetime import datetime
from decimal import Decimal, InvalidOperation

# The list separator for a `[]` hop — a cast, a genre list, an author list. A
# joined string rather than a list because the target is one declared field of a
# declared type, and the shape every one of these APIs uses is a list of scalars
# or of objects with one interesting key.
LIST_JOIN = ', '

# A picker is not a browser (§13, no pagination): the first page of results,
# capped. Also the parse ceiling §8.1 asks for on the element side.
MAX_CANDIDATES = 25
MAX_LIST_ITEMS = 50


@dataclass(frozen=True)
class AdapterSpec:
    """The provider's half of a declaration, as plain data.

    Built from a `DataSourceAdapter` row on migratis and from the
    `datasources.json` codegen emits into the package on a generated app
    (§3.1) — the module never reads either, because it has never heard of an
    `Application` and must not learn.
    """
    slug: str = ''
    base_url: str = ''
    search_path: str = ''
    query_param: str = 'q'
    detail_path: str = ''
    auth_mode: str = 'none'
    auth_name: str = ''
    result_path: str = ''
    label_path: str = ''
    id_path: str = ''
    provides: dict = dc_field(default_factory=dict)

    @classmethod
    def from_dict(cls, data):
        data = data or {}
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})

    def to_dict(self):
        return {f: getattr(self, f) for f in self.__dataclass_fields__}


@dataclass(frozen=True)
class BindingSpec:
    """One application's half — never reusable, and therefore never published.

    `field_types` rides along because §6's coercion is by the *target field's
    declared type*, and the mapper must not have to ask a model what a column
    is. Without it a `decimal` field receives the string the API sent and the
    platform re-acquires prod app 6's bug through a new door.
    """
    entity: str = ''
    adapter_slug: str = ''
    field_map: dict = dc_field(default_factory=dict)
    field_types: dict = dc_field(default_factory=dict)
    external_id_field: str = ''
    label: str = ''
    enabled_in_sandbox: bool = True

    @classmethod
    def from_dict(cls, data):
        data = data or {}
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})

    def to_dict(self):
        return {f: getattr(self, f) for f in self.__dataclass_fields__}


# --------------------------------------------------------------------------- #
# Dotted paths
# --------------------------------------------------------------------------- #

_ABSENT = object()


def resolve_path(payload, path):
    """Walk a dotted path into `payload`. `_ABSENT` when it does not resolve.

    `[]` means "each element of this list": the rest of the path is applied to
    every element and the results are joined with ", ". An unresolved element is
    dropped rather than joined as an empty string, and a hop that yields nothing
    at all is absent rather than an empty join — the same rule one level down.
    """
    raw = (path or '').strip()
    if not raw:
        return _ABSENT
    current = payload
    segments = raw.split('.')
    for index, segment in enumerate(segments):
        each = segment.endswith('[]')
        key = segment[:-2] if each else segment
        if not isinstance(current, dict) or key not in current:
            return _ABSENT
        current = current[key]
        if each:
            if not isinstance(current, list):
                return _ABSENT
            rest = '.'.join(segments[index + 1:])
            values = []
            for item in current[:MAX_LIST_ITEMS]:
                got = resolve_path(item, rest) if rest else item
                if got is _ABSENT or got is None:
                    continue
                values.append(_scalar(got))
            values = [v for v in values if v not in ('', None)]
            return LIST_JOIN.join(values) if values else _ABSENT
    return current


def _scalar(value):
    """A payload value as the text a field would hold. Never a repr of a dict."""
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (int, float, Decimal)):
        return str(value)
    if isinstance(value, str):
        return value
    return ''


# --------------------------------------------------------------------------- #
# Hop 1 — the adapter's half
# --------------------------------------------------------------------------- #

def result_list(payload, adapter):
    """The list of results inside `payload`, or []. A blank `result_path` means
    the payload IS the list, which is what half these APIs answer."""
    if not (adapter.result_path or '').strip():
        return payload if isinstance(payload, list) else []
    found = resolve_path(payload, adapter.result_path)
    return found if isinstance(found, list) else []


def resolve_slots(payload, adapter):
    """`[{label, id, slots}]` — the provider's payload read through its own
    declaration, with no application in sight."""
    candidates = []
    for item in result_list(payload, adapter)[:MAX_CANDIDATES]:
        if not isinstance(item, dict):
            continue
        candidates.append({
            'label': _text(resolve_path(item, adapter.label_path)),
            'id':    _text(resolve_path(item, adapter.id_path)) if adapter.id_path else '',
            'slots': slots_of(item, adapter),
        })
    return candidates


def slots_of(item, adapter):
    """One result object → `{slot: value}`, absent paths simply absent."""
    slots = {}
    for slot, path in (adapter.provides or {}).items():
        value = resolve_path(item, path)
        if value is _ABSENT or value is None:
            continue
        if isinstance(value, (dict, list)):
            # A slot whose path lands on a container is a declaration mistake,
            # not a value. Dropping it is the same judgement as an unresolved
            # path: the field stays untouched and the required check still fires.
            continue
        slots[slot] = value
    return slots


def _text(value):
    return '' if value is _ABSENT or value is None else _scalar(value)


# --------------------------------------------------------------------------- #
# Hop 2 — the application's half
# --------------------------------------------------------------------------- #

def bind_values(slots, binding):
    """`{entity field: value}`, coerced by the target field's DECLARED type.

    Never guesses a type from the value: a `string` field holding a reference
    code `"007"` is text, exactly as `_normalise_numeric_values` decided it is
    (`sandbox/views.py`), and the same rule is what keeps a `decimal` field from
    storing the string the API sent.
    """
    values = {}
    for field_name, slot in (binding.field_map or {}).items():
        if slot not in (slots or {}):
            continue
        coerced = coerce_value(slots[slot], (binding.field_types or {}).get(field_name, ''))
        if coerced is _ABSENT:
            continue
        values[field_name] = coerced
    return values


def _coerce_integer(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        try:
            return int(float(str(value).strip()))
        except (TypeError, ValueError):
            return _ABSENT


def _coerce_decimal(value):
    try:
        return float(Decimal(str(value).strip()))
    except (TypeError, ValueError, InvalidOperation):
        return _ABSENT


def _coerce_boolean(value):
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ('true', '1', 'yes', 'y'):
        return True
    if text in ('false', '0', 'no', 'n'):
        return False
    return _ABSENT


def _coerce_date(value):
    """A date the write path will accept, or absent.

    Deliberately narrow: ISO-8601, `YYYY/MM/DD`, and the bare `YYYY` a film
    catalog answers for a release year. **No `03/04/2026`** — guessing between
    its two readings is how a French catalogue acquires American dates, and
    absent is a better answer than a wrong one the owner cannot see.
    """
    text = str(value).strip()
    if not text:
        return _ABSENT
    if len(text) == 4 and text.isdigit():
        return f'{text}-01-01'
    head = text.replace('/', '-')[:10]
    try:
        return datetime.strptime(head, '%Y-%m-%d').date().isoformat()
    except ValueError:
        return _ABSENT


def _coerce_year_int(value):
    """`release_date: "1999-03-31"` into an `integer` year field.

    The single most common shape in the case that triggered this scope, and the
    one place a plain int() would answer 1999 by accident and 0 by accident too.
    """
    text = str(value).strip()
    if len(text) >= 4 and text[:4].isdigit() and (len(text) == 4 or not text[:5].isdigit()):
        return int(text[:4])
    return _coerce_integer(value)


def _coerce_text(value):
    text = _scalar(value)
    return text if text != '' else _ABSENT


_COERCERS = {
    'integer':  _coerce_year_int,
    'decimal':  _coerce_decimal,
    'boolean':  _coerce_boolean,
    'date':     _coerce_date,
    'datetime': _coerce_date,
}


def coerce_value(value, field_type):
    """One payload value as the declared type, or `_ABSENT`."""
    if value is None or value is _ABSENT:
        return _ABSENT
    if isinstance(value, (dict, list)):
        return _ABSENT
    return _COERCERS.get((field_type or '').strip(), _coerce_text)(value)


def is_absent(value):
    """Whether `coerce_value`/`resolve_path` said "nothing here"."""
    return value is _ABSENT
