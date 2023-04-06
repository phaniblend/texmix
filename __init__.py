import bpy
from bpy.types import Operator, Panel
from bpy.props import PointerProperty, FloatProperty
from bpy.utils import register_class, unregister_class

bl_info = {
    "name": "TexMix",
    "author": "Phani",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "description": "A Blender addon for mixing two textures.",
    "category": "Textures"
}


class TexMixProperties(bpy.types.PropertyGroup):
    texture_1: PointerProperty(type=bpy.types.Image, name="Texture 1")
    texture_2: PointerProperty(type=bpy.types.Image, name="Texture 2")
    mix_ratio: FloatProperty(name="Mix Ratio", min=0.0, max=1.0, default=0.5)


class TexMixPanel(Panel):
    bl_idname = "OBJECT_PT_texmix_panel"
    bl_label = "TexMix"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'TexMix'
    bl_context = "NODE_EDITOR"

    def draw(self, context):
        layout = self.layout
        texmix_props = context.scene.texmix_props

        # Texture 1 selector
        layout.prop(texmix_props, "texture_1")

        # Texture 2 selector
        layout.prop(texmix_props, "texture_2")

        # Mix ratio slider
        layout.prop(texmix_props, "mix_ratio")

        # Mix button
        layout.operator("object.texmix_mix", text="Mix Textures")


class TexMixMixOperator(bpy.types.Operator):
    """Mix two textures based on the mix ratio"""
    bl_idname = "texture.texmix_mix_operator"
    bl_label = "TexMix Mix Operator"

    mix_ratio: bpy.props.FloatProperty(
        name="Mix Ratio",
        description="The ratio of the two textures to mix (0.0-1.0)",
        default=0.5,
        min=0.0,
        max=1.0
    )

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        # Get the active material of the selected object
        active_material = context.object.active_material

        # Get the two textures to mix
        texture1 = active_material.texture_slots[0].texture
        texture2 = active_material.texture_slots[1].texture

        # Create the mix texture node
        mix_node = active_material.node_tree.nodes.new('ShaderNodeMixRGB')
        mix_node.location = (0, 0)

        # Set the mix ratio based on the operator property
        mix_node.inputs[0].default_value = self.mix_ratio

        # Connect the two textures to the mix node
        active_material.node_tree.links.new(
            texture1.outputs['Color'], mix_node.inputs[1])
        active_material.node_tree.links.new(
            texture2.outputs['Color'], mix_node.inputs[2])

        # Connect the mix node to the output node
        active_material.node_tree.links.new(
            mix_node.outputs['Color'], active_material.node_tree.nodes['Material Output'].inputs['Surface'])

        return {'FINISHED'}


def register():
    bpy.utils.register_class(TexMixProperties)
    bpy.utils.register_class(TexMixPanel)
    bpy.utils.register_class(TexMixMixOperator)

    bpy.types.Scene.texmix_props = bpy.props.PointerProperty(
        type=TexMixProperties)


def unregister():
    del bpy.types.Scene.texmix_props

    bpy.utils.unregister_class(TexMixMixOperator)
    bpy.utils.unregister_class(TexMixPanel)
    bpy.utils.unregister_class(TexMixProperties)


if __name__ == "__main__":
    register()
