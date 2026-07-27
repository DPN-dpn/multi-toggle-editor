import bpy
from bpy.types import Panel

class MULTI_TOGGLE_PT_io_panel(Panel):
    """N-Panel에 표시될 입출력 전용 패널 (가장 위)"""
    bl_label = "불러오기/내보내기"
    bl_idname = "MULTI_TOGGLE_PT_io_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = '멀티 토글'
    bl_order = 0
    
    def draw(self, context):
        layout = self.layout
        layout.operator("multi_toggle.import_ini", text="INI 불러오기", icon='IMPORT')
        layout.operator("multi_toggle.export_ini", text="INI 내보내기", icon='EXPORT')

classes = (
    MULTI_TOGGLE_PT_io_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
