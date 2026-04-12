import bpy
from bpy.types import Panel


def _get_foldout_icon(is_expanded):
    return "TRIA_DOWN" if is_expanded else "TRIA_RIGHT"


class PT_EDITOR(Panel):
    bl_label = "멀티 토글 에디터"
    bl_idname = "MTE_PT_editor"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "멀티 토글"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        col = layout.column(align=True)

        row_path = col.row(align=True)
        row_path.prop(
            scene,
            "mte_show_paths",
            icon=_get_foldout_icon(scene.mte_show_paths),
            emboss=False,
            text="경로 설정",
        )
        if scene.mte_show_paths:
            box_path = col.box()
            row_path = box_path.row(align=True)
            row_path.enabled = False
            row_path.prop(scene, "mte_import_path", text="불러오기")
            row_path.enabled = True
            row_path.operator("mte.import_ini", text="", icon="FILE")

            row_path = box_path.row(align=True)
            row_path.enabled = False
            row_path.prop(scene, "mte_export_path", text="내보내기")
            row_path.enabled = True
            row_path.operator("mte.select_export_dir", text="", icon="FILE_FOLDER")

        row_key = col.row(align=True)
        row_key.prop(
            scene,
            "mte_show_keys",
            icon=_get_foldout_icon(scene.mte_show_keys),
            emboss=False,
            text="키 설정",
        )
        if scene.mte_show_keys:
            box_key = col.box()
            row_key = box_key.row(align=True)
            


def register():
    bpy.utils.register_class(PT_EDITOR)


def unregister():
    bpy.utils.unregister_class(PT_EDITOR)
