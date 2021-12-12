import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator
from bpy.utils import register_class

from bpy.props import (
    BoolProperty,
    CollectionProperty,
    StringProperty,
)

import math
import os
import struct

pitch_offset = math.radians(90)
bpy.context.scene.render.fps = 60.0

# helper read functions
def read_bytes_int32(fs):
    return struct.unpack("i", bytearray(fs.read(4)))[0]

def read_bytes_float32(fs):
    return struct.unpack("f", bytearray(fs.read(4)))[0]

def read_bytes_double64(fs):
    return struct.unpack("d", bytearray(fs.read(8)))[0]

def read_bytes_uint16(fs):
    return struct.unpack("H", bytearray(fs.read(2)))[0]

def read_bytes_float3(fs):
    vec = []
    vec.append(read_bytes_float32(fs)) #x
    vec.append(read_bytes_float32(fs)) #y
    vec.append(read_bytes_float32(fs)) #z
    return vec

################################################################
 
class SCTGeomImporter(Operator, ImportHelper):
    bl_idname = 'sct.import_geom'
    bl_label = 'Import File(s)'
    bl_options = {'PRESET', 'UNDO'}
 
    filename_ext = '.*'
    
    filter_glob: StringProperty(
        default='*.*',
        options={'HIDDEN'}
    )
 
    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement,
        options={'HIDDEN', 'SKIP_SAVE'},
    ) 
    
    def import_sct(self, filename):
        print("file: " + filename)
        # parse file and create anim
        with open(filename, 'rb') as fs:
            # read header
            version = read_bytes_int32(fs)
            frame_count = read_bytes_int32(fs)
            device_orientation = read_bytes_int32(fs)
            horizontal_fov = read_bytes_float32(fs)
            vertical_fov = read_bytes_float32(fs)
            focal_length_x = read_bytes_float32(fs)
            focal_length_y = read_bytes_float32(fs)
            capture_type = read_bytes_int32(fs)
    
            print("version: " + str(version) + "\n" + "fc: " + str(frame_count) + "\n" + "o: " + str(device_orientation) + "\n" + "type: " + str(capture_type) + "\n")

            # create anchors
            user_anchor_count = read_bytes_int32(fs)
            for i in range(user_anchor_count):
                anchor_pos = read_bytes_float3(fs)
                bpy.ops.mesh.primitive_uv_sphere_add(
                    radius=0.1,
                    location=(anchor_pos[0], -anchor_pos[2], anchor_pos[1]),
                    scale=(1, 1, 1)
                )
                bpy.context.object.name = "Anhor_" + str(i)
        
            # create camera
            cam = bpy.ops.object.camera_add(enter_editmode=False, 
                align='WORLD', 
                location=(0, 0, 0), 
                rotation=(0, 0, 0), 
                scale=(1, 1, 1))
                
            obj = bpy.context.object
            # Set the relevant camera properties
            obj.data.angle_x = math.radians(horizontal_fov)

            # create animation
            bpy.context.scene.frame_start = 0
            bpy.context.scene.frame_end = frame_count
            bpy.context.scene.frame_set(0)

            for i in range(frame_count):        
                timestamp = read_bytes_double64(fs)
                location = read_bytes_float3(fs)
                rotation = read_bytes_float3(fs)
                exposure_offset = read_bytes_float32(fs)
                exposure_duration = read_bytes_double64(fs)
        
                obj.location = (location[0], -location[2], location[1])
                obj.keyframe_insert(data_path="location", frame=i)
        
                #PYR TO PRY. Add 90 degrees offset to Pitch
                obj.rotation_mode = "XYZ"
                obj.rotation_euler = (pitch_offset+rotation[0],rotation[2],rotation[1])
                obj.keyframe_insert(data_path="rotation_euler", frame=i)
        
        
    def execute(self, context):
        for file in self.files:
            filename = file.name
            directory = os.path.dirname(self.filepath)

            if filename.endswith(".dat"):
                self.import_sct(os.path.join(directory, filename))
            elif filename.endswith(".obj"):
                bpy.ops.import_scene.obj(filepath=os.path.join(directory, filename))
                
        return {'FINISHED'}

 
register_class(SCTGeomImporter)

bpy.ops.sct.import_geom('INVOKE_DEFAULT')
