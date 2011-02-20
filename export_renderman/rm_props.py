
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
from math import *

RM_FILTER =(("box", "Box", "Box Filter"),
            ("gaussian", "Gaussian", "Gaussian Filter"),
            ("sinc", "Sinc", "Cube Filter"),
            ("triangle", "Triangle", "Triangle Filter"),
            ("catmull-rom", "Catmull-Rom", ""),
            ("blackman-harris", "Blackman-Harris", ""),
            ("mitchell", "Mitchell", ""),
            ("bessel", "Bessel", ""),
            ("other", "Other", "Custom Filter"))

##################################################################################################################################
#Define classes for Collection and Pointer properties

class passes(bpy.types.IDPropertyGroup):            #passes
    pass

class DisplayCollection(bpy.types.IDPropertyGroup):         #Display Drivers
    pass

class Collection(bpy.types.IDPropertyGroup):            #All Variable Properties: Shader Parameters, Options, Attributes
    pass

class Shader(bpy.types.IDPropertyGroup):            #Shader Settings Passes
    pass

class ObjectParameters(bpy.types.IDPropertyGroup):            #Object Attributes
    pass

class RendermanSceneSettings(bpy.types.IDPropertyGroup):            #Renderman Scene Settings
    pass

class Paths(bpy.types.IDPropertyGroup):             #Shader Paths
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

class ParticlePasses(bpy.types.IDPropertyGroup):
    pass

class Empty(bpy.types.IDPropertyGroup):
    pass

class EmptyPasses(bpy.types.IDPropertyGroup):
    pass

class RibStructureBase(bpy.types.IDPropertyGroup):
    pass

class RibStructure(bpy.types.IDPropertyGroup):
    pass

class RendermanCamera(bpy.types.IDPropertyGroup):
    pass

class OutputImages(bpy.types.IDPropertyGroup):
    pass

class ClientParameters(bpy.types.IDPropertyGroup):
    pass

class VarCollections(bpy.types.IDPropertyGroup):
    type_ = bpy.props.StringProperty()

class ImageProcessing(bpy.types.IDPropertyGroup):
    
    process = bpy.props.BoolProperty(    name="Process",
                                        default=False,
                                        description="run Texture processing tool to convert into rendermans intern texture format")
                                        
    overwrite = bpy.props.BoolProperty(name="Overwrite", description="Overwrite existing", default=False)
    
    output = bpy.props.StringProperty(name="Output",
                                  description="name of Image Output")
    
    default_output = bpy.props.BoolProperty(name="Default",
                                            description="Use Default Output",
                                            default=True)
    
    filter = bpy.props.EnumProperty(   name="Filter",
                                        default="box",
                                        items=RM_FILTER,
                                        description="Filter to use when converting the image")
    
    custom_filter = bpy.props.StringProperty(name = "Custom Filter")
    
    width = bpy.props.FloatProperty(     name ="Width",
                                        min = 0,
                                        max = 100,
                                        default = 1,
                                        description = "Filter Width")
    
    swidth = bpy.props.FloatProperty(    name = "s Width",
                                        min = 0,
                                        max = 100,
                                        default = 1,
                                        description = "Filter Width in s direction")
    
    twidth = bpy.props.FloatProperty(    name = "t Width",
                                        min = 0,
                                        max = 100,
                                        default = 1,
                                        description = "Filter Width in t direction")
    
    stwidth = bpy.props.BoolProperty(    name = "st Width",
                                        default = False,
                                        description = "Specify Filter Width in s and t direction separately")
            
    envcube = bpy.props.BoolProperty(name="EnvCube", description="make cubeface environment", default=False)
    
    fov = bpy.props.FloatProperty(name="FOV", description="Field of View for Cube Face Environment", min=0.01, max=360, default=radians(90), subtype="ANGLE")
    
    shadow = bpy.props.BoolProperty(name="Shadow", description="Make Shadwo", default=False)
    
    custom_parameter = bpy.props.StringProperty(name="Custom Parameter")

class CustomCodeCollection(bpy.types.IDPropertyGroup):
    foreach = bpy.props.BoolProperty(name="For Each Environment Direction",
                                     description="Export Code for each environment direction or only for the last",
                                     default=False)
    
    position = bpy.props.EnumProperty(name="Position", items=(("begin", "Begin", ""),
                                                              ("end", "End", "")))
    
    world_position = bpy.props.EnumProperty(name="Position", items=(("begin", "Begin", ""),
                                                                    ("end_inside", "End (Inside World Block)", ""),
                                                                    ("end_outside", "End (Outside World Block)", "")))
    
    particle_position = bpy.props.EnumProperty(name="Position", items=(("begin", "Begin", ""),
                                                                        ("end", "End", ""),
                                                                        ("begin_data", "Begin (Data)", ""),
                                                                        ("end_data", "End (Data)", "")))
    
    parameter = bpy.props.PointerProperty(type=Collection)
        
    image_prcessing = bpy.props.PointerProperty(type=ImageProcessing)
    
    all_dirs = bpy.props.BoolProperty(name="All Directions",
                                      description="Convert file name input into 6 files"
                                                   + "replacing [dir] with the direction",
                                      default=True)
    
    makeshadow = bpy.props.BoolProperty(name="MakeShadow (RIB)",
                                        default=False,
                                        description="Convert Image into Shadowmap")
    
    makecubefaceenv = bpy.props.BoolProperty(name="MakeCubeFaceEnvironment (RIB)",
                                    default=False,
                                    description="Convert Images into Cubic Environment")
    
    output = bpy.props.StringProperty(name="Output",
                                  description="name of Image Output")
    
    default_output = bpy.props.BoolProperty(name="Default",
                                            description="Use Default Output",
                                            default=True)
    
    filter = bpy.props.EnumProperty(   name="Filter",
                                        default="box",
                                        items=RM_FILTER,
                                        description="Filter to use when converting the image")
    
    custom_filter = bpy.props.StringProperty(name = "Custom Filter")
    
    width = bpy.props.FloatProperty(     name ="Width",
                                        min = 0,
                                        max = 100,
                                        default = 1,
                                        description = "Filter Width")
    
    swidth = bpy.props.FloatProperty(    name = "s Width",
                                        min = 0,
                                        max = 100,
                                        default = 1,
                                        description = "Filter Width in s direction")
    
    twidth = bpy.props.FloatProperty(    name = "t Width",
                                        min = 0,
                                        max = 100,
                                        default = 1,
                                        description = "Filter Width in t direction")
    
    stwidth = bpy.props.BoolProperty(    name = "st Width",
                                        default = False,
                                        description = "Specify Filter Width in s and t direction separately")
    
    blur = bpy.props.FloatProperty(name="Blur", min=0, max=1000, default=1.0)
        
    fov = bpy.props.FloatProperty(name="FOV", description="Field of View for Cube Face Environment", min=0.01, max=360, default=radians(90), subtype="ANGLE")

#########################################################################################################
#                                                                                                       #
#       Create Properties                                                                               #
#                                                                                                       #
#########################################################################################################

ClientParameters.client = bpy.props.StringProperty()

ClientParameters.output = bpy.props.StringProperty()

ClientParameters.preset = bpy.props.StringProperty()

ClientParameters.render_pass = bpy.props.StringProperty()

ClientParameters.pass_name = bpy.props.StringProperty()

ClientParameters.request_pass = bpy.props.StringProperty()

ClientParameters.index = bpy.props.IntProperty(min = 0, max = 100, default = 0)

RendermanCamera.respercentage = bpy.props.IntProperty(min=1, max=100, default=100, subtype='PERCENTAGE', name="Resolution Percentage")

RendermanCamera.resx = bpy.props.IntProperty(min = 1, max = 100000, default = 1920, name = "X Resolution")

RendermanCamera.resy = bpy.props.IntProperty(min = 1, max = 100000, default = 1080, name = "Y Resolution")

RendermanCamera.aspectx = bpy.props.FloatProperty(min = 1, max = 10000, default = 1, name ="Aspect X")

RendermanCamera.aspecty = bpy.props.FloatProperty(min = 1, max = 10000, default = 1, name ="Aspect Y")

RendermanCamera.square = bpy.props.BoolProperty(name = "Square", default = False, description = "Same Value for X and Y Resolution")

RendermanCamera.shift_x = bpy.props.FloatProperty(default = 0, name="Shift X")

RendermanCamera.shift_y = bpy.props.FloatProperty(default = 0, name="Shift Y")

RendermanCamera.fov = bpy.props.FloatProperty(default = 90, min=0.001, max= 360, name="FOV")

RendermanCamera.depthoffield = bpy.props.BoolProperty(default = False,
                        name = "DOF")
                        
RendermanCamera.dof_distance = bpy.props.FloatProperty(default = 1, name = "DOF Distance")

RendermanCamera.focal_length = bpy.props.FloatProperty(min=0,
                        default=0,
                        name="Focal Length")

RendermanCamera.fstop = bpy.props.FloatProperty(min=0,
                        default=2.8,
                        name="F-Stop")

RendermanCamera.use_lens_length = bpy.props.BoolProperty(default=True,
                        name="Use Camera Lens")
                        
RendermanCamera.perspective_blur = bpy.props.BoolProperty(   name="perspective_blur",
                                            default = False,
                                            description = "apply motion blur to the viewing angle of this camera")
                                            
RendermanCamera.transformation_blur = bpy.props.BoolProperty(name="transformation Blur",
                                            default=False,
                                            description="apply motion blur to the transformation of this object")                     

RendermanCamera.near_clipping = bpy.props.FloatProperty(min = 0,
                                    max = 1000000,
                                    default = 1)

RendermanCamera.far_clipping = bpy.props.FloatProperty(min = 0,
                                    max = 1000000,
                                    default = 30)


### Rib Structure Settings
RibStructure.own_file = bpy.props.BoolProperty(default = True, name = "Own File", description="write into own RIB Archive")

RibStructure.filename = bpy.props.StringProperty(name="File", default="", subtype = 'FILE_PATH')

RibStructure.default_name = bpy.props.BoolProperty(default = True, name = "Default Name", description = "Default RIB Archive Name")

RibStructure.overwrite = bpy.props.BoolProperty(default = True, name = "Overwrite", description="overwrite existing files")

RibStructure.expand = bpy.props.BoolProperty(default=False, name="Expand", description="Expand Properties")

RibStructure.folder = bpy.props.StringProperty(default = "")

Collection.parametertype = bpy.props.EnumProperty(items=(
                                ("string", "String", "String Parameter"),
                                ("float", "Float", "Float Parameter"),
                                ("int", "Integer", "Integer Parameter"),
                                ("color", "Color", "Color Parameter"),
                                ),
                                default="string",
                                name = "Parameter Type",
                                description = "Type of Parameter")


Collection.textparameter = bpy.props.StringProperty()

Collection.input_type = bpy.props.EnumProperty(name = "Input Type",
                                               description = "Where to look for input",
                                               items = (("display", "Display", ""),
                                                        ("texture", "Texture", ""),
                                                        ("string", "String", "")),
                                               default = "string")
                            
Collection.export = bpy.props.BoolProperty(default=True, description="export object attribute", options={'ANIMATABLE'})

Collection.preset_include = bpy.props.BoolProperty(default = True, description = "include Attribute in preset", options={'ANIMATABLE'})

Collection.rib_name = bpy.props.StringProperty()                          

Collection.float_one = bpy.props.FloatVectorProperty( precision = 4,
                                    size = 1,
                                    options={'ANIMATABLE'})

Collection.float_two = bpy.props.FloatVectorProperty( default=(0.0, 0.0),
                                    precision = 4,
                                    size = 2,
                                    options={'ANIMATABLE'})
                                
Collection.float_three = bpy.props.FloatVectorProperty(   default=(0.0, 0.0, 0.0),
                                        precision = 4,
                                        size = 3,
                                        options={'ANIMATABLE'})
                                
Collection.int_one = bpy.props.IntVectorProperty(     step=100,
                                    size=1,
                                    options={'ANIMATABLE'})
                                
Collection.int_two = bpy.props.IntVectorProperty( step=100,
                                size=2,
                                options={'ANIMATABLE'})
                                
Collection.int_three = bpy.props.IntVectorProperty(   step=100,
                                    size=3,
                                    options={'ANIMATABLE'})                                                                                                                                                                

Collection.colorparameter = bpy.props.FloatVectorProperty(name="Color Parameter",
                                        description="Color Parameter",
                                        subtype='COLOR',
                                        precision = 4,
                                        step = 0.01,
                                        min=0,
                                        max = 1,
                                        default = (0, 0, 0),
                                        options={'ANIMATABLE'})

Collection.parameterindex = bpy.props.IntProperty(default=-1,
                                min=-1,
                                max=1000,
                                options={'ANIMATABLE'})
                        
Collection.vector_size = bpy.props.IntProperty(   default = 1,
                                min = 1,
                                max = 3,
                                options={'ANIMATABLE'})                        

Collection.collection = bpy.props.CollectionProperty(type = Collection)

Collection.free = bpy.props.BoolProperty(default = False)

Collection.type = bpy.props.StringProperty()

#############################################
#                                           #
#   Render Properties                       #
#                                           #
#############################################

RendermanSceneSettings.shellscript_create = bpy.props.BoolProperty(name="Create shell script", description="Create batchfile/shellscript to start rendering later", default=False)

RendermanSceneSettings.shellscript_append = bpy.props.BoolProperty(name="Append", description="Append to existing file", default=False)

RendermanSceneSettings.shellscript_file = bpy.props.StringProperty(name="Script File", description="Path to the script file", subtype="FILE_PATH")

RendermanSceneSettings.bi_render = bpy.props.BoolProperty(name="Use BI Render Op", description="Use Blender's default render Operator(may crash more likely. Save often!)", default=True)

passes.export = bpy.props.BoolProperty(name="Export", description="Export this Render Pass", default=True)

passes.client = bpy.props.StringProperty()

passes.requested = bpy.props.BoolProperty(default = False)

passes.displaydrivers = bpy.props.CollectionProperty(type=DisplayCollection)

passes.displayindex = bpy.props.IntProperty(  default = -1,
                            min=-1,
                            max=1000)

RendermanSceneSettings.requests = bpy.props.CollectionProperty(type = ClientParameters)

RendermanSceneSettings.displays = bpy.props.CollectionProperty(type=DisplayDrivers)

RendermanSceneSettings.display_index = bpy.props.IntProperty(min = -1, max = 1000, default = -1)

RendermanSceneSettings.output_images = bpy.props.CollectionProperty(type = OutputImages)

passes.output_images = bpy.props.CollectionProperty(type = OutputImages)

OutputImages.render_pass = bpy.props.StringProperty()
                                            
RendermanSceneSettings.hider_list = bpy.props.CollectionProperty(type=Hider)

passes.hider_list = bpy.props.CollectionProperty(type=Hider)

RendermanSceneSettings.hider_list_index = bpy.props.IntProperty(  min=-1,
                                                max=10000,
                                                default=-1)
                                    
RendermanSceneSettings.default_hider = bpy.props.StringProperty()                                    

Hider.options = bpy.props.CollectionProperty(type=Collection)

passes.hider = bpy.props.StringProperty()

RendermanSceneSettings.rib_structure = bpy.props.PointerProperty(type=RibStructureBase)

RibStructureBase.frame = bpy.props.PointerProperty(type=RibStructure)

RibStructureBase.render_pass = bpy.props.PointerProperty(type = RibStructure)

RibStructureBase.settings = bpy.props.PointerProperty(type = RibStructure)

RibStructureBase.world = bpy.props.PointerProperty(type = RibStructure)

RibStructureBase.object_blocks = bpy.props.PointerProperty(type = RibStructure)

RibStructureBase.objects = bpy.props.PointerProperty(type = RibStructure)

RibStructureBase.lights = bpy.props.PointerProperty(type = RibStructure)

RibStructureBase.particles = bpy.props.PointerProperty(type = RibStructure)

RibStructureBase.particle_data = bpy.props.PointerProperty(type = RibStructure)

RibStructureBase.meshes = bpy.props.PointerProperty(type = RibStructure)

RibStructureBase.materials = bpy.props.PointerProperty(type = RibStructure)
                                            
#############################################
#                                           #
#   Display Properties                      #
#                                           #
#############################################

Collection.expand = bpy.props.BoolProperty(default = False, name = "Expand")

DisplayDrivers.custom_parameter = bpy.props.CollectionProperty(type = Collection)

DisplayCollection.send = bpy.props.BoolProperty(default = False)

DisplayCollection.export = bpy.props.BoolProperty(default=True, name="Export", description="Export this display")

DisplayCollection.custom_options = bpy.props.CollectionProperty(type = Collection)

Collection.use_var = bpy.props.BoolProperty(default=False, name = "Use Var", description="use name of output variable as value")

DisplayCollection.default_name = bpy.props.BoolProperty(default = True, name = "Default", description="Default Filename")                                          

RendermanSceneSettings.var_collection = bpy.props.CollectionProperty( name="Output Value",
                                                    type=VarCollections
                                                    )
                               
DisplayCollection.var = bpy.props.StringProperty(default="rgba")                               
                                
DisplayCollection.displaydriver = bpy.props.StringProperty()                                

DisplayCollection.file = bpy.props.StringProperty()

DisplayCollection.filename = bpy.props.StringProperty()

DisplayCollection.raw_name = bpy.props.StringProperty()

DisplayCollection.quantize_min = bpy.props.IntProperty(min=0, max=100000, default=0, description = "min")

DisplayCollection.quantize_max = bpy.props.IntProperty(min=0, max=100000, default=0, description = "max")

DisplayCollection.quantize_black = bpy.props.IntProperty(min=0, max=100000, default=0, description = "black")

DisplayCollection.quantize_white = bpy.props.IntProperty(min=0, max=100000, default=0, description = "white")

DisplayCollection.quantize_presets = bpy.props.EnumProperty(items=    (
                                                                        ("8bit", "8 bit", ""),
                                                                        ("16bit", "16 bit", ""),
                                                                        ("32bit", "32 bit", ""),
                                                                        ("other", "other", "")
                                                                    ),
                                                                    default = "16bit",
                                                                    name = "Quantization")

DisplayCollection.processing = bpy.props.PointerProperty(type=ImageProcessing)

DisplayCollection.expand = bpy.props.BoolProperty(default=False)

DisplayCollection.quantize_expand = bpy.props.BoolProperty(default=False)

DisplayCollection.exposure_expand = bpy.props.BoolProperty(default=False)

DisplayCollection.processing_expand = bpy.props.BoolProperty(default=False)

DisplayCollection.custom_expand = bpy.props.BoolProperty(default=False)

passes.pixelsamples_x = bpy.props.IntProperty(name="PixelSamples",
                    default = 2,
                    min = 1,
                    max = 100)

passes.pixelsamples_y = bpy.props.IntProperty(name="PixelSamples",
                    default = 2,
                    min = 1,
                    max = 100)

DisplayCollection.gain = bpy.props.FloatProperty(min=0,
                        max=100,
                        default=1,
                        name="Gain")

DisplayCollection.gamma = bpy.props.FloatProperty(min=0,
                        max=100,
                        default=1,
                        name="Gamma")

passes.pixelfilter = bpy.props.PointerProperty(type=RendermanPixelFilter)


RendermanPixelFilter.filterlist = bpy.props.EnumProperty(items=RM_FILTER,
                                    default="box",
                                    name = "PixelFilter")

RendermanPixelFilter.customfilter = bpy.props.StringProperty(name="Custom Filter",
                                    default = "")

RendermanPixelFilter.filterwidth = bpy.props.FloatProperty(min = 0,
                                    max = 100,
                                    default = 1)

RendermanPixelFilter.filterheight = bpy.props.FloatProperty(min = 0,
                                    max = 100,
                                    default = 1)




RendermanSceneSettings.facevertex = bpy.props.BoolProperty(name="facevertex",
                            default = False)

Paths.shaderpaths = bpy.props.CollectionProperty(type = PathProperties)

Paths.shadercollection = bpy.props.CollectionProperty(type = PathProperties)

Paths.surface_collection = bpy.props.CollectionProperty(type = PathProperties)

Paths.displacement_collection = bpy.props.CollectionProperty(type = PathProperties)

Paths.volume_collection = bpy.props.CollectionProperty(type = PathProperties)

Paths.light_collection = bpy.props.CollectionProperty(type = PathProperties)

Paths.imager_collection = bpy.props.CollectionProperty(type = PathProperties)

Paths.shaderpathsindex = bpy.props.IntProperty(min = -1,
                    max = 1000,
                    default = -1)

RendermanSceneSettings.shaders = bpy.props.PointerProperty(type = Paths)

RendermanSceneSettings.shaderpath = bpy.props.StringProperty(subtype='DIR_PATH')

RendermanSceneSettings.shaderpath_recursive = bpy.props.BoolProperty(name ="Recursive", description="add sub folders")

RendermanSceneSettings.framepadding = bpy.props.IntProperty(default=4,
                    min=1,
                    max=1000)

RendermanSceneSettings.passes = bpy.props.CollectionProperty(type=passes)

RendermanSceneSettings.passes_index = bpy.props.IntProperty(default=-1,
                                min=-1,
                                max=1000)

RendermanSceneSettings.searchpass = bpy.props.StringProperty(name = "Search Pass",
                        default = "")


bpy.types.Scene.renderman_settings = bpy.props.PointerProperty(type=RendermanSceneSettings)                       

RendermanSceneSettings.exportallpasses = bpy.props.BoolProperty(name="Export All Passes",
                    description="",
                    default=True)

##########################################################
#Settings
RendermanSceneSettings.presetname = bpy.props.StringProperty()
RendermanSceneSettings.preset_subfolder = bpy.props.StringProperty()
RendermanSceneSettings.active_engine = bpy.props.StringProperty()
RendermanSceneSettings.basic_expand = bpy.props.BoolProperty(default=False)
RendermanSceneSettings.hider_expand = bpy.props.BoolProperty(default=False)
RendermanSceneSettings.options_expand = bpy.props.BoolProperty(default=False)
RendermanSceneSettings.attributes_expand = bpy.props.BoolProperty(default=False)
RendermanSceneSettings.shader_expand = bpy.props.BoolProperty(default=False)
RendermanSceneSettings.dir_expand = bpy.props.BoolProperty(default=False)
RendermanSceneSettings.drivers_expand = bpy.props.BoolProperty(default=False)

RendermanSceneSettings.renderexec = bpy.props.StringProperty(name="Render Executable",
                        description="Render Executable",
                        default="",
                        options={'HIDDEN'},
                        subtype='NONE')

RendermanSceneSettings.shaderexec = bpy.props.StringProperty(name="Shader Compiler",
                        description="Shader Compiler Executable",
                        default="",
                        options={'HIDDEN'},
                        subtype='NONE')

RendermanSceneSettings.shadersource = bpy.props.StringProperty(name="Source Extension",
                        description="Shader Source Code Extension",
                        default="",
                        options={'HIDDEN'},
                        subtype='NONE')

RendermanSceneSettings.shaderinfo = bpy.props.StringProperty(name="Shaderinfo Binary",
                        description="Shader information Tool binary",
                        default="",
                        options={'HIDDEN'},
                        subtype='NONE')

RendermanSceneSettings.textureexec = bpy.props.StringProperty(name="Texture Preparation",
                        description ="Texture Preparation Tool",
                        default="",
                        options={'HIDDEN'},
                        subtype="NONE")

RendermanSceneSettings.shaderbinary = bpy.props.StringProperty(name="Binary Extension",
                        description="Shader Binary Extension",
                        default="",
                        options={'HIDDEN'},
                        subtype='NONE')

RendermanSceneSettings.textureext = bpy.props.StringProperty(name="Texture Extension",
                        description="Texture Extension",
                        default="",
                        options={'HIDDEN'},
                        subtype='NONE')

RendermanSceneSettings.displaydrvpath = bpy.props.StringProperty(name="Display Path",
                        description="Path to Display Driver folder",
                        default="",
                        options={'HIDDEN'},
                        subtype='DIR_PATH')
                        
RendermanSceneSettings.disp_ext_os_default = bpy.props.BoolProperty(name="OS Lib", description="Default OS Lib extension", default=True)

RendermanSceneSettings.disp_ext = bpy.props.StringProperty(name="Extension", description='Custom Display Driver extension(without "."')

RendermanSceneSettings.drv_identifier = bpy.props.StringProperty(description = "Prefix or suffix in drivers filename to identify, that its actually a Display Driver")

RendermanSceneSettings.default_driver = bpy.props.StringProperty(description = "Default Display Driver")


#########################################################

RendermanSceneSettingsdefaultribpath = bpy.props.BoolProperty(default=True)

RendermanSceneSettings.ribpath = bpy.props.StringProperty(name="RIB Path",
                        description="Path to Scene RIB File",
                        default="",
                        options={'HIDDEN'},
                        subtype='DIR_PATH')
                                        
RendermanSceneSettings.bakedir = bpy.props.StringProperty( name="Bake",
                                        description = "Folder where bake files are stored",
                                        default = "Bakes")                                                                                                                        

RendermanSceneSettings.texdir = bpy.props.StringProperty(name="Texturemaps Folder",
                        description="Name of Texture Maps Folder",
                        default="textures",
                        options={'HIDDEN'})

passes.imagedir = bpy.props.StringProperty(name="Image Folder",
                        description="Name of Image Output Folder",
                        default="images",
                        options={'HIDDEN'})

RendermanSceneSettings.exportonly = bpy.props.BoolProperty(name="Export Only",
                    description="Only Export Scene Rib File without rendering",
                    default=False,
                    options={'HIDDEN'},
                    subtype='NONE')

passes.exportobjects = bpy.props.BoolProperty(name="Export All Objects",
                    description="Export All Objects to .rib files",
                    default=True)

passes.exportlights = bpy.props.BoolProperty(name="Export All Lights",
                    description="Export All Lights to Scene .rib file",
                    default=True)

passes.exportanimation = bpy.props.BoolProperty(name="Export Animation",
                    default=True)

passes.shadow = bpy.props.BoolProperty(name="Export Animation",
                    default=False)

passes.sceneindex = bpy.props.IntProperty(name="Object Index",
                    description = "",
                    default = -1,
                    min = -1,
                    max = 10000)

passes.objectgroup = bpy.props.StringProperty(name="Object Group",
                        description="export only objects in this group")

passes.lightgroup = bpy.props.StringProperty(name="Light Group",
                        description="export only lights in this group")

passes.filename = bpy.props.StringProperty(default = "")

passes.environment = bpy.props.BoolProperty(default = False)

passes.camera_object = bpy.props.StringProperty()

passes.motionblur = bpy.props.BoolProperty(default=False,
                            name="Motion Blur",
                            description = "render motion blur for this pass")

passes.shutter_type = bpy.props.EnumProperty(name = "Shutter Type",
                                             items = (  ("angle", "Angle", ""),
                                                        ("seconds", "Seconds", "")),
                                             default = "seconds")
                        
passes.shutterspeed_sec = bpy.props.FloatProperty(name="Shutter Speed",
                            min=0.0001,
                            max=1000,
                            precision = 4,
                            default=0.01,
                            unit = 'TIME',
                            description="Amount of time the shutter is open(in seconds)")

passes.shutterspeed_ang = bpy.props.FloatProperty(name="Shutter Speed",
                            min=0.0001,
                            max=1000,
                            precision = 4,
                            default=180,
                            unit = 'ROTATION',
                            description="Amount of time the shutter is open(in degrees)")   

passes.option_groups = bpy.props.CollectionProperty(type=AttributeOptionGroup,
                            name="Option Groups",
                            description="Renderman Option Groups")
                            
passes.renderresult = bpy.props.StringProperty()                            
                            
                            
AttributeOptionGroup.expand = bpy.props.BoolProperty(default =False)

AttributeOptionGroup.export = bpy.props.BoolProperty(default =True)

AttributeOptionGroup.preset_include = bpy.props.BoolProperty(default = True, description="include Attribute Group in preset")

AttributeOptionGroup.options = bpy.props.CollectionProperty(type=Collection ,
                            name="Renderman Options",
                            description="Renderman Options")
                                                        
                            
RendermanSceneSettings.option_groups = bpy.props.CollectionProperty(type=AttributeOptionGroup,
                            name="Option Groups",
                            description="Renderman Option Groups")   
                            
RendermanSceneSettings.option_groups_index = bpy.props.IntProperty(min=-1, max=1000, default=-1)

Collection.rman_type = bpy.props.StringProperty()

passes.scene_code = bpy.props.CollectionProperty(type = CustomCodeCollection)

passes.scene_code_index = bpy.props.IntProperty(min = -1, max = 1000, default = -1)

passes.world_code = bpy.props.CollectionProperty(type = CustomCodeCollection)

passes.world_code_index = bpy.props.IntProperty(min = -1, max = 1000, default = -1)

passes.renderman_camera = bpy.props.PointerProperty(type = RendermanCamera)

#############################################
#                                           #
#   World Properties                        #
#                                           #
#############################################

passes.attribute_groups = bpy.props.CollectionProperty(type=AttributeOptionGroup)

AttributeOptionGroup.attributes = bpy.props.CollectionProperty(type=Collection)

RendermanSceneSettings.attribute_groups = bpy.props.CollectionProperty(type=AttributeOptionGroup)
                            
RendermanSceneSettings.attribute_groups_index = bpy.props.IntProperty(min=-1, max=1000, default=-1)                            

passes.global_shader = bpy.props.PointerProperty(type = Shader)

passes.override_shadingrate = bpy.props.BoolProperty(name="Override ShadingRate", description="Override ShadingRate of Objects", default=False)

passes.shadingrate = bpy.props.FloatProperty(name="ShadingRate", description="", min=0, max=100, default=1)

#############################################
#                                           #
#   Imager Shader Properties                #
#                                           #
#############################################


passes.imager_shader = bpy.props.StringProperty(name="Imager Shader",
                                    description="Name of Imager Shader",
                                    default="",
                                    options={'HIDDEN'},
                                    subtype='NONE')

passes.imager_shader_parameter = bpy.props.CollectionProperty(type=Collection ,
                            name="ImagerParam",
                            description="Imager Shader Parameter")

passes.imager_shader_parameter_index = bpy.props.IntProperty(name="Imager Shader Parameter Index",
                    description="",
                    default=-1,
                    min=-1,
                    max=1000)



#############################################
#                                           #
#   Camera Properties                       #
#                                           #
#############################################
                                          

#############################################
#                                           #
#   Light Properties                        #
#                                           #
#############################################
Shader.links = bpy.props.CollectionProperty(type = EmptyCollections)

Shader.attribute_groups = bpy.props.CollectionProperty(type = AttributeOptionGroup)

Shader.shaderpath = bpy.props.StringProperty(name="Shader Path",
                                description="Path to custom shader",
                                default="",
                                options={'HIDDEN'},
                                subtype='NONE')

Shader.light_shader_parameter = bpy.props.CollectionProperty(type=Collection ,
                            name="LightParam",
                            description="Light Shader Parameter")     
                    
Shader.use_as_light = bpy.props.BoolProperty(name="AreaLight", description="use the object this material is assigned to as an AreaLight")

bpy.types.Lamp.renderman = bpy.props.CollectionProperty(type=Shader)

bpy.types.Lamp.renderman_index = bpy.props.IntProperty(min = -1, max = 1000, default = -1)

PathProperties.lamp_type = bpy.props.EnumProperty(items=(
                                            ("spot", "Spot", "Spot Light"),
                                            ("point", "Point", "Point Light"),
                                            ("directional", "Directional", "Directional Light"),
                                            ),
                                    default="point",
                                    name="Light Type",
                                    description="How to draw this light in Blenders Viewport")

#############################################
#                                           #
#   Object Properties                       #
#                                           #
#############################################
Object = bpy.types.Object

Object.requests = bpy.props.CollectionProperty(type = ClientParameters)

Object.renderman = bpy.props.CollectionProperty(type = ObjectParameters, name="Renderman")

Object.renderman_index = bpy.props.IntProperty(min = -1, max = 1000, default = -1)

ObjectParameters.links = bpy.props.CollectionProperty(type = EmptyCollections)

ObjectParameters.custom_code = bpy.props.CollectionProperty(type = CustomCodeCollection)

ObjectParameters.custom_code_index = bpy.props.IntProperty(min = -1, max = 100, default = -1)

ObjectParameters.attribute_groups = bpy.props.CollectionProperty(type=AttributeOptionGroup)

ObjectParameters.light_list = bpy.props.CollectionProperty(name="Light List",
                                    description="Ligh List",
                                    type=LightCollection)

LightCollection.illuminate = bpy.props.BoolProperty(name="Illuminate",
                                default=True)

ObjectParameters.lightgroup = bpy.props.StringProperty()

ObjectParameters.shadingrate = bpy.props.FloatProperty(name="Shading Rate",
                                min = 0,
                                max = 100,
                                default = 1)
                                
ObjectParameters.transformation_blur = bpy.props.BoolProperty(name="transformation Blur",
                                            default=False,
                                            description="apply motion blur to the transformation of this object")
                                    
ObjectParameters.deformation_blur = bpy.props.BoolProperty(   name="deformation Blur",
                                            default = False,
                                            description = "apply motion blur to the deformation of this object")
                                            
                                            
                                            
ObjectParameters.motion_samples = bpy.props.IntProperty(  name="motion samples",
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

mesh.export_normals = bpy.props.BoolProperty(name="Export Normals", default=True)

mesh.primitive_type = bpy.props.EnumProperty(   name = "PrimitiveType", 
                                                default="pointspolygons", 
                                                items=( ("pointspolygons", "PointsPolygons", ""),
                                                        ("points", "Points", ""),
                                                        ("subdivisionmesh", "SubdivisionMesh",""),
                                                        ("quadrics", "Quadrics", "Quadrics")))
                                                                                    
mesh.export_type = bpy.props.EnumProperty(name = "Export As", default="ReadArchive", items=(  ("ReadArchive", "ReadArchive", ""),
                                                                            ("DelayedReadArchive", "DelayedReadArchive", ""),
                                                                            ("ObjectInstance", "ObjectInstance", "")))

mesh.size_vgroup = bpy.props.StringProperty(name="Vertex Group", description="Control the siza of each point via Vertex Group", default ="")  

mesh.points_scale = bpy.props.FloatProperty(name ="Points Scale", description="Scale of Points", min=0, max=10000, default=1)

#############################################
#                                           #
#   Empty Properties                        #
#                                           #
#############################################


RNAEmpty = bpy.types.Empty

RNAEmpty.renderman = bpy.props.PointerProperty(type = Empty)

Empty.passes = bpy.props.CollectionProperty(type = EmptyPasses)

Empty.quadrics = bpy.props.EnumProperty(  name = "Quadrics", 
                                        description="Replace Mesh by render intern Quadrics", 
                                        default="Sphere",
                                        items = (   ("Sphere", "Sphere", "Sphere"),
                                                    ("Cone", "Cone", "Cone"),
                                                    ("Cylinder", "Cylinder", "Cylinder"),
                                                    ("Hyperboloid", "Hyperboloid", "Hyperboloid"),
                                                    ("Paraboloid", "Paraboloid", "Paraboloid"),
                                                    ("Disk", "Disk", "Disk"),
                                                    ("Torus", "Torus", "Torus")))         

EmptyPasses.quadrics = bpy.props.EnumProperty(  name = "Quadrics", 
                                        description="Replace Mesh by render intern Quadrics", 
                                        default="Sphere",
                                        items = (   ("Sphere", "Sphere", "Sphere"),
                                                    ("Cone", "Cone", "Cone"),
                                                    ("Cylinder", "Cylinder", "Cylinder"),
                                                    ("Hyperboloid", "Hyperboloid", "Hyperboloid"),
                                                    ("Paraboloid", "Paraboloid", "Paraboloid"),
                                                    ("Disk", "Disk", "Disk"),
                                                    ("Torus", "Torus", "Torus")))
                                                    
mesh.export_type = bpy.props.EnumProperty(name = "Export As", default="ReadArchive", items=(  ("ReadArchive", "ReadArchive", ""),
                                                                            ("DelayedReadArchive", "DelayedReadArchive", ""),
                                                                            ("ObjectInstance", "ObjectInstance", "")))                                                     
                                                                                             
#############################################################
#                                                           #
#   Material Properties                                     #
#                                                           #
#############################################################

mat = bpy.types.Material
tex = bpy.types.Texture

tex.renderman = bpy.props.PointerProperty(type=RendermanTexture)

RendermanTexture.type = bpy.props.EnumProperty(name="Type", default="none", items=(
                                                                    ("none", "None", ""),
                                                                    ("file", "Image File", ""),
                                                                    ("bake", "Bake File", "")))

RendermanTexture.processing = bpy.props.PointerProperty(type = ImageProcessing)                                                       

mat.renderman = bpy.props.CollectionProperty(type=Shader)

mat.renderman_index = bpy.props.IntProperty(min = -1, max = 1000, default = -1)
                        
Shader.preview_scene = bpy.props.StringProperty()

Shader.preview = bpy.props.BoolProperty(name="Preview", description="activate Preview", default=False)
                        
Shader.arealight_shader = bpy.props.StringProperty(name="AreaLight", description="Area Light Shader")                        

Shader.opacity = bpy.props.FloatVectorProperty(name="Opacity",
                            subtype="COLOR",
                            default=(1, 1, 1),
                            precision = 4,
                            step = 0.01,
                            min=0,
                            max=1)
                            
Shader.color = bpy.props.FloatVectorProperty(name="Color",
                            subtype="COLOR",
                            default=(1, 1, 1),
                            precision = 4,
                            step = 0.01,
                            min=0,
                            max=1)                            
                            
                            
Shader.motion_samples = bpy.props.IntProperty(    default=2,
                                min=2,
                                max=1000,
                                name="Motion Samples",
                                description="number samples to put into motion block")
                                
Shader.color_blur = bpy.props.BoolProperty(   default=False,
                            name="Color Blur",
                            description="Motion Blur for surface color")
                            
Shader.opacity_blur = bpy.props.BoolProperty(   default=False,
                            name="Opacity Blur",
                            description="Motion Blur for surface opacity") 
                            
Shader.shader_blur = bpy.props.BoolProperty(  default=False,
                            name = "Shader Blur",
                            description = "Motion Blur for parameters of assigned shader")                                                                                                                                             

PathProperties.fullpath = bpy.props.StringProperty(default = "")

PathProperties.mod_time = bpy.props.IntProperty()

PathProperties.tmp_mod_time = bpy.props.IntProperty()


Shader.matte = bpy.props.BoolProperty(name="Matte",
                            default=False)                            

#############################################
#                                           #
#   Surface Shader Properties               #
#                                           #
#############################################


Shader.surface_shader = bpy.props.StringProperty(name="Surface Shader",
                                    description="Name of Surface Shader",
                                    default="matte",
                                    options={'HIDDEN'},
                                    subtype='NONE')

Shader.surface_shader_parameter = bpy.props.CollectionProperty(type=Collection ,
                            name="SurfaceParam",
                            description="Surface Shader Parameter")

#############################################
#                                           #
#   Displacement Shader Properties          #
#                                           #
#############################################


Shader.displacement_shader = bpy.props.StringProperty(name="Displacement Shader",
                                    description="Name of Displacement Shader",
                                    default="",
                                    options={'HIDDEN'},
                                    subtype='NONE')

Shader.disp_shader_parameter = bpy.props.CollectionProperty(type=Collection ,
                            name="DisplacementParam",
                            description="Displacement Shader Parameter")

#############################################
#                                           #
#   Interior Shader Properties              #
#                                           #
#############################################


Shader.interior_shader = bpy.props.StringProperty(name="Interior Shader",
                                    description="Interior Volume Shader",
                                    default="",
                                    options={'HIDDEN'},
                                    subtype='NONE')

Shader.interior_shader_parameter = bpy.props.CollectionProperty(type=Collection ,
                            name="VolumeParam",
                            description="Volume Shader Parameter")

#############################################
#                                           #
#   Exterior Shader Properties              #
#                                           #
#############################################


Shader.exterior_shader = bpy.props.StringProperty(name="Exterior Shader",
                                    description="Exterior Volume Shader",
                                    default="",
                                    options={'HIDDEN'},
                                    subtype='NONE')

Shader.exterior_shader_parameter = bpy.props.CollectionProperty(type=Collection ,
                            name="VolumeParam",
                            description="Volume Shader Parameter")
                    
#############################################
#                                           #
#   Atmosphere Shader Properties            #
#                                           #
#############################################


Shader.atmosphere_shader = bpy.props.StringProperty(name="Atmosphere Shader",
                                    description="Atmosphere Volume Shader",
                                    default="",
                                    options={'HIDDEN'},
                                    subtype='NONE')

Shader.atmosphere_shader_parameter = bpy.props.CollectionProperty(type=Collection ,
                            name="VolumeParam",
                            description="Volume Shader Parameter")

Shader.atmosphere_parameter_index = bpy.props.IntProperty(name="Volume Shader Parameter Index",
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

psettings.renderman = bpy.props.CollectionProperty(type = ParticlePasses)

psettings.renderman_index = bpy.props.IntProperty(min = -1, max = 1000, default = -1)

ParticlePasses.custom_code = bpy.props.CollectionProperty(type = CustomCodeCollection)

ParticlePasses.custom_code_index = bpy.props.IntProperty(min = -1, max = 100, default = -1)

ParticlePasses.links = bpy.props.CollectionProperty(type = EmptyCollections)

ParticlePasses.motion_blur = bpy.props.BoolProperty(name = "Motion Blur", default=False, description = "Activate Motion Blur for Particles")

ParticlePasses.motion_samples = bpy.props.IntProperty(name = "motion samples", description="Number samples to export in this motion block", min=2, max = 100, default = 2)

ParticlePasses.render_type = bpy.props.EnumProperty(  name = "Render Type",
                                    description = "Choose how to render the particles",
                                    items = (   ("Points", "Points", "Points"),
                                                ("Object", "Object", "Object"),
                                                ("Group", "Group", "Group"),
                                                ("Archive", "Archive", "Archive")))
                                                
ParticlePasses.object = bpy.props.StringProperty(name = "Object", description ="Object to use for Rendering Particles")

ParticlePasses.archive = bpy.props.StringProperty(name ="Archive", description  = "Archive to load for Rendering Particles", subtype = "FILE_PATH") 

ParticlePasses.group = bpy.props.StringProperty(name = "Group", description ="Objects of group to use for Rendering Particles")                                              

ParticlePasses.attribute_groups = bpy.props.CollectionProperty(type=AttributeOptionGroup)

ParticlePasses.material_slot = bpy.props.IntProperty(name = "Material Slot",
                                                     description = "Material Slot to use",
                                                     min = -1,
                                                     max = 100,
                                                     default = 1)
