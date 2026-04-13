import re
import keyword

_MODIFIERS = {
    "CTRL",
    "CONTROL",
    "SHIFT",
    "ALT",
    "ALTGR",
    "META",
    "CMD",
    "COMMAND",
    "WIN",
    "SUPER",
}

_NAMED_KEYS = {
    "ENTER",
    "RETURN",
    "TAB",
    "SPACE",
    "BACKSPACE",
    "BS",
    "ESC",
    "ESCAPE",
    "UP",
    "DOWN",
    "LEFT",
    "RIGHT",
    "PAGEUP",
    "PAGEDOWN",
    "HOME",
    "END",
    "INSERT",
    "DELETE",
    "DEL",
    "PRINTSCREEN",
    "PAUSE",
    "CAPSLOCK",
    "NUMLOCK",
    "SCROLLLOCK",
    "PLUS",
    "MINUS",
    "EQUALS",
    "COMMA",
    "DOT",
    "PERIOD",
    "SLASH",
    "BACKSLASH",
    "SEMICOLON",
    "QUOTE",
    "APOSTROPHE",
    "BRACKETLEFT",
    "BRACKETRIGHT",
    "TILDE",
    "GRAVE",
    "HASH",
    "ASTERISK",
    "AMPERSAND",
}


def validate_key_name(name):
    """파이썬 식별자 규칙으로 검사.
    유효하면 True, 아니면 False 반환."""
    if not isinstance(name, str) or not name:
        return False
    if not name.isidentifier():
        return False
    if keyword.iskeyword(name):
        return False
    return True


def validate_key_key(key):
    """단축키 문자열 검사.
    - 토큰은 공백으로만 구분(예: 'CTRL SHIFT A').
    - 'VK_' 접두사 허용(대소문자 무시).
    - 수정자 키만으로도 허용(예: 'CTRL' 또는 'ALT').
    - 일반키 허용: A-Z, 0-9, F1-F24, 그리고 _NAMED_KEYS에 정의된 이름들.
    유효하면 True, 아니면 False 반환."""
    if not isinstance(key, str) or not key.strip():
        return False

    tokens = [t for t in re.split(r"[\s]+", key.strip()) if t]
    if not tokens:
        return False

    for token in tokens:
        t = token.upper()
        if t.startswith("VK_"):
            t = t[3:]
        t = t.replace("-", "_").strip()
        if not t:
            return False

        if t in _MODIFIERS:
            continue

        if re.fullmatch(r"[A-Z]", t):
            continue

        if re.fullmatch(r"[0-9]", t):
            continue

        m = re.fullmatch(r"F([1-9][0-9]?)", t)
        if m:
            num = int(m.group(1))
            if 1 <= num <= 24:
                continue
            return False

        if t in _NAMED_KEYS:
            continue

        return False

    return True


def validate_key_pos_neg(poskey, negkey):
    """poskey와 negkey가 낱개 키 단위로 겹치지 않는지 검사하여 True/False 반환.
    주: 개별 키 문법 검사는 여기서 하지 않음(다른 곳에서 처리됨)."""

    def _canon_tokens(s):
        if not isinstance(s, str) or not s.strip():
            return set()
        toks = [t for t in re.split(r"[\s]+", s.strip()) if t]
        out = set()
        for token in toks:
            t = token.upper()
            if t.startswith("VK_"):
                t = t[3:]
            t = t.replace("-", "_").strip()
            if not t:
                continue

            if t in ("LEFT_CTRL", "RIGHT_CTRL", "CTRL", "CONTROL"):
                out.add("CTRL")
                continue
            if t in ("LEFT_SHIFT", "RIGHT_SHIFT", "SHIFT"):
                out.add("SHIFT")
                continue
            if t in ("LEFT_ALT", "RIGHT_ALT", "ALT", "ALTGR"):
                out.add("ALT")
                continue
            if t in ("OSKEY", "META", "CMD", "COMMAND", "WIN", "SUPER"):
                out.add("CMD")
                continue

            named_syn = {
                "BS": "BACKSPACE",
                "ESCAPE": "ESC",
                "RETURN": "ENTER",
                "DEL": "DELETE",
                "DOT": "PERIOD",
            }
            if t in named_syn:
                out.add(named_syn[t])
                continue

            if t in _NAMED_KEYS:
                out.add(t)
                continue

            if re.fullmatch(r"[A-Z]", t) or re.fullmatch(r"[0-9]", t):
                out.add(t)
                continue

            m = re.fullmatch(r"F([1-9][0-9]?)", t)
            if m:
                num = int(m.group(1))
                if 1 <= num <= 24:
                    out.add(f"F{num}")
                    continue

            out.add(t)
        return out

    pos_set = _canon_tokens(poskey)
    neg_set = _canon_tokens(negkey)

    # 한쪽이 비어있으면 겹침 없음으로 처리
    if not pos_set or not neg_set:
        return True

    # 낱개 키 단위로 겹치는지 검사
    return pos_set.isdisjoint(neg_set)
