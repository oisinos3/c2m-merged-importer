import bpy
import os
from .material_settings import*

def createBasicMaterial(codMaterial, images_path):
    if codMaterial.SortKey > 0:
        return
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
    if "glass" in codMaterial.TechSet or "glass" in codMaterial.Name:
        material.blend_method = "BLEND"
        material.shadow_method = "NONE"
        principled_node.inputs["Transmission"].default_value = 1.0
    # Create material
    loc_y = 100
    # Add images
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
            node_image.location = (-250, loc_y)
            node_image.image.colorspace_settings.name = "sRGB"
            links.new(node_image.outputs[0], principled_node.inputs['Base Color'])
            if texture.TexType == "colorOpacity" or texture.TexType == "colorMap":
                links.new(node_image.outputs[1], principled_node.inputs['Alpha'])
            elif texture.TexType == "colorGloss":
                node_invert = nodes.new('ShaderNodeInvert')
                node_invert.location = (100, loc_y)
                links.new(node_image.outputs[1], node_invert.inputs['Color'])
                links.new(node_invert.outputs[0], principled_node.inputs['Roughness'])

            loc_y -= 300
        # normalMap
        elif texture.TexType == "normalMap":
            node_image.location = (-250, loc_y)
            # Normal Map node
            normal_node = nodes.new('ShaderNodeNormalMap')
            normal_node.location = (50, loc_y)
            normal_node.inputs['Strength'].default_value = 2.0
            links.new(node_image.outputs[0], normal_node.inputs[1])
            links.new(normal_node.outputs[0], principled_node.inputs['Normal'])

            loc_y -= 300
        # specularMap
        elif texture.TexType == "specularMap":
            node_image.location = (-250, loc_y)
            node_invert = nodes.new('ShaderNodeInvert')
            node_invert.location = (50, loc_y)
            links.new(node_image.outputs[0], principled_node.inputs['Specular'])
            links.new(node_image.outputs[1], node_invert.inputs[1])
            links.new(node_invert.outputs[0], principled_node.inputs['Roughness'])
            loc_y -= 300

        else:
            nodes.remove(node_image)
    links.new(principled_node.outputs[0], material_output.inputs[0])
    
