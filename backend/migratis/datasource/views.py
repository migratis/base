"""The lookup endpoint a generated application serves.

SCOPE_external_data_sources.md@d2de531 §4.1 P6. The same body as the sandbox's
(`{candidates: [{label, id, values}]}`) from its own host with its own
credentials, and **the two never call each other** —
`SCOPE_routing_sandbox_external.md@c170e1a` D3′, one module over, unchanged:

> *the design sandbox calls a source through Migratis so a designer can try it;
> a generated app calls it from its own host with credentials its own operator
> installed, and nothing about its end users reaches Migratis.*

That is the one sentence that carries over from routing's privacy bullet, and
the one that matters most.

`auth=None` and **no authorizer by default**, which is base's posture and the
right one here: an installed app calls its owner's key against its owner's quota
and may let an anonymous role create records, so gating this would mean the
lookup works for the owner and silently does nothing for everyone else. A
deployment that wants a gate names one in `DATASOURCE_AUTHORIZER`.

Nothing is written, nothing is billed, and nothing here reaches an AI provider.
"""
import json
import logging

from django.http import JsonResponse
from ninja import Router

from . import access, registry, services, throttle

logger = logging.getLogger(__name__)

router = Router()


def _body(request):
    try:
        return json.loads(request.body)
    except (ValueError, AttributeError, TypeError):
        return None


def _resolve(request, key):
    """`(binding, adapter, error_response)`."""
    binding = registry.binding(key)
    if binding is None:
        return None, None, JsonResponse({'detail': 'datasource-not-declared'}, status=404)
    adapter = registry.adapter_for(binding)
    if adapter is None:
        return None, None, JsonResponse({'detail': 'datasource-not-declared'}, status=404)
    if not access.may_lookup(request, entity_name=binding.entity, source_key=key):
        return None, None, JsonResponse({'detail': 'forbidden'}, status=403)
    if not throttle.allow(request):
        # 429 rather than 503: the source is fine, this caller is not.
        return None, None, JsonResponse({'detail': 'datasource-rate-limited'}, status=429)
    return binding, adapter, None


def _failure(exc):
    """§8.4 — three outcomes, told apart. Never a silent empty list."""
    status = 502 if exc.key == services.REFUSED else 503
    body = {'detail': exc.key}
    if exc.status:
        body['source_status'] = exc.status
    return JsonResponse(body, status=status)


@router.post('/{key}/lookup', auth=None)
def lookup(request, key: str):
    """Candidate values for a form. **Nothing is written** — the ordinary create
    endpoint still writes the row, with every check it already runs."""
    binding, adapter, error = _resolve(request, key)
    if error is not None:
        return error
    payload = _body(request)
    if payload is None:
        return JsonResponse({'detail': 'invalid-json'}, status=422)
    query_text = (payload.get('q') or '').strip()
    if not query_text:
        # Never worth sending, and refused before the owner's meter moves.
        return JsonResponse({'candidates': [], 'source': key})
    try:
        candidates = services.search(
            adapter, binding, query_text,
            credential=registry.credential_for(adapter), application_id=key)
    except services.LookupError_ as exc:
        return _failure(exc)
    return JsonResponse({'candidates': candidates, 'source': key,
                         'needs_detail': bool(adapter.detail_path)})


@router.post('/{key}/lookup-detail', auth=None)
def lookup_detail(request, key: str):
    """The second request of the two-step flow, fired on the PICK (§4.2)."""
    binding, adapter, error = _resolve(request, key)
    if error is not None:
        return error
    payload = _body(request)
    if payload is None:
        return JsonResponse({'detail': 'invalid-json'}, status=422)
    external_id = str(payload.get('id') or '').strip()
    if not external_id:
        return JsonResponse({'detail': 'invalid-json'}, status=422)
    try:
        picked = services.detail(
            adapter, binding, external_id,
            credential=registry.credential_for(adapter), application_id=key)
    except services.LookupError_ as exc:
        return _failure(exc)
    return JsonResponse(picked)


@router.get('/availability', auth=None)
def availability(request):
    """Which sources this deployment can actually use, measured now.

    Not gated, and it is what lets a form decide whether to offer a button at
    all — closing it would hide the feature from the very page allowed to use
    it. It names the env vars still unset (`datasource_key_required`'s shape),
    and **never a key**.
    """
    return JsonResponse({
        'sources': [
            {'key': key, 'entity': b.entity, 'label': b.label,
             'fields': sorted((b.field_map or {}).keys())}
            for key, b in sorted(registry._load()['bindings'].items())
        ],
        'missing_credentials': registry.missing_credential_settings(),
    })
