"""Legacy alias: dependencies.auth -> utils.dependencies."""
from utils.dependencies import *  # noqa: F401,F403
from utils.dependencies import get_current_user, get_current_user_optional  # noqa: F401

get_optional_user = get_current_user_optional

