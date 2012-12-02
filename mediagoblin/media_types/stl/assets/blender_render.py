# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import bpy, json, os


try:
    CONFIG = json.loads(os.environ["RENDER_SETUP"])
    MODEL_EXT = CONFIG["model_ext"]
    MODEL_PATH = CONFIG["model_path"]
    CAMERA_COORD = CONFIG["camera_coord"]
    CAMERA_FOCUS = CONFIG["camera_focus"]
    CAMERA_CLIP = CONFIG["camera_clip"]
    CAMERA_TYPE = CONFIG["projection"]
    CAMERA_ORTHO = CONFIG["greatest"] * 1.5
    RENDER_WIDTH = CONFIG["width"]
    RENDER_HEIGHT = CONFIG["height"]
    RENDER_FILE = CONFIG["out_file"]
except KeyError:
    print("Failed to load RENDER_SETUP environment variable.")
    exit(1)


# add and setup camera
bpy.ops.object.camera_add(view_align=False, enter_editmode=False,
                          location = CAMERA_COORD)
camera_ob = bpy.data.objects[0]
camera = bpy.data.cameras[0]
camera.clip_end = CAMERA_CLIP
camera.ortho_scale = CAMERA_ORTHO
camera.type = CAMERA_TYPE



# add an empty for focusing the camera
bpy.ops.object.add(location=CAMERA_FOCUS)
target = bpy.data.objects[1]
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.track_set(type="TRACKTO")
bpy.ops.object.select_all(action="DESELECT")


if MODEL_EXT == 'stl':
    # import an stl model
    bpy.ops.import_mesh.stl(filepath=MODEL_PATH)
    
elif MODEL_EXT == 'obj':
    # import an obj model
    bpy.ops.import_scene.obj(
        filepath=MODEL_PATH, 
        use_smooth_groups=False, 
        use_image_search=False, 
        axis_forward="Y", 
        axis_up="Z")


# rotate the imported objects with meshes in the scene
if CAMERA_TYPE == "PERSP":
    for obj in bpy.data.objects[2:]:
        obj.rotation_euler[2]=-.3


# attempt to render
scene = bpy.data.scenes.values()[0]
scene.camera = camera_ob
scene.render.filepath = RENDER_FILE
scene.render.resolution_x = RENDER_WIDTH
scene.render.resolution_y = RENDER_HEIGHT
scene.render.resolution_percentage = 100
bpy.ops.render.render(write_still=True)
