
# Blender 2.5 or later to Renderman Exporter
# Author: Sascha Fricke

#############################################################################
#                                                                           #
#       Begin GPL Block                                                     #
#                                                                           #
#############################################################################
#                                                                           #
# This program is free software;                                            #
# you can redistribute it and/or modify it under the terms of the           #
# GNU General Public License as published by the Free Software Foundation;  #
# either version 3 of the LicensGe, or (at your option) any later version.  #
#                                                                           #
# This program is distributed in the hope that it will be useful, but       #
# WITHOUT ANY WARRANTY;                                                     #
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A     #
# PARTICULAR PURPOSE.                                                       #
# See the GNU General Public License for more details.                      #
#                                                                           #
# You should have received a copy of the GNU General Public License along   #
# with this program;                                                        #
# if not, see <http://www.gnu.org/licenses/>.                               #
#                                                                           #
#############################################################################
#                                                                           #
#       End GPL Block                                                       #
#                                                                           #
#############################################################################

#Thanks to: Campbell Barton, Eric Back, Nathan Vegdahl

#############################################################################
#                                                                           #
#       Export data functions                                               #
#                                                                           #
#############################################################################

import export_renderman
import export_renderman.rm_maintain
from export_renderman.rm_maintain import *

import bpy
from math import *

current_pass = base_archive = active_archive = None
direction = ""


def get_write():
    global active_archive
    return active_archive.file.write


def create_child(data_path, type=""):
    global active_archive
    return Archive(data_path=data_path, parent_archive=active_archive, type=type)


def close_all():
    global base_archive
    def close(ar):
        ar.close()
        for ch in ar.child_archives:
            close(ch)
    close(base_archive)


def set_parent_active():
    global active_archive
    active_archive = active_archive.parent_archive


class Archive():    # if specified open a new archive
                    # otherwise link to the parents file handle
    '''
    Class to manage structure of RIB Archives.  The main export function
    initializes the base archive with
    Archive(scene = scene, current_pass = ..., filepath),
    where filepath is the path specified in the export() function and
    stores this Archive Object in the global variable base_archive.
    On creation the archive object is also automatically stored in a global var
    called active_archive.
    All the other functions just call create_child(data_path) and get the
    correct Archive Object except functions that are executed on several
    archives, e.g. writeparms() just need to call get_write()
    that will return the active archive.  If one wants to export a single
    object call Archive(obj, scene = scene, current_pass = rpass) directly.
    If one function's archive mustn't get children it can at the end call
    set_parent_active() which will make the parent of the active archive the new
    active archive.
    '''

    data_path = None    # path to datablock
    parent_archive = None   # store its parent
    filepath = ""
    scene = None
    frame = None
    rs = None   # path to rib_structure properties
    def __init__(self,
                 data_path=None,
                 parent_archive=None,
                 filepath="",
                 scene=None,
                 type=""):
        self.child_archives = []
        self.type = ""
        self.file = None
        global base_archive, active_archive, direction, current_pass
        if not base_archive: 
            base_archive = self
            if not data_path:
                data_path = self.data_path = self.scene = scene
        self.type = type
        self.filepath = filepath
        self.data_path = data_path
        self.parent_archive = parent_archive

        active_archive = self
        name = ""
        parent_name = ""
        parent_type =""
        try:
            name = self.data_path.name
            parent_name = self.parent_archive.data_path.name
            parent_type = self.parent_archive.type
        except:
            pass
        dbprint("active archive is", self.type, name, "parent:", parent_type, parent_name, lvl=2, grp="archive")

            
        if scene == None:
            scene = self.scene = base_archive.scene
        else:
            self.scene = scene
        self.frame = scene.frame_current 
        
        rm = scene.renderman_settings
        
        rs_base = rm.rib_structure
        
        types = {'Object': rs_base.objects,
                 'Material': rs_base.materials,
                 'MESH': rs_base.meshes,
                 'LAMP': rs_base.lights,
                 'Pass': rs_base.render_pass,
                 'Settings': rs_base.settings,
                 'World': rs_base.world,
                 'Particle System': rs_base.particles,
                 'Particle Data': rs_base.particle_data,
                 'Frame' : rs_base.frame}
           
        base_path = getdefaultribpath(scene)
        if type == "":
            type = self.type = data_path.rna_type.name
            
        self.rs = rs = types[type]
        path = os.path.join(base_path, rs.folder)
        pname =""
        if type in ["Particle System", "Particle Data"]:
            prop_path = data_path.settings
        elif type == "LAMP" and data_path.data.rna_type.name == 'LAMP':
            prop_path = data_path.data
        else:
            prop_path = data_path
        
        if self.type in ['Pass', 'Settings', 'World']:
            pname = current_pass.name
        elif self.type in ['MESH', 'Frame']:
            pname = ''
        elif filepath == "":
            dbprint("trying to get linked pass for this object", lvl=2, grp="archive")
            pname = linked_pass(prop_path, current_pass).name
            dbprint("linked pass is", pname, lvl=2, grp="archive")
        try:
            objname = data_path.name
        except AttributeError:
            objname = ""
        name = getname(rs.filename,
                       name=objname,
                       pass_name=pname,
                       frame=framepadding(scene),
                       scene=scene) + '.rib'
        filepath = os.path.join(path, name)
            
        filepath = filepath.replace('[dir]', direction)
        
        if rs.own_file:
            self.filepath = filepath
            if not os.path.exists(path):
                os.mkdir(path)
            if parent_archive != None:
                if (type == "MESH"
                    and prop_path.export_type == 'DelayedReadArchive'):
                    parent_archive.file.write('DelayedReadArchive "'
                                              + filepath.replace('\\', '\\\\')
                                              + '" [')
                    for bound in obj.bound_box:
                        parent_archive.file.write([" ".join(str(b))
                                                   for b in bound])
                        parent_archive.file.write(" ")
                    parent_archive.file.write(']\n') 
                parent_archive.file.write('ReadArchive "'
                                          + filepath.replace('\\', '\\\\')
                                          + '"\n')
            if self.rs.overwrite or not os.path.exists(filepath):
                self.file = open(filepath, "w")
        else:
            if parent_archive != None:
                self.file = parent_archive.file
        if parent_archive != None:
            parent_archive.child_archives.append(self)
        
    def close(self):
        global base_archive
        if self == base_archive: 
            # if it's the base archive reset the global var back to None
            # because exporting finished
            base_archive = None
        if self.parent_archive and not self.parent_archive.file == self.file:   
            self.file.close()
        elif not self.parent_archive:     
            self.file.close()


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
            writeparms(grp[attr_opt])                                       

def write_custom_code(code, type_, position):
    global base_archive
    global direction
    rpass = base_archive.current_pass
    if rpass.environment:
        env = True
    else:
        env = False
    if code:
        for c in code:
            if type_ == "world":
                cpos = c.world_position
            else:
                cpos = c.position
            if c.world_position == position:
                if c.foreach or direction == "nz":
                    write_single_parm(code.parameter)
                
def write_single_parm(parm):
    global base_archive, current_pass
    scene = base_archive.scene
    write = get_write()
    write('\n\t\t')
    name = parm.name
    if name.find('[') != -1:
        name = name[:name.find('[')]
    if parm.export:
        if parm.parametertype == 'string':
            if parm.input_type == "texture":
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

def writeparms(path):
    global base_archive
    scene = base_archive.scene
    write = get_write()
    for parm in path:
        write_single_parm(parm)
    write('\n')

def writeshaderparameter(parameterlist):
    global current_pass, base_archive
    scene = base_archive.scene
    write = get_write()
    for i, parm in enumerate(parameterlist):
        write('\n\t"'+parm.type+' '+parm.name+'"')
        if parm.parametertype == 'string':
            if parm.input_type == "texture":
                tx = ""
                if parm.textparameter in bpy.data.textures:
                    texture = bpy.data.textures[parm.textparameter]
                    if texture.renderman.type == "file":
                        image = texture.image
                        if image.source == 'GENERATED':
                            image.filepath = os.path.join(getdefaultribpath(scene), image.name)
                            image.save()
                        tx = image_processing(texture.renderman.processing, image.filepath, tex=True)
                    elif texture.renderman.type == "bake":
                        tx = os.path.join(getdefaultribpath(scene), texture.name+framepadding(scene)+".bake").replace('\\', '\\\\')
                write(' ["'+tx+'"] ')
                        
            else:
                string = parm.textparameter.replace('[frame]', framepadding(scene))
                string = string.replace('[dir]', '')
                write(' ["' + string + '"] ')
        elif parm.parametertype == 'float' and parm.vector_size == 1:
            write(" [" + str(parm.float_one[0]) + '] ')
        elif parm.parametertype == 'color':
            colR = parm.colorparameter[0]
            colG = parm.colorparameter[1]
            colB = parm.colorparameter[2]
            write(" [" + str(colR) + " " + str(colG) + " " + str(colB) + "] ")
        elif parm.parametertype == 'float' and parm.vector_size == 3:
            x = str(parm.float_three[0])
            y = str(parm.float_three[1])
            z = str(parm.float_three[2])
            write(" [" + x + " " + y + " " + z + "] ")

def prepared_texture_file(file):
    global current_pass, base_archive
    scene = base_archive.scene
    return os.path.splitext(file)[0]+"."+scene.renderman_settings.textureext
    
def image_processing(pr, input, scene=None, env=-1, tex=False):
    envdirections = ["px", "nx", "py", "ny", "pz", "nz"]
    global base_archive
    if pr.process:
        if base_archive != None:
            scene = base_archive.scene
        rm = scene.renderman_settings
        tx = rm.textureext
        txdir = os.path.join(getdefaultribpath(scene), rm.texdir)
        output = getname(input,
                         frame=framepadding(scene),
                         scene=scene)
        if tex:
            output = os.path.join(txdir, os.path.split(output)[1])
            if not os.path.exists(txdir): os.mkdir(txdir)
        parmsarray = []
        if pr.shadow:
            shadow = "-shadow"
            parmsarray.append(shadow)
            ext = 'shd'
        else:
            if pr.envcube and env == 5:
                envcube = "-envcube"
                parmsarray.append(envcube)
            ext = tx
        
            if pr.filter == "other":
                filter = "-filter "+pr.custom_filter
            else:
                filter = "-filter "+pr.filter
            parmsarray.append(filter)
            if pr.stwidth:
                width = "-sfilterwidth " + str(pr.swidth)
                width += "-tfilterwidth " + str(pr.twidth)
            else:
                width = "-filterwidth " + str(pr.width)
            parmsarray.append(width)
            parmsarray.append(pr.custom_parameter)
        
        inp = '"'+input.replace('[frame]', framepadding(scene))+'"'
        if env == 5:
            inputs = []
            for dir in envdirections:
                inputs.append(inp.replace('[dir]', dir))
            inp = ' '.join(inputs)
        output = output.replace(checkextension(output), ext)
        output = output.replace('[dir]', '')
        parmsarray.append(inp)
        parmsarray.append('"'+output+'"')
        
        parms = " ".join(parmsarray)
        
        textool = scene.renderman_settings.textureexec
        command = textool+ ' ' +parms
        dbprint(command, lvl=2, grp="textures")
        if not os.path.exists(output):
            os.system(command)
        return output

def get_mb_sampletime(samples, shutterspeed):
    global current_pass
    sampletime = [0]
    for i in range(2, samples+1):
        addtosample = (shutterspeed/samples)*i
        sampletime.append(addtosample)
    return sampletime

def mb_setframe(t):
    global base_archive, current_pass
    scene = base_archive.scene
    fps = scene.render.fps
    speed = current_pass.shutterspeed_sec * fps
    start_frame = base_archive.frame
    frame = modf(start_frame - (speed - t))
    scene.frame_set(frame[1], frame[0])

def motionblur( path,
                function,
                *args,
                frameset=True,
                **keys):
                    
    global current_pass, active_archive
    dbprint("writing motion blur", "active archive is", active_archive.data_path, lvl=2, grp="mb")
    write = get_write()
    scene = active_archive.scene
    fps = scene.render.fps
    motion_samples = path.motion_samples
    shutterspeed = current_pass.shutterspeed_sec * fps
    
    sampletime = get_mb_sampletime(motion_samples, shutterspeed)
        
    write('MotionBegin[')
    write(' '.join([str(s) for s in sampletime]))
    write(']\n')
    for s in sampletime:
        if frameset:
            mb_setframe(s)
        function(*args, **keys)
    write('MotionEnd\n')

#############################################
#                                           #
#   Write Render Settings                   #
#   (the stuff before World Block begins)   #
#                                           #
#############################################
                    
def writeSettings(camrot):
    global base_archive, direction, current_pass
    dir = direction
    scene = base_archive.scene
    
    settings_archive = create_child(current_pass,
                                    type="Settings")
    write = settings_archive.file.write
    dbprint("write Scene Settings ...", lvl=1, grp="Settings")

    if not current_pass.displaydrivers:
        nodisplay = True
    else:
        nodisplay = False
				
    if current_pass.name == "Beauty" and not current_pass.displaydrivers:
        adddisp(current_pass)
    render = scene.render
   
    camera = scene.objects[current_pass.camera_object]
    rc = current_pass.renderman_camera

    nearclipping = rc.near_clipping
    farclipping = rc.far_clipping
    shift_x = rc.shift_x * 2
    shift_y = rc.shift_y * 2
    
    resx = int(rc.resx * rc.respercentage)*0.01
    resy = int(rc.resy * rc.respercentage)*0.01

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

    if rc.depthoffield:
        dof_distance = rc.dof_distance
        if rc.use_lens_length:
            focal_length = scene.camera.data.lens/100 # TODO: store lens data in rc
        else:
            focal_length = rc.focal_length
        fstop = rc.fstop


## Declare AOVs
    default_vars = ["rgb", "rgba", "a", "z", "N", 
                        "P", "Ci", "Cs", "Oi", "Os", 
                        "s", "t", "u", "v", "Ng", 
                        "E", "du", "dv", "dPtime", "dPdu", 
                        "dPdv"]
    for var in scene.renderman_settings.var_collection:
        if not var.name in default_vars:
            write('Declare "'+var.name+'" "'+var.type_+'"\n')


### Display driver
    for dispcount, display in enumerate(current_pass.displaydrivers):
        if not display.export:
            write('#')
        quant_min = str(display.quantize_min)
        quant_black = str(display.quantize_black)
        quant_max = str(display.quantize_max)
        quant_white = str(display.quantize_white)
        gamma = str(float(int(display.gamma*100)/100))
        gain = str(float(int(display.gain*100)/100))
        file = display.file.replace("[frame]",framepadding(scene))
        dbprint(dir, lvl=1, grp="env")
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
    dbprint(current_pass.camera_object, lvl=2, grp="Settings")
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

    dbprint("Done", lvl=1, grp="Settings")
    
### Camera
    if current_pass.displaydrivers:
        writeCamera(camera, camrot)
    set_parent_active()
      


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

def writetransform(obj, mx = None):
    if mx: matrix = mx
    else: matrix = obj.matrix_world
    write = get_write()
    write('ConcatTransform [\t')    
    for i, row in enumerate(matrix):
        for val in row:
            write(" " + str(val))
        if not i == len(matrix)-1: write('\n\t\t\t\t\t')
    write(']\n')

def objtransform(obj, mx = None):
    global base_archive, current_pass
    
    ## transformation blur    
    sampletime = []
    
    objpass = linked_pass(obj, current_pass)
    if objpass and objpass.transformation_blur and current_pass.motionblur:
        motionblur( objpass,
                    writetransform,
                    obj,
                    mx)
    else: writetransform(obj)


def writeCamera(cam, camrot):
    degrees = math.degrees
    global current_pass, direction, base_archive
    dir = direction
    scene = base_archive.scene
    write = get_write()
    print("write Camera Settings ...")
    
    def writeCameraTransform(trans):
        matrix = cam.matrix_world
        ribx = str(matrix[3][0]*-1)
        riby = str(matrix[3][1]*-1)
        ribz = str(matrix[3][2]*-1)
        if current_pass.environment:
            rotx, roty, rotz = camrot
        else:
            rotx = degrees(cam.rotation_euler[0])
            roty = degrees(cam.rotation_euler[1])
            rotz = degrees(cam.rotation_euler[2])
            
        transform = {   "RotX" : "Rotate "+str(rotx*-1)+" 1 0 0\n",
                        "RotY" : "Rotate "+str(roty*-1)+" 0 1 0\n",
                        "RotZ" : "Rotate "+str(rotz*-1)+" 0 0 1\n",
                        "Translate" : "Translate "+ribx+" "+riby+" "+ribz+"\n" }
        write(transform[trans])
        
    def writePerspective(fov, perspective):
        if perspective:
            typestring = '"perspective" "fov" ['+fov+']\n'
    
        elif not perspective:
            typestring = '"orthographic"\n'

        write('Projection '+typestring)

    if current_pass.motionblur:
        shutterspeed = current_pass.shutterspeed_sec * scene.render.fps
        write('Shutter 0 '+str(shutterspeed)+'\n')

    def checkoutFOVnPersp():
        perspective = True
        fov = ""
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
            fov = str(current_pass.renderman_camera.fov)
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

    ts = current_pass.renderman_camera.transformation_blur
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
    
    world_archive = create_child(current_pass, type = "World")
    write = world_archive.file.write
    global_shader = current_pass.global_shader

    write("WorldBegin\n")
    if current_pass.override_shadingrate:
        write("ShadingRate "+str(current_pass.shadingrate)+"\n")
    write_attrs_or_opts(current_pass.attribute_groups, "Attribute", "")
    write('\n\n')
    ### Custom Code
    
    wc = current_pass.world_code
    if wc:
        for code in current_pass.world_code:
            if code.world_position == "begin":
                
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
            if (not obj.hide_render
                and not obj.name == current_pass.camera_object
                and check_visible(obj, scene)):
                writeObject(obj)
                writeParticles(obj)                 
    write("WorldEnd\n")


#############################################
#                                           #
#   Lights                                  #
#                                           #
#############################################


def writeLight(light, scene = None):
    global base_archive, current_pass
    if scene == None:
        scene = base_archive.scene
    rmansettings = scene.renderman_settings
    al = False
    if light.type != 'LAMP' and light.active_material:
        mat = light.active_material
        try:
            alshader = linked_pass(mat, current_pass).arealight_shader
        except:
            print(mat, current_pass)
            raise
        if alshader != "":
            al = True
            print("yo")
            
    if (light.type == 'LAMP' or al) and not light.hide_render:
        if check_visible(light, scene):
            light_archive = create_child(light,
                                        type = "LAMP")
            write = light_archive.file.write
            
            print("write "+light.name)
            rotx = str(math.degrees(light.rotation_euler.x))
            roty = str(math.degrees(light.rotation_euler.y))
            rotz = str(math.degrees(light.rotation_euler.z))          
    
            write("\nAttributeBegin\n")      
            objtransform(light)
            if al:
                write_attrs_or_opts(linked_pass(light, current_pass).attribute_groups, "Attribute", "")
                write('AreaLightSource ')
                parameterlist = linked_pass(mat, current_pass).light_shader_parameter
                write('"'+alshader.replace("."+rmansettings.shaderbinary, "")+'" "'+light.name+'" ')
                writeshaderparameter(parameterlist)
                write('\n')
                export_type = light.data.export_type
                
                if light.data.show_double_sided:
                    write('Sides 2\n')
                    
                if mat: writeMaterial(mat)
                
                if export_type == 'ObjectInstance':
                    write('ObjectInstance "'+light.data.name+'"\n')
                else:
                    export_object(light, export_type)
            else:
                write_attrs_or_opts(linked_pass(light.data, current_pass).attribute_groups, "Attribute", "")
                write('LightSource ')
                parameterlist = linked_pass(light.data, current_pass).light_shader_parameter
                write('"'+linked_pass(light.data, current_pass).shaderpath.replace("."+rmansettings.shaderbinary, "")+'" "'+light.name+'" ')         
                writeshaderparameter(parameterlist)
                write('\n')

            write('AttributeEnd\n')
            print("Done")
            
            set_parent_active()


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

def writeMaterial(mat, mat_archive=None, active_matpass=False):
    global active_archive
    scene = active_archive.scene
    p = active_archive
    if mat_archive == None:
        mat_archive = Archive(data_path=mat, parent_archive=p)
    write = mat_archive.file.write
    rmansettings = scene.renderman_settings
    if active_matpass:
        mat_pass=mat.renderman[mat.renderman_index]
    else:
        mat_pass = linked_pass(mat, current_pass)
    
    if mat_pass:
        if mat_pass.matte:
            write('Matte 1\n')
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
            matblur(writeshader, displacement_shader, displacement_parameter, "Displacement")
            matblur(writeshader, surface_shader, surface_parameter, "Surface")
            matblur(writeshader, interior_shader, interior_parameter, "Interior")
            matblur(writeshader, exterior_shader, exterior_parameter, "Exterior")
        else:
            writeshader(displacement_shader, displacement_parameter, "Displacement")
            writeshader(surface_shader, surface_parameter, "Surface")
            writeshader(interior_shader, interior_parameter, "Interior")
            writeshader(exterior_shader, exterior_parameter, "Exterior")
    set_parent_active()


#############################################
#                                           #
#   Particles                               #
#                                           #
#############################################
matrices = []

def writeParticles(obj):
    global base_archive, current_pass
    scene = base_archive.scene
    rmansettings = scene.renderman_settings
    pfiles = []

    if len(obj.particle_systems) > 0:
        for psystem in obj.particle_systems:
            if psystem.settings.type == 'EMITTER':
                rman = linked_pass(psystem.settings, current_pass)
                particle_archive = create_child(psystem)
                write = particle_archive.file.write
                write("\nAttributeBegin ##Particle System\n")
                write('Attribute "identifier" "name" ["'+obj.name+'_'+psystem.name+'"]\n')
                try:
                    mat = obj.material_slots[rman.material_slot]
                except IndexError:
                    mat = None
                if mat: writeMaterial(mat)
                write_attrs_or_opts(linked_pass(obj, current_pass).attribute_groups, "Attribute", "")
                
                if current_pass.motionblur and rman.motion_blur:
                    locations, sizes = mb_gather_point_locations(psystem)
                    shutterspeed = current_pass.shutterspeed_sec * scene.render.fps
                    sampletime = get_mb_sampletime(rman.motion_samples, shutterspeed)
                    write('MotionBegin[')
                    write(' '.join([str(s) for s in sampletime]))
                    write(']\n')
                    for i, s in enumerate(sampletime):
                        mb_setframe(s)
                        writeParticle_data(psystem, locs = locations, sizes = sizes, sample = i)
                    write('MotionEnd\n')
                else:
                    writeParticle_data(psystem)
                write('AttributeEnd\n')
                
def mb_gather_point_locations(psystem):
    locations = []
    sizes = []
    global active_archive
    current_pass = active_archive.current_pass
    scene = active_archive.scene
    rman = linked_pass(psystem.settings, current_pass)
    shutterspeed = current_pass.shutterspeed_sec * scene.render.fps
    sampletime = get_mb_sampletime(rman.motion_samples, shutterspeed)
    
    ## gather locations and size for each motion sample
    for s in sampletime:
        loc_sample = []
        siz_sample = []
        mb_setframe(s)
        for part in psystem.particles:
            if part.alive_state == 'ALIVE':
                locx = str(part.location.x)
                locy = str(part.location.y)
                locz = str(part.location.z)
                loc_sample.append([locx, locy, locz])
        locations.append(loc_sample)
        
        for i, part in enumerate(psystem.particles):
            if part.alive_state == 'ALIVE':
                size = str(part.size)
                siz_sample.append(size)
        sizes.append(siz_sample)
    print("locations", len(locations), "sizes", len(sizes))
    return locations, sizes

def writeParticle_data(psystem, locs = [], sizes = [], sample = -1):
    global active_archive
    scene = active_archive.scene
    current_pass = active_archive.current_pass
    pdata_archive = Archive(psystem, type = "Particle Data", parent_archive = active_archive)
    write = pdata_archive.file.write
    rman = linked_pass(psystem.settings, current_pass)
    if rman:
        ## Points
        if rman.render_type == "Points":
            write('Points\n')
            write = get_write()
            write('"P" [')
            if locs != []:
                enum = locs[len(locs)-1]
            else:
                enum = psystem.particles
            for i, part in enumerate(enum):    
                if enum != psystem.particles:
                    if locs != [] and i < len(locs[sample]):
                        write(' '.join(locs[sample][i])+'\n')
                    else:
                        write(' '.join(locs[len(locs)-1][i])+'\n')
                elif part.alive_state == 'ALIVE':
                    locx = str(part.location.x)
                    locy = str(part.location.y)
                    locz = str(part.location.z)
                                       
                    write(locx+' '+locy+' '+locz+'\n')
            write(']\n')
            
            write('"width" [')
            if sizes != []:
                enum = sizes[len(sizes)-1]
            else:
                enum = psystem.particles
            for i, part in enumerate(enum):
                if enum != psystem.particles:
                    if sizes != [] and i < len(sizes[sample]):
                        try:
                            write(sizes[sample][i]+'\n')
                        except:
                            print("size", len(sizes), len(sizes[sample]), "locations", len(locs), len(locs[sample]))
                            raise
                    else:
                        write(sizes[len(sizes)-1][i]+'\n')
                elif part.alive_state == 'ALIVE':
                    size = str(part.size)
                    write(size+'\n')
            write(']\n')
            
        ## Objects
        elif rman.render_type == "Object":
            part_obj = scene.objects[rman.object]
            
            
        #def transform(part):          
        #        mx_new = mathutils.Matrix()
        #        trans = part.location
        #        mx_trans = mx_new.Translation(trans)
        #        mx_rot = part.rotation.to_matrix().to_4x4()
        #        mx_scale = mx_new.Scale(part.size, 4)
        #        mx = mx_trans * mx_scale * mx_rot
        #        return mx
        #
        #def mb_trans_particles(matrices, i):
        #    for m in matrices:
        #        objtransform(None, mx = matrices.pop(0)[i])
        #
        #matrices = []
        #mx_set = []
        #for i, part in enumerate(psystem.particles):
        #    mx_set.append(transform(part))
        #matrices.append(mx_set)                   
        #
        #for i, part in enumerate(psystem.particles):
        #    if scene.frame_current >= part.birth_time:
        #        write('AttributeBegin\n')
        #        
        #        if rman.motion_blur and current_pass.motionblur:
        #            motionblur( rman,
        #                        mb_trans_particles,
        #                        matrices,
        #                        i,
        #                        frameset = 0)
        #        else:
        #            mb_trans_particles
        #                                    
        #        writeObject(part_obj) 
            
        #        write('AttributeEnd\n')
    set_parent_active()
                                

#############################################
#                                           #
#   Objects                                 #
#                                           #
#############################################
    
def writeObject(obj):
    global base_archive, current_pass
    scene = base_archive.scene

    if obj.type in ['MESH']:
        al = False
        m = obj.active_material
        if m:
            if linked_pass(m, current_pass).arealight_shader != "":
                al = True
        obj_pass = linked_pass(obj, current_pass)
        if obj_pass and not al:               
            obj_archive = create_child(obj)
            write = obj_archive.file.write
            mat = obj.active_material            
            
            write("##"+obj.name+'\n')
            if obj.parent:
                write('#child of '+obj.parent.name+'\n')
            write("AttributeBegin\n")
            write('Attribute "identifier" "name" ["'+obj.name+'"]\n')
            write_attrs_or_opts(obj_pass.attribute_groups, "Attribute", "")
                
            objtransform(obj)
            rmansettings = scene.renderman_settings

            if mat: writeMaterial(mat)
            
            if obj.data.show_double_sided:
                write('Sides 2\n')
                
            if not current_pass.override_shadingrate:
                write('ShadingRate '+str(obj_pass.shadingrate)+'\n')
            
            export_type = obj.data.export_type
            if export_type == 'ObjectInstance':
                write('ObjectInstance "'+obj.data.name+'"\n')
            else:
                export_object(obj, export_type)
            write("AttributeEnd\n\n")
            set_parent_active()
        


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
    global active_archive
    mesh_archive = create_child(mesh.data, type = "MESH")
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
        if vindex in vindices or ptype != 'points' and mesh.data.export_normals:
            mwrite(str(n.normal[0])+' '+str(n.normal[1])+' '+str(n.normal[2])+' ')
    mwrite(']\n')
    
    #write Vertex Coordinates
    mwrite('"P" [')
    for vindex, v in enumerate(export_mesh.vertices):
        if vindex in vindices or ptype == 'points': #make sure vertex is in a polygon, as otherwise renderman cries
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
    elif ptype == "points":
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
    bpy.data.meshes.remove(export_mesh)
    set_parent_active()

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
    if obj_pass.deformation_blur and current_pass.motionblur:
        motionblur(obj_pass,
                   writeMesh,
                   obj)
    else:
        writeMesh(obj)
        
    if inst: write('ObjectEnd\n')
        
#########################            

            

def export(rpass, scene):
    global current_pass, direction, base_archive
    current_pass = rpass
    degrees = math.degrees
    rs = scene.renderman_settings.rib_structure.render_pass
    path = getdefaultribpath(scene)
    path = os.path.join(path, rs.folder)
    if current_pass.environment:
        camera = scene.objects[current_pass.camera_object]
        envrots = [ [180, 90, 180],
                    [180, -90, 180],
                    [90, -180, 180],
                    [-90, -180, 180],
                    [0, 0, 0],
                    [0, 180, 0]]
        envdirections = ["px", "nx", "py", "ny", "pz", "nz"]
        for i, dir in enumerate(envdirections):
            direction = dir            
            camrot = envrots[i]
            
            pass_archive = create_child(scene, type="Pass")
            writerib(camera, camrot, dir = dir)
            close_all()
            invoke_renderer(filepath.replace('[dir]', dir), scene)
            
            check_disps_processing(rpass, scene, env=i)
        direction = ""
        
    else:
        camera = scene.objects[current_pass.camera_object]
        rot = camera.rotation_euler
                        
        camrot = [degrees(rot[0]), degrees(rot[1]), degrees(rot[2])]    

        pass_archive = create_child(scene, type="Pass")
        writerib(camera, camrot, dir = "")

def check_disps_processing(current_pass, scene, env=-1):
    for disp in current_pass.displaydrivers:
        filepath = disp.file
        pr = disp.processing
        image_processing(pr, filepath, scene=scene, env=env)

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

def invoke_renderer(rib, scene):
    rndr = scene.renderman_settings.renderexec
    os.system('"'+rndr+'" "'+ rib+'"')
    