import bpy
import os
from .material_settings import*

def createRevealMix():
    # Create a group
    node_group = bpy.data.node_groups.new("RevealMix", 'ShaderNodeTree')
    nodes = node_group.nodes
    links = node_group.links
    # Create output node
    node_outputs = nodes.new('NodeGroupOutput')
    node_outputs.location = (400, -50)
    node_group.outputs.new('NodeSocketFloat','ALPHA')

    node_inputs = nodes.new('NodeGroupInput')
    node_inputs.location = (-400, 100)
    node_group.inputs.new('NodeSocketFloat','REVEAL')

    node_subtract = nodes.new('ShaderNodeMath')
    node_subtract.operation = "SUBTRACT"
    node_subtract.location = (-200, 100)
    node_subtract.inputs[1].default_value = 1.0
    links.new(node_inputs.outputs['REVEAL'], node_subtract.inputs[0])

    node_vertexColor = nodes.new('ShaderNodeVertexColor')
    node_vertexColor.location = (-400, -100)

    node_multiply = nodes.new('ShaderNodeMath')
    node_multiply.operation = "MULTIPLY"
    node_multiply.location = (-200, -100)
    node_multiply.inputs[1].default_value = 2.0
    links.new(node_vertexColor.outputs[1], node_multiply.inputs[0])

    node_add = nodes.new('ShaderNodeMath')
    node_add.location = (0, 0)
    links.new(node_subtract.outputs[0], node_add.inputs[0])
    links.new(node_multiply.outputs[0], node_add.inputs[1])

    node_clamp = nodes.new('ShaderNodeClamp')
    node_clamp.location = (200, 0)
    links.new(node_add.outputs[0], node_clamp.inputs[0])
    links.new(node_clamp.outputs[0], node_outputs.inputs['ALPHA'])

def createNodeGroup(codMaterial, images_path):
    image_nodes = {}
    # Create a group
    node_group = bpy.data.node_groups.new(codMaterial.Name, 'ShaderNodeTree')
    nodes = node_group.nodes
    links = node_group.links
    # Create output node
    group_outputs = nodes.new('NodeGroupOutput')
    group_outputs.location = (600,-250)
    node_group.outputs.new('NodeSocketColor','Base Color')
    node_group.outputs.new('NodeSocketFloat', 'Alpha')
    group_outputs.inputs['Alpha'].default_value = 1.0
    if "reveal" in codMaterial.TechSet or "_mask" in codMaterial.TechSet:
        node_multiply = nodes.new('ShaderNodeMath')
        node_multiply.operation = 'MULTIPLY'
        node_multiply.location = (100, -600)
    
    loc_y = 100
    # Add images
    #print(codMaterial.Name)
    for texture in codMaterial.Textures:
        if "$black" in texture.Name or "identitynormal" in texture.Name:
            continue
        imagePath = os.path.join(images_path, texture.Name + ".tga")
        if not os.path.isfile(imagePath):
            continue
        fullImageName = texture.Name + ".tga"
        if fullImageName not in bpy.data.images.keys():
            bpy.ops.image.open(filepath=imagePath)
        blender_image = bpy.data.images.get(fullImageName)
        if blender_image == None:
            blender_image = bpy.data.images.get(fullImageName.replace(".tga", ""))
        
        # Create image node
        node_image = nodes.new('ShaderNodeTexImage')
        # Assign image
        node_image.image = blender_image
        node_image.image.colorspace_settings.name = "Linear"
        node_image.image.alpha_mode = "CHANNEL_PACKED"
        node_image.name = texture.TexType

        # colorMap
        if "color" in texture.TexType:
            node_image.image.colorspace_settings.name = "sRGB"
            node_image.location = (-250, loc_y)
            links.new(node_image.outputs[0], group_outputs.inputs['Base Color'])
            if "reveal" in codMaterial.TechSet or "_mask" in codMaterial.TechSet:
                links.new(node_image.outputs[1], node_multiply.inputs[0])
            elif texture.TexType == "colorOpacity":
                links.new(node_image.outputs[1], group_outputs.inputs['Alpha'])
            image_nodes["colorMap"] = node_image

            loc_y -= 300
        # normalMap
        elif texture.TexType == "normalMap":
            node_group.outputs.new('NodeSocketVector','Normal')
            node_image.location = (-250, loc_y)
            # Normal Map node
            normal_node = nodes.new('ShaderNodeNormalMap')
            normal_node.location = (50, loc_y)
            normal_node.inputs['Strength'].default_value = 1.0
            links.new(node_image.outputs[0], normal_node.inputs[1])
            links.new(normal_node.outputs[0], group_outputs.inputs['Normal'])
            image_nodes["normalMap"] = node_image

            loc_y -= 300
        # specularMap
        elif texture.TexType == "specularMap":
            node_group.outputs.new('NodeSocketColor','Specular')
            node_image.location = (-250, loc_y)
            links.new(node_image.outputs[0], group_outputs.inputs['Specular'])
            image_nodes["specularMap"] = node_image

            loc_y -= 300
        # glossMap
        elif texture.TexType == "glossMap":
            node_group.outputs.new('NodeSocketFloat','Roughness')
            node_image.location = (-250, loc_y)
            node_invert = nodes.new('ShaderNodeInvert')
            node_invert.location = (50, loc_y)
            links.new(node_image.outputs[0], node_invert.inputs[1])
            links.new(node_invert.outputs[0], group_outputs.inputs['Roughness'])
            image_nodes["glossMap"] = node_image

            loc_y -= 300
        # mask
        elif texture.TexType == "revealMap" or texture.TexType == "emissionMask":
            node_image.location = (-250, loc_y)
            links.new(node_image.outputs[0], node_multiply.inputs[1])
            links.new(node_multiply.outputs[0], group_outputs.inputs["Alpha"])
            image_nodes[texture.TexType] = node_image

            loc_y -= 300
        
        elif "emissionMap" in texture.TexType and "decal_emissive" not in codMaterial.TechSet and "emissionMap" not in image_nodes.keys():
            node_image.location = (-250, loc_y)
            node_image.image.colorspace_settings.name = "sRGB"
            if "lit" in codMaterial.TechSet:
                links.new(node_image.outputs[0], group_outputs.inputs['Base Color'])
            else:
                node_group.outputs.new('NodeSocketColor', 'Emission')
                links.new(node_image.outputs[0], group_outputs.inputs['Emission'])        
            image_nodes["emissionMap"] = node_image

            loc_y -= 300

        else:
            nodes.remove(node_image)
    
    nodes_settings = {}
    for setting in codMaterial.Settings:
        if setting == "colorTint":
            if "colorMap" in image_nodes.keys():
                node_prevColor = image_nodes["colorMap"]
            elif "emissionMap" in image_nodes.keys():
                node_prevColor = image_nodes["emissionMap"]
            else:
                node_prevColor = None
            node_setting = addColorTint(codMaterial.Settings[setting], node_group, node_prevColor)
            links.new(node_setting.outputs[0], group_outputs.inputs['Base Color'])
            nodes_settings["colorTint"] = node_setting
        elif setting == "detailScale" and "rowCount" not in codMaterial.Settings.keys():
            node_setting = addDetailScale(codMaterial.Settings[setting], node_group)
            for node_image in image_nodes.values():
                links.new(node_setting.outputs[0], node_image.inputs[0])
            nodes_settings["detailScale"] = node_setting
        elif setting == "specColorTint":
            if "colorTint" in nodes_settings.keys():
                continue
            elif "colorMap" in image_nodes.keys():
                node_prevColor = image_nodes["colorMap"]
            else:
                node_prevColor = None
            node_setting = addSpecColorTint(codMaterial.Settings[setting], node_group, node_prevColor)
            links.new(node_setting.outputs[0], group_outputs.inputs['Base Color'])
            nodes_settings["specColorTint"] = node_setting
        elif setting == "rowCount":
            if codMaterial.Settings[setting] != "0":
                rowCount = int(codMaterial.Settings["rowCount"])
                columnCount = int(codMaterial.Settings["columnCount"])
                imageTime = float(codMaterial.Settings["imageTime"])
                node_spritesheet = nodes.new('ShaderNodeGroup')
                node_spritesheet.node_tree = bpy.data.node_groups["SpriteSheet"]
                node_spritesheet.inputs['rowCount'].default_value = rowCount
                node_spritesheet.inputs['columnCount'].default_value = columnCount
                node_spritesheet.inputs['imageTime'].default_value = imageTime
                node_spritesheet.location = (-700, -350)
                for node_image in image_nodes.values():
                    links.new(node_spritesheet.outputs[0], node_image.inputs[0])

        

    return node_group

def createEmissiveMaterial(codMaterial):
    # Make material name
    materialName = codMaterial.Name
    # Create new material
    material = bpy.data.materials.new(name=materialName)
    material.blend_method = "BLEND"
    material.shadow_method = "NONE"
    material.use_nodes=True
    nodes=material.node_tree.nodes
    links=material.node_tree.links
    # Remove all nodes
    for node in nodes:
        nodes.remove(node)
    # Add output node
    material_output = nodes.new('ShaderNodeOutputMaterial')
    material_output.location = (500, 0)
    # Add node group
    node_group = nodes.new('ShaderNodeGroup')
    node_group.node_tree = bpy.data.node_groups[materialName]
    node_group.location = (-250,0)
    # Emission Node
    node_emission = nodes.new('ShaderNodeEmission')
    node_emission.location = (0, -100)
    node_emission.inputs[1].default_value = 16.0
    if 'Emission' in node_group.outputs.keys():
        links.new(node_group.outputs['Emission'], node_emission.inputs['Color'])
    else:
        links.new(node_group.outputs['Base Color'], node_emission.inputs['Color'])
    # Transparent Node
    node_transparent = nodes.new('ShaderNodeBsdfTransparent')
    node_transparent.location = (0, 100)
    # MixShader Node
    node_mixshader = nodes.new('ShaderNodeMixShader')
    node_mixshader.location = (300, 0)
    links.new(node_group.outputs['Alpha'], node_mixshader.inputs[0])
    links.new(node_transparent.outputs[0], node_mixshader.inputs[1])
    links.new(node_emission.outputs[0], node_mixshader.inputs[2])
    
    links.new(node_mixshader.outputs[0], material_output.inputs[0])
    
    return material

def createMaterial(codMaterial):
    # Make material name
    materialName = codMaterial.Name
    # Create new material
    material = bpy.data.materials.new(name=materialName)
    material.blend_method = "CLIP"
    material.shadow_method = "CLIP"
    material.use_nodes=True
    nodes=material.node_tree.nodes
    links=material.node_tree.links
    # Remove all nodes
    for node in nodes:
        nodes.remove(node)
    # Add output node
    material_output = nodes.new('ShaderNodeOutputMaterial')
    # Principled BSDF Node
    principled_node = nodes.new('ShaderNodeBsdfPrincipled')
    principled_node.location = (500, -100)
    material_output.location = (850, -100)
    if "reveal" in codMaterial.TechSet or "_mask" in codMaterial.TechSet or "glass" in codMaterial.TechSet or "detail_decal" in codMaterial.TechSet:
        material.blend_method = "BLEND"
        material.shadow_method = "NONE"
        if "glass" in codMaterial.TechSet:
            principled_node.inputs["Transmission"].default_value = 1.0
    # Create mix material
    node_group = nodes.new('ShaderNodeGroup')
    node_group.node_tree = bpy.data.node_groups[materialName]
    node_group.location = (-100,0)
    for output in node_group.outputs:
        links.new(node_group.outputs[output.name], principled_node.inputs[output.name])
    if "reveal" in codMaterial.TechSet:
        node_revealMix = nodes.new('ShaderNodeGroup')
        node_revealMix.node_tree = bpy.data.node_groups['RevealMix']
        node_revealMix.location = (100, 0)
        links.new(node_group.outputs['Alpha'], node_revealMix.inputs["REVEAL"])
        links.new(node_revealMix.outputs['ALPHA'], principled_node.inputs['Alpha'])

    links.new(principled_node.outputs[0], material_output.inputs[0])
    
    return material

def createSpriteSheetGroup():
    # Create a group
    node_group = bpy.data.node_groups.new("SpriteSheet", 'ShaderNodeTree')
    nodes = node_group.nodes
    links = node_group.links
    # Create outputs
    node_outputs = nodes.new('NodeGroupOutput')
    node_outputs.location = (2150, 100)
    node_group.outputs.new('NodeSocketVector','Vector')
    # Create inputs
    node_inputs = nodes.new('NodeGroupInput')
    node_inputs.location = (-900, -150)
    node_group.inputs.new('NodeSocketFloat','columnCount')
    node_group.inputs.new('NodeSocketFloat','rowCount')
    node_group.inputs.new('NodeSocketFloat','imageTime')

    # Create ShaderNodes
    node_texcoord = nodes.new('ShaderNodeTexCoord')
    node_texcoord.location = (-900, 100)

    node_divide1 = nodes.new('ShaderNodeMath')
    node_divide1.operation = "DIVIDE"
    node_divide1.location = (-400, 100)

    node_divide2 = nodes.new('ShaderNodeMath')
    node_divide2.operation = "DIVIDE"
    node_divide2.location = (-400, -80)

    node_divide3 = nodes.new('ShaderNodeMath')
    node_divide3.operation = "DIVIDE"
    node_divide3.location = (-400, -300)

    node_sepXYZ1 = nodes.new('ShaderNodeSeparateXYZ')
    node_sepXYZ1.location = (-650, 100)

    node_currentFrame = nodes.new('ShaderNodeValue')
    node_currentFrame.label = "Current Frame"
    node_currentFrame.location = (-850, -350)
    driver_frame = node_currentFrame.outputs[0].driver_add("default_value")
    var_time = driver_frame.driver.variables.new()
    var_time.name='time'
    var_time.type='SINGLE_PROP'
    var_time.targets[0].id_type = 'SCENE'
    var_time.targets[0].id = bpy.data.scenes["Scene"]
    var_time.targets[0].data_path = 'frame_current'
    driver_frame.driver.expression = var_time.name
    node_currentFrame.outputs[0].default_value = 0.0

    node_sceneFPS = nodes.new('ShaderNodeValue')
    node_sceneFPS.label = "Scene Framerate"
    node_sceneFPS.location = (-850, -500)
    driver_fps = node_sceneFPS.outputs[0].driver_add("default_value")
    var_fps = driver_fps.driver.variables.new()
    var_fps.name='fps'
    var_fps.type='SINGLE_PROP'
    var_fps.targets[0].id_type = 'SCENE'
    var_fps.targets[0].id = bpy.data.scenes["Scene"]
    var_fps.targets[0].data_path = 'render.fps'
    driver_fps.driver.expression = var_fps.name
    node_sceneFPS.outputs[0].default_value = 0.0

    node_divide4 = nodes.new('ShaderNodeMath')
    node_divide4.operation = "DIVIDE"
    node_divide4.location = (-150, -450)

    node_divide5 = nodes.new('ShaderNodeMath')
    node_divide5.operation = "DIVIDE"
    node_divide5.location = (-150, -150)
    node_divide5.inputs[0].default_value = 1.0

    node_subtract1 = nodes.new('ShaderNodeMath')
    node_subtract1.operation = "SUBTRACT"
    node_subtract1.location = (100, -150)
    node_subtract1.inputs[0].default_value = 1.0
    
    node_add1 = nodes.new('ShaderNodeMath')
    node_add1.operation = "ADD"
    node_add1.location = (300, 0)

    node_combineXYZ1 = nodes.new('ShaderNodeCombineXYZ')
    node_combineXYZ1.location = (500, 100)

    node_floor1 = nodes.new('ShaderNodeMath')
    node_floor1.operation = "FLOOR"
    node_floor1.location = (50, -450)

    node_sepXYZ2 = nodes.new('ShaderNodeSeparateXYZ')
    node_sepXYZ2.location = (800, 250)

    node_totalFrames = nodes.new('ShaderNodeMath')
    node_totalFrames.operation = "MULTIPLY"
    node_totalFrames.label = "Total Frames"
    node_totalFrames.location = (800, 100)

    node_divide6 = nodes.new('ShaderNodeMath')
    node_divide6.operation = "DIVIDE"
    node_divide6.location = (800, -100)
    node_divide6.inputs[0].default_value = 1.0

    node_divide7 = nodes.new('ShaderNodeMath')
    node_divide7.operation = "DIVIDE"
    node_divide7.location = (800, -300)

    node_multiply1 = nodes.new('ShaderNodeMath')
    node_multiply1.operation = "MULTIPLY"
    node_multiply1.location = (1050, -125)

    node_floor2 = nodes.new('ShaderNodeMath')
    node_floor2.operation = "FLOOR"
    node_floor2.location = (1050, -300)

    node_add2 = nodes.new('ShaderNodeMath')
    node_add2.operation = "ADD"
    node_add2.location = (1250, -50)

    node_divide8 = nodes.new('ShaderNodeMath')
    node_divide8.operation = "DIVIDE"
    node_divide8.location = (1250, -125)

    node_subtract2 = nodes.new('ShaderNodeMath')
    node_subtract2.operation = "SUBTRACT"
    node_subtract2.inputs[0].default_value = 1.0
    node_subtract2.location = (1550, -200)

    node_add3 = nodes.new('ShaderNodeMath')
    node_add3.operation = "ADD"
    node_add3.location = (1750, -50)

    node_combineXYZ2 = nodes.new('ShaderNodeCombineXYZ')
    node_combineXYZ2.location = (1950, 100)

    # Link nodes
    links.new(node_texcoord.outputs[2], node_sepXYZ1.inputs[0])
    links.new(node_sepXYZ1.outputs[0], node_divide1.inputs[0])
    links.new(node_inputs.outputs[0], node_divide1.inputs[1])
    links.new(node_sepXYZ1.outputs[1], node_divide2.inputs[0])
    links.new(node_inputs.outputs[1], node_divide2.inputs[1])
    links.new(node_currentFrame.outputs[0], node_divide3.inputs[0])
    links.new(node_sceneFPS.outputs[0], node_divide3.inputs[1])
    links.new(node_inputs.outputs[1], node_divide5.inputs[1])
    links.new(node_divide3.outputs[0], node_divide4.inputs[0])
    links.new(node_inputs.outputs[2], node_divide4.inputs[1])
    links.new(node_divide5.outputs[0], node_subtract1.inputs[1])
    links.new(node_divide2.outputs[0], node_add1.inputs[0])
    links.new(node_subtract1.outputs[0], node_add1.inputs[1])
    links.new(node_divide1.outputs[0], node_combineXYZ1.inputs[0])
    links.new(node_add1.outputs[0], node_combineXYZ1.inputs[1])
    links.new(node_divide4.outputs[0], node_floor1.inputs[0])
    links.new(node_combineXYZ1.outputs[0], node_sepXYZ2.inputs[0])
    links.new(node_inputs.outputs[0], node_totalFrames.inputs[0])
    links.new(node_inputs.outputs[1], node_totalFrames.inputs[1])
    links.new(node_inputs.outputs[0], node_divide6.inputs[1])
    links.new(node_floor1.outputs[0], node_divide7.inputs[0])
    links.new(node_inputs.outputs[0], node_divide7.inputs[1])
    links.new(node_divide6.outputs[0], node_multiply1.inputs[0])
    links.new(node_floor1.outputs[0], node_multiply1.inputs[1])
    links.new(node_divide7.outputs[0], node_floor2.inputs[0])
    links.new(node_sepXYZ2.outputs[0], node_add2.inputs[0])
    links.new(node_multiply1.outputs[0], node_add2.inputs[1])
    links.new(node_floor2.outputs[0], node_divide8.inputs[0])
    links.new(node_inputs.outputs[1], node_divide8.inputs[1])
    links.new(node_divide8.outputs[0], node_subtract2.inputs[1])
    links.new(node_sepXYZ2.outputs[1], node_add3.inputs[0])
    links.new(node_subtract2.outputs[0], node_add3.inputs[1])
    links.new(node_add2.outputs[0], node_combineXYZ2.inputs[0])
    links.new(node_add3.outputs[0], node_combineXYZ2.inputs[1])
    links.new(node_sepXYZ2.outputs[2], node_combineXYZ2.inputs[2])
    links.new(node_combineXYZ2.outputs[0], node_outputs.inputs[0])