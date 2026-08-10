from django.apps import AppConfig


class RoutingConfig(AppConfig):
    """Road-following routes for `geo` fields in geo_mode='route'.

    The app is stateless — no models, no migrations. It holds one adapter to a
    self-hosted routing engine and the endpoint the map editor calls to turn
    waypoints into road geometry. Installing it cannot start the engine
    container (SCOPE_road_routing.md §10), which is why every path through it is
    written to degrade with a name rather than a straight line.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'migratis.routing'
