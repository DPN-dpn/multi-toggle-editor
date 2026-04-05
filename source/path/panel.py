import bpy
from bpy.types import Panel


class PT_PATH(Panel):
    bl_label = "경로 설정"
    bl_idname = "MTE_PT_path"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "멀티 토글"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        col = layout.column(align=True)

        row = col.row(align=True)
        row.enabled = False
        row.prop(scene, "mte_import_path", text="불러오기")
        row.enabled = True
        row.operator("mte.import_ini", text="", icon="FILE")

        row = col.row(align=True)
        row.enabled = False
        row.prop(scene, "mte_export_path", text="내보내기")
        row.enabled = True
        row.operator("mte.select_export_dir", text="", icon="FILE_FOLDER")


def register():
    bpy.utils.register_class(PT_PATH)


def unregister():
    bpy.utils.unregister_class(PT_PATH)
