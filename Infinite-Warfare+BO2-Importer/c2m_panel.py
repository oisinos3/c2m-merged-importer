import bpy_extras
import bpy
from bpy.types import Panel

class C2M_PT_Panel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "C2M"
    bl_category = "SHEILAN's Tools"

    def draw(self, context):
        layout = self.layout
        obj = context.object
        scene = context.scene
        sheilan_tools = scene.sheilan_tools
        
        col = layout.column()
        row = col.row(align=True)
        row.prop(sheilan_tools, 'c2m_objExport_path', text='Export path')
        row.operator("sheilan.file_selector", icon="FILE_FOLDER", text="")

        row = layout.row()
        col = row.column()
        col.operator("c2m.export_obj", text="Export map as FBX")