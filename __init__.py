bl_info = {
    "name": "멀티 토글 매니저",
    "author": "DPN",
    "version": (0, 2, 0),
    "blender": (2, 80, 0),
    "location": "3D 뷰 > 우측 UI 패널 > 멀티 토글",
    "description": "XXMI 모드의 멀티 토글을 쉽게 관리합니다.",
    "category": "3D View",
}

# 임포트
from . import source

def register():
    source.register()

def unregister():
    source.unregister()

if __name__ == "__main__":
    register()
