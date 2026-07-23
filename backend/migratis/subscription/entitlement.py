"""Phase 4 — entitlement seam (monetization-agnostic).

`@check_access()` historically asked "does this user have an active
subscription?" — hard-wired to the subscription model. As of 2026-07-22
subscription is **no longer an access gate** (owner): browsing/spec CRUD is free
for any logged-in user and the AI/approval endpoints self-protect by charging
credits. So the default gate is now **allow-all-authenticated**. The seam is kept
because a blocked request still needs a *machine-readable* reason (not an opaque
403), and a bespoke monetization model (pay-per-generation, per-app, metered) can
still slot in without touching an endpoint.

This module abstracts the gate behind a pluggable **provider**:

- `EntitlementProvider.check(request, action) -> EntitlementResult` decides
  access, optionally per `action` (e.g. only gate ``"generate"``).
- The active provider is resolved from ``settings.ENTITLEMENT_PROVIDER`` (a dotted
  path); absent that, the default `SubscriptionEntitlementProvider` allows any
  authenticated user.
- A different monetization model slots in by pointing the setting at a new
  provider — no endpoint changes.

`check_access()` (subscription/decorators.py) calls `check_entitlement()` and, on
a block, returns the `EntitlementResult.payload()` so the agent can branch on
`code`.
"""
from dataclasses import dataclass
from functools import lru_cache

from django.conf import settings
from django.utils.module_loading import import_string


@dataclass
class EntitlementResult:
    """Outcome of an entitlement check. `code` is a stable, machine-readable
    reason for a block (empty when allowed); `action` echoes the gated action."""
    allowed: bool
    code:    str = ""
    reason:  str = ""
    action:  str = ""

    def payload(self):
        return {
            "allowed": self.allowed,
            "code":    self.code,
            "reason":  self.reason,
            "action":  self.action,
        }


class EntitlementProvider:
    """Decides whether `request` is entitled to perform `action`. Subclass and
    point `settings.ENTITLEMENT_PROVIDER` at it to swap the monetization model."""

    def check(self, request, action=None) -> EntitlementResult:  # pragma: no cover
        raise NotImplementedError


class SubscriptionEntitlementProvider(EntitlementProvider):
    """Default provider — **allow-all-authenticated** (owner 2026-07-22).

    Subscription is no longer an *access* gate: browsing and spec CRUD are free
    for any logged-in user, and the AI/approval endpoints protect themselves
    independently by charging credits (or being subscription-covered). So the
    default gate only asks "is this an authenticated user?". Monetization moved
    entirely out of the access seam. The class name is kept so any
    `settings.ENTITLEMENT_PROVIDER` dotted path stays valid; a bespoke scheme can
    still swap the provider without touching an endpoint."""

    def check(self, request, action=None) -> EntitlementResult:
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            return EntitlementResult(allowed=True, action=action or "")
        return EntitlementResult(
            allowed=False,
            code="authentication_required",
            reason="Authentication is required to access this resource.",
            action=action or "",
        )


@lru_cache(maxsize=None)
def _load_provider(dotted_path):
    """Instantiate (and cache by path) the provider for a dotted path; empty
    path → the default subscription provider."""
    if not dotted_path:
        return SubscriptionEntitlementProvider()
    return import_string(dotted_path)()


def get_entitlement_provider():
    return _load_provider(getattr(settings, "ENTITLEMENT_PROVIDER", "") or "")


def check_entitlement(request, action=None) -> EntitlementResult:
    """Resolve the active provider and ask it whether `request` may perform
    `action`. The single entry point used by `check_access()`."""
    return get_entitlement_provider().check(request, action=action)
