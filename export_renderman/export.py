
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

#########################################################################################################
#                                                                                                       #
#       Export data functions                                                                           #
#                                                                                                       #
#########################################################################################################

import export_renderman
import export_renderman.rm_maintain
from export_renderman.rm_maintain import *

import bpy
import math

current_pass = base_archive = active_archive = None
direction = ""

def get_write():
    global active_archive
    return active_archive.file.write

def get_archive(path = None, type = "", parent_type = ""):
    global base_archive
    return base_archive.get_child(path, type = type, parent_type = parent_type)
        

class Archive(): ## if specified open a new archive otherwise link to the parents file handle
    
    '''
    Class to manage structure of RIB Archives. The main export function initializes the base archive
    with Archive(scene = scene, current_pass = ..., filepath), where filepath is the path specified in the export() function and
    stores this Archive Object in the global variable base_archive. All the other functions just call
    base_archive.get_child() and get the correct Archive Object except functions that are executed on several
    archives, e.g. writeparms() just need to call get_write() that will return the active archive.
    If one wants to export a single object call Archive(obj, scene = scene).
    '''
    
    data_path = None ## path to datablock
    parent_archive = None ## store its parent
    filepath = ""
    scene = None
    frame = None
    current_pass = None
    type = "" ## identifier for the rs path
    rs = None ## path to rib_structure properties
    closed = False
    
    def __init__(   self,
                    data_path = None,
                    parent_archive = None,
                    filepath = "",
                    scene = None,
                    current_pass = None,
                    type = ""):
        
        self.child_archives = []
        self.file = None
        global base_archive, active_archive
        if not base_archive: 
            base_archive = self
            if not data_path: data_path = self.data_path = self.scene = scene
        self.type = type
        self.filepath = filepath
        self.data_path = data_path
        self.parent_archive = parent_archive

        active_archive = self
            
        if scene == None:
            scene = self.scene = base_archive.scene
        else:
            self.scene = scene
            self.frame = scene.frame_current
        
        if current_pass != None:
            self.current_pass = current_pass
        else:
            self.current_pass = current_pass = base_archive.current_pass    
        
        rm = scene.renderman_settings
        
        rs_base = rm.rib_structure
        
        types = {   'Object' : rs_base.objects,
                    'Material' : rs_base.materials,
                    'MESH' : rs_base.meshes,
                    'LAMP' : rs_base.lights,
                    'Scene' : rs_base.render_pass,
                    'Settings' : rs_base.settings,
                    'World' : rs_base.world}
            
        base_path = getdefaultribpath(scene)
        if type == "":
            type = self.type = data_path.rna_type.name
            
        self.rs = rs = types[type]
        path = os.path.join(base_path, rs.folder)
        
        if type == "Particle System": prop_path = data_path.settings
        elif type == "LAMP": prop_path = data_path.data
        else: prop_path = data_path
        
        if self.type in ['Scene', 'Settings', 'World']:
            pname = current_pass.name
        else:
            print("trying to get linked pass for this object")
            pname = linked_pass(prop_path, current_pass).name
        try: objname = data_path.name
        except AttributeError: objname = ""
        name = getname( rs.filename,
                        name = objname,
                        pass_name = pname) + '.rib'
        if filepath == "":
            filepath = os.path.join(path, name)
        
        if rs.own_file:
            if not os.path.exists(path): os.mkdir(path)
            if parent_archive != None:
                if type == "MESH" and prop_path.data.export_type == 'DelayedReadArchive':
                    parent_archive.file.write('DelayedReadArchive "'+filepath.replace('\\', '\\\\')+'" [')
                    for bound in obj.bound_box:
                        parent_archive.file.write([" ".join(str(b)) for b in bound])
                        parent_archive.file.write(" ")
                    parent_archive.file.write(']\n') 
                parent_archive.file.write('ReadArchive "'+filepath.replace('\\', '\\\\')+'"\n')
            if self.rs.overwrite or not os.path.exists(filepath):
                self.file = open(filepath, "w")
        else:
            if parent_archive != None: self.file = parent_archive.file
        if parent_archive != None:
            parent_archive.child_archives.append(self)

        
    def close(self):
        global base_archive
        if self == base_archive: 
            ## if it's the base archive reset the global var back to None because exporting finished
            base_archive = None
        if self.parent_archive and not self.parent_archive.file == self.file:   
            self.file.close()
        elif not self.parent_archive:     
            self.file.close()
        
    def get_child(self, path, type = "", parent_type = ""):
        print("looking for:", type, "it's parent is", parent_type)
        def children(a):              ## recursivly checking the children and returning the one looking for
            print("checking:", a.type)
            if not (a.type == parent_type):
                if a.child_archives != []:
                    for ch in a.child_archives:
                        test = children(ch)
                        if test:
                            return test
            else:
                print("parent is matching")
                if a.child_archives == []: ## parent is matching and there is no child archive so create a new archive
                    print("there is no child so create a new archive")
                    return None, a
                else:
                    print("there are children, looking for matching one")
                    for child in a.child_archives:
                        if child.data_path == path and (type == "" or child.type == type):
                            print("child is matching, returning it")
                            return child, a                 
                        else:
                            print("no child is matching. returning a new archive")
                            return None, a

        a, p = children(self)
        
        if a != None:
            return a
        else:
            return Archive(data_path = path, parent_archive = p, type = type)


#############################################
#                                           #
#   Convert Collection Property items       #
#   into RIB Code                           #
#                                           #
#############################################


def write_attrs_or_opts(groups, attr_opt, tab):
    global current_pass
    write = get_write()
    for group in groups:
        grp = {"Option" : group.options, "Attribute" : group.attributes}        
        if group.export:
            write(tab + attr_opt + ' \n\t"'+group.name+'" ')
            writeparms(grp[attr_opt], write)                                       

def writeparms(path):
    global current_pass, scene
    scene = base_archive.scene
    write = get_write()
    for parm in path:
        write('\n\t\t')
        name = parm.name
        if name.find('[') != -1:
            name = name[:name.find('[')]
        if parm.export:
            if parm.parametertype == 'string':
                if parm.texture:
                    texture = bpy.data.textures[parm.textparameter]
                    if texture.renderman.type == 'bake':
                        string = os.path.join(getdefaultribpath(scene), texture.name+framepadding(scene)+".bake").replace('\\', '\\\\')
                else:
                    string = parm.textparameter
                write('"string '+name + '" ["' + string + '"]')
            if parm.parametertype == 'float':
                if parm.vector_size == 1:
                    write('"float '+name + '" [' + str(parm.float_one[0]) + ']')
                elif parm.vector_size == 2:
                    write('"float[2] '+name + '" [' + str(parm.float_two[0]) + ' ' + str(parm.float_two[1]) + ']')
                elif parm.vector_size == 3:
                    write('"float[3] '+name + '" [' + str(parm.float_three[0]) + ' ' + str(parm.float_three[1]) + ' ' + str(parm.float_three[3]) + ']')                                        
            if parm.parametertype == 'int':
                if parm.vector_size == 1:
                    write('"int '+name + '" [' + str(parm.int_one[0]) + ']')
                elif parm.vector_size == 2:
                    write('"int[2] '+name + '" [' + str(parm.int_two[0]) + ' ' + str(parm.int_two[1]) + ']')
                elif parm.vector_size == 3:
                    write('"int[3] '+name + '" [' + str(parm.int_three[0]) + ' ' + str(parm.int_three[1]) + ' ' + str(parm.int_three[3]) + ']')
            if parm.parametertype == 'color':
                colR = parm.colorparameter[0]
                colG = parm.colorparameter[1]
                colB = parm.colorparameter[2]
                write('"color '+name + '" [' + str(colR) + " " + str(colG) + " " + str(colB) + "]")
            write(' ')

def writeshaderparameter(parameterlist):
    global current_pass, base_archive
    scene = base_archive.scene
    write = get_write()
    for i, parm in enumerate(parameterlist):
        write('\n\t"'+parm.type+' '+parm.name+'"')
        if parm.parametertype == 'string':
            if parm.texture:
                if parm.texture != "" and parm.textparameter in bpy.data.textures:
                    texture = bpy.data.textures[parm.textparameter]
                if texture.renderman.type == "file":
                    image = texture.image
                    if image.source == 'GENERATED':
                        image.filepath = os.path.join(getdefaultribpath(scene), image.name)
                        image.save()
                    if texture.renderman.process:
                        prepare_texture(texture.image.filepath, "", scene)
                        tx = prepared_texture_file(texture.image.filepath, scene).replace('\\', '\\\\')
                elif texture.renderman.type =="envmap":
                    file = scene.renderman_settings.passes[texture.renderman.envpass].displaydrivers[0].file
                    tx = file.replace("[dir]", "").replace("[frame]", framepadding(scene))
                elif texture.renderman.type == "bake":
                    tx = os.path.join(getdefaultribpath(scene), texture.name+framepadding(scene)+".bake").replace('\\', '\\\\')
                write(' ["'+tx+'"] ')
                        
            else:
                write(' ["' + parm.textparameter + '"] ')
        if parm.parametertype == 'float' and parm.vector_size == 1:
            write(" [" + str(parm.float_one[0]) + '] ')
        if parm.parametertype == 'color':
            colR = parm.colorparameter[0]
            colG = parm.colorparameter[1]
            colB = parm.colorparameter[2]
            write(" [" + str(colR) + " " + str(colG) + " " + str(colB) + "] ")
        if parm.parametertype == 'float' and parm.vector_size == 3:
            x = str(parm.float_three[0])
            y = str(parm.float_three[1])
            z = str(parm.float_three[2])
            write(" [" + x + " " + y + " " + z + "] ")

def prepared_texture_file(file):
    global current_pass, base_archive
    scene = base_archive.scene
    return os.path.splitext(file)[0]+"."+scene.renderman_settings.textureext

def prepare_texture(texturefile, parameters):
    global current_pass, base_archive
    scene = base_archive.scene
    textool = scene.renderman_settings.textureexec
    args = ' "'+texturefile+'" "'+prepared_texture_file(texturefile)+'"'+parameters
    os.system(textool+args)

def get_mb_sampletime(samples, shutterspeed):
    global current_pass
    sampletime = [0]
    for i in range(2, samples+1):
        addtosample = round((shutterspeed/samples)*i)
        sampletime.append(addtosample)
    return sampletime

def mb_setframe(start_frame, t, speed):
    global base_archive, current_pass
    scene = base_archive.scene
    scene.frame_set(scene.frame_current - (speed - t))

def motionblur( path,
                function,
                *args,
                frameset = True,
                **keys):
                    
    global current_pass
    write = get_write()
    motion_samples = path.motion_samples
    shutterspeed = current_pass.shutterspeed
    
    sampletime = get_mb_sampletime(motion_samples, shutterspeed)
        
    write('MotionBegin[')
    write(' '.join([str(s) for s in sampletime]))
    write(']\n')
    for s in sampletime:
        if frameset:
            mb_setframe(s, shutterspeed, scene)
        function(*args, **args)
    write('MotionEnd\n')

#############################################
#                                           #
#   Write Render Settings                   #
#   (the stuff before World Block begins)   #
#                                           #
#############################################

def prepare_textures(textures):
    global base_archive, current_pass
    scene = base_archive.scene
    ouptputpath = os.path.join(getdefaultribpath(scene), scene.name)
    texturepath = os.path.join(outputpath, scene.renderman_settings.texdir)

    for texture in textures:
        if texture.renderman.type == "file":
            image = texture.image
            if image:
                if image.source == "GENERATED":
                    image.file_format = "TARGA"
                    image.filepath = os.join(texturepath, image.name)
                    if not os.path.exists(image.filepath):
                        image.save()
                    prepare_texture(image.filepath, "", scene)
                    
    textureribfile.close()
    
    os.system('"'+scene.renderman_settings.renderexec+'" "'+texturerib+'"')
                    
def writeSettings(camrot):
    global base_archive, direction
    dir = direction
    scene = base_archive.scene
    current_pass = base_archive.current_pass
    
    settings_archive = get_archive(current_pass, type = "Settings", parent_type = "Scene")
    write = settings_archive.file.write
    print("write Scene Settings ...")

    if not current_pass.displaydrivers:
        nodisplay = True
    else:
        nodisplay = False
				
    if current_pass.name == "Beauty" and not current_pass.displaydrivers:
        adddisp(current_pass)
    render = scene.render
   

    respercentage = render.resolution_percentage

    camera = scene.objects[current_pass.camera_object]
    rc = camera.renderman_camera

    nearclipping = rc.near_clipping
    farclipping = rc.far_clipping
    shift_x = rc.shift_x * 2
    shift_y = rc.shift_y * 2
    
    resx = math.trunc(rc.resx/100*respercentage)
    resy = math.trunc(rc.resy/100*respercentage)

    x = rc.resx * rc.aspectx
    y = rc.resy * rc.aspecty
   
    if x >= y:
        asp_y = y/x
        asp_x = 1.0
    else:
        asp_x = x/y
        asp_y = 1.0

    aspectratio = rc.aspectx/rc.aspecty

    left = str(-asp_x+shift_x)
    right = str(asp_x+shift_x)

    top = str(-asp_y+shift_y)
    bottom = str(asp_y+shift_y)

    dof_distance = scene.camera.data.dof_distance
    if rc.use_lens_length:
        focal_length = scene.camera.data.lens/100
    else:
        focal_length = rc.focal_length
    fstop = rc.fstop





### Display driver
    for dispcount, display in enumerate(current_pass.displaydrivers):
        quant_min = str(display.quantize_min)
        quant_black = str(display.quantize_black)
        quant_max = str(display.quantize_max)
        quant_white = str(display.quantize_white)
        gamma = str(float(int(display.gamma*100)/100))
        gain = str(float(int(display.gain*100)/100))
        file = display.file.replace("[frame]",framepadding(scene))
        print(dir)
        file = file.replace("[dir]", dir)
        write('Display ')
        if dispcount > 0:
            write('"+')
        else:
            write('"')
        write(file + '" "' + display.displaydriver + '" "'+display.var+'" ')
        write('"int[4] quantize" [' + quant_min + ' ' + quant_max + ' ' + quant_black + ' ' + quant_white + ']')
        write(' "float[2] exposure" [' + gain + ' ' + gamma + ']')
        if display.custom_options:
            write(" ")
            writeshaderparameter(display.custom_options, write)
        write('\n')

### Format
    write('Format ')
    write(str(resx) +' '+ str(resy) +' '+ str(aspectratio)+'\n')

### ScreenWindow
    write('ScreenWindow '+left +' '+ right +' '+ top +' '+ bottom + '\n')

### Clipping
    write('Clipping '+str(nearclipping)+' '+str(farclipping)+'\n')

### DepthOfField
    print(current_pass.camera_object)
    if current_pass.camera_object == "" and scene.camera.data.depthoffield:
        write('DepthOfField '+str(fstop)+' '+str(focal_length)+' '+str(dof_distance)+'\n')

### PixelFilter
    filter = current_pass.pixelfilter.filterlist
    fwidth = str(current_pass.pixelfilter.filterwidth)
    fheight = str(current_pass.pixelfilter.filterheight)
    write('PixelFilter "'+filter+'" '+fwidth+' '+fheight+'\n')
    
### PixelSamples
    sampx = str(current_pass.pixelsamples_x)
    sampy = str(current_pass.pixelsamples_y)
    write('PixelSamples '+sampx+' '+sampy+'\n')    

### Options
    write_attrs_or_opts(current_pass.option_groups, "Option", "")
    write('\n')
    
### Hider
    if current_pass.hider != "":
        write('Hider "'+current_pass.hider+'"')
        hider_parms = current_pass.hider_list[current_pass.hider].options
        writeparms(hider_parms)
        write('\n')    

### Orientation    
    write('Orientation "lh"\n')

### Custom Code
    if current_pass.scene_code:
        for code in current_pass.scene_code:
            write(code.name + '\n')

    print("Done")
    
### Camera
    if current_pass.displaydrivers:
        writeCamera(camera, camrot)
    
    
    settings_archive.close()
      


#############################################
#                                           #
#   Camera Projection and Transformation    #
#                                           #
#############################################

def round(float):
    if math.modf(float)[0] >= 0.5:
        integer = math.ceil(float)
    else:
        integer = math.floor(float)
    return integer 

def objtransform(obj, mx = None):
    global base_archive, current_pass
    write = get_write()
    def writetransform(obj):
        if mx: matrix = mx
        else: matrix = obj.matrix_world
        write('ConcatTransform [\t')    
        for i, row in enumerate(matrix):
            for val in row:
                write(" " + str(val))
            if not i == len(matrix)-1: write('\n\t\t\t\t\t')
        write(']\n')
    
    ## transformation blur    
    sampletime = []
    
    objpass = linked_pass(obj, current_pass)
    if objpass and objpass.transformation_blur and current_pass.motionblur:
        motionblur( objpass,
                    writetramsform,
                    obj)
    else: writetransform(obj)


def writeCamera(cam, camrot):
    degrees = math.degrees
    global current_pass, direction, base_archive
    dir = direction
    scene = base_archive.scene
    settings_archive = get_archive(current_pass, type = "Settings", parent_type = "Scene")
    write = settings_archive.file.write    
    print("write Camera Settings ...")
    
    def writeCameraTransform(trans):
        matrix = cam.matrix_world
        ribx = str(matrix[3][0]*-1)
        riby = str(matrix[3][1]*-1)
        ribz = str(matrix[3][2]*-1)
        if current_pass.environment:
            rotx, roty, rotz = camrot
        else:
            rotx, roty, rotz = cam.rotation_euler
            
        transform = {   "RotX" : "Rotate "+str(degrees(rotx*-1))+" 1 0 0\n",
                        "RotY" : "Rotate "+str(degrees(roty*-1))+" 0 1 0\n",
                        "RotZ" : "Rotate "+str(degrees(rotz*-1))+" 0 0 1\n",
                        "Translate" : "Translate "+ribx+" "+riby+" "+ribz+"\n" }
        write(transform[trans])
        
    def writePerspective(fov, perspective):
        if perspective:
            typestring = '"perspective" "fov" ['+fov+']\n'
    
        elif not perspective:
            typestring = '"orthographic"\n'

        write('Projection '+typestring)

    if current_pass.motionblur:
        shutterspeed = current_pass.shutterspeed
        write('Shutter 0 '+str(shutterspeed)+'\n')

    def checkoutFOVnPersp():
        perspective = True
        if cam.type =='CAMERA':
            lens = degrees(cam.data.angle)
            if cam.data.type == 'PERSP':
                perspective = True
                fov = str(lens)
            else:
                perspective = False
    
        elif cam.type =='LAMP':
            if cam.data.type == 'SPOT':
                lens = math.degrees(cam.data.spot_size)
                fov = str(lens)
                perspective = True
            elif cam.data.type == 'POINT':
                perspective = True
                fov = "90"
            elif cam.data.type == 'SUN':
                perspective = False
        else:
            fov = str(bpy.data.textures[current_pass.envname].renderman.fov)
            perspective = True
        return fov, perspective

#    ##perspective blur
#    sampletime = []
#    if linked_pass(cam, current_pass).perspective_blur:
#        motion_samples = linked_pass(cam, current_pass).motion_samples
#        current_frame = scene.frame_current  
#        shutterspeed, sampletime = motionblur(motion_samples, current_pass, scene)
#    
#        if current_pass.motionblur:
#            write('MotionBegin[')
#            for s in sampletime:
#                write(str(s)+' ')
#            write(']\n')
#            for s in sampletime:
#                scene.frame_set(current_frame - (shutterspeed - s))
#                fov, perspective = checkoutFOVnPersp()
#                writePerspective(fov, perspective)
#        write('MotionEnd\n')
#                   
#    else:
    fov, perspective = checkoutFOVnPersp()
    writePerspective(fov, perspective)

    if not current_pass.environment:
        write("Scale 1 1 -1\n")
        
    ##Camera Transformation Blur

    ts = cam.renderman_camera.transformation_blur
    if ts and current_pass.motion_blur:
        for t in ["RotX", "RotY", "RotZ", "Translate"]:
            motionblur( linked_pass(cam, current_pass),
                        current_pass,
                        write,
                        scene,
                        writeCameraTransform,
                        t)
    else:
        for t in ["RotX", "RotY", "RotZ", "Translate"]:
            writeCameraTransform(t)
              
    write("\n\n")
    print("Done")
    

#############################################
#                                           #
#  World Block                              #
#                                           #
#############################################


def writeWorld():
    global base_archive, current_pass
    scene = base_archive.scene
    
    world_archive = get_archive(current_pass, type = "World", parent_type = "Scene")
    write = world_archive.file.write
    global_shader = current_pass.global_shader

    write("WorldBegin\n")
    write_attrs_or_opts(current_pass.attribute_groups, "Attribute", "")
    write('\n\n')
    ### Custom Code
    
    if current_pass.world_code:
        for code in current_pass.world_code:
            write(code.name + '\n')
            
    writeshader(global_shader.surface_shader, global_shader.surface_shader_parameter, "Surface")
    writeshader(global_shader.atmosphere_shader, global_shader.atmosphere_shader_parameter, "Atmosphere")
            

    if not current_pass.exportobjects and current_pass.lightgroup:
        objects = bpy.data.groups[current_pass.objectgroup].objects
    else:
        objects = scene.objects

    if not current_pass.exportlights and current_pass.lightgroup:
        lights = bpy.data.groups[current_pass.lightgroup].objects
    elif not current_pass.exportlights and not current_pass.lightgroup:
        lights = []
    else:
        lights = scene.objects

    if lights:
        for light in lights:
            writeLight(light)
        write('\n')
        for light in lights:
            al = False
            if light.type != 'LAMP':
                m = light.active_material
                if m:
                    if linked_pass(m, current_pass).arealight_shader != "":
                        al = True
            if light.type == 'LAMP' or al:
                write('Illuminate "'+light.name+'" 1\n')
        
    write('\n')

    if objects:
        for obj in objects:
            if not obj.hide_render and not obj.name == current_pass.camera_object and check_visible(obj, scene):
                writeObject(obj)
                writeParticles(obj)                 
    write("WorldEnd\n")
    world_archive.close()


#############################################
#                                           #
#   Lights                                  #
#                                           #
#############################################


def writeLight(light, scene = None):
    if light.type == 'LAMP':
        global base_archive, current_pass
        if scene == None:
            scene = base_archive.scene
        rmansettings = scene.renderman_settings
        al = False
        if light.type != 'LAMP' and light.active_material:
            mat = light.active_material
            alshader = linked_pass(mat, current_pass).arealight_shader
            if alshader != "":
                al = True
            
        if (light.type == 'LAMP' or al) and not light.hide_render:
            if check_visible(light, scene):
                
                light_archive = get_archive(path = light,
                                            type = "LAMP",
                                            parent_type = "World")
                write = light_archive.file.write
                
                print("write "+light.name)
                rotx = str(math.degrees(light.rotation_euler.x))
                roty = str(math.degrees(light.rotation_euler.y))
                rotz = str(math.degrees(light.rotation_euler.z))          
        
                write("\nAttributeBegin\n")      
                write_attrs_or_opts(linked_pass(light.data, current_pass).attribute_groups, "Attribute", "")
                objtransform(light)
                if al:
                    write('AreaLightSource ')
                    parameterlist = linked_pass(mat, current_pass).light_shader_parameter
                    write('"'+alshader.replace("."+rmansettings.shaderbinary, "")+'" "'+light.name+'" ')
                    writeshaderparameter(parameterlist, write)
                    write('\n')
                    export_type = light.data.export_type
                    
                    if light.data.show_double_sided:
                        write('Sides 2\n')
                        
                    if mat: write(writeMaterial(write, current_pass, scene, mat))
                    
                    if export_type == 'ObjectInstance':
                        write('ObjectInstance "'+light.data.name+'"\n')
                    else:
                        export_object(write, current_pass, scene, light, export_type)
                else:
                    write('LightSource ')
                    parameterlist = linked_pass(light.data, current_pass).light_shader_parameter
                    write('"'+linked_pass(light.data, current_pass).shaderpath.replace("."+rmansettings.shaderbinary, "")+'" "'+light.name+'" ')         
                    writeshaderparameter(parameterlist)
                    write('\n')

                write('AttributeEnd\n')
                light_archive.close()
                print("Done")


#############################################
#                                           #
#   Materials                               #
#                                           #
#############################################
def writeshader(shader, parms, type):
    global base_archive
    scene = base_archive.scene
    write = get_write()
    rmansettings = scene.renderman_settings
    if shader:
        shader = shader.replace("."+rmansettings.shaderbinary, "")
        write(type+' "'+shader+'" ')
        writeshaderparameter(parms)
        write('\n')             

def writeMaterial(mat):
    global active_archive
    scene = active_archive.scene
    p = active_archive
    mat_archive = get_archive(path = mat, parent_type = "Object")
    write = mat_archive.file.write
    rmansettings = scene.renderman_settings
    mat_pass = linked_pass(mat, current_pass)
    
    if mat_pass:
        ## Color & Opacity Motion Blur
        def writeColor():  
            colR = mat_pass.color.r
            colG = mat_pass.color.g
            colB = mat_pass.color.b
            write('Color ['+str(colR)+' '+str(colG)+' '+str(colB)+']\n')
           
        def writeOpacity():
            opR, opG, opB = mat_pass.opacity    
            write('Opacity ['+str(opR)+' '+str(opG)+' '+str(opB)+']\n')
            


        def matblur(function, *args):     
            motionblur( mat_pass,
                        current_pass,
                        write,
                        scene,
                        function,
                        *args)

        if mat_pass.color_blur:                
            matblur(writeColor)
        else:
            writeColor()
            
        if mat_pass.opacity_blur:        
            matblur(writeOpacity)
        else:
            writeOpacity()

        surface_shader = mat_pass.surface_shader
        surface_parameter = mat_pass.surface_shader_parameter 
        displacement_shader = mat_pass.displacement_shader
        displacement_parameter = mat_pass.disp_shader_parameter 
        interior_shader = mat_pass.interior_shader
        interior_parameter = mat_pass.interior_shader_parameter
        exterior_shader = mat_pass.exterior_shader
        exterior_parameter = mat_pass.exterior_shader_parameter    
      
        if mat_pass.shader_blur:
            matblur(writeshader, surface_shader, surface_parameter, "Surface")
            matblur(writeshader, displacement_shader, displacement_parameter, "Displacement")
            matblur(writeshader, interior_shader, interior_parameter, "Interior")
            matblur(writeshader, exterior_shader, exterior_parameter, "Exterior")
        else:
            writeshader(surface_shader, surface_parameter, "Surface")
            writeshader(displacement_shader, displacement_parameter, "Displacement")
            writeshader(interior_shader, interior_parameter, "Interior")
            writeshader(exterior_shader, exterior_parameter, "Exterior")
        mat_archive.close()


#############################################
#                                           #
#   Particles                               #
#                                           #
#############################################
matrices = []

def writeParticles(obj):
    rmansettings = scene.renderman_settings
    pfiles = []

    if len(obj.particle_systems) > 0:
        for psystem in obj.particle_systems:
            if psystem.settings.type == 'EMITTER':
                
                rman = linked_pass(psystem.settings, current_pass)
                if rman:
                    ## Points
                    if rman.render_type == "Points":
                        pwrite('Points\n')
                    
                        pwrite('"P" [')
                        for part in psystem.particles:
                            rotation = part.rotation.to_euler()
                            rotx = str(math.degrees(rotation[0]))
                            roty = str(math.degrees(rotation[1]))
                            rotz = str(math.degrees(rotation[2]))
                            locx = str(part.location.x)
                            locy = str(part.location.y)
                            locz = str(part.location.z)
                                               
                            pwrite(locx+' '+locy+' '+locz+' ')                  
                                           
                        pwrite(']\n')
                        
                        pwrite('"width" [')
                        for part in psystem.particles:
                            size = str(part.size)
                            
                            pwrite(size+' ')
                        pwrite(']\n')
                        
                    ## Objects
                    elif rman.render_type == "Object":
                        part_obj = scene.objects[rman.object]
                    def transform(part):          
                            mx_new = mathutils.Matrix()
                            trans = part.location
                            mx_trans = mx_new.Translation(trans)
                            mx_rot = part.rotation.to_matrix().to_4x4()
                            mx_scale = mx_new.Scale(part.size, 4)
                            mx = mx_trans * mx_scale * mx_rot
                            return mx

                    def mb_trans_particles(matrices, i):
                        for m in matrices:
                            objtransform(None, mx = matrices.pop(0)[i])

                    matrices = []
                    mx_set = []
                    for i, part in enumerate(psystem.particles):
                        mx_set.append(transform(part))
                    matrices.append(mx_set)                   
                    
                    for i, part in enumerate(psystem.particles):
                        if scene.frame_current >= part.birth_time:
                            pwrite('AttributeBegin\n')
                            
                            if rman.motion_blur and current_pass.motionblur:
                                motionblur( rman,
                                            current_pass,
                                            write,
                                            scene,
                                            mb_trans_particles,
                                            matrices,
                                            i,
                                            frameset = 0)
                            else:
                                mb_trans_particles
                                                        
                            writeObject(pwrite, current_pass, scene, part_obj) 
                        
                            pwrite('AttributeEnd\n')  
                                
                        write("\nAttributeBegin\n")
                        write('Attribute "identifier" "name" ["'+obj.name+'_particles"]\n')
                        write_attrs_or_opts(linked_pass(obj, current_pass).attribute_groups, write, "Attribute", "", scene)
                    
                        if not current_pass.shadow:
                            for item in linked_pass(obj, current_pass).light_list:
                                if not item.illuminate:
                                    write('Illuminate "'+item.lightname+'"')
                                    write(' 0\n')
                        for p in pfiles:
                            write('ReadArchive "'+p.replace('\\', '\\\\')+'"\n')                        
                        write('AttributeEnd\n')

#############################################
#                                           #
#   Objects                                 #
#                                           #
#############################################
    
def writeObject(obj):
    global base_archive, current_pass
    scene = base_archive.scene

    if obj.type in ['MESH']:
        obj_pass = linked_pass(obj, current_pass)
        if obj_pass:               
            obj_archive = get_archive(obj, parent_type = "World")
            write = obj_archive.file.write
            mat = obj.active_material            
            
            write("##"+obj.name+'\n')
            if obj.parent:
                write('#child of '+obj.parent.name+'\n')
            write("AttributeBegin\n")
            write('Attribute "identifier" "name" ["'+obj.name+'"]\n')
            write_attrs_or_opts(obj_pass.attribute_groups, "Attribute", "")

            if not current_pass.shadow:
                for item in obj_pass.light_list:
                    if not item.illuminate:
                        write('Illuminate "'+item.lightname+'"')
                        write(' 0\n')
                
            objtransform(obj)
            rmansettings = scene.renderman_settings

            if mat: writeMaterial(mat)
            
            if obj.data.show_double_sided:
                write('Sides 2\n')
                
            write('ShadingRate '+str(obj_pass.shadingrate)+'\n')
            
            export_type = obj.data.export_type
            if export_type == 'ObjectInstance':
                write('ObjectInstance "'+obj.data.name+'"\n')
            else:
                export_object(obj, export_type)
            write("AttributeEnd\n\n")
            obj_archive.close()
        


#############################################
#                                           #
#   Mesh data (own RIB file)                #
#                                           #
#############################################


def writeMesh(mesh):
    subsurf = False
    ptype = mesh.data.primitive_type
    subsurf = ptype == 'subdivisionmesh'
    smoothshade = False
    
    mesh_archive = get_archive(path = mesh, type = "MESH", parent_type = "Object")
    scene = mesh_archive.scene
    print("This Polygon Object is a", ptype)
    mwrite = mesh_archive.file.write
#        mwrite("AttributeBegin\n")

#    for face in mesh.data.faces:        #ugly hack!! (rather use subD Mesh and ignore smoothing)
#        if face.use_smooth:
#            smoothshade = True
#    if smoothshade:
#        mwrite('ShadingInterpolation "smooth"\n')
#    else:
#        mwrite('ShadingInterpolation "constant"\n')
    
        #check for SubSurf


    #Apply Modifiers
    export_mesh = mesh.create_mesh(scene, True, 'RENDER')
    print("apllied modifiers:", export_mesh)
    
    
    if subsurf:
        mwrite('SubdivisionMesh "catmull-clark" ')
    elif ptype == 'pointspolygons':
        mwrite("PointsPolygons ")
    elif ptype == 'points':
        mwrite('Points\n')        
    vindices = []
    if ptype in ['subdivisionmesh', 'pointspolygons']:
        #write Polygon Vertex Count
        mwrite("[")
        for face in export_mesh.faces:
            mwrite(str(len(face.vertices))+" ")
        mwrite("]")
    
        #write Polygon Vertex Index
        mwrite(" [")
        for face in export_mesh.faces:
            for v in face.vertices:
                mwrite(str(v.real)+" ")
                vindices.append(v.real)
        mwrite("]\n")
    
        if subsurf:
            mwrite('["interpolateboundary"] [0 0] [] []\n')

        
    #write Normals
    mwrite('"N" [')
    for vindex, n in enumerate(export_mesh.vertices):
        if vindex in vindices or ptype == 'points':
            mwrite(str(n.normal[0])+' '+str(n.normal[1])+' '+str(n.normal[2])+' ')
    mwrite(']\n')
    
    #write Vertex Coordinates
    mwrite('"P" [')
    for vindex, v in enumerate(export_mesh.vertices):
        if vindex in vindices or ptype == 'points': #make shure vertex is in a polygon, as otherwise renderman cries
            mwrite(str(v.co.x)+' '+str(v.co.y)+' '+str(v.co.z)+' ')                
    mwrite("]\n")

    p_scale = mesh.data.points_scale
    
    if ptype == "points" and mesh.data.size_vgroup != "":
        mwrite('"width" [')
        for vert in mesh.data.vertices:
            i = mesh.vertex_groups[mesh.data.size_vgroup].index
            size_value = vert.groups[i].weight
            mwrite(str(size_value*p_scale)+' ')
        mwrite(']')
    else:
        mwrite('"constantwidth" ['+str(p_scale)+']\n')       
    
    #write UV coordinates        
    uv = False
    for uvlayer, uv_texture in enumerate(export_mesh.uv_textures):
        if uvlayer == 0:
            s = "s"
            t = "t"
        else:
            s = "s"+str(uvlayer)
            t = "t"+str(uvlayer)
        if scene.renderman_settings.facevertex:
            mwrite('"facevertex float[2] '+s+t+'" [')
        else:
            mwrite('"facevarying float[2] '+s+t+'" [')
        for face in uv_texture.data:
            for co in face.uv:
                mwrite(" "+str(co[0])+" "+str(1-co[1])+" ")
        mwrite("]\n")
#        mwrite("AttributeEnd")
    mesh_archive.close()
    bpy.data.meshes.remove(export_mesh)

#############################################
#                                           #
#   gather data and                         #
#   execute all export functions            #
#                                           #
#############################################

def export_object(obj, type = "ReadArchive"):
    global current_pass, active_archive
    write = active_archive.file.write
    
    if type == 'ObjectInstance':
        inst = True
    else:
        inst = False
        
    if inst:
        global exported_instances
        if obj.data.name in exported_instances: return 0
        exported_instances.append(obj.data.name)
        write('ObjectBegin "'+obj.data.name+'"\n')

    obj_pass =linked_pass(obj, current_pass)
    if obj_pass.transformation_blur and current_pass.motion_blur:
        motionblur(obj_pass,
                   writeMesh,
                   obj)
    else:
        writeMesh(obj)
        
    if inst: write('ObjectEnd\n')
        
#########################            

            

def export(rib, rpass, scene):
    global current_pass, base_archive
    base_archive = None
    current_pass = rpass
    degrees = math.degrees
    if current_pass.environment:
        camera = scene.objects[current_pass.camera_object]
        envrots = [[180, 90, 180], [180, -90, 180], [90, -180, 180], [-90, -180, 180], [0, 0, 0], [0, 180, 0]]
        envdirections = ["_px", "_nx", "_py", "_ny", "_pz", "_nz"]
        for i, dir in enumerate(envdirections):
            global direction
            direction = dir
            name = getname( rib,
                            dir = dir)              
            camrot = envrots[i]
            filepath = os.path.join(os.path.split(rib)[0], name)
            
            base_archive = Archive(scene, current_pass = rpass, filepath = filepath)
            writerib(camera, camrot, dir = dir)
            base_archive.close()
            invoke_renderer(filepath, scene)
            
        if not current_pass.shadow:
            fov = "90"
            process_envmap(current_pass, fov, scene)
            
    else:
        if current_pass.shadow:
            camera = scene.objects[current_pass.camera_object]
        else:
            camera = scene.camera
            if camera == None:
                print("No Camera Selected")
                return
            
        rot = camera.rotation_euler
                        
        camrot = [degrees(rot[0]), degrees(rot[1]), degrees(rot[2])]    

        base_archive = Archive(scene = scene, current_pass = rpass, filepath = rib)
        writerib(camera, camrot, dir = "")
        base_archive.close()


def getfinalpath(subfolder):
    return os.path.join(getdefaultribpath(scene), subfolder)

    #Write RIB Files
def writerib(camera, camrot, dir = ""):
    global base_archive
    scene = base_archive.scene
    rm = scene.renderman_settings
    for obj in scene.objects:
        if obj.type in ['MESH']:
            if obj.data.export_type == 'ObjectInstance':
                export_object(obj, type = obj.data.export_type)

    writeSettings(camrot)
    writeWorld()

def invoke_renderer(rib):
    rndr = scene.renderman_settings.renderexec
    os.system('"'+rndr+'" "'+ rib+'"')

def process_envmap(current_pass, fov, scene):
    envdirections = ["_px", "_nx", "_py", "_ny", "_pz", "_nz"]
    envfile = current_pass.displaydrivers[0].file
    textool = scene.renderman_settings.textureexec
    envtx = bpy.data.textures[current_pass.envname].renderman
    width = envtx.width
    swidth = envtx.swidth
    twidth = envtx.twidth
    filter = envtx.filter
    stwidth = envtx.stwidth
    fov = envtx.fov
    args = ""
    for dir in envdirections:
        env = envfile.replace("[dir]", dir).replace("[frame]", framepadding(scene))
        args += ' -envcube "'+env+'"'
    args += ' "'+envfile.replace("[dir]", "").replace("[frame]", framepadding(scene))+'"'
    args +=' -fov '+str(fov)
    args += ' -filter "'+filter+'"'
    if stwidth:
        args += ' -swidth '+str(swidth)
        args += ' -twidth '+str(twidth)
    else:
        args += ' -width '+str(width)
    cmd = textool+args
    print("processing Environment Map", current_pass.name)
    print(cmd)
    os.system(cmd)
