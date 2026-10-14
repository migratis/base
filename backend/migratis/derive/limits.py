"""The ceilings a run is held to (SCOPE_calculated_tables.md §6.5).

A run is refused whole when it would cross one — never truncated, because a
calculated table holding the first 5 000 of 40 000 rows looks complete. Every
refusal names the step and the number. The host passes its own `Limits` (a
generated application reads them from settings); the engine imports no
settings, so these are the defaults, not the policy.
"""
import dataclasses


@dataclasses.dataclass(frozen=True)
class Limits:
    #: Rows read from one input slot.
    max_input_rows: int = 10000
    #: Rows produced by any one step — a join is where this bites.
    max_rows: int = 50000
    #: Rows the run may write; the file import's ceiling, for the same reason.
    max_write_rows: int = 5000
    #: Rows one input row may expand into (`recur`, `repeat`).
    max_expansion: int = 1000
    #: Seconds of wall time for the whole run.
    time_budget: float = 10.0


DEFAULT = Limits()
