import bpy
from bpy.props import PointerProperty, FloatProperty, EnumProperty
from bpy.types import Operator, Panel, PropertyGroup

bl_info = {
    "name": "TexMix",
    "author": "Phani",
    "location": "N Panel",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "description": "A Blender addon for blending two materials.",
    "category": "Material"
}

def material_items_callback(self, context):
    materials = [(mat.name, mat.name, "") for mat in bpy.data.materials]
    return materials

def create_node_tree_from_material(material):
    # Create a new node tree
    node_tree = bpy.data.node_groups.new(name=material.name + "_NodeTree", type='ShaderNodeTree')

    # Create a material output node
    output_node = node_tree.nodes.new(type='ShaderNodeOutputMaterial')
    output_node.location = (0, 0)

    # Get the material's node tree
    material_node_tree = material.node_tree

    # Copy the nodes from the material's node tree to the new node tree
    for node in material_node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED' or node.type == 'OUTPUT_MATERIAL':
            new_node = node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
        else:
            new_node = node_tree.nodes.new(type=node.type)
        new_node.location = node.location
        new_node.name = node.name

    # Copy the node inputs and outputs
    for input in node.inputs:
        new_input = new_node.inputs[input.name]
        input.copy(new_input)

    for output in node.outputs:
        new_output = new_node.outputs[output.name]
        output.copy(new_output)

    # Copy the links from the material's node tree to the new node tree
    for link in material_node_tree.links:
        node_tree.links.new(
            node_tree.nodes[link.from_node.name].outputs[link.from_socket.name],
            node_tree.nodes[link.to_node.name].inputs[link.to_socket.name]
        )

    # Connect the output node to the material's last node
    node_tree.links.new(
        node_tree.nodes[material_node_tree.nodes[-1].name].outputs['Shader'],
        output_node.inputs['Surface']
    )

    return node_tree

class MixOperator(bpy.types.Operator):
    """Mix two materials based on the mix ratio"""
    bl_idname = "texmix.mix_operator"
    bl_label = "Mix Operator"

    def execute(self, context):
        # Get the selected materials
        material_1 = context.scene.texmix_props.material_1
        material_2 = context.scene.texmix_props.material_2

        if not material_1 or not material_2:
            self.report({'ERROR'}, "Please select two valid materials to mix.")
            return {'CANCELLED'}

        # Get the two selected materials by name
        material_1_obj = bpy.data.materials.get(material_1)
        material_2_obj = bpy.data.materials.get(material_2)

        if not material_1_obj or not material_2_obj:
            self.report({'ERROR'}, "Please select two valid materials to mix.")
            return {'CANCELLED'}

        # Create a new material for the mix
        mix_material = bpy.data.materials.new(name="MixMaterial")
        mix_material.use_nodes = True
        mix_nodes = mix_material.node_tree.nodes
        mix_links = mix_material.node_tree.links

        # Create node trees from the selected materials
        node_tree_1 = create_node_tree_from_material(material_1_obj)
        node_tree_2 = create_node_tree_from_material(material_2_obj)

        # Create the mix node and add it to the node tree
        mix_node = mix_nodes.new(type='ShaderNodeMixShader')
        mix_node.location = (0, 0)

        # Set the mix ratio based on the operator property
        mix_node.inputs[0].default_value = context.scene.texmix_props.mix_ratio

        # Connect the two materials to the mix node
        mix_links.new(node_tree_1.outputs['Shader'], mix_node.inputs[1])
        mix_links.new(node_tree_2.outputs['Shader'], mix_node.inputs[2])

        # Connect the mix node to the output node
        mix_output_node = mix_nodes['Material Output']
        mix_links.new(mix_node.outputs['Shader'],
                      mix_output_node.inputs['Surface'])

        # Apply the mix material to the active object
        context.object.active_material = mix_material

        return {'FINISHED'}

class MaterialSelectorPanel(bpy.types.Panel):
    bl_idname = "MATERIAL_SELECTOR_PT_texmix"
    bl_label = "Material Selector"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    bl_category = "TexMix"

    def draw(self, context):
        layout = self.layout
        texmix_props = context.scene.texmix_props

        # Material selectors
        layout.prop(texmix_props, "material_1")
        layout.prop(texmix_props, "material_2")

        layout.separator()

        # Mix ratio slider
        layout.prop(texmix_props, "mix_ratio")

        layout.separator()

        # Mix button
        row = layout.row()
        row.operator("texmix.mix_operator", text="Mix Materials")

        # Apply button
        row = layout.row()
        row.operator("texmix.apply_operator", text="Apply Material")

class ApplyOperator(bpy.types.Operator):
    """Apply the mixed material to the selected object and add the material to the list of materials"""
    bl_idname = "texmix.apply_operator"
    bl_label = "Apply Operator"

    def execute(self, context):
        # Get the active material
        mix_material = context.object.active_material

        # Give the material a unique name
        mix_material.name = mix_material.name + "_" + str(len(bpy.data.materials))

        # Apply the mix material to the active object
        context.object.active_material = mix_material

        return {'FINISHED'}

class TexMixProperties(PropertyGroup):
    material_1: EnumProperty(
        items=material_items_callback,
        name="Material 1",
        description="Select the first material to mix."
    )
    material_2: EnumProperty(
        items=material_items_callback,
        name="Material 2",
        description="Select the second material to mix."
    )
    mix_ratio: FloatProperty(
        name="Mix Ratio",
        description="The ratio of the two materials to mix.",
        default=0.5,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    )

def register():
    bpy.utils.register_class(TexMixProperties)
    bpy.utils.register_class(MaterialSelectorPanel)
    bpy.utils.register_class(MixOperator)
    bpy.utils.register_class(ApplyOperator)
    bpy.types.Scene.texmix_props = PointerProperty(type=TexMixProperties)

def unregister():
    bpy.utils.unregister_class(ApplyOperator)
    bpy.utils.unregister_class(MixOperator)
    bpy.utils.unregister_class(MaterialSelectorPanel)
    bpy.utils.unregister_class(TexMixProperties)
    del bpy.types.Scene.texmix_props

if __name__ == "__main__":
    register()
