"""Calculated values and, later, calculated tables (SCOPE_calculated_tables.md).

The runtime half of the feature, and deliberately the smaller one: every
declaration lives in `generator`, and this module must never import it. It is
mirrored verbatim into base, so the sandbox and every generated application
evaluate an expression with the same file.

P0 shipped the expression language (`expr.py`, `dates.py`), used by
`Field.computed_kind = 'expression'`. P1 adds the engine — `engine.py` (the
gate and the nine operators), `limits.py`, and `seed_transforms.json`, whose
examples are the engine's test suite — pure: no Django, no network. P2 adds
the one model this module owns, the run log (`models.DerivationRun`, D9),
string-keyed so both hosts write the same shape without importing `generator`.
P5 adds what a generated application runs: `sets.py` and `reactive.py` (shared
with the design sandbox), `runner.py` (driven by each module's
`derivations.json`), `views.py` (`/derive/<name>/run`, `/derive/status/<module>`)
and `manage.py run_derivations --due`.
"""
