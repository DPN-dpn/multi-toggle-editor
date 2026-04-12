from . import panel, operators


def register():
    operators.register()
    panel.register()


def unregister():
    panel.unregister()
    operators.unregister()
