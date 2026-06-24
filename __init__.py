bl_info = {
    "name": "3DMigoto 멀티 토글 매니저",
    "author": "Antigravity",
    "version": (0, 1, 0),
    "blender": (3, 6, 23),
    "location": "View3D > N-Panel > 멀티 토글",
    "description": "3DMigoto 모드용 멀티 토글과 메쉬 가시성을 쉽게 관리합니다.",
    "warning": "",
    "doc_url": "",
    "category": "3D View",
}

if "bpy" in locals():
    import importlib
    importlib.reload(core)
    importlib.reload(live_preview)
    importlib.reload(properties)
    
    importlib.reload(global_toggles)
    importlib.reload(gt_operators)
    importlib.reload(gt_panel)
    
    importlib.reload(mesh_rules)
    importlib.reload(mr_operators)
    importlib.reload(mr_panel)
    
    importlib.reload(io)
    importlib.reload(io.operators)
    importlib.reload(io.panel)
    
    importlib.reload(updator)
    importlib.reload(up_operators)
    importlib.reload(up_panel)
else:
    import bpy

# 1. 코어 임포트
from .source import core
from .source.core import properties
from .source.core import live_preview

# 2. 패널 및 기능 폴더 임포트
from .source import global_toggles
from .source.global_toggles import operators as gt_operators
from .source.global_toggles import panel as gt_panel

from .source import mesh_rules
from .source.mesh_rules import operators as mr_operators
from .source.mesh_rules import panel as mr_panel

from .source import io
from .source.io import operators as io_operators
from .source.io import panel as io_panel

from .source import updator
from .source.updator import operators as up_operators
from .source.updator import panel as up_panel

modules = [
    properties,
    io_panel,
    gt_operators,
    gt_panel,
    mr_operators,
    mr_panel,
    io_operators,
    up_operators,
    up_panel,
]

def register():
    for mod in modules:
        if hasattr(mod, "register"):
            mod.register()

def unregister():
    for mod in reversed(modules):
        if hasattr(mod, "unregister"):
            mod.unregister()

if __name__ == "__main__":
    register()
