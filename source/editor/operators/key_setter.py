import bpy
from bpy.types import Operator
from bpy.props import StringProperty
import re
from ...utils.validator import validate_key_name, validate_key_key, validate_key_pos_neg


def event_to_token(event):
    t = event.type.upper()
    # 마우스 관련 이벤트와 타이머 무시
    if t.endswith("MOUSE") or t in {"TIMER", "MOUSEMOVE", "INBETWEEN_MOUSEMOVE"}:
        return None

    if t in {
        "LEFT_CTRL",
        "RIGHT_CTRL",
        "LEFT_SHIFT",
        "RIGHT_SHIFT",
        "LEFT_ALT",
        "RIGHT_ALT",
        "CTRL",
        "SHIFT",
        "ALT",
        "OSKEY",
    }:
        return None
    if t.endswith("_ARROW"):
        return t[:-6]
    if t.startswith("NUMPAD_"):
        s = t[7:]
        if s.isdigit():
            return s
        return s
    num_map = {
        "ZERO": "0",
        "ONE": "1",
        "TWO": "2",
        "THREE": "3",
        "FOUR": "4",
        "FIVE": "5",
        "SIX": "6",
        "SEVEN": "7",
        "EIGHT": "8",
        "NINE": "9",
    }
    if t in num_map:
        return num_map[t]
    if re.fullmatch(r"F([1-9][0-9]?)", t):
        return t
    if re.fullmatch(r"[A-Z]", t):
        return t
    tt = t.replace("-", "_").replace("_", "")
    return tt if tt else None


def handle_key_capture(op, context, event, target_attr, header_clear=True):
    area = getattr(op, "_area", None)

    # ESC로 취소
    if event.type == "ESC" and event.value == "PRESS":
        if area and header_clear:
            area.header_text_set(None)
        if hasattr(op, "_tokens"):
            del op._tokens
        if hasattr(op, "_mods"):
            del op._mods
        op.report({"INFO"}, "키 캡처 취소")
        return {"CANCELLED"}

    if event.type in {"TIMER", "MOUSEMOVE", "INBETWEEN_MOUSEMOVE"}:
        return {"RUNNING_MODAL"}

    if event.value != "PRESS":
        return {"RUNNING_MODAL"}

    # Enter로 확정 (modifier만 있어도 허용)
    if event.type in {"RET", "NUMPAD_ENTER"}:
        tokens = getattr(op, "_tokens", [])
        mods = getattr(op, "_mods", [])
        if not tokens and not mods:
            return {"RUNNING_MODAL"}
        combo = " ".join((mods or []) + (tokens or []))

        if not validate_key_key(combo):
            op.report({"WARNING"}, f"유효하지 않은 단축키: {combo}")
            return {"RUNNING_MODAL"}

        scene = context.scene
        idx = scene.mte_keys_index
        if 0 <= idx < len(scene.mte_keys):
            item = scene.mte_keys[idx]

            # pos/neg 조합 검사: 새로 저장할 값으로 검사
            if target_attr == "poskey":
                new_pos = combo
                new_neg = getattr(item, "negkey", "")
            else:
                new_pos = getattr(item, "poskey", "")
                new_neg = combo

            if not validate_key_pos_neg(new_pos, new_neg):
                # 캡처를 취소하지 않고 경고만 표시, 상태 유지하여 계속 입력 가능하게 함
                op.report({"WARNING"}, "긍정/부정 키가 서로 겹칩니다.")
                if area:
                    current = " ".join((mods or []) + (tokens or []))
                    area.header_text_set(f"단축키: {current} (Enter: 완료, Esc: 취소)")
                return {"RUNNING_MODAL"}

            try:
                setattr(item, target_attr, combo)
            except Exception as e:
                op.report({"ERROR"}, f"단축키 저장 실패: {e}")
                if area and header_clear:
                    area.header_text_set(None)
                if hasattr(op, "_tokens"):
                    del op._tokens
                if hasattr(op, "_mods"):
                    del op._mods
                return {"CANCELLED"}

        if area and header_clear:
            area.header_text_set(None)

        # UI 갱신
        for window in context.window_manager.windows:
            for a in window.screen.areas:
                if a.type == "VIEW_3D":
                    for region in a.regions:
                        if region.type == "UI":
                            region.tag_redraw()

        op.report({"INFO"}, f"단축키 설정: {combo}")
        if hasattr(op, "_tokens"):
            del op._tokens
        if hasattr(op, "_mods"):
            del op._mods
        return {"FINISHED"}

    # 내부 상태 보장
    if not hasattr(op, "_tokens"):
        op._tokens = []
    if not hasattr(op, "_mods"):
        op._mods = []

    # modifier 키 자체를 눌렀을 때는 해당 modifier를 토글(추가/제거)
    t = event.type.upper()
    mod_map = {
        "LEFT_CTRL": "CTRL",
        "RIGHT_CTRL": "CTRL",
        "CTRL": "CTRL",
        "LEFT_SHIFT": "SHIFT",
        "RIGHT_SHIFT": "SHIFT",
        "SHIFT": "SHIFT",
        "LEFT_ALT": "ALT",
        "RIGHT_ALT": "ALT",
        "ALT": "ALT",
        "OSKEY": "CMD",
    }
    if t in mod_map:
        mod = mod_map[t]
        if mod in op._mods:
            op._mods.remove(mod)
        else:
            op._mods.append(mod)
        if area:
            current = (
                " ".join(op._mods + op._tokens) if op._mods else " ".join(op._tokens)
            )
            area.header_text_set(f"단축키: {current} (Enter: 완료, Esc: 취소)")
        return {"RUNNING_MODAL"}

    # 키를 누를 때 해당 modifier들이 눌려있다면 자동으로 포함 (중복 방지)
    if getattr(event, "ctrl", False) and "CTRL" not in op._mods:
        op._mods.append("CTRL")
    if getattr(event, "shift", False) and "SHIFT" not in op._mods:
        op._mods.append("SHIFT")
    if getattr(event, "alt", False) and "ALT" not in op._mods:
        op._mods.append("ALT")
    if getattr(event, "oskey", False) and "CMD" not in op._mods:
        op._mods.append("CMD")

    token = event_to_token(event)
    if not token:
        return {"RUNNING_MODAL"}

    # 같은 키를 다시 누르면 제거(토글), 없으면 추가
    if token in op._tokens:
        op._tokens.remove(token)
    else:
        op._tokens.append(token)

    if area:
        current = " ".join(op._mods + op._tokens) if op._mods else " ".join(op._tokens)
        area.header_text_set(f"단축키: {current} (Enter: 완료, Esc: 취소)")

    return {"RUNNING_MODAL"}


class MTE_OT_add_key(Operator):
    bl_idname = "mte.add_key"
    bl_label = "키 추가"

    def execute(self, context):
        scene = context.scene

        # 기본 이름 생성
        base = "New_Key"
        existing = {k.name for k in scene.mte_keys}
        name = base
        i = 1
        while name in existing:
            name = f"{base}_{i}"
            i += 1

        # 키 추가
        item = scene.mte_keys.add()
        item.name = name
        item.key = ""
        scene.mte_keys_index = len(scene.mte_keys) - 1
        return {"FINISHED"}


class MTE_OT_remove_key(Operator):
    bl_idname = "mte.remove_key"
    bl_label = "키 제거"

    def execute(self, context):
        scene = context.scene
        idx = scene.mte_keys_index
        if len(scene.mte_keys) > 0:
            scene.mte_keys.remove(idx)
            # clamp index
            if idx >= len(scene.mte_keys):
                scene.mte_keys_index = max(0, len(scene.mte_keys) - 1)
        return {"FINISHED"}


class MTE_OT_up_key(Operator):
    bl_idname = "mte.up_key"
    bl_label = "키 위로 이동"

    def execute(self, context):
        scene = context.scene
        idx = scene.mte_keys_index
        if idx > 0:
            scene.mte_keys.move(idx, idx - 1)
            scene.mte_keys_index -= 1
        return {"FINISHED"}


class MTE_OT_down_key(Operator):
    bl_idname = "mte.down_key"
    bl_label = "키 아래로 이동"

    def execute(self, context):
        scene = context.scene
        idx = scene.mte_keys_index
        if idx < len(scene.mte_keys) - 1:
            scene.mte_keys.move(idx, idx + 1)
            scene.mte_keys_index += 1
        return {"FINISHED"}


class MTE_OT_positive_key_capture(Operator):
    bl_idname = "mte.positive_key_capture"
    bl_label = "긍정 키 캡처"
    target: StringProperty()

    def invoke(self, context, event):
        self._area = context.area
        self._tokens = []
        self._mods = []
        if self._area:
            self._area.header_text_set("단축키를 누르세요 (Enter: 완료, Esc: 취소)")
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        return handle_key_capture(self, context, event, self.target)


class MTE_OT_negative_key_capture(Operator):
    bl_idname = "mte.negative_key_capture"
    bl_label = "부정 키 캡처"
    target: StringProperty()

    def invoke(self, context, event):
        self._area = context.area
        self._tokens = []
        self._mods = []
        if self._area:
            self._area.header_text_set("단축키를 누르세요 (Enter: 완료, Esc: 취소)")
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        return handle_key_capture(self, context, event, self.target)


classes = (
    MTE_OT_add_key,
    MTE_OT_remove_key,
    MTE_OT_up_key,
    MTE_OT_down_key,
    MTE_OT_positive_key_capture,
    MTE_OT_negative_key_capture,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
