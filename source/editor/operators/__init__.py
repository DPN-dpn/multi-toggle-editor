from . import path_selector, key_setter


def register():
    path_selector.register()
    key_setter.register()


def unregister():
    key_setter.unregister()
    path_selector.unregister()
