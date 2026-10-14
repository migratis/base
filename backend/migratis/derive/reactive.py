"""The recalculation queue (SCOPE_calculated_tables.md §6.3, §6.4).

One queue, both hosts. A committed write calls `note` with the recalculations
it calls for; they run once the transaction commits (`transaction.on_commit`),
so **a run never breaks a write**. Writes made BY a run are appended one level
deeper and the queue is drained level by level, in each item's `rank` (its
place in the dependency order) — which is how a chain runs in order, and how a
loop cannot spin past `DERIVE_MAX_CHAIN_DEPTH`.

The drain is scheduled on every write, with no "already registered" flag: a
transaction that rolls back DISCARDS its callbacks, and a flag it had set would
silence every later write on that worker. The first drain after a commit
empties the whole queue, deduplicated by each item's `key` — an import of fifty
rows is one recalculation.
"""
import logging
import threading

from django.conf import settings
from django.db import transaction

logger = logging.getLogger(__name__)

_local = threading.local()


def _state():
    state = getattr(_local, 'state', None)
    if state is None:
        state = _local.state = {'queue': [], 'flushing': False, 'depth': 0}
    return state


def max_depth():
    return getattr(settings, 'DERIVE_MAX_CHAIN_DEPTH', 5)


def note(items):
    """Queue `items` — each `{'key': hashable, 'rank': number, 'run': callable}`."""
    if not items:
        return
    state = _state()
    depth = state['depth'] if state['flushing'] else 0
    for item in items:
        state['queue'].append(dict(item, depth=depth))
    if not state['flushing']:
        transaction.on_commit(flush)


def flush():
    state = _state()
    if state['flushing']:
        return
    state['flushing'] = True
    try:
        while state['queue']:
            batch, state['queue'] = state['queue'], []
            seen, todo = set(), []
            for item in batch:
                if item['key'] in seen:
                    continue
                seen.add(item['key'])
                todo.append(item)
            todo.sort(key=lambda i: (i['depth'], i.get('rank', 0)))
            for item in todo:
                if item['depth'] >= max_depth():
                    logger.warning('[DERIVE] chain depth %s reached; %s left stale',
                                   item['depth'], item['key'])
                    continue
                state['depth'] = item['depth'] + 1
                try:
                    item['run']()
                except Exception:                          # pragma: no cover
                    logger.exception('[DERIVE] reactive run %s failed', item['key'])
    finally:
        state['flushing'] = False
        state['depth'] = 0
