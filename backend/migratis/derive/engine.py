"""The calculated-tables engine (SCOPE_calculated_tables.md §5, §6.5, phase P1).

A **transform** is a declaration: typed input slots, typed params, typed output
columns, an output key and a small DAG of steps. This module checks one (the
gate, `check`) and runs one (`run`) as a pure function of
*(declaration, input rows, params, as_of)* — no Django, no database, no
network, no `eval`. The host (the design sandbox, or a generated application)
reads the inputs through its own list path and writes the rows through its own
write path; nothing here knows what an application is.

    plan = check(declaration)                 # raises TransformError
    result = run(plan, {'items': rows}, params={'months': 6}, as_of=date)
    result.rows                               # typed output rows

Nine operators, one registry (`_OPS`) — `computed.py`'s device: adding one is
one entry. The rules that carry the design:

* **Refused whole, never truncated.** Every ceiling (`limits.Limits`) raises
  `RunError` naming the step and the number; a partial result is never
  returned.
* **Null is unknown**, as in the expression language: a filter keeps only
  rows whose condition is *true*, aggregates skip unknowns, `sum` of nothing
  is 0, a join never matches an unknown key.
* **Deterministic.** Same inputs, params and `as_of` → same rows, in the same
  order. `today` is `as_of`, fixed once per run. Months are anchored.
* **Numbers stay exact** (`Decimal`) and are rounded once, by the host, at the
  write — except that the output key is compared as it will be stored, so
  two rows that would collide in the table are refused here.
"""
import copy
import decimal
import functools
import json
import os
import re
import time

from . import dates, expr, limits as limits_mod
from .expr import ANY, BOOL, DATE, NUMBER, TEXT


# --------------------------------------------------------------------------- #
# Vocabulary
# --------------------------------------------------------------------------- #

#: What a slot, a param or an output column may hold. `ref` is an opaque record
#: id carried through from an input to an output FK.
SLOT_TYPES = ('decimal', 'integer', 'date', 'string', 'boolean', 'ref')
PARAM_TYPES = ('decimal', 'integer', 'date', 'string', 'boolean')

_SLOT_READS = {'decimal': NUMBER, 'integer': NUMBER, 'date': DATE,
               'string': TEXT, 'boolean': BOOL, 'ref': ANY}
_SLOT_AS_FIELD = {'decimal': 'decimal', 'integer': 'integer', 'date': 'date',
                  'string': 'string', 'boolean': 'boolean', 'ref': 'fk'}
_TYPE_AS_FIELD = {NUMBER: 'decimal', DATE: 'date', TEXT: 'string',
                  BOOL: 'boolean', ANY: 'fk'}
_TYPE_WORDS = {NUMBER: 'a number', DATE: 'a date', TEXT: 'text',
               BOOL: 'yes/no', ANY: 'a record'}

OPS = ('join', 'filter', 'compute', 'recur', 'repeat', 'group', 'running',
       'union', 'write')

# op -> (required keys, optional keys)
_STEP_KEYS = {
    'join':    ({'id', 'op', 'left', 'right'}, {'how', 'on', 'prefix', 'doc'}),
    'filter':  ({'id', 'op', 'from', 'where'}, {'doc'}),
    'compute': ({'id', 'op', 'from', 'set'}, {'keep', 'doc'}),
    'recur':   ({'id', 'op', 'from', 'start', 'unit'},
                {'every', 'until', 'count', 'window', 'doc'}),
    'repeat':  ({'id', 'op', 'from', 'times'}, {'doc'}),
    'group':   ({'id', 'op', 'from', 'by'}, {'set', 'order_by', 'doc'}),
    'running': ({'id', 'op', 'from', 'order_by'}, {'partition_by', 'set', 'doc'}),
    'union':   ({'id', 'op', 'from'}, {'doc'}),
    'write':   ({'op', 'from'}, {'id', 'doc'}),
}

RECUR_UNITS = ('day', 'week', 'month', 'year')
RECUR_COLUMNS = {'occurrence': DATE, 'occurrence_index': NUMBER,
                 'occurrence_total': NUMBER}
REPEAT_COLUMNS = {'index': NUMBER}

_NAME = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
_CONTEXT = expr._CONTEXT
_ZERO = decimal.Decimal(0)


class TransformError(Exception):
    """A declaration the gate refuses. `errors` is `[{loc, code, msg}]`, the
    platform's rejection shape, every problem found at once."""

    def __init__(self, errors):
        super().__init__('; '.join(e['msg'] for e in errors))
        self.errors = errors


class RunError(Exception):
    """A run refused whole. `step` names the step (or input slot) that
    crossed the line."""

    def __init__(self, code, message, step=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.step = step

    def __str__(self):
        return self.message


# --------------------------------------------------------------------------- #
# Reading values
# --------------------------------------------------------------------------- #

def _coerce(value, slot_type):
    """A stored value as the engine holds it for `slot_type`, or `None`."""
    if value is None or value == '' and slot_type != 'string':
        return None
    if slot_type in ('decimal', 'integer'):
        return expr.as_decimal(value)
    if slot_type == 'date':
        return dates.as_date(value)
    if slot_type == 'string':
        return value if isinstance(value, str) else expr._text(value)
    if slot_type == 'boolean':
        return value if isinstance(value, bool) else None
    return value  # ref


_CENT = decimal.Decimal('0.01')
_ONE = decimal.Decimal(1)


def _stored(value, slot_type):
    """`value` as an output column of `slot_type` will be stored — what the
    key is compared on and what an example is checked against."""
    if value is None:
        return None
    if slot_type in ('decimal', 'integer'):
        n = expr.as_decimal(value)
        if n is None:
            return None
        try:
            return n.quantize(_CENT if slot_type == 'decimal' else _ONE,
                              rounding=decimal.ROUND_HALF_UP, context=_CONTEXT)
        except decimal.DecimalException:
            return None
    return _coerce(value, slot_type)


def _render(value):
    if isinstance(value, decimal.Decimal):
        return str(value)
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return value


def _hashable(value):
    try:
        hash(value)
        return value
    except TypeError:
        return repr(value)


def _whole(n):
    return expr._whole(n)


# --------------------------------------------------------------------------- #
# The gate
# --------------------------------------------------------------------------- #

class Plan:
    """A checked transform: what `run` executes."""

    def __init__(self, decl):
        self.decl = decl
        self.slots = {}       # slot -> {column: slot type}
        self.params = {}      # name -> spec
        self.output = {}      # column -> slot type
        self.key = []
        self.steps = {}       # id -> compiled step
        self.order = []       # step ids, topological, ending with the write
        self.schemas = {}     # id (slot or step) -> {column: expression type}
        self.write_id = None


class _Gate:

    def __init__(self, decl):
        self.decl = decl
        self.errors = []
        self.plan = Plan(decl)

    def err(self, loc, code, msg):
        self.errors.append({'loc': list(loc), 'code': code, 'msg': msg})

    # -- the declaration's head ---------------------------------------------- #

    def head(self):
        decl = self.decl
        if not isinstance(decl, dict):
            self.err([], 'transform_invalid', 'A transform is an object.')
            return False
        inputs = decl.get('inputs')
        if not isinstance(inputs, dict) or not inputs:
            self.err(['inputs'], 'transform_slot',
                     'A transform reads at least one input slot.')
        else:
            for slot, cols in inputs.items():
                self.slot(slot, cols)
        params = decl.get('params') or {}
        if not isinstance(params, dict):
            self.err(['params'], 'transform_param', 'params is an object.')
        else:
            for name, spec in params.items():
                self.param(name, spec)
        output = decl.get('output')
        if not isinstance(output, dict) or not output:
            self.err(['output'], 'transform_output',
                     'A transform declares at least one output column.')
        else:
            for col, t in output.items():
                if not _NAME.match(str(col)) or t not in SLOT_TYPES:
                    self.err(['output', col], 'transform_output',
                             f"Output column {col!r} must be a name with a type "
                             f"among {', '.join(SLOT_TYPES)}.")
                else:
                    self.plan.output[col] = t
        key = decl.get('key')
        if (not isinstance(key, list) or not key
                or any(k not in self.plan.output for k in key)
                or len(set(key)) != len(key)):
            self.err(['key'], 'transform_key',
                     'The key is a non-empty list of distinct output columns: it '
                     'is what tells one calculated row from another across runs.')
        else:
            self.plan.key = list(key)
        return True

    def slot(self, slot, cols):
        loc = ['inputs', slot]
        if not _NAME.match(str(slot)):
            self.err(loc, 'transform_slot', f"Input slot {slot!r} is not a name.")
            return
        if not isinstance(cols, dict) or not cols:
            self.err(loc, 'transform_slot',
                     f"Input slot {slot!r} declares no columns.")
            return
        typed = {}
        for col, spec in cols.items():
            t = spec.get('type') if isinstance(spec, dict) else None
            extra = set(spec) - {'type', 'optional', 'doc', 'label'} if isinstance(spec, dict) else set()
            if not _NAME.match(str(col)) or t not in SLOT_TYPES or extra:
                self.err(loc + [col], 'transform_slot',
                         f"Slot column {slot}.{col} needs a type among "
                         f"{', '.join(SLOT_TYPES)}"
                         + (f" and has unknown keys {sorted(extra)}" if extra else '')
                         + '.')
                continue
            typed[col] = t
        self.plan.slots[slot] = typed
        self.plan.schemas[slot] = {c: _SLOT_READS[t] for c, t in typed.items()}

    def param(self, name, spec):
        loc = ['params', name]
        if not _NAME.match(str(name)) or not isinstance(spec, dict):
            self.err(loc, 'transform_param', f"Param {name!r} is not a name with a spec.")
            return
        t = spec.get('type')
        extra = set(spec) - {'type', 'default', 'min', 'max', 'doc', 'label'}
        if t not in PARAM_TYPES or extra:
            self.err(loc, 'transform_param',
                     f"Param {name!r} needs a type among {', '.join(PARAM_TYPES)}"
                     + (f" and has unknown keys {sorted(extra)}" if extra else '') + '.')
            return
        default = spec.get('default')
        if default is not None:
            if default == 'today':
                if t != 'date':
                    self.err(loc, 'transform_param',
                             f"Only a date param may default to 'today' ({name!r} "
                             f"is {t!r}).")
                    return
            elif _param_value(default, t) is None:
                self.err(loc, 'transform_param',
                         f"The default of {name!r} is not {t!r}.")
                return
        for bound in ('min', 'max'):
            if bound in spec and (t not in ('decimal', 'integer')
                                  or expr.as_decimal(spec[bound]) is None):
                self.err(loc, 'transform_param',
                         f"{bound!r} bounds a number param only.")
                return
        self.plan.params[name] = spec

    # -- steps --------------------------------------------------------------- #

    def steps(self):
        steps = self.decl.get('steps')
        if not isinstance(steps, list) or not steps:
            self.err(['steps'], 'transform_steps', 'A transform has steps.')
            return
        raw = {}
        writes = []
        for i, step in enumerate(steps):
            loc = ['steps', i]
            if not isinstance(step, dict):
                self.err(loc, 'transform_invalid', f"Step {i} is not an object.")
                continue
            op = step.get('op')
            if op not in _STEP_KEYS:
                self.err(loc + ['op'], 'transform_unknown_op',
                         f"Unknown operator {op!r} in step {i}. Available: "
                         f"{', '.join(OPS)}.")
                continue
            sid = step.get('id', 'write' if op == 'write' else None)
            if not isinstance(sid, str) or not _NAME.match(sid):
                self.err(loc + ['id'], 'transform_invalid',
                         f"Step {i} needs an id that is a name.")
                continue
            if sid in raw or sid in self.plan.slots:
                self.err(loc + ['id'], 'transform_duplicate_step',
                         f"Two steps (or a step and an input slot) are called {sid!r}.")
                continue
            required, optional = _STEP_KEYS[op]
            missing = (required - {'id'} if op != 'write' else required) - set(step)
            if op != 'write' and 'id' not in step:
                missing = missing | {'id'}
            unknown = set(step) - required - optional
            if unknown:
                self.err(loc, 'transform_unknown_key',
                         f"Step {sid!r} ({op}) does not take {sorted(unknown)}.")
                continue
            if missing:
                self.err(loc, 'transform_missing_key',
                         f"Step {sid!r} ({op}) needs {sorted(missing)}.")
                continue
            raw[sid] = (i, step)
            if op == 'write':
                writes.append(sid)
        if len(writes) != 1:
            self.err(['steps'], 'transform_write_count',
                     f"A transform has exactly one write step; this one has "
                     f"{len(writes)}.")
        sources = {}
        for sid, (i, step) in raw.items():
            srcs = _sources(step)
            if srcs is None:
                self.err(['steps', i, 'from'], 'transform_invalid',
                         f"Step {sid!r} names its input(s) by id.")
                continue
            bad = [s for s in srcs if s not in raw and s not in self.plan.slots]
            if bad:
                self.err(['steps', i], 'transform_unknown_step',
                         f"Step {sid!r} reads {', '.join(map(repr, bad))}, which is "
                         f"neither a step nor an input slot.")
                continue
            sources[sid] = srcs
        order = self.toposort(raw, sources)
        if order is None:
            return
        if len(writes) == 1 and writes[0] in sources:
            reached, todo = set(), [writes[0]]
            while todo:
                s = todo.pop()
                if s in reached or s not in sources:
                    continue
                reached.add(s)
                todo.extend(sources[s])
            lost = [s for s in raw if s not in reached]
            for s in lost:
                self.err(['steps', raw[s][0]], 'transform_unreachable_step',
                         f"Step {s!r} feeds nothing the write step reads — remove "
                         f"it or connect it.")
            self.plan.write_id = writes[0]
        for sid in order:
            i, step = raw[sid]
            self.compile_step(sid, i, step, sources[sid])
        self.plan.order = order

    def toposort(self, raw, sources):
        order, done = [], set()
        pending = [s for s in raw if s in sources]
        while pending:
            progressed = False
            for s in list(pending):
                if all(src in done or src in self.plan.slots for src in sources[s]):
                    order.append(s)
                    done.add(s)
                    pending.remove(s)
                    progressed = True
            if not progressed:
                self.err(['steps'], 'transform_cycle',
                         f"These steps read each other in a circle: "
                         f"{', '.join(sorted(pending))}.")
                return None
        return order

    # -- expressions --------------------------------------------------------- #

    def expression(self, source, schema, loc, want=None, aggregates=None,
                   inner=None):
        if not isinstance(source, str):
            if isinstance(source, (int, float, decimal.Decimal)) and not isinstance(source, bool):
                source = str(source)
            else:
                self.err(loc, 'expression_syntax', 'An expression is written as text.')
                return None
        types = None if schema is None else {c: _TYPE_AS_FIELD[t] for c, t in schema.items()}
        inner_types = None if inner is None else {c: _TYPE_AS_FIELD[t] for c, t in inner.items()}
        params = {n: _SLOT_AS_FIELD[s['type']] for n, s in self.plan.params.items()}
        try:
            e = expr.compile(source, types=types, allow_today=True, params=params,
                             aggregates=aggregates, inner_types=inner_types)
        except expr.ExpressionError as exc:
            self.err(loc, exc.code, f"{exc.message} (in {source!r})")
            return None
        if want is not None and e.result_type not in (want, ANY):
            self.err(loc, 'transform_type',
                     f"{source!r} computes {_TYPE_WORDS[e.result_type]}; "
                     f"{_TYPE_WORDS[want]} is needed here.")
            return None
        return e

    def order_specs(self, specs, schema, loc):
        if not isinstance(specs, list):
            self.err(loc, 'transform_invalid', 'An ordering is a list of expressions.')
            return None
        out = []
        for j, spec in enumerate(specs):
            desc = False
            source = spec
            if isinstance(spec, dict):
                if set(spec) - {'expr', 'desc'}:
                    self.err(loc + [j], 'transform_invalid',
                             "An ordering entry is an expression or {expr, desc}.")
                    return None
                source, desc = spec.get('expr'), bool(spec.get('desc'))
            e = self.expression(source, schema, loc + [j])
            if e is None:
                return None
            out.append((e, desc))
        return out

    # -- per-operator compilation -------------------------------------------- #

    def compile_step(self, sid, i, step, srcs):
        op = step['op']
        loc = ['steps', i]
        inputs = [self.plan.schemas.get(s) for s in srcs]
        compiled = {'id': sid, 'op': op, 'sources': srcs, 'index': i}
        schema = getattr(self, 'op_' + op)(step, compiled, inputs, loc)
        self.plan.steps[sid] = compiled
        self.plan.schemas[sid] = schema

    def add_columns(self, schema, columns, loc, sid):
        if schema is None:
            return None
        clash = [c for c in columns if c in schema]
        if clash:
            self.err(loc, 'transform_column_collision',
                     f"Step {sid!r} adds {', '.join(map(repr, clash))}, which its "
                     f"input already has. Rename the input column in an earlier "
                     f"compute step.")
            return None
        out = dict(schema)
        out.update(columns)
        return out

    def op_filter(self, step, c, inputs, loc):
        c['where'] = self.expression(step['where'], inputs[0], loc + ['where'], want=BOOL)
        return inputs[0]

    def op_compute(self, step, c, inputs, loc):
        schema = inputs[0]
        keep = step.get('keep')
        if keep is not None:
            if not isinstance(keep, list):
                self.err(loc + ['keep'], 'transform_invalid', 'keep is a list of columns.')
                keep = []
            elif schema is not None:
                unknown = [k for k in keep if k not in schema]
                if unknown:
                    self.err(loc + ['keep'], 'transform_unknown_column',
                             f"keep names {', '.join(map(repr, unknown))}, which the "
                             f"input does not have.")
        c['keep'] = keep
        sets = step['set']
        if not isinstance(sets, dict):
            self.err(loc + ['set'], 'transform_invalid', 'set maps columns to expressions.')
            return None
        env = dict(schema) if schema is not None else None
        out = None
        if schema is not None:
            out = dict(schema) if keep is None else {k: schema[k] for k in keep if k in schema}
        compiled = []
        items, cycle = _set_order(sets)
        if cycle:
            self.err(loc + ['set'], 'transform_cycle',
                     f"These columns read each other in a circle: {', '.join(cycle)}.")
            return None
        for col, source in items:
            if not _NAME.match(str(col)):
                self.err(loc + ['set', col], 'transform_invalid', f"{col!r} is not a column name.")
                return None
            e = self.expression(source, env, loc + ['set', col])
            compiled.append((col, e))
            if e is None:
                env = out = None
            elif env is not None:
                env[col] = e.result_type
                out[col] = e.result_type
        c['set'] = compiled
        return out

    def op_recur(self, step, c, inputs, loc):
        schema = inputs[0]
        unit = step['unit']
        if unit not in RECUR_UNITS:
            self.err(loc + ['unit'], 'transform_recur_unit',
                     f"unit is one of {', '.join(RECUR_UNITS)}, not {unit!r}.")
        c['unit'] = unit
        c['start'] = self.expression(step['start'], schema, loc + ['start'], want=DATE)
        c['every'] = (self.expression(step['every'], schema, loc + ['every'], want=NUMBER)
                      if 'every' in step else None)
        c['until'] = (self.expression(step['until'], schema, loc + ['until'], want=DATE)
                      if 'until' in step else None)
        c['count'] = (self.expression(step['count'], schema, loc + ['count'], want=NUMBER)
                      if 'count' in step else None)
        window = step.get('window')
        c['window'] = None
        if window is not None:
            if not isinstance(window, list) or len(window) != 2:
                self.err(loc + ['window'], 'transform_invalid',
                         'window is [from, to): two date expressions.')
            else:
                c['window'] = (
                    self.expression(window[0], schema, loc + ['window', 0], want=DATE),
                    self.expression(window[1], schema, loc + ['window', 1], want=DATE))
        if not any(k in step for k in ('until', 'count', 'window')):
            self.err(loc, 'transform_recur_unbounded',
                     f"Step {c['id']!r} repeats without end: give it an until, a "
                     f"count or a window.")
        return self.add_columns(schema, RECUR_COLUMNS, loc, c['id'])

    def op_repeat(self, step, c, inputs, loc):
        c['times'] = self.expression(step['times'], inputs[0], loc + ['times'], want=NUMBER)
        return self.add_columns(inputs[0], REPEAT_COLUMNS, loc, c['id'])

    def op_group(self, step, c, inputs, loc):
        schema = inputs[0]
        by = step['by']
        if not isinstance(by, dict):
            self.err(loc + ['by'], 'transform_invalid', 'by maps key columns to expressions.')
            return None
        out = {}
        c['by'] = []
        for col, source in by.items():
            e = self.expression(source, schema, loc + ['by', col])
            c['by'].append((col, e))
            if e is None:
                out = None
            elif out is not None:
                out[col] = e.result_type
        c['order_by'] = (self.order_specs(step['order_by'], schema, loc + ['order_by'])
                         if 'order_by' in step else [])
        sets = step.get('set') or {}
        if not isinstance(sets, dict):
            self.err(loc + ['set'], 'transform_invalid', 'set maps columns to expressions.')
            return None
        c['set'] = []
        items, cycle = _set_order(sets, expr.GROUP_FUNCTIONS)
        if cycle:
            self.err(loc + ['set'], 'transform_cycle',
                     f"These columns read each other in a circle: {', '.join(cycle)}.")
            return None
        for col, source in items:
            if out is not None and col in out:
                self.err(loc + ['set', col], 'transform_column_collision',
                         f"{col!r} is already a group key.")
                return None
            e = self.expression(source, out, loc + ['set', col],
                                aggregates=expr.GROUP_FUNCTIONS,
                                inner=schema if out is not None else None)
            c['set'].append((col, e))
            if e is None:
                out = None
            elif out is not None:
                out[col] = e.result_type
        return out

    def op_running(self, step, c, inputs, loc):
        schema = inputs[0]
        c['order_by'] = self.order_specs(step['order_by'], schema, loc + ['order_by'])
        c['partition_by'] = (self.order_specs(step['partition_by'], schema,
                                              loc + ['partition_by'])
                             if 'partition_by' in step else [])
        sets = step.get('set') or {}
        if not isinstance(sets, dict):
            self.err(loc + ['set'], 'transform_invalid', 'set maps columns to expressions.')
            return None
        out = dict(schema) if schema is not None else None
        c['set'] = []
        items, cycle = _set_order(sets, expr.WINDOW_FUNCTIONS)
        if cycle:
            self.err(loc + ['set'], 'transform_cycle',
                     f"These columns read each other in a circle: {', '.join(cycle)}.")
            return None
        for col, source in items:
            e = self.expression(source, out, loc + ['set', col],
                                aggregates=expr.WINDOW_FUNCTIONS, inner=out)
            c['set'].append((col, e))
            if e is None:
                out = None
            elif out is not None:
                out[col] = e.result_type
        return out

    def op_union(self, step, c, inputs, loc):
        if any(s is None for s in inputs):
            return None
        out = {}
        for schema in inputs:
            for col, t in schema.items():
                have = out.get(col)
                if have is None or have == ANY:
                    out[col] = t
                elif t not in (ANY, have):
                    self.err(loc, 'transform_type',
                             f"Column {col!r} is {_TYPE_WORDS[have]} in one input of "
                             f"the union and {_TYPE_WORDS[t]} in another.")
                    return None
        return out

    def op_join(self, step, c, inputs, loc):
        left, right = inputs
        how = step.get('how', 'inner')
        if how not in ('inner', 'left'):
            self.err(loc + ['how'], 'transform_invalid', "how is 'inner' or 'left'.")
        c['how'] = how
        prefix = step.get('prefix') or ''
        if prefix and not _NAME.match(prefix):
            self.err(loc + ['prefix'], 'transform_invalid', 'prefix must start a column name.')
            prefix = ''
        c['prefix'] = prefix
        pairs = step.get('on') or []
        if not isinstance(pairs, list):
            self.err(loc + ['on'], 'transform_invalid',
                     'on is a list of {left, right} expressions.')
            pairs = []
        c['on'] = []
        shared = set()
        for j, pair in enumerate(pairs):
            if not isinstance(pair, dict) or set(pair) != {'left', 'right'}:
                self.err(loc + ['on', j], 'transform_invalid',
                         'Each join key is {left, right}.')
                return None
            le = self.expression(pair['left'], left, loc + ['on', j, 'left'])
            re_ = self.expression(pair['right'], right, loc + ['on', j, 'right'])
            if le is None or re_ is None:
                return None
            if ANY not in (le.result_type, re_.result_type) and le.result_type != re_.result_type:
                self.err(loc + ['on', j], 'transform_type',
                         f"The join compares {_TYPE_WORDS[le.result_type]} with "
                         f"{_TYPE_WORDS[re_.result_type]}.")
                return None
            c['on'].append((le, re_))
            if (not prefix and le.tree[0] == 'ref' and le.tree == re_.tree):
                shared.add(le.tree[1])
        if left is None or right is None:
            c['right_columns'] = None
            return None
        out = dict(left)
        columns = []
        for col, t in right.items():
            name = prefix + col
            if col in shared:
                continue
            if name in out:
                self.err(loc, 'transform_column_collision',
                         f"Both sides of join {c['id']!r} have a column {name!r}. Give "
                         f"the right side a prefix, or rename it in an earlier step.")
                return None
            out[name] = t
            columns.append((col, name))
        c['right_columns'] = columns
        return out

    def op_write(self, step, c, inputs, loc):
        schema = inputs[0]
        if schema is None:
            return None
        missing = [col for col in self.plan.output if col not in schema]
        if missing:
            self.err(loc, 'transform_output_missing',
                     f"The write step reads {step['from']!r}, which has no column "
                     f"{', '.join(map(repr, missing))} for the output.")
            return None
        for col, t in self.plan.output.items():
            have, wanted = schema[col], _SLOT_READS[t]
            if have != ANY and have != wanted:
                self.err(loc, 'transform_type',
                         f"Output column {col!r} is {t!r}, but {step['from']!r} "
                         f"computes {_TYPE_WORDS[have]} for it.")
        return {col: _SLOT_READS[t] for col, t in self.plan.output.items()}


def _set_order(sets, aggregates=None):
    """The columns of a `set` in an order where each comes after the columns of
    the same `set` it reads — never the declaration's own order, which a
    database `jsonb` column does not keep. A column reading ITSELF reads its
    input. Returns `(ordered items, cycle names or [])`; a source that does not
    parse keeps its place, and its own error is reported where it is compiled."""
    names = list(sets)
    deps = {}
    for name, source in sets.items():
        try:
            e = expr.compile(str(source), aggregates=aggregates)
            refs = set(e.references) | set(e.inner_references)
        except expr.ExpressionError:
            refs = set()
        deps[name] = {r for r in refs if r in sets and r != name}
    ordered, done = [], set()
    pending = list(names)
    while pending:
        ready = [n for n in pending if deps[n] <= done]
        if not ready:
            return [(n, sets[n]) for n in ordered + pending], sorted(pending)
        for n in ready:
            ordered.append(n)
            done.add(n)
            pending.remove(n)
    return [(n, sets[n]) for n in ordered], []


def _sources(step):
    op = step['op']
    if op == 'join':
        srcs = [step.get('left'), step.get('right')]
    elif op == 'union':
        srcs = step.get('from')
        if not isinstance(srcs, list) or not srcs:
            return None
    else:
        srcs = [step.get('from')]
    if not all(isinstance(s, str) for s in srcs):
        return None
    return srcs


def check(decl):
    """Check a transform declaration. Returns a `Plan`; raises `TransformError`
    with every problem found."""
    gate = _Gate(decl)
    if gate.head():
        gate.steps()
    if gate.errors:
        raise TransformError(gate.errors)
    return gate.plan


# --------------------------------------------------------------------------- #
# Params
# --------------------------------------------------------------------------- #

def _param_value(raw, t):
    if raw is None:
        return None
    if t in ('decimal', 'integer'):
        n = expr.as_decimal(raw)
        if n is None or (t == 'integer' and _whole(n) is None):
            return None
        return n
    return _coerce(raw, t)


def _resolve_params(plan, given, as_of):
    if not isinstance(given, dict):
        raise RunError('derive_param_invalid', 'Params are an object.')
    unknown = [n for n in given if n not in plan.params]
    if unknown:
        raise RunError('derive_param_invalid',
                       f"Unknown param {', '.join(map(repr, unknown))}; this transform "
                       f"takes {', '.join(plan.params) or 'none'}.")
    out = {}
    for name, spec in plan.params.items():
        t = spec['type']
        raw = given[name] if name in given else spec.get('default')
        if raw == 'today' and t == 'date':
            value = as_of
        else:
            value = _param_value(raw, t)
            if raw is not None and raw != '' and value is None:
                raise RunError('derive_param_invalid',
                               f"Param {name!r} is {t!r}; {raw!r} is not.")
        if value is not None and t in ('decimal', 'integer'):
            lo, hi = expr.as_decimal(spec.get('min')), expr.as_decimal(spec.get('max'))
            if (lo is not None and value < lo) or (hi is not None and value > hi):
                raise RunError('derive_param_out_of_range',
                               f"Param {name!r} is {value}; it must be between "
                               f"{lo if lo is not None else '-∞'} and "
                               f"{hi if hi is not None else '∞'}.")
        out[name] = value
    return out


# --------------------------------------------------------------------------- #
# The run
# --------------------------------------------------------------------------- #

class RunResult:

    def __init__(self, rows, counts, skipped, as_of, params):
        #: The output rows, typed (Decimal / date / str / bool / ref), unrounded.
        self.rows = rows
        #: Rows produced by every input slot and step, by id.
        self.counts = counts
        #: `{step: {reason: n}}` — rows a step could not place (an unknown start,
        #: an unknown repeat count). Reported, never guessed at.
        self.skipped = skipped
        self.as_of = as_of
        self.params = params


class _Run:

    def __init__(self, plan, params, as_of, lim, clock):
        self.plan = plan
        self.params = params
        self.as_of = as_of
        self.lim = lim
        self.clock = clock
        self.deadline = clock() + lim.time_budget
        self.ticks = 0
        self.skipped = {}

    def tick(self, step, every=64):
        self.ticks += 1
        if every > 1 and self.ticks % every:
            return
        if self.clock() > self.deadline:
            raise RunError('derive_time_budget',
                           f"The run took longer than {self.lim.time_budget:g} seconds "
                           f"(at step {step!r}).", step)

    def skip(self, step, reason):
        bucket = self.skipped.setdefault(step, {})
        bucket[reason] = bucket.get(reason, 0) + 1

    def grow(self, out, step):
        if len(out) > self.lim.max_rows:
            raise RunError('derive_too_many_rows',
                           f"Step {step!r} produced more than {self.lim.max_rows} rows.",
                           step)

    def ev(self, e, row, aggs=None):
        return e.evaluate_row(row, self.as_of, self.params, aggs)

    # -- operators ----------------------------------------------------------- #

    def op_filter(self, c, data):
        out = []
        for row in data[0]:
            self.tick(c['id'])
            if self.ev(c['where'], row) is True:
                out.append(row)
        return out

    def op_compute(self, c, data):
        keep = c['keep']
        out = []
        for row in data[0]:
            self.tick(c['id'])
            new = dict(row) if keep is None else {k: row.get(k) for k in keep}
            env = dict(row)
            for col, e in c['set']:
                v = self.ev(e, env)
                new[col] = v
                env[col] = v
            out.append(new)
        return out

    def op_recur(self, c, data):
        sid, unit = c['id'], c['unit']
        cap = self.lim.max_expansion
        out = []
        for n, row in enumerate(data[0]):
            self.tick(sid)
            start = self.ev(c['start'], row)
            if start is None:
                self.skip(sid, 'unknown_start')
                continue
            every = None
            if c['every'] is not None:
                raw = self.ev(c['every'], row)
                if raw is not None:
                    every = _whole(raw)
                    if every is None or every <= 0:
                        raise RunError('derive_recur_invalid_period',
                                       f"Step {sid!r}: row {n} repeats every {raw} "
                                       f"{unit}(s); a period is a whole number above 0.",
                                       sid)
            else:
                every = 1
            until = self.ev(c['until'], row) if c['until'] is not None else None
            count = None
            if c['count'] is not None:
                raw = self.ev(c['count'], row)
                if raw is not None:
                    count = _whole(raw)
                    if count is None or count < 0:
                        raise RunError('derive_recur_invalid_period',
                                       f"Step {sid!r}: row {n} has a count of {raw}; a "
                                       f"count is a whole number.", sid)
            lo = hi = None
            if c['window'] is not None:
                lo = self.ev(c['window'][0], row)
                hi = self.ev(c['window'][1], row)
            if every is None:
                total = 1
            else:
                total = count
                if until is not None:
                    length = _series_length(start, until, every, unit)
                    total = length if total is None else min(total, length)
            if total is None and hi is None:
                raise RunError('derive_recur_unbounded',
                               f"Step {sid!r}: row {n} has no end — its until and "
                               f"count are unknown and no window closes it.", sid)
            step_n = every or 1
            k = _first_index(start, lo, step_n, unit) if lo is not None else 0
            emitted = 0
            while total is None or k < total:
                try:
                    when = _shift(start, unit, k * step_n)
                except (OverflowError, ValueError):
                    break
                if hi is not None and when >= hi:
                    break
                if lo is None or when >= lo:
                    emitted += 1
                    if emitted > cap:
                        raise RunError('derive_expansion_too_large',
                                       f"Step {sid!r}: row {n} expands into more than "
                                       f"{cap} occurrences.", sid)
                    new = dict(row)
                    new['occurrence'] = when
                    new['occurrence_index'] = decimal.Decimal(k)
                    # Unknown when only a window bounds the series: its
                    # length is then a fact about the window, not the series.
                    new['occurrence_total'] = (decimal.Decimal(total)
                                               if total is not None else None)
                    out.append(new)
                    self.grow(out, sid)
                k += 1
                self.tick(sid, every=256)
        return out

    def op_repeat(self, c, data):
        sid, cap = c['id'], self.lim.max_expansion
        out = []
        for n, row in enumerate(data[0]):
            self.tick(sid)
            raw = self.ev(c['times'], row)
            if raw is None:
                self.skip(sid, 'unknown_times')
                continue
            times = _whole(raw)
            if times is None or times < 0:
                self.skip(sid, 'invalid_times')
                continue
            if times > cap:
                raise RunError('derive_expansion_too_large',
                               f"Step {sid!r}: row {n} repeats {times} times, more "
                               f"than {cap}.", sid)
            for i in range(times):
                new = dict(row)
                new['index'] = decimal.Decimal(i)
                out.append(new)
            self.grow(out, sid)
        return out

    def op_group(self, c, data):
        sid = c['id']
        rows = data[0]
        if c['order_by']:
            rows = self.sort(rows, c['order_by'])
        groups = {}
        keys = {}
        if not c['by']:
            groups[()] = list(rows)
            keys[()] = {}
        for row in rows:
            self.tick(sid)
            if not c['by']:
                continue
            values = {col: self.ev(e, row) for col, e in c['by']}
            k = tuple(_hashable(values[col]) for col, _ in c['by'])
            if k not in groups:
                groups[k] = []
                keys[k] = values
            groups[k].append(row)
        out = []
        for k, members in groups.items():
            new = dict(keys[k])
            for col, e in c['set']:
                aggs = {}
                for idx, fname, args in e.aggregates:
                    values = ([expr.evaluate_node(args[0], r, self.as_of, self.params)
                               for r in members] if args else None)
                    aggs[idx] = _aggregate(fname, values, len(members))
                new[col] = self.ev(e, new, aggs)
            out.append(new)
            self.tick(sid)
        return out

    def op_running(self, c, data):
        sid = c['id']
        rows = self.sort([dict(r) for r in data[0]], c['order_by'])
        for col, e in c['set']:
            states = {}
            for row in rows:
                self.tick(sid)
                part = tuple(_hashable(self.ev(pe, row)) for pe, _ in c['partition_by'])
                okey = tuple(_hashable(self.ev(oe, row)) for oe, _ in c['order_by'])
                st = states.get(part)
                if st is None:
                    st = states[part] = {'n': 0, 'last': None, 'rank': 0, 'dense': 0,
                                         'prev': None, 'sums': {}}
                tie = st['n'] > 0 and okey == st['last']
                rank = st['rank'] if tie else st['n'] + 1
                dense = st['dense'] if tie else st['dense'] + 1
                aggs = {}
                for idx, fname, args in e.aggregates:
                    if fname == 'cumsum':
                        v = expr.as_decimal(expr.evaluate_node(args[0], row, self.as_of,
                                                               self.params))
                        total = st['sums'].get(idx, _ZERO)
                        if v is not None:
                            total = _CONTEXT.add(total, v)
                        st['sums'][idx] = total
                        aggs[idx] = total
                    elif fname == 'row_number':
                        aggs[idx] = decimal.Decimal(st['n'] + 1)
                    elif fname == 'rank':
                        aggs[idx] = decimal.Decimal(rank)
                    elif fname == 'dense_rank':
                        aggs[idx] = decimal.Decimal(dense)
                    elif fname == 'previous':
                        aggs[idx] = (None if st['prev'] is None else
                                     expr.evaluate_node(args[0], st['prev'], self.as_of,
                                                        self.params))
                row[col] = self.ev(e, row, aggs)
                st['n'] += 1
                st['last'], st['rank'], st['dense'], st['prev'] = okey, rank, dense, row
        return rows

    def op_union(self, c, data):
        columns = list(self.plan.schemas[c['id']])
        out = []
        for rows in data:
            for row in rows:
                self.tick(c['id'])
                out.append({col: row.get(col) for col in columns})
            self.grow(out, c['id'])
        return out

    def op_join(self, c, data):
        sid = c['id']
        left, right = data
        columns = c['right_columns']
        pairs = c['on']
        index = None
        if pairs:
            index = {}
            for r in right:
                self.tick(sid)
                k = tuple(self.ev(re_, r) for _, re_ in pairs)
                if any(v is None for v in k):
                    continue
                index.setdefault(tuple(_hashable(v) for v in k), []).append(r)
        out = []
        for row in left:
            self.tick(sid)
            if index is None:
                matches = right
            else:
                k = tuple(self.ev(le, row) for le, _ in pairs)
                matches = ([] if any(v is None for v in k)
                           else index.get(tuple(_hashable(v) for v in k), []))
            for m in matches:
                new = dict(row)
                for col, name in columns:
                    new[name] = m.get(col)
                out.append(new)
                self.grow(out, sid)
            if not matches and c['how'] == 'left':
                new = dict(row)
                for _, name in columns:
                    new[name] = None
                out.append(new)
                self.grow(out, sid)
        return out

    def op_write(self, c, data):
        sid = c['id']
        plan = self.plan
        rows = [{col: row.get(col) for col in plan.output} for row in data[0]]
        if len(rows) > self.lim.max_write_rows:
            raise RunError('derive_too_many_write_rows',
                           f"The run would write {len(rows)} rows; the ceiling is "
                           f"{self.lim.max_write_rows}.", sid)
        seen = set()
        for row in rows:
            k = tuple(_hashable(_stored(row[col], plan.output[col])) for col in plan.key)
            if k in seen:
                named = ', '.join(f"{col}={_render(v)!r}" for col, v in zip(plan.key, k))
                raise RunError('derive_duplicate_key',
                               f"Two output rows share the key {named}; the key must "
                               f"tell every calculated row apart.", sid)
            seen.add(k)
        return rows

    # -- ordering ------------------------------------------------------------ #

    def sort(self, rows, specs):
        keyed = [([self.ev(e, r) for e, _ in specs], r) for r in rows]
        descs = [desc for _, desc in specs]

        def cmp(a, b):
            for x, y, desc in zip(a[0], b[0], descs):
                c = _compare(x, y)
                if c and x is not None and y is not None and desc:
                    c = -c
                if c:
                    return c
            return 0

        keyed.sort(key=functools.cmp_to_key(cmp))
        return [r for _, r in keyed]


def _compare(x, y):
    """Unknowns last, whichever the direction."""
    if x is None and y is None:
        return 0
    if x is None:
        return 1
    if y is None:
        return -1
    try:
        return -1 if x < y else 1 if x > y else 0
    except TypeError:
        a, b = type(x).__name__, type(y).__name__
        return -1 if a < b else 1 if a > b else 0


def _aggregate(name, values, n_rows):
    if name == 'count':
        if values is None:
            return decimal.Decimal(n_rows)
        return decimal.Decimal(sum(1 for v in values if v is not None and v != ''))
    present = [v for v in values if v is not None]
    if name in ('first', 'last'):
        return (present[0] if name == 'first' else present[-1]) if present else None
    if name in ('min', 'max'):
        if not present:
            return None
        try:
            return min(present) if name == 'min' else max(present)
        except TypeError:
            return None
    numbers = [n for n in (expr.as_decimal(v) for v in present) if n is not None]
    if name == 'sum':
        total = _ZERO
        for n in numbers:
            total = _CONTEXT.add(total, n)
        return total
    if not numbers:
        return None
    if name == 'avg':
        total = _ZERO
        for n in numbers:
            total = _CONTEXT.add(total, n)
        return _CONTEXT.divide(total, decimal.Decimal(len(numbers)))
    if name == 'median':
        numbers.sort()
        mid = len(numbers) // 2
        if len(numbers) % 2:
            return numbers[mid]
        return _CONTEXT.divide(_CONTEXT.add(numbers[mid - 1], numbers[mid]),
                               decimal.Decimal(2))
    return None  # pragma: no cover


# -- recurrence arithmetic --------------------------------------------------- #

def _shift(start, unit, n):
    if unit == 'day':
        return dates.add_days(start, n)
    if unit == 'week':
        return dates.add_days(start, 7 * n)
    if unit == 'month':
        return dates.add_months(start, n)
    return dates.add_years(start, n)


def _units_between(a, b, unit):
    """Whole units from `a` to `b` (≥ 0 when `b` is later)."""
    if unit == 'day':
        return dates.days_between(a, b)
    if unit == 'week':
        return dates.days_between(a, b) // 7
    m = dates.months_between(a, b)
    return m if unit == 'month' else m // 12


def _first_index(start, lo, step, unit):
    """The first series index whose occurrence is on or after `lo`, found by
    jumping — a weekly series that began in 1990 is not walked week by week."""
    if lo <= start:
        return 0
    k = max(0, _units_between(start, lo, unit) // step - 1)
    while _shift(start, unit, k * step) < lo:
        k += 1
    return k


def _series_length(start, until, step, unit):
    """How many occurrences fall on or before `until`."""
    if until < start:
        return 0
    k = _units_between(start, until, unit) // step
    while k >= 0 and _shift(start, unit, k * step) > until:
        k -= 1
    while _shift(start, unit, (k + 1) * step) <= until:
        k += 1
    return k + 1


# --------------------------------------------------------------------------- #
# Entry points
# --------------------------------------------------------------------------- #

def run(transform, inputs, params=None, as_of=None, limits=None, clock=None):
    """Run a transform (a declaration or a checked `Plan`) over `inputs`
    (`{slot: [row dict]}`). Returns a `RunResult`; raises `RunError` (refused
    whole) or `TransformError` (a declaration the gate refuses)."""
    plan = transform if isinstance(transform, Plan) else check(transform)
    lim = limits or limits_mod.DEFAULT
    as_of = dates.as_date(as_of) if as_of is not None else None
    inputs = inputs or {}
    unknown = [s for s in inputs if s not in plan.slots]
    if unknown:
        raise RunError('derive_unknown_input',
                       f"This transform has no input slot {', '.join(map(repr, unknown))}.",
                       unknown[0])
    resolved = _resolve_params(plan, params or {}, as_of)
    state = _Run(plan, resolved, as_of, lim, clock or time.monotonic)
    data, counts = {}, {}
    for slot, cols in plan.slots.items():
        rows = inputs.get(slot) or []
        if len(rows) > lim.max_input_rows:
            raise RunError('derive_too_many_input_rows',
                           f"Input {slot!r} has {len(rows)} rows; the ceiling is "
                           f"{lim.max_input_rows}.", slot)
        data[slot] = [{col: _coerce((r or {}).get(col), t) for col, t in cols.items()}
                      for r in rows]
        counts[slot] = len(rows)
    for sid in plan.order:
        c = plan.steps[sid]
        state.tick(sid, every=1)
        rows = getattr(state, 'op_' + c['op'])(c, [data[s] for s in c['sources']])
        state.grow(rows, sid)
        data[sid] = rows
        counts[sid] = len(rows)
    return RunResult(data[plan.write_id], counts, state.skipped, as_of, resolved)


def run_examples(transform, limits=None):
    """Run every example a transform carries; `[]` when all pass, otherwise one
    failure per example that did not, saying which rows and columns differ."""
    try:
        plan = check(transform)
    except TransformError as exc:
        return [{'example': None, 'code': 'transform_invalid', 'msg': str(exc),
                 'errors': exc.errors}]
    failures = []
    for i, ex in enumerate(transform.get('examples') or []):
        try:
            result = run(plan, ex.get('inputs') or {}, ex.get('params'),
                         as_of=ex.get('as_of'), limits=limits)
        except RunError as exc:
            failures.append({'example': i, 'code': exc.code, 'msg': exc.message,
                             'step': exc.step})
            continue
        failure = _compare_rows(plan, ex.get('expect') or [], result.rows)
        if failure:
            failure['example'] = i
            failures.append(failure)
    return failures


def _compare_rows(plan, expected, actual):
    def stored(row, cols):
        return {c: _stored(row.get(c), plan.output[c]) for c in cols if c in plan.output}

    def key_of(row):
        return tuple(_hashable(row.get(c)) for c in plan.key)

    def rendered(row):
        return {c: _render(v) for c, v in row.items()}

    want = {}
    for row in expected:
        s = stored(row, list(row))
        want[key_of(s)] = s
    have = {}
    for row in actual:
        s = stored(row, list(plan.output))
        have[key_of(s)] = s
    missing = [rendered(want[k]) for k in want if k not in have]
    unexpected = [rendered(have[k]) for k in have if k not in want]
    differing = []
    for k, w in want.items():
        h = have.get(k)
        if h is None:
            continue
        for col, v in w.items():
            if h.get(col) != v:
                differing.append({'key': {c: _render(x) for c, x in zip(plan.key, k)},
                                  'column': col, 'expected': _render(v),
                                  'actual': _render(h.get(col))})
    if not (missing or unexpected or differing):
        return None
    return {'code': 'transform_example_mismatch',
            'msg': (f"{len(missing)} expected row(s) missing, {len(unexpected)} "
                    f"unexpected, {len(differing)} value(s) differ."),
            'missing': missing, 'unexpected': unexpected, 'differing': differing}


_SEED_PATH = os.path.join(os.path.dirname(__file__), 'seed_transforms.json')


@functools.lru_cache(maxsize=1)
def _seed_file():
    with open(_SEED_PATH, encoding='utf-8') as fh:
        return json.load(fh)['transforms']


def seed_transforms():
    """The scope's seed transforms (§5.3), as declarations — a fresh copy
    each call, so a caller may change one without touching the next."""
    return copy.deepcopy(_seed_file())
