"""The calculated tables' endpoints in a generated application (SCOPE_calculated_tables.md §9).

Mounted at `/derive` when the module is installed. The gate is the module's own
(`host.can_run`: the anchor's write floor, or anchorless, the target's), and so is
the read path a run reads through. Free: deterministic, no provider anywhere.
"""
import json

from django.http import JsonResponse
from ninja import Router

from . import runner

# `auth=None`: the gate is the MODULE's own (`host.can_run` / `host.can_read`,
# its role rules), exactly as its CRUD router's is. Inheriting the platform's
# session auth answered 401 to every caller of an application built without the
# user module — where nobody can sign in at all.
router = Router(auth=None)


@router.post('/{name}/run')
def run_derivation(request, name: str):
    decl = runner.declarations().get(name)
    if decl is None:
        return JsonResponse({'detail': 'not-found'}, status=404)
    if not runner._host(decl).can_run(decl, request.user):
        return JsonResponse({'detail': 'forbidden'}, status=403)
    try:
        body = json.loads(request.body) if request.body else {}
    except ValueError:
        return JsonResponse({'detail': 'invalid-json'}, status=422)
    try:
        result = runner.run(name, anchor_id=body.get('anchor_id'), user=request.user)
    except runner.DerivationRefused as exc:
        return JsonResponse({'detail': exc.detail()}, status=exc.status)
    result.update({'success': True, 'detail': [{'success': ['derivation-run-done']}]})
    return JsonResponse(result)


@router.get('/status/{module}')
def derivation_status(request, module: str):
    """What the calculated tab's strip shows — for the tables the requester may
    read, gated by the module's own read rule (`host.can_read`)."""
    return JsonResponse({'derived': runner.status(module, request.user)})
