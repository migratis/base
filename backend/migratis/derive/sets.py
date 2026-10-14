"""What a calculated set IS, for both hosts (SCOPE_calculated_tables.md §4.3, §6.2).

Pure. The design sandbox (`generator/sandbox/derive_host.py`) and every
generated application (`derive/runner.py`) read and write rows in different
stores, but what a run MEANS — how an output row becomes a stored row, how the
new set is matched to the stored one, which param comes from where — is decided
here, once, so the preview and the shipped application cannot disagree about
it. `getDisplayMode`'s lesson, applied before the second host existed.
"""
from . import expr


def _as_id(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def target_value(value, field):
    """One output value as the target column stores it. `field` is
    `{'type', 'choices'}` for a field, or `None` for a link (an FK column),
    which carries a record id as it is."""
    if field is None:
        return _as_id(value) if value is not None else None
    return expr.to_json_value(expr.to_field_value(value, field['type'], field.get('choices')))


def to_target_row(row, output_map, target_fields, anchor_fk='', anchor_id=None):
    """An engine output row as the target stores it: mapped, rounded once by
    each target field's declared type (D10), carrying the anchor link."""
    data = {name: target_value(row.get(col), target_fields.get(name))
            for col, name in (output_map or {}).items()}
    if anchor_fk and anchor_id is not None:
        data[anchor_fk] = anchor_id
    return data


def _hashable(value):
    if isinstance(value, float) and value == int(value):
        return int(value)
    try:
        hash(value)
        return value
    except TypeError:
        return repr(value)


def row_key(data, key_fields):
    return tuple(_hashable((data or {}).get(name)) for name in key_fields)


def diff_sets(new_rows, existing, key_fields, mapped, mode):
    """Match the new set against the stored one by key (D4).

    `existing` is `[(handle, data)]` in a stable order; `handle` is whatever
    the host deletes or updates with. `replace` updates what changed, creates
    what is new and deletes what vanished — so ids are stable across runs;
    `generate` only creates the keys that are missing and never touches a row
    again. Returns `{creates, updates, deletes, unchanged}`.
    """
    stored, extras = {}, []
    for handle, data in existing:
        k = row_key(data, key_fields)
        if k in stored:
            extras.append(handle)
        else:
            stored[k] = (handle, data)
    creates, updates, unchanged, seen = [], [], 0, set()
    for data in new_rows:
        k = row_key(data, key_fields)
        seen.add(k)
        found = stored.get(k)
        if found is None:
            creates.append(data)
        elif mode == 'replace' and any(_hashable((found[1] or {}).get(n)) != _hashable(data.get(n))
                                       for n in mapped):
            updates.append((found[0], data))
        else:
            unchanged += 1
    deletes = ([h for k, (h, _) in stored.items() if k not in seen] + extras
               if mode == 'replace' else [])
    return {'creates': creates, 'updates': updates, 'deletes': deletes,
            'unchanged': unchanged}


def bound_params(params_map, anchor_data):
    """The params a binding supplies. A blank is unknown, and an unknown param
    takes the transform's own default — an empty opening balance is 0, not
    "every balance unknown"."""
    params = {}
    for name, bound in (params_map or {}).items():
        value = ((anchor_data or {}).get(bound['anchor']) if 'anchor' in bound
                 else bound.get('value'))
        if value is not None and value != '':
            params[name] = value
    return params
