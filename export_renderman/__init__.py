
#Blender 2.5 or later to Renderman Exporter
# Copyright (C) 2011 Sascha Fricke



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


bl_info = {
    'name': 'Renderman',
    'author': 'Sascha Fricke',
    'version': '0.01',
    'blender': (2, 5, 6),
    'location': 'Info Header',
    'description': 'Connects Blender to Renderman Interface',
    'category': 'Render'}
    
##################################################################################################################################
if "bpy" in locals():
    reload(rm_props)
    reload(ops)
    reload(maintain)
    reload(ui)
    reload(export)
else:
    from export_renderman import rm_props
    from export_renderman import ops
    from export_renderman.ops import *
    from export_renderman import rm_maintain
    from export_renderman.rm_maintain import *
    from export_renderman import ui
    from export_renderman import export
    from export_renderman.export import *

import bpy
import os
import subprocess
import math
import mathutils
import tempfile
import time

import threading

##################################################################################################################################

from bl_ui import properties_data_mesh
from bl_ui import properties_data_camera
from bl_ui import properties_data_lamp
from bl_ui import properties_texture
from bl_ui import properties_particle
from bl_ui import properties_render

#properties_render.RENDER_PT_render.COMPAT_ENGINES.add('RENDERMAN')
properties_render.RENDER_PT_dimensions.COMPAT_ENGINES.add('RENDERMAN')
#properties_render.RENDER_PT_output.COMPAT_ENGINES.add('RENDERMAN')
#properties_render.RENDER_PT_post_processing.COMPAT_ENGINES.add('RENDERMAN')
properties_data_mesh.DATA_PT_context_mesh.COMPAT_ENGINES.add('RENDERMAN')
properties_data_mesh.DATA_PT_settings.COMPAT_ENGINES.add('RENDERMAN')
properties_data_mesh.DATA_PT_vertex_groups.COMPAT_ENGINES.add('RENDERMAN')
properties_data_mesh.DATA_PT_shape_keys.COMPAT_ENGINES.add('RENDERMAN')
properties_data_mesh.DATA_PT_uv_texture.COMPAT_ENGINES.add('RENDERMAN')
properties_data_camera.DATA_PT_context_camera.COMPAT_ENGINES.add('RENDERMAN')
properties_data_camera.DATA_PT_camera_display.COMPAT_ENGINES.add('RENDERMAN')
properties_data_lamp.DATA_PT_context_lamp.COMPAT_ENGINES.add('RENDERMAN')

for member in dir(properties_texture):
    subclass = getattr(properties_texture, member)
    exceptions = [  "", "Colors", "Influence", "Mapping", 
                    "Image Sampling", "Image Mapping", 
                    "Environment Map Sampling", "Custom Properties",
                    "Preview", "Environment Map"]
    try:
        if not subclass.bl_label in exceptions:
            subclass.COMPAT_ENGINES.add('RENDERMAN')
    except:
        pass

for member in dir(properties_particle):
    subclass = getattr(properties_particle, member)
    exceptions = ['Render', 'Children']
    try:
        if not subclass.bl_label in exceptions:
            subclass.COMPAT_ENGINES.add('RENDERMAN')
    except:
        pass
            
del properties_texture
del properties_data_mesh
del properties_data_camera
del properties_data_lamp

##################################################################################################################################
#checking folders and creating them if necessary

def checkpaths(folderpath):
    if os.path.exists(folderpath):
        fullofcrap = True
        dir = folderpath
        while fullofcrap:
            if not os.path.exists(dir):
                fullofcrap = False
                break
            if os.listdir(dir):
                for item in os.listdir(dir):
                    if os.path.isfile(os.path.join(dir, item)):
                        os.remove(os.path.join(dir, item))
                    elif os.path.isdir(os.path.join(dir, item)):
                        dir = os.path.join(folderpath, item)
            else:
                os.rmdir(dir)
                dir = folderpath
    os.mkdir(folderpath)


##################################################################################################################################
##################################################################################################################################

##################################################################################################################################

##################################################################################################################################


#########################################################################################################
#                                                                                                       #
#       R E N D E R                                                                                     #
#                                                                                                       #
#########################################################################################################
preview_scene = False

def checksize(img):
    size = -1

    ready = False
    while not ready:
        if size != os.path.getsize(img):
            size = os.path.getsize(img)
        else:
            ready = True
            break

        time.sleep(1)
    return 0

def rm_shellscript(cmd, rm):
    if rm.shellscript_create:
        ssfile = rm.shellscript_file
    if not rm.shellscript_append or not os.path.exists(ssfile):
        file = open(ssfile, "w")
    elif rm.shellscript_append and os.path.exists(ssfile):
        file = open(ssfile, "a")
    file.write(cmd+'\n')
    file.close()

class Renderman_OT_Render(bpy.types.Operator):
    bl_label = "Render"
    bl_idname = "renderman.render"
    bl_description = "Export/Render Scene using Renderman"
    
    anim = bpy.props.BoolProperty(default = False)
    
    def invoke(self, context, event):
        scene = context.scene
        path = getdefaultribpath(scene)        
        checkpaths(path)
        checkpaths(os.path.join(path, scene.renderman_settings.texdir))
        if self.anim:
            for i in range(context.frame_start, scene.frame_end+scene.frame_step, scene.frame_step):
                scene.frame_set(i)
                render(scene)
        else:
            render(scene)
        return{'FINISHED'}   

def image(name, scene): return name.replace("[frame]", framepadding(scene))

def start_render(render, ribfile, current_pass, scene):
    r = scene.render
    x = int(r.resolution_x * r.resolution_percentage * 0.01)
    y = int(r.resolution_y * r.resolution_percentage * 0.01)

#    if current_pass.displaydrivers and not current_pass.shadow:
#        print("Render .. "+current_pass.name)
#        print(render + ' ' + ribfile)
        
        #renderprocess = subprocess.Popen([render, ribfile])                                         
#        while not renderprocess.poll:
#            if rhandle.test_break():
#                try:
#                    renderprocess.terminate()
#                except:
#                    renderprocess.kill()
#    else:
    renderprocess = subprocess.Popen([render, ribfile])      
                 
    #wait for the file to be completely written
    for disp in current_pass.displaydrivers:
        if not disp.displaydriver == "framebuffer":
            img = image(disp.file, scene)
            while not os.path.exists(img): ###wait for the file to be created
                pass            
            checksize(img)

            
    ## until the render api is fixed, load all images manually in the image editor
    for disp in current_pass.displaydrivers:
        if not disp.displaydriver == "framebuffer" or current_pass.shadow or current_pass.environment:
            img = image(disp.file, scene)
            if not img in bpy.data.images and not disp.displaydriver == "framebuffer":
                bpy.data.images.load(img) 
       
def render(scene):
    rndr = scene.renderman_settings.renderexec
    rm = scene.renderman_settings
    rs = rm.rib_structure    
    if rndr != "":
        maintain(eval("bpy.context"))
        path = getdefaultribpath(scene)
                                             
        active_pass = getactivepass(scene)

        global exported_instances
        pname = getname(rs.frame.filename,
                        scene=scene,
                        frame=framepadding(scene))+'.rib'
        
        filepath = os.path.join(path, pname)
                
        if scene.renderman_settings.exportallpasses:
            global base_archive
            base_archive = Archive(data_path=scene, type="Frame", scene=scene, filepath=filepath)
            for item in scene.renderman_settings.passes:
                if item.export:
                    imagefolder = os.path.join(getdefaultribpath(scene), item.imagedir)
                    checkForPath(imagefolder)                                       

                    exported_instances = []

                    export(item, scene)
            close_all()
            rm = scene.renderman_settings
            if not rm.exportonly:
                if rndr != "" and not item.environment:
                    start_render(rndr, base_archive.filepath, item, scene)
                    check_disps_processing(item, scene)
            else:
                rndr_cmd = rndr + ' "'+base_archive.filepath+'"'
                rm_shellscript(rndr_cmd, rm)
                    
        else:

            exported_instances = []


            export(active_pass, scene)
            close_all()
            imagefolder = os.path.join(path, active_pass.imagedir)
            checkpaths(imagefolder)
            if not scene.renderman_settings.exportonly:
               if rndr != "":
                   start_render(rndr, base_archive.filepath, active_pass, scene)
                   check_disps_processing(active_pass, scene)
            else:
                rndr_cmd = rndr + ' "'+base_archive.filepath+'"'
                rm_shellscript(rndr_cmd, rm)
       
update_counter = 0
class RendermanRender(bpy.types.RenderEngine):
    bl_idname = 'RENDERMAN'
    bl_label = "Renderman"
    #bl_use_preview = True
    update = 50
    
    def rm_start_render(self, render, ribfile, current_pass, scene):
        rd = scene.render
        x = int(rd.resolution_x * rd.resolution_percentage)*0.01
        y = int(rd.resolution_y * rd.resolution_percentage)*0.01
        
        self.update_stats("", "Render ... "+current_pass.name)
    
        if current_pass.displaydrivers:
            print("Render .. "+current_pass.name)
            print(render + ' ' + ribfile)
            
            renderprocess = subprocess.Popen([render, ribfile])
           
            def image(name): return name.replace("[frame]", framepadding(scene))    

            def update_image(image):
                result = self.begin_result(0, 0, x, y)
              
                layer = result.layers[0]
                
                try:
                    layer.load_from_file(image)
                except:
                    print("can't load image")
                self.end_result(result)

            if (current_pass.renderresult != ""
                and current_pass.displaydrivers[current_pass.renderresult].displaydriver != "framebuffer"):
                img = image(current_pass.displaydrivers[current_pass.renderresult].file)
                
                while not os.path.exists(img):
                    if os.path.exists(img):
                        break                 
                   
                    if self.test_break():
                        try:
                            renderprocess.terminate()
                        except:
                            renderprocess.kill()
            
                    if renderprocess.poll() == 0:
                        self.update_stats("", "Error: Check Console")
                        break            
                                      
                prev_size = -1
                ready = False
               
                dbprint("all image files created, now load them", lvl=2, grp="renderprocess")
                dbprint("renderprocess finished?", renderprocess.poll(), lvl=2, grp="renderprocess")
                while True:
                    dbprint("Rendering ...", lvl=2, grp="renderprocess")
                    update_image(img)
#                            if renderprocess.poll():
#                                print("Finished")
#                                self.update_stats("", "Finished")
#                                update_image(layname, image)
#                                break
    
                    if self.test_break():
                        dbprint("aborting rendering", lvl=2, grp="renderprocess")
                        try:
                            renderprocess.terminate()
                        except:
                            renderprocess.kill()
                        break
              
                    if renderprocess.poll() == 0:
                        dbprint("renderprocess terminated", lvl=2, grp="renderprocess")
                        break
              
                    if os.path.getsize(img) != prev_size:
                        prev_size = os.path.getsize(img) 
                        update_image(img)                                                               
                            
            ## until the render api is fixed, load all images manually in the image editor
            try:
                for disp in current_pass.displaydrivers:
                    img = image(disp.file)
                    if not disp.displaydriver == "framebuffer":
                        if not img in bpy.data.images:
                            bpy.data.images.load(image(img))
                        else: bpy.data.images[img].update()
            except SystemError:
                pass

    def check_objects(self, scene):
        abort = False
        for obj in scene.objects:
            if obj.type == "LAMP" and len(obj.data.renderman) == 0:
                self.update_stats("", "Light: "+obj.name+" has no Render Pass, cancel Rendering ...")
                abort = True
            elif obj.type == "MESH" and len(obj.renderman) == 0:
                self.update_stats("", "Object: "+obj.name+"has nor Render Pass, cancel Rendering ...")
                abort = True
        return abort

    def render(self, scene):
        rm = scene.renderman_settings
        rs = rm.rib_structure
        if scene.name == "preview":
            global update_counter
            update_counter += 1
            if update_counter < self.update:
                return
            update_counter = 0
            mat, rndr = preview_mat()
            matrm = mat.renderman[mat.renderman_index]

            rmprdir = bpy.utils.preset_paths("renderman")[0]
            mat_preview_path = os.path.join(rmprdir, "material_previews")
            if matrm.preview_scene == "":
                return
            previewdir = os.path.join(mat_preview_path, matrm.preview_scene)
            previewdir_materialdir = os.path.join(previewdir, "Materials")
            mat_archive_file = os.path.join(previewdir_materialdir, "preview_material.rib")
            mat_archive = Archive(data_path=mat, filepath=mat_archive_file, scene=scene)
            print(mat.name)
            writeMaterial(mat, mat_archive=mat_archive, active_matpass=True)
            ribfile = os.path.join(previewdir, "material_preview.rib")
            renderprocess = subprocess.Popen([rndr, ribfile])  

            def update_image(image):
                result = self.begin_result(0, 0, 128, 128)
              
                layer = result.layers[0]
                try:
                    layer.load_from_file(image)
                    loaded = True
                except SystemError:
                    loaded = False
                self.end_result(result)
                return loaded

            img = os.path.join(previewdir, "material_preview.tiff")
            
            while not os.path.exists(img):
                if os.path.exists(img):
                    break                 
        
                if renderprocess.poll() == 0:
                    break            

            while not renderprocess.poll() == 0:
                update_image(img)
            update_image(img)

            
        else:
            if self.check_objects(scene):
                return
            rndr = scene.renderman_settings.renderexec
            if rndr == "":
                return
            
            path = getdefaultribpath(scene)
            pname = getname(rs.frame.filename,
                            scene=scene,
                            frame=framepadding(scene))+'.rib'
            
            filepath = os.path.join(path, pname)
                    
            rndr = scene.renderman_settings.renderexec

                                                 
            active_pass = getactivepass(scene)
    
            global exported_instances, base_archive
            base_archive = Archive(data_path=scene, type="Frame", scene=scene, filepath=filepath)
    
            if scene.renderman_settings.exportallpasses:
                for item in scene.renderman_settings.passes:
                    if item.export:
                        imagefolder = os.path.join(getdefaultribpath(scene), item.imagedir)
                        checkForPath(imagefolder)
                        export(item, scene)
                close_all()
                if not scene.renderman_settings.exportonly:
                    if rndr != "":
                        self.rm_start_render(rndr, base_archive.filepath, item, scene)
                        check_disps_processing(item, scene)
                else:
                    rndr_cmd = rndr + ' "'+base_archive.filepath+'"'
                    rm_shellscript(rndr_cmd, rm)
            else:
                export(active_pass, scene)
                close_all()
                imagefolder = os.path.join(path, active_pass.imagedir)
                checkpaths(imagefolder)
                if not scene.renderman_settings.exportonly:
                   if rndr != "":
                       self.rm_start_render(rndr, base_archive.filepath, active_pass, scene)
                       check_disps_processing(active_pass, scene)
                else:
                    rndr_cmd = rndr + ' "'+base_archive.filepath+'"'
                    rm_shellscript(rndr_cmd, rm)

##################################################################################################################################

##################################################################################################################################

##################################################################################################################################
##################################################################################################################################




##################################################################################################################################
maintainthread = None

def register():
    rm_props.register()
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.append(ui.draw_obj_specials_rm_menu)
    bpy.types.INFO_MT_add.append(ui.draw_rm_add_light)
    #threaded_maintaining()

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.remove(ui.draw_obj_specials_rm_menu)
    bpy.types.INFO_MT_add.remove(ui.draw_rm_add_light)
    #stop_maintaining()

if __name__ == "__main__":
    register()
