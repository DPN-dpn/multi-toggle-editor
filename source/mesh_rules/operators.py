import bpy
import re
from bpy.types import Operator
from bpy.props import IntProperty
from ..core.live_preview import update_visibility, compile_rules

def is_syntax_valid(rules, globals_list):
    expr = compile_rules(rules, globals_list)
    if not expr: return True
    def repl(match):
        return "1"
    py_expr = re.sub(r'\$([a-zA-Z0-9_]+)', repl, expr)
    py_expr = py_expr.replace("&&", " and ").replace("||", " or ")
    try:
        eval(py_expr)
        return True
    except Exception:
        return False

def backup_rules(rules):
    return [{'type': c.type, 'saved_toggle_index': c.saved_toggle_index, 'compare_op': c.compare_op, 
             'target_state': c.target_state, 'logical_op': c.logical_op} for c in rules]

def restore_rules(rules, backup):
    rules.clear()
    for b in backup:
        c = rules.add()
        c.type = b['type']
        c.saved_toggle_index = b['saved_toggle_index']
        c.compare_op = b['compare_op']
        c.target_state = b['target_state']
        c.logical_op = b['logical_op']

class MULTI_TOGGLE_OT_add_condition(Operator):
    """선택된 오브젝트에 새로운 가시성 조건을 추가합니다"""
    bl_idname = "multi_toggle.add_condition"
    bl_label = "조건 추가"
    
    def execute(self, context):
        obj = context.active_object
        if not (obj and obj.type == 'MESH'):
            obj = context.scene.multi_toggle_active_mesh
            
        if obj:
            rules = obj.multi_toggle_rules.conditions
            bkp = backup_rules(rules)
            
            new_cond = rules.add()
            new_cond.type = 'CONDITION'
            
            if not is_syntax_valid(obj.multi_toggle_rules, context.scene.multi_toggle_globals):
                restore_rules(rules, bkp)
                self.report({'WARNING'}, "문법 오류가 발생하여 추가가 취소되었습니다.")
                return {'CANCELLED'}
            
            scene = context.scene
            if getattr(scene, "multi_toggle_track_preview", False):
                idx = new_cond.saved_toggle_index
                globals_list = scene.multi_toggle_globals
                if idx < len(globals_list):
                    global_toggle = globals_list[idx]
                    if global_toggle.current_state != new_cond.target_state:
                        global_toggle.current_state = min(new_cond.target_state, global_toggle.max_states)
            
            update_visibility(None, context)
        return {'FINISHED'}

class MULTI_TOGGLE_OT_add_paren(Operator):
    bl_idname = "multi_toggle.add_paren"
    bl_label = "괄호 쌍 추가"
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not (obj and obj.type == 'MESH'):
            obj = getattr(context.scene, "multi_toggle_active_mesh", None)
        if not obj: return False
        for c in obj.multi_toggle_rules.conditions:
            if c.type == 'CONDITION': return True
        return False

    def execute(self, context):
        obj = context.active_object
        if not (obj and obj.type == 'MESH'):
            obj = context.scene.multi_toggle_active_mesh
            
        if obj:
            rules = obj.multi_toggle_rules.conditions
            bkp = backup_rules(rules)
            
            last_cond_idx = -1
            for i in range(len(rules)-1, -1, -1):
                if rules[i].type == 'CONDITION':
                    last_cond_idx = i
                    break
                    
            if last_cond_idx == -1:
                return {'CANCELLED'}
            
            p1 = rules.add()
            p1.type = 'PAREN_OPEN'
            rules.move(len(rules)-1, last_cond_idx)
            
            p2 = rules.add()
            p2.type = 'PAREN_CLOSE'
            rules.move(len(rules)-1, last_cond_idx + 2)
            
            if not is_syntax_valid(obj.multi_toggle_rules, context.scene.multi_toggle_globals):
                restore_rules(rules, bkp)
                self.report({'WARNING'}, "괄호 추가 시 문법 오류가 발생하여 취소되었습니다.")
                return {'CANCELLED'}
                
            update_visibility(None, context)
        return {'FINISHED'}

class MULTI_TOGGLE_OT_remove_condition(Operator):
    bl_idname = "multi_toggle.remove_condition"
    bl_label = "조건 삭제"
    index: IntProperty()
    def execute(self, context):
        obj = context.active_object
        if not (obj and obj.type == 'MESH'):
            obj = context.scene.multi_toggle_active_mesh
            
        if obj:
            rules = obj.multi_toggle_rules.conditions
            bkp = backup_rules(rules)
            
            target_type = rules[self.index].type
            to_delete = [self.index]
            
            if target_type == 'PAREN_OPEN':
                depth = 0
                for i in range(self.index + 1, len(rules)):
                    if rules[i].type == 'PAREN_OPEN': depth += 1
                    elif rules[i].type == 'PAREN_CLOSE':
                        if depth == 0:
                            to_delete.append(i)
                            break
                        depth -= 1
            elif target_type == 'PAREN_CLOSE':
                depth = 0
                for i in range(self.index - 1, -1, -1):
                    if rules[i].type == 'PAREN_CLOSE': depth += 1
                    elif rules[i].type == 'PAREN_OPEN':
                        if depth == 0:
                            to_delete.append(i)
                            break
                        depth -= 1
            
            for i in sorted(to_delete, reverse=True):
                rules.remove(i)
                
            # 빈 괄호 자동 삭제
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
                
            if not is_syntax_valid(obj.multi_toggle_rules, context.scene.multi_toggle_globals):
                restore_rules(rules, bkp)
                self.report({'WARNING'}, "삭제 시 문법 오류가 발생하여 취소되었습니다. (관련 연산자를 먼저 정리하세요)")
                return {'CANCELLED'}
                
            if len(rules) == 0:
                obj.hide_viewport = False
                obj.hide_set(False)
            else:
                update_visibility(None, context)
        return {'FINISHED'}

class MULTI_TOGGLE_OT_move_condition(Operator):
    bl_idname = "multi_toggle.move_condition"
    bl_label = "조건 이동"
    index: IntProperty()
    direction: IntProperty()
    def execute(self, context):
        obj = context.active_object
        if not (obj and obj.type == 'MESH'):
            obj = context.scene.multi_toggle_active_mesh
            
        if obj:
            rules = obj.multi_toggle_rules.conditions
            new_index = self.index + self.direction
            if 0 <= new_index < len(rules):
                bkp = backup_rules(rules)
                
                # 논리 연산자가 순서 변경 시에도 고정되도록 스왑
                op1 = rules[self.index].logical_op
                op2 = rules[new_index].logical_op
                
                rules.move(self.index, new_index)
                
                rules[self.index].logical_op = op1
                rules[new_index].logical_op = op2
                
                if not is_syntax_valid(obj.multi_toggle_rules, context.scene.multi_toggle_globals):
                    restore_rules(rules, bkp)
                    self.report({'WARNING'}, "이동 시 문법 오류가 발생하여 취소되었습니다. (예: 빈 괄호나 잘못된 연산자 위치)")
                    return {'CANCELLED'}
                    
                update_visibility(None, context)
        return {'FINISHED'}

classes = (
    MULTI_TOGGLE_OT_add_condition,
    MULTI_TOGGLE_OT_add_paren,
    MULTI_TOGGLE_OT_remove_condition,
    MULTI_TOGGLE_OT_move_condition,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
