import os
import math
from .BinaryReader import*

CoDVersions = {
	0 : "modern_warfare",
	1 : "world_at_war",
	2 : "modern_warfare_2",
	3 : "black_ops_1",
	4 : "modern_warfare_3",
	5 : "black_ops_2",
	6 : "ghosts",
	7 : "advanced_warfare",
	8 : "black_ops_3",
	9 : "modern_warfare_rm",
	10: "infinite_warfare",
	11 : "world_war_2",
    12 : "black_ops_4",
    13 : "modern_warfare_4",
    14 : "black_ops_5"
}
CoDLights = {
    1 : "SUN",
    2 : "SPOT",
    3 : "SPOT",
    4 : "SPOT",
    5 : "POINT",
}
CoDMaterialSettings = {
    0 : "colorTint",
    1 : "detailScale",
    2 : "detailScale1",
    3 : "detailScale2",
    4 : "detailScale3",
    5 : "specColorTint",
    6 : "rowCount",
    7 : "columnCount",
    8 : "imageTime",
}
class CoDMap(object):
    Name = ""
    AmbientColor = []
    Version = ""
    Objects = []
    ModelInstances = []
    Lights = []
    Materials = {}
    def __init__(self, file):
        self.Objects = []
        self.ModelInstances = []
        self.Lights = []
        self.Materials = {}
        # Read header
        magic = read_bytes(file, 3)
        file_version = read_byte(file)
        self.Version = CoDVersions[read_byte(file)]
        print(self.Version)
        # Check magic
        if magic[0] != 67 and magic[1] != 50 and magic[2] != 77:
            print("Invalid magic, expected \"C2M\"")
            return

        # Read map name
        self.Name = read_string(file)
        # Read objects
        objectCount = read_uint(file)
        for x in range(objectCount):
            self.Objects.append(CoDMesh(file))
        materialCount = read_uint(file)
        for x in range(materialCount):
            material = CoDMaterial(file)
            self.Materials[material.Name] = material
        # Read model instances
        instanceCount = read_uint(file)
        for x in range(instanceCount):
            self.ModelInstances.append(CoDModelInstance(file))
        # Read lights
        lightCount = read_uint(file)
        for x in range(lightCount):
            light = CoDLight(file)
            self.Lights.append(light)
class CoDSurface(object):
    Name = ""
    Faces = []
    Materials = []
    
    def __init__(self, file):
        self.Name = read_string(file)
        self.Faces = []
        self.Materials = []

        materialCount = read_uint(file)
        for x in range(materialCount):
            self.Materials.append(read_string(file))
        face_count = read_uint(file)
        for f in range(face_count):
            faceVerts = []
            # Read indices of triangle -- position,normal,uv,color
            for x in range(3):
                vertex_index = read_uint(file)
                faceVerts.append(vertex_index)
            # Add face to surface
            self.Faces.append(faceVerts)
class CoDMesh(object):
    Name = ""
    Vertices = []
    Normals = []
    UVs = []
    Colors = []
    Surfaces = []
    IS_XMODEL = False
    def __init__(self, file):
        self.Name = read_string(file)
        self.Vertices = []
        self.Normals = []
        self.UVs = []
        self.Colors = []
        self.Surfaces = []
        self.IS_XMODEL = read_bool(file)

        # Read vertices
        vertex_count = read_uint(file)
        for i in range(vertex_count):
            # Read vertex & add it
            self.Vertices.append([read_float(file),
                                  read_float(file),
                                  read_float(file)])
        # Read normals
        normal_count = read_uint(file)
        for i in range(normal_count):
            # Read normal & add it
            self.Normals.append([read_float(file),
                                 read_float(file),
                                 read_float(file)])
        # Read UVs
        uv_count = read_uint(file)
        for i in range(uv_count):
            # Read UV & add it
            self.UVs.append([read_float(file),
                             read_float(file)])
        # Read Colors
        color_count = read_uint(file)
        for i in range(color_count):
            # Read normal & add it
            self.Colors.append([(read_byte(file))/255,
                                (read_byte(file))/255,
                                (read_byte(file))/255,
                                (read_byte(file))/255])
        # Read Surfaces
        surf_count = read_uint(file)
        for i in range(surf_count):
            # Add surface
            self.Surfaces.append(CoDSurface(file))
class CoDModelInstance(object):
    Name = ""
    Position = ()
    Rotation_degrees = ()
    Rotation_euler = ()
    Scale = ()
    def __init__(self, file):
        # Read name
        self.Name = read_string(file)
        # Read position
        self.Position = (read_float(file), read_float(file), read_float(file))
        # Read rotation (default is degrees)
        self.Rotation_degrees = (read_float(file), read_float(file), read_float(file))
        # Make euler variation
        self.Rotation_euler = (math.radians(self.Rotation_degrees[0]),
                               math.radians(self.Rotation_degrees[1]),
                               math.radians(self.Rotation_degrees[2]))
        # Read scale & apply
        scale = read_float(file)
        self.Scale = (scale, scale, scale)

class CoDMaterial(object):
    Name = ""
    TechSet = ""
    SortKey = 0
    Textures = []
    Settings = {}
    def __init__(self, file):
        # Read material name
        self.Name = read_string(file)
        self.TechSet = read_string(file)
        self.SortKey = read_byte(file)
        self.Textures = []
        self.Settings = {}
        # Read image count
        imageCount = read_byte(file)
        # Read images
        for i in range(imageCount):
            self.Textures.append(CoDTexture(file))
        # Read settings
        settingsCount = read_byte(file)
        for i in range(settingsCount):
            setting = CoDMaterialSettings[read_byte(file)]
            value = read_string(file)
            self.Settings[setting] = value
class CoDTexture(object):
    Name = ""
    TexType = ""
    def __init__(self, file):
        # Read texture name
        self.Name = read_string(file)
        # Read texture type
        self.TexType = read_string(file)

class CoDLight(object):
    Type = ""
    Origin = []
    Direction = []
    Color = []
    Angles = []
    Radius = 0.0
    CosHalfFovOuter = 0.0
    CosHalfFovInner = 0.0
    dAttenuation = 0.0
    def __init__(self, file):
        self.Type = CoDLights[read_byte(file)]
        self.Origin = (read_float(file), read_float(file), read_float(file))
        self.Direction = [read_float(file), read_float(file), read_float(file)]
        self.Angles = (read_float(file), read_float(file), read_float(file))
        self.Color = [read_float(file), read_float(file), read_float(file), read_float(file)]
        self.Radius = read_float(file)
        self.CosHalfFovOuter = read_float(file)
        self.CosHalfFovInner = read_float(file)
        self.dAttenuation = read_float(file)