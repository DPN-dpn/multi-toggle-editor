import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    CollectionProperty,
    IntProperty,
    EnumProperty,
)
from bpy.types import PropertyGroup
from ..utils.validator import validate_key_name

_name_update_lock = False

TYPE_ITEMS = [
    ("CYCLE", "Cycle", "값을 순환합니다"),
    ("TOGGLE", "Toggle", "켜기/끄기 전환"),
    ("HOLD", "Hold", "키를 누르고 있는 동안 활성화됩니다"),
]


def _show_name_error(context, title, message):
    if not context or not hasattr(context, "window_manager"):
        return

    def _draw(self, ctx):
        self.layout.label(text=message)

    context.window_manager.popup_menu(_draw, title=title, icon="ERROR")


def _on_name_update(self, context):
    global _name_update_lock
    if _name_update_lock:
        return

    new = getattr(self, "name", "") or ""
    # 문법 검사
    if not validate_key_name(new):
        prev = getattr(self, "_last_valid_name", "")
        _name_update_lock = True
        try:
            self.name = prev
        finally:
            _name_update_lock = False
        _show_name_error(
            context, "이름 검사 실패", "이름이 유효하지 않습니다."
        )
        return

    # 중복 검사 (같은 Scene.mte_keys 내 다른 항목과 이름이 겹치면 거부)
    scene = context.scene if context else getattr(self, "id_data", None)
    if scene:
        try:
            my_ptr = self.as_pointer()
        except Exception:
            my_ptr = id(self)
        for item in scene.mte_keys:
            try:
                item_ptr = item.as_pointer()
            except Exception:
                item_ptr = id(item)
            if item_ptr != my_ptr and getattr(item, "name", "") == new:
                prev = getattr(self, "_last_valid_name", "")
                _name_update_lock = True
                try:
                    self.name = prev
                finally:
                    _name_update_lock = False
                _show_name_error(
                    context, "이름 중복", "다른 키 항목과 이름이 겹칩니다."
                )
                return

    # 유효하면 기록
    self._last_valid_name = new


class MTEKeyItem(PropertyGroup):
    name: StringProperty(name="이름", default="", update=_on_name_update)
    poskey: StringProperty(name="긍정 키", default="")
    negkey: StringProperty(name="부정 키", default="")
    type: EnumProperty(name="타입", items=TYPE_ITEMS, default="CYCLE")
    warp: BoolProperty(name="워프", default=True)
    num: IntProperty(name="단계", default=2, min=2)


def register():
    # 접기
    bpy.types.Scene.mte_show_paths = BoolProperty(name="경로 설정 탭", default=True)
    bpy.types.Scene.mte_show_keys = BoolProperty(name="키 설정 탭", default=True)
    bpy.types.Scene.mte_show_presets = BoolProperty(name="프리셋 탭", default=True)

    # 경로 설정
    bpy.types.Scene.mte_import_path = StringProperty(name="불러오기", default="")
    bpy.types.Scene.mte_export_path = StringProperty(name="내보내기", default="")

    # 키 목록
    bpy.utils.register_class(MTEKeyItem)
    bpy.types.Scene.mte_keys = CollectionProperty(type=MTEKeyItem)
    bpy.types.Scene.mte_keys_index = IntProperty(name="키 목록", default=0)


def unregister():
    del bpy.types.Scene.mte_keys_index
    del bpy.types.Scene.mte_keys
    bpy.utils.unregister_class(MTEKeyItem)

    del bpy.types.Scene.mte_export_path
    del bpy.types.Scene.mte_import_path

    del bpy.types.Scene.mte_show_presets
    del bpy.types.Scene.mte_show_keys
    del bpy.types.Scene.mte_show_paths
