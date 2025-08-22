import bpy,bmesh
import os
import array
from math import *
from mathutils import *

def createMixGroup():
    # Create a group
    node_group = bpy.data.node_groups.new("BlendTextures", 'ShaderNodeTree')
    # Create input & output nodes
    group_outputs = node_group.nodes.new('NodeGroupOutput')
    group_outputs.location = (500,0)
    group_inputs = node_group.nodes.new('NodeGroupInput')
    group_inputs.location = (-850,0)
    # Add outputs
    node_group.outputs.new('NodeSocketColor','COLOR')
    node_group.outputs.new('NodeSocketColor','NORMAL')
    node_group.outputs.new('NodeSocketColor','SPECULAR')
    node_group.outputs.new('NodeSocketColor','ROUGHNESS')
    node_group.outputs.new('NodeSocketFloat', 'ALPHA')
    # Add inputs
    node_group.inputs.new('NodeSocketColor','COLOR_1')
    node_group.inputs.new('NodeSocketColor','COLOR_2')
    node_group.inputs.new('NodeSocketColor','NORMAL_1')
    node_group.inputs['NORMAL_1'].default_value = [0.5, 0.5, 1.0, 1.0]
    node_group.inputs.new('NodeSocketColor','NORMAL_2')
    node_group.inputs['NORMAL_2'].default_value = [0.5, 0.5, 1.0, 1.0]
    node_group.inputs.new('NodeSocketColor','SPECULAR_1')
    node_group.inputs['SPECULAR_1'].default_value = [1.0, 1.0, 1.0, 1.0]
    node_group.inputs.new('NodeSocketColor','SPECULAR_2')
    node_group.inputs['SPECULAR_2'].default_value = [1.0, 1.0, 1.0, 1.0]
    node_group.inputs.new('NodeSocketColor','ROUGHNESS_1')
    node_group.inputs['ROUGHNESS_1'].default_value = [1.0, 1.0, 1.0, 1.0]
    node_group.inputs.new('NodeSocketColor','ROUGHNESS_2')
    node_group.inputs['ROUGHNESS_2'].default_value = [1.0, 1.0, 1.0, 1.0]
    node_group.inputs.new('NodeSocketColor','VERTEX_ALPHA')
    node_group.inputs.new('NodeSocketFloat','ALPHA')
    node_group.inputs['ALPHA'].default_value = 1.0
    # Multiply node for alpha + vertex color
    multiply_node = node_group.nodes.new('ShaderNodeMath')
    multiply_node.operation = "MULTIPLY"
    multiply_node.location = (-350, 250)
    node_group.links.new(group_inputs.outputs['VERTEX_ALPHA'], multiply_node.inputs[0])
    # ColorRamp nodes
    ramp_node = node_group.nodes.new('ShaderNodeValToRGB')
    ramp_node.color_ramp.elements[1].position = 0.22
    ramp_node.location = (-650, 250)
    node_group.links.new(group_inputs.outputs['ALPHA'], ramp_node.inputs[0])
    node_group.links.new(ramp_node.outputs[0], multiply_node.inputs[1])
    ramp_node2 = node_group.nodes.new('ShaderNodeValToRGB')
    ramp_node2.color_ramp.elements[1].position = 0.5
    ramp_node2.location = (-50, 250)
    node_group.links.new(multiply_node.outputs[0], ramp_node2.inputs[0])
    # Color MIX
    mix_color = node_group.nodes.new('ShaderNodeMixRGB')
    mix_color.location = (0, 0)
    mix_color.label = "MixCOLOR"
    node_group.links.new(group_inputs.outputs['COLOR_1'], mix_color.inputs['Color1'])
    node_group.links.new(group_inputs.outputs['COLOR_2'], mix_color.inputs['Color2'])
    node_group.links.new(ramp_node2.outputs[0], mix_color.inputs[0])
    node_group.links.new(mix_color.outputs[0], group_outputs.inputs['COLOR'])
    # Normal MIX
    mix_normal = node_group.nodes.new('ShaderNodeMixRGB')
    mix_normal.location = (0, -200)
    mix_normal.label = "MixNORMAL"
    node_group.links.new(group_inputs.outputs['NORMAL_1'], mix_normal.inputs['Color1'])
    node_group.links.new(group_inputs.outputs['NORMAL_2'], mix_normal.inputs['Color2'])
    node_group.links.new(ramp_node2.outputs[0], mix_normal.inputs[0])
    node_group.links.new(mix_normal.outputs[0], group_outputs.inputs['NORMAL'])
    # Specular MIX
    mix_specular = node_group.nodes.new('ShaderNodeMixRGB')
    mix_specular.location = (0, -400)
    mix_specular.label = "MixSPECULAR"
    node_group.links.new(group_inputs.outputs['SPECULAR_1'], mix_specular.inputs['Color1'])
    node_group.links.new(group_inputs.outputs['SPECULAR_2'], mix_specular.inputs['Color2'])
    node_group.links.new(ramp_node2.outputs[0], mix_specular.inputs[0])
    node_group.links.new(mix_specular.outputs[0], group_outputs.inputs['SPECULAR'])
    # Roughness MIX
    mix_roughness = node_group.nodes.new('ShaderNodeMixRGB')
    mix_roughness.location = (0, -600)
    mix_roughness.label = "MixROUGHNESS"
    node_group.links.new(group_inputs.outputs['ROUGHNESS_1'], mix_roughness.inputs['Color1'])
    node_group.links.new(group_inputs.outputs['ROUGHNESS_2'], mix_roughness.inputs['Color2'])
    node_group.links.new(ramp_node2.outputs[0], mix_roughness.inputs[0])
    node_group.links.new(mix_roughness.outputs[0], group_outputs.inputs['ROUGHNESS'])
def createNodeGroup(codMaterial, images_path):
    image_nodes = {}
    # Create a group
    node_group = bpy.data.node_groups.new(codMaterial.Name, 'ShaderNodeTree')
    nodes = links = node_group.nodes
    links = node_group.links
    # Create output node
    group_outputs = node_group.nodes.new('NodeGroupOutput')
    group_outputs.location = (300,0)
    # Add base outputs
    node_group.outputs.new('NodeSocketColor','COLOR')
    group_outputs.inputs['COLOR'].default_value = [1.0, 1.0, 1.0, 1.0]
    node_group.outputs.new('NodeSocketColor','NORMAL')
    group_outputs.inputs['NORMAL'].default_value = [0.5, 0.5, 1.0, 1.0]
    node_group.outputs.new('NodeSocketColor','SPECULAR')
    group_outputs.inputs['SPECULAR'].default_value = [1.0, 1.0, 1.0, 1.0]
    node_group.outputs.new('NodeSocketFloat','ROUGHNESS')
    group_outputs.inputs['ROUGHNESS'].default_value = 0.5
    node_group.outputs.new('NodeSocketFloat', 'ALPHA')
    # If material has multiply decal, we don't support it yet
    if codMaterial.Name[-8:] != "multiply":
        group_outputs.inputs['ALPHA'].default_value = 1.0
    else:
        group_outputs.inputs['ALPHA'].default_value = 0
    # Add images
    for texture in codMaterial.Textures:
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

        if "color" in texture.TexType:
            node_image.location = (-250, 100)
            node_image.image.colorspace_settings.name = "sRGB"
            links.new(node_image.outputs[0], group_outputs.inputs['COLOR'])
            if texture.TexType == "colorOpacity" or texture.TexType == "colorMap":
                links.new(node_image.outputs[1], group_outputs.inputs['ALPHA'])
            elif texture.TexType == "colorGloss":
                node_invert = nodes.new('ShaderNodeInvert')
                node_invert.location = (100, 0)
                links.new(node_image.outputs[1], node_invert.inputs['Color'])
                links.new(node_invert.outputs[0], group_outputs.inputs['ROUGHNESS'])
        elif texture.TexType == "normalMap":
            node_image.location = (-250, -300)
            links.new(node_image.outputs[0], group_outputs.inputs['NORMAL'])
        elif texture.TexType == "specularMap":
            node_image.location = (-250, -700)
            node_invert = nodes.new('ShaderNodeInvert')
            node_invert.location = (100, -700)
            links.new(node_image.outputs[0], group_outputs.inputs['SPECULAR'])
            links.new(node_image.outputs[1], node_invert.inputs[1])
            links.new(node_invert.outputs[0], group_outputs.inputs['ROUGHNESS'])

    for setting in codMaterial.Settings:
        addMaterialSetting(setting, codMaterial.Settings[setting], image_nodes, node_group, group_outputs)
    return node_group
def createMaterial(matList):
    # Make material name
    materialName = "::".join(matList)
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
    # Normal Map node
    normal_node = nodes.new('ShaderNodeNormalMap')
    normal_node.location = (250, -200)
    normal_node.inputs['Strength'].default_value = 1.0
    # Principled BSDF Node
    principled_node = nodes.new('ShaderNodeBsdfPrincipled')
    principled_node.location = (500, -100)
    if "glass" in materialName:
        material.blend_method = "BLEND"
        principled_node.inputs["Transmission"].default_value = 1.0
    material_output.location = (850, -100)
    location_x = -500
    location_y = 0
    # Create mix material
    if len(matList)>1:
        # Add vertex color nodes
        vertex_node = nodes.new('ShaderNodeVertexColor')
        vertex_node.location = (-500, 150)
        sepRGB_node = nodes.new('ShaderNodeSeparateRGB')
        sepRGB_node.location = (-300, 150)
        links.new(vertex_node.outputs[0], sepRGB_node.inputs[0])
        # Lists for our shader nodes & mix nodes
        group_nodes = []
        blend_nodes = []
        # Loop over materials
        for index, mat in enumerate(matList):
            # Get material node group
            node_group = nodes.new('ShaderNodeGroup')
            node_group.node_tree = bpy.data.node_groups[mat]
            node_group.location = (location_x,location_y)
            # Add to list
            group_nodes.append(node_group)
            # Set up decal nodes
            if index != 0:
                # Create Mix node
                blend_node = nodes.new('ShaderNodeGroup')
                blend_node.node_tree = bpy.data.node_groups['BlendTextures']
                blend_node.location = (-325 + -(location_y), 0)
                blend_nodes.append(blend_node)
            # If decal 1 or 2
            if 0 < index < 4:
                if index != 3:
                    links.new(sepRGB_node.outputs[index], blend_nodes[index-1].inputs['VERTEX_ALPHA'])
                else:
                    links.new(vertex_node.outputs[1], blend_nodes[index-1].inputs['VERTEX_ALPHA'])
                links.new(group_nodes[index].outputs['ALPHA'], blend_nodes[index-1].inputs['ALPHA'])
                links.new(group_nodes[index].outputs['COLOR'], blend_nodes[index-1].inputs['COLOR_2'])
                links.new(group_nodes[index].outputs['NORMAL'], blend_nodes[index-1].inputs['NORMAL_2'])
                links.new(group_nodes[index].outputs['SPECULAR'], blend_nodes[index-1].inputs['SPECULAR_2'])
                links.new(group_nodes[index].outputs['ROUGHNESS'], blend_nodes[index-1].inputs['ROUGHNESS_2'])
            if index == 1:
                links.new(group_nodes[0].outputs['COLOR'], blend_nodes[index-1].inputs['COLOR_1'])
                links.new(group_nodes[0].outputs['NORMAL'], blend_nodes[index-1].inputs['NORMAL_1'])
                links.new(group_nodes[0].outputs['SPECULAR'], blend_nodes[index-1].inputs['SPECULAR_1'])
                links.new(group_nodes[0].outputs['ROUGHNESS'], blend_nodes[index-1].inputs['ROUGHNESS_1'])
            elif 1 < index < 4:
                links.new(blend_nodes[index-2].outputs['COLOR'], blend_nodes[index-1].inputs['COLOR_1'])
                links.new(blend_nodes[index-2].outputs['NORMAL'], blend_nodes[index-1].inputs['NORMAL_1'])
                links.new(blend_nodes[index-2].outputs['SPECULAR'], blend_nodes[index-1].inputs['SPECULAR_1'])
                links.new(blend_nodes[index-2].outputs['ROUGHNESS'], blend_nodes[index-1].inputs['ROUGHNESS_1'])

            location_y -= 200
        
        links.new(blend_node.outputs['COLOR'], principled_node.inputs['Base Color'])
        links.new(blend_node.outputs['SPECULAR'], principled_node.inputs['Specular'])
        links.new(blend_node.outputs['ROUGHNESS'], principled_node.inputs['Roughness'])
        links.new(blend_node.outputs['NORMAL'], normal_node.inputs[1])
    else:
        node_group = nodes.new('ShaderNodeGroup')
        node_group.node_tree = bpy.data.node_groups[matList[0]]
        node_group.location = (location_x,location_y)
        links.new(node_group.outputs['COLOR'], principled_node.inputs['Base Color'])
        links.new(node_group.outputs['SPECULAR'], principled_node.inputs['Specular'])
        links.new(node_group.outputs['ROUGHNESS'], principled_node.inputs['Roughness'])
        links.new(node_group.outputs['NORMAL'], normal_node.inputs[1])
        links.new(node_group.outputs['ALPHA'], principled_node.inputs['Alpha'])
        
    links.new(normal_node.outputs[0], principled_node.inputs['Normal'])
    links.new(principled_node.outputs[0], material_output.inputs[0])

    return material