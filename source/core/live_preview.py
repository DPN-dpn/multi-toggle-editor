import bpy
import re

def evaluate_advanced_expression(expr, globals_list):
    if not expr:
        return True
        
    def repl(match):
        var_name = match.group(1)
        for gt in globals_list:
            if gt.name == var_name:
                return str(gt.current_state)
        return "0"
        
    py_expr = re.sub(r'\$([a-zA-Z0-9_]+)', repl, expr)
    py_expr = py_expr.replace("&&", " and ").replace("||", " or ")
    
    try:
        return bool(eval(py_expr))
    except Exception:
        # 문법이 미완성이거나 오류일 때는 숨기지 않음 (편집 중 패널 사라짐 방지)
        return True

def compile_rules(rules, globals_list):
    parts = []
    last_type = None
    
    for i, cond in enumerate(rules.conditions):
        if cond.type == 'LOGIC': continue
        
        needs_logic = False
        if i > 0 and last_type in ('CONDITION', 'PAREN_CLOSE') and cond.type in ('CONDITION', 'PAREN_OPEN'):
            needs_logic = True
            
        if needs_logic:
            parts.append(cond.logical_op)
            
        if cond.type == 'CONDITION':
            try:
                idx = cond.saved_toggle_index
                name = globals_list[idx].name
            except:
                name = "Unknown"
            parts.append(f"${name} {cond.compare_op} {cond.target_state}")
            
        elif cond.type == 'PAREN_OPEN':
            parts.append("(")
            
        elif cond.type == 'PAREN_CLOSE':
            parts.append(")")
            
        last_type = cond.type
        
    expr = " ".join(parts)
    
    # 잉여 수식(빈 괄호, 남겨진 논리 연산자 등) 정리
    while True:
        new_expr = expr.replace("( )", "").replace("()", "")
        new_expr = re.sub(r'\s+', ' ', new_expr).strip()
        
        # 중복 논리 연산자 정리
        new_expr = new_expr.replace("&& &&", "&&").replace("|| ||", "||")
        new_expr = new_expr.replace("&& ||", "&&").replace("|| &&", "||")
        new_expr = re.sub(r'\s+', ' ', new_expr).strip()
        
        if new_expr.startswith("&&"): new_expr = new_expr[2:].strip()
        if new_expr.startswith("||"): new_expr = new_expr[2:].strip()
        if new_expr.endswith("&&"): new_expr = new_expr[:-2].strip()
        if new_expr.endswith("||"): new_expr = new_expr[:-2].strip()
        
        if new_expr == expr:
            break
        expr = new_expr
        
    return expr

def update_visibility(self=None, context=None):
    """
    씬 내의 모든 메쉬 오브젝트를 순회하며, multi_toggle_rules 조건에 따라
    가시성(hide_viewport, hide_set)을 실시간으로 업데이트합니다.
    """
    if context is None:
        context = bpy.context
        
    scene = context.scene
    
    # 뷰포트에서 사라지기 전에 현재 활성 메쉬를 고정 타겟으로 저장
    act_obj = context.active_object
    if act_obj and act_obj.type == 'MESH':
        scene.multi_toggle_active_mesh = act_obj
        
    live_preview_enabled = getattr(scene, "multi_toggle_live_preview", True)
    globals_list = scene.multi_toggle_globals
    
    for obj in scene.objects:
        if obj.type != 'MESH':
            continue
            
        if not live_preview_enabled:
            if obj.hide_viewport != False:
                obj.hide_viewport = False
            if obj.hide_get() != False:
                obj.hide_set(False)
            continue
            
        rules = obj.multi_toggle_rules
        if len(rules.conditions) == 0:
            # 규칙이 없으면 기본 가시성 상태를 건드리지 않습니다.
            continue
            
        expr = compile_rules(rules, globals_list)
        is_visible = evaluate_advanced_expression(expr, globals_list)
                
        # 가시성 업데이트 (상태가 다를 때만 갱신하여 퍼포먼스 최적화)
        target_hide = not is_visible
        
        if obj.hide_viewport != target_hide:
            obj.hide_viewport = target_hide
            
        if obj.hide_get() != target_hide:
            obj.hide_set(target_hide)
