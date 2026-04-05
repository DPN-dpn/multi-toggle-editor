import bpy
from bpy.props import StringProperty


def register():
    bpy.types.Scene.mte_import_path = StringProperty(name="불러오기", default="")
    bpy.types.Scene.mte_export_path = StringProperty(name="내보내기", default="")


def unregister():
    del bpy.types.Scene.mte_export_path
    del bpy.types.Scene.mte_import_path
