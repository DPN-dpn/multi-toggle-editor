import bpy
from bpy.types import Operator
from bpy.props import StringProperty


class MTE_OT_import_ini(Operator):
    bl_idname = "mte.import_ini"
    bl_label = "INI 파일 선택"
    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(default="*.ini", options={"HIDDEN"})

    def execute(self, context):
        context.scene.mte_import_path = self.filepath
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


class MTE_OT_select_export_dir(Operator):
    bl_idname = "mte.select_export_dir"
    bl_label = "내보내기 경로 선택"
    filepath: StringProperty(subtype="DIR_PATH")

    def execute(self, context):
        context.scene.mte_export_path = self.filepath
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


classes = (MTE_OT_import_ini, MTE_OT_select_export_dir)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
