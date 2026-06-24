import bpy
from bpy.types import Panel

def creates_empty_parens(rules, idx1, idx2):
    if idx2 < 0 or idx2 >= len(rules): return False
    types = [c.type for c in rules]
    types[idx1], types[idx2] = types[idx2], types[idx1]
    for i in range(len(types) - 1):
        if types[i] == 'PAREN_OPEN' and types[i+1] == 'PAREN_CLOSE':
            return True
    return False

class MULTI_TOGGLE_PT_mesh_rules_panel(Panel):
    """선택된 메쉬의 가시성 규칙을 설정하는 패널"""
    bl_label = "메쉬 가시성 규칙"
    bl_idname = "MULTI_TOGGLE_PT_mesh_rules_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = '멀티 토글'
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH'
        
    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        scene = context.scene
        
        layout.label(text=f"선택됨: {obj.name}", icon='MESH_DATA')
        
        row = layout.row(align=True)
        row.operator("multi_toggle.add_condition", text="조건", icon='ADD')
        row.operator("multi_toggle.add_paren", text="( ) 추가", icon='PASTEDOWN')
        
        rules = obj.multi_toggle_rules
        
        # 이전 버전 데이터 변환 (LOGIC 토큰을 다음 토큰의 속성으로 흡수)
        i = 0
        while i < len(rules.conditions):
            if rules.conditions[i].type == 'LOGIC':
                if i + 1 < len(rules.conditions):
                    rules.conditions[i+1].logical_op = rules.conditions[i].logical_op
                rules.conditions.remove(i)
            else:
                i += 1
                
        if len(rules.conditions) == 0:
            layout.label(text="조건이 없습니다. 항상 표시됩니다.")
        else:
            box = layout.box()
            last_type = None
            for i, cond in enumerate(rules.conditions):
                row = box.row(align=True)
                
                needs_logic = False
                if i > 0 and last_type in ('CONDITION', 'PAREN_CLOSE') and cond.type in ('CONDITION', 'PAREN_OPEN'):
                    needs_logic = True
                    
                if needs_logic:
                    logic_row = box.row()
                    logic_row.alignment = 'CENTER'
                    logic_row.prop(cond, "logical_op", text="")
                
                row = box.row(align=True)
                if cond.type == 'CONDITION':
                    row.prop(cond, "toggle_enum", text="")
                    row.prop(cond, "compare_op", text="")
                    row.prop(cond, "target_state", text="")
                elif cond.type == 'PAREN_OPEN':
                    row.label(text="(")
                elif cond.type == 'PAREN_CLOSE':
                    row.label(text=")")
                
                can_up = i > 0 and not creates_empty_parens(rules.conditions, i, i - 1)
                can_dn = i < len(rules.conditions) - 1 and not creates_empty_parens(rules.conditions, i, i + 1)
                
                col = row.column(align=True)
                col.enabled = can_up
                up = col.operator("multi_toggle.move_condition", text="", icon='TRIA_UP')
                up.index = i; up.direction = -1
                
                col = row.column(align=True)
                col.enabled = can_dn
                dn = col.operator("multi_toggle.move_condition", text="", icon='TRIA_DOWN')
                dn.index = i; dn.direction = 1
                
                remove_op = row.operator("multi_toggle.remove_condition", text="", icon='TRASH')
                remove_op.index = i
                
                last_type = cond.type

classes = (
    MULTI_TOGGLE_PT_mesh_rules_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
