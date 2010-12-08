
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

class RibStructureBase(bpy.types.IDPropertyGroup):
    pass

class RibStructure(bpy.types.IDPropertyGroup):
    pass

class RendermanCamera(bpy.types.IDPropertyGroup):
    pass

class OutputImages(bpy.types.IDPropertyGroup):
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

RendermanCamera.resx = Int(min = 1, max = 100000, default = 1920, name = "X Resolution")

RendermanCamera.resy = Int(min = 1, max = 100000, default = 1080, name = "Y Resolution")

RendermanCamera.aspectx = Float(min = 1, max = 10000, default = 1, name ="Aspect X")

RendermanCamera.aspecty = Float(min = 1, max = 10000, default = 1, name ="Aspect Y")

RendermanCamera.square = Bool(name = "Square", default = False, description = "Same Value for X and Y Resolution")

RendermanCamera.shift_x = Float(default = 0, name="Shift X")

RendermanCamera.shift_y = Float(default = 0, name="Shift Y")

RendermanCamera.depthoffield = Bool(default = False,
                        name = "DOF")
                        
RendermanCamera.dof_distance = Float(default = 1, name = "DOF Distance")

RendermanCamera.focal_length = Float(min=0,
                        default=0,
                        name="Focal Length")

RendermanCamera.fstop = Float(min=0,
                        default=2.8,
                        name="F-Stop")

RendermanCamera.use_lens_length = Bool(default=True,
                        name="Use Camera Lens")
                        
RendermanCamera.perspective_blur = Bool(   name="perspective_blur",
                                            default = False,
                                            description = "apply motion blur to the viewing angle of this camera")                        

RendermanCamera.near_clipping = Float(min = 0,
                                    max = 1000000,
                                    default = 1)

RendermanCamera.far_clipping = Float(min = 0,
                                    max = 1000000,
                                    default = 30)


### Rib Structure Settings
RibStructure.own_file = Bool(default = True, name = "Own File", description="write into own RIB Archive")

RibStructure.filename = String(name="File", default="", subtype = 'FILE_PATH')

RibStructure.default_name = Bool(default = True, name = "Default Name", description = "Default RIB Archive Name")

RibStructure.overwrite = Bool(default = True, name = "Overwrite", description="overwrite existing files")

RibStructure.expand = Bool(default=False, name="Expand", description="Expand Properties")

RibStructure.folder = String(default = "")



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
                            
Collection.output_image = Bool( name = "Output Image",
                                description = "Is output image",
                                default = False)
                            
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

passes.ordered = Bool(name="Ordered", default = False)

passes.displaydrivers = CollectionProp(type=DisplayCollection)

passes.displayindex = Int(  default = -1,
                            min=-1,
                            max=1000)

RendermanSceneSettings.displays = CollectionProp(type=DisplayDrivers)

RendermanSceneSettings.output_images = CollectionProp(type = OutputImages)
                                            
RendermanSceneSettings.hider_list = CollectionProp(type=Hider)

passes.hider_list = CollectionProp(type=Hider)

RendermanSceneSettings.hider_list_index = Int(  min=-1,
                                                max=10000,
                                                default=-1)
                                    
RendermanSceneSettings.default_hider = String()                                    

Hider.options = CollectionProp(type=Collection)

passes.hider = String()

RendermanSceneSettings.rib_structure = Pointer(type=RibStructureBase)

RibStructureBase.render_pass = Pointer(type = RibStructure)

RibStructureBase.settings = Pointer(type = RibStructure)

RibStructureBase.world = Pointer(type = RibStructure)

RibStructureBase.object_blocks = Pointer(type = RibStructure)

RibStructureBase.objects = Pointer(type = RibStructure)

RibStructureBase.lights = Pointer(type = RibStructure)

RibStructureBase.particles = Pointer(type = RibStructure)

RibStructureBase.meshes = Pointer(type = RibStructure)

RibStructureBase.materials = Pointer(type = RibStructure)
                                            
#############################################
#                                           #
#   Display Properties                      #
#                                           #
#############################################

DisplayCollection.send = Bool(default = False)

DisplayCollection.custom_options = CollectionProp(type = Collection)

Collection.custom_var = Bool(default=True, description="use name of output variable as value")

DisplayCollection.default_name = Bool(default = True, name = "Default", description="Default Filename")                                          

RendermanSceneSettings.var_collection = CollectionProp( name="Output Value",
                                                    type=DisplayDrivers
                                                    )
                               
DisplayCollection.var = String(default="rgba")                               
                                
DisplayCollection.displaydriver = String()                                

DisplayCollection.file = String()

DisplayCollection.filename = String()

DisplayCollection.raw_name = String()

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
                                        
RendermanSceneSettings.lightdir = String( name="Lights",
                                        description = "Folder where Light Archives are stored",
                                        default = "Lights")
                                        
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

camera.renderman_camera = Pointer(type = RendermanCamera)                                           

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

Shader.light_shader_parameter = CollectionProp(type=Collection ,
                            name="LightParam",
                            description="Light Shader Parameter")     
                    
Shader.use_as_light = Bool(name="AreaLight", description="use the object this material is assigned to as an AreaLight")

bpy.types.Lamp.renderman = CollectionProp(type=Shader)

bpy.types.Lamp.renderman_index = Int(min = -1, max = 1000, default = -1)

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

Object.renderman_camera = Pointer(type = RendermanCamera)

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
