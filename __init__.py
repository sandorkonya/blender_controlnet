
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
import re
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

# TODO: Get tokens from UI
if "REPLICATE_API_TOKEN" in os.environ:
  print("Replicate Token exists")
else:
    Replicate_TOKEN = "0da145ebb6ee17b520a00ebc492f0464d5ae352e"
    os.environ["REPLICATE_API_TOKEN"] = Replicate_TOKEN

if "DALLE2_API_TOKEN" in os.environ:
  print("Dalle-2 Token exists")
else:
    TOKEN = "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"
    os.environ["DALLE2_API_TOKEN"] = TOKEN

openai.api_key = os.environ["DALLE2_API_TOKEN"]

#_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-
#_-_-_-_-_-_-_-_-_-_-_-_-_-_-_- _-_-Specify paths for images_-_-_-_-__-_-_-_-_-_-_-_-_-_-_-_-_-_-
#_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-

blender_path = os.path.abspath(bpy.path.abspath("images"))
render_image_path = os.path.join(blender_path, "rendered.png")
ai_image_path = os.path.join(blender_path, "ai_render.jpg")
ai_skeleton_path = os.path.join(blender_path, "ai_skeleton_path.jpg")




from bpy.props import (StringProperty, PointerProperty)
from bpy.types import (PropertyGroup, Panel)


class MyProperties(PropertyGroup):

    my_string: StringProperty(
        name="Foo",
        description=":",
        default="",
        maxlen=1024,
        )

    bar: StringProperty(
        name="Bar",
        description=":",
        default="",
        maxlen=1024,
        )


class OBJECT_PT_MyOperatorUI(Panel):
    bl_label = "Blender Pose AI Renderer"
    bl_idname = "OBJECT_PT_my_panel"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        my_tool = scene.my_tool

        layout.prop(my_tool, "my_string")

        row = layout.row()
        row.label(text="Stable Diffusion")
        layout.operator("object.stable_diffusion_operator")

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


    def call_API(self):
        # bpy.context.space_data.context = 'WORLD'
        bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
        bpy.context.scene.view_settings.exposure = -0.5


        bpy.context.scene.render.filepath = render_image_path
        # Render the image
        bpy.ops.render.render(write_still=True)
        output_file_path = bpy.context.scene.render.filepath
        output = replicate.run(
            "jagilley/controlnet-pose:0304f7f774ba7341ef754231f794b1ba3d129e3c46af3022241325ae0c50fb99",
            input={
                "image": open(output_file_path, "rb"),
                "prompt": "A slim and fit man on the street, photograph, advertisement, handsome, 8k, 4k, color",
            }
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
        threading.Thread(target=self.call_API).start()
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
    WM_OT_SDOperator
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