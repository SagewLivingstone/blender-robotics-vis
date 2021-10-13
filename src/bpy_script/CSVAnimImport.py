import bpy, csv
from math import radians

# ----------------------
#       CONSTANTS
# ----------------------
#  Set these before running script as needed
MOTION_FILE_PATH = r'C:\Users\cocot\Downloads\9H7G_condition_1_camera_trial1_W3C.csv'
FRAMES_PER_SECOND = bpy.context.scene.render.fps
AXES = {  # Which axis (local) to rotate each joint on
    "j0": "Z",
    "j1": "Y",
    "j2": "X",
    "j3": "Y",
    "j4": "X",
    "j5": "Y",
    "j6": "X"
}

def lprint(message, mode="OUTPUT"):
    """
    Print with info attached
    """
    print("CSVAnimReader::" + mode + ": " + message)

def getJointsFromHeaders(headers):
    """
    Get joint names from headers and find associated objects in scene
    --
    returns dict of name:object (in scene)
    """
    dict = {}
    for name in headers:
        if name == 'time':
            continue
        
        dict[name] = bpy.data.objects[name]
    
    return dict

def readCSVAnimationFile(fp):
    """
    Main function to read csv animation and output keyframes
    """
    
    lprint("Reading file at path: " + fp)

    with open(fp) as csvfile:
        reader = csv.reader(csvfile)
        
        headers = None
        objs = None
        
        lprint("File read successfully, importing keyframes")
        
        for i, row in enumerate(reader):
            if i == 0:
                # Title
                headers = row
                objs = getJointsFromHeaders(headers)
                continue
            
            time = 0
            for col, val in zip(headers, row):
                # Body row
                if col == "time":
                    time = float(val.replace(',',''))
                    continue
                
                # Save original rotation
                orig_rot = objs[col].rotation_euler.copy()
                objs[col].rotation_euler = [0,0,0]
                
                # Set obj rot from csv data
                rot_value = float(val.replace(',',''))
                objs[col].rotation_euler.rotate_axis(AXES[col], rot_value)
                
                # Insert the new keyframe
                frame = int(time * FRAMES_PER_SECOND)
                print("Adding keyframe: [" + str(frame) + "]", end='\r')
                objs[col].keyframe_insert(data_path="rotation_euler",
                                            frame=frame)
                
                # Reset rotation back to where it was
                objs[col].rotation_euler = [0,0,0]
            
            for col in headers:
                if col == "time":
                    continue
                
                objs[col].rotation_euler = [0,0,0]
                objs[col].keyframe_insert(data_path="rotation_euler",
                                            frame=-1)
            
    lprint("Done loading csv animation.")

if __name__ == "__main__":
    readCSVAnimationFile(MOTION_FILE_PATH)