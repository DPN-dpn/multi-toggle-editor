import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    CollectionProperty,
    IntProperty,
    EnumProperty,
)
from bpy.types import PropertyGroup

TYPE_ITEMS = [
    ("CYCLE", "Cycle", "값을 순환합니다"),
    ("TOGGLE", "Toggle", "켜기/끄기 전환"),
    ("HOLD", "Hold", "키를 누르고 있는 동안 활성화됩니다"),
]


class MTEKeyItem(PropertyGroup):
    name: StringProperty(name="이름", default="")
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
