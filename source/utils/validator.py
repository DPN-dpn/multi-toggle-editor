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
    - 수정자 키만으로는 안됨(최소 하나의 일반키 필요).
    - 일반키 허용: A-Z, 0-9, F1-F24, 그리고 _NAMED_KEYS에 정의된 이름들.
    유효하면 True, 아니면 False 반환."""
    if not isinstance(key, str) or not key.strip():
        return False

    tokens = [t for t in re.split(r"[\s]+", key.strip()) if t]
    if not tokens:
        return False

    has_regular = False
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
            has_regular = True
            continue

        if re.fullmatch(r"[0-9]", t):
            has_regular = True
            continue

        m = re.fullmatch(r"F([1-9][0-9]?)", t)
        if m:
            num = int(m.group(1))
            if 1 <= num <= 24:
                has_regular = True
                continue
            return False

        if t in _NAMED_KEYS:
            has_regular = True
            continue

        return False

    return has_regular
