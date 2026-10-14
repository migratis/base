"""Calendar arithmetic for `migratis.derive` (SCOPE_calculated_tables.md §5.2).

Pure and dependency-free, like the rest of the engine. One rule matters more
than the others: **months are anchored, never chained.** Occurrence *k* of a
monthly series that starts on 31 January is `add_months(start, k)` — 28
February, then **31 March** — never "one month after the previous one", which
drifts to the 28th and stays there for ever.
"""
import calendar
import datetime
import re

_ISO_DATE = re.compile(r'^(\d{4})-(\d{2})-(\d{2})')


def as_date(value):
    """The calendar date a stored value represents, or `None`.

    A `datetime` is read as its date: an expression reasons in days, and a time
    of day carried silently through `add_months` would be a precision nobody
    asked for. A string is read by its leading ISO date, which covers both
    `"2026-10-14"` and the `"2026-10-14T23:30:00Z"` a datetime field stores —
    and is read in the timezone it was written in, never converted.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        m = _ISO_DATE.match(value.strip())
        if not m:
            return None
        try:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    return None


def add_days(d, n):
    return d + datetime.timedelta(days=n)


def add_months(d, n):
    """`d` moved by `n` months, the day clamped to the target month's length."""
    index = d.year * 12 + (d.month - 1) + n
    year, month = divmod(index, 12)
    month += 1
    if not 1 <= year <= 9999:
        raise OverflowError('date out of range')
    last = calendar.monthrange(year, month)[1]
    return datetime.date(year, month, min(d.day, last))


def add_years(d, n):
    return add_months(d, 12 * n)


def days_between(a, b):
    """Days from `a` to `b` — negative when `b` is earlier."""
    return (b - a).days


def months_between(a, b):
    """Whole months from `a` to `b`: the largest `m` with `add_months(a, m) <= b`
    (or, going backwards, the smallest with `add_months(a, m) >= b`)."""
    m = (b.year - a.year) * 12 + (b.month - a.month)
    if m > 0 and add_months(a, m) > b:
        m -= 1
    elif m < 0 and add_months(a, m) < b:
        m += 1
    return m


def week_start(d):
    """The Monday of `d`'s ISO week."""
    return d - datetime.timedelta(days=d.weekday())


def month_start(d):
    return d.replace(day=1)


def quarter_start(d):
    return datetime.date(d.year, 3 * ((d.month - 1) // 3) + 1, 1)


def year_start(d):
    return datetime.date(d.year, 1, 1)
