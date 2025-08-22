import bpy,os
from bpy.types import Operator
from bpy.props import *
from bpy_extras.io_utils import ImportHelper, ExportHelper
from .reader.C2MReader import CoDMap
from .c2m_import import *


class WMFileSelector(Operator, ExportHelper):
    bl_idname = "sheilan.file_selector"
    bl_label = "Choose folder"

    filename_ext = ""

    def execute(self, context):
        fdir = self.properties.filepath
        context.scene.sheilan_tools.c2m_objExport_path = os.path.dirname(fdir)
        return{'FINISHED'}

class SHEILAN_PROPERTIES(bpy.types.PropertyGroup):
    c2m_objExport_path : bpy.props.StringProperty(name= "Enter Text")

class C2M_ExportObj(Operator):
    bl_idname = "c2m.export_obj"
    bl_label = "Export MAP to FBX"
    bl_description = "Export the loaded C2M map to FBX"
    globalFPath: bpy.props.StringProperty(
        subtype="FILE_PATH",
        name = "Folder QC/SMD files",
        description = "Folder for import",
    )
    @classmethod
    def poll(cls, context):
        obj = context.object

        if obj is not None:
            if obj.mode == "OBJECT":
                return True

        return False

    def execute(self, context):
        exportPath = context.scene.sheilan_tools.c2m_objExport_path
        collections = context.collection.children
        col_mapGeo = collections['mapGeometry']
        col_models = collections['Model Instances']
        for o in col_mapGeo.all_objects:
            o.select_set(True)
        for o in col_models.all_objects:
            o.select_set(True)

            
        bpy.ops.export_scene.fbx(filepath = os.path.join(exportPath, context.collection.name + ".fbx"), use_selection=True)
        
        return{"FINISHED"}

class C2M_ImportSettings(object):
     import_props = False
     import_materials = False
     material_type = ""
     import_lights = False
     game = ""
     def __init__(self, Import_Props, Import_Materials, Material_Type, Import_Lights):
         self.import_props = Import_Props
         self.import_materials = Import_Materials
         self.material_type = Material_Type
         self.import_lights = Import_Lights
     
class C2M_ImportFile(Operator,ImportHelper):
    bl_label="Import CoD Map"
    bl_idname="c2m.import"

    filter_glob       : StringProperty(default="*.c2m", options={'HIDDEN'},)
    import_props      : BoolProperty(name="Import Props", default=True)
    import_materials  : BoolProperty(name="Import Materials", default=True)
    material_type     : EnumProperty(name="Material type", items=[("CoD Shader", "CoD Shader", ""), ("simple (Wavefront OBJ)", "simple (Wavefront OBJ)", "")])
    import_lights     :  BoolProperty(name="Import Lights", default=True)
    
    def execute(self,context):
        import_settings = C2M_ImportSettings(self.import_props, self.import_materials, self.material_type, self.import_lights)
        # Get file path
        file_path = bpy.path.abspath(self.properties.filepath)
        # Load C2M file
        c2m_file=open(file_path, "rb")
        # Create CoDMap object
        mapObject = CoDMap(c2m_file)
        # Get images folder
        images_path = os.path.join(file_path.split("\\exported")[0], "exported_images", mapObject.Version, )
        import_settings.game = mapObject.Version
        # Create map in Blender
        createMap(mapObject, images_path, import_settings)
        c2m_file.close()
        return{"FINISHED"}
        
def import_c2m_menu(self,context):
    self.layout.operator(C2M_ImportFile.bl_idname,text="CoD Map (.c2m)")