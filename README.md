# Blender Robotics Visualization

### Contents
This repo contains a collection of tools and resources used in Blender to provide high-quality image and video renders of robotics simulations/actions. This is not a single pipeline, but instead a collection of tools that can aid in the creation of renders within Blender. A description of some of the objects available is provided below, and further use is up to the individual needs of the project.

### Useful files:

**src/CSVAnimImport.py**:

This is a Blender script that can be used to import robot joint animation data into Blender by applying animation data to respective joint objects. Make note of the following steps when using the script:

1. Open the script in a Blender text editor
2. Set the filepath of the animation .csv file
3. Object names in Blender scene must match joint names in the columns of the target CSV file - this is used to lookup the objects to apply rotations to
4. Check the axes dict at the top of the script file - some experimenting must be done to check which axes the robot joints rotate on. This defines the local axes that each joint rotates around. (Currently all joints are assumed to be revolute)
5. Run the script in Blender - the console will show progress of the keyframe insertion. Depending on the length of the animation it may take a minute or two to load, because Blender needs to update the UI and render for each keyframe (switch to solid view for better performance).

After importing, you can use the keyframe scrollbar at the bottom to view the animation, set bounds, and edit parts of the movement. The zero'd position of the robot is saved at frame -1. From here you can treat the robot as any keyframed Blender object, and render out images/videos as you wish. 