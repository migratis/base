"""Declarative billing-plugin abstraction over the raw handler ``registry``.

A *billing plugin* is everything one paying feature contributes to the shared
Stripe engine, as a single object:

* ``purpose`` — the metadata tag stamped on every Checkout Session it creates
  (``'subscription'``, ``'credits'``, …), routing the grant;
* ``checkout_builder`` — ``(request, user) -> (kwargs, error)`` for
  ``POST /billing/checkout``;
* ``grant_handler`` — ``(user, session, payment) -> None``, run once by the
  idempotent ledger (optional: a plugin may only listen to lifecycle events);
* ``events`` — ``{stripe_event_type: handler | [handlers]}`` lifecycle fan-out.

``register_plugin`` wires all of that down into ``registry`` (which the service /
webhook paths already read from — no behaviour change) *and* records the plugin
so the platform can enumerate what is installed (``installed_plugins``).

Dependency direction is unchanged: **feature → stripe_payment**. Each feature
calls ``register_plugin`` from its ``AppConfig.ready()``.

``module`` names the *generated-app* module this plugin backs (e.g. the generator
offers ``subscription`` / ``credits`` as installable modules). It is the source
of truth for the generator's Application-module picker via
``monetization_modules()`` — platform-only purposes leave it ``None`` so they
never surface as a selectable module (decision D6).
"""
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Union

from . import registry

_INSTALLED: Dict[str, "BillingPlugin"] = {}

# One handler, or a list of them, per event type.
EventMap = Dict[str, Union[Callable, List[Callable]]]


@dataclass(frozen=True, eq=False)
class BillingPlugin:
    purpose: str
    checkout_builder: Callable
    grant_handler: Optional[Callable] = None
    events: EventMap = field(default_factory=dict)
    label_key: str = ''
    module: Optional[str] = None


def register_plugin(plugin: BillingPlugin) -> BillingPlugin:
    """Wire ``plugin`` into the engine and record it as installed."""
    registry.register_checkout_builder(plugin.purpose, plugin.checkout_builder)
    if plugin.grant_handler is not None:
        registry.register_purpose(plugin.purpose, plugin.grant_handler)
    for event_type, handlers in (plugin.events or {}).items():
        if callable(handlers):
            handlers = [handlers]
        for handler in handlers:
            registry.register_event(event_type, handler)
    _INSTALLED[plugin.purpose] = plugin
    return plugin


def get_plugin(purpose: str) -> Optional[BillingPlugin]:
    return _INSTALLED.get(purpose)


def installed_plugins() -> List[BillingPlugin]:
    return list(_INSTALLED.values())


def monetization_modules() -> set:
    """Generated-app module names backed by an installed billing plugin.

    The generator's Application-module picker derives its monetization set from
    this, so adding a plugin that declares a ``module`` makes it selectable —
    and auto-pulls the ``stripe_payment`` engine — with no generator edit."""
    return {p.module for p in _INSTALLED.values() if p.module}
