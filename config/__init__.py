# Configuration package for fastapi_users_auth module

from .auth_config import (
    get_auth_config,
    get_testing_config,
    get_development_config,
    get_production_config,
    get_custom_config,
    get_config_for_environment
)

__all__ = [
    "get_auth_config",
    "get_testing_config",
    "get_production_config",
    "get_development_config",
    "get_custom_config",
    "get_config_for_environment"
]
