from typing import List

from ninja import Schema
from pydantic import ConfigDict

from .services import DEFAULT_PROFILE


class SnapIn(Schema):
    """Waypoints to snap, in GeoJSON order ``[lng, lat]``.

    ``extra='forbid'`` for the same reason the agent-lane endpoints use it: a
    caller that misspells a key gets a 422 naming it rather than a silent no-op
    on a default. Nothing here identifies a record — snapping is an edit-time
    computation over coordinates and writes nothing.
    """
    model_config = ConfigDict(extra='forbid')

    waypoints: List[List[float]]
    profile: str = DEFAULT_PROFILE
