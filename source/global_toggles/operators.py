import bpy
from bpy.types import Operator
from bpy.props import IntProperty, StringProperty
from ..core.live_preview import update_visibility

class MULTI_TOGGLE_OT_add_global(Operator):
    """새로운 글로벌 토글을 추가합니다"""
    bl_idname = "multi_toggle.add_global"
    bl_label = "글로벌 토글 추가"
    
    def execute(self, context):
        item = context.scene.multi_toggle_globals.add()
        item.name = f"토글 {len(context.scene.multi_toggle_globals)}"
        update_visibility(None, context)
        return {'FINISHED'}

class MULTI_TOGGLE_OT_remove_global(Operator):
    """선택한 글로벌 토글을 삭제합니다"""
    bl_idname = "multi_toggle.remove_global"
    bl_label = "글로벌 토글 삭제"
    
    index: IntProperty()
    
    def execute(self, context):
        scene = context.scene
        scene.multi_toggle_globals.remove(self.index)
        
        # 연쇄 삭제 로직
        deleted_idx_str = str(self.index)
        for obj in scene.objects:
            if obj.type == 'MESH':
                rules = obj.multi_toggle_rules.conditions
                
                # 역순 순회하며 삭제를 위한 인덱스 수집, 및 살아남은 조건 인덱스 보정
                to_delete = []
                for i in range(len(rules)):
                    cond = rules[i]
                    if cond.type == 'CONDITION':
                        if cond.saved_toggle_index == self.index:
                            to_delete.append(i)
                        else:
                            if cond.saved_toggle_index > self.index:
                                cond.saved_toggle_index -= 1
                
                if to_delete:
                    for i in sorted(to_delete, reverse=True):
                        rules.remove(i)
                        
                    # 빈 괄호 자동 정리
                    while True:
                        found_empty = False
                        for i in range(len(rules)-1):
                            if rules[i].type == 'PAREN_OPEN' and rules[i+1].type == 'PAREN_CLOSE':
                                rules.remove(i+1)
                                rules.remove(i)
                                found_empty = True
                                break
                        if not found_empty:
                            break
                            
                    if len(rules) == 0:
                        obj.hide_viewport = False
                        obj.hide_set(False)
                        
        update_visibility(None, context)
        return {'FINISHED'}

class MULTI_TOGGLE_OT_clear_globals(Operator):
    """모든 글로벌 토글을 삭제합니다"""
    bl_idname = "multi_toggle.clear_globals"
    bl_label = "모든 토글 지우기"
    
    def execute(self, context):
        context.scene.multi_toggle_globals.clear()
        
        for obj in context.scene.objects:
            if obj.type == 'MESH':
                obj.multi_toggle_rules.conditions.clear()
                obj.hide_viewport = False
                obj.hide_set(False)
                
        update_visibility(None, context)
        return {'FINISHED'}

class MULTI_TOGGLE_OT_capture_key(Operator):
    """키보드 입력을 캡처하여 단축키로 설정합니다"""
    bl_idname = "multi_toggle.capture_key"
    bl_label = "키 캡처"
    
    index: IntProperty()
    target_prop: StringProperty()
    
    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        # 상단 헤더 텍스트 변경으로 사용자에게 알림
        if context.area:
            context.area.header_text_set("키보드 키를 누르세요... (취소: ESC)")
        return {'RUNNING_MODAL'}
        
    def modal(self, context, event):
        if event.value == 'PRESS':
            if context.area:
                context.area.header_text_set(None)
                
            if event.type == 'ESC':
                return {'CANCELLED'}
            
            # 모디파이어 키 단독 입력 무시
            if event.type in {'LEFT_SHIFT', 'RIGHT_SHIFT', 'LEFT_CTRL', 'RIGHT_CTRL', 'LEFT_ALT', 'RIGHT_ALT'}:
                return {'PASS_THROUGH'}
                
            # Blender Event Type을 3DMigoto 스타일로 간단히 매핑
            b_type = event.type
            vk_key = b_type
            
            mapping = {
                'UP_ARROW': 'VK_UP',
                'DOWN_ARROW': 'VK_DOWN',
                'LEFT_ARROW': 'VK_LEFT',
                'RIGHT_ARROW': 'VK_RIGHT',
                'SPACE': 'VK_SPACE',
            }
            if b_type in mapping:
                vk_key = mapping[b_type]
            elif b_type.startswith('NUMPAD_'):
                vk_key = 'VK_NUMPAD' + b_type.split('_')[1]
            elif len(b_type) == 1 and b_type.isalnum():
                vk_key = b_type # A, B, 1, 2
            elif b_type.startswith('F') and b_type[1:].isdigit():
                vk_key = 'VK_' + b_type # VK_F1
                
            # 데이터 저장
            item = context.scene.multi_toggle_globals[self.index]
            setattr(item, self.target_prop, vk_key)
            
            # UI 강제 갱신
            for area in context.screen.areas:
                area.tag_redraw()
                
            return {'FINISHED'}
            
        return {'RUNNING_MODAL'}

class MULTI_TOGGLE_OT_cycle_modifier(Operator):
    """조합키 조건을 설정합니다 (없음 -> 긍정 -> 부정)"""
    bl_idname = "multi_toggle.cycle_modifier"
    bl_label = "조합키 설정"
    
    index: IntProperty()
    prop_name: StringProperty()
    
    def execute(self, context):
        item = context.scene.multi_toggle_globals[self.index]
        current = getattr(item, self.prop_name)
        if current == 'NONE':
            setattr(item, self.prop_name, 'POS')
        elif current == 'POS':
            setattr(item, self.prop_name, 'NEG')
        else:
            setattr(item, self.prop_name, 'NONE')
        return {'FINISHED'}

class MULTI_TOGGLE_OT_expand_all_globals(Operator):
    """모든 토글을 펼칩니다"""
    bl_idname = "multi_toggle.expand_all_globals"
    bl_label = "모두 펼치기"
    
    def execute(self, context):
        for item in context.scene.multi_toggle_globals:
            item.is_expanded = True
        return {'FINISHED'}

class MULTI_TOGGLE_OT_collapse_all_globals(Operator):
    """모든 토글을 접습니다"""
    bl_idname = "multi_toggle.collapse_all_globals"
    bl_label = "모두 접기"
    
    def execute(self, context):
        for item in context.scene.multi_toggle_globals:
            item.is_expanded = False
        return {'FINISHED'}

classes = (
    MULTI_TOGGLE_OT_add_global,
    MULTI_TOGGLE_OT_remove_global,
    MULTI_TOGGLE_OT_clear_globals,
    MULTI_TOGGLE_OT_capture_key,
    MULTI_TOGGLE_OT_cycle_modifier,
    MULTI_TOGGLE_OT_expand_all_globals,
    MULTI_TOGGLE_OT_collapse_all_globals,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
