import os
import re

def parse_expr_to_conditions(full_expr, conditions_to_add, globals_list):
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
    
    # 1. [Key...] 블록들을 찾아서 글로벌 토글 리스트 복원
    key_block_pattern = r'\[Key([a-zA-Z0-9_]+)\](.*?)(?=\n\[|$)'
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
            use_ctrl = 'POS' if "ctrl" in key_parts else 'NEG' if "no_ctrl" in key_parts else 'NONE'
            use_shift = 'POS' if "shift" in key_parts else 'NEG' if "no_shift" in key_parts else 'NONE'
            use_alt = 'POS' if "alt" in key_parts else 'NEG' if "no_alt" in key_parts else 'NONE'
            
            # Parse Backward Key
            back_key = ""
            back_use_ctrl = 'NONE'
            back_use_shift = 'NONE'
            back_use_alt = 'NONE'
            
            if back_match:
                back_parts = back_match.group(1).strip().split()
                if back_parts:
                    back_key = back_parts[-1]
                    back_use_ctrl = 'POS' if "ctrl" in back_parts else 'NEG' if "no_ctrl" in back_parts else 'NONE'
                    back_use_shift = 'POS' if "shift" in back_parts else 'NEG' if "no_shift" in back_parts else 'NONE'
                    back_use_alt = 'POS' if "alt" in back_parts else 'NEG' if "no_alt" in back_parts else 'NONE'
            
            states_str = var_match.group(1).strip()
            states = [s.strip() for s in states_str.split(',')]
            max_states = len(states) if len(states) > 0 else 1
            
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
    
    # 2. [TextureOverride...] 섹션 내 파싱
    tex_pattern = r'\[TextureOverride(.*?)\](.*?)(?=\n\[|$)'
    tex_matches = re.finditer(tex_pattern, content, re.IGNORECASE | re.DOTALL)
    
    restored_meshes = 0
    for tex_match in tex_matches:
        tex_mesh_name = tex_match.group(1).strip()
        block_content = tex_match.group(2)
        
        conditions_to_add_legacy = []
        
        # 1. 이전 버전 하위 호환성 (if $name != X \n ... handling = skip) -> 전체 메쉬에 적용
        old_if_pattern = r'if\s+\$([a-zA-Z0-9_]+)\s*!=\s*(\d+).*?handling\s*=\s*skip'
        for if_match in re.finditer(old_if_pattern, block_content, re.IGNORECASE | re.DOTALL):
            var_name = if_match.group(1)
            target_state = int(if_match.group(2))
            toggle_index = -1
            for i, gt in enumerate(globals_list):
                if gt.name == var_name:
                    toggle_index = i
                    break
            if toggle_index != -1:
                conditions_to_add_legacy.append({"basic": True, "idx": toggle_index, "state": target_state})
                
        # 2. 구버전 신규 버전 (if EXPR \n else \n handling = skip \n endif) -> 전체 메쉬에 적용
        new_if_pattern = r'if\s+(.+?)\n\s*else\s*\n\s*handling\s*=\s*skip\s*\n\s*endif'
        for new_match in re.finditer(new_if_pattern, block_content, re.IGNORECASE):
            parse_expr_to_conditions(new_match.group(1).strip(), conditions_to_add_legacy, globals_list)
            
        if len(conditions_to_add_legacy) > 0:
            for obj in scene.objects:
                if obj.type == 'MESH' and obj.name == tex_mesh_name:
                    rules = obj.multi_toggle_rules.conditions
                    rules.clear()
                    for c in conditions_to_add_legacy:
                        if 'basic' in c:
                            new_cond = rules.add()
                            new_cond.type = 'CONDITION'
                            new_cond.saved_toggle_index = c["idx"]
                            new_cond.compare_op = '=='
                            new_cond.target_state = c["state"]
                        else:
                            new_cond = rules.add()
                            new_cond.type = c['type']
                            if 'logical_op' in c: new_cond.logical_op = c['logical_op']
                            if c['type'] == 'CONDITION':
                                new_cond.saved_toggle_index = c["idx"]
                                new_cond.compare_op = c["cmp"]
                                new_cond.target_state = c["state"]
                    restored_meshes += 1
                    break
                    
        # 3. 최신 파츠별 drawindexed 버전 (if EXPR \n ... drawindexed = ... \n endif)
        part_pattern = r'if\s+(.+?)\n(.*?drawindexed\s*=.*?)\nendif'
        for match in re.finditer(part_pattern, block_content, re.IGNORECASE | re.DOTALL):
            expr = match.group(1).strip()
            inner_block = match.group(2)
            
            part_mesh_name = None
            for line in reversed(inner_block.splitlines()):
                m = re.match(r'^\s*;\s*(.*?)(?:\s*\(\d+\))?\s*$', line)
                if m:
                    part_mesh_name = m.group(1).strip()
                    break
                    
            if part_mesh_name:
                conditions_to_add = []
                parse_expr_to_conditions(expr, conditions_to_add, globals_list)
                
                for obj in scene.objects:
                    if obj.type == 'MESH' and obj.name == part_mesh_name:
                        rules = obj.multi_toggle_rules.conditions
                        rules.clear()
                        for c in conditions_to_add:
                            new_cond = rules.add()
                            new_cond.type = c['type']
                            if 'logical_op' in c: new_cond.logical_op = c['logical_op']
                            if c['type'] == 'CONDITION':
                                new_cond.saved_toggle_index = c["idx"]
                                new_cond.compare_op = c["cmp"]
                                new_cond.target_state = c["state"]
                        restored_meshes += 1
                        break
                        
    print(f"[{restored_meshes}] 개의 메쉬에서 가시성 규칙 복원을 마쳤습니다.")
