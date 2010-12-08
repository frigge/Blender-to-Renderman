
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

String = bpy.props.StringProperty
Bool = bpy.props.BoolProperty
Enum = bpy.props.EnumProperty
CollectionProp = bpy.props.CollectionProperty
Pointer = bpy.props.PointerProperty
FloatVector = bpy.props.FloatVectorProperty
IntVector = bpy.props.IntVectorProperty
Int = bpy.props.IntProperty
Float = bpy.props.FloatProperty

##################################################################################################################################
##################################################################################################################################


assigned_shaders = {}
objects_size = -1
light_list = []
light_list_size = -1
obj_passes = {}
pass_disp_len = {}

                
##################################################################################################################################
#   the fun par begins here:                                                                                                     #
##################################################################################################################################

class Renderman_OT_modal(bpy.types.Operator):
    bl_idname = 'renderman.maintain'
    bl_label ="maintain renderman"
    
    def modal(self, context, event):
        scene = context.scene
        #print("Blender to Renderman Addon Loaded")
        if scene.render.engine == 'RENDERMAN':
            maintain(scene)
        return {'PASS_THROUGH'}
                
    def execute(self, context):
        print("started maintain operator")
        context.window_manager.add_modal_handler(self)
        return {'RUNNING_MODAL'}

#########################################################################################################
#                                                                                                       #
#       functions for keeping things up-to-date                                                         #
#                                                                                                       #
#########################################################################################################
def getactivepass(scene):
    rm = scene.renderman_settings
    passes = rm.passes
    active_pass = None
    if rm.passes_index >= len(rm.passes) or rm.passes_index < len(rm.passes):
        bpy.ops.renderman.set_pass_index()
    try:
        active_pass = passes[rm.passes_index]
    except IndexError:
        pass
    return active_pass
    
    
def getname(raw, name = "", pass_name = "", var = "", driver = "", dir = "", sce = None):
    if sce == None:
        global scene
        sce = scene
    else:
        scene = sce
    n = raw.replace('[scene]', scene.name)
    n = n.replace('[frame]', framepadding(scene))
    if name != "":
        n = n.replace('[name]', name)
    if pass_name != "":
        n = n.replace('[pass]', pass_name)
    if var != "":
        n = n.replace('[var]', var)
    if driver != "":
        n = n.replace('[driver]', driver)
    if dir != "":
        n = n.replace('[dir]', dir)
    return n

def framepadding(scene):
    currentframe = scene.frame_current
    framestr = str(currentframe)
    length = len(framestr)
    padding = scene.renderman_settings.framepadding - length
    frame = padding*"0" + str(currentframe)
    return frame

def shader_info(shader, collection, scene):
    pathcollection = scene.renderman_settings.pathcollection
    shadercollection = pathcollection.shadercollection
    shaderpaths = pathcollection.shaderpaths
    if len(shaderpaths) >= 1:
        if len(shadercollection) >= 1:
            if shader:
                info = pathcollection.shadercollection[shader].fullpath
            else:
                info="No shader selected"
        else:
            info = "No shader(s) found"
    else:
        info = "No shader path(s) selected" 
        
    return info                                      

def active_layers(data, scene):
    active_layers = []
    for i in range(len(scene.layers)):
        if data.layers[i]:
            active_layers.append(i)
    return active_layers  

def check_visible(obj, scene):
    active_scene_layers = active_layers(scene, scene)
    active_obj_layers = active_layers(obj, scene)
    is_visible = False
    for active_layer in active_obj_layers:
        if active_layer in active_scene_layers:
            is_visible = True
            
    return is_visible                                  

def check_env(path):
    if path.find("$") != -1:
        path_splitters = ["/", "\\"]
        for path_splitter in path_splitters:
            if path.find(path_splitter) != -1:
                splitted_path = path.split(path_splitter)
        env_var_raw = splitted_path.pop(0)
        env_var = env_var_raw.replace("$", "")
        final_path = os.environ[env_var]
        for dir in splitted_path:
            final_path = os.path.join(final_path, dir)
        return final_path
    else:
        return path 

def getdefaultribpath(scene):
    if not bpy.data.is_dirty:
        filename = bpy.data.filepath
        defpathmain = os.path.split(filename)[0]
    else:
        defpathmain = tempfile.gettempdir()
    defaultpath = os.path.join(defpathmain, scene.name)
    if not os.path.exists(defaultpath): os.mkdir(defaultpath)
    return defaultpath

def getrendererdir(scene):
    if scene.renderman_settings.use_env_var and not scene.renderman_settings.renderenvvar == "":
        renderdir = os.environ[scene.renderman_settings.renderenvvar]
    else:
        renderdir = scene.renderman_settings.renderpath
    renderdir += "/bin/"
    return renderdir

def addenvironmentmappass(object, texture, scene):
    passes = scene.renderman_settings.passes
    envmap = object.name + "_environment"
#    envmap = [  envmap_base + "_px", envmap_base + "_nx", 
#                envmap_base + "_py", envmap_base + "_ny", 
#                envmap_base + "_pz", envmap_base + "_nz"]
#    for env in envmap:
    if envmap not in passes:
        global assigned_shaders
        assigned_shaders = {}
        passes.add().name = envmap
        envpass = passes[envmap]
        adddisp(envpass, name=envmap, display="file")
        shadowindex = -1
        for index, item in enumerate(passes):
            if item.shadow:
                shadowindex = index
            elif item.name == envmap and not passes[index-1] == passes[shadowindex]:
                passes.move(index, shadowindex+1)
    
    envpass = passes[envmap]        
    envpass.environment = True
    envpass.envname = texture.name
    texture.renderman.envpass = envpass.name
    envpass.imagedir = scene.renderman_settings.envdir
    envpass.camera_object = object.name
    envdisp = envpass.displaydrivers[envmap+'01']
    envdisp.displaydriver = "file"
    if texture.environment_map.source == "STATIC":
        envpass.exportanimation = False
    else:
        envpass.exportanimation = True

def addpass(name, scene):
    rmansettings = scene.renderman_settings
    scene_passes = rmansettings.passes
        
    if not name in scene_passes: scene_passes.add().name = name

def addshadowmappass(shadowname, name, scene):
    light = scene.objects[name]
    lightsettings = light.data.lightsettings
    rmansettings = scene.renderman_settings
    maptype = {"classic" : rmansettings.defaultshadow, "deep" : rmansettings.deepdisplay}        
    passes = rmansettings.passes
    exist = False
    if not shadowname in passes:
        global assigned_shaders
        assigned_shaders = {}
        addpass(shadowname, scene)
        shadowpass = passes[shadowname]
        adddisp(shadowpass, name="shadowmap", display=maptype[lightsettings.shadowmaptype], var="z")
        
        for passindex, item in enumerate(passes):
            if item.name == shadowname and not passes[passindex-1].shadow:
                passes.move(passindex, 0)

    shadowpass = passes[shadowname]
    shadowpass.shadow = True
    shadowpass.imagedir = rmansettings.shadowdir    
    shadowpass.camera_object = name
    shadowpass.exportlights = False
    shadowpass.lightgroup = ""
    shadowdisplay = shadowpass.displaydrivers['shadowmap01']
    shadowdisplay.displaydriver = maptype[lightsettings.shadowmaptype]
                                          
            
def maintain_display_drivers(current_pass, scene):
    path = getdefaultribpath(scene)
    rmansettings = scene.renderman_settings
    shad = rmansettings.defaultshadow
    deep = rmansettings.deepdisplay
    
    oilist = rmansettings.output_images
    
    quant_presets = {   "8bit" : [0, 255, 0, 255],
                        "16bit" : [0, 65535, 0, 65535],
                        "32bit" : [0, 0, 0, 0]
                    }
                                        
    for display in current_pass.displaydrivers:
        disp_drv = display.displaydriver      
        imagepath = os.path.join(path, current_pass.imagedir)

        if display.default_name:
            display.raw_name = '[name]_[pass]_[var][frame].[driver]'
                   
        display.file = os.path.join(imagepath, display.filename).replace('\\', '\\\\')
        
        if display.quantize_presets != "other":
            quant = quant_presets[display.quantize_presets]
            
            display.quantize_min = quant[0]
            display.quantize_max = quant[1]
            display.quantize_black = quant[2]
            display.quantize_white = quant[3]
            
        n = getname(display.raw_name,
                    name = display.name,
                    pass_name = current_pass.name,
                    var = display.var,
                    driver = disp_drv,
                    sce = scene)
                    
        display.filename = n
        
        if not n in oilist:
            oilist.add().name = n 

        global pass_disp_len
        passes_len = len(scene.renderman_settings.passes)
        if passes_len != len(pass_disp_len) or not current_pass.name in pass_disp_len or pass_disp_len[current_pass.name] != len(current_pass.displaydrivers):
            for i, o in enumerate(oilist):
                e = False
                for p in scene.renderman_settings.passes:
                    pass_disp_len[p.name] = len(p.displaydrivers)
                    for d in p.displaydrivers:
                        if o == d.filename: e = True
                if not e: oilist.remove(i)

def update_illuminate_list(obj, scene):
    global light_list
    for objpass in obj.renderman:
        for l in light_list:
            if not l in objpass.light_list:
               objpass.light_list.add().name = l
    
        for killer, light in enumerate(objpass.light_list):
    
            if not light.name in light_list:
                objpass.light_list.remove(killer)
    
        if objpass.lightgroup:
            for item in objpass.light_list:
                if item.name in bpy.data.groups[objpass.lightgroup].objects:
                    item.illuminate = True
                else:
                    item.illuminate = False
            objpass.lightgroup = ""

def check_displaydrivers(scene):
    rmansettings = scene.renderman_settings
    drv_path_raw = rmansettings.displaydrvpath
    if rmansettings.disp_ext_os_default:
        if os.sys.platform == "Windows":
            drv_ext = "dll"
        else:
            drv_ext = "so"
    else:
        drv_ext = rmansettings.disp_ext
    if drv_path_raw:
        display_drivers = []
        drv_path = check_env(drv_path_raw)
        drv_dir = os.listdir(drv_path)
        for drv in drv_dir:
            if checkextension(drv) == drv_ext:                             
                if rmansettings.drv_identifier:
                    if drv.find(rmansettings.drv_identifier) != -1:
                        driver = drv.replace(rmansettings.drv_identifier, "")
                        driver = driver.replace('.'+drv_ext, "")
                else:
                    driver = drv.replace('.'+drv_ext, "")
                    
                display_drivers.append(driver)
                
        if rmansettings.defaultshadow not in display_drivers:
            display_drivers.append(rmansettings.defaultshadow)
        if rmansettings.deepdisplay not in display_drivers:
            display_drivers.append(rmansettings.deepdisplay)               
        
        for drv in display_drivers:
            if drv not in rmansettings.displays:
                rmansettings.displays.add().name = drv
                                                                    
        for index, drv in enumerate(rmansettings.displays):
            if drv.name not in display_drivers:
                rmansettings.displays.remove(index)
        

def check_display_variables(scene):
    rmansettings = scene.renderman_settings
    var_collection = rmansettings.var_collection
    
    default_vars = ["rgb", "rgba", "a", "z", "N", 
                    "P", "Ci", "Cs", "Oi", "Os", 
                    "s", "t", "u", "v", "Ng", 
                    "E", "du", "dv", "dPtime", "dPdu", 
                    "dPdv"]
                    
    for var in default_vars:
        if not var in var_collection:
            var_collection.add().name = var
            
            
def maintain_searchpaths(current_pass, scene):
    rmansettings = scene.renderman_settings

    if not "searchpath" in rmansettings.option_groups:
        rmansettings.option_groups.add().name = "searchpath"
    rmansettings.option_groups['searchpath'].export = True
          
    master_searchpath = rmansettings.option_groups["searchpath"].options      

    def maintain_searchpath(name, value):
        if not name in master_searchpath:
            master_searchpath.add().name = name     
        searchpath_option = master_searchpath[name]
        searchpath_option.export = True
        searchpath_option.parametertype = "string"
        searchpath_option.textparameter = value.replace('\\', '\\\\')
    
        try:
            slave_searchpath = current_pass.option_groups["searchpath"]
        except KeyError:
            return 0
        
        slave = current_pass.option_groups["searchpath"].options[name]
        copy_parameter(slave, searchpath_option)
    
    texpath = os.path.join(getdefaultribpath(scene), rmansettings.texdir)        ##texture searchpath
    shadowpath = os.path.join(getdefaultribpath(scene), rmansettings.shadowdir)
    envpath = os.path.join(getdefaultribpath(scene), rmansettings.envdir)
    maintain_searchpath('texture', texpath+':'+shadowpath+':'+envpath)                    

    if rmansettings.pathcollection.shaderpaths:                             ##shader searchpath
        shader_path_value = ""
        for shader_path in rmansettings.pathcollection.shaderpaths:
            shader_path_value += check_env(shader_path.name)+':'
    else:
        shader_path_value = ''
    shader_path_value += '@:&'                           
    maintain_searchpath('shader', shader_path_value) 


def sort_collection(collection):
    for i in range(len(collection)):
        if i>0:
            while collection[i].name < collection[i-1].name:
                collection.move(i, i-1)
                i -= 1

################################################################### not in use
def layer_name(current_pass, var):
    return current_pass.name  + "_" + var

def create_render_layers(current_pass, scene):
    names = []  
    for display in current_pass.displaydrivers:
        lname = layer_name(current_pass, display.var)
        if not display.displaydriver == "framebuffer":
            names.append(lname)
            
    layers = scene.render.layers            
            
    for i in range(len(names)):
        try:
            layers[i].name = names[i]  
        except:
            bpy.ops.scene.render_layer_add()
            layers[i].name = names[i] 
            
    for i in range(len(layers)):
        if not layers[i].name in names:
            scene.render.layers.active_index = i
            bpy.ops.scene.render_layer_remove()                                             
#################################################################### may delete this ... but we'll what the render api brings
             
def copy_parameters(master_groups, slave_groups, options = True):    
    for master_group in master_groups:
        slave_group = slave_groups[master_group.name]
        master_group.export = slave_group.export
        if options:
            masters = master_group.options
            slaves = slave_group.options
        else:
            masters = master_group.attributes
            slaves = slave_group.attributes 
                       
        for master in masters:
            slave = slaves[master.name]    
            copy_parameter(master, slave)
            
def copy_parameter(master, slave):
    master.parametertype = slave.parametertype
    master.textparameter = slave.textparameter
    master.colorparameter = slave.colorparameter
    try:
        master.export = slave.export
    except:
        pass        
    master.vector_size = slave.vector_size
    master.texture = slave.texture
    master.int_one[0] = slave.int_one[0]
    master.int_two[0] = slave.int_two[0]
    master.int_two[1] = slave.int_two[1]
    master.int_three[0] = slave.int_three[0]
    master.int_three[1] = slave.int_three[1]
    master.int_three[2] = slave.int_three[2] 
    master.float_one[0] = slave.float_one[0]
    master.float_two[0] = slave.float_two[0]
    master.float_two[1] = slave.float_two[1]
    master.float_three[0] = slave.float_three[0]
    master.float_three[1] = slave.float_three[1]
    master.float_three[2] = slave.float_three[2]                          

def maintain_parameters(master_groups, slave_groups, scene, options = True, obj=False):    
    for master_group in master_groups:
        if options:
            masters = master_group.options
        else:
            masters = master_group.attributes               
             
        if not master_group.name in slave_groups:
            slave_groups.add().name = master_group.name
            slave_group = slave_groups[master_group.name]
            try:
                slave_group.export = master_group.export
            except AttributeError:
                pass

        slave_group = slave_groups[master_group.name]                                      
        
        if options:    
            slaves = slave_group.options
        else:
            slaves = slave_group.attributes                     

        for master in masters:
            if not master.name in slaves:
                slaves.add().name = master.name
                slave = slaves[master.name]
                copy_parameter(slave, master)                          
                            
        sort_collection(slaves)
                            
        for index, slave in enumerate(slaves):
            if slave.name not in masters:
                slaves.remove(index)
            
    for group_index, slave_group in enumerate(slave_groups):
        if slave_group.name not in master_groups:
            print("remove group", slave_group.name, slave_groups)
            slave_groups.remove(group_index)
            
    if len(slave_groups) != len(master_groups):
        for sg in slave_groups:
            print(slave_groups, len(slave_groups), "!=", master_groups, len(master_groups))
            slave_groups.remove(0)            
            
    sort_collection(slave_groups)    
    
def maintain_beauty_pass(scene):
    renderman_settings = scene.renderman_settings
    if len(scene.renderman_settings.passes) == 0:
        renderman_settings.passes.add().name = 'Beauty'
    beauty = renderman_settings.passes[0]
    if not beauty.displaydrivers:
        adddisp(beauty)
        
    if renderman_settings.passes:
        if len(renderman_settings.passes) == 1 and not renderman_settings.searchpass:
            renderman_settings.passes_index = 0
        elif renderman_settings.searchpass:
            for i, passes in enumerate(renderman_settings.passes):
                if passes.name == renderman_settings.searchpass:
                    renderman_settings.passes_index = i
                    renderman_settings.searchpass = ""   
        
def atleast_one_pass(path):
    if not path.renderman:
        path.renderman.add().name = "Beauty"
    if path.renderman_index == -1 or path.renderman_index > len(path.renderman)-1:
        path.renderman_index = 0
    
def maintain_hiders(current_pass, scene):
    rmansettings =  scene.renderman_settings
    master_hiders = rmansettings.hider_list
    slave_hiders = current_pass.hider_list

    maintain_parameters(master_hiders, slave_hiders, scene)    
    
    if current_pass.hider == '':
        current_pass.hider = rmansettings.default_hider

def maintain_options(current_pass, scene):             ###maintain options for every pass
    rmansettings = scene.renderman_settings
    master_groups = rmansettings.option_groups
    slave_groups = current_pass.option_groups
    
    maintain_parameters(master_groups, slave_groups, scene)   

def checkForEnvMap(obj, scene):
    env = False
    texture = None
    if obj.active_material:
        textures = obj.active_material.texture_slots
        for mpass in obj.active_material.renderman:
            shader_parameter = obj.active_material.renderman[mpass.name].surface_shader_parameter
            for parm in shader_parameter:
                if parm.texture and parm.textparameter != "":
                    try:
                        texture = textures[parm.textparameter].texture
                        if texture.type == "ENVIRONMENT_MAP" and not texture.environment_map.source == "IMAGE_FILE":
                            env = True
                    except KeyError:
                        print("Texture Not Found")
    return env, texture
    
def maintain_environment_map_passes(obj, scene):
    passes = scene.renderman_settings.passes

    env, texture = checkForEnvMap(obj, scene)

    if env:                    
        addenvironmentmappass(obj, texture, scene)                
    
def clear_envmap_passes(pass_number, scene):
    ##clear envmap passes when not needed anymore
    global assigned_shaders
    passes = scene.renderman_settings.passes

    if pass_number < len(passes):    
        item = passes[pass_number]
        if item.camera_object:
            if not item.camera_object in scene.objects:
                passes.remove(pass_number)
                global assigned_shaders
                assigned_shaders = {}
            else:
                obj = scene.objects[item.camera_object]
                if not obj.type == "LAMP":
                    env, texture = checkForEnvMap(obj, scene)
                    if item.environment and not env:
                        print("killing envmap pass")
                        passes.remove(pass_number)
                        assigned_shaders = {}
                        pass_number -= 1
    
    return pass_number

    
    
def maintain_shadowmap_passes(obj, scene):
    passes = scene.renderman_settings.passes
    if obj.type == "LAMP":                    
        name = obj.name
        shadowname = name+"_shadowmap"
        shadow = False
        try:
            for lpass in obj.data.renderman:
                if lpass.shadowtype == "shadowmap":
                    shadow = True
        except AttributeError:
            pass
        
        if shadow:                     
            addshadowmappass(shadowname, name, scene)        
            shadowpass = passes[shadowname]           
            if obj.data.type == "POINT":                
                shadowpass.environment = True
            else:
                shadowpass.environment = False

        def remove(index):
            global assigned_shaders
            assigned_shaders = {}
            passes.remove(index)
        
        for passindex, item in enumerate(passes):
            if item.shadow:                
                try:
                    shadowlight = scene.objects[item.camera_object]
                    shadow = False                
                    for lpass in shadowlight.data.renderman:                
                        if lpass.shadowtype == "shadowmap":
                            shadow = True
                    if not shadow:      
                        remove(passindex)
                except KeyError:
                    remove(passindex)



def maintain_light(light, scene):
    if light.type == "LAMP":
        rc = light.renderman_camera
        global obj_passes, assigned_shaders
        rm = light.data.renderman
        if not light.name in obj_passes or len(rm) != obj_passes[light.name]:
            if light.name in assigned_shaders:
                lshaders = assigned_shaders[light.name]
                for l in lshaders:
                    if not l in rm:
                        assigned_shaders[light.name].pop(l)
                        break
                        
        for lpass in rm:
            parameter = lpass.light_shader_parameter
            active_parameter = light.data.renderman[light.data.renderman_index].light_shader_parameter
            if lpass.shadowtype == "shadowmap":
                shadowname = light.name + "_shadowmap"         
                addshadowmappass(shadowname, light.name, scene)
                shadowmap_unprocessed = scene.renderman_settings.passes[shadowname].displaydrivers[0].filename
                shadowmapname = shadowmap_unprocessed.replace("[frame]", framepadding(scene))
            elif lpass.shadowtype == 'raytrace':
                shadowname = ""
                shadowmapname = "raytrace"
            type = light.data.type
            
            if type == "SPOT":
                if light.data.shadow_method == "BUFFER_SHADOW":
                    light.data.shadow_buffer_clip_start = rc.near_clipping
                    light.data.shadow_buffer_clip_end = rc.far_clipping
            
            lrotx = light.rotation_euler[0]
            lroty = light.rotation_euler[1]
            lrotz = light.rotation_euler[2]   
            topoint = (0, 0, 1)
            
            
            cos = math.cos
            sin = math.sin
            abs = math.fabs
            radians = math.radians
            
            
            def maintainitem(name, value):
                if name in parameter:
                    active_parameter = parameter[name]
                    type = active_parameter.parametertype
                    if not active_parameter.free:
                        if type == "color":
                            active_parameter.colorparameter = value
                        elif type == "float":
                            if active_parameter.vector_size == 1:
                                active_parameter.float_one[0] = value
                            elif active_parameter.vector_size == 3:
                                active_parameter.float_three[0] = value[0]
                                active_parameter.float_three[1] = value[1]
                                active_parameter.float_three[2] = value[2]
                        elif type == "integer":
                            active_parameter.int_one[0] = value
                        elif type == "string":                                       
                            active_parameter.textparameter = value
            
            chsh = checkshaderparameter
            
            mappings = scene.renderman_settings.mappings
            
            if type == 'POINT':
                dirs = ["px", "nx", "py", "ny", "pz", "nz"]
                if lpass.shadowtype == "shadowmap":
                    if not lpass.customshader:
                        lpass.shaderpath = mappings.shadowpointshader
                    chsh(light.name, lpass, lpass.shaderpath, parameter, scene)
                    for dir in dirs:
                        maintainitem(mappings.point_shadowpref+dir, shadowmapname.replace("[dir]", dir))
                elif lpass.shadowtype == "raytrace":
                    if not lpass.customshader:
                        lpass.shaderpath = mappings.shadowpointshader
                    chsh(light.name, lpass, lpass.shaderpath, parameter, scene)
                    for dir in dirs:
                        maintainitem(mappings.point_shadowpref+dir, "raytrace")
                else:
                    if not lpass.customshader:
                        lpass.shaderpath = mappings.pointshader
                    chsh(light.name, lpass, lpass.shaderpath, parameter, scene)
                if "lightcolor" in active_parameter:
                    light.data.color = active_parameter["lightcolor"].colorparameter
                if "intensity" in active_parameter:
                    light.data.energy = active_parameter["intensity"].float_one[0]
            
            elif type == 'SPOT':
                if lpass.shadowtype == "shadowmap" or lpass.shadowtype == "raytrace":
                    if not lpass.customshader:
                        lpass.shaderpath = mappings.shadowspotshader
                    chsh(light.name, lpass, lpass.shaderpath, parameter, scene)
                    maintainitem(mappings.shadowmap, shadowmapname.replace("[dir]", ""))
                else:
                    if not lpass.customshader:
                        lpass.shaderpath = mappings.spotshader
                    chsh(light.name, lpass, lpass.shaderpath, parameter, scene)
                if "lightcolor" in active_parameter:
                    light.data.color = active_parameter["lightcolor"].colorparameter
                if "intensitiy" in active_parameter:
                    light.data.energy = active_parameter["intensity"].float_one[0]
                if "coneangle" in active_parameter:
                    if active_parameter["coneangle"].float_one[0] <= 0:
                        active_parameter["coneangle"].float_one[0] = radians(1)
                    light.data.spot_size = active_parameter["coneangle"].float_one[0]
                if "conedeltaangle" in active_parameter:
                    light.data.spot_blend = active_parameter["conedeltaangle"].float_one[0]/active_parameter["coneangle"].float_one[0]
                maintainitem("to", [0, 0, -1])
                maintainitem("from", [0, 0, 0])                
            
            elif type == 'SUN':
                if lpass.shadowtype == "shadowmap":
                    if not lpass.customshader:
                        lpass.shaderpath = mappings.shadowdistantshader
                    chsh(light.name, lpass, lpass.shaderpath, parameter, scene)
                    maintainitem(mappings.shadowmap, shadowmapname)
                elif lpass.shadowtype == "raytrace":
                    maintainitem(mappings.shadowmap, "raytrace")
                else:
                    if not lpass.customshader:
                        lpass.shaderpath = mappings.distantshader
                    chsh(light.name, lpass, lpass.shaderpath, parameter, scene)
                if "lightcolor" in active_parameter:
                    light.data.color = active_parameter["lightcolor"].colorparameter
                if "intensity" in active_parameter:
                    light.data.energy = active_parameter["intensity"].float_one[0]
                maintainitem("to", [0, 0, -1])     
                maintainitem("from", [0, 0, 0])                       

def objpass(p):
    if len(p.renderman) == 0:
        p.renderman.add().name = 'Beauty'
    if p.renderman_index < 0 or p.renderman_index >= len(p.renderman):
        p.renderman_index = len(p.renderman)-1
    return p.renderman[p.renderman_index]

def linked_pass(p, rpass):
    for lp in p.renderman:
        if rpass.name in lp.links:
            return lp

def maintain_lists(scene):
    global light_list, objects_size
    if not len(scene.objects) == objects_size:
        try:
            for obj in scene.objects:
                if not obj.type == 'LAMP':
                    al = False
                    if obj.active_material:
                        m = obj.active_material
                        if objpass(m).arealight_shader != "":
                            al = True
                if (obj.type == 'LAMP' or al) and not obj.name in light_list:
                    light_list.append(obj.name)
                    
            for i, obj in enumerate(light_list):
                if not obj in scene.objects:
                    light_list.pop(i)
                    
        except UnicodeDecodeError:
            pass         

class Renderman_OT_set_Active_Camera(bpy.types.Operator):
    bl_label = ""
    bl_idname = "renderman.set_active_camera"
    
    cam = String()
    
    def execute(self, context):
        context.scene.camera = context.scene.objects[cam]
        return {'FINISHED'}

def maintain_camera(rpass, scene):
    if rpass.camera_object == "" and scene.camera:
        rpass.camera_object = scene.camera.name
    rd = scene.render
    apass_cam_name = getactivepass(scene).camera_object
    if apass_cam_name != "" and apass_cam_name in scene.objects:
        apass_cam = scene.objects[apass_cam_name]
        rc = apass_cam.renderman_camera
        rd.resolution_x = rc.resx
        rd.resolution_y = rc.resy
        bpy.ops.renderman.set_active_camera(cam = apass_cam_name)

def maintain_rib_struct(scene):
    rm = scene.renderman_settings
    rs = rm.rib_structure
    rs.objects.folder = rm.objectdir
    rs.lights.folder = rm.lightdir
    rs.settings.folder = rm.settingsdir
    rs.world.folder =  rm.worlddir
    rs.particles.folder = rm.particledir
            

def maintain(scene):
    pathcoll = scene.renderman_settings.pathcollection
    if pathcoll.shaderpaths and not pathcoll.shadercollection:
        checkshadercollection(scene)
    
    maintain_beauty_pass(scene)
    
    maintain_lists(scene)          

    for i, rpass in enumerate(scene.renderman_settings.passes):
        maintain_camera(rpass, scene)
        maintain_display_drivers(rpass, scene)
#        maintain_options(rpass, scene)
        maintain_hiders(rpass, scene)
 #       create_render_layers(rpass, scene)
        maintain_searchpaths(rpass, scene) 
        i = clear_envmap_passes(i, scene)  
    
    for obj in scene.objects:
        atleast_one_pass(obj)    
        if obj.type == 'LAMP':
            atleast_one_pass(obj.data)
            maintain_shadowmap_passes(obj, scene)
            maintain_light(obj, scene)       

        else:
            for ps in obj.particle_systems:
                atleast_one_pass(ps.settings)
            for m in obj.material_slots:
                atleast_one_pass(m.material)
            update_illuminate_list(obj, scene)
            maintain_environment_map_passes(obj, scene)
            
    check_displaydrivers(scene) 
    check_display_variables(scene)  

    sort_collection(scene.renderman_settings.hider_list)
    for hider in scene.renderman_settings.hider_list:
        sort_collection(hider.options)   


def checkextension(file):
    file_array = file.split(".")
    file_array_len = len(file_array)
    file_extension = file_array[file_array_len-1]
    return file_extension    

def checkshadercollection(scene):
    pathcollection = scene.renderman_settings.pathcollection

    for shader in pathcollection.shadercollection:
        pathcollection.shadercollection.remove(0)

    shadbin = scene.renderman_settings.shaderbinary

    def addshader(path):
        for item in os.listdir(path):
            fullpath = os.path.join(path, item)
            shadext = checkextension(item)
            if pathcollection.shadercollection:
                exist = False
                for shader in pathcollection.shadercollection:
                    if fullpath == shader.fullpath:
                        exist = True

                if not exist and shadext == shadbin:
                    pathcollection.shadercollection.add().fullpath = fullpath
            else:
                if shadext and shadext == shadbin:
                    pathcollection.shadercollection.add().fullpath = fullpath


    for path in pathcollection.shaderpaths:
        checked_subdirs = []
        path_name = check_env(path.name)
        if os.path.exists(path_name):
            current_path = path_name
            checksubdir = True

            while checksubdir:
                addshader(current_path)

                subdir = False
                for dir in os.listdir(current_path):
                    fullpath = os.path.join(current_path, dir)

                    if os.path.isdir(fullpath):
                        if not fullpath in checked_subdirs:
                            subdir = True
                            current_path = fullpath

                if not subdir:
                    checked_subdirs.append(current_path)
                    if current_path == path_name:
                        checksubdir = False
                        break
                    else:
                        current_path = path_name

    
    for item in pathcollection.shadercollection:
        if item.name == "":
            item.name = os.path.split(item.fullpath)[1].replace('.'+shadbin, '')

def checkshaderparameter(identifier, active_pass, shader, shader_parameter, scene):
    global assigned_shaders
    
    def clear_shader_parameter(shader_parameter):
        for i in range(len(shader_parameter)):
            shader_parameter.remove(0)
            
    def addparameter(parameter, shader_parameter, value):
        parmname = parameter[0]
        if len(parameter) > 3:
            parameter.pop(1)
        type = parameter[1] + " " + parameter[2]
        shader_parameter.add().name = parmname
        ap = shader_parameter[parmname]
        ap.type = type
        if "color" in parameter:
            ap.parametertype = "color"
            value = value.split()
            ap.colorparameter[0] = float(value[0])
            ap.colorparameter[1] = float(value[1])
            ap.colorparameter[2] = float(value[2])
        elif "float" in parameter:
            ap.parametertype = "float"
            ap.vector_size = 1
            ap.float_one[0] = float(value)
            
        elif "point" in parameter or "normal" in parameter or "vector" in parameter:
            ap.parametertype  = "float"
            ap.vector_size = 3
            value = value.split()
            ap.float_three[0] = float(value[0])
            ap.float_three[1] = float(value[1])
            ap.float_three[2] = float(value[2])

        elif parameter[2] == "string":
            value = value.replace('"', "")
            value = value.replace(" ", "")
            ap.textparameter = value
             
    def readparms():
        parameters = []
        values = []
        output_variables = []        
        tmpfile = open(fulltmpname, "r")
        textlines = tmpfile.readlines()
        tmpfile.close()
        for i, line in enumerate(textlines):
            if len(line.split()) == 0:
                textlines.pop(i)
        try:       
            textlines.pop(0)
        except IndexError:
            assigned_shaders = {}
            return 0
        [parameters.append(p) for p in textlines if p.find("Default value") == -1]
        parameters = [parameter.replace('\n', '') for parameter in parameters]
        parameters = [parameter.replace('\t', '') for parameter in parameters]
        parameters = [parameter.replace('"', '') for parameter in parameters]
        [values.append(v) for v in textlines if not v.find("Default value") == -1]
        
        if shader_parameter:
            old_removed = False
            i = -1
            removing = False
            while not old_removed:
                i += 1
                if i < len(shader_parameter):
                    there = False
                    p = shader_parameter[i]
                    for parameter in parameters:
                        try:
                            pname = parameter.split()[0]
                        except:
                            print(parameter)
                        if pname == p.name:
                            there = True
                    if not there:
                        shader_parameter.remove(i)
                        removing = True
                else:
                    if not removing:
                        old_removed = True
                        break
                    else:
                        removing = False
                        i = -1
        
        for index, parameter in enumerate(parameters):
            try:
                value = values[index]
            except:
                break
            
            value = value.replace("Default value:", "")
            if value.find('[') != -1:
                value = value[value.find("["):value.find("]")]
                value = value.replace('[', '')
            if parameter.find("output") != -1:
                parmname = parameters.pop(index).split()[0]
                output_variables.append(parmname)
            
            parm = parameter.split()
            if not parm[0] in shader_parameter: 
                addparameter(parm, shader_parameter, value)
        
        var_collection = scene.renderman_settings.var_collection        
        for var in output_variables:
            if not var in var_collection:
                var_collection.add().name = var                
        
        parmnames = []
        [parmnames.append(parm.split()[0]) for parm in parameters]
        for killer, item in enumerate(shader_parameter):
            if item.name not in parmnames:
                shader_parameter.remove(killer) 
        return parameters, values
                
    def check_curr_shader(current_shader):
        if not active_pass.name in current_shader or current_shader[active_pass.name] != shader:
            readparms()
            current_shader[active_pass.name] = shader
        return current_shader

    shadercollection = scene.renderman_settings.pathcollection.shadercollection
    if not shader or not shadercollection:
        clear_shader_parameter(shader_parameter)
        return 0
    
    shadinfo = scene.renderman_settings.shaderinfo
    
    tmpdir = tempfile.gettempdir()
    tmpfilename = shader+".tmp"
    fulltmpname = os.path.join(tmpdir, tmpfilename)
    mod_time = shadercollection[shader].mod_time       
    
    try:
        fullshaderpath = shadercollection[shader].fullpath
    except:
        fullshaderpath = ""      
        clear_shader_parameter(shader_parameter)
    
    ###### Binary Shader
    if fullshaderpath:          

        modtime_new = math.floor(os.path.getmtime(fullshaderpath))

        if modtime_new != mod_time:
            scene.renderman_settings.pathcollection.shadercollection[shader].mod_time = modtime_new
            
            file = open(fulltmpname, "w")
            subprocess.Popen([shadinfo, fullshaderpath], stdout=file).communicate()
            file.close()
            readparms()
            
        if not identifier in assigned_shaders or assigned_shaders[identifier] != check_curr_shader(assigned_shaders[identifier]):
            cs = check_curr_shader({})
            assigned_shaders[identifier] = cs
                
    sort_collection(shader_parameter)                   

##################################################################################################################################

def register():
    bpy.ops.renderman.maintain()
    
def unregister():
    pass


    
