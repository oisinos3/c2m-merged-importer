import bpy,bmesh
import os
import array
from math import *
from mathutils import *
from .materials.basic import *

def createMap(c2m_map, image_path, settings):
    """
    General functions used to create a map
    """
    def NormalFlipYNodeGroup():
        # Create a group
        node_group = bpy.data.node_groups.new("DirectXNormalMap", 'ShaderNodeTree')
        nodes = node_group.nodes
        links = node_group.links
        # Create input/output nodes
        group_inputs = nodes.new('NodeGroupInput')
        group_inputs.location = (0, -250)
        group_outputs = nodes.new('NodeGroupOutput')
        group_outputs.location = (600, -250)
        node_group.inputs.new('NodeSocketColor','DirectXNormal')
        node_group.outputs.new('NodeSocketColor','Normal')

        # Separate DX Normal
        sepRGB_node = nodes.new('ShaderNodeSeparateRGB')
        sepRGB_node.location = (150, -250)
        links.new(group_inputs.outputs[0], sepRGB_node.inputs[0])
        # Invert node for Y channel
        node_invert = nodes.new('ShaderNodeInvert')
        node_invert.location = (250, 0)
        links.new(sepRGB_node.outputs[1], node_invert.inputs[1])
        # Make new RGB with inverted Y
        combRGB_node = nodes.new('ShaderNodeCombineRGB')
        node_invert.location = (450, -250)
        links.new(sepRGB_node.outputs[0], combRGB_node.inputs[0])
        links.new(node_invert.outputs[0], combRGB_node.inputs[1])
        links.new(sepRGB_node.outputs[2], combRGB_node.inputs[2])
        links.new(combRGB_node.outputs[0], group_outputs.inputs[0])
    def createMesh(meshObject, parent, map_materials, game):
        # Create mesh group
        meshCollection = bpy.data.collections.new(meshObject.Name)
        
        # Assign to correct collection & group
        parent.children.link(meshCollection)
        # List for surfaces & surface data
        objects = []
        objects_data = []
        # Create surfaces
        for surface in meshObject.Surfaces:
            # Create new mesh object in the scene
            mesh = bmesh.new()
            surf_sortkey = map_materials[surface.Materials[0]].SortKey
            if surf_sortkey > 0 and settings.material_type == "simple (Wavefront OBJ)":
                continue
            data = bpy.data.meshes.new(name=surface.Name)
            obj = bpy.data.objects.new(name=surface.Name,object_data=data)
            meshCollection.objects.link(obj)
            # Create VC & UV layers
            uvSets = []
            for i in range(len(surface.Materials)):
                uvSets.append(mesh.loops.layers.uv.new())
            vcLayer = mesh.loops.layers.color.new()
            # List for normal data
            normals = []
            # Loop over surface faces
            for face in surface.Faces:
                # Create lists for data
                verts = []
                faceUVs = []
                faceVCs = []
                faceLayerVCs = []
                faceLayerUVs = []
                # Loop over face indices
                for x in range(3):
                    # Create new vertex
                    vert = mesh.verts.new()
                    # Get vertex index
                    vertexIndex = face[x]
                    # Read index data
                    vertex = Vector((inch2meter(meshObject.Vertices[vertexIndex][0]),
                                    inch2meter(meshObject.Vertices[vertexIndex][1]),
                                    inch2meter(meshObject.Vertices[vertexIndex][2])))
                    uv = (meshObject.UVs[vertexIndex][0][0], meshObject.UVs[vertexIndex][0][1])
                    vc = Vector(meshObject.Colors[vertexIndex])
                    normal = Vector(meshObject.Normals[vertexIndex])
                    if surf_sortkey > 0:
                        vertexMultiplier = 0.001
                        vertex[0] += 0.025 - (surf_sortkey * (normal[0] * vertexMultiplier))
                        vertex[1] += 0.025 - (surf_sortkey * (normal[1] * vertexMultiplier))
                        vertex[2] += 0.025 - (surf_sortkey * (normal[2] * vertexMultiplier))
                    
                    if len(surface.Materials) > 1:
                        layerUVs = meshObject.UVs[vertexIndex][1:]
                        faceLayerUVs.append(layerUVs)
                    # Assign vertex data
                    vert.co = vertex
                    verts.append(vert)
                    normals.append(normal)
                    faceUVs.append(uv)
                    faceVCs.append(vc)
                # Create face
                face = mesh.faces.new(verts)
                # Loop over face vertices
                for x in range(3):
                    # Add UV & VC
                    face.loops[x][uvSets[0]].uv = faceUVs[x]
                    face.loops[x][vcLayer] = faceVCs[x]
                    if (len(surface.Materials) > 1):
                        for i in range(len(faceLayerUVs[x])):
                            layerUV = faceLayerUVs[x][i]
                            face.loops[x][uvSets[i + 1]].uv = layerUV
            # Assign mesh data to object
            mesh.to_mesh(data)
            # Apply normal data
            data.create_normals_split()
            for loop_idx, loop in enumerate(data.loops):
                data.loops[loop_idx].normal = normals[loop_idx]
            data.validate(clean_customdata=False)
            clnors = array.array('f', [0.0] * (len(data.loops) * 3))
            data.loops.foreach_get("normal", clnors)
            # Enable smoothing - must be BEFORE normals_split_custom_set, etc.
            polygon_count = len(data.polygons)
            data.polygons.foreach_set("use_smooth", [True] * polygon_count)
            data.normals_split_custom_set(tuple(zip(*(iter(clnors),) * 3)))
            data.use_auto_smooth = True
            # Rename uv & vc sets 
            for i in range(len(surface.Materials)):
                data.uv_layers[i].name = surface.Materials[i]
            data.vertex_colors[0].name = surface.Name + "_vc"
            data.update()
            bmesh.ops.remove_doubles(mesh,verts=mesh.verts,dist=0.001)
            # Add surface object to list
            objects.append(obj)
            objects_data.append(obj.data)
            obj.data.name = meshObject.Name
            # Loop over materials
            if len(surface.Materials) > 0 and settings.import_materials == True and settings.material_type == "CoD Shader":
                if (game == "black_ops_2" or game == "modern_warfare_rm" or game == "modern_warfare_4" or
                    game == "advanced_warfare" or game == "black_ops" or game == "world_war_2" or
                    game == "infinite_warfare" or game == "modern_warfare_2_rm"):
                    matName = "::".join(surface.Materials)
                    if matName not in bpy.data.materials.keys():
                        if game == "infinite_warfare" or game == "world_war_2":
                            data.materials.append(createMaterial(surface.Materials))
                            
                        else:
                            data.materials.append(createMaterial(surface.Materials, map_materials))
                    else:
                        data.materials.append(bpy.data.materials[matName])
                elif (game == "modern_warfare" or game == "modern_warfare_2" or
                      game == "modern_warfare_3" or
                      game == "black_ops_4" or game == "black_ops_3" or
                      game == "ghosts" or game == "black_ops_5"
                      ):
                    codMat = map_materials[surface.Materials[0]]
                    matName = codMat.Name
                    if matName not in bpy.data.materials.keys():
                        if "emissive" in codMat.TechSet and "lit" not in codMat.TechSet and game == "black_ops_3":
                            createEmissiveMaterial(codMat)
                        else:
                            createMaterial(codMat)
                
                    data.materials.append(bpy.data.materials[matName])
            elif len(surface.Materials) > 0 and settings.import_materials == True and settings.material_type == "simple (Wavefront OBJ)":
                codMat = map_materials[surface.Materials[0]]
                matName = codMat.Name
                try:
                    data.materials.append(bpy.data.materials[matName])
                except:
                    print("Failed to import material.");
                    
               
        return meshCollection
    def createInstance(instanceObject, index, blender_obj, col):
        # Create instance object
        instance_obj = bpy.data.objects.new(name="{0}_{1}".format(instanceObject.Name, index), object_data=None)
        # Loop over mesh surfaces
        if blender_obj != None:
            instance_obj.instance_collection = blender_obj
            instance_obj.instance_type = 'COLLECTION'
            col.objects.link(instance_obj)
        else:
            instance_obj.empty_display_size = 0.75
            instance_obj.empty_display_type = 'SPHERE' 
            col.objects.link(instance_obj)
        # Place model instance accordingly
        instance_obj.location = (inch2meter(instanceObject.Position[0]),
                                 inch2meter(instanceObject.Position[1]),
                                 inch2meter(instanceObject.Position[2]))
        if (instanceObject.Rotation_mode == 0):
            instance_obj.rotation_mode = 'QUATERNION'
            instance_obj.rotation_quaternion = instanceObject.Rotation
        elif(instanceObject.Rotation_mode == 1):
            instance_obj.rotation_euler = instanceObject.Rotation_euler
        instance_obj.scale = instanceObject.Scale
        
        return instance_obj
    def createLight(codLight):
        # Create data for light
        light_data = bpy.data.lights.new(name=codLight.Type, type=codLight.Type)
        light_data.color = [codLight.Color[0], codLight.Color[1], codLight.Color[2]]
        light_data.energy = codLight.Color[3] * 16
        # Apply base settings
        if codLight.Type == "SUN":  
            light_data.shadow_cascade_max_distance = 1000
        elif codLight.Type == "SPOT":
            #light_data.use_shadow = False
            light_data.shadow_soft_size = codLight.Radius * 0.0254
            light_data.shadow_buffer_clip_start = 1.0
            light_data.use_custom_distance = True
            if codLight.dAttenuation != 0.0:
                light_data.cutoff_distance = codLight.dAttenuation
            if codLight.CosHalfFovOuter == 0.0 and codLight.CosHalfFovInner == 0.0:
                light_data.spot_blend = 1.0
            else:
                outer = acos(codLight.CosHalfFovOuter) * 2
                inner = acos(codLight.CosHalfFovInner) * 2
                light_data.spot_size = outer
                #light_data.spot_blend = 1.0
                light_data.spot_blend = 1 - (inner / outer)
            light_data.energy = codLight.Color[3] * 500
        elif codLight.Type == "POINT":
            light_data.energy = codLight.Color[3] * 500
            light_data.shadow_soft_size = codLight.Radius * 0.0254
        # Attach to object
        light_object = bpy.data.objects.new(name=codLight.Type, object_data=light_data)
        # Change location
        light_object.location = (inch2meter(codLight.Origin[0]), inch2meter(codLight.Origin[1]), inch2meter(codLight.Origin[2]))
        # Calculate direction
        # Apply direction
        light_object.rotation_euler = dir2euler(codLight.Origin, codLight.Direction)

        return light_object
    def createWorld(name, path_images):
        world = bpy.data.worlds.new(name)
        world.use_nodes = True
        nodes = world.node_tree.nodes
        links = world.node_tree.links

        nodes.clear()

        node_envTexture = nodes.new(type="ShaderNodeTexEnvironment")
        imagePath = os.path.join(path_images, name + ".tga")
        node_envTexture.image = bpy.data.images.load(filepath=imagePath)
        node_envTexture.image.colorspace_settings.name = "Raw"
        node_background = nodes.new(type="ShaderNodeBackground")

        node_background.location = 200, 0
        node_background.inputs["Strength"].default_value = 1.0

        node_output = nodes.new(type="ShaderNodeOutputWorld")
        node_output.location = 400, 0
        
        links.new(node_envTexture.outputs[0], node_background.inputs[0])
        links.new(node_background.outputs[0], node_output.inputs[0])

        return world
    def dir2euler(loc_source, direction):
        loc_target = Vector((loc_source[0] - direction[0],
                            loc_source[1] - direction[1],
                            loc_source[2] - direction[2]))

        direction = loc_target - Vector(loc_source)
        # point the cameras '-Z' and use its 'Y' as up
        rot_quat = direction.to_track_quat('-Z', 'Y')
        # assume we're using euler rotation
        return rot_quat.to_euler()
    def inch2meter(value):
        return value * 0.0254


    if (c2m_map.Version == "modern_warfare" or c2m_map.Version == "modern_warfare_2" or
        c2m_map.Version == "modern_warfare_3" or c2m_map.Version == "ghosts"):
            from .materials.cod4 import createRevealMix, createNodeGroup, createMaterial
            createRevealMix()
    elif (c2m_map.Version == "black_ops_3" or c2m_map.Version == "black_ops_4" or
          c2m_map.Version == "black_ops_5"):
            from .materials.bo3 import createRevealMix, createNodeGroup, createEmissiveMaterial, createMaterial, createSpriteSheetGroup
            createRevealMix()
            createSpriteSheetGroup()
    elif (c2m_map.Version == "modern_warfare_rm" or c2m_map.Version == "advanced_warfare"):
        from .materials.mwr import createRevealMix, createNodeGroup, createEmissiveMaterial, createMaterial, createMixGroup, createMixMultiplyGroup
        createRevealMix()
        createMixGroup()
        createMixMultiplyGroup()
    elif (c2m_map.Version == "infinite_warfare"):
        from .materials.iw import createRevealMix, createNodeGroup, createEmissiveMaterial, createMaterial, createMixGroup
        createRevealMix()
        createMixGroup()
    elif (c2m_map.Version == "world_war_2"):
        from .materials.ww2 import createRevealMix, createNodeGroup, createEmissiveMaterial, createMaterial, createMixGroup
        createRevealMix()
        createMixGroup()
    elif (c2m_map.Version == "modern_warfare_2_rm"):
        from .materials.mw2cr import createRevealMix, createNodeGroup, createEmissiveMaterial, createMaterial, createMixGroup
        createRevealMix()
        createMixGroup()
    elif (c2m_map.Version == "modern_warfare_4"):
        from .materials.mw19 import createRevealMix, createNodeGroup, createEmissiveMaterial, createMaterial, createMixGroup
        createRevealMix()
        createMixGroup()
    elif (c2m_map.Version == "black_ops_2" or c2m_map.Version == "black_ops"):
        from .materials.bo2 import createMixGroup, createNodeGroup, createMaterial, createRevealMix, createMixMultiplyGroup
        createRevealMix()
        createMixGroup()
        createMixMultiplyGroup()

    # Create node group that converts DX Normal Map
    NormalFlipYNodeGroup()
    for screen in bpy.data.screens:
        for area in screen.areas:
            for space in area.spaces:
                if space.type == "OUTLINER":
                    space.show_restrict_column_viewport = True
                    space.show_restrict_column_render = True
    # Set scene settings
    scene = bpy.data.scenes["Scene"]
    #scene.display_settings.display_device = 'None'
    #scene.sequencer_colorspace_settings.name = 'Linear'
    scene.view_settings.gamma = 1.0
    # eevee settings
    scene.eevee.use_gtao = True
    scene.eevee.gtao_distance = 0.5
    scene.eevee.gtao_factor = 2.0
    scene.eevee.shadow_cube_size = '4096'
    scene.eevee.shadow_cascade_size = '4096'
    scene.eevee.use_shadow_high_bitdepth = True
    scene.eevee.use_soft_shadows = False
    # scene.eevee.use_ssr = True
    # scene.eevee.use_ssr_refraction = True
    # Set world settings
    if c2m_map.Skybox:
        scene.world = createWorld(c2m_map.Skybox, image_path)
    else:
        world_bg = bpy.data.worlds["World"].node_tree.nodes["Background"]
        world_bg.inputs['Color'].default_value = [1.0, 1.0, 1.0, 1.0]
        world_bg.inputs['Strength'].default_value = 0.5
    # Get main collection
    main_collection = bpy.context.scene.collection
    
    # Create empties
    mapCollection = bpy.data.collections.new(c2m_map.Name)
    
    lightsCollection = bpy.data.collections.new("Lights")
    # Link objects to scene
    main_collection.children.link(mapCollection)
    mapCollection.children.link(lightsCollection)
    # Dictionary for blender objects
    blender_objects = {}
    blender_materials = {}
    # Create materials
    if settings.import_materials == True:
        print("Creating materials")
        for matName, material in c2m_map.Materials.items():
            if matName not in blender_materials.keys():
                if settings.material_type == "simple (Wavefront OBJ)":
                    createBasicMaterial(material, image_path)
                else:
                    blender_materials[matName] = createNodeGroup(material, image_path)
    # Create map Geo
    print("Creating map geometry")
    createMesh(c2m_map.Objects[0], mapCollection, c2m_map.Materials, c2m_map.Version)
    print("Creating unique xmodels")
    if settings.import_props == True:
        # Create props
        xmodels_collection = bpy.data.collections.new("XModels [DO NOT DELETE]")
        xmodels_collection.hide_viewport = True
        xmodels_collection.hide_render = True
        mapCollection.children.link(xmodels_collection)
        instancesCollection = bpy.data.collections.new("Model Instances")
        mapCollection.children.link(instancesCollection)
        for index, map_object in enumerate(c2m_map.Objects[1:]):
            print(f"Importing model {index} / {len(c2m_map.Objects)}")
            # Create Blender object
            blender_obj = createMesh(map_object, xmodels_collection, c2m_map.Materials, c2m_map.Version)
            # Store it to make instance later
            blender_objects[map_object.Name] = blender_obj 
        
        # Create model instances
        print("Creating model instances")
        for index, instance in enumerate(c2m_map.ModelInstances):
            print(f"Creating model instance {index} / {len(c2m_map.ModelInstances)}")
            if instance.Position[0] == 0 and instance.Position[1] == 0 and instance.Position[2] == 0:
                continue
            # Get model object
            blender_obj = None
            if instance.Name in blender_objects.keys():
                blender_obj = blender_objects[instance.Name]
            # Create instance
            instance_obj = createInstance(instance, index, blender_obj, instancesCollection)
    
    if settings.import_lights == True:
        # Create lights
        print("Creating lights")
        for light in c2m_map.Lights:
            blender_light = createLight(light)
            lightsCollection.objects.link(blender_light)


    print("Done")
    