import os
import re
from ...core.live_preview import compile_rules

def clean_existing_rules(content):
    # 1. Clean explicit markers (from the previous version)
    pattern = r'; --- MT: [a-zA-Z0-9_.-]+ ---\nif.*?\n(.*?)endif\n; -------------------------\n?'
    def repl(m):
        inner = m.group(1)
        return re.sub(r'^    ', '', inner, flags=re.MULTILINE)
    content = re.sub(pattern, repl, content, flags=re.DOTALL | re.IGNORECASE)
    
    # 2. Clean implicit wrappers (if...endif around drawindexed)
    lines = content.splitlines(keepends=True)
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().lower().startswith('if '):
            j = i + 1
            inner_lines = []
            has_drawindexed = False
            has_other = False
            found_endif = False
            while j < len(lines):
                inner_line = lines[j]
                stripped = inner_line.strip().lower()
                if stripped == 'endif':
                    found_endif = True
                    break
                elif stripped.startswith('if '):
                    has_other = True
                    break
                elif stripped.startswith('drawindexed'):
                    has_drawindexed = True
                    inner_lines.append(inner_line)
                elif stripped.startswith(';') or not stripped:
                    inner_lines.append(inner_line)
                else:
                    has_other = True
                    break
                j += 1
                
            if found_endif and has_drawindexed and not has_other:
                # This is a valid wrapper
                for il in inner_lines:
                    new_lines.append(re.sub(r'^    ', '', il))
                i = j + 1
                continue
                
        new_lines.append(line)
        i += 1
        
    return "".join(new_lines)

def process_export_mod_ini(filepath, globals_list, scene_objects):
    """
    내보내기 완료 후 Mod.ini 파일을 파이썬으로 열어 토글 로직을 주입합니다.
    """
    if not os.path.exists(filepath):
        print(f"Mod.ini 파일을 찾을 수 없습니다: {filepath}")
        return
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 기존 자동 생성된 규칙 및 키 블록 초기화 (중복 방지)
    content = re.sub(r'; --- Multi-Toggle Auto-Generated Rules ---.*?;\s*-{10,}\n?', '', content, flags=re.DOTALL | re.IGNORECASE)
    content = clean_existing_rules(content)
    content = re.sub(r'; =========================================\n;\s*Multi-Toggle Auto-Generated Keys.*?$', '', content, flags=re.DOTALL | re.IGNORECASE)
    
    lines = content.splitlines(keepends=True)
    new_lines = []
    
    buffer_comments = []
    in_texture_override = False
    
    for line in lines:
        if line.strip().startswith('[TextureOverride'):
            in_texture_override = True
            
        elif line.strip().startswith('['):
            in_texture_override = False
            
        if in_texture_override:
            if line.strip().startswith(';') or not line.strip():
                buffer_comments.append(line)
                continue
                
            if line.strip().lower().startswith('drawindexed'):
                mesh_name = None
                for c in reversed(buffer_comments):
                    m = re.match(r'^\s*;\s*([a-zA-Z0-9_.-]+)', c)
                    if m:
                        mesh_name = m.group(1)
                        break
                        
                expr = None
                if mesh_name:
                    obj = next((o for o in scene_objects if o.type == 'MESH' and o.name == mesh_name), None)
                    if obj and hasattr(obj, 'multi_toggle_rules') and len(obj.multi_toggle_rules.conditions) > 0:
                        expr = compile_rules(obj.multi_toggle_rules, globals_list)
                        
                if expr:
                    new_lines.append(f"if {expr}\n")
                    for c in buffer_comments:
                        new_lines.append("    " + c if c.strip() else c)
                    new_lines.append(f"    {line}")
                    new_lines.append(f"endif\n")
                else:
                    for c in buffer_comments:
                        new_lines.append(c)
                    new_lines.append(line)
                    
                buffer_comments.clear()
                continue
                
        # Flush buffers if any
        for c in buffer_comments:
            new_lines.append(c)
        buffer_comments.clear()
        
        new_lines.append(line)
        
    # 남아있는 주석 버퍼가 있다면 모두 플러시
    for c in buffer_comments:
        new_lines.append(c)
                    
    # 글로벌 토글 [Key] 블록을 파일 끝에 추가
    if len(globals_list) > 0:
        new_lines.append("\n; =========================================\n")
        new_lines.append("; Multi-Toggle Auto-Generated Keys\n")
        new_lines.append("; =========================================\n")
        for i, global_toggle in enumerate(globals_list):
            new_lines.append(f"\n[Key{global_toggle.name}]\n")
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
            states = ", ".join([str(s) for s in range(global_toggle.max_states)])
            new_lines.append(f"${global_toggle.name} = {states}\n")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
        
    print(f"성공적으로 Mod.ini 파일에 멀티 토글 규칙을 주입했습니다: {filepath}")
