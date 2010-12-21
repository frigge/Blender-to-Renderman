
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

##################################################################################################################################

                                  
##################################################################################################################################
#                                                                                                                                #
#       Render Engine Preset Class                                                                                               #
#                                                                                                                                #
##################################################################################################################################

import bpy
import export_renderman
import export_renderman.rm_maintain
from export_renderman.rm_maintain import *

String = bpy.props.StringProperty
Bool = bpy.props.BoolProperty
Enum = bpy.props.EnumProperty
CollectionProp = bpy.props.CollectionProperty
Pointer = bpy.props.PointerProperty
FloatVector = bpy.props.FloatVectorProperty
IntVector = bpy.props.IntVectorProperty
Int = bpy.props.IntProperty
Float = bpy.props.FloatProperty

def checkForPath(target_path): # create Presetsdirecory if not found
    try:
        if os.path.exists(target_path):
            pass
        else:
            os.mkdir(target_path)
    except:
        pass
    
    
def clear_collections(scene):
    if scene == None: scene = bpy.context.scene
    rmansettings = scene.renderman_settings
    shaderpaths = rmansettings.shaders.shaderpaths
    attributes = rmansettings.attribute_groups
    options = rmansettings.option_groups
    hiders = rmansettings.hider_list
    
    collections = [shaderpaths, attributes, options, hiders]
    
    def remcollection(coll):
        for i in range(len(coll)): coll.remove(0)
    
    for c in collections: remcollection(c)
        
    
class ExecuteRendermanPreset(bpy.types.Operator):
    ''' Executes a preset '''
    bl_idname = "script.execute_rendermanpreset"
    bl_label = "Execute a Python Preset"

    filepath = bpy.props.StringProperty(name="Path", description="Path of the Python file to execute", maxlen=512, default="")

    def execute(self, context):
#        # change the menu title to the most recently chosen option
#        preset_class = getattr(bpy.types, self.menu_idname)
#        preset_class.bl_label = self.preset_name

        context.scene.renderman_settings.active_engine = os.path.split(self.filepath)[1].replace(".py", "")

        # execute the preset using script.python_file_run
        clear_collections(context.scene)
        bpy.ops.script.python_file_run(filepath=self.filepath)
        return {'FINISHED'}



class AddPresetRenderer(bpy.types.Operator):
    '''Add a Render Engine Preset'''
    bl_idname = "renderengine_preset_add"
    bl_label = "Add Renderman Preset"

    name = bpy.props.StringProperty(name="Name", 
                                    description="Name of the preset, used to make the path name", 
                                    maxlen=64, 
                                    default="")
    
    preset_subdir = "renderman"

    preset_values = [
        "bpy.context.scene.renderman_settings.renderexec",
        "bpy.context.scene.renderman_settings.shaderexec",
        "bpy.context.scene.renderman_settings.textureexec",
        "bpy.context.scene.renderman_settings.shadersource",
        "bpy.context.scene.renderman_settings.shaderbinary",
        "bpy.context.scene.renderman_settings.shaderinfo",
        "bpy.context.scene.renderman_settings.textureext",
        "bpy.context.scene.renderman_settings.disp_ext",
        "bpy.context.scene.renderman_settings.disp_ext_os_default",
        "bpy.context.scene.renderman_settings.displaydrvpath",
        "bpy.context.scene.renderman_settings.drv_identifier",
        "bpy.context.scene.renderman_settings.deepdisplay",
        "bpy.context.scene.renderman_settings.defaultshadow",
        "bpy.context.scene.renderman_settings.default_hider",
        "bpy.context.scene.renderman_settings.mappings.point_shadowpref",
        "bpy.context.scene.renderman_settings.mappings.shadowmap",
        "bpy.context.scene.renderman_settings.mappings.pointshader",
        "bpy.context.scene.renderman_settings.mappings.shadowpointshader",
        "bpy.context.scene.renderman_settings.mappings.spotshader",
        "bpy.context.scene.renderman_settings.mappings.shadowspotshader",
        "bpy.context.scene.renderman_settings.mappings.distantshader",
        "bpy.context.scene.renderman_settings.mappings.shadowdistantshader",
    ]
    
    collection_path = []
    
    def _as_filename(self, name): # could reuse for other presets
        name = bpy.path.clean_name(name, replace='_')
        return name.lower()    
    
    def execute(self, context):
        scene = context.scene                        ### Modified AddPresetBase Class to allow CollectionProperties
        if not self.name:
            return {'FINISHED'}
        presetname = self._as_filename(self.name)
        filename = self.name

        target_path = bpy.utils.preset_paths(self.preset_subdir)[0] # we need some way to tell the user and system preset path

        filepath = os.path.join(target_path, filename)
        checkForPath(target_path)
        
        file_preset = open(filepath, 'w')
        write = file_preset.write
        write("import bpy\n")
            
        for rna_path in self.preset_values:
            try:
                value = eval(rna_path)
                write(rna_path+' = '+repr(value)+'\n')
            except:
                pass
                        
        rmansettings = bpy.context.scene.renderman_settings
        option_groups = rmansettings.option_groups
        attribute_groups = rmansettings.attribute_groups
        hider_list = rmansettings.hider_list
        shaderpaths = rmansettings.shaders.shaderpaths
        
        def parmgroups(group):      
            parmprops = [   ".parametertype", 
                            ".vector_size", 
                            ".texture", 
                            ".textparameter", 
                            ".colorparameter[0]",
                            ".colorparameter[1]",
                            ".colorparameter[2]",
                            ".float_one[0]",
                            ".float_two[0]",
                            ".float_two[1]",
                            ".float_three[0]",
                            ".float_three[1]",
                            ".float_three[2]",
                            ".int_one[0]",
                            ".int_two[0]",
                            ".int_two[1]",
                            ".int_three[0]",
                            ".int_three[1]",
                            ".int_three[2]"]
            path =  'bpy.context.scene.renderman_settings.'+group              
            for g in eval(path):
                write('if not "'+g.name+'" in '+path+':\n')
                write('\t'+path+'.add().name = "'+g.name+'"\n')            
                g_path = path+'["'+g.name+'"]'
                t = {   'attribute_groups' : '.attributes', 
                        'option_groups' : '.options', 
                        'hider_list' : '.options'}
                parms = g_path+t[group]
                for p in eval(parms):
                    write('if not "'+p.name+'" in '+parms+':\n')
                    write('\t'+parms+'.add().name = "'+p.name+'"\n')                    
                    p_path = parms+'["'+p.name+'"]'
                    for prop in parmprops:
                        prop_path = p_path+prop
                        if prop in ['.textparameter', '.parametertype']:
                            val = '"'+eval(prop_path)+'"'
                        else:
                            val = str(eval(prop_path))
                        write(prop_path + ' = ' + val +'\n')

        
        ##option presets:
        parmgroups("option_groups")
        
        ##attribute presets:    
        parmgroups("attribute_groups")
        
        ##shaderpath presets:
        s_path = "bpy.context.scene.renderman_settings.shaders.shaderpaths"
        for path in shaderpaths:
            write('if not "'+path.name+'" in '+s_path+':\n')
            write('\t'+s_path+'.add().name = "'+path.name+'"\n')
        
        ##hider presets:
        parmgroups("hider_list")

        file_preset.close()

        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        #crashes, TODO - fix
        #return wm.invoke_props_popup(self, event)

        wm.invoke_props_popup(self, event)
        return {'RUNNING_MODAL'}


def write_sub_preset(grp, sub_path, write):
    export = {True : "1", False : "0"}
    for sub in sub_path:
        if sub.preset_include:
            float_size = {1 : sub.float_one, 2 : sub.float_two, 3 : sub.float_three}
            int_size = {1 : sub.int_one, 2 : sub.int_two, 3 : sub.int_three}
            type = {"float" : float_size, "int" : int_size}

            ptype = sub.parametertype
            
            write(grp.name + " " + sub.name + " ")
            if ptype == "string":
                write('"'+sub.textparameter+'" ')
            elif ptype == "color":
                r, g, b = sub.colorparameter
                write("("+str(r)+" "+str(g)+" "+str(b)+") ")
            elif ptype in ["float", "int"]:
                v = sub.vector_size
                if v == 1:
                    a = type[ptype][v][0]
                    write(str(a)+" ")
                elif v == 2:
                    a, b = type[ptype][v]
                    write("("+str(a)+" "+str(b)+") ")
                elif v == 3:
                    a, b, c = type[ptype][v]
                    write("("+str(a)+" "+str(b)+" "+str(c)+") ")
            write(export[sub.export]+"\n")
            
            
def write_grp_preset(path, type, write):
    gtype = {   "attr" : path.attribute_groups,
                "opt" : path.option_groups}
                                    
    for grp in gtype[type]:
        export = {True : "1", False : "0"}
        if grp.preset_include:
            write(grp.name+" "+export[grp.export]+"\n")
            stype = {   'attr' : grp.attributes,
                        'opt' : grp.options}               
            write_sub_preset(grp, stype[type], write)
    
class WriteAttributePreset(bpy.types.Operator):
    bl_label = "write Preset"
    bl_idname = "attribute.write_preset"
    bl_description = "write preset"

    obj = bpy.props.StringProperty(default = "", name="Object Name")       
    
    def execute(self, context):
        scene = context.scene
        rmansettings = context.scene.renderman_settings
        target_path = bpy.utils.preset_paths(rmansettings.active_engine)[0]
        checkForPath(target_path)
        filename = rmansettings.presetname+".preset"
        rmansettings.presetname = ""
        filename = filename.replace(" ", "_")
        subpreset = os.path.join(target_path, filename)
        
        try:
            file = open(subpreset, "w")
        except:
            print("file not found")
            return {'CANCELLED'}
        
        if self.obj:
            obj = scene.objects[self.object]
            rna_path = obj.renderman[obj.renderman_index]
        else: rna_path = getactivepass(context.scene)
            
        write_grp_preset(rna_path, "attr")
                    
        return {'FINISHED'}  
    

class AddAttributePreset(bpy.types.Operator):
    bl_label = "add Preset"
    bl_idname = "attribute.add_preset"
    bl_description = "add preset for current attributes"
    
    obj = bpy.props.StringProperty(default = "", name="Object Name")
    
    def invoke(self, context, event):
        wm = context.window_manager
        wm.invoke_popup(self, width=800)
        return{'RUNNING_MODAL'}
    
    def draw(self, context):
        renderman_settings = context.scene.renderman_settings
        layout = self.layout
        cols = 0
        for g in getactivepass(context.scene).attribute_groups:
            if cols == 0: 
                row = layout.row()
            col = row.column()
            sub_row = col.row()                
            sub_row.prop(g, "preset_include", text=g.name)
            cols +=1
            if cols == 5: cols = 0
            
            for a in g.attributes:
                sub_row = col.row(align=True)
                sub_row.prop(a, "preset_include", text="- "+a.name)
        row = layout.row()
        row.prop(renderman_settings, "presetname")
        row.operator("attribute.write_preset", text="write Preset").obj = self.obj

def load_sub_preset(sub_path, line):
    export = {"1" : True, "0" : False}
    raw_value = ""
    if line.find("(") != -1:
        raw_value = line[line.find("("):line.find(")")].replace("(", "")
        line = line.replace("("+raw_value+")", "")
        val = raw_value.split()
        grp_name, sub_name, ex = line.split()
    else:
        grp_name, sub_name, val, ex = line.split()
    
    if not sub_name in sub_path:
        sub_path.add().name = sub_name
    sub = sub_path[sub_name]
    
    ptype = sub.parametertype
    float_size = {1 : sub.float_one, 2 : sub.float_two, 3 : sub.float_three}
    int_size = {1 : sub.int_one, 2 : sub.int_two, 3 : sub.int_three}
                    
    sub.export = export[ex]
    if ptype == "string": sub.textparameter = val.replace('"', '')
    
    elif ptype == "color":
        for i, v in enumerate(val): 
            sub.colorparameter[i] = float(v)        
                                         
    elif ptype == "float":
        if sub.vector_size > 1:
            for i, v in enumerate(val):
                float_size[sub.vector_size][i] = float(v)
        else:                       
            float_size[sub.vector_size][0] = float(val)
        
    elif ptype == "int":
        if sub.vector_size > 1:
            for i, v in enumerate(val):
                int_size[sub.vector_size][i] = int(v)
        else:
            int_size[sub.vector_size][0] = int(val)
                   
def load_grp_preset(prs, path, type):
    if type == "attr": grps = path.attribute_groups
    else: grps = path.option_groups
    
    export = {"0" : False, "1" : True}
        
    for line in prs:              
        if len(line.split()) == 2:
            grp_name, grp_export = line.split()
            if not grp_name in grps: grps.add().name = grp_name
            grps[grp_name].export = export[grp_export]
            
        else:
            stype = {   "attr" : grps[grp_name].attributes,
                        "opt" : grps[grp_name].options}
            sub = stype[type]
            load_sub_preset(sub, line)

                    
    
class LoadAttributePreset(bpy.types.Operator):
    bl_label = "load Preset"
    bl_idname = "attribute.load"
    bl_description = "load preset"
    
    preset = String(default = "")
    path = String(default = "")
    
    def execute(self, context):
        scene = context.scene
        rmansettings = context.scene.renderman_settings
        target_path = os.path.join(bpy.utils.preset_paths("renderman")[0], rmansettings.active_engine)

        preset = self.preset
        path = eval(self.path)
            
        filename = preset+".preset"
        subpreset = os.path.join(target_path, filename)
        
        try:
            file = open(subpreset, "r")
        except:
            print("file not found")
            return {'CANCELLED'}

        attributes = file.readlines()
        load_grp_preset(attributes, path, "attr")
                    
        return {'FINISHED'}
   
   
class LoadAttributePresettoSelected(bpy.types.Operator):
    bl_label = "load Preset"
    bl_idname = "attribute.load_selected"
    bl_description = "load Attribute Preset to selected"
    
    preset = bpy.props.StringProperty()
    
    def execute(self, context):
        preset = self.preset
        for obj in context.scene.objects:
            if obj.select:
                bpy.ops.attribute.load(preset_obj = preset+" "+obj.name)
                
        return {'FINISHED'}
   
##################################################################################################################################
class Renderman_OT_Set_Pass_Index(bpy.types.Operator):
    bl_label = ""
    bl_idname = "renderman.set_pass_index"

    def execute(self, context):
        rm = context.scene.renderman_settings
        rm.passes_index = len(rm.passes)-1
        return {'FINISHED'}

#########################################################################################################
#                                                                                                       #
#       Operators                                                                                       #
#       (mainly for adding/removing and moving items of CollectionProperties)                           #
#                                                                                                       #
#########################################################################################################

#############################################
#                                           #
#   Light Linking Operator                  #
#                                           #
#############################################

class Renderman_OT_LightLinking(bpy.types.Operator):
    bl_label="Light Linking"
    bl_idname="lightlinking"
    bl_description="Light Linking"

    type = bpy.props.EnumProperty(items = (
                                            ("all", "", ""),
                                            ("none", "", ""),
                                            ("invert", "", "")
                                            ),
                                    default = "all"
                                    )

    def invoke(self, context, event):
        scene = context.scene
        obj = context.object
        for item in obj.renderman[obj.renderman_index].light_list:
            type = self.type
            if type == "invert":
                item.illuminate = not item.illuminate 
            elif type == "all":
                item.illuminate = True 
            elif type == "none":
                item.illuminate = False 

        return {'FINISHED'}

#############################################
#                                           #
#   Display Operator                        #
#                                           #
#############################################

def adddisp(active_pass, name = "Default", display="framebuffer", var="rgba", is_aov=False, aov=""):
    defcount = 1

    def getdefname(name, count):
        countstr = "0"*(2 - len(str(count))) + str(count)
        defaultname = name+countstr
        return defaultname

    defname = getdefname(name, defcount)

    for item in active_pass.displaydrivers:
        if item.name == defname:
            defcount +=1
            defname = getdefname(name, defcount)

    active_pass.displaydrivers.add().name = defname
    dispdriver = active_pass.displaydrivers[defname]
    dispdriver.displaydriver = display
    dispdriver.var = var
    dispdriver.is_aov = is_aov
    dispdriver.aov = aov
    return defname

class Renderman_OT_addDisplay(bpy.types.Operator):
    bl_label = "addDisplay"
    bl_idname = "adddisplay"
    bl_description = "add Display Driver"
    
    def invoke(self, context, event):
        adddisp(getactivepass(context.scene))
        return {'FINISHED'}

class Renderman_OT_removeDisplay(bpy.types.Operator):
    bl_label = "removeDisplay"
    bl_idname = "remdisplay"
    bl_description = "remove Display Driver"
    
    index = bpy.props.IntProperty(min = -1, max=10000, default=-1)

    def invoke(self, context, event):
        scene = context.scene
        active_pass = getactivepass(scene)
        index = self.index
        active_pass.displaydrivers.remove(index)
        return {'FINISHED'}

class Renderman_OT_adddisplayoption(bpy.types.Operator):
    bl_label = "add option"
    bl_description = "add custom display option"
    bl_idname="displayoption.add"
    
    display = bpy.props.StringProperty()
    
    def invoke(self, context, event):
        scene = context.scene
        active_pass = getactivepass(scene)
        display = active_pass.displaydrivers[self.display]
        defcount = 1
        
        def getdefname(name, count):
            countstr = "0"*(2 - len(str(count))) + str(count)
            defaultname = name+countstr
            return defaultname
    
        defname = "Default01"
    
        for item in display.custom_options:
            if item.name == defname:
                defcount +=1
                defname = getdefname("Default", defcount)    
        display.custom_options.add().name = defname
    
        return {'FINISHED'}          
        
class Renderman_OT_removedisplayoption(bpy.types.Operator):
    bl_label = "remove option"
    bl_description = "remove custom display option"
    bl_idname="displayoption.remove"
    
    disp_opt = bpy.props.StringProperty()
    
    def invoke(self, context, event):
        scene = context.scene
        active_pass = getactivepass(scene)
        disp, opt = self.disp_opt.split()
        display = active_pass.displaydrivers[disp]
        display.custom_options.remove(int(opt))
        return {'FINISHED'} 
        
class Renderman_OT_senddisplay(bpy.types.Operator):
    bl_label = "send Display"
    bl_idname = "display.send"
    bl_description = "send display driver to Render Result"
    
    display = bpy.props.StringProperty()
    
    def invoke(self, context, event):
        scene = context.scene
        rmansettings = scene.renderman_settings
        active_pass = getactivepass(scene)

        if active_pass.displaydrivers[self.display].send:
            active_pass.displaydrivers[self.display].send = False
            return {'FINSIHED'}

        for rpass in rmansettings.passes:
            for disp in rpass.displaydrivers:                
                disp.send = False
                    
        active_pass.renderresult = self.display
        active_pass.displaydrivers[self.display].send = True
    
        return {'FINISHED'}            
        
#############################################
#                                           #
#   passes Operator                         #
#                                           #
#############################################

class Renderman_OT_addPassPreset(bpy.types.Operator):
    bl_label = "Add Preset"
    bl_idname = "renderman.addpasspreset"
    bl_description = "add Pass Preset"
    
    def invoke(self, context, event):
        scene = context.scene
        wm = context.window_manager
        wm.invoke_popup(self)
        return {'RUNNING_MODAL'}
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        rmansettings = scene.renderman_settings
        layout.prop(rmansettings, "presetname")
        layout.operator("renderman.writepasspreset")
        

class Renderman_OT_writePassPreset(bpy.types.Operator):
    bl_label = "Write Preset"
    bl_idname = "renderman.writepasspreset"
    bl_description = "write Pass Preset"
    
    def invoke(self, context, event):
        scene = context.scene
        rmansettings = scene.renderman_settings
        active_pass = getactivepass(scene)
        active_engine = scene.renderman_settings.active_engine
        main_preset_path = bpy.utils.preset_paths('renderman')[0]
        sub_preset_path = os.path.join(main_preset_path, active_engine)
        checkForPath(sub_preset_path)
        preset = rmansettings.presetname
        rmansettings.presetname = ""
        
        preset_file = os.path.join(sub_preset_path, preset)+'.pass'
        
        file = open(preset_file, "w")

        e = ' = '
        a_pass = 'bpy.context.scene.renderman_settings.passes["'+active_pass.name+'"].'
        def w(slist): 
            for s in slist:
                val_raw = eval(a_pass+s)
                if type(val_raw) == type(""): val = '"'+val_raw+'"'
                else: val = str(val_raw)
                file.write(s + e + val + '\n')
        
        ## Settings
        # Quality
        file.write('##Quality\n')
        w([ 'pixelsamples_x',
            'pixelsamples_y',
            'pixelfilter.filterlist',
            'pixelfilter.filterheight',
            'pixelfilter.filterwidth',
            'pixelfilter.customfilter'])
        file.write('##\n\n')
        
        # Motion Blur
        file.write('##Motion Blur\n')
        w([ 'motionblur',
            'shutterspeed'])
        file.write('##\n\n')
        
        # Export Objects
        file.write('##Export Objects\n')
        w([ 'exportobjects',
            'objectgroup'])
        file.write('##\n\n')
        
        # Export Lights
        file.write('##Export Lights\n')
        w([ 'exportlights',
            'lightgroup'])
        file.write('##\n\n')
        
        # Animate Pass
        file.write('##Animate Pass\n')
        w(['exportanimation'])
        file.write('##\n\n')
        
        ## Options
        file.write('##Options\n')
        write_grp_preset(active_pass, "opt", file.write)
        file.write('##\n\n')
        
        ## Hider
        hider = active_pass.hider
        if hider in scene.renderman_settings.hider_list:
            file.write('##Hider\n')
            file.write(hider+'\n')
            curr_hider = active_pass.hider_list[hider]
            write_sub_preset(curr_hider, curr_hider.options, file.write)
            file.write('##\n\n')
        
        ## Display Driver
        file.write('##Displays\n')
        for disp in active_pass.displaydrivers:
            file.write('NewDisplay '+disp.name+'\n')
            disppath = 'displaydrivers["'+disp.name+'"].'
            w([ disppath+'name',
                disppath+'displaydriver',
                disppath+'filename_var',
                disppath+'gain',
                disppath+'gamma',
                disppath+'quantize_black',
                disppath+'quantize_white',
                disppath+'quantize_min',
                disppath+'quantize_max',
                disppath+'send'])
            file.write('#Custom Options\n')
            write_sub_preset(disp, disp.custom_options, file.write)
        file.write('##\n\n')
        
        ## Custom Pass Rib Code
        file.write('##Custom Scene RIB Code\n')
        for sc in active_pass.scene_code:
            file.write(sc.name+'\n')
        file.write('##\n\n')
        
        ## Custom World Rib Code
        file.write('##Custom World RIB Code\n')
        for wc in active_pass.world_code:
            file.write(wc.name+'\n')
        file.write('##\n\n')
        
        ## World Attribute Preset World Shading Rate, etc. Settings(overrides for Objects)
        file.write('##Attribute Preset\n')
        write_grp_preset(active_pass, "attr", file.write)
        file.write('##\n\n')
        
        ##World Shaders
        file.write('##World Shaders\n')
        gshad = active_pass.global_shader
        g = 'global_shader.'
        w([ 'imager_shader',
            g+'surface_shader',
            g+'atmosphere_shader'])
        file.write('##\n\n')

        def shader_presets(shader_parameter, shad_path):
            for parm in shader_parameter:
                parm_path = shad_path+'["'+parm.name+'"].'
                w([ parm_path+"textparameter",
                    parm_path+"vector_size",
                    parm_path+"parametertype",
                    parm_path+"float_one[0]",
                    parm_path+"float_two[0]",
                    parm_path+"float_two[1]",
                    parm_path+"float_three[0]",
                    parm_path+"float_three[1]",
                    parm_path+"float_three[2]",
                    parm_path+"int_one[0]",
                    parm_path+"int_two[0]",
                    parm_path+"int_two[1]",
                    parm_path+"int_three[0]",
                    parm_path+"int_three[1]",
                    parm_path+"int_three[2]",
                    parm_path+"texture",
                    parm_path+"colorparameter[0]",
                    parm_path+"colorparameter[1]",
                    parm_path+"colorparameter[2]"])
                file.write('##\n\n')
                        
        ##Imager
        if active_pass.imager_shader != "":
            file.write('##Imager\n')        
            shader_presets(active_pass.imager_shader_parameter, 'imager_shader_parameter')                        

        ##Surface
        if gshad.surface_shader != "":
            file.write('##Surface\n')        
            shader_presets(gshad.surface_shader_parameter, g+'surface_shader_parameter')
            
        ##Atmosphere
        if gshad.atmosphere_shader != "":
            file.write('##Atmosphere\n')        
            shader_presets(gshad.atmosphere_shader_parameter, g+'atmosphere_shader_parameter')
        file.write('##\n\n')                  
        return {'FINISHED'}
        

def invoke_preset(rpass, preset, scene):
    active_engine = scene.renderman_settings.active_engine
    main_preset_path = bpy.utils.preset_paths('renderman')[0]
    sub_preset_path = os.path.join(main_preset_path, active_engine)
    
    preset_file = os.path.join(sub_preset_path, preset)+'.pass'

    pass_path = 'bpy.context.scene.renderman_settings.passes["'+rpass.name+'"].'
    
    try:
        file = open(preset_file, "r")
    except:
        print("file not found")
        return 0

    def eval_preset(ei, plines):
        pi = ei
        while True:
            pi += 1
            pline = plines[pi]
            if pline == '##\n': break
            else:
                prop = pass_path + pline
                exec(prop)

    def eval_sub_preset(ei, plines, type):                
        subs = []
        pi = ei
        while True:
            pi += 1
            line = lines[pi]
            if line == '##\n': break
            else:
                subs.append(line)
        load_grp_preset(subs, rpass, type)                
    
    lines = file.readlines()
    
    for i, line in enumerate(lines):
        if line in ['##Quality\n', 
                    '##Motion Blur\n', 
                    '##Export Objects\n', 
                    '##Export Lights\n', 
                    '##Animate Pass\n',
                    '##World Shaders\n']:
            eval_preset(i, lines)
            checkshaderparameter("worldi", rpass, rpass.imager_shader, rpass.imager_shader_parameter, scene)
            checkshaderparameter("worlds", rpass, rpass.global_shader.surface_shader, rpass.global_shader.surface_shader_parameter, scene)
            checkshaderparameter("worlda", rpass, rpass.global_shader.atmosphere_shader, rpass.global_shader.atmosphere_shader_parameter, scene)
            
        elif line == '##Options\n':
            eval_sub_preset(i, lines, "opt")
        
        elif line == '##Hider\n':
            pi = i
            pi += 1
            hider = lines[pi].replace('\n', '')
            rpass.hider = hider
            while True:
                pi += 1
                hline = lines[pi]
                if hline == '##\n': break
                else:
                    load_sub_preset(rpass.hider_list[hider].options, hline)
            
        elif line == '##Displays\n':
            disp_name = ""
            disp = None
            disp_path = ""
            co = False
            pi = i
            while True:
                pi += 1
                dline = lines[pi]
                if dline == '##\n': break
                else:               
                    if dline.find('NewDisplay') != -1:
                        disp_name = dline.split()[1]
                        if not disp_name in rpass.displaydrivers:
                            rpass.displaydrivers.add().name = disp_name
                        disp = rpass.displaydrivers[disp_name]
                        disp_path = pass_path + 'displaydrivers["'+disp_name+'"].'
                        co = False
                    elif dline == '#Custom Options\n': 
                        co = True
                    elif co:
                        load_sub_preset(disp.custom_options, dline)
                    else:
                        prop = pass_path + dline
                        exec(prop)
                        
        elif line == '##Custom Scene RIB Code\n':
            pi = i
            while True:
                pi += 1
                pline = lines[pi]
                if pline == '##\n': break
                else:
                    if not pline in rpass.scene_code:
                        rpass.scene_code.add().name = pline
                    
        elif line == '##Custom World RIB Code\n':
            pi = i
            while True:
                pi += 1
                pline = lines[pi]
                if pline == '##\n': break
                else:
                    if not pline in rpass.world_code:
                        rpass.world_code.add().name = pline
                    
        elif line in ['##Imager\n', '##Surface\n', '##Atmosphere\n']:
            eval_preset(i, lines)                  
                    


class Renderman_OT_loadPresetPass(bpy.types.Operator):
    bl_label = "Load Pass Preset"
    bl_idname = "renderman.loadpresetpass"
    bl_description = "load Preset Pass"
    
    props = bpy.props
    
    preset = props.StringProperty()
    
    def invoke(self, context, event):
        scene = context.scene
        current_pass = getactivepass(scene)
       
        preset = self.preset
        
        invoke_preset(current_pass, preset, scene)
        return {'FINISHED'}


class Renderman_OT_addPresetPass(bpy.types.Operator):
    bl_label = "Add Pass"
    bl_idname = "renderman.addpresetpass"
    bl_description = "add Preset Pass"
    
    props = bpy.props
    
    preset = props.StringProperty()
    
    def invoke(self, context, event):
        scene = context.scene
        passes = scene.renderman_settings.passes
       
        preset = self.preset
        name = preset
        defcount = 1
        defname = name+"01"
        print(name)
        for item in passes:
            if item.name == defname:
                defcount += 1
                defname = name + "0"*(2 - len(str(defcount))) + str(defcount)
        passes.add().name = defname
        maintain(scene)
        invoke_preset(passes[defname], preset, scene)
        
        return {'FINISHED'}
        
class Renderman_OT_remPass(bpy.types.Operator):
    bl_label = "Remove Pass"
    bl_idname = "renderman.rempass"
    bl_description = "Remove Renderman Pass"
    
    path = bpy.props.StringProperty()
    
    def invoke(self, context, event):
        path = eval(self.path)
        index = eval(self.path+'_index')
        path.remove(index)
        
        return {'FINISHED'}
          

class Renderman_OT_addPass(bpy.types.Operator):
    bl_label = "addPass"
    bl_idname = "addpass"
    bl_description = "add render Pass"
    
    path = bpy.props.StringProperty()
    
    def invoke(self, context, event):
        scene = context.scene
        passes = eval(self.path)
        name = "Default"
        defcount = 1
        defname = "Default01"
        for item in passes:
            if item.name == defname:
                defcount += 1
                defname = name + "0"*(2 - len(str(defcount))) + str(defcount)
        passes.add().name = defname
        return{'FINISHED'}

class Renderman_OT_removePass(bpy.types.Operator):
    bl_label = "removePass"
    bl_idname = "rempass"
    bl_description = "remove render pass"

    def invoke(self, context, event):
        scene = context.scene
        index = scene.renderman_settings.passes_index
        if len(scene.renderman_settings.passes) > 1:
            scene.renderman_settings.passes.remove(index)
        return{'FINISHED'}

class Renderman_OT_movepass(bpy.types.Operator):
    bl_label = "movepass"
    bl_idname = "movepass"
    bl_description = "move Pass"

    direction = bpy.props.EnumProperty(items = (
                                                    ("up", "up", "up"),
                                                    ("down", "down", "down")
                                                ),
                                        default = "up",
                                        name = "Direction",
                                        description = "Direction to move Pass")

    def invoke(self, context, event):
        renderman_settings = context.scene.renderman_settings
        index = renderman_settings.passes_index
        if self.direction == "up":
            renderman_settings.passes.move(index, index-1)
        elif self.direction == "down":
            renderman_settings.passes.move(index, index+1)
        return{'FINISHED'}


#############################################
#                                           #
#   Render Operator                         #
#                                           #
#############################################


class Renderman_OT_addOptionGroup(bpy.types.Operator):
    bl_label = "addOptionGroup"
    bl_idname = "addoptiongroup"
    bl_description = "add Renderman Option Group"
    
    def invoke(self, context, event):
        rmansettings = context.scene.renderman_settings
        master_option_groups = rmansettings.option_groups
        master_option_groups.add()
        return {'FINISHED'}
    
class Renderman_OT_removeOptionGroup(bpy.types.Operator):
    bl_label = "removeOptionGroup"
    bl_idname = "removeoptiongroup"
    bl_description = "remove Renderman Option Group"
    
    def invoke(self, context, event):
        rmansettings = context.scene.renderman_settings
        index = rmansettings.option_groups_index
        master_option_groups = rmansettings.option_groups
        master_option_groups.remove(index)
    
        return {'FINISHED'}              

class Renderman_OT_addOption(bpy.types.Operator):
    bl_label = "addOption"
    bl_idname = "addoption"
    bl_description = "add Renderman Option"

    def invoke(self, context, event):
        rmansettings = context.scene.renderman_settings
        group_index = rmansettings.option_groups_index
        master_options = rmansettings.option_groups[group_index].options
        master_options.add()
        return {'FINISHED'}

class Renderman_OT_removeOption(bpy.types.Operator):
    bl_label = "removeOption"
    bl_idname = "remoption"
    bl_description = "remove Option"

    index = bpy.props.IntProperty(min = -1, max = 10000, default = -1)

    def invoke(self, context, event):
        rmansettings = context.scene.renderman_settings
        group_index = rmansettings.option_groups_index
        master_options = rmansettings.option_groups[group_index].options
        index = self.index
        master_options.remove(index)
        return {'FINISHED'} 
 

class Renderman_OT_set_all_as_default(bpy.types.Operator):
    bl_label = "set_as_default"
    bl_idname = "options.set_as_default"
    bl_description = "set values of all options as default for new passes"

    def invoke(self, context, event):
        rmansettings = context.scene.renderman_settings
        copy_parameters(rmansettings.option_groups, getactivepass(context.scene).option_groups)  
        return {'FINISHED'}  
    
class Renderman_OT_get_all_defaults(bpy.types.Operator):
    bl_label = "get_default"
    bl_idname = "options.get_default"
    bl_description = "get the default values for options in active pass"

    def invoke(self, context, event):
        rmansettings = context.scene.renderman_settings
        copy_parameters(getactivepass(context.scene).option_groups, rmansettings.option_groups)
        return {'FINISHED'}   


class Renderman_OT_set_current_default(bpy.types.Operator):
    bl_label = "set current option defaults"
    bl_idname = "option.set_current_default"
    bl_description = "set current value as default"
   
    
    grp_opt = bpy.props.StringProperty(default = "", name="", subtype='NONE')
    
    def invoke(self, context, event):
        rmansettings = context.scene.renderman_settings
        grp_opt = self.grp_opt
        grp = grp_opt.split()[0]
        opt = grp_opt.split()[1]
        
        master_option = rmansettings.option_groups[grp].options[opt]
        slave_option = getactivepass(context.scene).option_groups[grp].options[opt]
    
        copy_parameter(master_option, slave_option)
    
        return {'FINISHED'}          
    
class Renderman_OT_get_current_default(bpy.types.Operator):
    bl_label = "get current option defaults"
    bl_idname = "option.get_current_default"
    bl_description = "get default value"
    
    grp_opt = bpy.props.StringProperty(default = "")
    
    def invoke(self, context, event):
        rmansettings = context.scene.renderman_settings
        grp_opt = self.grp_opt
        grp = grp_opt.split()[0]
        opt = grp_opt.split()[1]
        
        master_option = rmansettings.option_groups[grp].options[opt]
        slave_option = getactivepass(context.scene).option_groups[grp].options[opt]
    
        copy_parameter(slave_option, master_option) 
    
        return {'FINISHED'}          
        
class Renderman_OT_get_group_default(bpy.types.Operator):
    bl_label = "get group defaults"
    bl_idname = "option_group.get_default"
    bl_description = "get defaults for current group"
    
    grp = bpy.props.StringProperty()
    
    def invoke(self, context, event):
        rmansettings = context.scene.renderman_settings
        grp = self.grp
        master_group = rmansettings.option_groups[grp]
        slave_group = getactivepass(context.scene).option_groups[grp]
    
        for master_option in master_group.options:
            slave_option = slave_group.options[master_option.name]
            copy_parameter(slave_option, master_option)  
    
        return {'FINISHED'}              
            
class Renderman_OT_set_group_default(bpy.types.Operator):
    bl_label = "set group defaults"
    bl_idname = "option_group.set_default"
    bl_description = "set defaults for current group"
    
    grp = bpy.props.StringProperty()
    
    def invoke(self, context, event):
        rmansettings = context.scene.renderman_settings
        grp = self.grp
        master_group = rmansettings.option_groups[grp]
        slave_group = getactivepass(context.scene).option_groups[grp]
    
        for master_option in master_group.options:
            slave_option = slave_group.options[master_option.name]
            copy_parameter(master_option, slave_option)                                                                                                                
    
        return {'FINISHED'}  
    
#############################################
#                                           #
#  World Operator                           #
#                                           #
#############################################  
class Renderman_OT_addnew_Attribute(bpy.types.Operator):
    bl_label = ""
    bl_idname = "attributes.add_new"
    bl_description = "add new attribute"
    
    grp = String()
    attr = String()
    path = String()
    
    def execute(self, context):
        path = eval(self.path)
        try:
            grps = path.attribute_groups
        except:
            print(self.path)
            raise
        if not self.grp in grps: grps.add().name = self.grp
        grp = grps[self.grp]
        if not self.attr in grp.attributes: grp.attributes.add().name = self.attr
        print(self.attr)
        return {'FINISHED'}
    

class Renderman_OT_remove_Attribute(bpy.types.Operator):
    bl_label = ""
    bl_idname = "attributes.remove"
    bl_description = "remove attribute"
    
    type = bpy.props.EnumProperty(default = "all", items = (("all", "All", ""),
                                                            ("grp", "Group", ""),
                                                            ("attr", "Attribute", "")))
    grp = String()
    attr = String()
    path = String()
    
    def invoke(self, context, event):
        try:
            path = eval(self.path)
        except:
            print(self.path)
            raise
        grps = path.attribute_groups
        if self.grp != "":
            grp = grps[self.grp]
        
        type = self.type
        if type == "all":
            for g in grps:
                grps.remove(0)
                
        elif type == "attr":
            for i, a in enumerate(grp.attributes):
                if a.name == self.attr:
                    grp.attributes.remove(i)
        else:
            for i, g in enumerate(grps):
                if g.name == self.grp:
                    grps.remove(i)
        return {'FINISHED'}
            

class Renderman_OT_addAttributeGroup(bpy.types.Operator):
    bl_label = "addAttributeGroup"
    bl_idname = "addattributegroup"
    bl_description = "add Renderman Attribute Group"
    
    def invoke(self, context, event):
        rmansettings = context.scene.renderman_settings
        master_attribute_groups = rmansettings.attribute_groups
        master_attribute_groups.add()
        return {'FINISHED'}
    
class Renderman_OT_removeAttributeGroup(bpy.types.Operator):
    bl_label = "removeAttributeGroup"
    bl_idname = "removeattributegroup"
    bl_description = "remove Renderman Attribute Group"
    
    def invoke(self, context, event):
        rmansettings = context.scene.renderman_settings
        index = rmansettings.attribute_groups_index
        master_attribute_groups = rmansettings.attribute_groups
        master_attribute_groups.remove(index)
    
        return {'FINISHED'}          

class Renderman_OT_addAttribute(bpy.types.Operator):
    bl_label = "addAttribute"
    bl_idname = "addattribute"
    bl_description = "add Attribute"

    def invoke(self, context, event):
        renderman_settings = context.scene.renderman_settings 
        group_index = renderman_settings.attribute_groups_index
        attributes = renderman_settings.attribute_groups[group_index].attributes
        attributes.add()
        return {'FINISHED'}

class Renderman_OT_removeAttribute(bpy.types.Operator):
    bl_label = "removeAttribute"
    bl_idname = "remattribute"
    bl_description = "remove Attribute"

    index = bpy.props.IntProperty(min=-1, max=10000, default=-1)

    def invoke(self, context, event):
        renderman_settings = context.scene.renderman_settings
        group_index = renderman_settings.attribute_groups_index
        attributes = renderman_settings.attribute_groups[group_index].attributes    
        index = self.index
        attributes.remove(index)
        return {'FINISHED'}


class Renderman_OT_attributes_set_as_default(bpy.types.Operator):
    bl_label = "attributes_set_as_default"
    bl_idname = "attributes.set_as_default"
    bl_description = "set values of all attributes as default for new passes"

    path = String()

    def invoke(self, context, event):
        rmansettings = context.scene.renderman_settings
        path = eval(self.path)
        copy_parameters(rmansettings.attribute_groups, path.attribute_groups, False)
        return {'FINISHED'}  
    
class Renderman_OT_attributes_get_default(bpy.types.Operator):
    bl_label = "get_default_attributes"
    bl_idname = "attributes.get_default"
    bl_description = "get the default values for attributes in active pass"

    path = String()

    def invoke(self, context, event):
        rmansettings = context.scene.renderman_settings
        path = eval(self.path)
        copy_parameters(path.attribute_groups, rmansettings.attribute_groups, False)
        return {'FINISHED'}  
    
    
class Renderman_OT_get_current_attribute_default(bpy.types.Operator):
    bl_label = "get current attribute defaults"
    bl_idname = "attribute.get_default"
    bl_description = "get default value"
    
    grp = String()
    attr = String()
    path = String()
    
    def invoke(self, context, event):
        rmansettings = context.scene.renderman_settings
        grp = self.grp
        attr = self.attr
        path = eval(self.path)
        
        master_attribute = rmansettings.attribute_groups[grp].attributes[attr]
        slave_attribute = path.attribute_groups[grp].attributes[attr]
    
        copy_parameter(slave_attribute, master_attribute)
    
        return {'FINISHED'}          
        
class Renderman_OT_set_current_attribute_default(bpy.types.Operator):
    bl_label = "set current attribute defaults"
    bl_idname = "attribute.set_default"
    bl_description = "set current value as default"
   
    
    grp = String()
    attr = String()
    path = String()
    
    def invoke(self, context, event):
        rmansettings = context.scene.renderman_settings
        grp = self.grp
        attr = self.attr
        path = eval(self.path)
        
        master_attribute = rmansettings.attribute_groups[grp].attributes[attr]
        slave_attribute = path.attribute_groups[grp].attributes[attr]
    
        copy_parameter(master_attribute, slave_attribute)    
    
        return {'FINISHED'}          
        
class Renderman_OT_get_attr_group_default(bpy.types.Operator):
    bl_label = "get group defaults"
    bl_idname = "attribute_group.get_default"
    bl_description = "get defaults for current group"
    
    grp = String()
    path = String()
    
    def invoke(self, context, event):
        rmansettings = context.scene.renderman_settings
        grp = self.grp
        path = eval(self.path)
        master_group = rmansettings.attribute_groups[grp]
        slave_group = path.attribute_groups[grp]
        
        slave_group.export = master_group.export
        for master_attribute in master_group.attributes:
            if master_attribute.name in slave_group.attributes:
                slave_attribute = slave_group.attributes[master_attribute.name]
                copy_parameter(slave_attribute, master_attribute)
    
        return {'FINISHED'}              
            
class Renderman_OT_set_attr_group_default(bpy.types.Operator):
    bl_label = "set group defaults"
    bl_idname = "attribute_group.set_default"
    bl_description = "set defaults for current group"
    
    grp = String()
    path = String()
    
    def invoke(self, context, event):
        rmansettings = context.scene.renderman_settings
        grp = self.grp
        path = eval(self.path)
        master_group = rmansettings.attribute_groups[grp]
        slave_group = path.attribute_groups[grp]
    
        master_group.export = slave_group.export
        for master_attribute in master_group.attributes:
            if master_attribute.name in slave_group.attributes:
                slave_attribute = slave_group.attributes[master_attribute.name]
                copy_parameter(master_attribute, slave_attribute)                   
    
        return {'FINISHED'}  
    
#############################################
#                                           #
#   Object Operators                        #
#                                           #
#############################################

class Renderman_OT_LightLinking_selected(bpy.types.Operator):
    bl_label = "Link Lights"
    bl_idname = "renderman.light_linking"
    bl_description = "Link Lights to Objects"
    
    type = Enum(items = (   ("add", "add Lights", "add selected lights"),
                            ("remove", "remove Lights", "remove selected lights"),
                            ("exclusive", "only selected", "exlusively use selected lights")),
                default = "add")
    
    def invoke(self, context, event):
        t = self.type
        lights = []
        for l in context.scene.objects:
            al = False
            if l.active_material:
                for rm in l.active_material.renderman:
                    if rm.arealight_shader != '':
                        al = True
            if (l.type == 'LAMP' or al) and l.select:
                lights.append(l.name)
                
        for obj in context.scene.objects:
            if obj.type in ["MESH"] and obj.select:
                for l in obj.renderman[obj.renderman_index].light_list:
                    if l.name in lights:
                        if t in ["add", "exclusive"]:
                            l.illuminate = True
                        elif t == "remove":
                            l.illuminate = False
                    else:
                        if t == "exclusive":
                            l.illuminate = False
        return {'FINISHED'}
        
class Renderman_OT_addAttributeSelected(bpy.types.Operator):
    bl_label = "add Attribute"
    bl_idname = "attributes.add_new_selected"
    bl_description = "add Attribute to selected"
    
    grp = String()
    attr = String()
    
    def execute(self, context):
        grp = self.grp
        attr = self.attr
        for obj in context.scene.objects:
            path = 'bpy.context.scene.objects["'+obj.name+'"].renderman'
            path += '['+path+'_index]'
            if obj.select:
                bpy.ops.attributes.add_new(grp = grp, attr = attr, path=path )
                
        return {'FINISHED'}
    

class Renderman_OT_changeLinking(bpy.types.Operator):
    bl_label = ""
    bl_idname = "renderman.change_pass_linking"
    bl_description = "change Pass linking"
    
    path = String()
    type = Enum(items = (   ("all", "All", "all"),
                            ("none", "None", "none"),
                            ("active", "Active", "active"),
                            ("invert", "Invert", "invertcd my")),
                default = "all")
                
    def  invoke(self, context, event):
        path = eval(self.path)
        type = self.type
        curr_pass = path[eval(self.path+'_index')]
        rm = context.scene.renderman_settings
    
        if type == "all":
            for l in curr_pass.links:
                curr_pass.links.remove(0)
            for global_pass in rm.passes:
                bpy.ops.renderman.link_pass(path = self.path, rpass = global_pass.name)
            
        elif type == "none":
            for l in curr_pass.links:
                curr_pass.links.remove(0)
            
        elif type == "active":
            bpy.ops.renderman.link_pass(path = self.path, rpass = rm.passes[rm.passes_index].name)
        
        elif type == "invert":
            for global_pass in rm.passes:
                bpy.ops.renderman.link_pass(path = self.path, rpass = global_pass.name)
        return {'FINISHED'}
            
        
class Renderman_OT_link_pass(bpy.types.Operator):
    bl_label = ""
    bl_idname = "renderman.link_pass"
    bl_description = "Link/Unlink Object Pass to this Render Pass"
    
    rpass = String()
    path = String()
    
    def execute(self, context):
        rm = context.scene.renderman_settings
        path = eval(self.path)
        rpass = self.rpass
        curr_pass = path[eval(self.path+'_index')]
        for opass in path:
            links = opass.links
            if rpass in links:
                for i, p in enumerate(links):
                    if p.name == rpass: links.remove(i)
            elif opass == curr_pass:
                links.add().name = rpass
        return{'FINISHED'} 
    
#############################################
#                                           #
#   Shader Paths Operator                   #
#                                           #
#############################################


class Renderman_OT_RefreshShaderList(bpy.types.Operator):
    bl_label = "Refresh Shader List"
    bl_idname = "refreshshaderlist"
    bl_description = "Refresh Shader List"

    def invoke(self, context, event):
        checkshadercollection(context.scene)
        return {'FINISHED'}


class Renderman_OT_Shaderpaths(bpy.types.Operator):
    bl_label = "Shader Paths"
    bl_idname = "pathaddrem"
    bl_description = "adds or removes Shader Path"

    add = bpy.props.BoolProperty(default = True)

    def invoke(self, context, event):
        scene = context.scene
        shaders = context.scene.renderman_settings.shaders
        if self.add:
            shaders.shaderpaths.add().name = context.scene.renderman_settings.shaderpath
            checkshadercollection(context.scene)

        elif not self.add:
            index = shaders.shaderpathsindex
            shaders.shaderpaths.remove(index)

        return {'FINISHED'}


class Renderman_OT_CompileShader(bpy.types.Operator):
    bl_label = "Compile Shader"
    bl_idname = "text.compileshader"
    bl_description = "Compile Renderman Shader"
    COMPAT_ENGINES = {'RENDERMAN'}

    @classmethod
    def poll(cls, context):
        text = context.space_data.text
        return text

    def invoke(self, context, event):
        scene = context.scene
        text = context.space_data.text
        scpath = context.scene.renderman_settings.shaderexec
        if not text.filepath:
            bpy.ops.text.save_as()

        shader = os.path.split(text.filepath)
        os.chdir(shader[0])
        os.system('"'+scpath+'" "'+shader[1]+'"')

        return {'FINISHED'}
        
#############################################
#                                           #
#   Hider List Operator                     #
#                                           #
#############################################

class Renderman_OT_addremhider(bpy.types.Operator):
    bl_label="add or remove hider"
    bl_idname="addremhider"
    bl_description = "add or remove Hider"
    
    add = bpy.props.BoolProperty(default = True)
    
    def invoke(self, context, event):
        scene = context.scene
        rmansettings = context.scene.renderman_settings
        add = self.add
        if add:
            rmansettings.hider_list.add()
        else:
            index = rmansettings.hider_list_index
            rmansettings.hider_list.remove(index)
            
        return {'FINISHED'}  
    
class Renderman_OT_addhideroption(bpy.types.Operator):
    bl_label = "add hider option"
    bl_idname="addhideroption"
    bl_description = "add hider specific option"
    
    def invoke(self, context, event):
        scene = context.scene
        rmansettings = context.scene.renderman_settings
        hider = rmansettings.hider_list[rmansettings.hider_list_index]
        hider.options.add()
        
        return {'FINISHED'}
    
class Renderman_OT_remhideroption(bpy.types.Operator):
    bl_label = "remove hider option"
    bl_idname = "remhideroption"
    bl_description = "remove hider specific option"
    
    index = bpy.props.IntProperty(min = 0, max=10000, default=0)
    
    def invoke(self, context, event):
        scene = context.scene
        rmansettings = context.scene.renderman_settings
        index = self.index
        hider = rmansettings.hider_list[rmansettings.hider_list_index]
        hider.options.remove(index)
        
        return {'FINISHED'}                           


class Renderman_OT_hider_set_default_values(bpy.types.Operator):
    bl_label = "set default"
    bl_idname = "hider.set_default_values"
    bl_description = "set current values as default for current hider"
    
    hider = bpy.props.StringProperty()
    
    def invoke(self, context, event):
        scene = context.scene
        rmansettings = context.scene.renderman_settings
        hider = self.hider        
        master_hider = rmansettings.hider_list[hider]
        slave_hider = getactivepass(context.scene).hider_list[hider]
    
        for master_option in master_hider.options:
            slave_option = slave_hider.options[master_option.name]
            copy_parameter(master_option, slave_option)
            
        return {'FINISHED'}
    
    
class Renderman_OT_hider_get_default_values(bpy.types.Operator):
    bl_label = "get default"
    bl_idname = "hider.get_default_values"
    bl_description = "get default values for current hider"
    
    hider = bpy.props.StringProperty()
    
    def invoke(self, context, event):
        scene = context.scene
        rmansettings = context.scene.renderman_settings
        hider = self.hider        
        master_hider = rmansettings.hider_list[hider]
        slave_hider = getactivepass(context.scene).hider_list[hider]
    
        for master_option in master_hider.options:
            slave_option = slave_hider.options[master_option.name]
            copy_parameter(slave_option, master_option)
            
        return {'FINISHED'}    
    
    
class Renderman_OT_hider_option_set_default(bpy.types.Operator):
    bl_label = "set default"
    bl_idname = "hider_option.set_default"
    bl_description = "set current value as default"
    
    hider_option = bpy.props.StringProperty()
    
    def invoke(self, context, event):
        scene = context.scene
        rmansettings = context.scene.renderman_settings
        hider = self.hider_option.split()[0]
        option = self.hider_option.split()[1]        
        master_option = rmansettings.hider_list[hider].options[option]
        slave_option = getactivepass(context.scene).hider_list[hider].options[option]
    
        copy_parameter(master_option, slave_option)
            
        return {'FINISHED'} 
    
    
class Renderman_OT_hider_option_get_default(bpy.types.Operator):
    bl_label = "get default"
    bl_idname = "hider_option.get_default"
    bl_description = "get default value"
    
    hider_option = bpy.props.StringProperty()
    
    def invoke(self, context, event):
        scene = context.scene
        rmansettings = context.scene.renderman_settings
        hider = self.hider_option.split()[0]
        option = self.hider_option.split()[1]        
        master_option = rmansettings.hider_list[hider].options[option]
        slave_option = getactivepass(context.scene).hider_list[hider].options[option]
    
        copy_parameter(slave_option, master_option)
            
        return {'FINISHED'}   
    
    
class Renderman_OT_hider_set_default(bpy.types.Operator):
    bl_label="set default"
    bl_idname="hider.set_default"    
    bl_description="set this hider as default for new passes"

    hider = bpy.props.StringProperty()
    
    def invoke(self, context, event):
        scene = context.scene
        rmansettings = context.scene.renderman_settings
        hider = self.hider
        rmansettings.default_hider = hider
        return {'FINISHED'}     


#############################################
#                                           #
#   Custom RIB Code Operators               #
#                                           #
#############################################

class Renderman_OT_addCustomSceneRIBCode(bpy.types.Operator):
    bl_label = "Scene RIB Code"
    bl_idname = "scene.ribcode"
    bl_description = "add or remove custom rib code"
    
    add = bpy.props.BoolProperty(default = True)
    
    def invoke(self, context, event):
        scene = context.scene
        active_pass = getactivepass(scene)
        add = self.add
        if add:
            active_pass.scene_code.add()
        else:
            active_pass.scene_code.remove(active_pass.scene_code_index)
        return {'FINISHED'}        
        
class Renderman_OT_addCustomWorldRIBCode(bpy.types.Operator):
    bl_label = "World RIB Code"
    bl_idname = "world.ribcode"
    bl_description = "add or remove custom rib code"
    
    add = bpy.props.BoolProperty(default = True)
    
    def invoke(self, context, event):
        scene = context.scene
        active_pass = getactivepass(scene)
        add = self.add
        if add:
            active_pass.world_code.add()
        else:
            active_pass.world_code.remove(active_pass.world_code_index)        
        return {'FINISHED'}  
