import bpy
import re
from bpy.props import StringProperty, IntProperty, CollectionProperty, PointerProperty
from bpy.types import PropertyGroup
from .live_preview import update_visibility

def update_current_state(self, context):
    if self.current_state > self.max_states - 1:
        self.current_state = self.max_states - 1
        return
    update_visibility(self, context)

def update_max_states(self, context):
    if self.current_state > self.max_states - 1:
        self.current_state = self.max_states - 1

def update_toggle_name(self, context):
    # 영문자, 숫자만 남기기
    new_name = re.sub(r'[^a-zA-Z0-9]', '', self.name)
    if not new_name:
        new_name = "Toggle"
    # 만약 첫 글자가 숫자인 경우 (예: "1" 또는 "123")
    if new_name[0].isdigit():
        new_name = "key" + new_name
        
    if new_name != self.name:
        self.name = new_name

class MultiToggleGlobalItem(PropertyGroup):
    """글로벌 토글 항목 한 개를 정의하는 클래스"""
    name: StringProperty(
        name="이름(영문)", 
        description="INI 변수명으로 사용되므로 영문자/숫자만 허용됩니다.", 
        default="NewToggle",
        update=update_toggle_name
    )
    hotkey: StringProperty(name="단축키", description="이 토글을 작동시킬 단축키입니다 (예: VK_UP)", default="VK_UP")
    use_ctrl: bpy.props.BoolProperty(name="Ctrl", description="정방향 단축키에 Ctrl을 조합합니다", default=False)
    use_shift: bpy.props.BoolProperty(name="Shift", description="정방향 단축키에 Shift를 조합합니다", default=False)
    use_alt: bpy.props.BoolProperty(name="Alt", description="정방향 단축키에 Alt를 조합합니다", default=False)
    
    back_key: StringProperty(name="역방향 키", description="상태를 역순환시킬 단축키입니다 (빈 칸이면 사용 안 함)", default="")
    back_use_ctrl: bpy.props.BoolProperty(name="Ctrl", description="역방향 단축키에 Ctrl을 조합합니다", default=False)
    back_use_shift: bpy.props.BoolProperty(name="Shift", description="역방향 단축키에 Shift를 조합합니다", default=False)
    back_use_alt: bpy.props.BoolProperty(name="Alt", description="역방향 단축키에 Alt를 조합합니다", default=False)
    
    max_states: IntProperty(
        name="상태 수", 
        description="토글이 가질 수 있는 총 상태의 개수입니다 (예: 2이면 0과 1)", 
        default=2, 
        min=1,
        update=update_max_states
    )
    current_state: IntProperty(
        name="현재 상태", 
        description="실시간 미리보기를 위한 현재 상태입니다", 
        default=0, 
        min=0,
        update=update_current_state
    )
    is_expanded: bpy.props.BoolProperty(
        name="펼치기/접기",
        description="토글 세부 설정을 표시하거나 숨깁니다",
        default=True
    )

def update_condition(self, context):
    scene = context.scene
    globals_list = scene.multi_toggle_globals
    
    idx = self.saved_toggle_index
        
    if idx < len(globals_list):
        global_toggle = globals_list[idx]
        
        # 요구 상태(target_state)가 토글의 최대 상태 인덱스를 넘지 못하게 제한
        if self.target_state > global_toggle.max_states - 1:
            self.target_state = global_toggle.max_states - 1
            
        if getattr(scene, "multi_toggle_track_preview", False):
            if global_toggle.current_state != self.target_state:
                new_state = min(self.target_state, global_toggle.max_states - 1)
                if global_toggle.current_state != new_state:
                    global_toggle.current_state = new_state
    
    update_visibility(self, context)

def get_toggle_items(self, context):
    items = []
    for i, gt in enumerate(context.scene.multi_toggle_globals):
        items.append((str(i), gt.name, f"Index: {i}"))
    if not items:
        items.append(("0", "없음", ""))
    return items

class MultiToggleVisibilityCondition(PropertyGroup):
    """특정 메쉬가 보여지기 위한 조건 (토큰 역할 겸용)"""
    type: bpy.props.EnumProperty(
        name="종류",
        items=[
            ('CONDITION', "조건", ""),
            ('LOGIC', "논리 연산", ""),
            ('PAREN_OPEN', "열린 괄호", ""),
            ('PAREN_CLOSE', "닫힌 괄호", "")
        ],
        default='CONDITION',
        update=update_condition
    )
    logical_op: bpy.props.EnumProperty(
        name="논리 연산자",
        items=[
            ('&&', "AND", ""),
            ('||', "OR", "")
        ],
        default='&&',
        update=update_condition
    )
    compare_op: bpy.props.EnumProperty(
        name="비교 연산자",
        items=[
            ('==', "==", ""),
            ('!=', "!=", ""),
            ('<', "<", ""),
            ('>', ">", ""),
            ('<=', "<=", ""),
            ('>=', ">=", "")
        ],
        default='==',
        update=update_condition
    )
    saved_toggle_index: IntProperty(default=0)
    
    def get_toggle_index(self):
        return self.saved_toggle_index
        
    def set_toggle_index(self, value):
        self.saved_toggle_index = value
        update_condition(self, bpy.context)
        
    toggle_enum: bpy.props.EnumProperty(
        name="대상 토글", 
        description="이 조건이 확인할 글로벌 토글입니다", 
        items=get_toggle_items,
        get=get_toggle_index,
        set=set_toggle_index
    )
    target_state: IntProperty(
        name="목표 상태", 
        description="메쉬가 보이기 위해 일치해야 하는 상태 값입니다", 
        default=0, 
        min=0,
        update=update_condition
    )

class MultiToggleMeshRules(PropertyGroup):
    """메쉬 Object에 부착될 가시성 조건들의 모음"""
    conditions: CollectionProperty(type=MultiToggleVisibilityCondition)

classes = (
    MultiToggleGlobalItem,
    MultiToggleVisibilityCondition,
    MultiToggleMeshRules,
)

def register():
    bpy.types.Scene.multi_toggle_live_preview = bpy.props.BoolProperty(
        name="미리보기 렌더링",
        description="토글 조건에 따라 메쉬를 실시간으로 숨깁니다. (끄면 항상 표시)",
        default=True,
        update=lambda self, context: update_visibility(None, context)
    )
    bpy.types.Scene.multi_toggle_track_preview = bpy.props.BoolProperty(
        name="미리보기 추적",
        description="토글 조건을 변경하면 실시간 미리보기도 해당 상태로 자동 전환됩니다",
        default=False
    )
    bpy.types.Scene.multi_toggle_show_globals = bpy.props.BoolProperty(
        name="토글 키 목록 표시",
        description="토글 키 목록을 펼치거나 접습니다",
        default=True
    )
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.multi_toggle_globals = CollectionProperty(type=MultiToggleGlobalItem)
    bpy.types.Scene.multi_toggle_active_mesh = PointerProperty(type=bpy.types.Object)
    bpy.types.Object.multi_toggle_rules = PointerProperty(type=MultiToggleMeshRules)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.multi_toggle_globals
    del bpy.types.Scene.multi_toggle_active_mesh
    del bpy.types.Object.multi_toggle_rules
    if hasattr(bpy.types.Scene, "multi_toggle_live_preview"):
        del bpy.types.Scene.multi_toggle_live_preview
        del bpy.types.Scene.multi_toggle_track_preview
