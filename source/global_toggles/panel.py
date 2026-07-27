import bpy
from bpy.types import Panel

class MULTI_TOGGLE_PT_main_panel(Panel):
    """N-Panel에 표시될 메인 탭"""
    bl_label = "토글 매니저"
    bl_idname = "MULTI_TOGGLE_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = '멀티 토글'
    bl_order = 1
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # 1. Live Preview 컨트롤러 (상단)
        box = layout.box()
        box.label(text="실시간 미리보기 조작", icon='RESTRICT_VIEW_OFF')
        
        box.prop(scene, "multi_toggle_live_preview", toggle=True, icon='RESTRICT_VIEW_OFF' if scene.multi_toggle_live_preview else 'RESTRICT_VIEW_ON')
        box.prop(scene, "multi_toggle_track_preview", toggle=True, icon='TRACKING')
        
        box.separator()
        
        if len(scene.multi_toggle_globals) == 0:
            box.label(text="정의된 글로벌 토글이 없습니다.")
        else:
            for item in scene.multi_toggle_globals:
                row = box.row()
                row.prop(item, "current_state", text=item.name)
                
        layout.separator()
        
        # 2. 글로벌 토글 매니저
        row = layout.row()
        icon = 'TRIA_DOWN' if scene.multi_toggle_show_globals else 'TRIA_RIGHT'
        row.prop(scene, "multi_toggle_show_globals", text="", icon=icon, emboss=False)
        row.label(text="토글 키", icon='PREFERENCES')
        
        if scene.multi_toggle_show_globals:
            row = layout.row()
            row.operator("multi_toggle.add_global", text="토글 추가", icon='ADD')
            row.operator("multi_toggle.clear_globals", text="모두 지우기", icon='X')
            
            if len(scene.multi_toggle_globals) > 0:
                row = layout.row()
                row.operator("multi_toggle.expand_all_globals", text="모두 펼치기", icon='DOWNARROW_HLT')
                row.operator("multi_toggle.collapse_all_globals", text="모두 접기", icon='RIGHTARROW')
    
            for i, item in enumerate(scene.multi_toggle_globals):
                box = layout.box()
                row = box.row()
                
                # 접기/펼치기 버튼
                icon = 'TRIA_DOWN' if item.is_expanded else 'TRIA_RIGHT'
                row.prop(item, "is_expanded", text="", icon=icon, emboss=False)
                
                row.prop(item, "name", text="")
                
                if not item.is_expanded:
                    row.prop(item, "max_states")
                    
                remove_op = row.operator("multi_toggle.remove_global", text="", icon='TRASH')
                remove_op.index = i
                
                if item.is_expanded:
                    row = box.row()
                    row.prop(item, "hotkey", text="다음")
                    cap_op = row.operator("multi_toggle.capture_key", text="", icon='RESTRICT_RENDER_OFF')
                    cap_op.index = i
                    cap_op.target_prop = "hotkey"
                    
                    row2 = box.row(align=True)
                    
                    def draw_mod(layout, index, prop_name, display_name):
                        val = getattr(item, prop_name)
                        if val == 'NONE':
                            op = layout.operator("multi_toggle.cycle_modifier", text=display_name, depress=False)
                        elif val == 'POS':
                            op = layout.operator("multi_toggle.cycle_modifier", text=f"+ {display_name}", depress=True)
                        else:
                            op = layout.operator("multi_toggle.cycle_modifier", text=f"- {display_name}", depress=True)
                        op.index = index
                        op.prop_name = prop_name
                        
                    draw_mod(row2, i, "use_ctrl", "Ctrl")
                    draw_mod(row2, i, "use_shift", "Shift")
                    draw_mod(row2, i, "use_alt", "Alt")
                    
                    row = box.row()
                    row.prop(item, "back_key", text="이전")
                    cap_op_back = row.operator("multi_toggle.capture_key", text="", icon='RESTRICT_RENDER_OFF')
                    cap_op_back.index = i
                    cap_op_back.target_prop = "back_key"
                    
                    row3 = box.row(align=True)
                    draw_mod(row3, i, "back_use_ctrl", "Ctrl")
                    draw_mod(row3, i, "back_use_shift", "Shift")
                    draw_mod(row3, i, "back_use_alt", "Alt")
                    
                    row = box.row()
                    row.prop(item, "max_states")

classes = (
    MULTI_TOGGLE_PT_main_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
