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

    node_uv = nodes.new('ShaderNodeUVMap')
    node_uv.uv_map = codMaterial.Name
    node_uv.location = (-800, -400)
    node_mapping = nodes.new('ShaderNodeMapping')
    node_mapping.vector_type = "TEXTURE"
    node_mapping.location = (-600, -400)
    links.new(node_uv.outputs[0], node_mapping.inputs[0])
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
            if texture.TexType == "colorOpacity":
                if "reveal" in codMaterial.TechSet:
                    links.new(node_image.outputs[1], node_multiply.inputs[0])
                    links.new(node_multiply.outputs[0], group_outputs.inputs['Alpha'])
                else:
                    links.new(node_image.outputs[1], group_outputs.inputs['Alpha'])
            links.new(node_mapping.outputs[0], node_image.inputs[0])

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
            links.new(node_mapping.outputs[0], node_image.inputs[0])

            loc_y -= 300
        # specularMap
        elif texture.TexType == "specularMap":
            node_group.outputs.new('NodeSocketFloat','Specular')
            node_group.outputs.new('NodeSocketFloat','Roughness')
            node_image.location = (-250, loc_y)
            sepRGB_node = nodes.new('ShaderNodeSeparateRGB')
            sepRGB_node.location = (-50, loc_y)
            node_invert = nodes.new('ShaderNodeInvert')
            node_invert.location = (150, loc_y)
            links.new(node_image.outputs[0], sepRGB_node.inputs[0])
            links.new(sepRGB_node.outputs[0], group_outputs.inputs['Specular'])
            links.new(sepRGB_node.outputs[2], node_invert.inputs[1])
            links.new(node_invert.outputs[0], group_outputs.inputs['Roughness'])
            links.new(node_mapping.outputs[0], node_image.inputs[0])

            loc_y -= 300         
        # mask
        elif texture.TexType == "revealMap":
            node_image.location = (-250, loc_y)
            links.new(node_image.outputs[0], node_multiply.inputs[1])
            links.new(node_mapping.outputs[0], node_image.inputs[0])
            loc_y -= 300

        else:
            nodes.remove(node_image)
    
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
                    links.new(sepRGB_node.outputs[index], blend_nodes[index-1].inputs['Vertex Alpha'])
                else:
                    links.new(vertex_node.outputs[1], blend_nodes[index-1].inputs['Vertex Alpha'])
                    
                for output in group_nodes[index].outputs:
                    if output.name != "Alpha":
                        links.new(group_nodes[index].outputs[output.name], blend_nodes[index-1].inputs["{0}_2".format(output.name)])
                links.new(group_nodes[index].outputs['Alpha'], blend_nodes[index-1].inputs['Alpha'])
            if index == 1:
                for output in group_nodes[0].outputs:
                    if output.name != "Alpha":
                        links.new(group_nodes[0].outputs[output.name], blend_nodes[index-1].inputs["{0}_1".format(output.name)])
            elif 1 < index < 5:
                for output in blend_nodes[index-2].outputs:
                    if output.name != "Alpha":
                        links.new(blend_nodes[index-2].outputs[output.name], blend_nodes[index-1].inputs["{0}_1".format(output.name)])

            location_y -= 200
        
        for output in blend_node.outputs:
            if output.name != "Alpha":
                links.new(blend_node.outputs[output.name], principled_node.inputs[output.name])
    else:
        node_group = nodes.new('ShaderNodeGroup')
        node_group.node_tree = bpy.data.node_groups[matList[0]]
        node_group.location = (location_x,location_y)
        for output in node_group.outputs:
            links.new(node_group.outputs[output.name], principled_node.inputs[output.name])
        
    links.new(principled_node.outputs[0], material_output.inputs[0])

    return material
def createMixGroup():
    # Create a group
    node_group = bpy.data.node_groups.new("BlendTextures", 'ShaderNodeTree')
    # Create input & output nodes
    group_outputs = node_group.nodes.new('NodeGroupOutput')
    group_outputs.location = (500,0)
    group_inputs = node_group.nodes.new('NodeGroupInput')
    group_inputs.location = (-1000,0)
    # Add outputs
    node_group.outputs.new('NodeSocketColor','Base Color')
    node_group.outputs.new('NodeSocketColor','Normal')
    node_group.outputs.new('NodeSocketColor','Specular')
    node_group.outputs.new('NodeSocketColor','Roughness')
    node_group.outputs.new('NodeSocketFloat', 'Alpha')
    # Add inputs
    node_group.inputs.new('NodeSocketColor','Base Color_1')
    node_group.inputs.new('NodeSocketColor','Base Color_2')
    node_group.inputs.new('NodeSocketVector','Normal_1')
    node_group.inputs['Normal_1'].default_value = [0.5, 0.5, 1.0]
    node_group.inputs.new('NodeSocketVector','Normal_2')
    node_group.inputs['Normal_2'].default_value = [0.5, 0.5, 1.0]
    node_group.inputs.new('NodeSocketColor','Specular_1')
    node_group.inputs['Specular_1'].default_value = [0.5, 0.5, 0.5, 1.0]
    node_group.inputs.new('NodeSocketColor','Specular_2')
    node_group.inputs['Specular_2'].default_value = [0.5, 0.5, 0.5, 1.0]
    node_group.inputs.new('NodeSocketColor','Roughness_1')
    node_group.inputs['Roughness_1'].default_value = [0.5, 0.5, 0.5, 1.0]
    node_group.inputs.new('NodeSocketColor','Roughness_2')
    node_group.inputs['Roughness_2'].default_value = [0.5, 0.5, 0.5, 1.0]
    node_group.inputs.new('NodeSocketColor','Vertex Alpha')
    node_group.inputs.new('NodeSocketFloat','Alpha')
    node_group.inputs['Alpha'].default_value = 1.0
    # Multiply node for alpha + vertex color
    node_multiply1 = node_group.nodes.new('ShaderNodeMath')
    node_multiply1.operation = "MULTIPLY"
    node_multiply1.location = (-800, 0)
    node_multiply1.inputs[1].default_value = 3.0
    node_multiply2 = node_group.nodes.new('ShaderNodeMath')
    node_multiply2.operation = "MULTIPLY"
    node_multiply2.location = (-600, 0)
    node_group.links.new(group_inputs.outputs['Vertex Alpha'], node_multiply1.inputs[0])
    node_group.links.new(node_multiply1.outputs[0], node_multiply1.inputs[0])
    node_group.links.new(group_inputs.outputs['Alpha'], node_multiply2.inputs[1])
    node_clamp = node_group.nodes.new('ShaderNodeClamp')
    node_clamp.location = (-400, 0)
    node_group.links.new(node_multiply2.outputs[0], node_clamp.inputs[0])
    # Color MIX
    mix_color = node_group.nodes.new('ShaderNodeMixRGB')
    mix_color.location = (0, 0)
    mix_color.label = "MixCOLOR"
    node_group.links.new(group_inputs.outputs['Base Color_1'], mix_color.inputs['Color1'])
    node_group.links.new(group_inputs.outputs['Base Color_2'], mix_color.inputs['Color2'])
    node_group.links.new(node_clamp.outputs[0], mix_color.inputs[0])
    node_group.links.new(mix_color.outputs[0], group_outputs.inputs['Base Color'])
    # Normal MIX
    mix_normal = node_group.nodes.new('ShaderNodeMixRGB')
    mix_normal.location = (0, -200)
    mix_normal.label = "MixNORMAL"
    node_group.links.new(group_inputs.outputs['Normal_1'], mix_normal.inputs['Color1'])
    node_group.links.new(group_inputs.outputs['Normal_2'], mix_normal.inputs['Color2'])
    node_group.links.new(node_clamp.outputs[0], mix_normal.inputs[0])
    node_group.links.new(mix_normal.outputs[0], group_outputs.inputs['Normal'])
    # Specular MIX
    mix_specular = node_group.nodes.new('ShaderNodeMixRGB')
    mix_specular.location = (0, -400)
    mix_specular.label = "MixSPECULAR"
    node_group.links.new(group_inputs.outputs['Specular_1'], mix_specular.inputs['Color1'])
    node_group.links.new(group_inputs.outputs['Specular_2'], mix_specular.inputs['Color2'])
    node_group.links.new(node_clamp.outputs[0], mix_specular.inputs[0])
    node_group.links.new(mix_specular.outputs[0], group_outputs.inputs['Specular'])
    # Roughness MIX
    mix_roughness = node_group.nodes.new('ShaderNodeMixRGB')
    mix_roughness.location = (0, -600)
    mix_roughness.label = "MixROUGHNESS"
    node_group.links.new(group_inputs.outputs['Roughness_1'], mix_roughness.inputs['Color1'])
    node_group.links.new(group_inputs.outputs['Roughness_2'], mix_roughness.inputs['Color2'])
    node_group.links.new(node_clamp.outputs[0], mix_roughness.inputs[0])
    node_group.links.new(mix_roughness.outputs[0], group_outputs.inputs['Roughness'])