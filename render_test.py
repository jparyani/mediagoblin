#!/usr/bin/env python

import subprocess, json


# import the model
#model, ext, gr = ("/home/aeva/library/models/octocat_ascii.stl", "stl", 131.8)
model, ext, gr = ("/home/aeva/library/models/psycho/printme.obj", "obj", 93.4)


args = "blender blender_render.blend -F JPEG -P blender_render.py".split(" ")
env = {
    "DISPLAY" : ":0",
    "RENDER_SETUP" : json.dumps({            
            "out_file" : "foo.jpg",
            "model_path" : model,
            "model_ext" : ext,
            "greatest" : gr,
            "camera_coord" : [0, gr*-1.5, gr],
            "camera_focus" : (0, 0, gr/2.0),
            "camera_clip" : gr*10,
            "projection" : "PERSP", # "ORTHO" or "PERSP"
            "width" : 800,
            "height" : 800,
            })
    }

subprocess.call(args, env=env)
#subprocess.call(["eog", "foo.jpg"])
