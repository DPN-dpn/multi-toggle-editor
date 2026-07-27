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
            m = re.match(r'^\$([a-zA-Z0-9_]+)\s*(==|!=|<|>|<=|>=)\s*(\d+)$', tk)
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
                    if target_state >= globals_list[toggle_index].max_states:
                        globals_list[toggle_index].max_states = target_state + 1
                        
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
    
    # 1. Target Variables 수집 (Phase 1)
    target_vars = set()
    tex_pattern = r'\[TextureOverride(.*?)\](.*?)(?=\n\[|$)'
    tex_matches = list(re.finditer(tex_pattern, content, re.IGNORECASE | re.DOTALL))
    
    for tex_match in tex_matches:
        block_content = tex_match.group(2)
        for line in block_content.splitlines():
            stripped = line.strip().lower()
            if stripped.startswith('if ') or stripped.startswith('elif '):
                for m in re.finditer(r'\$([a-zA-Z0-9_]+)', line):
                    target_vars.add(m.group(1))
                    
    # [Present] 블록 추출 (변수 필터링용)
    present_content = ""
    present_match = re.search(r'\[Present\](.*?)(?=\n\[|$)', content, re.IGNORECASE | re.DOTALL)
    if present_match:
        present_content = present_match.group(1)
        
    # [Key...] 블록들 스캔
    key_block_pattern = r'\[Key([a-zA-Z0-9_]+)\](.*?)(?=\n\[|$)'
    key_blocks = list(re.finditer(key_block_pattern, content, re.IGNORECASE | re.DOTALL))
    
    # 2. Target Variables에 해당하는 토글만 생성 (Phase 2 & 3)
    for var_name in target_vars:
        # 내부 계산용 변수 필터링
        if present_content and re.search(r'\$' + re.escape(var_name) + r'\b', present_content, re.IGNORECASE):
            continue
            
        matched_block = None
        var_match_in_block = None
        
        for kb in key_blocks:
            kb_content = kb.group(2)
            # 이 키 블록이 해당 변수를 조작하는지 확인 ($var_name = ...)
            v_match = re.search(r'\$' + re.escape(var_name) + r'\s*=\s*(.+)', kb_content, re.IGNORECASE)
            if v_match:
                matched_block = kb
                var_match_in_block = v_match
                break
                
        item = globals_list.add()
        item.name = var_name
        
        if matched_block:
            kb_content = matched_block.group(2)
            key_match = re.search(r'key\s*=\s*(.+)', kb_content, re.IGNORECASE)
            back_match = re.search(r'back\s*=\s*(.+)', kb_content, re.IGNORECASE)
            
            if key_match:
                key_parts = key_match.group(1).strip().split()
                item.hotkey = key_parts[-1] if key_parts else ""
                item.use_ctrl = 'POS' if "ctrl" in key_parts else 'NEG' if "no_ctrl" in key_parts else 'NONE'
                item.use_shift = 'POS' if "shift" in key_parts else 'NEG' if "no_shift" in key_parts else 'NONE'
                item.use_alt = 'POS' if "alt" in key_parts else 'NEG' if "no_alt" in key_parts else 'NONE'
                
            if back_match:
                back_parts = back_match.group(1).strip().split()
                if back_parts:
                    item.back_key = back_parts[-1]
                    item.back_use_ctrl = 'POS' if "ctrl" in back_parts else 'NEG' if "no_ctrl" in back_parts else 'NONE'
                    item.back_use_shift = 'POS' if "shift" in back_parts else 'NEG' if "no_shift" in back_parts else 'NONE'
                    item.back_use_alt = 'POS' if "alt" in back_parts else 'NEG' if "no_alt" in back_parts else 'NONE'
                    
            states_str = var_match_in_block.group(1).strip()
            states = [s.strip() for s in states_str.split(',')]
            item.max_states = len(states) if len(states) > 0 else 1
        else:
            item.max_states = 2
            
    print(f"[{len(globals_list)}] 개의 글로벌 토글 규칙을 복원했습니다.")
    
    # 3. [TextureOverride...] 섹션 내 규칙 복원
    restored_meshes = 0
    for tex_match in tex_matches:
        tex_mesh_name = tex_match.group(1).strip()
        block_content = tex_match.group(2)
        
        conditions_to_add_legacy = []
        
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
                if target_state >= globals_list[toggle_index].max_states:
                    globals_list[toggle_index].max_states = target_state + 1
                conditions_to_add_legacy.append({"basic": True, "idx": toggle_index, "state": target_state})
                
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
                    
        condition_stack = []
        buffer_comments = []
        
        lines = block_content.splitlines()
        for line in lines:
            stripped = line.strip().lower()
            if stripped.startswith('if '):
                expr = line.strip()[3:].strip()
                condition_stack.append({'type': 'if', 'expr': expr})
            elif stripped.startswith('elif '):
                expr = line.strip()[5:].strip()
                if condition_stack:
                    condition_stack[-1] = {'type': 'elif', 'expr': expr}
            elif stripped == 'else':
                if condition_stack:
                    prev_expr = condition_stack[-1]['expr']
                    if '==' in prev_expr:
                        inverted = prev_expr.replace('==', '!=')
                    elif '!=' in prev_expr:
                        inverted = prev_expr.replace('!=', '==')
                    else:
                        inverted = f"!({prev_expr})"
                    condition_stack[-1] = {'type': 'else', 'expr': inverted}
            elif stripped == 'endif':
                if condition_stack:
                    condition_stack.pop()
            elif stripped.startswith(';') or not stripped:
                buffer_comments.append(line)
            elif stripped.startswith('drawindexed'):
                part_mesh_name = None
                for c in reversed(buffer_comments):
                    m = re.match(r'^\s*;\s*(.*?)(?:\s*\(\d+\))?\s*$', c)
                    if m:
                        part_mesh_name = m.group(1).strip()
                        break
                        
                if part_mesh_name:
                    combined_expr = ""
                    if condition_stack:
                        exprs = [c['expr'] for c in condition_stack]
                        combined_expr = " && ".join([f"({e})" if len(exprs) > 1 else e for e in exprs])
                    
                    if combined_expr:
                        conditions_to_add = []
                        parse_expr_to_conditions(combined_expr, conditions_to_add, globals_list)
                        
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
                
                buffer_comments.clear()
            else:
                buffer_comments.clear()
                        
    print(f"[{restored_meshes}] 개의 메쉬에서 가시성 규칙 복원을 마쳤습니다.")
                        
