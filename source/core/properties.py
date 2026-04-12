import bpy
from bpy.props import StringProperty, BoolProperty


def register():
    bpy.types.Scene.mte_import_path = StringProperty(name="불러오기", default="")
    bpy.types.Scene.mte_export_path = StringProperty(name="내보내기", default="")

    # 접기
    bpy.types.Scene.mte_show_paths = BoolProperty(name="경로 설정 탭", default=True)
    bpy.types.Scene.mte_show_keys = BoolProperty(name="키 설정 탭", default=True)


def unregister():
    del bpy.types.Scene.mte_show_keys
    del bpy.types.Scene.mte_show_paths
    del bpy.types.Scene.mte_export_path
    del bpy.types.Scene.mte_import_path
