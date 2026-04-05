# Blender 애드온 정보
bl_info = {
    "name": "멀티 토글 에디터",
    "author": "DPN",
    "version": (0, 1, 0),
    "blender": (3, 6, 23),
    "location": "3D 뷰 > 우측 UI 패널 > 멀티 토글 에디터",
    "description": "멀티 토글 에디터 애드온입니다.",
    "category": "Import-Export",
}

# 라이브러리 임포트
from .source import path, updator, editor, core


# 애드온 등록 함수
def register():
    core.register()
    path.register()
    editor.register()
    updator.register()


# 애드온 해제 함수
def unregister():
    updator.unregister()
    editor.unregister()
    path.unregister()
    core.unregister()


# 스크립트 직접 실행 시 등록
if __name__ == "__main__":
    register()
