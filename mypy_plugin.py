"""
We extend attrs to support our configuration classes and fields.

To make mypy happy we need to register these wrapped versions of the `attr` functions,
so that the type checker knows about them.

Without this the `env_field` function would not correctly type check the return value.

See Also
--------
- https://www.attrs.org/en/stable/extending.html#mypy
"""

from mypy.plugin import Plugin
from mypy.plugins.attrs import (
    attr_attrib_makers,
    attr_class_makers,
)

# This works just like `attr.s`.
attr_class_makers.add("cmip_ref._config_helpers.config")

# These are our `attr.ib` makers.
attr_attrib_makers.add("cmip_ref._config_helpers.env_field")


class MyPlugin(Plugin):  # noqa
    # Our plugin does nothing, but it has to exist so this file gets loaded.
    pass


def plugin(version):  # noqa
    return MyPlugin
