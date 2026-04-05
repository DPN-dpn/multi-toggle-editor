import bpy
from bpy.props import StringProperty, BoolProperty


def addon_module_name():
    # Use the top-level package/module name so bl_idname matches the addon module
    try:
        return __name__.split(".")[0]
    except Exception:
        return __name__


class EVBHPreferences(bpy.types.AddonPreferences):
    bl_idname = addon_module_name()

    def draw(self, context):
        layout = self.layout


classes = (EVBHPreferences,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
