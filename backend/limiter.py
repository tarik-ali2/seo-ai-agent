"""
Shared slowapi rate limiter instance.
Import this single instance into main.py and all routers — do not create new instances.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Key: client IP address.
# For user-scoped limits on authenticated routes, use DB-count checks instead.
limiter = Limiter(key_func=get_remote_address)
