import bpy
from bpy.types import Operator
from bpy.props import StringProperty
import re
from ...utils.validator import validate_key_key


def event_to_token(event):
    t = event.type.upper()
    if t.endswith("_MOUSE") or t in {"TIMER", "INBETWEEN_MOUSEMOVE"}:
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


def handle_key_capture(
    op, context, event, target_attr, validator=validate_key_key, header_clear=True
):
    area = getattr(op, "_area", None)

    # ESC로 취소
    if event.type == "ESC" and event.value == "PRESS":
        if area and header_clear:
            area.header_text_set(None)
        op.report({"INFO"}, "키 캡처 취소")
        return {"CANCELLED"}

    if event.type in {"TIMER", "MOUSEMOVE", "INBETWEEN_MOUSEMOVE"}:
        return {"RUNNING_MODAL"}

    if event.value != "PRESS":
        return {"RUNNING_MODAL"}

    token = event_to_token(event)

    mods = []
    if getattr(event, "ctrl", False):
        mods.append("CTRL")
    if getattr(event, "shift", False):
        mods.append("SHIFT")
    if getattr(event, "alt", False):
        mods.append("ALT")
    if getattr(event, "oskey", False):
        mods.append("CMD")

    if not token:
        return {"RUNNING_MODAL"}

    combo = " ".join(mods + [token]) if mods else token

    if not validator(combo):
        op.report({"WARNING"}, f"유효하지 않은 단축키: {combo}")
        return {"RUNNING_MODAL"}

    scene = context.scene
    idx = scene.mte_keys_index
    if 0 <= idx < len(scene.mte_keys):
        item = scene.mte_keys[idx]
        try:
            setattr(item, target_attr, combo)
        except Exception as e:
            op.report({"ERROR"}, f"단축키 저장 실패: {e}")
            if area and header_clear:
                area.header_text_set(None)
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
    return {"FINISHED"}


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


class MTE_OT_key_positive_capture(Operator):
    bl_idname = "mte.key_positive_capture"
    bl_label = "긍정 키 캡처"
    target: StringProperty()

    def invoke(self, context, event):
        self._area = context.area
        if self._area:
            self._area.header_text_set("단축키를 누르세요 (Esc: 취소)")
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        return handle_key_capture(self, context, event, self.target)


class MTE_OT_key_negative_capture(Operator):
    bl_idname = "mte.key_negative_capture"
    bl_label = "부정 키 캡처"
    target: StringProperty()

    def invoke(self, context, event):
        self._area = context.area
        if self._area:
            self._area.header_text_set("단축키를 누르세요 (Esc: 취소)")
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        return handle_key_capture(self, context, event, self.target)


classes = (
    MTE_OT_add_key,
    MTE_OT_remove_key,
    MTE_OT_up_key,
    MTE_OT_down_key,
    MTE_OT_key_positive_capture,
    MTE_OT_key_negative_capture,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
