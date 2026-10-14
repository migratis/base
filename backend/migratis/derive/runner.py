"""Calculated tables in a GENERATED application (SCOPE_calculated_tables.md §9, P5).

The generated application has no `Derivation` table — every declaration lives
in `generator`, and this module must never import it. So the declarations
arrive as data: each installed module ships `derivations.json`, listed in
`settings.DERIVE_DECLARATIONS`, naming the module's **host** — an emitted
`derive_host.py` that knows the module's models and reads and writes through
the module's own list path and `perform_*` functions. Everything that is not
about the module's models is here, once, and what a run MEANS is in
`derive.sets`, shared with the design sandbox:

    run(name, anchor_id, user)         a run, refused whole or not at all
    note_write(module, entity, ...)    on_input_write, via derive.reactive
    run_due()                          the schedule (`run_derivations --due`)
    status(module)                     the calculated tab's strip

A host module provides: `anchor_record`, `set_owner`, `read`, `existing`,
`create`, `update`, `delete`, `drop_anchor`, `anchors_owned_by`,
`all_anchors`, `latest_change`, `can_read`, `can_run`, `user_by_id` and
`WriteRefused`.
"""
import datetime
import functools
import importlib
import json
import logging
import os

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from . import engine, expr, reactive, sets
from .limits import Limits
from .models import DerivationRun

logger = logging.getLogger(__name__)

SCHEDULE_DAYS = {'daily': 1, 'weekly': 7}


class DerivationRefused(Exception):
    def __init__(self, code, message, *, step=None, status=422):
        super().__init__(message)
        self.code = code
        self.message = message
        self.step = step
        self.status = status
        self.logged = False

    def detail(self):
        loc = ['derivation'] + ([self.step] if self.step else [])
        return [{'loc': loc, 'code': self.code, 'msg': self.message}]


def configured_limits():
    base = Limits()
    return Limits(
        max_input_rows=getattr(settings, 'DERIVE_MAX_INPUT_ROWS', base.max_input_rows),
        max_rows=getattr(settings, 'DERIVE_MAX_ROWS', base.max_rows),
        max_write_rows=getattr(settings, 'DERIVE_MAX_WRITE_ROWS', base.max_write_rows),
        max_expansion=getattr(settings, 'DERIVE_MAX_EXPANSION', base.max_expansion),
        time_budget=getattr(settings, 'DERIVE_TIME_BUDGET', base.time_budget),
    )


# --------------------------------------------------------------------------- #
# Declarations
# --------------------------------------------------------------------------- #

_files = {}


def _load(path):
    path = str(path)
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        logger.warning('[DERIVE] declarations file %s is missing', path)
        return {}
    cached = _files.get(path)
    if cached and cached[0] == mtime:
        return cached[1]
    with open(path, encoding='utf-8') as fh:
        doc = json.load(fh)
    _files[path] = (mtime, doc)
    return doc


def declarations():
    """`{name: declaration}` over every installed module. A declaration carries
    its module's `module` and `host` (the dotted path of its derive_host)."""
    out = {}
    for item in getattr(settings, 'DERIVE_DECLARATIONS', None) or []:
        doc = item if isinstance(item, dict) else _load(item)
        for d in doc.get('derivations') or []:
            out[d['name']] = dict(d, module=doc.get('module', ''), host=doc.get('host', ''))
    return out


def _host(decl):
    return importlib.import_module(decl['host'])


def _plan(decl):
    return engine.check(decl['transform'])


def _log(decl, anchor_id, runner, trigger, as_of, status, *, error=None,
         result=None, diff=None, total=0):
    return DerivationRun.objects.create(
        application_key=decl['module'], derivation_key=decl['name'],
        anchor_key='' if anchor_id is None else str(anchor_id),
        host='app', trigger=trigger, runner=str(runner or 'system')[:120],
        as_of=as_of, status=status,
        error_code=getattr(error, 'code', '') or '',
        error=getattr(error, 'message', '') or '',
        step_counts=result.counts if result is not None else {},
        skipped=result.skipped if result is not None else {},
        created=(diff or {}).get('created', 0), updated=(diff or {}).get('updated', 0),
        deleted=(diff or {}).get('deleted', 0), total=total,
        finished_at=timezone.now())


# --------------------------------------------------------------------------- #
# A run
# --------------------------------------------------------------------------- #

def run(name, anchor_id=None, user=None, trigger='manual', dry_run=False,
        as_of=None, limits=None):
    """Run one calculated table for one anchor (or its anchorless set).

    `user` is who pressed the button; `None` is the system (a reactive or a
    scheduled run), which looks anchors up unscoped and still reads and writes
    as the owner of the set.
    """
    decl = declarations().get(name)
    if decl is None:
        raise DerivationRefused('derivation_unknown', f'No calculated table {name!r}.',
                                status=404)
    host = _host(decl)
    try:
        plan = _plan(decl)
    except engine.TransformError as exc:                       # pragma: no cover
        raise DerivationRefused('derivation_transform_invalid', str(exc))
    lim = limits or configured_limits()

    anchor_obj, anchor_data = None, {}
    if decl.get('anchor'):
        if anchor_id in (None, ''):
            raise DerivationRefused('derivation_anchor_required',
                                    f"This calculation runs for one {decl['anchor']}; say which.")
        found = host.anchor_record(decl, anchor_id, user)
        if found is None:
            raise DerivationRefused('derivation_anchor_not_found',
                                    f"No {decl['anchor']} {anchor_id} that you can see.",
                                    status=404)
        anchor_obj, anchor_data = found
    anchor_key = anchor_obj.pk if anchor_obj is not None else None
    owner = host.set_owner(decl, anchor_obj, user)

    as_of = as_of or timezone.localdate()
    inputs = {inp['slot']: host.read(decl, inp, owner, anchor_key, lim.max_input_rows + 1)
              for inp in decl.get('inputs') or []}
    params = sets.bound_params(decl.get('params_map'), anchor_data)
    try:
        result = engine.run(plan, inputs, params, as_of=as_of, limits=lim)
    except engine.RunError as exc:
        refused = DerivationRefused(exc.code, exc.message, step=exc.step)
        if not dry_run:
            _log(decl, anchor_key, user, trigger, as_of, 'failed', error=exc)
            refused.logged = True
        raise refused

    output_map = decl.get('output_map') or {}
    anchor_fk = decl.get('anchor_fk') or ''
    new_rows = [sets.to_target_row(r, output_map, decl.get('target_fields') or {},
                                   anchor_fk, anchor_key) for r in result.rows]
    key_fields = [output_map[c] for c in plan.key]
    mapped = list(output_map.values())
    existing = host.existing(decl, owner, anchor_key, mapped)
    plan_ = sets.diff_sets(new_rows, existing, key_fields, mapped, decl['mode'])
    diff = {'created': len(plan_['creates']), 'updated': len(plan_['updates']),
            'deleted': len(plan_['deletes']), 'unchanged': plan_['unchanged']}
    total = (len(new_rows) if decl['mode'] == 'replace'
             else len(existing) + len(plan_['creates']))
    payload = {
        'status': 'ok', 'dry_run': dry_run, 'rows': new_rows, 'diff': diff,
        'trace': result.counts, 'skipped': result.skipped, 'as_of': as_of.isoformat(),
        'params': {k: expr.to_json_value(v) for k, v in result.params.items()},
        'run_id': None,
    }
    if dry_run:
        return payload
    try:
        with transaction.atomic():
            for handle, data in plan_['updates']:
                host.update(decl, handle, data, owner)
            for data in plan_['creates']:
                host.create(decl, data, owner)
            for handle in plan_['deletes']:
                host.delete(decl, handle)
    except host.WriteRefused as exc:
        refused = DerivationRefused(
            'derivation_write_refused',
            f"{decl['target']} refused a calculated row ({exc}); nothing was written "
            f"and the previous rows are untouched.")
        _log(decl, anchor_key, user, trigger, as_of, 'failed', error=refused, result=result)
        refused.logged = True
        raise refused
    payload['run_id'] = _log(decl, anchor_key, user, trigger, as_of, 'ok',
                             result=result, diff=diff, total=total).id
    return payload


# --------------------------------------------------------------------------- #
# on_input_write (§6.3) and chains (§6.4)
# --------------------------------------------------------------------------- #

def _ranks(decls):
    writers = {}
    for d in decls:
        writers.setdefault(d['target'], []).append(d['name'])
    reads = {d['name']: {i['entity'] for i in d.get('inputs') or []} for d in decls}
    rank = {d['name']: 0 for d in decls}
    for _ in range(len(decls)):
        changed = False
        for d in decls:
            best = max((rank[w] + 1 for e in reads[d['name']] for w in writers.get(e, ())
                        if w != d['name']), default=0)
            if best > rank[d['name']]:
                rank[d['name']] = min(best, len(decls))
                changed = True
        if not changed:
            break
    return rank


def _affected(decls, entity, record_id, old, new, owner_id):
    out = []
    for d in decls:
        if 'on_input_write' not in (d.get('triggers') or []):
            continue
        if d.get('anchor') == entity and record_id:
            out.append((d, record_id, None, 'drop' if new is None else 'run'))
        for inp in d.get('inputs') or []:
            if inp['entity'] != entity:
                continue
            if not d.get('anchor'):
                out.append((d, None, owner_id, 'run'))
            elif inp.get('scope_fk'):
                for data in (old, new):
                    value = (data or {}).get(inp['scope_fk'])
                    if value not in (None, ''):
                        out.append((d, value, None, 'run'))
            elif owner_id is not None:
                limit = getattr(settings, 'DERIVE_MAX_REACTIVE_ANCHORS', 20)
                ids = _host(d).anchors_owned_by(d, owner_id, limit + 1)
                if len(ids) <= limit:
                    out.extend((d, i, None, 'run') for i in ids)
            # An unscoped SHARED input is never fanned out (D6): stale instead.
    return out


def note_write(module, entity, record_id, old, new, owner_id=None):
    """Called by a module's `perform_*` after every write. Never raises."""
    try:
        decls = [d for d in declarations().values() if d['module'] == module]
        affected = _affected(decls, entity, record_id, old, new, owner_id) if decls else []
        ranks = _ranks(decls) if affected else {}
    except Exception:                                          # pragma: no cover
        logger.exception('[DERIVE] could not work out what %s affects', entity)
        return
    reactive.note([{
        'key': ('app', d['name'], anchor_id, owner_id_, action),
        'rank': ranks.get(d['name'], 0),
        'run': functools.partial(_run_reactive, d['name'], anchor_id, owner_id_, action),
    } for d, anchor_id, owner_id_, action in affected])


def _run_reactive(name, anchor_id, owner_id, action, trigger='on_input_write'):
    decl = declarations().get(name)
    if decl is None:
        return
    host = _host(decl)
    if action == 'drop':
        if decl['mode'] == 'replace':
            with transaction.atomic():
                host.drop_anchor(decl, anchor_id)
        return
    user = host.user_by_id(owner_id) if owner_id is not None else None
    try:
        run(name, anchor_id=anchor_id, user=user, trigger=trigger)
    except DerivationRefused as exc:
        if exc.code == 'derivation_anchor_not_found' or exc.logged:
            return
        _log(decl, anchor_id, user, trigger, timezone.localdate(), 'failed', error=exc)


# --------------------------------------------------------------------------- #
# The schedule (§6.3) — `run_derivations --due`, from CRONJOBS
# --------------------------------------------------------------------------- #

def is_due(schedule, last_as_of, today):
    """Whether a set last calculated `as_of` `last_as_of` is due today."""
    if last_as_of is None:
        return True
    if schedule == 'monthly':
        from .dates import add_months
        return add_months(last_as_of, 1) <= today
    days = SCHEDULE_DAYS.get(schedule)
    return days is not None and last_as_of + datetime.timedelta(days=days) <= today


def run_due(today=None):
    """Run every scheduled set whose period has elapsed. Returns the count run."""
    today = today or timezone.localdate()
    count = 0
    for decl in declarations().values():
        if 'schedule' not in (decl.get('triggers') or []):
            continue
        host = _host(decl)
        anchors = host.all_anchors(decl) if decl.get('anchor') else [None]
        for anchor_id in anchors:
            last = DerivationRun.last(decl['module'], decl['name'],
                                      '' if anchor_id is None else anchor_id, status='ok')
            if not is_due(decl.get('schedule'), last.as_of if last else None, today):
                continue
            try:
                run(decl['name'], anchor_id=anchor_id, trigger='schedule', as_of=today)
                count += 1
            except DerivationRefused as exc:
                if not exc.logged:
                    _log(decl, anchor_id, None, 'schedule', today, 'failed', error=exc)
    return count


# --------------------------------------------------------------------------- #
# The strip (§6.6)
# --------------------------------------------------------------------------- #

def status(module, user):
    """`{target model: info}` — the sandbox's `derived_info` shape, so the one
    strip component reads both. Only the tables `user` may read are listed: a
    run's time, size and refusal are facts about a table, and they are shown
    to whoever its list is shown to, nobody else."""
    from django.db.models import Max
    out = {}
    for decl in declarations().values():
        if decl['module'] != module:
            continue
        host = _host(decl)
        if not host.can_read(decl, user):
            continue
        last = DerivationRun.last(module, decl['name'])
        per_anchor = (DerivationRun.objects
                      .filter(application_key=module, derivation_key=decl['name'], status='ok')
                      .values('anchor_key').annotate(at=Max('started_at')))
        if decl.get('anchor'):
            alive = {str(i) for i in host.all_anchors(decl)}
            per_anchor = [r for r in per_anchor if r['anchor_key'] in alive]
        times = [r['at'] for r in per_anchor]
        latest = host.latest_change(decl)
        out[decl['target']] = {
            'derivation_id': decl['name'], 'label': decl.get('label', ''),
            'mode': decl['mode'], 'anchored': bool(decl.get('anchor')),
            'anchor_entity': decl.get('anchor') or '',
            'last_run': None if last is None else {
                'at': last.started_at.isoformat(), 'status': last.status,
                'rows': last.total, 'error_code': last.error_code, 'error': last.error},
            'stale': bool(times and latest and latest > min(times)),
        }
    return out
