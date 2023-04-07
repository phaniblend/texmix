
import bpy
from bpy.props import PointerProperty, FloatProperty, EnumProperty
from bpy.types import Operator, Panel


bl_info = {
    "name": "TexMix",
    "author": "Phani",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "description": "A Blender addon for blending two textures.",
    "category": "Textures"
}


def populate_material_list(self, context):
    material_items = []
    for material in bpy.data.materials:
        if material.use_nodes and any(node.type == 'TEX_IMAGE' for node in material.node_tree.nodes):
            material_items.append((material.name, material.name, ""))
    return material_items

class MixOperator(bpy.types.Operator):
    """Mix two textures based on the mix ratio"""
    bl_idname = "texmix.mix_operator"
    bl_label = "Mix Operator"

    def execute(self, context):
        # Get the selected materials
        material_1 = context.scene.texmix_props.material_1
        material_2 = context.scene.texmix_props.material_2

        if not material_1 or not material_2:
            self.report({'ERROR'}, "Please select two valid materials to mix.")
            return {'CANCELLED'}

        # Get the two textures to mix
        texture1 = material_1.node_tree.nodes.get('Image Texture')
        texture2 = material_2.node_tree.nodes.get('Image Texture')

        if not texture1 or not texture2:
            self.report(
                {'ERROR'}, "Please select materials with image textures to mix.")
            return {'CANCELLED'}

        # Get the active material of the selected object
        active_material = context.object.active_material

        # Create the mix texture node
        mix_node = active_material.node_tree.nodes.new('ShaderNodeMixRGB')
        mix_node.location = (0, 0)

        # Set the mix ratio based on the operator property
        mix_node.inputs[0].default_value = context.scene.texmix_props.mix_ratio

        # Connect the two textures to the mix node
        active_material.node_tree.links.new(
            texture1.outputs['Color'], mix_node.inputs[1])
        active_material.node_tree.links.new(
            texture2.outputs['Color'], mix_node.inputs[2])

        # Connect the mix node to the output node
        active_material.node_tree.links.new(
            mix_node.outputs['Color'], active_material.node_tree.nodes['Material Output'].inputs['Surface'])

        return {'FINISHED'}


class MaterialSelector(bpy.types.Operator):
    """Operator to select materials for texture mixing"""
    bl_idname = "texmix.material_selector"
    bl_label = "Material Selector"

    texture_slot: bpy.props.EnumProperty(
        name="Texture Slot",
        items=[
            ("0", "Texture 1", ""),
            ("1", "Texture 2", "")
        ]
    )

    def update_material_list(self, context):
        materials = []
        for material in bpy.data.materials:
            if material.use_nodes and any(node.type == 'TEX_IMAGE' for node in material.node_tree.nodes):
                materials.append((material.name, material.name, ""))
        self.material_items = materials

    material_items: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)

    material_name: bpy.props.EnumProperty(
        name="Material Name",
        items=material_items,
        update=update_material_list
    )

    def execute(self, context):
        # Get the active material of the selected object
        active_material = context.object.active_material

        # Get the index of the texture slot to set the texture to
        texture_slot_index = int(self.texture_slot)

        # Get the selected material by name
        selected_material = bpy.data.materials[self.material_name]

        # Set the texture in the selected texture slot to the texture of the selected material
        active_material.node_tree.nodes['Image Texture'].image = selected_material.node_tree.nodes['Image Texture'].image
        active_material.texture_paint_images[texture_slot_index] = selected_material.texture_paint_images[0]

        return {'FINISHED'}


class Properties(bpy.types.PropertyGroup):
    material_1: EnumProperty(
        items=[(mat.name, mat.name, "") for mat in bpy.data.materials],
        name="Material 1"
    )

    material_2: EnumProperty(
        items=[(mat.name, mat.name, "") for mat in bpy.data.materials],
        name="Material 2"
    )

    texture_1: PointerProperty(type=bpy.types.Image, name="Texture 1")
    texture_2: PointerProperty(type=bpy.types.Image, name="Texture 2")
    mix_ratio: FloatProperty(name="Mix Ratio", min=0.0, max=1.0, default=0.5)


class Panel(bpy.types.Panel):
    """Panel for the TexMix addon"""
    bl_idname = "TEXMIX_PT_panel"
    bl_label = "TexMix"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'TexMix'

    def draw(self, context):
        layout = self.layout
        props = context.scene.texmix_props

        # Material selectors
        row = layout.row()
        row.prop(props, "material_1")
        row.prop(props, "material_2")

        layout.separator()

        # Texture selectors
        row = layout.row()
        row.prop(props, "texture_1")
        row.prop(props, "texture_2")

        layout.separator()

        # Mix ratio slider
        row = layout.row()
        row.prop(props, "mix_ratio")

        layout.separator()

        # Mix button
        row = layout.row()
        row.operator("texmix.mix_operator", text="Mix Textures")

        layout.separator()

        # Material selector buttons
        row = layout.row()
        row.operator("texmix.material_selector",
                     text="Set Material 1").texture_slot = "0"
        row.operator("texmix.material_selector",
                     text="Set Material 2").texture_slot = "1"


def register():
    bpy.utils.register_class(Properties)
    bpy.utils.register_class(Panel)
    bpy.utils.register_class(MixOperator)
    bpy.utils.register_class(MaterialSelector)
    bpy.types.Scene.props = bpy.props.PointerProperty(
        type=Properties)
    bpy.types.Scene.texmix_props = bpy.props.PointerProperty(type=Properties)


def unregister():
    del bpy.types.Scene.props

    bpy.utils.unregister_class(MixOperator)
    bpy.utils.unregister_class(Panel)
    bpy.utils.unregister_class(Properties)
    bpy.utils.unregister_class(MaterialSelector)


if __name__ == "__main__":
    register()
