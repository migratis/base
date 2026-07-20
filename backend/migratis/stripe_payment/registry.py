"""Handler registries for the unified Stripe billing engine.

Each *feature* (subscription, AI credits, …) registers its own callbacks — the
`stripe_payment` app never imports the features, so the dependency only ever
points feature → stripe_payment. Registration happens in each feature app's
``AppConfig.ready()``.

Two kinds of handler:

* **purpose handler** — keyed on the ``purpose`` metadata we stamp on every
  Checkout Session (e.g. ``ai_credits``, ``subscription``). Invoked once, from
  inside the idempotent grant (``services.grant_for_session``), when a
  ``checkout.session.completed`` event / redirect-return first applies a paid
  session. Signature: ``handler(user, session, payment) -> None``.

* **event handler** — keyed on a raw Stripe event type (e.g.
  ``customer.subscription.updated``). Invoked for lifecycle events that are not
  one-off grants. Signature: ``handler(event) -> None``. Multiple allowed.
"""

_PURPOSE_HANDLERS = {}
_EVENT_HANDLERS = {}
_CHECKOUT_BUILDERS = {}


def register_checkout_builder(purpose, builder):
    """Register how the unified ``POST /billing/checkout`` assembles a Checkout
    Session for ``purpose``. ``builder(request, user) -> (kwargs, error)`` where
    ``kwargs`` are passed to ``services.create_checkout_session`` (mode,
    line_items, success_url, cancel_url, metadata, subscription_data) and
    ``error`` is a ``formatErrors``-style dict or None."""
    _CHECKOUT_BUILDERS[purpose] = builder


def get_checkout_builder(purpose):
    return _CHECKOUT_BUILDERS.get(purpose)


def register_purpose(purpose, handler):
    _PURPOSE_HANDLERS[purpose] = handler


def get_purpose_handler(purpose):
    return _PURPOSE_HANDLERS.get(purpose)


def register_event(event_type, handler):
    _EVENT_HANDLERS.setdefault(event_type, []).append(handler)


def get_event_handlers(event_type):
    return list(_EVENT_HANDLERS.get(event_type, ()))
