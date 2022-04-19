import bpy
from .. import util


# ---------------------------------------------------------------------------- #
#                   Optimizer code by StandingPad Animations                   #
# ---------------------------------------------------------------------------- #
class MCprepOptimizerProperties(bpy.types.PropertyGroup):

	def TimeInScene(self, context):
		itms = [
        ("Day", "Day time", ""), 
        ("Night", "Night time", "")
        ]
		return itms

    # --------------------------------- Caustics --------------------------------- #
	CausticsBool = bpy.props.BoolProperty(
		name="Caustics (Increases render times)",
        default=False
	)
    
    # -------------------------------- Motion Blur ------------------------------- #
	MotionBlurBool = bpy.props.BoolProperty(
		name="Motion Blur (increases render times)",
        default=False
	)

    # ---------------------------------- Fast GI --------------------------------- #
	FastGIBool = bpy.props.BoolProperty(
		name="Fast GI (Decreases render times)",
        default=False
	)
    
    # -------------------------- Materials in the scene -------------------------- #
	GlossyBool = bpy.props.BoolProperty(
		name="Glossy Materials",
        default=False
	)
    
	TransmissiveBool = bpy.props.BoolProperty(
		name="Glass Materials",
        default=False
	)

	VolumetricBool = bpy.props.BoolProperty(
		name="Volumetrics" if util.bv30() else "Volumetrics (Increases render times)",
        default=False
	)
    
    # ------------------------- Time of day in the scene ------------------------- #
	TimeInScene : bpy.props.EnumProperty(
		name="",
		description="Time of day in the scene",
		items=TimeInScene
	)

def panel_draw(self, context):
    row = self.layout.row()
    col = row.column()
    engine = context.scene.render.engine
    scn_props = context.scene.optimizer_props
    if util.bv30:
        if engine == 'CYCLES':
            col.label(text="Materials in Scene")
            
            # ---------------------------------- Glossy ---------------------------------- #
            if scn_props.GlossyBool:
                col.prop(scn_props, "GlossyBool", icon="INDIRECT_ONLY_ON")
            else:
                col.prop(scn_props, "GlossyBool", icon="INDIRECT_ONLY_OFF")
            
            # ------------------------------- Transmissive ------------------------------- #
            if scn_props.TransmissiveBool:
                col.prop(scn_props, "TransmissiveBool", icon="FULLSCREEN_EXIT")
            else:
                col.prop(scn_props, "TransmissiveBool", icon="FULLSCREEN_ENTER")
                
            # -------------------------------- Volumetric -------------------------------- #
            if scn_props.VolumetricBool:
                col.prop(scn_props, "VolumetricBool", icon="OUTLINER_OB_VOLUME")
            else:
                col.prop(scn_props, "VolumetricBool", icon="OUTLINER_DATA_VOLUME")
                
            # ---------------------------------- Options --------------------------------- #
            col.label(text="Options")
            col.label(text="Time of Day")
            col.prop(scn_props, "TimeInScene")
            col.prop(scn_props, "CausticsBool", icon="TRIA_UP")
            col.prop(scn_props, "MotionBlurBool", icon="TRIA_UP")
            col.prop(scn_props, "FastGIBool", icon="TRIA_DOWN")
            col.operator("mcprep.optimize_scene", text="Optimize Scene")
        else:
            col.label(text= "Cycles Only >:C")
    else:
        col.label(text= "Old Cycles Support Still a WIP")


class MCPrep_OT_optimize_scene(bpy.types.Operator):
    bl_idname = "mcprep.optimize_scene"
    bl_label = "Optimize Scene"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        CyclesComputeDeviceType = bpy.context.preferences.addons["cycles"].preferences.compute_device_type, bpy.context.scene.cycles.device
        scn_props = context.scene.optimizer_props
        """
        Sampling Settings
        """
        Samples = 128
        NoiseThreshold = 0.2
        MinimumSamples = 64
        
        """
        Light Bounces
        """
        Diffuse = 2 # This is default because diffuse bounces don't need to be high 
        Glossy = 1
        Transmissive = 1
        Volume = 0  
        FastGI = False;
        
        """
        Volumetric Settings
        """
        MaxSteps = 100 
        
        """
        Filter Glossy and clamping settings
        """
        FilterGlossy = 1
        ClampingIndirect = 1
        
        """
        Motion blur, caustics, etc
        """
        MotionBlur = False
        ReflectiveCaustics = False 
        RefractiveCaustics = False 
        
        """
        Optimizer Settings
        """
        Quality = True 
        
        
        # -------------------------- Render engine settings -------------------------- #
        if scn_props.CausticsBool:
            ReflectiveCaustics = True 
            RefractiveCaustics = True 
        
        if scn_props.MotionBlurBool:
            MotionBlur = True
            
        if scn_props.FastGIBool:
            FastGI = True
        # ------------------------------ Scene materials ----------------------------- #
        if scn_props.GlossyBool:
            Glossy = 3
            
        if scn_props.VolumetricBool:
            Volume = 2
            
        if scn_props.TransmissiveBool:
            Transmissive = 3
            
        # -------------------------------- Time of day ------------------------------- #
        if scn_props.TimeInScene == "Day":
            NoiseThreshold = 0.2
        else:
            NoiseThreshold = 0.02
        
        # ------------------------------ Compute device ------------------------------ #
        if CyclesComputeDeviceType == "NONE":
            Samples = 128 
            if Quality:
                NoiseThreshold = 0.05
                MinimumSamples = 25 
                FilterGlossy = 0.5
                MaxSteps = 200
                
            else:
                NoiseThreshold = 0.09
                MinimumSamples = 10
                FilterGlossy = 1
                MaxSteps = 50
        
        elif CyclesComputeDeviceType == "CUDA" or CyclesComputeDeviceType == "HIP":
            if CurrentRenderDevice == "CPU":
                if bpy.context.preferences.addons["cycles"].preferences.has_active_device():
                    print("Detected GPU: Switching to GPU...")
                    CurrentRenderDevice = "GPU"
                    
            Samples = 128 
            if Quality:
                NoiseThreshold = 0.02
                MinimumSamples = 32 
                FilterGlossy = 0.5
                MaxSteps = 200
                
            else:
                NoiseThreshold = 0.06
                MinimumSamples = 15
                FilterGlossy = 1
                MaxSteps = 70

        elif CyclesComputeDeviceType == "OPTIX":
            if CurrentRenderDevice == "CPU":
                if bpy.context.preferences.addons["cycles"].preferences.has_active_device():
                    print("Detected GPU: Switching to GPU...") 
                    CurrentRenderDevice = "GPU"
                    
            Samples = 128 
            if Quality:
                NoiseThreshold = 0.02
                MinimumSamples = 64 
                FilterGlossy = 0.2
                MaxSteps = 250
                
            else:
                NoiseThreshold = 0.04
                MinimumSamples = 20
                FilterGlossy = 0.8
                MaxSteps = 80
                
        """
        Cycles Render Settings Optimizations
        """
        
        """
        Unique changes
        """
        bpy.context.scene.cycles.samples = Samples
        bpy.context.scene.cycles.adaptive_threshold = NoiseThreshold
        bpy.context.scene.cycles.adaptive_min_samples = MinimumSamples
        bpy.context.scene.cycles.blur_glossy = FilterGlossy
        bpy.context.scene.cycles.volume_max_steps = MaxSteps
        bpy.context.scene.cycles.glossy_bounces = Glossy
        bpy.context.scene.cycles.transmission_bounces = Transmissive
        bpy.context.scene.cycles.caustics_reflective = ReflectiveCaustics
        bpy.context.scene.cycles.caustics_refractive = RefractiveCaustics
        bpy.context.scene.cycles.sample_clamp_indirect = ClampingIndirect
        bpy.context.scene.render.use_motion_blur = MotionBlur
        bpy.context.scene.cycles.volume_bounces = Volume
        bpy.context.scene.cycles.diffuse_bounces = Diffuse
        bpy.context.scene.cycles.use_fast_gi = FastGI


        """Other changes"""
        bpy.context.scene.cycles.max_bounces = 8 
        bpy.context.scene.cycles.preview_samples = 32
        bpy.context.scene.render.use_simplify = True
        bpy.context.scene.render.simplify_subdivision = 0
        
        return {'FINISHED'}

classes = (
    MCprepOptimizerProperties,
    MCPrep_OT_optimize_scene
)
def register():
    for cls in classes:
        util.make_annotations(cls)
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.optimizer_props = bpy.props.PointerProperty(type=MCprepOptimizerProperties)


def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)
	del bpy.types.Scene.optimizer_props