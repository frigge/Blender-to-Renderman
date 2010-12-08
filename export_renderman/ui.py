
#Blender 2.5 or later to Renderman Exporter
#Author: Sascha Fricke



#############################################################################################
#                                                                                           #
#       Begin GPL Block                                                                     #
#                                                                                           #
#############################################################################################
#                                                                                           #
#This program is free software;                                                             #
#you can redistribute it and/or modify it under the terms of the                            #
#GNU General Public License as published by the Free Software Foundation;                   #
#either version 3 of the LicensGe, or (at your option) any later version.                   #
#                                                                                           #
#This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;  #
#without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  #
#See the GNU General Public License for more details.                                       #
#                                                                                           #
#You should have received a copy of the GNU General Public License along with this program; #
#if not, see <http://www.gnu.org/licenses/>.                                                #
#                                                                                           #
#############################################################################################
#                                                                                           #
#       End GPL Block                                                                       #
#                                                                                           #
############################################################################################

#Thanks to: Campbell Barton, Eric Back, Nathan Vegdahl

import bpy
import export_renderman
import export_renderman.rm_maintain
from export_renderman.rm_maintain import *

##################################################################################################################################
#########################################################################################################
#                                                                                                       #
#       U I   L A Y O U T                                                                               #
#                                                                                                       #
#########################################################################################################

#########################################################################################################
#                                                                                                       #
#       layout functions                                                                                #
#                                                                                                       #
#########################################################################################################

def parmlayout(parm, master_parm, layout):
    float_size = {  1 : "float_one",
                    2 : "float_two",
                    3 : "float_three"}
                        
    int_size = {    1 : "int_one",
                    2 : "int_two",
                    3 : "int_three"}
                                                                                                
    if master_parm.parametertype == 'string':
        row = layout.row(align=True)
        
        if master_parm.texture:
            row.prop_search(parm, "textparameter", bpy.data, "textures", text=parm.name)
        else:
            row.prop(parm, "textparameter", text="")
    if master_parm.parametertype == 'float':
        layout.prop(parm, float_size[master_parm.vector_size])
    if master_parm.parametertype == 'int':
        layout.prop(parm, int_size[master_parm.vector_size])        
    if master_parm.parametertype == 'color':
        layout.prop(parm, "colorparameter", text="") 

def matparmlayout(parmlist, layout, material):
    if parmlist:
        for active_parameter in parmlist:
            row = layout.row(align=True)
            if active_parameter.parametertype == 'string':
                
                if active_parameter.texture:
                    if material == bpy.data:
                        row.prop_search(active_parameter, "textparameter", material, "textures", text=active_parameter.name)
                    else:
                        row.prop_search(active_parameter, "textparameter", material, "texture_slots", text=active_parameter.name)
                else:
                    row.prop(active_parameter, "textparameter", text=active_parameter.name)
                row.prop(active_parameter, "texture", text="", icon='TEXTURE')
            if active_parameter.parametertype == 'float':
                if active_parameter.vector_size == 1:
                    row.prop(active_parameter, "float_one", text=active_parameter.name)
                elif active_parameter.vector_size == 3:
                    row.prop(active_parameter, "float_three", text=active_parameter.name)                    
            if active_parameter.parametertype == 'color':
                row.prop(active_parameter, "colorparameter", text=active_parameter.name)             
    
def checkderived(active_parameter, layout, settings):
    for setting in settings:
        if active_parameter.name == setting:
            layout.prop(active_parameter, "free")
                
grp_menus = {}
attr_menus = {}
def attribute_panel(name, str_path, Pclass):
    def draw_panel(self, context):
        global grp_menus, attr_menus
        scene = context.scene
        active_pass = getactivepass(scene)
        if active_pass:
            #maintain(scene)
            path = eval(str_path)
            rm = scene.renderman_settings
            if eval(str_path) == rm.passes:
                realpath = str_path+'["'+getactivepass(scene).name+'"]'
            else:
                realpath = str_path
            path = eval(realpath)
            layout = self.layout
            row = layout.row(align=True)
            row.operator("attributes.set_as_default", text="set as default", icon="FILE_TICK").path = str_path
            row.operator("attributes.get_default", text="get default", icon="ANIM").path = str_path
            row.operator("attributes."+name+"_remove_all")
            row.menu("Renderman_MT_"+name+"_attribute_menu", icon="ZOOMIN", text="")
            for group in path.attribute_groups:
                box = layout.box()
                row = box.row(align=True)
                row.prop(group, "expand", text="", icon="TRIA_DOWN" if group.expand else "TRIA_RIGHT", emboss=False)
                row.label(text=group.name)
                box.active = group.export
                if not group.name in grp_menus:
                    mname = attribute_options(name, str_path, "", group.name)
                    grp_menus[group.name] = mname
                else:
                    mname = grp_menus[group.name]
                row.menu(mname, icon="DOWNARROW_HLT")
                
                if group.expand:
                    for attribute in group.attributes:
                        master_attribute = context.scene.renderman_settings.attribute_groups[group.name].attributes[attribute.name]
                        row = box.row(align=True)
                        row.active = attribute.export
                        row.label(text=master_attribute.name)
                        parmlayout(attribute, master_attribute, row)
                        if not attribute.name in attr_menus:
                            mname = attribute_options(name, str_path, attribute.name, group.name)
                            attr_menus[attribute.name] = mname
                        else:
                            mname = attr_menus[attribute.name]
                        row.menu(mname, icon="DOWNARROW_HLT")
        else:
            self.layout.label("No Render Pass")
    
    attribute_menu(name, str_path)

    pname = "Renderman_PT_"+name+"_AttributesPanel"    
    type(bpy.types.Panel)(pname, (bpy.types.Panel, Pclass ), {  "bl_label" : "Attributes",
                                                                "COMPAT_ENGINES" : {'RENDERMAN'},
                                                                "draw" : draw_panel})


def attribute_options(name, path, attr, grp):
    if attr == "": is_grp = True 
    else: is_grp = False
    
    grps = eval(path).attribute_groups
    
    ## add/remove/defaults for attributes
    def draw_attr_options(self, context):
        layout = self.layout
        
        op = layout.operator("attributes.remove", text = "Remove")
        op.path = path
        op.attr = attr
        op.grp = grp
        
        if is_grp: ex_path = grps[grp]
        else: ex_path = grps[grp].attributes[attr]
        layout.prop(ex_path, "export", text = "export")
        
        if is_grp:
            opname = "attribute_group.get_default"
        else:
            opname = "attribute.get_default"
            
        op = layout.operator(opname, text="get default")
        op.grp = grps[grp].name
        if not is_grp: op.attr = grps[grp].attributes[attr].name
        op.path = path

        if is_grp:
            opname = "attribute_group.set_default"
        else:
            opname = "attribute.set_default"
                    
        op = layout.operator(opname, text="set default")
        op.grp = grps[grp].name
        if not is_grp: op.attr = grps[grp].attributes[attr].name
        op.path = path
   
    if is_grp: 
        mname = "Renderman_MT_"+name+'_'+grps[grp].name+"_Attribute_Group_Options"
    else:
        mname = "Renderman_MT_"+name+"_"+grps[grp].attributes[attr].name+"_Attribute_Group_Options"
    type(bpy.types.Menu)(mname, (bpy.types.Menu,), {"bl_label" : "",
                                                    "draw" : draw_attr_options})
    return mname

def passes_linking_panel(name, str_path, BClass):
    def draw_passes_linking(self, context):
        path = eval(str_path)
        layout = self.layout
        row = layout.row()
        col = row.column(align=True)
        renderman_settings = context.scene.renderman_settings

        if len(path.renderman) < 15:
            rows = len(path.renderman)+1
        else:
            rows = 15
        
        passes_str_path = str_path+'.renderman'
        col.template_list(path, "renderman", path, "renderman_index", rows=rows)
        col = row.column(align = True)
        col.operator("addpass", icon="ZOOMIN", text="").path = passes_str_path
        col.operator("renderman.rempass", icon="ZOOMOUT", text ="").path = passes_str_path
        ri = path.renderman_index
        if ri < len(path.renderman) and ri >= 0:
            curr_pass = path.renderman[path.renderman_index]
            layout.prop(curr_pass, "name")
        
            col = layout.column(align=True)
            box = col.box()
            row = box.row(align=True)
            row.label("Link to Pass:")
                
            op = row.operator("renderman.change_pass_linking", text="All")
            op.path = passes_str_path
            op.type = "all"
            op = row.operator("renderman.change_pass_linking", text="None")
            op.path = passes_str_path
            op.type = "none"
            op = row.operator("renderman.change_pass_linking", text="Invert")
            op.path = passes_str_path
            op.type = "invert"
            op = row.operator("renderman.change_pass_linking", text="Active")
            op.path = passes_str_path
            op.type = "active"
                                                
            box = col.box()
            for rpass in renderman_settings.passes:
                row = box.row()
                row.label(rpass.name)
                op_col = row.column()
                op_col.active = rpass.name in curr_pass.links
                op = op_col.operator("renderman.link_pass", icon="FILE_TICK", emboss=False)
                op.rpass = rpass.name
                op.path = passes_str_path
    
    pname = 'Renderman_PT_'+name+'Passes_Linking_Panel'        
    type(bpy.types.Panel)(pname, (bpy.types.Panel, BClass), {   "bl_label" : "Passes Linking",
                                                                "COMPAT_ENGINES" : {'RENDERMAN'},
                                                                "draw" : draw_passes_linking})

def attr_preset_menu(name, path):    
    def draw_menu(self, context):
        rmansettings = context.scene.renderman_settings
        target_path = os.path.join(bpy.utils.preset_paths("renderman")[0], rmansettings.active_engine)
        for preset in os.listdir(target_path):
            if preset.find(".preset") != -1:
                p = preset.replace(".preset", "")
                op = self.layout.operator("attribute.load", text=p.replace("_", " "))
                op.preset = p
                op.path = path
    
    mname = "Renderman_MT_"+name+"_attributepresets"
    type(bpy.types.Menu)(mname, (bpy.types.Menu,), {"bl_label" : "Presets",
                                                    "draw" : draw_menu})

                                                        
def attribute_menu(name, path, selected = False): ### create the attribute Menus
    mtype = bpy.types.Menu

    ## root menu
    def draw_root_menu(self, context):
        if name == "object": obj = context.object.name
        else: obj = ""
        layout = self.layout
        layout.menu("Renderman_MT_addnewattribute_"+name)
        layout.menu("Renderman_MT_"+name+"_attributepresets", text="Presets")
        if path != "":
            layout.operator("attribute.add_preset", text="save preset").obj = obj

    ## add Attribute:
    ## Groups   
    def draw_groups(self, context):        
        layout = self.layout
        rman = context.scene.renderman_settings
        for grp in rman.attribute_groups:
            mname = "Renderman_MT_"+grp.name+"addattr"
            type(mtype)(mname, (mtype,), {  "bl_label" : grp.name, 
                                            "grp_name" : grp.name, 
                                            "draw" : draw_attributes,
                                            "path" : path})
            layout.menu(mname)
                                                                
    ## Attributes 
    def draw_attributes(self, context):
        layout = self.layout
        rman = context.scene.renderman_settings
        sub = rman.attribute_groups[self.grp_name].attributes
        for attr in sub:
            attrname = attr.name
            if selected:
                op = layout.operator("attributes.add_new_selected", text=attrname)
            else:
                op = layout.operator("attributes.add_new", text=attrname)
                op.path = path
            op.grp = self.grp_name
            op.attr = attrname
           
    ##create menus
    ##attribute groups
    mname = "Renderman_MT_addnewattribute_"+name      
    type(mtype)(mname, (mtype,), {  "bl_label" : "New Attribute",
                                    "draw" : draw_groups})
                                            
    ##root menu
    mname = "Renderman_MT_"+name+"_attribute_menu"
    type(mtype)(mname, (mtype,), {   "bl_label" : "",
                                        "draw" : draw_root_menu})
        
        
def dimensions_layout(layout, rc, scene):
    col = layout.column(align = True)
    row = col.row(align = True)
    row.prop(rc, "square")
    row.prop(rc, "resx")
    row.prop(rc, "resy")
    if rc.square:
        rc.resy = rc.resx
    row = col.row(align=True)
    row.prop(rc, "aspectx")
    row.prop(rc, "aspecty")
    row = col.row(align=True)
    row.prop(rc, "shift_x")
    row.prop(rc, "shift_y")
    row = col.row(align = True)
    row.prop(rc, "near_clipping", text="Near")
    row.prop(rc, "far_clipping", text="Far")

            
#########################################################################################################
#                                                                                                       #
#      World Panels                                                                                     #
#                                                                                                       #
#########################################################################################################

class WorldButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "world"
    # COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (context.world) and (not rd.use_game_engine) and (rd.engine in cls.COMPAT_ENGINES)


bp = "bpy.context.scene.renderman_settings"
p = bp+".passes["+bp+".passes_index]"
attr_preset_menu("world", p)

class World_PT_RendermanPassesPanel(WorldButtonsPanel, bpy.types.Panel):
    bl_label="Passes"    
    
    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        scene = context.scene
        renderman_settings = scene.renderman_settings
        layout = self.layout
        row = layout.row()
        col = row.column(align=True)

        active_pass = getactivepass(scene)
        if active_pass:

            if len(renderman_settings.passes) < 15:
                rows = len(renderman_settings.passes)+1
            else:
                rows = 15
        
            col.template_list(renderman_settings, "passes", renderman_settings, "passes_index", rows=rows)
            sub_row=col.row(align=True)    
            sub_row.prop_search(renderman_settings, "searchpass", renderman_settings, "passes", icon='VIEWZOOM', text="")
    
            if renderman_settings.passes:
                if len(renderman_settings.passes) == 1 and not renderman_settings.searchpass:
                    renderman_settings.passes_index = 0
                elif renderman_settings.searchpass:
                    for i, passes in enumerate(renderman_settings.passes):
                        if passes.name == renderman_settings.searchpass:
                            renderman_settings.passes_index = i
                            renderman_settings.searchpass = ""   
        else:
            layout.label("No Render Pass")

class Renderman_PT_WorldPanel(WorldButtonsPanel, bpy.types.Panel):
    bl_label = "General World Settings"
    
    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        scene = context.scene
        layout = self.layout
        active_pass = getactivepass(scene)
        if active_pass:
            row = layout.row()
            col = row.column()
            col.prop(active_pass, "exportobjects", text="Export All Objects")
            col = row.column(align=True)
            col.enabled = not active_pass.exportobjects
            col.prop_search(active_pass, "objectgroup", bpy.data, "groups", text="")
            row = layout.row()
            row.prop(active_pass, "exportlights", text="Export All Lights")
            col  = row.column()
            col.enabled = not active_pass.exportlights
            col.prop_search(active_pass, "lightgroup", bpy.data, "groups", text="", icon="LAMP")   
        else:
            layout.label("No Render Pass")

class Render_PT_ImagershaderPanel(WorldButtonsPanel, bpy.types.Panel):
    bl_label = "Imager Shader Parameters"

    COMPAT_ENGINES = {'RENDERMAN'}
    

    def draw(self, context):
        scene = context.scene
        renderman_settings = scene.renderman_settings
        if renderman_settings.passes:
            active_pass = getactivepass(scene)
            layout = self.layout
            row = layout.row(align=True)
            pathcollection = context.scene.renderman_settings.pathcollection
            row.prop_search(active_pass, "imager_shader", pathcollection, "shadercollection", icon='MATERIAL', text="")
            row.operator("refreshshaderlist", text="", icon='FILE_REFRESH')            
            checkshaderparameter("worldi", active_pass, active_pass.imager_shader, active_pass.imager_shader_parameter, scene)

            layout.label(text=shader_info(active_pass.imager_shader, active_pass.imager_shader_parameter, scene))              

            matparmlayout(active_pass.imager_shader_parameter, layout, bpy.data)


class World_PT_SurfaceShaderPanel(bpy.types.Panel, WorldButtonsPanel):
    bl_label = "Surface Shader"
    
    COMPAT_ENGINES = {'RENDERMAN'}

    def draw(self, context):
        scene = context.scene
        #maintain(scene)
        active_pass = getactivepass(scene)
        layout = self.layout
        if active_pass:
            pathcollection = context.scene.renderman_settings.pathcollection
    
            row = layout.row(align = True)
            row.prop_search(active_pass.global_shader, "surface_shader", pathcollection, "shadercollection", text="", icon='MATERIAL')
            row.operator("refreshshaderlist", text="", icon="FILE_REFRESH")
            
            layout.label(text=shader_info(active_pass.global_shader.surface_shader, active_pass.global_shader.surface_shader_parameter, scene))
            checkshaderparameter("worlds", active_pass, active_pass.global_shader.surface_shader, active_pass.global_shader.surface_shader_parameter, scene)
    
            matparmlayout(active_pass.global_shader.surface_shader_parameter, layout, bpy.data)
        else:
            layout.label("No Render Pass")
                            
class World_PT_AtmosphereShaderPanel(bpy.types.Panel, WorldButtonsPanel):
    bl_label = "Atmosphere Shader"
    
    COMPAT_ENGINES = {'RENDERMAN'}

    def draw(self, context):
        scene = context.scene
        ##maintain(scene)
        active_pass = getactivepass(scene)
        layout = self.layout
        if active_pass:
            pathcollection = context.scene.renderman_settings.pathcollection
    
            row = layout.row(align = True)
            row.prop_search(active_pass.global_shader, "atmosphere_shader", pathcollection, "shadercollection", text="", icon='MATERIAL')
            row.operator("refreshshaderlist", text="", icon="FILE_REFRESH")
            
            layout.label(text=shader_info(active_pass.global_shader.atmosphere_shader, active_pass.global_shader.atmosphere_shader_parameter, scene))
            checkshaderparameter("worlda", active_pass, active_pass.global_shader.atmosphere_shader, active_pass.global_shader.atmosphere_shader_parameter, scene)
    
            matparmlayout(active_pass.global_shader.atmosphere_shader_parameter, layout, bpy.data)
        else:
            layout.label("No Render Pass")

string = 'bpy.context.scene.renderman_settings.passes'
string += '[bpy.context.scene.renderman_settings.passes_index]'
attribute_panel("world", string, WorldButtonsPanel)
                

class Renderman_PT_CustomWorldCodePanel(bpy.types.Panel, WorldButtonsPanel):
    bl_label = "Custom World RIB Code"
    
    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        scene = context.scene
        rmansettings = scene.renderman_settings
        active_pass = getactivepass(scene)
        layout = self.layout
        if active_pass:
            layout.label("custom rib code to insert before Word Block:")
            row = layout.row()
            code_length = len(active_pass.world_code)
            rows =code_length if code_length < 10 else 10        
            row.template_list(active_pass, "world_code", active_pass, "world_code_index", rows=rows)
            col = row.column(align=True)
            col.operator("world.ribcode", text="", icon="ZOOMIN")
            col.operator("world.ribcode", text="", icon="ZOOMOUT").add = False
            row = layout.row()      
            if active_pass.world_code:
                row.prop(active_pass.world_code[active_pass.world_code_index], "name")
        else:
            layout.label("No Render Pass")

##################################################################################################################################

#########################################################################################################
#                                                                                                       #
#      Render Panels                                                                                    #
#                                                                                                       #
#########################################################################################################
class Renderman_OT_set_hider(bpy.types.Operator):
    bl_label="set hider"
    bl_idname="hider.set"
    bl_description="set hider for current pass"

    hider = bpy.props.StringProperty()
    
    def invoke(self, context, event):
        rmansettings = context.scene.renderman_settings
        hider = self.hider
        getactivepass(context.scene).hider = hider
    
        return {'FINISHED'}
            
    
class Renderman_MT_hiderlist(bpy.types.Menu):
    bl_label="set hider"
    
    def draw(self, context):
        for hider in getactivepass(context.scene).hider_list:
            self.layout.operator("hider.set", text=hider.name, icon="GHOST_ENABLED").hider = hider.name    

class  RENDERMan_MT_renderenginepresets(bpy.types.Menu):
    bl_label = "Renderengine Presets"
    preset_subdir = "renderman"
    preset_operator = "script.execute_rendermanpreset"

    def draw(self, context):
        layout = self.layout
        main_preset_path = bpy.utils.preset_paths('renderman')[0]
        for file in os.listdir(main_preset_path):
            filepath = os.path.join(main_preset_path, file)
            if os.path.isfile(filepath):
                layout.operator(self.preset_operator, text=file.replace(".py", "")).filepath = filepath

class RenderButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"

    # COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (context.scene and rd.use_game_engine is False) and (rd.engine in cls.COMPAT_ENGINES)
    

class Renderman_PT_Animation(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Animation"
    
    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        scene = context.scene
        layout = self.layout
        split = layout.split(percentage = 0.5)
        col = split.column(align = True)
        col.label("Frame Range:")
        col.prop(scene, "frame_start", text="Start")
        col.prop(scene, "frame_end", text="End")
        col.prop(scene, "frame_step", text="Step")
        col = split.column(align = True)
        col.label("Frame Rate:")
        col.prop(scene.render, "fps")
        col.prop(scene.render, "fps_base", text="/")
        row = col.row(align = True)
        row.prop(scene.render, "frame_map_old", text="Old")
        row.prop(scene.render, "frame_map_new", text = "New")
    
    
class Renderman_PT_Render(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Render"
    
    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()    
        row.operator("renderman.render", text="Image", icon="RENDER_STILL")
        row.operator("renderman.render", text="Animation", icon="RENDER_ANIMATION").anim = True

class Render_PT_RendermanSettings(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Renderman Settings"
    bl_idname = "RenderSettingsPanel"
    bl_default_closed = True

    COMPAT_ENGINES = {'RENDERMAN'}
    

    def draw(self, context):
        global maintaining
        if not maintaining:
            bpy.ops.renderman.maintain()
        scene = context.scene
        rmansettings = scene.renderman_settings
        layout = self.layout
        row = layout.row(align = True)
        row.menu("RENDERMan_MT_renderenginepresets", text=rmansettings.active_engine)
        row.operator("renderengine_preset_add", text="", icon="ZOOMIN")
        
        ## basic render settings (executables, etc.)
        row = layout.row()
        col = row.column(align=True)
        renderer_label_box = col.box()        

        row = renderer_label_box.row(align=True)
        row.prop(rmansettings, "basic_expand", text="", icon="TRIA_DOWN" if rmansettings.basic_expand else "TRIA_RIGHT", emboss=False)
        row.label(text="Basic Settings", icon="PREFERENCES")
        if rmansettings.basic_expand:
            renderer_box = col.box()
            row = renderer_box.row(align=True)            
            col = row.column(align=True)
            col.label(text="Executables:")        
            col.prop(scene.renderman_settings, "renderexec", text="Renderer")
            col.prop(scene.renderman_settings, "shaderexec", text="Compiler")
            col.prop(scene.renderman_settings, "shaderinfo", text="Info")
            col.prop(scene.renderman_settings, "textureexec", text="Texture")
            col = row.column(align=True)
            col.label(text="Extensions:")        
            col.prop(scene.renderman_settings, "shadersource", text="source")
            col.prop(scene.renderman_settings, "shaderbinary", text="binary")
            col.prop(scene.renderman_settings, "textureext", text="texture")

            row = renderer_box.row(align=True)
            col = row.column(align = True)
            col.label(text = "Display Drivers:")   
            col.prop(scene.renderman_settings, "disp_ext_os_default", text="OS Default LIB extension")
            row = col.row(align=True)
            row.prop(scene.renderman_settings, "disp_ext", text="Extension")
            row.enabled = not scene.renderman_settings.disp_ext_os_default
            col.prop(scene.renderman_settings, "displaydrvpath", text="folder")
            col.prop(scene.renderman_settings, "drv_identifier", text="identifier")
            col.prop(scene.renderman_settings, "deepdisplay", text="deep shadow")
            col.prop(scene.renderman_settings, "defaultshadow", text="shadow")
            row = renderer_box.row()
            row.prop(scene.renderman_settings, "facevertex", text='Export UVs as "facevertex"')
        
        ## Hider settings
        col = layout.column(align=True)
        hider_label_box = col.box()
        row = hider_label_box.row(align=True)
        row.prop(rmansettings, "hider_expand", text="", icon="TRIA_DOWN" if rmansettings.hider_expand else "TRIA_RIGHT", emboss=False)
        row.label(text="Hider and Hider Options", icon="PREFERENCES")
        if rmansettings.hider_expand:
            hider_box = col.box()            
            row = hider_box.row()            
            rows = len(scene.renderman_settings.hider_list)+1
            row.template_list(scene.renderman_settings, "hider_list", scene.renderman_settings, "hider_list_index", rows=rows)
            col = row.column(align=True)
            col.operator("addremhider", icon='ZOOMIN', text="")
            col.operator("addremhider", icon='ZOOMOUT', text="").add = False
            
            if scene.renderman_settings.hider_list:
                ogindex = rmansettings.hider_list_index
                if ogindex >= len(rmansettings.hider_list): oqindex = 0   
                selected_hider = scene.renderman_settings.hider_list[ogindex]                
                col.label(text="", icon="FILE_TICK" if (selected_hider.name == rmansettings.default_hider and rmansettings.default_hider != "") else "BLANK1")
                row = hider_box.row(align=True)

                row.operator("addhideroption", text="", icon='ZOOMIN')
                row.prop(selected_hider, "name", text="")
                row.operator("hider.set_default", text="", icon="FILE_TICK").hider = selected_hider.name
                row = hider_box.row()
                hider_option_index = -1                
                for hider_option in selected_hider.options:
                    hider_option_index += 1
                    row = hider_box.row(align=True)
                    row.prop(hider_option, "name", text="")
                    if hider_option.parametertype == "float" or hider_option.parametertype == "int":
                        row.prop(hider_option, "vector_size", text="")
                    row.prop(hider_option, "parametertype", text="") 
                    row.operator("remhideroption", text="", icon="ZOOMOUT").index = hider_option_index                   
        ## Options
        col = layout.column(align=True)
        option_label_box = col.box()
        row = option_label_box.row(align=True)
        row.prop(rmansettings, "options_expand", text="", icon="TRIA_DOWN" if rmansettings.options_expand else "TRIA_RIGHT", emboss=False)
        row.label(text="Options", icon = "PREFERENCES")
        if rmansettings.options_expand:
            option_box = col.box()
            row = option_box.row()
            rows = len(rmansettings.option_groups)+1
            row.template_list(rmansettings, "option_groups", rmansettings, "option_groups_index", rows=rows)
            col = row.column(align=True)
            col.operator("addoptiongroup", text="", icon='ZOOMIN')
            col.operator("removeoptiongroup", text="", icon='ZOOMOUT')
            if rmansettings.option_groups:
                ogindex = rmansettings.option_groups_index
                if ogindex >= len(rmansettings.option_groups): oqindex = 0           
                selected_group = rmansettings.option_groups[ogindex]
                row = option_box.row(align=True)
                row.operator("addoption", text="", icon="ZOOMIN")
                row.prop(selected_group, "name", text="")
                option_index = -1
                for option in selected_group.options:
                    option_index += 1
                    row = option_box.row(align=True)
                    row.prop(option, "name", text="")
                    if option.parametertype == "float" or option.parametertype == "int":
                        row.prop(option, "vector_size", text="")
                    row.prop(option, "parametertype", text="")
                    row.operator("remoption", text="", icon='ZOOMOUT').index = option_index
                    
        ## Attributes
        col = layout.column(align=True)                
        attribute_label_box = col.box()
        row = attribute_label_box.row(align = True)
        row.prop(rmansettings, "attributes_expand", text="", icon="TRIA_DOWN" if rmansettings.attributes_expand else "TRIA_RIGHT", emboss=False)
        row.label(text="Attributes", icon="PREFERENCES")
        if rmansettings.attributes_expand:
            attribute_box = col.box()
            row = attribute_box.row()
            rows = len(rmansettings.attribute_groups)+1
            row.template_list(rmansettings, "attribute_groups", rmansettings, "attribute_groups_index", rows=rows)
            col = row.column(align=True)
            col.operator("addattributegroup", text="", icon='ZOOMIN')
            col.operator("removeattributegroup", text="", icon='ZOOMOUT')
            if rmansettings.attribute_groups:
                agindex = rmansettings.attribute_groups_index
                if agindex >= len(rmansettings.attribute_groups): aqindex = 0
                selected_group = rmansettings.attribute_groups[agindex]
                row = attribute_box.row(align = True)
                row.operator("addattribute", text="", icon='ZOOMIN')
                row.prop(selected_group, "name", text="")
                attribute_index = -1
                for attribute in selected_group.attributes:
                    attribute_index +=1
                    row = attribute_box.row(align=True)
                    row.prop(attribute, "name", text="")
                    if attribute.parametertype == "float" or attribute.parametertype == "int":
                        row.prop(attribute, "vector_size", text="")
                    row.prop(attribute, "parametertype", text="")
                    if attribute.parametertype == 'string':
                        row.prop(attribute, "texture", text="", icon='TEXTURE')                    
                    row.operator("remattribute", text="", icon='ZOOMOUT').index = attribute_index                        
                
        ## Shader Search Paths
        col = layout.column(align=True)
        shader_label_box = col.box()
        row = shader_label_box.row(align=True)
        row.prop(rmansettings, "shader_expand", text="", icon="TRIA_DOWN" if rmansettings.shader_expand else "TRIA_RIGHT", emboss=False)
        row.label(text = "Shader Paths", icon="PREFERENCES")
        if rmansettings.shader_expand:
            shader_box = col.box()
            row = shader_box.row()
            row.template_list(scene.renderman_settings.pathcollection, "shaderpaths", scene.renderman_settings.pathcollection, "shaderpathsindex")
            col = row.column()
            sub = col.column(align=True)
            sub.operator("pathaddrem", text="", icon="ZOOMIN").add = True
            sub.operator("pathaddrem", text="", icon="ZOOMOUT").add = False
            sub.operator("refreshshaderlist", text="", icon="FILE_REFRESH")
            row = shader_box.row()
            row.prop(scene.renderman_settings, "shaderpath", text="")
            
        ## Output Folders
        col = layout.column(align=True)
        dir_label_box = col.box()
        row = dir_label_box.row(align=True)
        row.prop(rmansettings, "dir_expand", text="", icon="TRIA_DOWN" if rmansettings.dir_expand else "TRIA_RIGHT", emboss=False)
        row.label(text = "Output Folders", icon="PREFERENCES")
        if rmansettings.dir_expand:
            dir_box = col.box()
            row = dir_box.row()
            col = row.column(align=True)    
            col.label(getdefaultribpath(scene)+"/...")
            col.prop(scene.renderman_settings, "objectdir", text="Objects")
            col.prop(scene.renderman_settings, "polydir", text="Poly Objects")
            col.prop(scene.renderman_settings, "settingsdir", text="Settings")
            col.prop(scene.renderman_settings, "worlddir", text="World")                          
            col.prop(scene.renderman_settings, "polydir", text="Poly Meshs")
            col.prop(scene.renderman_settings, "particledir", text="Particle Systems")
            col.prop(scene.renderman_settings, "texdir", text="Texture maps")
            col.prop(scene.renderman_settings, "shadowdir", text="Shadowmaps")
            col.prop(scene.renderman_settings, "envdir", text="Envmaps")
            col.prop(scene.renderman_settings, "bakedir", text="Bakefiles")
            row = dir_box.row(align=True)
            row.prop(scene.renderman_settings, "framepadding", text="Frame Padding")
            row.prop(scene.renderman_settings, "exportonly", text="Export Only")
            
        ## Mappings
        col = layout.column(align=True)
        mappings_label_box = col.box()
        row = mappings_label_box.row(align=True)
        row.prop(rmansettings, "mappings_expand", text="", icon="TRIA_DOWN" if rmansettings.mappings_expand else "TRIA_RIGHT", emboss=False)
        row.label(text = "Mappings", icon="PREFERENCES")
        if rmansettings.mappings_expand:
            mappings_box = col.box()
            row = mappings_box.row()
            mappings = rmansettings.mappings
            pathcoll = rmansettings.pathcollection
            col = row.column(align=True)
            col.label("shadowmap parameters")
            col.prop(mappings, "point_shadowpref", text = "Point prefix")
            col.prop(mappings, "shadowmap", text="normal")
            row = mappings_box.row()
            col = row.column(align=True)
            col.label("Default Shaders")
            col.prop_search(mappings, "pointshader", pathcoll, "shadercollection")
            col.prop_search(mappings, "shadowpointshader", pathcoll, "shadercollection")
            col.prop_search(mappings, "spotshader", pathcoll, "shadercollection")
            col.prop_search(mappings, "shadowspotshader", pathcoll, "shadercollection")
            col.prop_search(mappings, "distantshader", pathcoll, "shadercollection")
            col.prop_search(mappings, "shadowdistantshader", pathcoll, "shadercollection")


class Renderman_MT_loadPassPreset(bpy.types.Menu):
    bl_label = "Pass Presets"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        active_engine = scene.renderman_settings.active_engine
        main_preset_path = bpy.utils.preset_paths('renderman')[0]
        sub_preset_path = os.path.join(main_preset_path, active_engine)
 
        for file in os.listdir(sub_preset_path):
            if checkextension(file) == 'pass':
                preset = file.replace(".pass", "")
                layout.operator("renderman.loadpresetpass", text=preset).preset = preset
            
class Renderman_MT_addPresetPass(bpy.types.Menu):
    bl_label="Presets"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        active_engine = scene.renderman_settings.active_engine
        main_preset_path = bpy.utils.preset_paths('renderman')[0]
        sub_preset_path = os.path.join(main_preset_path, active_engine) 
        for file in os.listdir(sub_preset_path):
            if checkextension(file) == 'pass':
                preset = file.replace(".pass", "")
                layout.operator("renderman.addpresetpass", text=preset).preset = preset            

class Renderman_MT_addPassMenu(bpy.types.Menu):
    bl_label = ""
    
    def draw(self, context):
        layout = self.layout
        layout.operator("addpass", text="New").path = "bpy.context.scene.renderman_settings.passes"
        layout.menu("Renderman_MT_addPresetPass")
        layout.operator("renderman.addpasspreset", text = "Save Preset")


class Renderman_PT_RIB_Structure(bpy.types.Panel, RenderButtonsPanel):
    bl_label = "Rib Structure"
    
    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw_archive_panel(self, layout, p, name):
        defaults = {"Settings" : "[pass]_Settings[frame]",
                    "World" : "[pass]_World[frame]",
                    "Object" : "[name][frame]",
                    "Light" : "[name][frame]",
                    "Mesh" :  "[name][frame]",
                    "Particle System" : "[name][frame]",
                    "Pass" : "[scene]_[pass][frame]",
                    "Material" : "[name]_[pass][frame]"}
                
        mcol = layout.column(align=True)
        hbox = mcol.box()
        row = hbox.row(align=True)
        row.prop(p, "expand", text = "", icon = "TRIA_DOWN" if p.expand else "TRIA_RIGHT", emboss=False)
        row.label(name)
        if p.expand:
            bbox = mcol.box()
            bbox.prop(p, "own_file", text="Export to own Archive")
            row = bbox.row()
            row.enabled = p.own_file
            row.prop(p, "default_name")
            col = row.column()
            col.enabled = not p.default_name
            col.prop(p, "filename", text="")
            if p.filename == "" or p.filename == p.default_name: p.filename = defaults[name]
            row.prop(p, "overwrite", text="")
            row = layout.row()
        
    def draw(self, context):
        rm = context.scene.renderman_settings
        rs = rm.rib_structure
        types = {   "Pass" : rs.render_pass,
                    "Settings" : rs.settings,
                    "World" : rs.world,
                    "Object" : rs.objects,
                    "Light" : rs.lights,
                    "Mesh" : rs.meshes,
                    "Particle System" : rs.particles,
                    "Material" : rs.materials}
                        
        for t in types:
            self.draw_archive_panel(self.layout, types[t], t)

            
class Render_PT_RendermanPassesPanel(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Renderman Passes"
    bl_idname = "RenderPassesPanel"
    bl_default_closed = False

    COMPAT_ENGINES = {'RENDERMAN'}
    

    def draw(self, context):
        scene = context.scene
        renderman_settings = scene.renderman_settings
        layout = self.layout
        row = layout.row()
        col = row.column(align=True)

        active_pass = getactivepass(scene)

        if len(renderman_settings.passes) < 15:
            rows = len(renderman_settings.passes)+1
        else:
            rows = 15
    
        col.template_list(renderman_settings, "passes", renderman_settings, "passes_index", rows=rows)
        sub_row=col.row(align=True)    
        sub_row.prop_search(renderman_settings, "searchpass", renderman_settings, "passes", icon='VIEWZOOM', text="")
        sub_row.menu("Renderman_MT_loadPassPreset")
        sub_row.prop(scene.renderman_settings, "exportallpasses", text="All Passes")

     

        col = row.column(align=True)

        col.menu("Renderman_MT_addPassMenu", icon="ZOOMIN")
        col.operator("rempass", text="", icon="ZOOMOUT")
        col.operator("movepass", icon='TRIA_UP', text="").direction = "up"
        col.operator("movepass", icon='TRIA_DOWN', text="").direction = "down"

        if renderman_settings.passes:
            row = layout.row(align=True) 
            row.prop(active_pass, "name", text="")
            row.prop(active_pass, "exportanimation", text="Animate Pass")       
            row = layout.row()
            row.prop(active_pass, "imagedir", text="Image Folder")
        
        
class Renderman_PT_PassCamera(bpy.types.Panel, RenderButtonsPanel):
    bl_label = "Camera"
    
    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        #maintain(context.scene)
        apass = getactivepass(context.scene)
        layout = self.layout
        if apass:
            row = layout.row()
            row.prop_search(apass, "camera_object", context.scene, "objects", text = "Camera")
            row = layout.row()
            row.prop(apass, "environment", text="Environment")
            if apass.camera_object != "" and apass.camera_object in context.scene.objects:
                rc = context.scene.objects[apass.camera_object].renderman_camera
                dimensions_layout(layout, rc, context.scene)
        else:
            layout.label("No Render Pass")

class Renderman_PT_QualityPanel(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Quality"
    
    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        #maintain(scene)        
        active_pass = getactivepass(scene)
        if active_pass:
            row = layout.row(align=True)
            row.prop(active_pass.pixelfilter, "filterlist", text="")
            row.prop(active_pass, "pixelsamples_x", text="X Samples")                                                                       
            row.prop(active_pass, "pixelsamples_y", text="Y Samples")
            if active_pass.pixelfilter.filterlist == "other":
                row.prop(active_pass.pixelfilter, "customfilter")
            row=layout.row(align=True)                            
            row.prop(active_pass.pixelfilter, "filterwidth", text = "Filter width")
            row.prop(active_pass.pixelfilter, "filterheight", text = "Filter height")
        else:
            layout.label("No Render Pass")

class Renderman_PT_MotionBlurPanel(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Motion Blur"
    
    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        ##maintain()
        layout = self.layout
        scene = context.scene
        current_pass = getactivepass(scene)
        if current_pass:
            row = layout.row()
            row.prop(current_pass, "motionblur")
            row = layout.row()
            row.enabled = current_pass.motionblur
            row.prop(current_pass, "shutterspeed")
        else:
            layout.label("No Render Pass")
        
    
class RENDERMANRender_PT_OptionsPanel(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Options"
    bl_idname = "options"
    bl_default_closed = True

    COMPAT_ENGINES = {'RENDERMAN'}
    

    def draw(self, context):
        ##maintain()
        scene = context.scene
        render = scene.render
        renderman_settings = scene.renderman_settings

        if renderman_settings.passes:
            active_pass = getactivepass(scene)
            render = scene.render
            layout = self.layout
            row = layout.row(align=True)
            row.operator("options.set_as_default", text="set as default", icon="FILE_TICK")
            row.operator("options.get_default", text="get default", icon="ANIM")
            
            for group in active_pass.option_groups:
                master_options = renderman_settings.option_groups[group.name].options            
                group_box = layout.box()
                group_box.active = group.export
                row = group_box.row(align=True)
                row.prop(group, "expand", text="", icon="TRIA_DOWN" if group.expand else "TRIA_RIGHT", emboss=False)
                row.label(text = group.name)
                row.prop(group, "export", text="") 
                row.operator("option_group.get_default", text="", icon="ANIM").grp = group.name
                row.operator("option_group.set_default", text="", icon="FILE_TICK").grp = group.name                   
                if group.expand:
                    for option in group.options:
                        master_option = master_options[option.name]
                        row = group_box.row(align=True)
                        row.active = option.export
                        row.label(master_option.name)            
                        parmlayout(option, master_option, row)
                        row.prop(option, "export", text="")
                        row.operator("option.get_current_default", text="", icon="ANIM").grp_opt = group.name + ' ' + option.name
                        row.operator("option.set_current_default", text="", icon="FILE_TICK").grp_opt = group.name + ' ' + option.name  

                        
class Render_PT_RendermanHiderPanel(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Hider"
    bl_idname = "hider"

    COMPAT_ENGINES = {'RENDERMAN'}
    

    def draw(self, context):
        ##maintain()
        scene = context.scene
        layout = self.layout
        renderman_settings = scene.renderman_settings
        if renderman_settings.passes:
            active_pass = getactivepass(scene)
            layout.menu("Renderman_MT_hiderlist", text=active_pass.hider, icon="GHOST_ENABLED")
            if active_pass.hider != "":
                row = layout.row(align=True)
                row.operator("hider.get_default_values", text="get default", icon="ANIM").hider = active_pass.hider
                row.operator("hider.set_default_values", text="set default", icon="FILE_TICK").hider = active_pass.hider
                for master_option in renderman_settings.hider_list[active_pass.hider].options:
                    slave_option = getactivepass(scene).hider_list[active_pass.hider].options[master_option.name]
                    row = layout.row(align=True)
                    row.label(text=master_option.name)
                    parmlayout(slave_option, master_option, row)
                    row.operator("hider_option.get_default", text="", icon="ANIM").hider_option = active_pass.hider + ' ' + master_option.name
                    row.operator("hider_option.set_default", text="", icon="FILE_TICK").hider_option = active_pass.hider + ' ' + master_option.name                              

    
class Render_PT_RendermanDisplayPanel(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Display"
    bl_idname = "display"

    COMPAT_ENGINES = {'RENDERMAN'}
    

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        renderman_settings = scene.renderman_settings
        if renderman_settings.passes:
            active_pass = getactivepass(scene)
            if active_pass:
                layout.operator("adddisplay", text="", icon="ZOOMIN")
                for display_index, display in enumerate(active_pass.displaydrivers):
                    main_box = layout.box()
                    row = main_box.row(align=True)
                    col = row.column()
                    sub_row = col.row(align=True)
                    sub_row.label(text="", icon = "FILE_TICK" if display.send else "BLANK1")                  
                    sub_row.operator("display.send", icon="IMAGE_COL", text="").display = display.name
                    if display.displaydriver == "framebuffer":
                        sub_row.enabled = False
                    else:
                        sub_row.enabled = True                    
                                                
                    row.prop(display, "expand", text="", icon="TRIA_DOWN" if display.expand else "TRIA_RIGHT", emboss=False)
                    row.prop(display, "name", text="")
                    row.prop_search(display, "displaydriver", renderman_settings, "displays", text="", icon="FILE_SCRIPT")
                    row.prop_search(display, "var", renderman_settings, "var_collection", text="", icon="RENDER_RESULT")
                    row.operator("remdisplay", text="", icon="ZOOMOUT").index = display_index
                    if display.expand:
                        row = main_box.row()
                        split = row.split(percentage = 0.25)
                        split.prop(display, "default_name")
                        col = split.column()
    
                        col.label(text=display.filename)
                        r = col.row()
                        r.prop(display, "raw_name")
                        r.enabled = not display.default_name
                        box = main_box.box()
                        row = box.row(align=True)
                        row.prop(display, "quantize_expand", text="", icon="TRIA_DOWN" if display.quantize_expand else "TRIA_RIGHT", emboss=False)
                        row.label(text="Quantize:")
                        if display.quantize_expand:                        
                            row = box.row(align=True)
                            row.prop(display, "quantize_presets", text="")                        
                            row.prop(display, "quantize_min", text="")
                            row.prop(display, "quantize_max", text="")
                            row.prop(display, "quantize_black", text="")
                            row.prop(display, "quantize_white", text="") 
                        box = main_box.box()
                        row = box.row(align=True)
                        row.prop(display, "exposure_expand", text="", icon="TRIA_DOWN" if display.exposure_expand else "TRIA_RIGHT", emboss=False)
                        row.label(text="Exposure:")
                        if display.exposure_expand:
                            row = box.row(align=True)
                            row.prop(display, "gain")                                                
                            row.prop(display, "gamma")
                        box = main_box.box()
                        row = box.row(align=True)
                        row.prop(display, "custom_expand", text="", icon="TRIA_DOWN" if display.custom_expand else "TRIA_RIGHT", emboss=False)
                        row.label("Custom Options:")                        
                        if display.custom_expand:
                            row = box.row(align=True)
                            row.operator("displayoption.add", text="", icon="ZOOMIN").display = display.name
                            for i, option in enumerate(display.custom_options):
                                row = box.row(align=True)
                                row.active = option.export
                                row.prop(option, "name", text="")
                                row.prop(option, "custom_var", text="")
                                    
                                col = row.column()
                                row = col.row(align=True)
                                row.enabled = not option.custom_var 
                                row.prop(option, "parametertype", text="")
                                if option.parametertype == "int" or option.parametertype=="float":
                                    row.prop(option, "vector_size", text="") 
                                row = box.row(align=True)
                                if option.custom_var:
                                    row.label(display.var)
                                    option.parametertype = "string"
                                    option.textparameter = display.var
                                else:                                                                                                                    
                                    parmlayout(option, option, row)
                                row.active = option.export                            
                                row.prop(option, "export", text="")
                                row.operator("displayoption.remove", text="", icon="ZOOMOUT").disp_opt = display.name+" "+str(i)                     
            else:
                layout.label("No Render Pass")


class Renderman_PT_CustomSceneCodePanel(bpy.types.Panel, RenderButtonsPanel):
    bl_label = "Custom Scene RIB Code"
    
    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        scene = context.scene
        rmansettings = scene.renderman_settings
        active_pass = getactivepass(scene)
        if not active_pass:
            self.layout.label("No Render Pass")
        else:
            layout = self.layout
            layout.label("custom rib code to insert before Word Block:")
            row = layout.row()
            code_length = len(active_pass.scene_code)
            rows =code_length if code_length < 10 else 10        
            row.template_list(active_pass, "scene_code", active_pass, "scene_code_index", rows=rows)
            col = row.column(align=True)
            col.operator("scene.ribcode", text="", icon="ZOOMIN")
            col.operator("scene.ribcode", text="", icon="ZOOMOUT").add = False
            row = layout.row()        
            if active_pass.scene_code:
                row.prop(active_pass.scene_code[active_pass.scene_code_index], "name")

##################################################################################################################################

#########################################################################################################
#                                                                                                       #
#      Texture Panels                                                                                   #
#                                                                                                       #
#########################################################################################################


class TextureButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "texture"

    @classmethod
    def poll(cls, context):
        tex = context.texture
        if not tex:
            return False
        engine = context.scene.render.engine
        return (tex.type) and (engine in cls.COMPAT_ENGINES)
    
class RENDERMAN_PT_context_texture(TextureButtonsPanel, bpy.types.Panel):
    bl_label = ""
    bl_options = {'HIDE_HEADER'}
    COMPAT_ENGINES = {'RENDERMAN'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        if not hasattr(context, "texture_slot"):
            return False
        return ((context.material or context.world or context.lamp or context.brush or context.texture)
            and (engine in cls.COMPAT_ENGINES))

    def draw(self, context):
        scene = context.scene
        #maintain(scene)
        layout = self.layout
        slot = context.texture_slot
        node = context.texture_node
        space = context.space_data
        tex = context.texture
        if context.material:
            idblock = context.material
        elif context.lamp:
            idblock = context.lamp
        elif context.world:
            idblock = context.world
        else:
            idblock = context.brush

        tex_collection = type(idblock) != bpy.types.Brush and not node

        if tex_collection:
            row = layout.row()

            row.template_list(idblock, "texture_slots", idblock, "active_texture_index", rows=2)

            col = row.column(align=True)
            col.operator("texture.slot_move", text="", icon='TRIA_UP').type = 'UP'
            col.operator("texture.slot_move", text="", icon='TRIA_DOWN').type = 'DOWN'
            col.menu("TEXTURE_MT_specials", icon='DOWNARROW_HLT', text="")

        row = layout.row()
        if tex_collection:
            row.template_ID(idblock, "active_texture", new="texture.new")
        elif node:
            row.template_ID(node, "texture", new="texture.new")
        elif idblock:
            row.template_ID(idblock, "texture", new="texture.new")

#        if space.pin_id:
        row.template_ID(space, "pin_id")

        col = row.column()

        col.prop(space, "show_brush_texture", text="Brush", toggle=True)

        if tex:
            split = layout.split(percentage=0.2)

            if tex.use_nodes:

                if slot:
                    split.label(text="Output:")
                    split.prop(slot, "output_node", text="")

            else:
                split.label(text="Type:")
                if type(idblock) == bpy.types.Brush:
                    split.prop(tex, "type", text="")
                else:
                    split.prop(tex.renderman, "type", text="", icon="TEXTURE")
                
                types_dict = {"file" : "IMAGE", "envmap" : "ENVIRONMENT_MAP", "none" : "NONE", "bake" : "NONE"}
                
                if not type(idblock) == bpy.types.Brush:
                    tex.type = types_dict[tex.renderman.type]

class TextureTypePanel(TextureButtonsPanel):

    @classmethod
    def poll(cls, context):
        tex = context.texture
        engine = context.scene.render.engine
        return tex and ((tex.renderman.type == cls.tex_type and not tex.use_nodes) and (engine in cls.COMPAT_ENGINES))

    
class Renderman_PT_envmap(TextureTypePanel, bpy.types.Panel):
    bl_label = "Environment Map"
    tex_type = 'envmap'
    COMPAT_ENGINES = {'RENDERMAN'}

    def draw(self, context):
        layout = self.layout

        tex = context.texture
        env = tex.environment_map

        row = layout.row()
        row.prop(env, "source", expand=True)
        row = layout.row()
        col = row.column()
        col.template_ID(tex, "image", open="image.open")
        col.template_image(tex, "image", tex.image_user, compact=True)
        col.enabled = env.source == "IMAGE_FILE"

        row = layout.row()
        row.enabled = env.source != "IMAGE_FILE"
        col = row.column()
#            col.prop(env, "layers_ignore")
        col.label("Resolution:")
        col.prop(tex.renderman, "resolution")
        col.prop(tex.renderman, "depth")
        col.prop(tex.renderman, "fov")
#            col.prop(env, "depth")

        col = row.column(align=True)

        col.label(text="Clipping:")
        col.prop(env, "clip_start", text="Start")
        col.prop(env, "clip_end", text="End")
        
   
class Renderman_TextureFilterPanel(bpy.types.Panel, TextureTypePanel):
    bl_label = "Renderman Filtering"
    tex_type = 'file'
    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        layout = self.layout
        tex = context.texture
        row = layout.row()
        row.prop(tex.renderman, "process")
        master_row = layout.row()
        col = master_row.column(align=True)
        col.label("Filter:")
        col.prop(tex.renderman, "filter", text="")
        row = col.row()
        row.enabled = not tex.renderman.stwidth
        row.prop(tex.renderman, "width")
        col = master_row.column(align=True)
        col.enabled = tex.renderman.stwidth
        row = col.row()
        row.prop(tex.renderman, "stwidth")
        col.prop(tex.renderman, "swidth")
        col.prop(tex.renderman, "twidth")       
    

##################################################################################################################################

#########################################################################################################
#                                                                                                       #
#      Material Panels                                                                                  #
#                                                                                                       #
#########################################################################################################

current_scene = bpy.context.scene

class MaterialButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    # COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return (context.material) and (engine in cls.COMPAT_ENGINES)
    
#class Renderman_PT_materialPreview(bpy.types.Panel, MaterialButtonsPanel):
#    bl_label ="Preview"
#    COMPAT_ENGINES = {'RENDERMAN'}
#    
#    def draw(self, context):
#        global current_scene
#        current_scene = bpy.context.scene
#        self.layout.template_preview(context.material)    

bp = "bpy.context.object.active_material"
np = bp+'.name'
rmp = bp+'.renderman['+bp+'.renderman_index]'

passes_linking_panel("material", "bpy.context.object.active_material", MaterialButtonsPanel)

class RENDERMAN_PT_context_material(MaterialButtonsPanel, bpy.types.Panel):
    bl_label = " "
    bl_show_header = False
    COMPAT_ENGINES = {'RENDERMAN'}

    @classmethod
    def poll(cls, context):
        # An exception, dont call the parent poll func because
        # this manages materials for all engine types

        engine = context.scene.render.engine
        return (context.material or context.object) and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        #maintain(scene)

        mat = context.material
        ob = context.object
        slot = context.material_slot
        space = context.space_data
        split = layout.split(percentage=0.65)
        row = layout.row()

        if ob:
            row.template_list(ob, "material_slots", ob, "active_material_index", rows=2)

            col = row.column(align=True)
            col.operator("object.material_slot_add", icon='ZOOMIN', text="")
            col.operator("object.material_slot_remove", icon='ZOOMOUT', text="")
            split.template_ID(ob, "active_material", new="material.new")
            row = split.row()
            if slot:
                row.prop(slot, "link", text="")
            else:
                row.label()
        elif mat:
            split.template_ID(space, "pin_id")
            split.separator()
        else:
            if ob:
                layout.template_ID(ob, "active_material", new="material.new")
            elif mat:
                layout.template_ID(space, "pin_id")


class RENDERMANMaterial_PT_MotionBlurPanel(MaterialButtonsPanel, bpy.types.Panel):
    bl_label = "MotionBlur"

    COMPAT_ENGINES = {'RENDERMAN'}
    

    def draw(self, context):
        layout = self.layout
        ##maintain(context.scene)
        apass = getactivepass(context.scene)
        if apass:
            m = context.material
            mat = m.renderman[m.renderman_index]
            row = layout.row()
            col = row.column(align=True)
            row.enabled = apass.motionblur
            col.prop(mat, "color_blur")
            col.prop(mat, "opacity_blur")
            col.prop(mat, "shader_blur")
            col = row.column()
            col.prop(mat, "motion_samples")
        else:
            layout.label("No Render Pass")


class RENDERMANMaterial_PT_SurfaceShaderPanel(MaterialButtonsPanel, bpy.types.Panel):
    bl_label = "Surface Shader"
    bl_idname = "SurfaceShaderPanel"

    COMPAT_ENGINES = {'RENDERMAN'}
    

    def draw(self, context):
        scene = context.scene
        ##maintain(scene)
        m = context.object.active_material
        mat = m.renderman[m.renderman_index]
        layout = self.layout
        pathcollection = context.scene.renderman_settings.pathcollection

        row = layout.row(align = True)
        col = row.column()
        col.label(text="Color")
        col.prop(mat, "color", text="")
        context.object.active_material.diffuse_color = mat.color
        col = row.column()
        col.label(text="Opacity")
        col.prop(mat, "opacity", text="")

        row= layout.row(align=True)
        row.prop_search(mat, "surface_shader", pathcollection, "shadercollection", text="", icon='MATERIAL')
        row.operator("refreshshaderlist", text="", icon="FILE_REFRESH")
        
        layout.label(text=shader_info(mat.surface_shader, mat.surface_shader_parameter, scene))
        checkshaderparameter(context.object.active_material.name+"surf", mat, mat.surface_shader, mat.surface_shader_parameter, scene)

        matparmlayout(mat.surface_shader_parameter, layout, context.object.active_material)
    

class RENDERMANMaterial_PT_DisplacementShaderPanel(MaterialButtonsPanel, bpy.types.Panel):
    bl_label = "Displacement Shader"
    bl_idname = "DisplacementShaderPanel"

    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        scene = context.scene
        ##maintain(scene)
        m = context.object.active_material
        mat = m.renderman[m.renderman_index]
        layout = self.layout
        row = layout.row(align=True)
        pathcollection = context.scene.renderman_settings.pathcollection
        row.prop_search(mat, "displacement_shader", pathcollection, "shadercollection", text="", icon='MATERIAL')
        row.operator("refreshshaderlist", text="", icon="FILE_REFRESH")
        layout.label(text=shader_info(mat.displacement_shader, mat.disp_shader_parameter, scene))
        checkshaderparameter(context.object.active_material.name+"disp", mat, mat.displacement_shader, mat.disp_shader_parameter, scene)

        matparmlayout(mat.disp_shader_parameter, layout, context.object.active_material) 
    

class RENDERMANMaterial_PT_InteriorShaderPanel(MaterialButtonsPanel, bpy.types.Panel):
    bl_label = "Interior Shader"
    bl_idname = "InteriorShaderPanel"

    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        scene = context.scene
        ##maintain(scene)
        m = context.object.active_material
        mat = m.renderman[m.renderman_index]
        layout = self.layout
        row = layout.row(align=True)
        pathcollection = context.scene.renderman_settings.pathcollection
        row.prop_search(mat, "interior_shader", pathcollection, "shadercollection", text="", icon="MATERIAL")
        row.operator("refreshshaderlist", text="", icon="FILE_REFRESH")
        layout.label(text=shader_info(mat.interior_shader, mat.interior_shader_parameter, scene))
        checkshaderparameter(context.object.active_material.name+"int", mat, mat.interior_shader, mat.interior_shader_parameter, scene)

        matparmlayout(mat.interior_shader_parameter, layout, context.object.active_material)


class RENDERMANMaterial_PT_ExteriorShaderPanel(MaterialButtonsPanel, bpy.types.Panel):
    bl_label = "Exterior Shader"
    bl_idname = "ExteriorShaderPanel"

    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        scene = context.scene
        ##maintain(scene)
        m = context.object.active_material
        mat = m.renderman[m.renderman_index]
        layout = self.layout
        row = layout.row(align=True)
        pathcollection = context.scene.renderman_settings.pathcollection
        row.prop_search(mat, "exterior_shader", pathcollection, "shadercollection", text="", icon="MATERIAL")
        row.operator("refreshshaderlist", text="", icon="FILE_REFRESH")
        layout.label(text=shader_info(mat.exterior_shader, mat.exterior_shader_parameter, scene))
        checkshaderparameter(context.object.active_material.name+"ext", mat, mat.exterior_shader, mat.exterior_shader_parameter, scene)

        matparmlayout(mat.exterior_shader_parameter, layout, context.object.active_material)
        

class RENDERMANMaterial_PT_AreaLightShaderPanel(MaterialButtonsPanel, bpy.types.Panel):
    bl_label = "Area Light Shader"
    bl_idname = "AreaLightShaderPanel"

    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        scene = context.scene
        ##maintain(scene)
        m = context.object.active_material
        mat = m.renderman[m.renderman_index]
        layout = self.layout
        row = layout.row(align=True)
        pathcollection = context.scene.renderman_settings.pathcollection
        row.prop_search(mat, "arealight_shader", pathcollection, "shadercollection", text="", icon="MATERIAL")
        row.operator("refreshshaderlist", text="", icon="FILE_REFRESH")
        layout.label(text=shader_info(mat.arealight_shader, mat.light_shader_parameter, scene))
        checkshaderparameter(context.object.active_material.name+"al", mat, mat.arealight_shader, mat.light_shader_parameter, scene)

        matparmlayout(mat.light_shader_parameter, layout, context.object.active_material)


        
##################################################################################################################################




################################################################################################################################## 

#########################################################################################################
#                                                                                                       #
#      Light Panels                                                                                     #
#                                                                                                       #
#########################################################################################################


class LightDataButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (context.lamp) and (rd.engine in cls.COMPAT_ENGINES)
    
lbp = 'bpy.context.object.data'

lnp = lbp+'.name'
lrmp = lbp+'.renderman['+lbp+'.renderman_index]'

passes_linking_panel("light", lbp, LightDataButtonsPanel)

class LAMP_PT_RendermanLight(LightDataButtonsPanel, bpy.types.Panel):
    bl_label = "Renderman Settings"

    COMPAT_ENGINES = {'RENDERMAN'}


    def draw(self, context):
        #maintain(context.scene)
        layout = self.layout
        light = context.object
        rc = light.renderman_camera
        scene = context.scene
        lamp = light.data.renderman[light.data.renderman_index]
        type = light.data.type
        rmansettings = light.data.lightsettings
        renderman = lamp
        row = layout.row(align=True)

        pathcollection = context.scene.renderman_settings.pathcollection
        row.prop_search(lamp, "shaderpath", pathcollection, "shadercollection", text="")
        row.operator("refreshshaderlist", text="", icon="FILE_REFRESH")
        row.prop(lamp, "customshader", text="")
        layout.label(text=shader_info(lamp.shaderpath, lamp.light_shader_parameter, scene))
        checkshaderparameter(light.name, lamp, lamp.shaderpath, lamp.light_shader_parameter, scene)
            

        layout.prop(rmansettings, "type")

        matparmlayout(lamp.light_shader_parameter, layout, bpy.data)
        if rmansettings.type == "spot":
            context.object.data.type = "SPOT"

        elif rmansettings.type == "point":
            context.object.data.type = "POINT"

        elif rmansettings.type == "directional":
            context.object.data.type = "SUN"

        layout.prop(lamp, "shadowtype")
        row = layout.row()
        row.enabled = lamp.shadowtype == "shadowmap"
        row.prop(rmansettings, "shadowmaptype")

        if lamp.shadowtype == "shadowmap":
            if light.data.type == "SPOT":
                context.object.data.shadow_method = "BUFFER_SHADOW"
            dimensions_layout(layout, rc, scene)             
    

 




##################################################################################################################################

#########################################################################################################
#                                                                                                       #
#      Object Panels                                                                                    #
#                                                                                                       #
#########################################################################################################

p = "bpy.context.object.renderman"
p += "["+p+"_index]"
attr_preset_menu("object", p)



class ObjectButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (context.object) and (rd.engine in cls.COMPAT_ENGINES) and not (context.object.type in ["LAMP", "CAMERA"])
    
class ObjectAttributesPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (context.object) and (rd.engine in cls.COMPAT_ENGINES) and not (context.object.type in ["CAMERA"])    

passes_linking_panel("object", "bpy.context.object", ObjectButtonsPanel)

class Object_PT_MotionBlurPanel(ObjectButtonsPanel, bpy.types.Panel):
    bl_label ="Motion Blur"
    
    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        scene = context.scene
        ##maintain(scene)
        obj = context.object
        try:
            rman = obj.renderman[obj.renderman_index]
        except IndexError:
            pass
    
        layout = self.layout
        apass = getactivepass(scene)
        if apass:
            row = layout.row()
            col = row.column()
            col.enabled = getactivepass(scene).motionblur
            col.prop(rman, "transformation_blur")
            col.prop(rman, "deformation_blur")
            col.prop(rman, "motion_samples")
        else:
            layout.label("No Render Pass")

class Mesh_PT_IlluminatePanel(ObjectButtonsPanel, bpy.types.Panel):
    bl_label="Renderman Light Linking"

    COMPAT_ENGINES = {'RENDERMAN'}

    def draw(self, context):
        scene = context.scene
        #maintain(scene)
        layout = self.layout
        object = context.object
        renderman_settings = object.renderman[object.renderman_index]
        row=layout.row(align=True)
        row.operator("lightlinking", text="All").type = "all"
        row.operator("lightlinking", text="none").type = "none"
        row.operator("lightlinking", text="invert").type = "invert"
        row.prop_search(object.renderman[object.renderman_index], "lightgroup", bpy.data, "groups")
        row = layout.row()
        col = row.column(align=True)
        header_box = col.box()
        header_box.label("Light List:", icon="LAMP")
        body_box = col.box()
        body_col = body_box.column(align=True)
        for light in renderman_settings.light_list:
            row = body_col.row()
            row.label(light.name)
            row.prop(light, "illuminate", icon='OUTLINER_OB_LAMP' if light.illuminate else 'LAMP', emboss=False, text="")


name = "object"
string = 'bpy.context.object.renderman'
attribute_menu(name, string)
string += '['+string+'_index]'
attribute_panel(name, string, ObjectAttributesPanel)                

class Mesh_PT_GeneralSettings(ObjectButtonsPanel, bpy.types.Panel):
    bl_label ="General Settings"
    bl_idname  ="generalsettings"
    
    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        scene = context.scene
        ##maintain(scene)
        layout = self.layout
        object = context.object
        layout.prop(object.data, "show_double_sided")
        layout.prop(object.renderman[object.renderman_index], "shadingrate")
    
#########################################################################################################
#                                                                                                       #
#      Mesh Panels                                                                                      #
#                                                                                                       #
#########################################################################################################

class MeshDataButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'
    
    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (context.mesh) and (rd.engine in cls.COMPAT_ENGINES)

obp = 'bpy.context.object.data'

onp = obp+'.name'
        
class Mesh_PT_exportOptions(bpy.types.Panel, MeshDataButtonsPanel):

    bl_label = 'Export Options'
    
    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mesh = context.object.data
        row = layout.row()
        row.prop(mesh, "primitive_type")
        row = layout.row(align=True)
        row.enabled = mesh.primitive_type == 'Points'
        row.prop_search(mesh, "size_vgroup", context.object, "vertex_groups", text="")
        row.prop(mesh, 'points_scale', text="")
        row = layout.row()        
        row.prop(mesh, "export_type")
        
        
##################################################################################################################################

#########################################################################################################
#                                                                                                       #
#      Camera Panels                                                                                    #
#                                                                                                       #
#########################################################################################################


class CameraDataButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = "WINDOW"
    bl_context = "data"    
    bl_label=""

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (context.camera) and (rd.engine in cls.COMPAT_ENGINES)

class Camera_PT_dimensions(bpy.types.Panel, CameraDataButtonsPanel):
    bl_label = "Dimensions"
    
    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        camera = context.object
        cam = camera.data
        scene = context.scene
        layout = self.layout
        apass = getactivepass(scene)
        if apass:
            rc = cam.renderman_camera
            dimensions_layout(layout, rc, scene)
            row = layout.row()
            row.prop(rc, "depthoffield", text="Depth Of Field")
            row = layout.row()
            row.enabled = rc.depthoffield
            cola = row.column(align=True)
            cola.prop(rc, "dof_distance", text="Focus Distance")
            cola.prop(rc, "fstop")
            cola.prop(rc, "use_lens_length")
            row = layout.row()
            row.enabled = rc.depthoffield and not rc.use_lens_length
            row.prop(rc, "focal_length")
    
            row = layout.row(align=True)
            row.prop(cam, "type", text="")
    
            row.prop(cam, "lens_unit", text = "")
            if cam.lens_unit == "MILLIMETERS":
                row.prop(cam, "lens", text="")
            else:
                row.prop(cam, "angle", text="")
                
            row = layout.row()
            col = row.column()
            col.enabled = getactivepass(scene).motionblur
            col.prop(camera.renderman[camera.renderman_index], "transformation_blur")
            #col.prop(camera.renderman[camera.renderman_index], "perspective_blur")
            row = col.row()
            transformation_blur = camera.renderman[camera.renderman_index].transformation_blur
            row.enabled = transformation_blur
            row.prop(camera.renderman[camera.renderman_index], "motion_samples") 
        else:
            layout.label("No Render Pass")         
                

#passes_linking_panel("camera", "bpy.context.object", CameraDataButtonsPanel)
    

class Renderman_PT_CameraLens(CameraDataButtonsPanel, bpy.types.Panel):
    bl_label = "Renderman Lens Settings"
    bl_idname = "rendermanlens"

    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        scene = context.scene
        #maintain(scene)
        camera = scene.camera
        layout = self.layout

        row = layout.row()
        col = row.column(align=True)
        col.prop(camera.data, "clip_start")
        col.prop(camera.data, "clip_end")
        col = row.column(align=True)
        col.prop(camera.data, "shift_x")
        col.prop(camera.data, "shift_y")


##################################################################################################################################

#########################################################################################################
#                                                                                                       #
#      Particle Panels                                                                                  #
#                                                                                                       #
#########################################################################################################

class ParticleButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "particle"
    
    @classmethod
    def poll(cls, context):
        return properties_particle.particle_panel_poll(cls, context)
    
obp = "bpy.context.particle_system"

onp = obp+'.name'
ormp = obp+'.settings.renderman['+obp+'.renderman_index]'  

passes_linking_panel("particle", obp+'.settings', ParticleButtonsPanel)

class Renderman_PT_ParticleMBPanel(bpy.types.Panel, ParticleButtonsPanel):
    bl_label = "Motion Blur"
    
    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        scene = context.scene
        #maintain(scene)
        layout = self.layout
        psystem = context.particle_system
        rman =psystem.settings.renderman[psystem.settings.renderman_index]
    
        layout.prop(rman, "motion_blur")
        layout.prop(rman, "motion_samples")
                        
    
class Renderman_PT_ParticleRenderSettings(bpy.types.Panel, ParticleButtonsPanel):
    bl_label = "Render"
    
    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        scene = context.scene
        active_pass = getactivepass(scene)
        layout = self.layout
        if active_pass:
            pathcollection = context.scene.renderman_settings.pathcollection
            
            psystem = context.particle_system
            obj = context.object
            if psystem.settings.renderman:
                rman = psystem.settings.renderman[psystem.settings.renderman_index]
        
                row = layout.row()
                col = row.column(align=True)
                
                ##  surface shader
                surf_header_box = col.box()
                row = surf_header_box.row(align=True)
                row.prop(rman, "surface_expand", text="", icon="TRIA_DOWN" if rman.surface_expand else "TRIA_RIGHT", emboss=False)
                row.label("Surface Shader", icon="MATERIAL")
                if rman.surface_expand:
                    surf_box = col.box()
                    row = surf_box.row(align = True)
                    row.prop_search(rman.shaders, "surface_shader", pathcollection, "shadercollection", text="", icon='MATERIAL')
                    row.operator("refreshshaderlist", text="", icon="FILE_REFRESH")
                    
                    surf_box.label(text=shader_info(rman.shaders.surface_shader, rman.shaders.surface_shader_parameter, scene))
                    checkshaderparameter(obj.name+psystem.name+"surf", active_pass, rman.shaders.surface_shader, rman.shaders.surface_shader_parameter, scene)
        
                    matparmlayout(rman.shaders.surface_shader_parameter, surf_box, bpy.data)
                
                row = layout.row()    
                col = row.column(align=True)
                            
                ##  displacement shader
                disp_header_box = col.box()
                row = disp_header_box.row(align=True)
                row.prop(rman, "disp_expand", text="", icon="TRIA_DOWN" if rman.disp_expand else "TRIA_RIGHT", emboss=False)
                row.label("Displacement Shader", icon="MATERIAL")
                if rman.disp_expand:
                    disp_box = col.box()
                    row = disp_box.row(align = True)
                    row.prop_search(rman.shaders, "displacement_shader", pathcollection, "shadercollection", text="", icon='MATERIAL')
                    row.operator("refreshshaderlist", text="", icon="FILE_REFRESH")
                    
                    disp_box.label(text=shader_info(rman.shaders.displacement_shader, rman.shaders.disp_shader_parameter, scene))
                    checkshaderparameter(obj.name+psystem.name+"disp", active_pass, rman.shaders.displacement_shader, rman.shaders.disp_shader_parameter, scene)
        
                    matparmlayout(rman.shaders.disp_shader_parameter, disp_box, bpy.data)
                
                row = layout.row()    
                col = row.column(align=True)
                
                ##  interior shader
                int_header_box = col.box()
                row = int_header_box.row(align=True)
                row.prop(rman, "interior_expand", text="", icon="TRIA_DOWN" if rman.interior_expand else "TRIA_RIGHT", emboss=False)
                row.label("Interior Shader", icon="MATERIAL")
                if rman.interior_expand:
                    int_box = col.box()
                    row = int_box.row(align = True)
                    row.prop_search(rman.shaders, "interior_shader", pathcollection, "shadercollection", text="", icon='MATERIAL')
                    row.operator("refreshshaderlist", text="", icon="FILE_REFRESH")
                    
                    int_box.label(text=shader_info(rman.shaders.interior_shader, rman.shaders.interior_shader_parameter, scene))
                    checkshaderparameter(obj.name+psystem.name+"int", active_pass, rman.shaders.interior_shader, rman.shaders.interior_shader_parameter, scene)
        
                    matparmlayout(rman.shaders.interior_shader_parameter, int_box, bpy.data)
                
                row = layout.row()    
                col = row.column(align=True)
                ##  exterior shader
                ext_header_box = col.box()
                row = ext_header_box.row(align=True)
                row.prop(rman, "exterior_expand", text="", icon="TRIA_DOWN" if rman.exterior_expand else "TRIA_RIGHT", emboss=False)
                row.label("Exterior Shader", icon="MATERIAL")
                if rman.exterior_expand:
                    ext_box = col.box()
                    row = ext_box.row(align = True)
                    row.prop_search(rman.shaders, "exterior_shader", pathcollection, "shadercollection", text="", icon='MATERIAL')
                    row.operator("refreshshaderlist", text="", icon="FILE_REFRESH")
                    
                    ext_box.label(text=shader_info(rman.shaders.exterior_shader, rman.shaders.exterior_shader_parameter, scene))
                    checkshaderparameter(obj.name+psystem.name+"ext", active_pass, rman.shaders.exterior_shader, rman.shaders.exterior_shader_parameter, scene)
        
                    matparmlayout(rman.shaders.exterior_shader_parameter, ext_box, bpy.data)
                
                row = layout.row()
                col = row.column(align=True)    
                ##  arealight shader
                area_header_box = col.box()
                row = area_header_box.row(align=True)
                row.prop(rman, "arealight_expand", text="", icon="TRIA_DOWN" if rman.arealight_expand else "TRIA_RIGHT", emboss=False)
                row.label("Arealight Shader", icon="MATERIAL")
                if rman.arealight_expand:
                    area_box = col.box()
                    row = area_box.row(align = True)
                    row.prop_search(rman.shaders, "arealight_shader", pathcollection, "shadercollection", text="", icon='MATERIAL')
                    row.operator("refreshshaderlist", text="", icon="FILE_REFRESH")
                    
                    area_box.label(text=shader_info(rman.shaders.arealight_shader, rman.shaders.light_shader_parameter, scene))
                    checkshaderparameter(obj.name+psystem.name+"area", active_pass, rman.shaders.arealight_shader, rman.shaders.light_shader_parameter, scene)
        
                    matparmlayout(rman.shaders.light_shader_parameter, area_box, bpy.data)  
                    
                layout.prop(rman, "render_type")
                if rman.render_type == "Object":
                    psystem.settings.render_type = 'OBJECT'
                    if rman.object in scene.objects:
                        psystem.settings.dupli_object = scene.objects[rman.object]
                    layout.prop_search(rman, "object", scene, "objects")
                elif rman.render_type == "Archive":
                    layout.prop(rman, "archive")
                elif rman.render_type == "Group":
                    layout.prop_search(rman, "group", bpy.data, "groups")
        else:
            layout.label("No Render Pass")


### Attributes
name = "particle"
string = 'bpy.context.particle_system.settings.renderman'      
attribute_menu(name, string)

i = string+'_index'
string += '['+i+']'
attribute_panel(name, string, ParticleButtonsPanel)

attr_preset_menu(name, string)

##################################################################################################################################

#########################################################################################################
#                                                                                                       #
#      Empty Panels                                                                                     #
#                                                                                                       #
#########################################################################################################   


#class EmptyButtonsPanel():
#    bl_space_type = "PROPERTIES"
#    bl_region_type = "WINDOW"
#    bl_context = "Object"
#    
#    def poll(cls, context):
#        return 
#    def draw(self, context):
#        layout = self.layout
                                                              
    
##################################################################################################################################

#########################################################################################################
#                                                                                                       #
#      Text Editor Panels                                                                               #
#                                                                                                       #
#########################################################################################################


class Renderman_PT_RendermanShaderPanel(bpy.types.Panel):
    bl_space_type = "TEXT_EDITOR"
    bl_region_type = "UI"
    bl_label = "RSL"
    
    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return rd.engine == 'RENDERMAN'

    def draw(self, context):
        #maintain(context.scene)
        layout = self.layout
        layout.operator("text.compileshader")


##################################################################################################################################

#########################################################################################################
#                                                                                                       #
#      3D View                                                                                          #
#                                                                                                       #
#########################################################################################################
attribute_menu("obj_selected", "", selected = True)

class Renderman_MT_object_specials(bpy.types.Menu):
    bl_label = "Renderman"
    
    def draw(self, context):
        self.layout.menu("Renderman_MT_obj_selected_attribute_menu", text="Attributes")
        self.layout.menu("Renderman_MT_LightLinking")
        
class Renderman_MT_LightLinking(bpy.types.Menu):
    bl_label="Light Linking"
    
    def draw(self, context):
        layout = self.layout
        layout.operator("renderman.light_linking", text = "Add").type = "add"
        layout.operator("renderman.light_linking", text = "Remove").type = "remove"
        layout.operator("renderman.light_linking", text = "Exclusive").type = "exclusive"        

def draw_obj_specials_rm_menu(self, context):
    self.layout.menu("Renderman_MT_object_specials")



class Renderman_MT_obj_selected_attributepresets(bpy.types.Menu):
    bl_label = "Load Attribute Preset"
    
    def draw(self, context):
        rmansettings = context.scene.renderman_settings
        target_path = os.path.join(bpy.utils.preset_paths("renderman")[0], rmansettings.active_engine)
        for preset in os.listdir(target_path):
            if preset.find(".preset") != -1:
                p = preset.replace(".preset", "")
                self.layout.operator("attribute.load_selected", text=p.replace("_", " ")).preset = p


class Renderman_PT_3D_View_Ops(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Renderman"
    
    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return rd.engine == 'RENDERMAN'
    
    def draw(self, context):
        #maintain(context.scene)
        layout = self.layout
        layout.menu("Renderman_MT_object_specials")
