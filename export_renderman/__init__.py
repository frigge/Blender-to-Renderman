
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


bl_addon_info = {
    'name': 'Renderman',
    'author': 'Sascha Fricke',
    'version': '0.01',
    'blender': (2, 5, 5),
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
    import export_renderman
    import export_renderman.rm_props
    import export_renderman.ops
    import export_renderman.rm_maintain
    from export_renderman.rm_maintain import *
    import export_renderman.ui
    from export_renderman.ui import *
    import export_renderman.export

import bpy
import properties_render
import os
import subprocess
import math
import mathutils
import tempfile
import time

##################################################################################################################################

import properties_data_mesh
import properties_data_camera
import properties_data_lamp
import properties_texture
import properties_particle

#properties_render.RENDER_PT_render.COMPAT_ENGINES.add('RENDERMAN')
#properties_render.RENDER_PT_dimensions.COMPAT_ENGINES.add('RENDERMAN')
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
    exceptions = ['Render']
    try:
        if not subclass.bl_label in exceptions:
            subclass.COMPAT_ENGINES.add('RENDERMAN')
    except:
        pass
            
del properties_texture
del properties_data_mesh
del properties_data_camera
del properties_data_lamp

exported_instances = []

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

class Renderman_OT_Render(bpy.types.Operator):
    bl_label = "Render"
    bl_idname = "renderman.render"
    bl_description = "Export/Render Scene using Renderman"
    
    anim = bpy.props.BoolProperty(default = False)
    
    def invoke(self, context, event):
        scene = context.scene
        path = getdefaultribpath(scene)        
        checkpaths(path)
        checkpaths(os.path.join(path, scene.renderman_settings.polydir))
        checkpaths(os.path.join(path, scene.renderman_settings.shadowdir))
        checkpaths(os.path.join(path, scene.renderman_settings.envdir))
        checkpaths(os.path.join(path, scene.renderman_settings.texdir))
        if self.anim:
            for i in range(scene.frame_start, scene.frame_end+scene.frame_step, scene.frame_step):
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
    try:
        print("Render .. "+current_pass.name)
        print(render + ' ' + ribfile)
        os.system(render+" "+ribfile)
    except:
        pass           
                 
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
        maintain(scene)
        path = getdefaultribpath(scene)
                                             
        active_pass = getactivepass(scene)

        global exported_instances


        if scene.renderman_settings.exportallpasses:
            for item in scene.renderman_settings.passes:
                global current_pass
                current_pass = item
                imagefolder = os.path.join(path, item.imagedir)
                checkForPath(imagefolder)            
                name = getname( rs.render_pass.filename,
                                item.name,
                                sce = scene)+'.rib'
                rib = os.path.join(path, name)

                if item.displaydrivers:
                    image = item.displaydrivers[0].file   
                elif preview_scene and not item.displaydrivers:
                    adddisp(item)    
                    image = item.displaydrivers[0].file                                 

                exported_instances = []

                export(rib, scene)

                if not scene.renderman_settings.exportonly:
                    if rndr != "" and not item.environment:                            
                        start_render(rndr, rib, item, scene)                    
        else:

            exported_instances = []


            export(active_pass, path, scene)
            imagefolder = os.path.join(path, active_pass.imagedir)
            checkpaths(imagefolder)
            ribfilename = active_pass.name+framepadding(scene)+".rib"
            rib = os.path.join(path, ribfilename)
            if not scene.renderman_settings.exportonly:
               if rndr != "":
                   start_render(rndr, rib, active_pass, scene)       
       
       
class RendermanRender(bpy.types.RenderEngine):
    bl_idname = 'RENDERMAN'
    bl_label = "Renderman"
#    bl_use_preview = True
    delay = 0.02
    

    def render(self, scene):
#        global current_scene
#        global preview_scene
        for i, r in enumerate(scene.renderman_settings.passes):
            if r.name == 'Beauty':
                scene.renderman_settings.passes_index = i
        render(self, scene)
#        if scene.name == "preview":
#            preview_scene = True
#            rndr = current_scene.renderman_settings.renderexec 
#        else:    
#            preview_scene = False        
#            rndr = scene.renderman_settings.renderexec
#        if rndr != "":
#            maintain()
#            path = getdefaultribpath(scene)
#            
#
#
#    
#            def start_render(self, render, ribfile, current_pass):
#                r = scene.render
#                x = int(r.resolution_x * r.resolution_percentage * 0.01)
#                y = int(r.resolution_y * r.resolution_percentage * 0.01)
#                
#                self.update_stats("", "Render ... "+current_pass.name)
#            
#                if current_pass.displaydrivers and not current_pass.shadow:
#                    print("Render .. "+current_pass.name)
#                    print(render + ' ' + ribfile)
#                    
#                    renderprocess = subprocess.Popen([render, ribfile])
#                   
#                    def image(name): return name.replace("[frame]", framepadding(scene))    
#    
#                    def update_image(image):
#                        result = self.begin_result(0, 0, x, y)
#                      
#                        layer = result.layers[0]
#    
#                        try:
#                            layer.load_from_file(image)
#                            loaded = True
#                            print(name+" loaded "+printmessage)
#                        except:
#                            loaded = False
#                        self.end_result(result)
#                        return loaded
#                    if current_pass.displaydrivers[current_pass.renderresult].displaydriver != "framebuffer":
#                        img = image(current_pass.displaydrivers[current_pass.renderresult].file)
#                        
#                        while not os.path.exists(img):
#                            if os.path.exists(img):
#                                break                 
#                           
#                            if self.test_break():
#                                try:
#                                    renderprocess.terminate()
#                                except:
#                                    renderprocess.kill()
#                    
#                            if renderprocess.poll():
#                                self.update_stats("", "Error: Check Console")
#                                break
#    
#                            time.sleep(self.delay)              
#                                              
#                        prev_size = -1
#                        ready = False
#                       
#                        print("all image files created, now load them")
#                        while not ready:                 
#                            update_image(img)
#    #                            if renderprocess.poll():
#    #                                print("Finished")
#    #                                self.update_stats("", "Finished")
#    #                                update_image(layname, image)
#    #                                break
#            
#                            if self.test_break():
#                                try:
#                                    renderprocess.terminate()
#                                except:
#                                    renderprocess.kill()
#                                break
#                      
#                            try:
#                                if os.path.getsize(img) != prev_size:
#                                    prev_size = os.path.getsize(img) 
#                                    update_image(img)                                  
#                                else:
#                                    update_image(img)
#                                    ready = True
#                                    self.update_stats("", "Finished")
#                                    break
#                            except:
#                                pass                                   
#                            
#                            time.sleep(self.delay)                                          
#                  
#                    
#                    else:
#                        try:
#                            print("render " +ribfile)
#                            os.system(render+" "+ribfile)
#                        except:
#                            pass                    
#            
#                ## until the render api is fixed, load all images manually in the image editor
#                for disp in current_pass.displaydrivers:
#                    img = image(disp.file)
#                    if not img in bpy.data.images and not disp.displaydriver == "framebuffer":
#                        bpy.data.images.load(image(disp.file))
#                    else: bpy.data.images[img].update()                        
#            
#            self.update_stats("", "generating Folder structure")
#            checkpaths(path)
#            checkpaths(os.path.join(path, scene.renderman_settings.polydir))
#            checkpaths(os.path.join(path, scene.renderman_settings.shadowdir))
#            checkpaths(os.path.join(path, scene.renderman_settings.envdir))
#            checkpaths(os.path.join(path, scene.renderman_settings.texdir))
#    
#            if preview_scene:
#                scene.renderman_settings.facevertex = False
#                if not scene.renderman_settings.passes:
#                    scene.renderman_settings.passes.add().name = "preview"
#                if not scene.renderman_settings.passes["preview"].displaydrivers:
#                    adddisp(scene.renderman_settings.passes['preview'])
#                active_pass = scene.renderman_settings.passes["preview"]
#                maintain_display_drivers(active_pass, scene)
#            else:            
#                active_pass = getactivepass(scene)
#
#
#    
#            name = active_pass.name+framepadding(scene)
#    
#    
#            if scene.renderman_settings.exportallpasses:
#                for item in scene.renderman_settings.passes:
#                    imagefolder = os.path.join(path, item.imagedir)
#                    checkpaths(imagefolder)
#                for item in scene.renderman_settings.passes:
#                    ribfilename = item.name+framepadding(scene)+".rib"
#                    rib = os.path.join(path, ribfilename)
#    
#                    if item.displaydrivers:
#                        image = item.displaydrivers[0].file   
#                    elif preview_scene and not item.displaydrivers:
#                        adddisp(item)    
#                        image = item.displaydrivers[0].file                                 
#                    self.update_stats("", "export scene data to RenderMan Interface Bytestream")
#    
#    
#                    writedata(scene, item, path)
#                    if item.environment:
#                        exported_env_directions += 1
#                        print("env "+str(exported_env_directions))
#                    if not scene.renderman_settings.exportonly:
#    #                    ready = False
#    #                    prev_size = -1
#    #                    while not ready:
#    #                        if self.test_break():
#    #                            try:
#    #                                break
#    #                            except:
#    #                                break
#    #
#    #                        if os.path.exists(rib):
#    #                            size = os.path.getsize(rib)
#    #                            print("rib size "+str(size))
#    #                            if size == prev_size:
#    #                                ready = True
#    #                                break
#    #                            
#    #                            prev_size = size
#                        if rndr != "":                            
#                            start_render(self, rndr, rib, item)
#                        
#    
#            else:
#                self.update_stats("", "export scene data to RenderMan Interface Bytestream")
#    
#                writedata(scene, active_pass, path, frame)
#                imagefolder = os.path.join(path, active_pass.imagedir)
#                checkpaths(imagefolder)
#                image = os.path.join(imagefolder, imagename)
#                ribfilename = active_pass.name+framepadding(scene)+".rib"
#                rib = os.path.join(path, ribfilename)
#                if not scene.renderman_settings.exportonly:
#                   if rndr != "":
#                       start_render(self, rndr, rib, active_pass)

##################################################################################################################################

##################################################################################################################################

##################################################################################################################################
##################################################################################################################################




##################################################################################################################################

def register():
    export_renderman.rm_maintain.reg_maintain()
    bpy.types.VIEW3D_MT_object_specials.append(draw_obj_specials_rm_menu)
    
    

def unregister():
    bpy.types.VIEW3D_MT_object_specials.remove(draw_obj_specials_rm_menu)

if __name__ == "__main__":
    register()
