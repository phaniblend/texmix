import bpy
from bpy.types import Operator, Panel
from bpy.props import PointerProperty, FloatProperty, EnumProperty
from bpy.utils import register_class, unregister_class


bl_info = {
    "name": "TexMix",
    "author": "Phani",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "description": "A Blender addon for blending two textures.",
    "category": "Textures"
}


def populate_material_list(self, context):
    items = []
    for material in bpy.data.materials:
        if material.use_nodes and any(node.type == 'TEX_IMAGE' for node in material.node_tree.nodes):
            items.append((material.name, material.name, ""))
    return items


class tMProperties(bpy.types.PropertyGroup):
    texture_1: PointerProperty(type=bpy.types.Image, name="Texture 1")
    texture_2: PointerProperty(type=bpy.types.Image, name="Texture 2")
    mix_ratio: FloatProperty(name="Mix Ratio", min=0.0, max=1.0, default=0.5)
    material_1: EnumProperty(items=populate_material_list, name="Material 1")
    material_2: EnumProperty(items=populate_material_list, name="Material 2")


class tMPanel(Panel):
    bl_idname = "tM_tM_PT_panel"
    bl_label = "tM"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'TexMix'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        tM_props = context.scene.tM_props

        # Material selectors
        row = layout.row()
        row.prop(tM_props, "material_1")
        row.prop(tM_props, "material_2")

        layout.separator()

        # Texture selectors
        row = layout.row()
        row.prop(tM_props, "texture_1")
        row.prop(tM_props, "texture_2")

        layout.separator()

        # Mix ratio slider
        row = layout.row()
        row.prop(tM_props, "mix_ratio")

        layout.separator()

        # Mix button
        row = layout.row()
        row.operator("tM_tM_OT_mix_operator", text="Mix Textures")


class tMMixOperator(bpy.types.Operator):
    """Mix two textures based on the mix ratio"""
    bl_idname = "tM_tM_OT_mix_operator"
    bl_label = "tM tM Mix Operator"

    mix_ratio: bpy.props.FloatProperty(
        name="Mix Ratio",
        description="The ratio of the two textures to mix (0.0-1.0)",
        default=0.5,
        min=0.0,
        max=1.0
    )

    material_1: bpy.props.EnumProperty(
        name="Material 1",
        items=populate_material_list
    )

    material_2: bpy.props.EnumProperty(
        name="Material 2",
        items=populate_material_list
    )

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        # Get the selected materials
        material_1 = bpy.data.materials.get(self.material_1)
        material_2 = bpy.data.materials.get(self.material_2)

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


class tMMaterialSelector(bpy.types.Operator):
    """Operator to select materials for texture mixing"""
    bl_idname = "tM_tM_OT_material_selector"
    bl_label = "tM tM Material Selector"

    texture_slot: bpy.props.EnumProperty(
        name="Texture Slot",
        items=[
            ("0", "Texture 1", ""),
            ("1", "Texture 2", "")
        ]
    )

    material_name: bpy.props.EnumProperty(
        name="Material Name",
        items=populate_material_list
    )

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        # Get the active material of the selected object
        active_material = context.object.active_material

        # Get the index of the texture slot to set the texture to
        texture_slot_index = int(self.texture_slot)

        # Get the selected material by name
        selected_material = bpy.data.materials[self.material_name]

        # Set the texture in the selected texture slot to the texture of the selected material
        active_material.texture_slots[texture_slot_index].texture = selected_material.texture_slots[0].texture

        return {'FINISHED'}


def register():
    bpy.utils.register_class(tMProperties)
    bpy.types.Scene.tM_props = bpy.props.PointerProperty(
        type=tMProperties)

    bpy.utils.register_class(tMPanel)
    bpy.utils.register_class(tMMixOperator)

def unregister():
    del bpy.types.Scene.tM_props

    bpy.utils.unregister_class(tMMixOperator)
    bpy.utils.unregister_class(tMPanel)
    bpy.utils.unregister_class(tMProperties)

if __name__ == "__main__":
    register()
