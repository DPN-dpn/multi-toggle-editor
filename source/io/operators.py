import os
import bpy
from bpy.props import StringProperty
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper, ExportHelper

from .functions.import_ini import process_import_mod_ini
from .functions.export_ini import process_export_mod_ini

class MULTI_TOGGLE_OT_import_ini(Operator, ImportHelper):
    """INI 파일에서 토글 설정을 불러옵니다"""
    bl_idname = "multi_toggle.import_ini"
    bl_label = "INI 토글 세팅 불러오기"
    
    filename_ext = ".ini"
    filter_glob: StringProperty(
        default="*.ini",
        options={'HIDDEN'},
        maxlen=255,
    )
    
    def execute(self, context):
        process_import_mod_ini(self.filepath, context)
        self.report({'INFO'}, f"성공적으로 불러왔습니다: {os.path.basename(self.filepath)}")
        return {'FINISHED'}

class MULTI_TOGGLE_OT_export_ini(Operator, ExportHelper):
    """INI 파일을 읽어와 토글 설정을 추가하여 덮어씁니다"""
    bl_idname = "multi_toggle.export_ini"
    bl_label = "INI 덮어쓰기 (내보내기)"
    
    filename_ext = ".ini"
    filter_glob: StringProperty(
        default="*.ini",
        options={'HIDDEN'},
        maxlen=255,
    )
    
    def execute(self, context):
        process_export_mod_ini(self.filepath, context.scene.multi_toggle_globals, context.scene.objects)
        self.report({'INFO'}, f"성공적으로 내보냈습니다: {os.path.basename(self.filepath)}")
        return {'FINISHED'}

classes = (
    MULTI_TOGGLE_OT_import_ini,
    MULTI_TOGGLE_OT_export_ini,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
