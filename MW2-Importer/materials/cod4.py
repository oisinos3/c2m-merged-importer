import bpy,bmesh
import os
import array
from math import *
from mathutils import *

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


    node_add = nodes.new('ShaderNodeMath')
    node_add.location = (0, 0)
    links.new(node_subtract.outputs[0], node_add.inputs[0])
    links.new(node_vertexColor.outputs[1], node_add.inputs[1])

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
    
    loc_y = 100
    # Add images
    for texture in codMaterial.Textures:
        imagePath = os.path.join(images_path, texture.Name + ".tga")
        if not os.path.isfile(imagePath) or "$black" in texture.Name or "identitynormal" in texture.Name:
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
            if texture.TexType == "colorOpacity":
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
            normal_node.inputs['Strength'].default_value = 2.0
            links.new(node_image.outputs[0], normal_node.inputs[1])
            links.new(normal_node.outputs[0], group_outputs.inputs['Normal'])
            image_nodes["normalMap"] = node_image

            loc_y -= 300
        # specularMap
        elif texture.TexType == "specularMap":
            node_group.outputs.new('NodeSocketColor','Specular')
            node_group.outputs.new('NodeSocketFloat','Roughness')
            node_image.location = (-250, loc_y)
            node_invert = nodes.new('ShaderNodeInvert')
            node_invert.location = (50, loc_y)
            links.new(node_image.outputs[0], group_outputs.inputs['Specular'])
            links.new(node_image.outputs[1], node_invert.inputs[1])
            links.new(node_invert.outputs[0], group_outputs.inputs['Roughness'])
            image_nodes["specularMap"] = node_image
            loc_y -= 300

        else:
            nodes.remove(node_image)

    return node_group

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
    # Create mix material
    node_group = nodes.new('ShaderNodeGroup')
    node_group.node_tree = bpy.data.node_groups[materialName]
    node_group.location = (-100,0)
    for output in node_group.outputs:
        links.new(node_group.outputs[output.name], principled_node.inputs[output.name])
    links.new(principled_node.outputs[0], material_output.inputs[0])
    if codMaterial.SortKey > 0 and "mc_ambient" not in codMaterial.TechSet:
        material.blend_method = "BLEND"
        material.shadow_method = "NONE"
        if "glass" in codMaterial.Name:
            principled_node.inputs["Transmission"].default_value = 1.0
        node_revealMix = nodes.new('ShaderNodeGroup')
        node_revealMix.node_tree = bpy.data.node_groups['RevealMix']
        node_revealMix.location = (100, 0)
        links.new(node_group.outputs['Alpha'], node_revealMix.inputs["REVEAL"])
        links.new(node_revealMix.outputs['ALPHA'], principled_node.inputs['Alpha'])
    return material