
bl_info = {
    "name" : "Pose-AI-Renderer",
    "author" : "Arjuna Dev",
    "description" : "",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "",
    "warning" : "",
    "category" : "Generic"
}

import bpy
import sys
import subprocess
import platform
import os
import importlib
import requests
import threading

#_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-
#_-_-_-_-_-_-_-_-_-_-_-_ Install pip, openAI and replicate depending on OS_-_-_-_-_-_-_-_-_-_-_-_
#_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-

# Install pip
this_os = platform.system()

if this_os == "Windows":
    python_exe = os.path.join(sys.prefix, "bin", "python.exe")
    target = os.path.join(sys.prefix, "lib", "site-packages")
elif this_os == "Linux" or this_os == "Darwin":
    python_exe = sys.executable

if not importlib.util.find_spec('ensurepip'):
    subprocess.call([python_exe, "-m", "ensurepip"])
    subprocess.call([python_exe, "-m", "pip", "install", "--upgrade", "pip"])

# Install replicate
pip_frozen = subprocess.check_output([python_exe, "-m", "pip", "freeze"])
pip_frozen = pip_frozen.decode("utf-8")
if "\nreplicate==" not in pip_frozen:
    print("replicate not installed")
    if this_os == "Windows":
        subprocess.call([python_exe, "-m", "pip", "install", "--upgrade", "replicate", "-t", target]) 
    elif this_os == "Linux" or this_os == "Darwin":
        subprocess.call([python_exe, "-m", "pip", "install", "replicate"])

# Install openAI
pip_frozen = subprocess.check_output([python_exe, "-m", "pip", "freeze"])
pip_frozen = pip_frozen.decode("utf-8")
if "\nopenai==" not in pip_frozen:
    print("openai not installed")
    if this_os == "Windows":
        subprocess.call([python_exe, "-m", "pip", "install", "--upgrade", "openai", "-t", target]) 
    elif this_os == "Linux" or this_os == "Darwin":
        subprocess.call([python_exe, "-m", "pip", "install", "openai"])

import replicate
import openai

#_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-
#_-_-_-_-_-_-_-_-_-_-_-_-_-_-_- Get token for Replicate from UI_-_-__-_-_-_-_-_-_-_-_-_-_-_-_-_-_
#_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-


def set_token_from_UI(sd_token):
    if sd_token != "":
        os.environ["REPLICATE_API_TOKEN"] = sd_token

#_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-
#_-_-_-_-_-_-_-_-_-_-_-_-_-_-_- _-_-Specify paths for images_-_-_-_-__-_-_-_-_-_-_-_-_-_-_-_-_-_-
#_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-

blender_path = os.path.abspath(bpy.path.abspath("images"))
render_image_path = os.path.join(blender_path, "rendered.png")
ai_image_path = os.path.join(blender_path, "ai_render.jpg")
ai_skeleton_path = os.path.join(blender_path, "ai_skeleton_path.jpg")


#_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-
#_-_-_-_-_-_-_-_-_-_-_-_-_-_- _-_-_-_- Create Properties _-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-
#_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-


from bpy.props import (StringProperty, EnumProperty, PointerProperty)
from bpy.types import (PropertyGroup, Panel)


class MyProperties(PropertyGroup):

    sd_token: StringProperty(
        name= "New Token",
        description=":",
        default="",
        maxlen=1024,
        )

    sd_prompt: StringProperty(
        name= "Prompt",
        description=":",
        default="",
        maxlen=1024,
        )

    model_dropdown: EnumProperty(
        name="Choose Model:",
        description="Apply Data to attribute.",
        items=[ 
                ('canny', "Edge Detection (Canny)", ""),
                ('depth', "Depth Detection", ""),
                ('hed', "Detailed Edge Detection (HED)", ""),
                ('normal', "Normal Map", ""),
                ('mlsd', "Line Detection (M-LSD Lines)", ""),
                ('scribble', "Scribble Detection", ""),
                ('seg', "Semantic Segmentation", ""),
                ('openpose', "Pose Detection (OpenPose)", ""),
               ]
        )

    num_samples: StringProperty(
    name= "",
    description=":",
    default="1",
    maxlen=1024,
    )

    image_resolution: StringProperty(
    name= "",
    description=":",
    default="512",
    maxlen=1024,
    )

    ddim_steps: StringProperty(
    name= "",
    description=":",
    default="20",
    maxlen=1024,
    )

    scale: StringProperty(
    name= "",
    description=":",
    default="20",
    maxlen=1024,
    )

    seed: StringProperty(
    name= "",
    description=":",
    default="9",
    maxlen=1024,
    )

    eta: StringProperty(
    name= "",
    description=":",
    default="0",
    maxlen=1024,
    )

    n_prompt: StringProperty(
    name= "",
    description=":",
    default="longbody, lowres, bad anatomy, bad hands, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality",
    maxlen=1024,
    )

    low_threshold: StringProperty(
    name= "",
    description=":",
    default="100",
    maxlen=1024,
    )

    high_threshold: StringProperty(
    name= "",
    description=":",
    default="200",
    maxlen=1024,
    )

    bg_threshold: StringProperty(
    name= "",
    description=":",
    default="0",
    maxlen=1024,
    )

    value_threshold: StringProperty(
    name= "",
    description=":",
    default="0.1",
    maxlen=1024,
    )

    distance_threshold: StringProperty(
    name= "",
    description=":",
    default="0.1",
    maxlen=1024,
    )

#_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-
#_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_ Create Panel _-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_
#_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-

class ParentClass(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {"DEFAULT_CLOSED"}

class OBJECT_PT_MyOperatorUI(ParentClass, Panel):
    bl_label = "Blender Pose AI Renderer"
    bl_idname = "OBJECT_PT_MyOperatorUI"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        my_tool = scene.my_tool

        row = layout.row()
        row.label(text="*add only if you have a new token")
        layout.prop(my_tool, "sd_token")
        layout.prop(my_tool, "model_dropdown")
        layout.prop(my_tool, "sd_prompt")

        layout.operator("object.stable_diffusion_operator")

class Parameters_PT_Panel(ParentClass, Panel):
    bl_parent_id = "OBJECT_PT_MyOperatorUI"
    bl_label = "Parameters"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        my_tool = scene.my_tool

        layout.row().label(text="Number of Samples (max. 4, higher values may OOM):")
        layout.prop(my_tool, "num_samples")
        layout.row().label(text="Image Resolution:")
        layout.prop(my_tool, "image_resolution")
        layout.row().label(text="DDIM Steps:")
        layout.prop(my_tool, "ddim_steps")
        layout.row().label(text="Scale (for classifier-free guidance):")
        layout.prop(my_tool, "scale")
        layout.row().label(text="Seed:")
        layout.prop(my_tool, "seed")
        layout.row().label(text="eta (Controls the amount of noise that is added to the input data during the de-noising diffusion process)")
        layout.prop(my_tool, "eta")
        layout.row().label(text="Negative Prompt:")
        layout.prop(my_tool, "n_prompt")
        layout.row().label(text="Low Threshold (For Canny only):")
        layout.prop(my_tool, "low_threshold")
        layout.row().label(text="High Threshold (For Canny only):")
        layout.prop(my_tool, "high_threshold")
        layout.row().label(text="Background Threshold (For Normal only):")
        layout.prop(my_tool, "bg_threshold")
        layout.row().label(text="Value Threshold (For MLSD only):")
        layout.prop(my_tool, "value_threshold")
        layout.row().label(text="Distance Threshold (For MLSD only):")
        layout.prop(my_tool, "distance_threshold")

#_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-
#_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_- _-_ Stable Diffusion Operator -_-_-_-_-__-_-_-_-_-_-_-_-_-_-_-_
#_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-

class WM_OT_SDOperator(bpy.types.Operator):
    bl_idname = "object.stable_diffusion_operator"
    bl_label = "Render With Stable Diffusion"

    def create_image_window(self):
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
        area = bpy.context.window_manager.windows[-1].screen.areas[0]
        area.type = 'IMAGE_EDITOR'


    def call_API(self, model, prompt, num_samples, image_resolution, ddim_steps, scale, seed, eta, n_prompt, low_threshold, high_threshold, bg_threshold, value_threshold, distance_threshold):
        # bpy.context.space_data.context = 'WORLD'
        bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
        bpy.context.scene.view_settings.exposure = -0.5


        bpy.context.scene.render.filepath = render_image_path
        # Render the image
        bpy.ops.render.render(write_still=True)
        output_file_path = bpy.context.scene.render.filepath
        input={
            "image": open(output_file_path, "rb"),
            "prompt": prompt,
            "model_type": model,
            "num_samples": num_samples,
            "image_resolution": image_resolution,
            "ddim_steps": int(ddim_steps, 10),
            "scale": int(scale, 10),
            "seed": int(seed, 10),
            "eta": int(eta, 10),
            "n_prompt": n_prompt,
        }
        if model == "canny":
            input["low_threshold"]: low_threshold
            input["high_threshold"]: high_threshold
        elif model == "normal":
            input["bg_threshold"]: bg_threshold
        elif model == "mlsd":
            input["value_threshold"]: value_threshold
            input["distance_threshold"]: distance_threshold

        output = replicate.run(
            "jagilley/controlnet:8ebda4c70b3ea2a2bf86e44595afb562a2cdf85525c620f1671a78113c9f325b",
            input=input
        )
        url = output[1]

        download_image(output[0], ai_skeleton_path)
        download_image(url, ai_image_path)
        try:
            img = bpy.data.images.load(ai_image_path, check_existing=False)
            for window in bpy.data.window_managers["WinMan"].windows:
                for area in window.screen.areas:
                    if area.type == "IMAGE_EDITOR":
                        area.spaces.active.image = img
        except:
            print("Image not placed")

    def execute(self, context):
        sd_token = context.scene.my_tool.sd_token
        sd_prompt = context.scene.my_tool.sd_prompt
        sd_model = context.scene.my_tool.model_dropdown
        num_samples = context.scene.my_tool.num_samples
        image_resolution = context.scene.my_tool.image_resolution
        ddim_steps = context.scene.my_tool.ddim_steps
        scale = context.scene.my_tool.scale
        seed = context.scene.my_tool.seed
        eta = context.scene.my_tool.eta
        n_prompt = context.scene.my_tool.n_prompt
        low_threshold = context.scene.my_tool.low_threshold
        high_threshold = context.scene.my_tool.high_threshold
        bg_threshold = context.scene.my_tool.bg_threshold
        value_threshold = context.scene.my_tool.value_threshold
        distance_threshold = context.scene.my_tool.distance_threshold


        set_token_from_UI(sd_token)
        threading.Thread(target=self.call_API, args=(sd_model, sd_prompt, num_samples, image_resolution, ddim_steps, scale, seed, eta, n_prompt, low_threshold, high_threshold, bg_threshold, value_threshold, distance_threshold)).start()
        self.create_image_window()
        return {'FINISHED'}

#_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-
#-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_- Image Downloader _-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_
#_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-

def download_image(url, path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(path, 'wb') as f:
            f.write(response.content)

#_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-
#-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_- Register Classes _-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_
#_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-

classes = (
    MyProperties,
    OBJECT_PT_MyOperatorUI,
    WM_OT_SDOperator,
    Parameters_PT_Panel
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.my_tool = PointerProperty(type=MyProperties)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.my_tool