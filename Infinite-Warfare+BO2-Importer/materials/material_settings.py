import bpy
import os

# colorTint
def addColorTint(setting, node_group, prev_color):
    color = setting.split(" ")
    nodes = node_group.nodes
    links = node_group.links

    node_RGB = nodes.new('ShaderNodeRGB')
    node_RGB.location = (-150, 300)
    node_RGB.outputs[0].default_value = [float(color[0]), float(color[1]), float(color[2]), 1.0]

    if prev_color != None:
        node_mixRGB = nodes.new('ShaderNodeMixRGB')
        node_mixRGB.location = (100, 100)
        node_mixRGB.blend_type = "MULTIPLY"
        node_mixRGB.inputs[0].default_value =  1.0
        links.new(node_RGB.outputs[0], node_mixRGB.inputs[1])
        links.new(prev_color.outputs[0], node_mixRGB.inputs[2])
        
        return node_mixRGB
    else:
        return node_RGB

# detailScale (UV scale)
def addDetailScale(setting, node_group):
    scale = setting.split(" ")
    nodes = node_group.nodes
    links = node_group.links

    node_texCoord = nodes.new('ShaderNodeTexCoord')
    node_texCoord.location = (-700, -300)

    node_mapping = nodes.new('ShaderNodeMapping')
    node_mapping.location = (-500, -300)
    node_mapping.inputs[3].default_value[0] = float(scale[0])
    node_mapping.inputs[3].default_value[1] = float(scale[1])
    links.new(node_texCoord.outputs["UV"], node_mapping.inputs[0])

    return node_mapping

# specColorTint
def addSpecColorTint(setting, node_group, prev_color):
    color = setting.split(" ")
    nodes = node_group.nodes
    links = node_group.links

    node_RGB = nodes.new('ShaderNodeRGB')
    node_RGB.location = (-150, 300)
    node_RGB.outputs[0].default_value = [float(color[0]), float(color[1]), float(color[2]), 1.0]

    if prev_color !=  None:
        node_mixRGB = nodes.new('ShaderNodeMixRGB')
        node_mixRGB.location = (100, 100)
        node_mixRGB.blend_type = "MULTIPLY"
        node_mixRGB.inputs[0].default_value =  1.0
        links.new(node_RGB.outputs[0], node_mixRGB.inputs[1])

        if prev_color.bl_idname == "ShaderNodeMixRGB":
            node_RGB.location = (50, 300)
            node_mixRGB.location = (300, 150)

        links.new(prev_color.outputs[0], node_mixRGB.inputs[2])
        
        return node_mixRGB
    else:
        return node_RGB
