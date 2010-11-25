
#Basic Blender 2.5 or later to Renderman Exporter
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
assigned_shaders = {}
objects_size = -1
light_list = []
light_list_size = -1
obj_passes = {}



##################################################################################################################################
##################################################################################################################################


#Define classes for Collection and Pointer properties

class passes(bpy.types.IDPropertyGroup):            #passes
    pass

class DisplayCollection(bpy.types.IDPropertyGroup):         #Display Drivers
    pass

class Collection(bpy.types.IDPropertyGroup):            #All Variable Properties: Shader Settings, Options, Attributes
    pass

class Shader(bpy.types.IDPropertyGroup):            #
    pass

class ObjectParameters(bpy.types.IDPropertyGroup):            #Object Attributes
    pass

class RendermanSceneSettings(bpy.types.IDPropertyGroup):            #Renderman Scene Settings
    pass

class Paths(bpy.types.IDPropertyGroup):             #
    pass

class PathProperties(bpy.types.IDPropertyGroup):            #
    pass

class RendermanLightSettings(bpy.types.IDPropertyGroup):            #
    pass

class RendermanPixelFilter(bpy.types.IDPropertyGroup):          #Filter Settings
    pass

class LightCollection(bpy.types.IDPropertyGroup):           #
    pass

class DisplayDrivers(bpy.types.IDPropertyGroup):
    pass

class Hider(bpy.types.IDPropertyGroup):
    pass

class AttributeOptionGroup(bpy.types.IDPropertyGroup):
    pass

class RendermanTexture(bpy.types.IDPropertyGroup):
    pass

class EmptyCollections(bpy.types.IDPropertyGroup):
    pass

class Mappings(bpy.types.IDPropertyGroup):
    pass

class ParticlePasses(bpy.types.IDPropertyGroup):
    pass

class Empty(bpy.types.IDPropertyGroup):
    pass

class EmptyPasses(bpy.types.IDPropertyGroup):
    pass

class RibStructure(bpy.types.IDPropertyGroup):
    pass

#########################################################################################################
#                                                                                                       #
#       Create Properties                                                                               #
#                                                                                                       #
#########################################################################################################
String = bpy.props.StringProperty
Bool = bpy.props.BoolProperty
Enum = bpy.props.EnumProperty
CollectionProp = bpy.props.CollectionProperty
Pointer = bpy.props.PointerProperty
FloatVector = bpy.props.FloatVectorProperty
IntVector = bpy.props.IntVectorProperty
Int = bpy.props.IntProperty
Float = bpy.props.FloatProperty

RibStructure.own_file = Bool(default = True, name = "Own File", description="write into own RIB Archive")

RibStructure.filename = String(name="File", default="", subtype = 'FILE_PATH')

RibStructure.default_name = Bool(default = True, name = "Default Name", description = "Default RIB Archive Name")

RibStructure.overwrite = Bool(default = True, name = "Overwrite", description="overwrite existing files")

RibStructure.expand = Bool(default=False, name="Expand", description="Expand Properties")

Collection.parametertype = Enum(items=(
                                ("string", "String", "String Parameter"),
                                ("float", "Float", "Float Parameter"),
                                ("int", "Integer", "Integer Parameter"),
                                ("color", "Color", "Color Parameter"),
                                ),
                                default="string",
                                name = "Parameter Type",
                                description = "Type of Parameter")


Collection.textparameter = String()

Collection.texture = Bool(  description = "Choose from materials texture stack",
                            default=False,
                            options={'ANIMATABLE'})
                            
Collection.export = Bool(default=False, description="export object attribute", options={'ANIMATABLE'})

Collection.preset_include = Bool(default = True, description = "include Attribute in preset", options={'ANIMATABLE'})

Collection.rib_name = String()                          

Collection.texture_raw = String()


Collection.float_one = FloatVector( precision = 4,
                                    size = 1,
                                    options={'ANIMATABLE'})

Collection.float_two = FloatVector( default=(0.0, 0.0),
                                    precision = 4,
                                    size = 2,
                                    options={'ANIMATABLE'})
                                
Collection.float_three = FloatVector(   default=(0.0, 0.0, 0.0),
                                        precision = 4,
                                        size = 3,
                                        options={'ANIMATABLE'})
                                
Collection.int_one = IntVector(     step=100,
                                    size=1,
                                    options={'ANIMATABLE'})
                                
Collection.int_two = IntVector( step=100,
                                size=2,
                                options={'ANIMATABLE'})
                                
Collection.int_three = IntVector(   step=100,
                                    size=3,
                                    options={'ANIMATABLE'})                                                                                                                                                                

Collection.colorparameter = FloatVector(name="Color Parameter",
                                        description="Color Parameter",
                                        subtype='COLOR',
                                        precision = 4,
                                        step = 0.01,
                                        min=0,
                                        max = 1,
                                        default = (0, 0, 0),
                                        options={'ANIMATABLE'})

Collection.parameterindex = Int(default=-1,
                                min=-1,
                                max=1000,
                                options={'ANIMATABLE'})
                        
Collection.vector_size = Int(   default = 1,
                                min = 1,
                                max = 3,
                                options={'ANIMATABLE'})                        

Collection.collection = CollectionProp(type = Collection)

Collection.free = Bool(default = False)

Collection.type = String()

#############################################
#                                           #
#   Render Properties                       #
#                                           #
#############################################

passes.displaydrivers = CollectionProp(type=DisplayCollection)

passes.displayindex = Int(  default = -1,
                            min=-1,
                            max=1000)

RendermanSceneSettings.displays = CollectionProp(type=DisplayDrivers)
                                            
RendermanSceneSettings.hider_list = CollectionProp(type=Hider)

passes.hider_list = CollectionProp(type=Hider)

RendermanSceneSettings.hider_list_index = Int(  min=-1,
                                                max=10000,
                                                default=-1)
                                    
RendermanSceneSettings.default_hider = String()                                    

Hider.options = CollectionProp(type=Collection)

passes.hider = String()

RendermanSceneSettings.settings_rib_structure = Pointer(type=RibStructure)

RendermanSceneSettings.world_rib_structure = Pointer(type=RibStructure)
                                            
#############################################
#                                           #
#   Display Properties                      #
#                                           #
#############################################

DisplayCollection.send = Bool(default = False)

DisplayCollection.filename_var = Bool(default = True, name="Variable", description="add output variable to filename")

DisplayCollection.custom_options = CollectionProp(type = Collection)

Collection.custom_var = Bool(default=True, description="use name of output variable as value")

#DisplayDrivers.file_name = String()                                            

RendermanSceneSettings.var_collection = CollectionProp( name="Output Value",
                                                    type=DisplayDrivers
                                                    )
                               
DisplayCollection.var = String(default="rgba")                               
                                
DisplayCollection.displaydriver = String()                                

DisplayCollection.file = String()

DisplayCollection.filename = String()

DisplayCollection.quantize_min = Int(min=0, max=100000, default=0, description = "min")

DisplayCollection.quantize_max = Int(min=0, max=100000, default=0, description = "max")

DisplayCollection.quantize_black = Int(min=0, max=100000, default=0, description = "black")

DisplayCollection.quantize_white = Int(min=0, max=100000, default=0, description = "white")

DisplayCollection.quantize_presets = Enum(items=    (
                                                                        ("8bit", "8 bit", ""),
                                                                        ("16bit", "16 bit", ""),
                                                                        ("32bit", "32 bit", ""),
                                                                        ("other", "other", "")
                                                                    ),
                                                                    default = "16bit",
                                                                    name = "Quantization")

DisplayCollection.expand = Bool(default=False)

DisplayCollection.quantize_expand = Bool(default=False)

DisplayCollection.exposure_expand = Bool(default=False)

DisplayCollection.custom_expand = Bool(default=False)

passes.pixelsamples_x = Int(name="PixelSamples",
                    default = 2,
                    min = 1,
                    max = 100)

passes.pixelsamples_y = Int(name="PixelSamples",
                    default = 2,
                    min = 1,
                    max = 100)

DisplayCollection.gain = Float(min=0,
                        max=100,
                        default=1,
                        name="Gain")

DisplayCollection.gamma = Float(min=0,
                        max=100,
                        default=1,
                        name="Gamma")

passes.pixelfilter = Pointer(type=RendermanPixelFilter)

RendermanPixelFilter.filterlist = Enum(items=(
                                            ("box", "Box", "Box Filter"),
                                            ("gaussian", "Gaussian", "Gaussian Filter"),
                                            ("sinc", "Sinc", "Cube Filter"),
                                            ("triangle", "Triangle", "Triangle Filter"),
                                            ("catmull-rom", "Catmull-Rom", ""),
                                            ("blackman-harris", "Blackman-Harris", ""),
                                            ("mitchell", "Mitchell", ""),
                                            ("other", "Other", "Custom Filter")
                                        ),
                                    default="",
                                    name = "PixelFilter")

RendermanPixelFilter.customfilter = String(name="Custom Filter",
                                    default = "")

RendermanPixelFilter.filterwidth = Float(min = 0,
                                    max = 100,
                                    default = 1)

RendermanPixelFilter.filterheight = Float(min = 0,
                                    max = 100,
                                    default = 1)




RendermanSceneSettings.facevertex = Bool(name="facevertex",
                            default = False)

Paths.shaderpaths = CollectionProp(type = PathProperties)

Paths.shadercollection = CollectionProp(type = PathProperties)

Paths.shadersrccollection = CollectionProp(type = PathProperties)

Paths.shaderbincollection = CollectionProp(type = PathProperties)

Paths.shaderpathsindex = Int(min = -1,
                    max = 1000,
                    default = -1)

RendermanSceneSettings.pathcollection = Pointer(type = Paths)

RendermanSceneSettings.shaderpath = String(subtype='DIR_PATH')

RendermanSceneSettings.framepadding = Int(default=4,
                    min=1,
                    max=1000)

RendermanSceneSettings.passes = CollectionProp(type=passes)

RendermanSceneSettings.passes_index = Int(default=-1,
                                min=-1,
                                max=1000)

RendermanSceneSettings.searchpass = String(name = "Search Pass",
                        default = "")


bpy.types.Scene.renderman_settings = Pointer(type=RendermanSceneSettings)                       

RendermanSceneSettings.exportallpasses = Bool(name="Export All Passes",
                    description="",
                    default=True)

##########################################################
#Settings
RendermanSceneSettings.presetname = String()
RendermanSceneSettings.active_engine = String()
RendermanSceneSettings.basic_expand = Bool(default=False)
RendermanSceneSettings.hider_expand = Bool(default=False)
RendermanSceneSettings.options_expand = Bool(default=False)
RendermanSceneSettings.attributes_expand = Bool(default=False)
RendermanSceneSettings.shader_expand = Bool(default=False)
RendermanSceneSettings.dir_expand = Bool(default=False)
RendermanSceneSettings.mappings_expand = Bool(default=False)

RendermanSceneSettings.renderexec = String(name="Render Executable",
                        description="Render Executable",
                        default="",
                        options={'HIDDEN'},
                        subtype='NONE')

RendermanSceneSettings.shaderexec = String(name="Shader Compiler",
                        description="Shader Compiler Executable",
                        default="",
                        options={'HIDDEN'},
                        subtype='NONE')

RendermanSceneSettings.shadersource = String(name="Source Extension",
                        description="Shader Source Code Extension",
                        default="",
                        options={'HIDDEN'},
                        subtype='NONE')

RendermanSceneSettings.shaderinfo = String(name="Shaderinfo Binary",
                        description="Shader information Tool binary",
                        default="",
                        options={'HIDDEN'},
                        subtype='NONE')

RendermanSceneSettings.textureexec = String(name="Texture Preparation",
                        description ="Texture Preparation Tool",
                        default="",
                        options={'HIDDEN'},
                        subtype="NONE")

RendermanSceneSettings.shaderbinary = String(name="Binary Extension",
                        description="Shader Binary Extension",
                        default="",
                        options={'HIDDEN'},
                        subtype='NONE')

RendermanSceneSettings.textureext = String(name="Texture Extension",
                        description="Texture Extension",
                        default="",
                        options={'HIDDEN'},
                        subtype='NONE')
                        
RendermanSceneSettings.deepdisplay = String(name="Texture Extension",
                        description="Texture Extension",
                        default="",
                        options={'HIDDEN'},
                        subtype='NONE')

RendermanSceneSettings.defaultshadow = String(name="Texture Extension",
                        description="Texture Extension",
                        default="",
                        options={'HIDDEN'},
                        subtype='NONE')

RendermanSceneSettings.displaydrvpath = String(name="Display Path",
                        description="Path to Display Driver folder",
                        default="",
                        options={'HIDDEN'},
                        subtype='DIR_PATH')
                        
RendermanSceneSettings.disp_ext_os_default = Bool(name="OS Lib", description="Default OS Lib extension", default=True)

RendermanSceneSettings.disp_ext = String(name="Extension", description='Custom Display Driver extension(without "."')

RendermanSceneSettings.drv_identifier = String(description = "Prefix or suffix in drivers filename to identify, that its actually a Display Driver")

RendermanSceneSettings.default_driver = String(description = "Default Display Driver")

RendermanSceneSettings.mappings = Pointer(type = Mappings)

Mappings.point_shadowpref = String(name="Point Shadow Prefix", description="Pointlight Shadowmap Parameter Name Prefix in Light Shader")

Mappings.shadowmap = String(name="Shadowmap", description="Shadowmap Parameter Name in Light Shader")

Mappings.pointshader = String(name="PointShader", description="Default Pointlight Shader")

Mappings.shadowpointshader = String(name ="ShadowPointShader", description="Default Shadowpoint Shader")

Mappings.spotshader = String(name="SpotShader", description="Default Spotlight Shader")

Mappings.shadowspotshader = String(name ="ShadowSpotShader", description="Default Shadowspot Shader")

Mappings.distantshader = String(name="DistantShader", description="Default Distantlight Shader")

Mappings.shadowdistantshader = String(name ="ShadowDistantShader", description="Default Shadowdistant Shader")

#########################################################

RendermanSceneSettingsdefaultribpath = Bool(default=True)

RendermanSceneSettings.ribpath = String(name="RIB Path",
                        description="Path to Scene RIB File",
                        default="",
                        options={'HIDDEN'},
                        subtype='DIR_PATH')

RendermanSceneSettings.objectdir = String( name="Objects",
                                        description = "Folder where Object Archives are stored",
                                        default = "Objects")
                                        
RendermanSceneSettings.settingsdir = String( name="Settings",
                                        description = "Folder where Settings Archives are stored",
                                        default = "Settings")
                                        
RendermanSceneSettings.worlddir = String( name="Worlds",
                                        description = "Folder where World Archives are stored",
                                        default = "Worlds")
                                        
RendermanSceneSettings.bakedir = String( name="Bake",
                                        description = "Folder where bake files are stored",
                                        default = "Bakes")                                                                                                                        

RendermanSceneSettings.polydir = String(name="Poly Mesh Folder",
                        description="Folder where Poly Meshes are stored",
                        default="Mesh",
                        options={'HIDDEN'})
                        
RendermanSceneSettings.particledir = String(name="Particle Systems Folder",
                        description="Folder where Particle Systems are stored",
                        default="Particles",
                        options={'HIDDEN'})                        

RendermanSceneSettings.shadowdir = String(name="Shadowmap Folder",
                        description="Name of Shadow map's Folder",
                        default="shadowmaps",
                        options={'HIDDEN'})

RendermanSceneSettings.envdir = String(name="Environmentmaps Folder",
                        description="Name of Environment Maps Folder",
                        default="envmaps",
                        options={'HIDDEN'})

RendermanSceneSettings.texdir = String(name="Texturemaps Folder",
                        description="Name of Texture Maps Folder",
                        default="textures",
                        options={'HIDDEN'})

passes.imagedir = String(name="Image Folder",
                        description="Name of Image Output Folder",
                        default="images",
                        options={'HIDDEN'})

RendermanSceneSettings.exportonly = Bool(name="Export Only",
                    description="Only Export Scene Rib File without rendering",
                    default=False,
                    options={'HIDDEN'},
                    subtype='NONE')

passes.exportobjects = Bool(name="Export All Objects",
                    description="Export All Objects to .rib files",
                    default=True)

passes.exportlights = Bool(name="Export All Lights",
                    description="Export All Lights to Scene .rib file",
                    default=True)

passes.exportanimation = Bool(name="Export Animation",
                    default=True)

passes.shadow = Bool(name="Export Animation",
                    default=False)

passes.sceneindex = Int(name="Object Index",
                    description = "",
                    default = -1,
                    min = -1,
                    max = 10000)

passes.objectgroup = String(name="Object Group",
                        description="export only objects in this group")

passes.lightgroup = String(name="Light Group",
                        description="export only lights in this group")

passes.filename = String(default = "")

passes.environment = Bool(default = False)

passes.envname = String()

passes.camera_object = String()

passes.motionblur = Bool(default=False,
                            name="Motion Blur",
                            description = "render motion blur for this pass")
                        
passes.shutterspeed = Int(name="Shutter Speed",
                            min=2,
                            max=1000,
                            default=2,
                            description="Amount of time the shutter is open(in frames)")                        

passes.option_groups = CollectionProp(type=AttributeOptionGroup,
                            name="Option Groups",
                            description="Renderman Option Groups")
                            
passes.renderresult = String()                            
                            
                            
AttributeOptionGroup.expand = Bool(default =False)

AttributeOptionGroup.export = Bool(default =False)

AttributeOptionGroup.preset_include = Bool(default = True, description="include Attribute Group in preset")

AttributeOptionGroup.options = CollectionProp(type=Collection ,
                            name="Renderman Options",
                            description="Renderman Options")
                                                        
                            
RendermanSceneSettings.option_groups = CollectionProp(type=AttributeOptionGroup,
                            name="Option Groups",
                            description="Renderman Option Groups")   
                            
RendermanSceneSettings.option_groups_index = Int(min=-1, max=1000, default=-1)

Collection.envmap = Bool(name="Environmentmap",
                        description="",
                        default=False)

Collection.rman_type = String()

passes.scene_code = CollectionProp(type = EmptyCollections)

passes.scene_code_index = Int(min = -1, max = 1000, default = -1)

passes.world_code = CollectionProp(type = EmptyCollections)

passes.world_code_index = Int(min = -1, max = 1000, default = -1)
#############################################
#                                           #
#   World Properties                        #
#                                           #
#############################################

passes.attribute_groups = CollectionProp(type=AttributeOptionGroup)

AttributeOptionGroup.attributes = CollectionProp(type=Collection)

RendermanSceneSettings.attribute_groups = CollectionProp(type=AttributeOptionGroup)
                            
RendermanSceneSettings.attribute_groups_index = Int(min=-1, max=1000, default=-1)                            

passes.global_shader = Pointer(type = Shader)

#############################################
#                                           #
#   Imager Shader Properties                #
#                                           #
#############################################


passes.imager_shader = String(name="Imager Shader",
                                    description="Name of Imager Shader",
                                    default="",
                                    options={'HIDDEN'},
                                    subtype='NONE')

passes.imager_shader_parameter = CollectionProp(type=Collection ,
                            name="ImagerParam",
                            description="Imager Shader Parameter")

passes.imager_shader_parameter_index = Int(name="Imager Shader Parameter Index",
                    description="",
                    default=-1,
                    min=-1,
                    max=1000)



#############################################
#                                           #
#   Camera Properties                       #
#                                           #
#############################################


camera = bpy.types.Camera

camera.depthoffield = Bool(default = False,
                        name = "DOF")

camera.focal_length = Float(min=0,
                        default=0,
                        name="Focal Length")

camera.fstop = Float(min=0,
                        default=2.8,
                        name="F-Stop")

camera.use_lens_length = Bool(default=True,
                        name="Use Camera Lens")
                        
ObjectParameters.perspective_blur = Bool(   name="perspective_blur",
                                            default = False,
                                            description = "apply motion blur to the viewing angle of this camera")                        
                                           

#############################################
#                                           #
#   Light Properties                        #
#                                           #
#############################################
Shader.links = CollectionProp(type = EmptyCollections)

Shader.customshader = Bool(name="Custom Shader",
                            description="Assign custom shader",
                            default=False,
                            options={'HIDDEN'},
                            subtype='NONE')

Shader.shaderpath = String(name="Shader Path",
                                description="Path to custom shader",
                                default="",
                                options={'HIDDEN'},
                                subtype='NONE')

RendermanLightSettings.near_clipping = Float(min = 0,
                                    max = 1000000,
                                    default = 1)

RendermanLightSettings.far_clipping = Float(min = 0,
                                    max = 1000000,
                                    default = 30)

Shader.light_shader_parameter = CollectionProp(type=Collection ,
                            name="LightParam",
                            description="Light Shader Parameter")     
                    
Shader.use_as_light = Bool(name="AreaLight", description="use the object this material is assigned to as an AreaLight")

bpy.types.Lamp.renderman = CollectionProp(type=Shader)

bpy.types.Lamp.renderman_index = Int(min = -1, max = 1000, default = -1)

RendermanLightSettings.shadow_map_resolution = Int(min=0,
                                max=50000,
                                default=512)

bpy.types.Lamp.lightsettings = Pointer(type=RendermanLightSettings)


RendermanLightSettings.type = Enum(items=(
                                            ("spot", "Spot", "Spot Light"),
                                            ("point", "Point", "Point Light"),
                                            ("directional", "Directional", "Directional Light"),
                                            ),
                                    default="point",
                                    name="Light Type",
                                    description="")

Shader.shadowtype = Enum(items=(
                                            ("shadowmap", "Shadowmap", "Shadowmap"),
                                            ("raytrace", "Raytrace", "Raytraced Shadow"),
                                            ("none", "No Shadow", "No Shadow")
                                            ),
                                    default="none",
                                    name ="Shadow Type",
                                    description="")  
                                 
RendermanLightSettings.shadowmaptype = Enum(items=(
                                                    ("deep", "Deep Shadow", ""),
                                                    ("classic", "Classic Shadow", "")
                                                  ), default = "classic", name="Shadowmap Type")
#############################################
#                                           #
#   Object Properties                       #
#                                           #
#############################################
Object = bpy.types.Object

Object.env = Bool(default=False)

Object.renderman = CollectionProp(type = ObjectParameters, name="Renderman")

Object.renderman_index = Int(min = -1, max = 1000, default = -1)

ObjectParameters.links = CollectionProp(type = EmptyCollections)

ObjectParameters.attribute_groups = CollectionProp(type=AttributeOptionGroup)

ObjectParameters.light_list = CollectionProp(name="Light List",
                                    description="Ligh List",
                                    type=LightCollection)

LightCollection.illuminate = Bool(name="Illuminate",
                                default=True)

ObjectParameters.lightgroup = String()

ObjectParameters.shadingrate = Float(name="Shading Rate",
                                min = 0,
                                max = 100,
                                default = 1)
                                
ObjectParameters.transformation_blur = Bool(name="transformation Blur",
                                            default=False,
                                            description="apply motion blur to the transformation of this object")
                                    
ObjectParameters.deformation_blur = Bool(   name="deformation Blur",
                                            default = False,
                                            description = "apply motion blur to the deformation of this object")
                                            
                                            
                                            
ObjectParameters.motion_samples = Int(  name="motion samples",
                                        min = 2,
                                        max = 10,
                                        default = 2,
                                        description="number of motion samples(must be no smaller than motion length")                                           
                             
#############################################
#                                           #
#   Mesh Properties                         #
#                                           #
#############################################

mesh = bpy.types.Mesh

mesh.primitive_type = Enum(name = "Primitive Type", default="PointsPolygon", items=(("PointsPolygons", "PointsPolygons", ""),
                                                                                    ("Points", "Points", ""),
                                                                                    ("SubdivisionMesh", "SubdivisionMesh", ""),
                                                                                    ("Quadrics", "Quadrics", "Quadrics")))                                                                           
                                                                                    
mesh.export_type = Enum(name = "Export As", default="ReadArchive", items=(  ("ReadArchive", "ReadArchive", ""),
                                                                            ("DelayedReadArchive", "DelayedReadArchive", ""),
                                                                            ("ObjectInstance", "ObjectInstance", "")))

mesh.size_vgroup = String(name="Vertex Group", description="Control the siza of each point via Vertex Group", default ="")  

mesh.points_scale = Float(name ="Points Scale", description="Scale of Points", min=0, max=10000, default=1) 


#############################################
#                                           #
#   Empty Properties                        #
#                                           #
#############################################


RNAEmpty = bpy.types.Empty

RNAEmpty.renderman = Pointer(type = Empty)

Empty.passes = CollectionProp(type = EmptyPasses)

Empty.quadrics = Enum(  name = "Quadrics", 
                                        description="Replace Mesh by render intern Quadrics", 
                                        default="Points",
                                        items = (   ("Sphere", "Sphere", "Sphere"),
                                                    ("Cone", "Cone", "Cone"),
                                                    ("Cylinder", "Cylinder", "Cylinder"),
                                                    ("Hyperboloid", "Hyperboloid", "Hyperboloid"),
                                                    ("Paraboloid", "Paraboloid", "Paraboloid"),
                                                    ("Disk", "Disk", "Disk"),
                                                    ("Torus", "Torus", "Torus")))         

EmptyPasses.quadrics = Enum(  name = "Quadrics", 
                                        description="Replace Mesh by render intern Quadrics", 
                                        default="Points",
                                        items = (   ("Sphere", "Sphere", "Sphere"),
                                                    ("Cone", "Cone", "Cone"),
                                                    ("Cylinder", "Cylinder", "Cylinder"),
                                                    ("Hyperboloid", "Hyperboloid", "Hyperboloid"),
                                                    ("Paraboloid", "Paraboloid", "Paraboloid"),
                                                    ("Disk", "Disk", "Disk"),
                                                    ("Torus", "Torus", "Torus")))
                                                    
mesh.export_type = Enum(name = "Export As", default="ReadArchive", items=(  ("ReadArchive", "ReadArchive", ""),
                                                                            ("DelayedReadArchive", "DelayedReadArchive", ""),
                                                                            ("ObjectInstance", "ObjectInstance", "")))                                                     
                                                                                             
#############################################################
#                                                           #
#   Material Properties                                     #
#                                                           #
#############################################################

mat = bpy.types.Material
tex = bpy.types.Texture

tex.renderman = Pointer(type=RendermanTexture)

RendermanTexture.type = Enum(name="Type", default="none", items=(
                                                                    ("none", "None", ""),
                                                                    ("envmap", "Environment Map", ""),
                                                                    ("file", "Image File", ""),
                                                                    ("bake", "Bake File", "")))

RendermanTexture.envpass = String()

RendermanTexture.process = Bool(    name="Process",
                                    default = True,
                                    description = "run Texture processing tool to convert into rendermans intern texture format")

RendermanTexture.filter = String(   name="Filter",
                                    default ="box",
                                    description = "Filter to use when converting the image")

RendermanTexture.width = Float(     name ="Width",
                                    min = 0,
                                    max = 100,
                                    default = 1,
                                    description = "Filter Width")

RendermanTexture.swidth = Float(    name = "s Width",
                                    min = 0,
                                    max = 100,
                                    default = 1,
                                    description = "Filter Width in s direction")

RendermanTexture.twidth = Float(    name = "t Width",
                                    min = 0,
                                    max = 100,
                                    default = 1,
                                    description = "Filter Width in t direction")

RendermanTexture.stwidth = Bool(    name = "st Width",
                                    default = False,
                                    description = "Specify Filter Width in s and t direction separately")

RendermanTexture.resolution = Int(  min=0, 
                                    max = 10000, 
                                    default = 512, 
                                    name="Resolution", 
                                    description="Environment Map Resolution")
                                    
RendermanTexture.depth = Int(   min = 1,
                                max = 100,
                                default = 1,
                                name = "Depth",
                                description = "Times the environment map is generated")
                                
RendermanTexture.fov = Float(   min=1,
                                max = 360,
                                default = 90,
                                name = "FieldOfView",
                                description = "Field of View for environment maps")                                                        

mat.renderman = CollectionProp(type=Shader)

mat.renderman_index = Int(min = -1, max = 1000, default = -1)
                        
Shader.arealight_shader = String(name="AreaLight", description="Area Light Shader")                        

Shader.opacity = FloatVector(name="Opacity",
                            subtype="COLOR",
                            default=(1, 1, 1),
                            precision = 4,
                            step = 0.01,
                            min=0,
                            max=1)
                            
Shader.color = FloatVector(name="Color",
                            subtype="COLOR",
                            default=(1, 1, 1),
                            precision = 4,
                            step = 0.01,
                            min=0,
                            max=1)                            
                            
                            
Shader.motion_samples = Int(    default=2,
                                min=2,
                                max=1000,
                                name="Motion Samples",
                                description="number samples to put into motion block")
                                
Shader.color_blur = Bool(   default=False,
                            name="Color Blur",
                            description="Motion Blur for surface color")
                            
Shader.opacity_blur = Bool(   default=False,
                            name="Opacity Blur",
                            description="Motion Blur for surface opacity") 
                            
Shader.shader_blur = Bool(  default=False,
                            name = "Shader Blur",
                            description = "Motion Blur for parameters of assigned shader")                                                                                                                                             

PathProperties.fullpath = String(default = "")

PathProperties.mod_time = Int()


mat.matte = Bool(name="Matte",
                            default=True)                            

#############################################
#                                           #
#   Surface Shader Properties               #
#                                           #
#############################################


Shader.surface_shader = String(name="Surface Shader",
                                    description="Name of Surface Shader",
                                    default="matte",
                                    options={'HIDDEN'},
                                    subtype='NONE')

Shader.surface_shader_parameter = CollectionProp(type=Collection ,
                            name="SurfaceParam",
                            description="Surface Shader Parameter")

#############################################
#                                           #
#   Displacement Shader Properties          #
#                                           #
#############################################


Shader.displacement_shader = String(name="Displacement Shader",
                                    description="Name of Displacement Shader",
                                    default="",
                                    options={'HIDDEN'},
                                    subtype='NONE')

Shader.disp_shader_parameter = CollectionProp(type=Collection ,
                            name="DisplacementParam",
                            description="Displacement Shader Parameter")

#############################################
#                                           #
#   Interior Shader Properties              #
#                                           #
#############################################


Shader.interior_shader = String(name="Interior Shader",
                                    description="Interior Volume Shader",
                                    default="",
                                    options={'HIDDEN'},
                                    subtype='NONE')

Shader.interior_shader_parameter = CollectionProp(type=Collection ,
                            name="VolumeParam",
                            description="Volume Shader Parameter")

#############################################
#                                           #
#   Exterior Shader Properties              #
#                                           #
#############################################


Shader.exterior_shader = String(name="Exterior Shader",
                                    description="Exterior Volume Shader",
                                    default="",
                                    options={'HIDDEN'},
                                    subtype='NONE')

Shader.exterior_shader_parameter = CollectionProp(type=Collection ,
                            name="VolumeParam",
                            description="Volume Shader Parameter")
                    
#############################################
#                                           #
#   Atmosphere Shader Properties            #
#                                           #
#############################################


Shader.atmosphere_shader = String(name="Atmosphere Shader",
                                    description="Atmosphere Volume Shader",
                                    default="",
                                    options={'HIDDEN'},
                                    subtype='NONE')

Shader.atmosphere_shader_parameter = CollectionProp(type=Collection ,
                            name="VolumeParam",
                            description="Volume Shader Parameter")

Shader.atmosphere_parameter_index = Int(name="Volume Shader Parameter Index",
                    description="",
                    default=-1,
                    min=-1,
                    max=1000)
                    
                    
#############################################
#                                           #
#   Particle Properties                     #
#                                           #
############################################# 

psettings = bpy.types.ParticleSettings

psettings.renderman = CollectionProp(type = ParticlePasses)

psettings.renderman_index = Int(min = -1, max = 1000, default = -1)

ParticlePasses.links = CollectionProp(type = EmptyCollections)

ParticlePasses.motion_blur = Bool(name = "Motion Blur", default=False, description = "Activate Motion Blur for Particles")

ParticlePasses.motion_samples = Int(name = "motion samples", description="Number samples to export in this motion block", min=2, max = 100, default = 2)

ParticlePasses.render_type = Enum(  name = "Render Type",
                                    description = "Choose how to render the particles",
                                    items = (   ("Points", "Points", "Points"),
                                                ("Object", "Object", "Object"),
                                                ("Group", "Group", "Group"),
                                                ("Archive", "Archive", "Archive")))
                                                
ParticlePasses.object = String(name = "Object", description ="Object to use for Rendering Particles")

ParticlePasses.archive = String(name ="Archive", description  = "Archive to load for Rendering Particles", subtype = "FILE_PATH") 

ParticlePasses.group = String(name = "Group", description ="Objects of group to use for Rendering Particles")                                              

ParticlePasses.attribute_groups = CollectionProp(type=AttributeOptionGroup)

ParticlePasses.shaders = Pointer(type= Shader)

ParticlePasses.surface_expand = Bool(name="Expand", description="Expand Shader", default=False)

ParticlePasses.disp_expand = Bool(name="Expand", description="Expand Shader", default=False)

ParticlePasses.interior_expand = Bool(name="Expand", description="Expand Shader", default=False)

ParticlePasses.exterior_expand = Bool(name="Expand", description="Expand Shader", default=False)

ParticlePasses.arealight_expand = Bool(name="Expand", description="Expand Shader", default=False)
                                  
##################################################################################################################################
#                                                                                                                                #
#       Render Engine Preset Class                                                                                               #
#                                                                                                                                #
##################################################################################################################################

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
    shaderpaths = rmansettings.pathcollection.shaderpaths
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
        shaderpaths = rmansettings.pathcollection.shaderpaths
        
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
        s_path = "bpy.context.scene.renderman_settings.pathcollection.shaderpaths"
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
        
        if self.obj: rna_path = scene.objects[self.obj].renderman[getactivepass(scene).name]
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


def getactivepass(scene):
    maintain_beauty_pass(scene)
    renderman_settings = scene.renderman_settings
    passindex = renderman_settings.passes_index
    passes = renderman_settings.passes
    if passindex >= len(passes):
        scene.renderman_settings.passes_index = len(passes)-1
        passindex = renderman_settings.passes_index
    active_pass = passes[scene.renderman_settings.passes_index]
    return active_pass

#########################################################################################################
#                                                                                                       #
#       Operators                                                                                       #
#       (mainly for adding/removing and moving items of CollectionProperties)                           #
#                                                                                                       #
#########################################################################################################

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
    
        
def removeattrop(name, path):
    def invoke(self, context, event):
        p = eval(path)
        p = p[eval(path+'_index')]
        for grp in p.attribute_groups:
            p.attribute_groups.remove(0)
        return {'FINISHED'}
    
    oname = "Renderman_OT_"+name+"_attributes_remove_all"
    oidname = "attributes."+name+"_remove_all"
       
    type(bpy.types.Operator)(oname, ((bpy.types.Operator),), {  "bl_label" : "Remove All",
                                                                "bl_idname" : oidname,
                                                                "bl_description" : "remove all attributes",
                                                                "path" : String(),
                                                                "invoke" : invoke})

remops = {  "world" : "bpy.context.scene.renderman_settings.passes",
            "object" : "bpy.context.object.renderman",
            "particle" : "bpy.context.particle_system.settings.renderman"}
                
for op in remops:
    removeattrop(op, remops[op])

class Renderman_OT_remove_Attribute(bpy.types.Operator):
    bl_label = ""
    bl_idname = "attributes.remove"
    bl_description = "remove attribute"
    
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
        grp = grps[self.grp]
        
        if self.attr != "":
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
        pathcollection = context.scene.renderman_settings.pathcollection
        if self.add:
            pathcollection.shaderpaths.add().name = context.scene.renderman_settings.shaderpath
            checkshadercollection(context.scene)

        elif not self.add:
            index = pathcollection.shaderpathsindex
            pathcollection.shaderpaths.remove(index)

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

                
##################################################################################################################################
#   the fun par begins here:                                                                                                     #
##################################################################################################################################


#########################################################################################################
#                                                                                                       #
#       functions for keeping things up-to-date                                                         #
#                                                                                                       #
#########################################################################################################

def getname(raw, name, pass_name, scene):
    n = raw.replace('[scene]', scene.name)
    n = n.replace('[frame]', framepadding(scene))
    n = n.replace('[name]', name)
    n = n.replace('[pass]', pass_name)
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
        print("huhu")
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
    
    quant_presets = {   "8bit" : [0, 255, 0, 255],
                        "16bit" : [0, 65535, 0, 65535],
                        "32bit" : [0, 0, 0, 0]
                    }
                                        
    for display in current_pass.displaydrivers:
        disp_drv = display.displaydriver
        imagepath = os.path.join(path, current_pass.imagedir)

        extension = display.displaydriver
        display.filename = current_pass.name
        if display.filename_var:
            display.filename +='_'+display.var
        if current_pass.environment:
            display.filename += '_[dir][frame].'+extension
            if display.name.find(current_pass.name) != -1 or display.name.find("shadowmap") != -1:
                display.filename_var = False
        else:
            display.filename += '[frame].'+extension            
        display.file = os.path.join(imagepath, display.filename).replace('\\', '\\\\')
        
        if display.quantize_presets != "other":
            quant = quant_presets[display.quantize_presets]
            
            display.quantize_min = quant[0]
            display.quantize_max = quant[1]
            display.quantize_black = quant[2]
            display.quantize_white = quant[3]

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
        maintain_options(current_pass, scene)
    
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
            print("adding", master_group.name)
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
    if not "Beauty" in scene.renderman_settings.passes:
        renderman_settings.passes.add().name = "Beauty"
    beauty = renderman_settings.passes['Beauty']
    if not beauty.displaydrivers:
        adddisp(beauty)
        
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
                    light.data.shadow_buffer_clip_start = light.data.lightsettings.near_clipping
                    light.data.shadow_buffer_clip_end = light.data.lightsettings.far_clipping
            
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
        
def maintain(scene):
    pathcoll = scene.renderman_settings.pathcollection
    if pathcoll.shaderpaths and not pathcoll.shadercollection:
        checkshadercollection(scene)
    
    maintain_beauty_pass(scene)
    
    maintain_lists(scene)          

    for i, rpass in enumerate(scene.renderman_settings.passes):
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


#########################################################################################################
#                                                                                                       #
#       Export data functions                                                                           #
#                                                                                                       #
#########################################################################################################


#############################################
#                                           #
#   Convert Collection Property items       #
#   into RIB Code                           #
#                                           #
#############################################


def write_attrs_or_opts(groups, write, attr_opt, tab, scene):
    for group in groups:
        grp = {"Option" : group.options, "Attribute" : group.attributes}        
        if group.export:
            write(tab + attr_opt + ' \n\t"'+group.name+'" ')
            writeparms(grp[attr_opt], write, scene)                                          

def writeparms(path, write, scene):                                
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

def writeshaderparameter(parameterlist, write, scene):
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

def prepared_texture_file(file, scene):
    return os.path.splitext(file)[0]+"."+scene.renderman_settings.textureext

def prepare_texture(texturefile, parameters, scene):
    textool = scene.renderman_settings.textureexec
    args = ' "'+texturefile+'" "'+prepared_texture_file(texturefile, scene)+'"'+parameters
    os.system(textool+args)
    
    
def motionblur(motion_samples, current_pass, scene):
    shutterspeed = current_pass.shutterspeed        
    sampletime = [0]
    if current_pass.motionblur:
        for i in range(2, motion_samples+1):
            addtosample = round((shutterspeed/motion_samples)*i)
            sampletime.append(addtosample)        
    return shutterspeed, sampletime    


def ribarchive(rs, objname, folder, write, current_pass, scene, func, *args, **keys):
    rib_name = getname(rs.filename, objname, current_pass.name, scene)+'.rib'
    path = os.path.join(getdefaultribpath(scene), folder)
    if not os.path.exists(path):
        os.mkdir(path)
    rib_file = os.path.join(path, rib_name)
    if rs.own_file:
        if not rs.overwrite or not os.path.exists(rib_file):
            file = open(rib_file, "w")
            awrite = file.write
            write('ReadArchive "'+rib_file)
    else: awrite = write
    func(awrite, current_pass, scene, *args, **keys)
    try:
        file.close()
    except:
        pass

#############################################
#                                           #
#   Write Render Settings                   #
#   (the stuff before World Block begins)   #
#                                           #
#############################################

def prepare_textures(textures, scene):
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
                    
def writeSettings(write, current_pass, scene, camrot, dir = ""):
    print("write Scene Settings ...")

    if not current_pass.displaydrivers:
        nodisplay = True
    else:
        nodisplay = False
				
    if current_pass.name == "Beauty" and not current_pass.displaydrivers:
        adddisp(current_pass)
    render = scene.render
   

    respercentage = render.resolution_percentage

    if current_pass.camera_object != "":
        camera = scene.objects[current_pass.camera_object]
    else:
        camera = scene.camera

    if current_pass.shadow:
        light = scene.objects[current_pass.camera_object]    
        rmansettings = light.data.lightsettings    
        resx = rmansettings.shadow_map_resolution
        resy = resx
        x = resx
        y = resy

        nearclipping = rmansettings.near_clipping
        farclipping = rmansettings.far_clipping
        shift_x = 0
        shift_y = 0
    elif current_pass.environment:
        envtx = bpy.data.textures[current_pass.envname]
        envmap = envtx.environment_map
        resx = envtx.renderman.resolution
        resy = resx
        x = resx
        y = resy
        nearclipping = envmap.clip_start
        farclipping = envmap.clip_end
        shift_x = 0
        shift_y = 0
    else:            
        resx = math.trunc(render.resolution_x/100*respercentage)
        resy = math.trunc(render.resolution_y/100*respercentage)
        nearclipping = scene.camera.data.clip_start
        farclipping = scene.camera.data.clip_end
        shift_x = scene.camera.data.shift_x * 2
        shift_y = scene.camera.data.shift_y * 2

        x = render.resolution_x * render.pixel_aspect_x
        y = render.resolution_y * render.pixel_aspect_y
   
    if x >= y:
        asp_y = y/x
        asp_x = 1.0
    else:
        asp_x = x/y
        asp_y = 1.0

    aspectratio = render.pixel_aspect_x/render.pixel_aspect_y

    left = str(-asp_x+shift_x)
    right = str(asp_x+shift_x)

    top = str(-asp_y+shift_y)
    bottom = str(asp_y+shift_y)

    dof_distance = scene.camera.data.dof_distance
    if scene.camera.data.use_lens_length:
        focal_length = scene.camera.data.lens/100
    else:
        focal_length = scene.camera.data.focal_length
    fstop = scene.camera.data.fstop





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
    write_attrs_or_opts(current_pass.option_groups, write, "Option", "", scene)
    write('\n')
    
### Hider
    if current_pass.hider != "":
        write('Hider "'+current_pass.hider+'"')
        hider_parms = current_pass.hider_list[current_pass.hider].options
        writeparms(hider_parms, write, scene)
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
        writeCamera(write, current_pass, scene, camera, camrot)    


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

def objtransform(write, current_pass, scene, obj, mx = None):
    def writetransform(matrix):
        write('ConcatTransform [\t')    
        for i, row in enumerate(matrix):
            for val in row:
                write(" " + str(val))
            if not i == len(matrix)-1: write('\n\t\t\t\t\t')
        write(']\n')
    
    ## transformation blur    
    sampletime = []
    
    if mx: matrix = mx
    else: matrix = obj.matrix_world
        
    if obj and linked_pass(obj, current_pass).transformation_blur:
        motion_samples = linked_pass(obj, current_pass).motion_samples
        current_frame = scene.frame_current  
        shutterspeed, sampletime = motionblur(motion_samples, current_pass, scene)
    
        if current_pass.motionblur:
            write('MotionBegin[')
            for s in sampletime:
                write(str(s)+' ')
            write(']\n')
            for s in sampletime:
                scene.frame_set(current_frame - (shutterspeed - s))
                writetransform(matrix)
            write('MotionEnd\n')
    else: writetransform(matrix) 


def writeCamera(write, current_pass, scene, cam, camrot):
    degrees = math.degrees
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

    ##perspective blur
    sampletime = []
    if linked_pass(cam, current_pass).perspective_blur:
        motion_samples = linked_pass(cam, current_pass).motion_samples
        current_frame = scene.frame_current  
        shutterspeed, sampletime = motionblur(motion_samples, current_pass, scene)
    
        if current_pass.motionblur:
            write('MotionBegin[')
            for s in sampletime:
                write(str(s)+' ')
            write(']\n')
            for s in sampletime:
                scene.frame_set(current_frame - (shutterspeed - s))
                fov, perspective = checkoutFOVnPersp()
                writePerspective(fov, perspective)
        write('MotionEnd\n')
                   
    else:
        fov, perspective = checkoutFOVnPersp()
        writePerspective(fov, perspective)

    if not current_pass.environment:
        write("Scale 1 1 -1\n")
        
    ##Camera Transformation Blur
    def camtransblur(trans):
        sampletime = []
        if linked_pass(cam, current_pass).transformation_blur:
            motion_samples = linked_pass(cam, current_pass).motion_samples
            current_frame = scene.frame_current  
            shutterspeed, sampletime = motionblur(motion_samples, current_pass, scene)
        
            if current_pass.motionblur:
                write('MotionBegin[')
                for s in sampletime:
                    write(str(s)+' ')
                write(']\n')
                for s in sampletime:
                    scene.frame_set(current_frame - (shutterspeed - s))
                    writeCameraTransform(trans)
            write('MotionEnd\n')
                       
        else:
            writeCameraTransform(trans)
            
    camtransblur("RotX")
    camtransblur("RotY")
    camtransblur("RotZ")
    camtransblur("Translate")
              
    write("\n\n")
    print("Done")
    

#############################################
#                                           #
#  World Block                              #
#                                           #
#############################################


def writeWorld(write, current_pass, scene):    
    global_shader = current_pass.global_shader

    write("WorldBegin\n")
    write_attrs_or_opts(current_pass.attribute_groups, write, "Attribute", "", scene)
    write('\n\n')
    ### Custom Code
    
    if current_pass.world_code:
        for code in current_pass.world_code:
            write(code.name + '\n')
            
    writeshader(global_shader.surface_shader, global_shader.surface_shader_parameter, "Surface", write, scene)
    writeshader(global_shader.atmosphere_shader, global_shader.atmosphere_shader_parameter, "Atmosphere", write, scene)
            

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
            writeLight(write, current_pass, scene, light)
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
                writeObject(write, current_pass, scene, obj)
                writeParticles(write, current_pass, scene, path, obj)                 
    write("WorldEnd\n")


#############################################
#                                           #
#   Lights                                  #
#                                           #
#############################################


def writeLight(write, current_pass, scene, light):
    rmansettings = scene.renderman_settings
    al = False
    if light.type != 'LAMP' and light.active_material:
        mat = light.active_material
        alshader = linked_pass(mat, current_pass).arealight_shader
        if alshader != "":
            al = True
        
    global exported_children
    if (light.type == 'LAMP' or al) and not light.hide_render:
        if check_visible(light, scene):     
            print("write "+light.name)
            rotx = str(math.degrees(light.rotation_euler.x))
            roty = str(math.degrees(light.rotation_euler.y))
            rotz = str(math.degrees(light.rotation_euler.z))          
    
            write("\nAttributeBegin\n")      
            write_attrs_or_opts(linked_pass(light, current_pass).attribute_groups, write, "Attribute", "", scene)
            objtransform(light, write, current_pass, scene)
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
                exported_children.append(light.name)
            else:
                write('LightSource ')
                parameterlist = linked_pass(light.data, current_pass).light_shader_parameter
                write('"'+linked_pass(light.data, current_pass).shaderpath.replace("."+rmansettings.shaderbinary, "")+'" "'+light.name+'" ')         
                writeshaderparameter(parameterlist, write, scene)
                write('\n')

            write('AttributeEnd\n')                
            print("Done")


#############################################
#                                           #
#   Materials                               #
#                                           #
#############################################
def writeshader(shader, parms, type, write, scene):
    rmansettings = scene.renderman_settings
    if shader:
        shader = shader.replace("."+rmansettings.shaderbinary, "")
        write(type+' "'+shader+'" ')
        writeshaderparameter(parms, write, scene)
        write('\n')             

def writeMaterial(write, current_pass, scene, mat):
    rmansettings = scene.renderman_settings
    
    ## Color & Opacity Motion Blur
    def writeColor():  
        colR = linked_pass(mat, current_pass).color.r
        colG = linked_pass(mat, current_pass).color.g
        colB = linked_pass(mat, current_pass).color.b
        write('Color ['+str(colR)+' '+str(colG)+' '+str(colB)+']\n')
       
    def writeOpacity():
        opR, opG, opB = linked_pass(mat, current_pass).opacity    
        write('Opacity ['+str(opR)+' '+str(opG)+' '+str(opB)+']\n')
        


    def matblur(function, args=[]):     
        sampletime = [] 
        motion_samples = linked_pass(mat, current_pass).motion_samples
        current_frame = scene.frame_current  
        shutterspeed, sampletime = motionblur(motion_samples, current_pass, scene)
        
        if current_pass.motionblur:
            write('MotionBegin[')
            for s in sampletime:
                write(str(s)+' ')
            write(']\n')
            for s in sampletime:
                scene.frame_set(current_frame - (shutterspeed - s))
                if args: function(args[0], args[1], args[2], args[3], args[4])
                else: function()
            write('MotionEnd\n')
        else: 
            if args: function(args[0], args[1], args[2], args[3], args[4])
            else: function()

    if linked_pass(mat, current_pass).color_blur:                
        matblur(writeColor)
    else:
        writeColor()
        
    if linked_pass(mat, current_pass).opacity_blur:        
        matblur(writeOpacity)
    else:
        writeOpacity()

    surface_shader = linked_pass(mat, current_pass).surface_shader
    surface_parameter = linked_pass(mat, current_pass).surface_shader_parameter 
    displacement_shader = linked_pass(mat, current_pass).displacement_shader
    displacement_parameter = linked_pass(mat, current_pass).disp_shader_parameter 
    interior_shader = linked_pass(mat, current_pass).interior_shader
    interior_parameter = linked_pass(mat, current_pass).interior_shader_parameter
    exterior_shader = linked_pass(mat, current_pass).exterior_shader
    exterior_parameter = linked_pass(mat, current_pass).exterior_shader_parameter    
  
    if linked_pass(mat, current_pass).shader_blur:
        matblur(writeshader, args=[surface_shader, surface_parameter, "Surface", write, scene])
        matblur(writeshader, args=[displacement_shader, displacement_parameter, "Displacement", write, scene])
        matblur(writeshader, args=[interior_shader, interior_parameter, "Interior", write, scene])
        matblur(writeshader, args=[exterior_shader, exterior_parameter, "Exterior", write, scene])
    else:
        writeshader(surface_shader, surface_parameter, "Surface", write, scene)
        writeshader(displacement_shader, displacement_parameter, "Displacement", write, scene)
        writeshader(interior_shader, interior_parameter, "Interior", write, scene)
        writeshader(exterior_shader, exterior_parameter, "Exterior", write, scene)           
    return 'ReadArchive "'+matfilepath+'"\n'


#############################################
#                                           #
#   Particles                               #
#                                           #
#############################################


def writeParticles(write, current_pass, scene, obj):
    rmansettings = scene.renderman_settings
    pfiles = []

    if len(obj.particle_systems) > 0:
        for psystem in obj.particle_systems:
            if psystem.settings.type == 'EMITTER':
                filename = obj.name+'_'+psystem.name+framepadding(scene)+'.rib'
                particle_dir = os.path.join(getdefaultribpath(scene), rmansettings.particledir)
                
                if not os.path.exists(particle_dir): os.mkdir(particle_dir)
                
                part_path = os.path.join(particle_dir, filename)
                pfiles.append(part_path)
                
                file = open(part_path, "w")
                pwrite = file.write
                
                rman = linked_pass(psystem.settings, current_pass)
            
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
        
                    matrices = []
                    if linked_pass(psystem.settings, current_pass).motion_blur and current_pass.motionblur:
                        motion_samples = linked_pass(psystem.settings, current_pass).motion_samples
                        current_frame = scene.frame_current  
                        shutterspeed, sampletime = motionblur(motion_samples, current_pass, scene)
                    
                        for s in sampletime:
                            scene.frame_set(current_frame - (shutterspeed - s))
                            mx_set = []
                            for i, part in enumerate(psystem.particles):
                                mx_set.append(transform(part))
                            matrices.append([mx_set, scene.frame_current])                    
                    
                    for i, part in enumerate(psystem.particles):
                        if scene.frame_current >= part.birth_time:
                            pwrite('AttributeBegin\n')
                            
                            if len(matrices) > 1:
                                pwrite('MotionBegin[')
                                motion_samples = linked_pass(psystem.settings, current_pass).motion_samples
                                shutterspeed, sampletime = motionblur(motion_samples, current_pass, scene)
                                for s in sampletime:
                                    pwrite(str(s)+' ')
                                pwrite(']\n')
                            
                                for mx_set in matrices:
                                    objtransform(None, pwrite, current_pass, scene, mx = mx_set[0][i])
                                    pwrite('## '+str(mx_set[1])+'\n')
                                pwrite('MotionEnd\n')
                            else:
                                objtransform(None, pwrite, current_pass, scene, mx = transform(part))
                                                        
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
    
def writeObject(write, current_pass, scene, obj):
    if obj.type in ['MESH']:                

        mat = obj.active_material            
        
        write("##"+obj.name+'\n')
        if obj.parent:
            write('#child of '+obj.parent.name+'\n')
        write("AttributeBegin\n")
        write('Attribute "identifier" "name" ["'+obj.name+'"]\n')
        write_attrs_or_opts(linked_pass(obj, current_pass).attribute_groups, write, "Attribute", "", scene)

        if not current_pass.shadow:
            for item in linked_pass(obj, current_pass).light_list:
                if not item.illuminate:
                    write('Illuminate "'+item.lightname+'"')
                    write(' 0\n')
            
        objtransform(obj, write, current_pass, scene)
        rmansettings = scene.renderman_settings

        if mat: write(writeMaterial(write, current_pass, scene, mat).replace('\\', '\\\\'))
        
        if obj.data.show_double_sided:
            write('Sides 2\n')
            
        write('ShadingRate '+str(linked_pass(obj, current_pass).shadingrate)+'\n')
        
        export_type = obj.data.export_type
        meshpath = os.path.join(path, scene.renderman_settings.polydir)
        if export_type == 'ObjectInstance':
            write('ObjectInstance "'+obj.data.name+'"\n')
        else:
            export_object(write, current_pass, scene, obj, export_type)
        write("AttributeEnd\n\n")


#############################################
#                                           #
#   Mesh data (own RIB file)                #
#                                           #
#############################################


def writeMesh(write, current_pass, scene, mesh):
    subsurf = False
    ptype = mesh.data.primitive_type
    if ptype == 'SubdivisionMesh': subsurf = True
    smoothshade = False
    if not os.path.exists(path):
        os.mkdir(path)

    name = mesh.name

    meshfilename = name+framepadding(scene)+".rib"
    meshfilepath = os.path.join(path, meshfilename)

    meshfile = open(meshfilepath, "w")
    mwrite = meshfile.write
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
    
    
    if subsurf:
        mwrite('SubdivisionMesh "catmull-clark" ')
    elif ptype == 'PointsPolygons':
        mwrite("PointsPolygons ")
    elif ptype == 'Points':
        mwrite('Points\n')        
    vindices = []
    if ptype in ['SubdivisionMesh', 'PointsPolygons']:
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
        if vindex in vindices or ptype == 'Points':
            mwrite(str(n.normal[0])+' '+str(n.normal[1])+' '+str(n.normal[2])+' ')
    mwrite(']\n')
    
    #write Vertex Coordinates
    mwrite('"P" [')
    for vindex, v in enumerate(export_mesh.vertices):
        if vindex in vindices or ptype == 'Points': #make shure vertex is in a polygon, as otherwise renderman cries
            mwrite(str(v.co.x)+' '+str(v.co.y)+' '+str(v.co.z)+' ')                
    mwrite("]\n")

    p_scale = mesh.data.points_scale
    
    if ptype == "Points" and mesh.data.size_vgroup != "":
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
    meshfile.close()
    bpy.data.meshes.remove(export_mesh)
    
    return meshfilepath

#############################################
#                                           #
#   gather data and                         #
#   execute all export functions            #
#                                           #
#############################################

def export_object(write, current_pass, scene, obj, type = "ReadArchive"):    
    
    if type == 'ObjectInstance':
        inst = True
    else:
        inst = False
        
    if inst:
        global exported_instances
        if obj.data.name in exported_instances: return 0
        exported_instances.append(obj.data.name)
        write('ObjectBegin "'+obj.data.name+'"\n')
    
    ##deformation blur
    sampletime = []
    if linked_pass(obj, current_pass).deformation_blur:
        motion_samples = linked_pass(obj, current_pass).motion_samples
        current_frame = scene.frame_current  
        shutterspeed, sampletime = motionblur(motion_samples, current_pass, scene)
        
        if current_pass.motionblur:
            write('MotionBegin[')
            for s in sampletime:
                write(str(s)+' ')
            write(']\n')
            for s in sampletime:
                scene.frame_set(current_frame - (shutterspeed - s))
                fullath = writeMesh(write, current_pass, scene, obj)
                if type in ['ObjectInstance', 'ReadArchive']:
                    write('ReadArchive "'+fullpath.replace('\\', '\\\\')+'"\n')
                else:             
                    write('DelayedReadArchive "'+fullpath.replace('\\', '\\\\')+'" [')
                    for bound in obj.bound_box:
                        write([" ".join(str(b)) for b in bound]) 
                        write(" ")
                    write(']\n')              
        write('MotionEnd\n')
                   
    else:
        fullpath = writeMesh(write, current_pass, scene, obj)               
        if type in ['ObjectInstance', 'ReadArchive']:
            write('ReadArchive "'+fullpath.replace('\\', '\\\\')+'"\n')
        else:             
            write('DelayedReadArchive "'+fullpath.replace('\\', '\\\\')+'" [')
            for bound in obj.bound_box:
                for b in bound:
                    write(str(b)+' ')
            write(']\n')              
        
    if inst: write('ObjectEnd\n')
        
#########################            

            

def export(current_pass, path, scene):
    degrees = math.degrees
    if current_pass.environment:
        camera = scene.objects[current_pass.camera_object]
        envrots = [[180, 90, 180], [180, -90, 180], [90, -180, 180], [-90, -180, 180], [0, 0, 0], [0, 180, 0]]
#        pointrots = [[0, -90, 0], [0, 90, 0], [90, 0, 0], [-90, 0, 0], [0, 0, 0], [0, 180, 0]]
        envdirections = ["_px", "_nx", "_py", "_ny", "_pz", "_nz"]
        for i, dir in enumerate(envdirections):
            name = current_pass.name+dir+framepadding(scene)+".rib"                
            camrot = envrots[i]
            filepath = os.path.join(path, name)
            file = open(filepath, "w")
            write = file.write
            writerib(write, current_pass, scene, camera, camrot, dir = dir)
            file.close()
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
        name = current_pass.name+framepadding(scene)
        camrot = [degrees(rot[0]), degrees(rot[1]), degrees(rot[2])]    

        filename = name+".rib"
        file = open(os.path.join(path, filename), "w")   
        write = file.write
        writerib(write, current_pass, scene, camera, camrot, dir = "")
        file.close()


def getfinalpath(subfolder, scene):
    return os.path.join(getdefaultribpath(scene), subfolder)

    #Write RIB Files
def writerib(write, current_pass, scene, camera, camrot, dir = ""):
    rm = scene.renderman_settings
    global exported_children
    exported_children = []
    for obj in scene.objects:
        if obj.type in ['MESH']:
            if obj.data.export_type == 'ObjectInstance':
                export_object(write, current_pass, scene, obj, type = obj.data.export_type)
    
    rm = scene.renderman_settings
    rs = rm.settings_rib_structure

    ribarchive( rs,
                "",
                rm.settingsdir,
                write,
                current_pass,
                scene,
                writeSettings,
                camrot,
                dir=dir)
    
    rs = rm.world_rib_structure
    ribarchive( rs,
                "",
                current_pass,
                rm.worlddir,
                write,
                current_pass,
                scene,
                writeWorld)

def invoke_renderer(rib, scene):
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
    if rndr != "":
        maintain(scene)
        path = getdefaultribpath(scene)
                                             
        active_pass = getactivepass(scene)

        global exported_children, exported_instances


        if scene.renderman_settings.exportallpasses:
            for item in scene.renderman_settings.passes:
                imagefolder = os.path.join(path, item.imagedir)
                checkForPath(imagefolder)            
                ribfilename = item.name+framepadding(scene)+".rib"
                rib = os.path.join(path, ribfilename)

                if item.displaydrivers:
                    image = item.displaydrivers[0].file   
                elif preview_scene and not item.displaydrivers:
                    adddisp(item)    
                    image = item.displaydrivers[0].file                                 

                exported_children = exported_instances = []

                export(item, path, scene)

                if not scene.renderman_settings.exportonly:
                    if rndr != "" and not item.environment:                            
                        start_render(rndr, rib, item, scene)                    
        else:

            exported_children = exported_instances = []


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
#            global exported_children
#            global exported_env_directions
#            exported_env_directions = 0
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
#                    exported_children = []
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
#                exported_children = []
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
        maintain(scene)
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
        if path.renderman_index < len(path.renderman) >= 0:
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

class Renderman_PT_WorldPanel(WorldButtonsPanel, bpy.types.Panel):
    bl_label = "General World Settings"
    
    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        scene = context.scene
        layout = self.layout
        active_pass = getactivepass(scene)
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
        maintain(scene)
        active_pass = getactivepass(scene)
        layout = self.layout
        pathcollection = context.scene.renderman_settings.pathcollection

        row = layout.row(align = True)
        row.prop_search(active_pass.global_shader, "surface_shader", pathcollection, "shadercollection", text="", icon='MATERIAL')
        row.operator("refreshshaderlist", text="", icon="FILE_REFRESH")
        
        layout.label(text=shader_info(active_pass.global_shader.surface_shader, active_pass.global_shader.surface_shader_parameter, scene))
        checkshaderparameter("worlds", active_pass, active_pass.global_shader.surface_shader, active_pass.global_shader.surface_shader_parameter, scene)

        matparmlayout(active_pass.global_shader.surface_shader_parameter, layout, bpy.data)

                            
class World_PT_AtmosphereShaderPanel(bpy.types.Panel, WorldButtonsPanel):
    bl_label = "Atmosphere Shader"
    
    COMPAT_ENGINES = {'RENDERMAN'}

    def draw(self, context):
        scene = context.scene
        #maintain(scene)
        active_pass = getactivepass(scene)
        layout = self.layout
        pathcollection = context.scene.renderman_settings.pathcollection

        row = layout.row(align = True)
        row.prop_search(active_pass.global_shader, "atmosphere_shader", pathcollection, "shadercollection", text="", icon='MATERIAL')
        row.operator("refreshshaderlist", text="", icon="FILE_REFRESH")
        
        layout.label(text=shader_info(active_pass.global_shader.atmosphere_shader, active_pass.global_shader.atmosphere_shader_parameter, scene))
        checkshaderparameter("worlda", active_pass, active_pass.global_shader.atmosphere_shader, active_pass.global_shader.atmosphere_shader_parameter, scene)

        matparmlayout(active_pass.global_shader.atmosphere_shader_parameter, layout, bpy.data)


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
        defaults = {"Settings" : "[scene]_[pass][frame]",
                    "World" : "[scene]_[pass][frame]"}
                
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
        
    def draw(self, context):
        rm = context.scene.renderman_settings
        
        types = {   "Settings" : rm.settings_rib_structure,
                    "World" : rm.world_rib_structure}
                        
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

        if renderman_settings.passes:
            if len(renderman_settings.passes) == 1 and not renderman_settings.searchpass:
                renderman_settings.passes_index = 0
            elif renderman_settings.searchpass:
                for i, passes in enumerate(renderman_settings.passes):
                    if passes.name == renderman_settings.searchpass:
                        renderman_settings.passes_index = i
                        renderman_settings.searchpass = ""        

        col = row.column(align=True)

        col.menu("Renderman_MT_addPassMenu", icon="ZOOMIN")
        col.operator("rempass", text="", icon="ZOOMOUT")
        col.operator("movepass", icon='TRIA_UP', text="").direction = "up"
        col.operator("movepass", icon='TRIA_DOWN', text="").direction = "down"
        row = layout.row(align=True)
        row.prop(active_pass, "name", text="")
        row.prop(active_pass, "exportanimation", text="Animate Pass")

        if renderman_settings.passes:
            row = layout.row(align=True)        
            row = layout.row()
            row.prop(active_pass, "imagedir", text="Image Folder")

class Renderman_PT_QualityPanel(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Quality"
    
    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        maintain(scene)        
        active_pass = getactivepass(scene)
        row = layout.row(align=True)
        row.prop(active_pass.pixelfilter, "filterlist", text="")
        row.prop(active_pass, "pixelsamples_x", text="X Samples")                                                                       
        row.prop(active_pass, "pixelsamples_y", text="Y Samples")
        if active_pass.pixelfilter.filterlist == "other":
            row.prop(active_pass.pixelfilter, "customfilter")
        row=layout.row(align=True)                            
        row.prop(active_pass.pixelfilter, "filterwidth", text = "Filter width")
        row.prop(active_pass.pixelfilter, "filterheight", text = "Filter height")

class Renderman_PT_MotionBlurPanel(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Motion Blur"
    
    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        #maintain()
        layout = self.layout
        scene = context.scene
        current_pass = getactivepass(scene)
        row = layout.row()
        row.prop(current_pass, "motionblur")
        row = layout.row()
        row.enabled = current_pass.motionblur
        row.prop(current_pass, "shutterspeed")
    
    
class RENDERMANRender_PT_OptionsPanel(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Options"
    bl_idname = "options"
    bl_default_closed = True

    COMPAT_ENGINES = {'RENDERMAN'}
    

    def draw(self, context):
        #maintain()
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
        #maintain()
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
            layout.operator("adddisplay", text="", icon="ZOOMIN")
            for display_index, display in enumerate(active_pass.displaydrivers):
                main_box = layout.box()
                row = main_box.row(align=True)
#                col = main_row.column()
#                row = col.row(align=True)
#                row.label(text="", icon = "FILE_TICK" if display.send else "BLANK1")                  
#                row.operator("display.send", icon="IMAGE_COL", text="").display = display.name
#                if display.displaydriver == "framebuffer":
#                    row.enabled = False
#                else:
#                    row.enabled = True                    
#                row = main_row                                                 
                row.prop(display, "expand", text="", icon="TRIA_DOWN" if display.expand else "TRIA_RIGHT", emboss=False)
                row.prop(display, "name", text="")
                row.prop_search(display, "displaydriver", renderman_settings, "displays", text="", icon="FILE_SCRIPT")
                row.prop_search(display, "var", renderman_settings, "var_collection", text="", icon="RENDER_RESULT")
                row.operator("remdisplay", text="", icon="ZOOMOUT").index = display_index
                if display.expand:
                    row = main_box.row()
                    row.prop(display, "filename_var", text="Variable")
                    row.label(text=display.filename)
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
        #maintain(scene)


class Renderman_PT_CustomSceneCodePanel(bpy.types.Panel, RenderButtonsPanel):
    bl_label = "Custom Scene RIB Code"
    
    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        scene = context.scene
        rmansettings = scene.renderman_settings
        active_pass = getactivepass(scene)
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
        maintain(scene)
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
        maintain(scene)

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
        #maintain(context.scene)
        m = context.material
        mat = m.renderman[m.renderman_index]
        row = layout.row()
        col = row.column(align=True)
        row.enabled = getactivepass(context.scene).motionblur
        col.prop(mat, "color_blur")
        col.prop(mat, "opacity_blur")
        col.prop(mat, "shader_blur")
        col = row.column()
        col.prop(mat, "motion_samples")
        


class RENDERMANMaterial_PT_SurfaceShaderPanel(MaterialButtonsPanel, bpy.types.Panel):
    bl_label = "Surface Shader"
    bl_idname = "SurfaceShaderPanel"

    COMPAT_ENGINES = {'RENDERMAN'}
    

    def draw(self, context):
        scene = context.scene
        #maintain(scene)
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
        #maintain(scene)
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
        #maintain(scene)
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
        #maintain(scene)
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
        #maintain(scene)
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
        maintain(context.scene)
        layout = self.layout
        light = context.object
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
            layout.prop(rmansettings, "shadow_map_resolution", text="Shadow Map Size")
            layout.prop(rmansettings, "near_clipping", text="Near Clipping")
            layout.prop(rmansettings, "far_clipping", text="Far Clipping")              
    

 




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
    bl_label=""

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (context.object) and (rd.engine in cls.COMPAT_ENGINES) and not (context.object.type in ["LAMP", "CAMERA"])
    
class ObjectAttributesPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_label=""

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (context.object) and (rd.engine in cls.COMPAT_ENGINES) and not (context.object.type in ["CAMERA"])    

obp = 'bpy.context.object'

onp = obp+'.name'
ormp = obp+'.renderman['+obp+'.renderman_index]'

passes_linking_panel("object", "bpy.context.object", ObjectAttributesPanel)

class Object_PT_MotionBlurPanel(ObjectButtonsPanel, bpy.types.Panel):
    bl_label ="Motion Blur"
    
    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        scene = context.scene
        #maintain(scene)
        obj = context.object
        try:
            rman = obj.renderman[obj.renderman_index]
        except IndexError:
            pass
    
        layout = self.layout
        row = layout.row()
        col = row.column()
        col.enabled = getactivepass(scene).motionblur
        col.prop(rman, "transformation_blur")
        col.prop(rman, "deformation_blur")
        col.prop(rman, "motion_samples")

class Mesh_PT_IlluminatePanel(ObjectButtonsPanel, bpy.types.Panel):
    bl_label="Renderman Light Linking"

    COMPAT_ENGINES = {'RENDERMAN'}

    def draw(self, context):
        scene = context.scene
        maintain(scene)
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
        #maintain(scene)
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

    
class Camera_PT_RendermanPassesPanel(CameraDataButtonsPanel, bpy.types.Panel):
    bl_label="Passes"    
    
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

        if renderman_settings.passes:
            if len(renderman_settings.passes) == 1 and not renderman_settings.searchpass:
                renderman_settings.passes_index = 0
            elif renderman_settings.searchpass:
                for i, passes in enumerate(renderman_settings.passes):
                    if passes.name == renderman_settings.searchpass:
                        renderman_settings.passes_index = i
                        renderman_settings.searchpass = "" 
    

class Renderman_PT_CameraLens(CameraDataButtonsPanel, bpy.types.Panel):
    bl_label = "Renderman Lens Settings"
    bl_idname = "rendermanlens"

    COMPAT_ENGINES = {'RENDERMAN'}
    
    def draw(self, context):
        scene = context.scene
        maintain(scene)
        camera = scene.camera
        layout = self.layout
        row = layout.row(align=True)
        row.prop(camera.data, "type", text="")

        row.prop(camera.data, "lens_unit", text = "")
        if camera.data.lens_unit == "MILLIMETERS":
            row.prop(camera.data, "lens", text="")
        else:
            row.prop(camera.data, "angle", text="")
        row = layout.row()
        col = row.column(align=True)
        col.prop(camera.data, "clip_start")
        col.prop(camera.data, "clip_end")
        col = row.column(align=True)
        col.prop(camera.data, "shift_x")
        col.prop(camera.data, "shift_y")
        
        row = layout.row()
        row.prop(camera.data, "depthoffield", text="Depth Of Field")
        row = layout.row()
        row.enabled = camera.data.depthoffield
        col = row.column(align=True)
        col.prop(camera.data, "dof_distance", text="Focus Distance")
        col.prop(camera.data, "fstop")
        col.prop(camera.data, "use_lens_length")
        row = layout.row()
        row.enabled = camera.data.depthoffield and not camera.data.use_lens_length
        row.prop(camera.data, "focal_length")

        row = layout.row()
        col = row.column()
        col.enabled = getactivepass(scene).motionblur
        col.prop(camera.renderman[camera.renderman_index], "transformation_blur")
        #col.prop(camera.renderman[camera.renderman_index], "perspective_blur")
        row = col.row()
        transformation_blur = camera.renderman[camera.renderman_index].transformation_blur
        perspective_blur = camera.renderman[camera.renderman_index].perspective_blur
        row.enabled = perspective_blur or transformation_blur
        row.prop(camera.renderman[camera.renderman_index], "motion_samples")


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
        pathcollection = context.scene.renderman_settings.pathcollection
        
        psystem = context.particle_system
        rman = psystem.settings.renderman[psystem.settings.renderman_index]
        obj = context.object

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
        maintain(context.scene)
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
        maintain(context.scene)
        layout = self.layout
        layout.menu("Renderman_MT_object_specials")

##################################################################################################################################
        
def register():
    bpy.types.VIEW3D_MT_object_specials.append(draw_obj_specials_rm_menu)
    

def unregister():
    bpy.types.VIEW3D_MT_object_specials.remove(draw_obj_specials_rm_menu)

if __name__ == "__main__":
    register()