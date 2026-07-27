from . import core
from . import global_toggles
from . import mesh_rules
from . import io
from . import updator

modules = [
    core,
    global_toggles,
    mesh_rules,
    io,
    updator,
]

def register():
    for mod in modules:
        if hasattr(mod, "register"):
            mod.register()

def unregister():
    for mod in reversed(modules):
        if hasattr(mod, "unregister"):
            mod.unregister()