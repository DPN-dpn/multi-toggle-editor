import bpy
from bpy.types import Panel

class MULTI_TOGGLE_PT_main_panel(Panel):
    """N-Panel에 표시될 메인 탭"""
    bl_label = "글로벌 토글 매니저"
    bl_idname = "MULTI_TOGGLE_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = '멀티 토글'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # 1. Live Preview 컨트롤러 (상단)
        box = layout.box()
        box.label(text="실시간 미리보기 조작", icon='RESTRICT_VIEW_OFF')
        
        row = box.row()
        row.prop(scene, "multi_toggle_live_preview", toggle=True, icon='RESTRICT_VIEW_OFF' if scene.multi_toggle_live_preview else 'RESTRICT_VIEW_ON')
        row.prop(scene, "multi_toggle_track_preview", toggle=True, icon='TRACKING')
        
        box.separator()
        
        if len(scene.multi_toggle_globals) == 0:
            box.label(text="정의된 글로벌 토글이 없습니다.")
        else:
            for item in scene.multi_toggle_globals:
                row = box.row()
                row.prop(item, "current_state", text=item.name)
                
        layout.separator()
        
        # 2. 글로벌 토글 매니저
        layout.label(text="토글 스위치 설정:", icon='PREFERENCES')
        
        row = layout.row()
        row.operator("multi_toggle.add_global", text="토글 추가", icon='ADD')
        row.operator("multi_toggle.clear_globals", text="모두 지우기", icon='X')

        for i, item in enumerate(scene.multi_toggle_globals):
            box = layout.box()
            row = box.row()
            row.prop(item, "name", text="")
            
            remove_op = row.operator("multi_toggle.remove_global", text="", icon='TRASH')
            remove_op.index = i
            
            row = box.row()
            row.prop(item, "hotkey", text="다음")
            cap_op = row.operator("multi_toggle.capture_key", text="", icon='RESTRICT_RENDER_OFF')
            cap_op.index = i
            cap_op.target_prop = "hotkey"
            
            row2 = box.row(align=True)
            row2.prop(item, "use_ctrl", toggle=True)
            row2.prop(item, "use_shift", toggle=True)
            row2.prop(item, "use_alt", toggle=True)
            
            row = box.row()
            row.prop(item, "back_key", text="이전")
            cap_op_back = row.operator("multi_toggle.capture_key", text="", icon='RESTRICT_RENDER_OFF')
            cap_op_back.index = i
            cap_op_back.target_prop = "back_key"
            
            row3 = box.row(align=True)
            row3.prop(item, "back_use_ctrl", toggle=True)
            row3.prop(item, "back_use_shift", toggle=True)
            row3.prop(item, "back_use_alt", toggle=True)
            
            row = box.row()
            row.prop(item, "max_states", text="상태 수")

classes = (
    MULTI_TOGGLE_PT_main_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
