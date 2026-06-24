import os
import re
import bpy
from ..core.live_preview import compile_rules

def process_export_mod_ini(filepath, globals_list, scene_objects):
    """
    내보내기 완료 후 Mod.ini 파일을 파이썬으로 열어 토글 로직을 주입합니다.
    """
    if not os.path.exists(filepath):
        print(f"Mod.ini 파일을 찾을 수 없습니다: {filepath}")
        return
        
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    new_lines = []
    
    for line in lines:
        # 기존 텍스트는 그대로 유지
        new_lines.append(line)
        
        # [TextureOverride...] 섹션 감지
        match = re.match(r'^\[TextureOverride(.*)\]', line.strip(), re.IGNORECASE)
        if match:
            mesh_name = match.group(1).strip()
            
            # 메쉬 이름과 일치하는 씬 오브젝트 찾기 (이름 매칭 로직은 모드 구조에 따라 조정 필요)
            obj = None
            for o in scene_objects:
                if o.name.replace(".", "") == mesh_name.replace(".", ""):
                    obj = o
                    break
                    
            if obj and hasattr(obj, 'multi_toggle_rules'):
                rules = obj.multi_toggle_rules.conditions
                if len(rules) > 0:
                    # 조건이 있으면 텍스처 오버라이드 밑에 if문 삽입
                    # 참고: 3DMigoto에서 조건부로 메쉬를 표시하려면, 보통 조건에 안 맞을 때 handling=skip을 씁니다.
                    
                    new_lines.append("; --- Multi-Toggle Auto-Generated Rules ---\n")
                    
                    expr = compile_rules(rules, globals_list)
                    if expr:
                        new_lines.append(f"if {expr}\n")
                        new_lines.append(f"else\n")
                        new_lines.append(f"    handling = skip\n")
                        new_lines.append(f"endif\n")
                    
                    new_lines.append("; -----------------------------------------\n")
                    
    # 글로벌 토글 [Key] 블록을 파일 끝에 추가
    if len(globals_list) > 0:
        new_lines.append("\n; =========================================\n")
        new_lines.append("; Multi-Toggle Auto-Generated Keys\n")
        new_lines.append("; =========================================\n")
        for i, global_toggle in enumerate(globals_list):
            new_lines.append(f"\n[KeyMT_{global_toggle.name}]\n")
            new_lines.append(f"condition = $active == 1\n")
            
            # 정방향 키 생성
            key_mods = []
            if global_toggle.use_ctrl: key_mods.append("ctrl")
            if global_toggle.use_alt: key_mods.append("alt")
            if global_toggle.use_shift: key_mods.append("shift")
            
            key_str = " ".join(key_mods) + f" {global_toggle.hotkey}" if key_mods else f"no_modifiers {global_toggle.hotkey}"
            new_lines.append(f"key = {key_str}\n")
            
            # 역방향 키 생성
            if global_toggle.back_key:
                back_mods = []
                if global_toggle.back_use_ctrl: back_mods.append("ctrl")
                if global_toggle.back_use_alt: back_mods.append("alt")
                if global_toggle.back_use_shift: back_mods.append("shift")
                
                back_str = " ".join(back_mods) + f" {global_toggle.back_key}" if back_mods else f"no_modifiers {global_toggle.back_key}"
                new_lines.append(f"back = {back_str}\n")
                
            new_lines.append(f"type = cycle\n")
            
            # 0, 1, 2 등의 상태 리스트 생성
            states = ", ".join([str(s) for s in range(global_toggle.max_states + 1)])
            new_lines.append(f"${global_toggle.name} = {states}\n")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
        
    print(f"성공적으로 Mod.ini 파일에 멀티 토글 규칙을 주입했습니다: {filepath}")

def process_import_mod_ini(filepath, context):
    """
    Mod.ini 파일을 파싱하여 글로벌 토글 매니저와 메쉬 가시성 규칙을 블랜더 프로퍼티로 복원합니다.
    """
    if not os.path.exists(filepath):
        print(f"Mod.ini 파일을 찾을 수 없습니다: {filepath}")
        return
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    scene = context.scene
    globals_list = scene.multi_toggle_globals
    globals_list.clear()
    
    # 1. [KeyMT_...] 블록들을 찾아서 글로벌 토글 리스트 복원
    # 예시:
    # [KeyMT_Hair]
    # condition = $active == 1
    # key = VK_UP
    # back = VK_DOWN
    # type = cycle
    # $Hair = 0, 1, 2
    
    key_block_pattern = r'\[KeyMT_([a-zA-Z0-9_]+)\](.*?)(?=\n\[|$)'
    blocks = re.finditer(key_block_pattern, content, re.IGNORECASE | re.DOTALL)
    
    for block_match in blocks:
        block_name = block_match.group(1).strip()
        block_content = block_match.group(2)
        
        key_match = re.search(r'key\s*=\s*(.+)', block_content, re.IGNORECASE)
        back_match = re.search(r'back\s*=\s*(.+)', block_content, re.IGNORECASE)
        var_match = re.search(r'\$' + block_name + r'\s*=\s*(.+)', block_content, re.IGNORECASE)
        
        if key_match and var_match:
            # Parse Forward Key
            key_parts = key_match.group(1).strip().split()
            hotkey = key_parts[-1] if key_parts else ""
            use_ctrl = "ctrl" in key_parts
            use_shift = "shift" in key_parts
            use_alt = "alt" in key_parts
            
            # Parse Backward Key
            back_key = ""
            back_use_ctrl = False
            back_use_shift = False
            back_use_alt = False
            
            if back_match:
                back_parts = back_match.group(1).strip().split()
                if back_parts:
                    back_key = back_parts[-1]
                    back_use_ctrl = "ctrl" in back_parts
                    back_use_shift = "shift" in back_parts
                    back_use_alt = "alt" in back_parts
            
            states_str = var_match.group(1).strip()
            states = [s.strip() for s in states_str.split(',')]
            max_states = len(states) - 1 if len(states) > 0 else 1
            
            item = globals_list.add()
            item.name = block_name
            item.hotkey = hotkey
            item.use_ctrl = use_ctrl
            item.use_shift = use_shift
            item.use_alt = use_alt
            
            item.back_key = back_key
            item.back_use_ctrl = back_use_ctrl
            item.back_use_shift = back_use_shift
            item.back_use_alt = back_use_alt
            
            item.max_states = max_states
        
    print(f"[{len(globals_list)}] 개의 글로벌 토글 규칙을 복원했습니다.")
    
    # 2. [TextureOverride...] 섹션 내의 if $Name != Y 블록 파싱
    tex_pattern = r'\[TextureOverride(.*?)\](.*?)(?=\n\[|$)'
    tex_matches = re.finditer(tex_pattern, content, re.IGNORECASE | re.DOTALL)
    
    restored_meshes = 0
    for tex_match in tex_matches:
        mesh_name = tex_match.group(1).strip()
        block_content = tex_match.group(2)
        
        conditions_to_add = []
        
        # 1. 이전 버전 하위 호환성 (if $name != X \n ... handling = skip)
        old_if_pattern = r'if\s+\$([a-zA-Z0-9_]+)\s*!=\s*(\d+)'
        for if_match in re.finditer(old_if_pattern, block_content, re.IGNORECASE):
            var_name = if_match.group(1)
            target_state = int(if_match.group(2))
            
            toggle_index = -1
            for i, gt in enumerate(globals_list):
                if gt.name == var_name:
                    toggle_index = i
                    break
            if toggle_index != -1:
                conditions_to_add.append({"basic": True, "idx": toggle_index, "state": target_state})
                
        # 2. 신규 버전 (if EXPR \n else \n handling = skip \n endif)
        new_if_pattern = r'if\s+(.+?)\n\s*else\s*\n\s*handling\s*=\s*skip\s*\n\s*endif'
        for new_match in re.finditer(new_if_pattern, block_content, re.IGNORECASE):
            full_expr = new_match.group(1).strip()
            
            # 괄호, &&, || 로 분리하여 토큰화
            tokens = re.split(r'(\(|\)|&&|\|\|)', full_expr)
            pending_logical_op = '&&'
            for tk in tokens:
                tk = tk.strip()
                if not tk: continue
                if tk == '(':
                    conditions_to_add.append({'type': 'PAREN_OPEN', 'logical_op': pending_logical_op})
                    pending_logical_op = '&&'
                elif tk == ')':
                    conditions_to_add.append({'type': 'PAREN_CLOSE'})
                elif tk == '&&' or tk == '||':
                    pending_logical_op = tk
                else:
                    m = re.match(r'^\$?([a-zA-Z0-9_]+)\s*(==|!=|<|>|<=|>=)\s*(\d+)$', tk)
                    if m:
                        var_name = m.group(1)
                        cmp_op = m.group(2)
                        target_state = int(m.group(3))
                        
                        toggle_index = -1
                        for i, gt in enumerate(globals_list):
                            if gt.name == var_name:
                                toggle_index = i
                                break
                        if toggle_index != -1:
                            conditions_to_add.append({'type': 'CONDITION', 'idx': toggle_index, 'cmp': cmp_op, 'state': target_state, 'logical_op': pending_logical_op})
                            pending_logical_op = '&&'
                
        if len(conditions_to_add) > 0:
            for obj in scene.objects:
                if obj.type == 'MESH' and obj.name.replace(".", "") == mesh_name.replace(".", ""):
                    rules = obj.multi_toggle_rules.conditions
                    rules.clear()
                    for c in conditions_to_add:
                        new_cond = rules.add()
                        new_cond.type = c['type']
                        if 'logical_op' in c:
                            new_cond.logical_op = c['logical_op']
                        
                        if c['type'] == 'CONDITION':
                            new_cond.toggle_enum = str(c["idx"])
                            new_cond.compare_op = c["cmp"]
                            new_cond.target_state = c["state"]
                    restored_meshes += 1
                    break
                    
    print(f"[{restored_meshes}] 개의 메쉬에서 가시성 규칙을 복원했습니다.")
