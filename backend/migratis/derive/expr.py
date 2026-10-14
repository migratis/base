"""The expression language (SCOPE_calculated_tables.md §5.2, phase P0).

Closed, typed, parsed once into a tree and evaluated by a tree-walker — never
`eval`, no attribute access, no loops, no user-defined functions, capped in size
and depth. The same file runs in the design sandbox and in every generated
application (it is mirrored into base), so a value the preview computes is the
value the shipped application computes: there is no second implementation to
drift.

    e = compile('add_days(planted_on, days_to_maturity)',
                types={'planted_on': 'date', 'days_to_maturity': 'integer'})
    e.references         # ['planted_on', 'days_to_maturity']
    e.result_type        # 'date'
    e.evaluate({'planted_on': '2026-04-15', 'days_to_maturity': 70})

Four rules carry it:

* **Numbers are `Decimal`**, rounded once, at the write, by the target field's
  declared type (`to_field_value`), `ROUND_HALF_UP` — an owner expects 2.5 to
  become 3, and Python's default would make it 2 on their first invoice.
* **Null is unknown** — `computed.py`'s rule: arithmetic and comparison with an
  unknown are unknown, division by zero is unknown, `if` takes its else branch
  on an unknown condition, and `and`/`or` are three-valued.
* **Evaluation never raises.** A value that cannot be computed is `None`; a
  stored declaration outlives the data it was written against, and a 500 on
  every write of an entity is a worse answer than a blank column.
* **Types are checked as far as they are known.** `Field.clean` sees one field
  and none of its siblings (a design pass writes a spec before the field it
  names exists), so with `types=None` only the shape is checked; the advisory
  that runs over a finished design passes the types and gets the full check.
"""
import datetime
import decimal
import functools
import re

from . import dates

# --------------------------------------------------------------------------- #
# Limits
# --------------------------------------------------------------------------- #

MAX_SOURCE_LENGTH = 2000
MAX_NODES = 200
MAX_DEPTH = 40
# A power beyond this is not a calculation anybody's application needs, and
# `Decimal` would happily spend real time on it.
MAX_EXPONENT = 1000

# Numbers beyond ±1e99 overflow to unknown rather than to a figure nobody can
# read; 28 significant digits is far beyond any money or quantity.
_CONTEXT = decimal.Context(
    prec=28, rounding=decimal.ROUND_HALF_UP, Emax=99, Emin=-99,
    traps=[decimal.Overflow, decimal.InvalidOperation, decimal.DivisionByZero],
)


class ExpressionError(Exception):
    """A declaration that cannot be compiled. `code` is a stable token for the
    rejection catalogue; `message` is the sentence a person reads."""

    def __init__(self, code, message, position=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.position = position

    def __str__(self):
        return self.message


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #

NUMBER, DATE, TEXT, BOOL, ANY = 'number', 'date', 'text', 'bool', 'any'

#: How a declared field type reads inside an expression. A type that is not
#: here cannot be read at all — a file, an image, a map and a list of links
#: have no value an expression could compute with.
FIELD_TYPE_READS_AS = {
    'integer':  NUMBER,
    'decimal':  NUMBER,
    'date':     DATE,
    'datetime': DATE,   # read as its date — expressions reason in days
    'string':   TEXT,
    'text':     TEXT,
    'enum':     TEXT,
    'boolean':  BOOL,
    'fk':       ANY,    # the linked record's id: only `is_set` means anything
}

#: The field types an expression may fill, and the result type each needs.
TARGET_FIELD_TYPES = {
    'integer': NUMBER,
    'decimal': NUMBER,
    'date':    DATE,
    'string':  TEXT,
    'text':    TEXT,
    'enum':    TEXT,
    'boolean': BOOL,
}

_TYPE_WORDS = {NUMBER: 'a number', DATE: 'a date', TEXT: 'text', BOOL: 'yes/no'}


def fits_field(result_type, field_type):
    """`''` when an expression of `result_type` may fill a `field_type` field,
    otherwise the sentence saying why not."""
    wanted = TARGET_FIELD_TYPES.get(field_type)
    if wanted is None:
        if field_type == 'datetime':
            return ("A 'datetime' field records a moment, and an expression "
                    "computes a date — declare the field as 'date'.")
        return (f"An expression computes a number, a date, text or yes/no, so it "
                f"cannot fill a {field_type!r} field.")
    if result_type in (ANY, wanted):
        return ''
    return (f"This expression computes {_TYPE_WORDS.get(result_type, result_type)}, "
            f"but the field is {field_type!r}, which holds "
            f"{_TYPE_WORDS[wanted]}.")


# --------------------------------------------------------------------------- #
# Tokens
# --------------------------------------------------------------------------- #

_TOKEN = re.compile(r'''
    (?P<ws>\s+)
  | (?P<num>\d+(?:\.\d*)?|\.\d+)
  | (?P<str>'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")
  | (?P<name>[^\W\d]\w*)
  | (?P<op>\*\*|==|!=|<>|<=|>=|[-+*/%<>=(),.])
''', re.VERBOSE | re.UNICODE)

_KEYWORDS = {'true', 'false', 'null', 'and', 'or', 'not', 'today'}


def _tokenize(source):
    tokens, pos = [], 0
    while pos < len(source):
        m = _TOKEN.match(source, pos)
        if not m:
            raise ExpressionError(
                'expression_syntax',
                f"Unexpected character {source[pos]!r} at position {pos + 1}.",
                pos + 1)
        kind = m.lastgroup
        if kind != 'ws':
            text = m.group(kind)
            if kind == 'name' and text.lower() in _KEYWORDS:
                kind, text = 'kw', text.lower()
            tokens.append((kind, text, pos + 1))
        pos = m.end()
    tokens.append(('end', '', len(source) + 1))
    return tokens


def _unquote(text):
    body = text[1:-1]
    return re.sub(r'\\(.)', r'\1', body)


# --------------------------------------------------------------------------- #
# Functions
# --------------------------------------------------------------------------- #

# name -> (min args, max args or None for variadic)
_ARITY = {
    'round': (1, 2), 'floor': (1, 1), 'ceil': (1, 1), 'abs': (1, 1),
    'min': (2, None), 'max': (2, None),
    'if': (3, 3), 'coalesce': (1, None), 'is_set': (1, 1),
    'add_days': (2, 2), 'add_weeks': (2, 2), 'add_months': (2, 2),
    'add_years': (2, 2), 'days_between': (2, 2), 'months_between': (2, 2),
    'year': (1, 1), 'month': (1, 1), 'day': (1, 1), 'weekday': (1, 1),
    'week_start': (1, 1), 'month_start': (1, 1), 'quarter_start': (1, 1),
    'year_start': (1, 1),
    'concat': (1, None), 'lower': (1, 1), 'upper': (1, 1), 'trim': (1, 1),
}

FUNCTIONS = tuple(sorted(_ARITY))

#: Functions over a set of rows rather than one row. They exist only where the
#: engine passes them to `compile` — a calculated field knows none of them, so
#: `sum(quantity)` in a field is an unknown function, not a silent per-row sum.
#: `min`/`max` with one argument are the aggregate; with two or more they stay
#: the scalar function, so `max(sum(row.n), 0)` reads as written.
GROUP_FUNCTIONS = {
    'sum': (1, 1), 'count': (0, 1), 'avg': (1, 1), 'min': (1, 1), 'max': (1, 1),
    'first': (1, 1), 'last': (1, 1), 'median': (1, 1),
}
#: Functions over the rows before this one in a `running` step's order.
WINDOW_FUNCTIONS = {
    'cumsum': (1, 1), 'rank': (0, 0), 'dense_rank': (0, 0), 'row_number': (0, 0),
    'previous': (1, 1),
}


# --------------------------------------------------------------------------- #
# Parser — recursive descent into tuples
# --------------------------------------------------------------------------- #

class _Parser:

    def __init__(self, source, allow_today, params, aggregates=None):
        self.tokens = _tokenize(source)
        self.i = 0
        self.depth = 0
        self.nodes = 0
        self.allow_today = allow_today
        self.params = params
        self.aggregates = aggregates or {}
        self.agg_count = 0

    # -- plumbing ----------------------------------------------------------- #

    def peek(self):
        return self.tokens[self.i]

    def take(self):
        tok = self.tokens[self.i]
        self.i += 1
        return tok

    def expect(self, text):
        tok = self.take()
        if tok[1] != text or tok[0] == 'str':
            self.fail(tok, f"expected {text!r}")
        return tok

    def fail(self, tok, what):
        found = 'the end of the expression' if tok[0] == 'end' else repr(tok[1])
        raise ExpressionError(
            'expression_syntax', f"Syntax error at position {tok[2]}: {what}, "
                                 f"found {found}.", tok[2])

    def node(self, *parts):
        self.nodes += 1
        if self.nodes > MAX_NODES:
            raise ExpressionError(
                'expression_too_large',
                f"The expression is too large (more than {MAX_NODES} parts). "
                f"Split it across several calculated fields.")
        return parts

    def enter(self):
        self.depth += 1
        if self.depth > MAX_DEPTH:
            raise ExpressionError(
                'expression_too_large',
                f"The expression is nested too deeply (more than {MAX_DEPTH} "
                f"levels).")

    def leave(self):
        self.depth -= 1

    def at(self, kind, *texts):
        tok = self.peek()
        return tok[0] == kind and (not texts or tok[1] in texts)

    # -- grammar ------------------------------------------------------------ #

    def parse(self):
        if self.peek()[0] == 'end':
            raise ExpressionError('expression_syntax', 'The expression is empty.', 1)
        tree = self.expr()
        if self.peek()[0] != 'end':
            self.fail(self.peek(), 'expected an operator or the end')
        return tree

    def expr(self):
        self.enter()
        try:
            return self.or_()
        finally:
            self.leave()

    def or_(self):
        left = self.and_()
        while self.at('kw', 'or'):
            self.take()
            left = self.node('or', left, self.and_())
        return left

    def and_(self):
        left = self.not_()
        while self.at('kw', 'and'):
            self.take()
            left = self.node('and', left, self.not_())
        return left

    def not_(self):
        if self.at('kw', 'not'):
            self.take()
            self.enter()
            try:
                return self.node('not', self.not_())
            finally:
                self.leave()
        return self.comparison()

    def comparison(self):
        left = self.additive()
        if self.at('op', '=', '==', '!=', '<>', '<', '<=', '>', '>='):
            op = self.take()[1]
            op = {'==': '=', '<>': '!='}.get(op, op)
            left = self.node('cmp', op, left, self.additive())
        return left

    def additive(self):
        left = self.multiplicative()
        while self.at('op', '+', '-'):
            op = self.take()[1]
            left = self.node('bin', op, left, self.multiplicative())
        return left

    def multiplicative(self):
        left = self.unary()
        while self.at('op', '*', '/', '%'):
            op = self.take()[1]
            left = self.node('bin', op, left, self.unary())
        return left

    def unary(self):
        if self.at('op', '-', '+'):
            op = self.take()[1]
            self.enter()
            try:
                operand = self.unary()
            finally:
                self.leave()
            return operand if op == '+' else self.node('neg', operand)
        return self.power()

    def power(self):
        base = self.atom()
        if self.at('op', '**'):
            self.take()
            self.enter()
            try:
                return self.node('bin', '**', base, self.unary())
            finally:
                self.leave()
        return base

    def atom(self):
        tok = self.take()
        kind, text, pos = tok
        if kind == 'num':
            return self.node('lit', decimal.Decimal(text))
        if kind == 'str':
            return self.node('lit', _unquote(text))
        if kind == 'kw':
            if text in ('true', 'false'):
                return self.node('lit', text == 'true')
            if text == 'null':
                return self.node('lit', None)
            if text == 'today':
                if not self.allow_today:
                    raise ExpressionError(
                        'expression_today_not_allowed',
                        "`today` cannot be used in a calculated field: the value "
                        "is stored when the record is saved, so it would be "
                        "right on that day and wrong every day after.", pos)
                return self.node('today')
            self.fail(tok, 'expected a value')
        if kind == 'op' and text == '(':
            inner = self.expr()
            self.expect(')')
            return inner
        if kind == 'name':
            if self.at('op', '('):
                return self.call(text, pos)
            return self.reference(text, pos)
        self.fail(tok, 'expected a value')

    def call(self, name, pos):
        fname = name.lower()
        if fname not in _ARITY and fname not in self.aggregates:
            available = sorted(set(FUNCTIONS) | set(self.aggregates))
            raise ExpressionError(
                'expression_unknown_function',
                f"Unknown function {name!r} at position {pos}. Available: "
                f"{', '.join(available)}.", pos)
        self.expect('(')
        args = []
        self.enter()
        try:
            if not self.at('op', ')'):
                args.append(self.expr())
                while self.at('op', ','):
                    self.take()
                    args.append(self.expr())
        finally:
            self.leave()
        self.expect(')')
        if fname in self.aggregates and not (fname in _ARITY and len(args) >= 2):
            return self.aggregate(fname, args, pos)
        lo, hi = _ARITY[fname]
        if len(args) < lo or (hi is not None and len(args) > hi):
            want = (f"{lo}" if lo == hi else
                    f"at least {lo}" if hi is None else f"{lo} to {hi}")
            raise ExpressionError(
                'expression_arity',
                f"{fname}() takes {want} argument{'s' if (hi or lo) > 1 else ''}, "
                f"got {len(args)} (position {pos}).", pos)
        return self.node('call', fname, tuple(args))

    def aggregate(self, fname, args, pos):
        lo, hi = self.aggregates[fname]
        if len(args) < lo or (hi is not None and len(args) > hi):
            want = f"{lo}" if lo == hi else f"{lo} to {hi}"
            raise ExpressionError(
                'expression_arity',
                f"{fname}() takes {want} argument{'' if hi == 1 else 's'}, "
                f"got {len(args)} (position {pos}).", pos)
        if any(_contains_aggregate(a) for a in args):
            raise ExpressionError(
                'expression_nested_aggregate',
                f"{fname}() at position {pos} contains another aggregate; an "
                f"aggregate reads the rows one at a time, so it cannot hold "
                f"one. Compute the inner value in an earlier step.", pos)
        idx = self.agg_count
        self.agg_count += 1
        return self.node('agg', idx, fname, tuple(args))

    def reference(self, name, pos):
        parts = [name]
        while self.at('op', '.'):
            self.take()
            tok = self.take()
            if tok[0] not in ('name', 'kw'):
                self.fail(tok, 'expected a name after "."')
            parts.append(tok[1])
        if parts[0] == 'param' and len(parts) > 1:
            if self.params is None or len(parts) != 2:
                raise ExpressionError(
                    'expression_param_not_allowed',
                    f"`{'.'.join(parts)}` names a parameter, and there are none "
                    f"here — a calculated field reads only its own record.", pos)
            return self.node('param', parts[1])
        if parts[0] == 'row' and len(parts) > 1:
            parts = parts[1:]
        if len(parts) > 2:
            raise ExpressionError(
                'expression_path_too_deep',
                f"`{'.'.join(parts)}` follows more than one link. An expression "
                f"reads its own fields and the fields of a record it links to "
                f"directly (`link.field`), no further.", pos)
        return self.node('ref', '.'.join(parts))


def _contains_aggregate(node):
    found = []
    _collect_aggregates(node, found)
    return bool(found)


def _collect_aggregates(node, out):
    if node[0] == 'agg':
        out.append((node[1], node[2], node[3]))
        return
    for part in node[1:]:
        if isinstance(part, tuple) and part and isinstance(part[0], str):
            _collect_aggregates(part, out)
        elif isinstance(part, tuple):
            for a in part:
                if isinstance(a, tuple) and a and isinstance(a[0], str):
                    _collect_aggregates(a, out)


# --------------------------------------------------------------------------- #
# Type checker
# --------------------------------------------------------------------------- #

def _type_error(message):
    return ExpressionError('expression_type', message)


def _unify(a, b, what):
    if a == ANY:
        return b
    if b == ANY or a == b:
        return a
    raise _type_error(f"{what} mixes {_TYPE_WORDS[a]} and {_TYPE_WORDS[b]}.")


def _need(t, wanted, what):
    if t not in (ANY, wanted):
        hint = ''
        if wanted == NUMBER and t == DATE:
            hint = (' To move a date use add_days / add_weeks / add_months / '
                    'add_years; to measure between two dates use days_between '
                    'or months_between.')
        elif wanted == NUMBER and t == TEXT:
            hint = ' To join text use concat().'
        raise _type_error(f"{what} needs {_TYPE_WORDS[wanted]}, not "
                          f"{_TYPE_WORDS[t]}.{hint}")


_DATE_FUNCS = {
    'add_days', 'add_weeks', 'add_months', 'add_years',
}
_DATE_PARTS = {'year', 'month', 'day', 'weekday'}
_DATE_STARTS = {'week_start', 'month_start', 'quarter_start', 'year_start'}


class _Ctx:
    """What a reference may name while checking: the row's own columns
    (`types`), the declared params, and — inside an aggregate — the columns of
    the rows being aggregated (`inner`)."""

    def __init__(self, types, params=None, inner=None):
        self.types = types
        self.refs = []
        self.params = params
        self.inner = inner


def _check(node, ctx):
    types, refs = ctx.types, ctx.refs
    tag = node[0]
    if tag == 'lit':
        v = node[1]
        if v is None:
            return ANY
        if isinstance(v, bool):
            return BOOL
        if isinstance(v, decimal.Decimal):
            return NUMBER
        return TEXT
    if tag == 'today':
        return DATE
    if tag == 'param':
        params = ctx.params
        if isinstance(params, (set, frozenset, list, tuple, dict)) and node[1] not in params:
            known = ', '.join(sorted(params)) or 'none'
            raise ExpressionError(
                'expression_unresolved_reference',
                f"`param.{node[1]}` is not a declared parameter (declared: {known}).")
        if isinstance(params, dict):
            return FIELD_TYPE_READS_AS.get(params[node[1]], ANY)
        return ANY
    if tag == 'agg':
        inner = ctx.inner if ctx.inner is not None else ctx
        arg_types = [_check(a, inner) for a in node[3]]
        return _check_aggregate(node[2], arg_types)
    if tag == 'ref':
        path = node[1]
        if path not in refs:
            refs.append(path)
        if types is None:
            return ANY
        if path not in types:
            raise ExpressionError(
                'expression_unresolved_reference',
                f"`{path}` is not a field this expression can read.")
        reads_as = FIELD_TYPE_READS_AS.get(types[path])
        if reads_as is None:
            raise _type_error(
                f"`{path}` is a {types[path]!r} field, which holds nothing an "
                f"expression can compute with.")
        return reads_as
    if tag == 'neg':
        _need(_check(node[1], ctx), NUMBER, 'A minus sign')
        return NUMBER
    if tag == 'bin':
        op = node[1]
        a = _check(node[2], ctx)
        b = _check(node[3], ctx)
        _need(a, NUMBER, f"`{op}`")
        _need(b, NUMBER, f"`{op}`")
        return NUMBER
    if tag == 'cmp':
        a = _check(node[2], ctx)
        b = _check(node[3], ctx)
        t = _unify(a, b, f"The comparison `{node[1]}`")
        if node[1] not in ('=', '!=') and t == BOOL:
            raise _type_error(f"`{node[1]}` cannot order yes/no values.")
        return BOOL
    if tag in ('and', 'or'):
        _need(_check(node[1], ctx), BOOL, f"`{tag}`")
        _need(_check(node[2], ctx), BOOL, f"`{tag}`")
        return BOOL
    if tag == 'not':
        _need(_check(node[1], ctx), BOOL, '`not`')
        return BOOL
    if tag == 'call':
        return _check_call(node[1], [_check(a, ctx) for a in node[2]])
    raise _type_error(f"Unknown node {tag!r}.")  # pragma: no cover


def _check_aggregate(name, ts):
    w = f"{name}()"
    if name in ('sum', 'avg', 'median', 'cumsum'):
        _need(ts[0], NUMBER, w)
        return NUMBER
    if name in ('count', 'rank', 'dense_rank', 'row_number'):
        return NUMBER
    if name in ('min', 'max'):
        if ts[0] not in (ANY, NUMBER, DATE, TEXT):
            raise _type_error(f"{w} compares numbers, dates or text.")
        return ts[0]
    return ts[0]  # first, last, previous


def _check_call(name, ts):
    w = f"{name}()"
    if name in ('round', 'floor', 'ceil', 'abs'):
        for t in ts:
            _need(t, NUMBER, w)
        return NUMBER
    if name in ('min', 'max'):
        t = ANY
        for x in ts:
            t = _unify(t, x, w)
        if t not in (ANY, NUMBER, DATE):
            raise _type_error(f"{w} compares numbers or dates.")
        return NUMBER if t == ANY else t
    if name == 'if':
        _need(ts[0], BOOL, 'The condition of if()')
        return _unify(ts[1], ts[2], 'if()')
    if name == 'coalesce':
        t = ANY
        for x in ts:
            t = _unify(t, x, w)
        return t
    if name == 'is_set':
        return BOOL
    if name in _DATE_FUNCS:
        _need(ts[0], DATE, w)
        _need(ts[1], NUMBER, w)
        return DATE
    if name in ('days_between', 'months_between'):
        _need(ts[0], DATE, w)
        _need(ts[1], DATE, w)
        return NUMBER
    if name in _DATE_PARTS:
        _need(ts[0], DATE, w)
        return NUMBER
    if name in _DATE_STARTS:
        _need(ts[0], DATE, w)
        return DATE
    if name == 'concat':
        return TEXT
    if name in ('lower', 'upper', 'trim'):
        _need(ts[0], TEXT, w)
        return TEXT
    raise _type_error(f"Unknown function {name!r}.")  # pragma: no cover


# --------------------------------------------------------------------------- #
# Reading values
# --------------------------------------------------------------------------- #

_NUMERIC_TEXT = re.compile(r'^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$')


def as_decimal(value):
    """The number a stored value represents, as a `Decimal`, or `None`.

    `computed.as_number`'s rule: a number written as text (`"197.8"`, the shape
    prod app 6 stored) is that number; a `bool` is never one; a float is read as
    the digits it prints, so `0.1` is one tenth and not its binary neighbour.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, decimal.Decimal):
        return value if value.is_finite() else None
    if isinstance(value, int):
        return decimal.Decimal(value)
    if isinstance(value, float):
        if value != value or value in (float('inf'), float('-inf')):
            return None
        return decimal.Decimal(repr(value))
    if isinstance(value, str):
        text = value.strip()
        if not _NUMERIC_TEXT.match(text):
            return None
        return decimal.Decimal(text)
    return None


def _read(value, reads_as):
    if value is None:
        return None
    if reads_as == NUMBER:
        return as_decimal(value)
    if reads_as == DATE:
        return dates.as_date(value)
    if reads_as == TEXT:
        return value if isinstance(value, str) else str(value)
    if reads_as == BOOL:
        return value if isinstance(value, bool) else None
    return value


def _text(value):
    if value is None:
        return ''
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (datetime.date, datetime.datetime)):
        return dates.as_date(value).isoformat()
    if isinstance(value, (int, float, decimal.Decimal)):
        number = as_decimal(value)
        return '' if number is None else format(number, 'f')
    return str(value)


def _whole(n):
    """An integral Decimal as an int, or None."""
    if n is None or n != n.to_integral_value():
        return None
    return int(n)


# --------------------------------------------------------------------------- #
# Evaluator
# --------------------------------------------------------------------------- #

class _Unknown(Exception):
    """Raised inside the walker to abandon a branch; never escapes `evaluate`."""


class _Env:
    __slots__ = ('values', 'today', 'params', 'aggs')

    def __init__(self, values, today, params, aggs=None):
        self.values = values
        self.today = today
        self.params = params
        self.aggs = aggs


def _num(v):
    return as_decimal(v)


def _date(v):
    return dates.as_date(v)


def _truth(v):
    return v if isinstance(v, bool) else None


def _compare(op, a, b):
    if a is None or b is None:
        return None
    if isinstance(a, bool) or isinstance(b, bool):
        if not (isinstance(a, bool) and isinstance(b, bool)):
            return None
        x, y = a, b
    elif isinstance(a, (int, float, decimal.Decimal)) or isinstance(b, (int, float, decimal.Decimal)):
        x, y = _num(a), _num(b)
    elif isinstance(a, datetime.date) or isinstance(b, datetime.date):
        x, y = _date(a), _date(b)
    elif isinstance(a, str) and isinstance(b, str):
        x, y = a, b
    else:
        return None
    if x is None or y is None:
        return None
    if op == '=':
        return x == y
    if op == '!=':
        return x != y
    if isinstance(x, bool):
        return None
    if op == '<':
        return x < y
    if op == '<=':
        return x <= y
    if op == '>':
        return x > y
    return x >= y


def _arith(op, a, b):
    x, y = _num(a), _num(b)
    if x is None or y is None:
        return None
    if op == '+':
        return _CONTEXT.add(x, y)
    if op == '-':
        return _CONTEXT.subtract(x, y)
    if op == '*':
        return _CONTEXT.multiply(x, y)
    if op == '/':
        if y == 0:
            return None
        return _CONTEXT.divide(x, y)
    if op == '%':
        if y == 0:
            return None
        q = _CONTEXT.divide(x, y).to_integral_value(rounding=decimal.ROUND_FLOOR)
        return _CONTEXT.subtract(x, _CONTEXT.multiply(y, q))
    if op == '**':
        if abs(y) > MAX_EXPONENT:
            return None
        return _CONTEXT.power(x, y)
    return None  # pragma: no cover


def _eval(node, env):
    tag = node[0]
    if tag == 'lit':
        return node[1]
    if tag == 'ref':
        return env.values.get(node[1])
    if tag == 'today':
        return env.today
    if tag == 'param':
        return (env.params or {}).get(node[1])
    if tag == 'agg':
        return (env.aggs or {}).get(node[1])
    if tag == 'neg':
        x = _num(_eval(node[1], env))
        return None if x is None else _CONTEXT.minus(x)
    if tag == 'bin':
        return _arith(node[1], _eval(node[2], env), _eval(node[3], env))
    if tag == 'cmp':
        return _compare(node[1], _eval(node[2], env), _eval(node[3], env))
    if tag == 'and':
        a = _truth(_eval(node[1], env))
        if a is False:
            return False
        b = _truth(_eval(node[2], env))
        if b is False:
            return False
        return True if (a is True and b is True) else None
    if tag == 'or':
        a = _truth(_eval(node[1], env))
        if a is True:
            return True
        b = _truth(_eval(node[2], env))
        if b is True:
            return True
        return False if (a is False and b is False) else None
    if tag == 'not':
        a = _truth(_eval(node[1], env))
        return None if a is None else (not a)
    if tag == 'call':
        return _call(node[1], node[2], env)
    return None  # pragma: no cover


def _call(name, args, env):
    if name == 'if':
        cond = _truth(_eval(args[0], env))
        return _eval(args[1] if cond is True else args[2], env)
    if name == 'coalesce':
        # The first set value. When none is, empty text beats unknown: the
        # idiom `coalesce(row.unit, '')` asks for an empty text by default.
        blank = None
        for a in args:
            v = _eval(a, env)
            if v is not None and v != '':
                return v
            if v == '':
                blank = ''
        return blank

    vals = [_eval(a, env) for a in args]

    if name == 'is_set':
        return vals[0] is not None and vals[0] != ''
    if name == 'concat':
        return ''.join(_text(v) for v in vals)
    if name in ('lower', 'upper', 'trim'):
        v = vals[0]
        if not isinstance(v, str):
            return None
        return v.lower() if name == 'lower' else v.upper() if name == 'upper' else v.strip()

    if name in ('min', 'max'):
        if any(v is None for v in vals):
            return None
        if any(isinstance(v, datetime.date) for v in vals):
            ds = [_date(v) for v in vals]
            if any(d is None for d in ds):
                return None
            return min(ds) if name == 'min' else max(ds)
        ns = [_num(v) for v in vals]
        if any(n is None for n in ns):
            return None
        return min(ns) if name == 'min' else max(ns)

    if name in ('round', 'floor', 'ceil', 'abs'):
        x = _num(vals[0])
        if x is None:
            return None
        if name == 'abs':
            return abs(x)
        if name == 'floor':
            return x.to_integral_value(rounding=decimal.ROUND_FLOOR)
        if name == 'ceil':
            return x.to_integral_value(rounding=decimal.ROUND_CEILING)
        places = 0
        if len(vals) > 1:
            places = _whole(_num(vals[1]))
            if places is None or not -12 <= places <= 12:
                return None
        return x.quantize(decimal.Decimal(1).scaleb(-places),
                          rounding=decimal.ROUND_HALF_UP, context=_CONTEXT)

    if name in _DATE_FUNCS:
        d, n = _date(vals[0]), _whole(_num(vals[1]))
        if d is None or n is None:
            return None
        if name == 'add_days':
            return dates.add_days(d, n)
        if name == 'add_weeks':
            return dates.add_days(d, 7 * n)
        if name == 'add_months':
            return dates.add_months(d, n)
        return dates.add_years(d, n)

    if name in ('days_between', 'months_between'):
        a, b = _date(vals[0]), _date(vals[1])
        if a is None or b is None:
            return None
        fn = dates.days_between if name == 'days_between' else dates.months_between
        return decimal.Decimal(fn(a, b))

    if name in _DATE_PARTS:
        d = _date(vals[0])
        if d is None:
            return None
        part = {'year': d.year, 'month': d.month, 'day': d.day,
                'weekday': d.isoweekday()}[name]
        return decimal.Decimal(part)

    if name in _DATE_STARTS:
        d = _date(vals[0])
        if d is None:
            return None
        return getattr(dates, name)(d)

    return None  # pragma: no cover


def _normalise_result(v):
    if isinstance(v, bool) or v is None:
        return v
    if isinstance(v, (int, float)):
        return as_decimal(v)
    if isinstance(v, datetime.datetime):
        return v.date()
    return v


# --------------------------------------------------------------------------- #
# The compiled expression
# --------------------------------------------------------------------------- #

class Expression:
    """A parsed, checked expression. Immutable and safe to share."""

    def __init__(self, source, tree, references, result_type, types,
                 inner_references=None):
        self.source = source
        self.tree = tree
        self.references = references
        self.inner_references = inner_references or []
        self.result_type = result_type
        #: `[(index, function, args)]` — the aggregate / window calls the
        #: engine computes over a set of rows and hands back by index.
        self.aggregates = []
        _collect_aggregates(tree, self.aggregates)
        self._reads = {
            path: FIELD_TYPE_READS_AS.get(types[path], ANY) if types else ANY
            for path in references
        }

    def evaluate(self, values, today=None, params=None):
        """The value, or `None` when it is unknown. Never raises.

        `values` maps each reference (`'quantity'`, `'product.price'`) to the
        value as it is stored; it is read by the declared type the expression
        was compiled with, so `"197.8"` in a decimal field is a number and
        `"2026-01-31"` in a date field is a date.
        """
        try:
            read = {
                path: _read((values or {}).get(path), reads_as)
                for path, reads_as in self._reads.items()
            }
            env = _Env(read, dates.as_date(today) if today is not None else None,
                       params)
            return _normalise_result(_eval(self.tree, env))
        except Exception:  # an expression must never break a write
            return None

    def evaluate_row(self, values, today=None, params=None, aggs=None):
        """The engine's evaluation: `values` are already typed (the engine
        reads every input once, by its slot type), so nothing is re-read.
        `aggs` maps each aggregate's index to the value the engine computed.
        Never raises."""
        try:
            return _normalise_result(_eval(self.tree, _Env(values, today, params, aggs)))
        except Exception:  # a run must never be broken by one row
            return None

    def __repr__(self):
        return f"Expression({self.source!r})"


def evaluate_node(node, values, today=None, params=None):
    """One sub-tree (an aggregate's argument) over one typed row; `None` on
    any error."""
    try:
        return _normalise_result(_eval(node, _Env(values, today, params)))
    except Exception:
        return None


def compile(source, types=None, allow_today=True, params=None,  # noqa: A001
            aggregates=None, inner_types=None):
    """Parse and check `source`. Raises `ExpressionError`.

    `types` maps every readable reference to its declared field type; `None`
    checks the shape only. `params` names the parameters a transform declares
    (a dict to type them too); `None` (a calculated field) refuses `param.*`
    outright. `aggregates` is `GROUP_FUNCTIONS` or `WINDOW_FUNCTIONS` where the
    engine offers them; inside one, a reference names a column of the rows
    being aggregated, typed by `inner_types` (default: `types`).
    """
    if not isinstance(source, str) or not source.strip():
        raise ExpressionError('expression_syntax', 'The expression is empty.', 1)
    if len(source) > MAX_SOURCE_LENGTH:
        raise ExpressionError(
            'expression_too_large',
            f"The expression is longer than {MAX_SOURCE_LENGTH} characters.")
    tree = _Parser(source, allow_today, params, aggregates).parse()
    inner = None
    if aggregates and inner_types is not None:
        inner = _Ctx(dict(inner_types), params)
    ctx = _Ctx(dict(types) if types is not None else None, params, inner)
    result_type = _check(tree, ctx)
    return Expression(source, tree, ctx.refs, result_type, types,
                      inner.refs if inner is not None else None)


@functools.lru_cache(maxsize=1024)
def _compile_cached(source, types_items, allow_today):
    return compile(source, types=dict(types_items) if types_items is not None else None,
                   allow_today=allow_today)


def compile_cached(source, types=None, allow_today=False):
    """`compile`, memoised — what a write path calls on every save."""
    items = tuple(sorted(types.items())) if types is not None else None
    return _compile_cached(source, items, allow_today)


def evaluate_source(source, values, types=None):
    """Compile (cached) and evaluate a field expression; `None` on any error.

    The one call a generated application's `prepare()` makes.
    """
    try:
        return compile_cached(source, types).evaluate(values)
    except ExpressionError:
        return None


# --------------------------------------------------------------------------- #
# Writing values
# --------------------------------------------------------------------------- #

_CENT = decimal.Decimal('0.01')


def to_field_value(value, field_type, choices=None):
    """`value` as the declared field type holds it, or `None` when it does not
    fit. Numbers are rounded here, once, `ROUND_HALF_UP` — an `integer` to a
    whole number and a `decimal` to the two places every generated
    `DecimalField` carries."""
    if value is None:
        return None
    wanted = TARGET_FIELD_TYPES.get(field_type)
    try:
        if wanted == NUMBER:
            n = as_decimal(value)
            if n is None:
                return None
            if field_type == 'integer':
                return int(n.quantize(decimal.Decimal(1), rounding=decimal.ROUND_HALF_UP))
            return n.quantize(_CENT, rounding=decimal.ROUND_HALF_UP)
        if wanted == DATE:
            if isinstance(value, datetime.date):
                return dates.as_date(value)
            return None
        if wanted == BOOL:
            return value if isinstance(value, bool) else None
        if wanted == TEXT:
            if not isinstance(value, str):
                return None
            if field_type == 'enum' and choices is not None:
                allowed = {c.get('value') if isinstance(c, dict) else c for c in choices}
                if value not in allowed:
                    return None
            return value
    except (decimal.InvalidOperation, ValueError, OverflowError):
        return None
    return None


def to_json_value(value):
    """A typed value as the sandbox's JSON row stores it."""
    if isinstance(value, decimal.Decimal):
        if value == value.to_integral_value() and value.as_tuple().exponent >= 0:
            return int(value)
        return float(value)
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    return value


# --------------------------------------------------------------------------- #
# Several expressions on one record
# --------------------------------------------------------------------------- #

def dependency_order(sources, strict=True):
    """The names of `{field: source}` in an order where every expression comes
    after the expressions it reads. Unparseable sources are left out; a cycle
    raises `expression_cycle`, naming the fields in it — or, with
    `strict=False`, is left out too, which is what a write path wants: the
    fields that can be computed still are, and the advisory names the rest."""
    deps = {}
    for name, source in sources.items():
        try:
            refs = compile(source).references
        except ExpressionError:
            continue
        if name in refs:
            if not strict:
                continue
            raise ExpressionError(
                'expression_cycle',
                f"`{name}` reads itself, so it can never be computed.")
        deps[name] = [r for r in refs if r in sources]
    order, done = [], set()
    pending = [n for n in sources if n in deps]
    while pending:
        progressed = False
        for name in list(pending):
            if all(d in done or d not in deps for d in deps[name]):
                order.append(name)
                done.add(name)
                pending.remove(name)
                progressed = True
        if not progressed:
            if not strict:
                break
            raise ExpressionError(
                'expression_cycle',
                f"These calculated fields read each other in a circle, so none of "
                f"them can be computed: {', '.join(sorted(pending))}.")
    return order
