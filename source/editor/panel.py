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

        path_row = col.row(align=True)
        path_row.prop(
            scene,
            "mte_show_paths",
            icon=_get_foldout_icon(scene.mte_show_paths),
            emboss=False,
            text="경로 설정",
        )
        if scene.mte_show_paths:
            path_box = col.box()
            path_row = path_box.row(align=True)
            path_row.enabled = False
            path_row.prop(scene, "mte_import_path", text="불러오기")
            path_row.enabled = True
            path_row.operator("mte.import_ini", text="", icon="FILE")

            path_row = path_box.row(align=True)
            path_row.enabled = False
            path_row.prop(scene, "mte_export_path", text="내보내기")
            path_row.enabled = True
            path_row.operator("mte.select_export_dir", text="", icon="FILE_FOLDER")

        key_row = col.row(align=True)
        key_row.prop(
            scene,
            "mte_show_keys",
            icon=_get_foldout_icon(scene.mte_show_keys),
            emboss=False,
            text="키 설정",
        )
        if scene.mte_show_keys:
            key_box = col.box()

            key_row_content = key_box.row()

            key_row_list = key_row_content.row()
            key_row_list.template_list(
                "UI_UL_list",
                "mte_keys",
                scene,
                "mte_keys",
                scene,
                "mte_keys_index",
                rows=3,
            )

            key_row_toolbar = key_row_content.column(align=True)
            key_row_toolbar.operator("mte.add_key", text="", icon="ADD")
            key_row_toolbar.operator("mte.remove_key", text="", icon="REMOVE")
            key_row_toolbar.operator("mte.up_key", text="", icon="TRIA_UP")
            key_row_toolbar.operator("mte.down_key", text="", icon="TRIA_DOWN")

            if len(scene.mte_keys) > 0:
                item = scene.mte_keys[scene.mte_keys_index]
                key_col_edit = key_box.column(align=True)

                # 이름
                key_col_edit.prop(item, "name", text="이름")

                # 긍정 키
                key_row_edit_pos_key = key_col_edit.row(align=True)
                key_row_edit_pos_key.prop(item, "poskey", text="긍정 키")
                key_row_edit_pos_key.operator(
                    "mte.positive_key_capture", text="", icon="RESTRICT_RENDER_OFF"
                ).target = "poskey"

                # 부정 키
                key_row_edit_neg_key = key_col_edit.row(align=True)
                key_row_edit_neg_key.prop(item, "negkey", text="부정 키")
                key_row_edit_neg_key.operator(
                    "mte.negative_key_capture", text="", icon="RESTRICT_RENDER_OFF"
                ).target = "negkey"

                # 타입
                key_col_edit.prop(item, "type", text="타입")
                if getattr(item, "type", None) == "CYCLE":
                    key_col_edit.prop(item, "warp", text="워프")

                # 단계
                key_col_edit.prop(item, "num", text="단계 수")

        preset_row = col.row(align=True)
        preset_row.prop(
            scene,
            "mte_show_presets",
            icon=_get_foldout_icon(scene.mte_show_presets),
            emboss=False,
            text="프리셋 설정",
        )
        if scene.mte_show_presets:
            preset_box = col.box()


def register():
    bpy.utils.register_class(PT_EDITOR)


def unregister():
    bpy.utils.unregister_class(PT_EDITOR)
