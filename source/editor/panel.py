import bpy
from bpy.types import Panel


class PT_EDITOR(Panel):
    bl_label = "에디터"
    bl_idname = "MTE_PT_editor"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "멀티 토글"

    def draw(self, context):
        layout = self.layout


def register():
    bpy.utils.register_class(PT_EDITOR)


def unregister():
    bpy.utils.unregister_class(PT_EDITOR)
