# Back-compat shim. The access-control decorator now lives in the neutral
# migratis.api.decorators module so it no longer ties every caller to the
# subscription app. Existing imports (migratis.subscription.decorators import
# check_access) keep working through this re-export.
from migratis.api.decorators import check_access, test_access

__all__ = ['check_access', 'test_access']
