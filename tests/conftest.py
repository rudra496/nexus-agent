"""Pytest global configuration and compatibility shims."""
import sys
import typing

# Polyfill NotRequired for Python 3.10 environments
if sys.version_info < (3, 11):
    try:
        import typing_extensions
        if not hasattr(typing, "NotRequired"):
            typing.NotRequired = typing_extensions.NotRequired
    except ImportError:
        pass
