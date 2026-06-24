import bpy
from bpy.props import BoolProperty
import importlib
from .mod_ini_processor import process_export_mod_ini, process_import_mod_ini

class MULTI_TOGGLE_PT_ExportOptions(bpy.types.Panel):
    bl_label = "멀티 토글 옵션"
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_category = "XXMI"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        if not space:
            return False
        active_op = getattr(space, "active_operator", None)
        if not active_op:
            return False
        op_id = getattr(active_op, "bl_idname", "")
        # 보통 3DMigoto export 오퍼레이터 id
        return op_id in (
            "export_mesh.migoto_raw_buffers",
            "EXPORT_MESH_OT_migoto_raw_buffers",
            "export_scene.xxmi",
        )

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        layout.prop(wm, "multi_toggle_export_xxmi")


class MULTI_TOGGLE_PT_ImportOptions(bpy.types.Panel):
    bl_label = "멀티 토글 옵션"
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_category = "XXMI"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        if not space:
            return False
        active_op = getattr(space, "active_operator", None)
        if not active_op:
            return False
        op_id = getattr(active_op, "bl_idname", "")
        return op_id in (
            "import_mesh.migoto_raw_buffers",
            "IMPORT_MESH_OT_migoto_raw_buffers",
            "import_scene.xxmi",
        )

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        layout.prop(wm, "multi_toggle_import_xxmi")


# =========================================================
# Export Monkey Patch Logic
# =========================================================

def _apply_xxmi_export_adapter():
    try:
        mi_exp = importlib.import_module("XXMITools.migoto.export_ops")
    except Exception:
        return
        
    if hasattr(mi_exp, "_mt_orig_export_3dmigoto"):
        return
        
    # 원본 함수 백업 (여기서는 메인 export 함수가 export_3dmigoto 라고 가정)
    if hasattr(mi_exp, "export_3dmigoto"):
        mi_exp._mt_orig_export_3dmigoto = mi_exp.export_3dmigoto
        
        def _mt_export_3dmigoto(*args, **kwargs):
            # 1. 원본 함수 실행
            result = mi_exp._mt_orig_export_3dmigoto(*args, **kwargs)
            
            # 2. 체크박스 확인
            wm = bpy.context.window_manager
            if getattr(wm, "multi_toggle_export_xxmi", False):
                # 3. 여기서 생성된 Mod.ini를 찾아서 후처리 로직(Piggybacking) 수행
                # 보통 XXMITools 내보내기 경로를 인자로 받거나 context에서 찾음.
                # 임시로 현재 디렉토리의 Mod.ini를 찾는다고 가정. (수정 필요)
                import os
                
                # operator 속성이나 kwargs에서 파일 경로를 추출해야 함
                # 임시 하드코딩된 예제:
                ini_path = os.path.join(bpy.path.abspath("//"), "Mod.ini")
                
                process_export_mod_ini(
                    ini_path, 
                    bpy.context.scene.multi_toggle_globals, 
                    bpy.context.scene.objects
                )
                
            return result
            
        mi_exp.export_3dmigoto = _mt_export_3dmigoto

def _remove_xxmi_export_adapter():
    try:
        mi_exp = importlib.import_module("XXMITools.migoto.export_ops")
    except Exception:
        return
    if hasattr(mi_exp, "_mt_orig_export_3dmigoto"):
        mi_exp.export_3dmigoto = mi_exp._mt_orig_export_3dmigoto
        delattr(mi_exp, "_mt_orig_export_3dmigoto")


# =========================================================
# Import Monkey Patch Logic
# =========================================================

def _apply_xxmi_import_adapter():
    try:
        mi_imp = importlib.import_module("XXMITools.migoto.import_ops")
    except Exception:
        return
        
    if hasattr(mi_imp, "_mt_orig_import_3dmigoto_vb_ib"):
        return
        
    # 원본 함수 백업
    if hasattr(mi_imp, "import_3dmigoto_vb_ib"):
        mi_imp._mt_orig_import_3dmigoto_vb_ib = mi_imp.import_3dmigoto_vb_ib
        
        def _mt_import_3dmigoto_vb_ib(*args, **kwargs):
            # 1. 원본 함수 실행 전이나 후에 파싱 로직 수행 가능
            wm = bpy.context.window_manager
            if getattr(wm, "multi_toggle_import_xxmi", False):
                # Import 시 선택된 경로 기반으로 Mod.ini 찾아서 파싱
                # 임시 하드코딩
                import os
                ini_path = os.path.join(bpy.path.abspath("//"), "Mod.ini")
                process_import_mod_ini(ini_path, bpy.context)
                
            return mi_imp._mt_orig_import_3dmigoto_vb_ib(*args, **kwargs)
            
        mi_imp.import_3dmigoto_vb_ib = _mt_import_3dmigoto_vb_ib

def _remove_xxmi_import_adapter():
    try:
        mi_imp = importlib.import_module("XXMITools.migoto.import_ops")
    except Exception:
        return
    if hasattr(mi_imp, "_mt_orig_import_3dmigoto_vb_ib"):
        mi_imp.import_3dmigoto_vb_ib = mi_imp._mt_orig_import_3dmigoto_vb_ib
        delattr(mi_imp, "_mt_orig_import_3dmigoto_vb_ib")


classes = (
    MULTI_TOGGLE_PT_ExportOptions,
    MULTI_TOGGLE_PT_ImportOptions,
)

def register():
    if not hasattr(bpy.types.WindowManager, "multi_toggle_export_xxmi"):
        bpy.types.WindowManager.multi_toggle_export_xxmi = BoolProperty(
            name="멀티 토글 적용하여 내보내기",
            description="Mod.ini 파일에 멀티 토글 규칙을 적용하여 내보냅니다",
            default=True,
        )
    if not hasattr(bpy.types.WindowManager, "multi_toggle_import_xxmi"):
        bpy.types.WindowManager.multi_toggle_import_xxmi = BoolProperty(
            name="멀티 토글 불러오기",
            description="Mod.ini 파일을 읽어 블랜더의 멀티 토글 매니저를 복구합니다",
            default=True,
        )
        
    for cls in classes:
        bpy.utils.register_class(cls)
        
    _apply_xxmi_export_adapter()
    _apply_xxmi_import_adapter()

def unregister():
    _remove_xxmi_export_adapter()
    _remove_xxmi_import_adapter()
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    if hasattr(bpy.types.WindowManager, "multi_toggle_export_xxmi"):
        del bpy.types.WindowManager.multi_toggle_export_xxmi
    if hasattr(bpy.types.WindowManager, "multi_toggle_import_xxmi"):
        del bpy.types.WindowManager.multi_toggle_import_xxmi
