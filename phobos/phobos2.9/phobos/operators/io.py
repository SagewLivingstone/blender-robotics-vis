#!/usr/bin/python3
# coding=utf-8

# -------------------------------------------------------------------------------
# This file is part of Phobos, a Blender Add-On to edit robot models.
# Copyright (C) 2020 University of Bremen & DFKI GmbH Robotics Innovation Center
#
# You should have received a copy of the 3-Clause BSD License in the LICENSE file.
# If not, see <https://opensource.org/licenses/BSD-3-Clause>.
# -------------------------------------------------------------------------------

"""
Contains all Blender operators for import and export of models/files.
"""

import os
import json
import sys
import inspect

import bpy
import bgl
import glob
from bpy.types import Operator
from bpy.props import EnumProperty, StringProperty, FloatProperty, IntProperty, BoolProperty

import phobos.defs as defs
import phobos.display as display
from phobos.phoboslog import log
import phobos.model.models as models
import phobos.model.links as links
import phobos.utils.selection as sUtils
import phobos.utils.editing as eUtils
import phobos.utils.io as ioUtils
import phobos.utils.blender as bUtils
import phobos.utils.naming as nUtils
from phobos.utils.io import securepath
import phobos.io.entities as entity_io
from phobos.io.entities import entity_types
from phobos.io.entities.entities import deriveGenericEntity


class ExportSceneOperator(Operator):
    """Export the selected model(s) in a scene"""

    bl_idname = "phobos.export_scene"
    bl_label = "Export Scene"
    bl_options = {'REGISTER', 'UNDO'}

    exportModels : BoolProperty(name='Export models in scene')
    sceneName : StringProperty(name='Scene name')

    def invoke(self, context, event):
        """

        Args:
          context:
          event:

        Returns:

        """
        self.sceneName = bpy.path.basename(bpy.context.blend_data.filepath)[:-6]
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        """

        Args:
          context:

        Returns:

        """
        # identify all entities' roots in the scene
        rootobjects = ioUtils.getEntityRoots()
        if not rootobjects:
            log("There are no entities to export!", "WARNING")

        # derive entities and export if necessary
        models = set()
        for root in entities:
            log("Adding entity '" + str(root["entity/name"]) + "' to scene.", "INFO")
            if root["entity/type"] in entity_types:
                # TODO delete me?
                # try:
                if (
                    self.exportModels
                    and 'export' in entity_types[root['entity/type']]
                    and root['model/name'] not in models
                ):
                    modelpath = os.path.join(
                        ioUtils.getExportPath(), self.sceneName, root['model/name']
                    )
                    exportModel(models.deriveModelDictionary(root), modelpath)
                    models.add(root['model/name'])
                # known entity export
                entity = entity_types[root["entity/type"]]['derive'](
                    root, os.path.join(ioUtils.getExportPath(), self.sceneName)
                )
                # TODO delete me?
                # except KeyError:
                #    log("Required method ""deriveEntity"" not implemented for type " + entity["entity/type"], "ERROR")
                #    continue
            # generic entity export
            else:
                entity = deriveGenericEntity(root)
            exportlist.append(entity)
        for scenetype in scene_types:
            typename = "export_scene_" + scenetype
            # check if format exists and should be exported
            if getattr(bpy.context.scene, typename):
                scene_types[scenetype]['export'](
                    exportlist, os.path.join(ioUtils.getExportPath(), self.sceneName)
                )
        return {'FINISHED'}


class ExportModelOperator(Operator):
    """Export the selected model"""

    bl_idname = "phobos.export_model"
    bl_label = "Export Model"
    bl_options = {'REGISTER'}

    modelname : EnumProperty(
        items=ioUtils.getModelListForEnumProp, name="Model", description="Model to export"
    )

    exportall : BoolProperty(
        default=False, name="Export all", description="Export all (selected) models in the scene."
    )

    def invoke(self, context, event):
        """

        Args:
          context:
          event:

        Returns:

        """
        modellist = ioUtils.getModelListForEnumProp(self, context)
        # show selection dialog for models
        if len(modellist) > 1:
            return context.window_manager.invoke_props_dialog(self)
        # unless only one model is available
        elif modellist:
            self.modelname = modellist[0][0]
            return self.execute(context)
        log("No propely defined models to export.", 'ERROR')
        return {'CANCELLED'}

    def execute(self, context):
        """

        Args:
          context:

        Returns:

        """
        roots = ioUtils.getExportModels()
        if not roots:
            log("No properly defined models selected or present in scene.", 'ERROR')
            return {'CANCELLED'}
        elif not self.exportall:
            roots = [root for root in roots if nUtils.getModelName(root) == self.modelname]
            if len(roots) > 1:
                log(
                    "Ambiguous model definitions: "
                    + self.modelname
                    + " exists "
                    + str(len(roots))
                    + " times.",
                    "ERROR",
                )
                return {'CANCELLED'}

        for root in roots:
            # setup paths
            exportpath = ioUtils.getExportPath()
            if not securepath(exportpath):
                log("Could not secure path to export to.", "ERROR")
                continue
            log("Export path: " + exportpath, "DEBUG")
            ioUtils.exportModel(models.deriveModelDictionary(root), exportpath)

        # select all exported models after export is done
        if ioUtils.getExpSettings().selectedOnly:
            for root in roots:
                objectlist = sUtils.getChildren(root, selected_only=True, include_hidden=False)
                sUtils.selectObjects(objectlist, clear=False)
        else:
            bpy.ops.object.select_all(action='DESELECT')
            for root in roots:
                sUtils.selectObjects(list([root]), False)
            bpy.ops.phobos.select_model()

        # TODO: Move mesh export to individual formats? This is practically SMURF
        # export meshes in selected formats
        # for meshtype in meshes.mesh_types:
        #     mesh_path = ioUtils.getOutputMeshpath(meshtype)
        #     try:
        #         typename = "export_mesh_" + meshtype
        #         if getattr(bpy.data.worlds[0], typename):
        #             securepath(mesh_path)
        #             for meshname in model['meshes']:
        #                 meshes.mesh_types[meshtype]['export'](model['meshes'][meshname], mesh_path)
        #     except KeyError:
        #         log("No export function available for selected mesh function: " + meshtype,
        #             "ERROR", "ExportModelOperator")
        #         print(sys.exc_info()[0])

        # TODO: Move texture export to individual formats? This is practically SMURF
        # export textures
        # if ioUtils.textureExportEnabled():
        #     texture_path = ''
        #     for materialname in model['materials']:
        #         mat = model['materials'][materialname]
        #         for texturetype in ['diffuseTexture', 'normalTexture', 'displacementTexture']:
        #             if texturetype in mat:
        #                 texpath = os.path.join(os.path.expanduser(bpy.path.abspath('//')), mat[texturetype])
        #                 if os.path.isfile(texpath):
        #                     if texture_path == '':
        #                         texture_path = securepath(os.path.join(export_path, 'textures'))
        #                         log("Exporting textures to " + texture_path, "INFO", "ExportModelOperator")
        #                     try:
        #                         shutil.copy(texpath, os.path.join(texture_path, os.path.basename(mat[texturetype])))
        #                     except shutil.SameFileError:
        #                         log("{} already in place".format(texturetype), "INFO", "ExportModelOperator")
        # report success to user
        log("Export successful.", "INFO", end="\n\n")
        return {'FINISHED'}


class ImportModelOperator(bpy.types.Operator):
    """Import robot model file from various formats"""

    bl_idname = "phobos.import_robot_model"
    bl_label = "Import Robot Model"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'FILE'

    # creating property for storing the path to the .scn file
    filepath : bpy.props.StringProperty(subtype="FILE_PATH")

    # entitytype : EnumProperty(
    #     name="Entity type",
    #     items=tuple(
    #         (e, e, 'file extensions: ' + str(entity_io.entity_types[e]['extensions']))
    #         for e in entity_io.entity_types
    #         if 'import' in entity_io.entity_types[e]
    #     ),
    #     description="Type of entity to import from file",
    # )

    @classmethod
    def poll(cls, context):
        """

        Args:
          context:

        Returns:

        """
        return context is not None

    def execute(self, context):
        """

        Args:
          context:

        Returns:

        """
        suffix = self.filepath.split(".")[-1]
        if suffix in entity_io.entity_types:
            log("Importing " + self.filepath + ' as ' + suffix, "INFO")
            model = entity_io.entity_types[suffix]['import'](self.filepath)
            # bUtils.cleanScene()
            models.buildModelFromDictionary(model)
            for layer in ['link', 'inertial', 'visual', 'collision', 'sensor']:
                bUtils.toggleLayer(layer, True)
        else:
            log("No module found to import " + suffix, "ERROR")

        return {'FINISHED'}

    def invoke(self, context, event):
        """

        Args:
          context:
          event:

        Returns:

        """
        self.filepath = bUtils.getPhobosPreferences().modelsfolder
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


# TODO use it or delete it... Own dev branch?
# class ViewExportOperator(Operator):
#     """Open a file explorer window in the export path"""
#     bl_idname = "phobos.view_export"
#     bl_label = "Export Scene"
#     bl_options = {'REGISTER', 'UNDO'}
#
#     def execute(self, context):
#        bpy.ops.wm.path_open(filepath=bpy.types.World.path)
#        return {'FINISHED'}


# FIXME: parameter?
def generateLibEntries(param1, param2):
    """

    Args:
      param1:
      param2:

    Returns:

    """
    # DOCU add some docstring
    with open(os.path.join(os.path.dirname(defs.__file__), "RobotLib.yml"), "r") as f:
        return [("None",) * 3] + [(entry,) * 3 for entry in json.loads(f.read())]


def loadModelsAndPoses():
    """TODO Missing documentation"""
    # DOCU add some docstring
    if bUtils.getPhobosPreferences().modelsfolder:
        modelsfolder = os.path.abspath(bUtils.getPhobosPreferences().modelsfolder)
    else:
        modelsfolder = ''
    modelsPosesColl = bUtils.getPhobosPreferences().models_poses
    robots_found = []
    print(modelsfolder)
    for root, dirs, files in os.walk(modelsfolder):
        for file in files:
            if os.path.splitext(file)[-1] == '.smurf':
                robots_found.append(os.path.join(root, file))
    robots_dict = dict()
    for robot in robots_found:
        with open(robot, 'r') as robot_smurf:
            robot_yml = json.loads(robot_smurf)
            model_name = robot_yml["modelname"]
            robot_files = robot_yml["files"]
            for file in robot_files:
                if file.split('_')[-1] == "poses.yml":
                    if model_name not in robots_dict:
                        robots_dict[model_name] = []
                    with open(os.path.join(os.path.dirname(robot), file)) as poses:
                        poses_yml = json.loads(poses)
                        for pose in poses_yml['poses']:
                            robots_dict[model_name].append({"posename": pose['name']})
                            robots_dict[model_name][-1]["robotpath"] = os.path.dirname(robot)

    modelsPosesColl.clear()
    for model_name in robots_dict.keys():
        item = modelsPosesColl.add()
        item.robot_name = model_name
        item.name = model_name
        item.label = model_name
        item.type = "robot_name"
        if item.hide:
            item.icon = "RIGHTARROW"
        else:
            item.icon = "DOWNARROW_HLT"
        current_parent = item.name
        for pose in robots_dict[model_name]:
            item = modelsPosesColl.add()
            item.parent = current_parent
            item.name = model_name + '_' + pose["posename"]
            item.label = pose["posename"]
            item.path = pose["robotpath"]
            item.type = "robot_pose"
            item.robot_name = model_name
            item.icon = "X_VEC"
            search_path = pose["robotpath"]
            if os.path.split(search_path)[-1] == "smurf":
                search_path = os.path.dirname(search_path)
            for file in glob.glob(
                search_path + "/**/" + model_name + "_" + pose['posename'] + ".*"
            ) + glob.glob(search_path + "/" + model_name + "_" + pose['posename'] + ".*"):
                if (os.path.splitext(file)[-1].lower() == ".stl") or (
                    os.path.splitext(file)[-1].lower() == ".obj"
                ):
                    item.model_file = os.path.join(search_path, file)
                if os.path.splitext(file)[-1].lower() == ".png":
                    item.preview = os.path.join(search_path, file)
                    item.name = os.path.split(file)[-1]


class ReloadModelsAndPosesOperator(bpy.types.Operator):
    """Tooltip"""

    bl_idname = "scene.reload_models_and_poses_operator"
    bl_label = "Reload Models and Poses"

    def execute(self, context):
        """

        Args:
          context:

        Returns:

        """
        loadModelsAndPoses()
        modelsPosesColl = bUtils.getPhobosPreferences().models_poses
        for model_pose in modelsPosesColl:
            if model_pose.name not in bpy.data.images.keys():
                if model_pose.type == 'robot_name':
                    bpy.data.images.new(model_pose.name, 0, 0)
                elif 'robot_pose':
                    if model_pose.preview != '':
                        if os.path.split(model_pose.preview)[-1] in bpy.data.images.keys():
                            bpy.data.images[os.path.split(model_pose.preview)[-1]].reload()
                        im = bpy.data.images.load(model_pose.preview)
                        model_pose.name = im.name
                        # im.name = model_pose.name
                        im.gl_load(0, bgl.GL_LINEAR, bgl.GL_LINEAR)
                    else:
                        bpy.data.images.new(model_pose.name, 0, 0)
            else:
                bpy.data.images[model_pose.name].reload()
                bpy.data.images[model_pose.name].gl_load(0, bgl.GL_LINEAR, bgl.GL_LINEAR)
        return {'FINISHED'}


class ImportLibRobot(Operator):
    """Import a baked robot into the robot library"""

    bl_idname = "phobos.import_lib_robot"
    bl_label = "Import Baked Robot"
    bl_options = {'REGISTER', 'UNDO'}

    filepath : bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        """

        Args:
          context:

        Returns:

        """
        libPath = os.path.join(os.path.dirname(defs.__file__), "RobotLib.yml")
        path, file = os.path.split(self.filepath)
        if file.endswith(".bake"):
            with open(self.filepath, "r") as f:
                info = json.loads(f.read())
            if not os.path.isfile(libPath):
                open(libPath, "a").close()
            with open(libPath, "r+") as f:
                robot_lib = json.loads(f.read())
                robot_lib = robot_lib if robot_lib is not None else {}
                robot_lib[info["name"]] = path
                f.seek(0)
                f.write(json.dumps(robot_lib, indent=2))
                f.truncate()
        else:
            log("This is no robot bake!", "ERROR")
        return {"FINISHED"}

    def invoke(self, context, event):
        """

        Args:
          context:
          event:

        Returns:

        """
        # create the open file dialog
        context.window_manager.fileselect_add(self)

        return {'RUNNING_MODAL'}


class ImportSelectedLibRobot(Operator):
    """Import a baked robot into the robot library"""

    bl_idname = "scene.phobos_import_selected_lib_robot"
    bl_label = "Import Baked Robot"

    obj_name : StringProperty(
        name="New Smurf Entity Name", default="New Robot", description="Name of new Smurf Entity"
    )

    @classmethod
    def poll(self, context):
        """

        Args:
          context:

        Returns:

        """
        result = False
        modelsPosesColl = bUtils.getPhobosPreferences().models_poses
        activeModelPoseIndex = bpy.context.scene.active_ModelPose
        root = None
        # TODO delete me?
        # print("modelfile: ("+modelsPosesColl[bpy.data.images[activeModelPoseIndex].name].model_file+")")
        if context.view_layer.objects.active != None:
            root = sUtils.getRoot(context.view_layer.objects.active)
        try:
            if (
                not root
                or not sUtils.isRoot(root)
                or bpy.data.images[activeModelPoseIndex].name in modelsPosesColl.keys()
                and modelsPosesColl[bpy.data.images[activeModelPoseIndex].name].model_file != ''
                and len(bpy.context.selected_objects) == 0
                or modelsPosesColl[bpy.data.images[activeModelPoseIndex].name].robot_name
                != root["model/name"]
            ):
                result = True
        except KeyError:
            result = False
        return result

    def invoke(self, context, event):
        """

        Args:
          context:
          event:

        Returns:

        """
        wm = context.window_manager
        modelsPosesColl = bUtils.getPhobosPreferences().models_poses
        activeModelPoseIndex = bpy.context.scene.active_ModelPose

        selected_robot = modelsPosesColl[bpy.data.images[activeModelPoseIndex].name]
        if selected_robot.model_file != '':
            return wm.invoke_props_dialog(self, width=300, height=100)
        else:
            return {"CANCELLED"}

    def draw(self, context):
        """

        Args:
          context:

        Returns:

        """
        row = self.layout
        row.prop(self, "obj_name")

    def execute(self, context):
        """

        Args:
          context:

        Returns:

        """
        log("Import robot bake", "INFO")
        modelsPosesColl = bUtils.getPhobosPreferences().models_poses
        activeModelPoseIndex = bpy.context.scene.active_ModelPose
        selected_robot = modelsPosesColl[bpy.data.images[activeModelPoseIndex].name]
        if selected_robot.type != "robot_name":
            if os.path.splitext(selected_robot.model_file)[-1] == ".obj":
                bpy.ops.import_scene.obj(
                    filepath=selected_robot.model_file,
                    axis_forward='-Z',
                    axis_up='Y',
                    filter_glob="*.obj;*.mtl",
                    use_edges=True,
                    use_smooth_groups=True,
                    use_split_objects=True,
                    use_split_groups=True,
                    use_groups_as_vgroups=False,
                    use_image_search=True,
                    split_mode='ON',
                    global_clamp_size=0,
                )
            elif os.path.splitext(selected_robot.model_file)[-1] == ".stl":
                bpy.ops.import_mesh.stl(
                    filepath=selected_robot.model_file,
                    axis_forward='Y',
                    axis_up='Z',
                    filter_glob="*.stl",
                    files=[],
                    directory="",
                    global_scale=1,
                    use_scene_unit=True,
                    use_facet_normal=False,
                )
            robot_obj = bpy.context.selected_objects[0]
            bpy.context.view_layer.objects.active = robot_obj
            robot_obj.name = self.obj_name
            robot_obj["model/name"] = selected_robot.robot_name
            robot_obj["entity/name"] = self.obj_name
            robot_obj["entity/type"] = "smurf"
            robot_obj["entity/pose"] = selected_robot.label
            robot_obj["entity/isReference"] = True
            robot_obj.phobostype = 'entity'
        return {'FINISHED'}


class CreateRobotInstance(Operator):
    """Create a new instance of the selected robot lib entry"""

    bl_idname = "phobos.create_robot_instance"
    bl_label = "Create Robot Instance"
    bl_options = {'REGISTER', 'UNDO'}

    bakeObj : EnumProperty(
        name="Robot Lib Entries", items=generateLibEntries, description="The robot lib entries"
    )

    robName : StringProperty(
        name="Instance Name", default="instance", description="The instance's name"
    )

    def execute(self, context):
        """

        Args:
          context:

        Returns:

        """
        if self.bakeObj == "None":
            return {"FINISHED"}
        with open(os.path.join(os.path.dirname(defs.__file__), "RobotLib.yml"), "r") as f:
            robot_lib = json.loads(f.read())
        root = links.createLink(1.0, name=self.robName + "::" + self.bakeObj)
        root["model/name"] = self.bakeObj
        root["entity/name"] = self.robName
        root["isInstance"] = True
        bpy.ops.import_mesh.stl(filepath=os.path.join(robot_lib[self.bakeObj], "bake.stl"))
        bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
        obj = context.active_object
        obj.name = self.robName + "::visual"
        obj.phobostype = "visual"
        eUtils.parentObjectsTo(obj, root)
        return {"FINISHED"}

    @classmethod
    def poll(self, context):
        """

        Args:
          context:

        Returns:

        """
        return os.path.isfile(os.path.join(os.path.dirname(defs.__file__), "RobotLib.yml"))


class ExportCurrentPoseOperator(Operator):
    """Bake the selected model"""

    bl_idname = "phobos.export_current_poses"
    bl_label = "Export Selected Pose"

    decimate_type : EnumProperty(
        name="Decimate Type",
        items=[
            ('COLLAPSE', 'Collapse', 'COLLAPSE'),
            ('UNSUBDIV', 'Un-Subdivide', 'UNSUBDIV'),
            ('DISSOLVE', 'Planar', 'DISSOLVE'),
        ],
    )
    decimate_ratio : FloatProperty(name="Ratio", default=0.15)
    decimate_iteration : IntProperty(name="Iterations", default=1)
    decimate_angle_limit : FloatProperty(name="Angle Limit", default=5)

    @classmethod
    def poll(self, context):
        """

        Args:
          context:

        Returns:

        """
        modelsPosesColl = bUtils.getPhobosPreferences().models_poses
        activeModelPoseIndex = bpy.context.scene.active_ModelPose
        return (
            context.selected_objects
            and context.active_object
            and sUtils.isRoot(context.active_object)
            and bpy.data.images[activeModelPoseIndex].name in modelsPosesColl.keys()
            and modelsPosesColl[bpy.data.images[activeModelPoseIndex].name].robot_name
            == context.active_object['model/name']
            and modelsPosesColl[bpy.data.images[activeModelPoseIndex].name].type == 'robot_pose'
        )

    def invoke(self, context, event):
        """

        Args:
          context:
          event:

        Returns:

        """
        wm = context.window_manager
        bpy.context.scene.render.resolution_x = 256
        bpy.context.scene.render.resolution_y = 256
        bpy.context.scene.render.resolution_percentage = 100
        return wm.invoke_props_dialog(self, width=300, height=100)

    def draw(self, context):
        """

        Args:
          context:

        Returns:

        """
        row = self.layout
        row.label(text="Model Export Properties:")
        row.prop(self, "decimate_type")
        if self.decimate_type == 'COLLAPSE':
            row.prop(self, "decimate_ratio")
        elif self.decimate_type == 'UNSUBDIV':
            row.prop(self, "decimate_iteration")
        elif self.decimate_type == 'DISSOLVE':
            row.prop(self, "decimate_angle_limit")
        rd = bpy.context.scene.render
        # TODO delete me?
        # image_settings = rd.image_settings
        row.label(text="Preview Properties:")
        row.label(text="Resolution:")
        row.prop(rd, "resolution_x", text="X")
        row.prop(rd, "resolution_y", text="Y")
        row.prop(rd, "resolution_percentage", text="")
        # TODO delete me?
        # row.label(text="File Format:")
        # row.template_image_settings(image_settings, color_management=False)

    def check(self, context):
        """

        Args:
          context:

        Returns:

        """
        return True

    def execute(self, context):
        """

        Args:
          context:

        Returns:

        """
        root = sUtils.getRoot(context.selected_objects[0])

        modelsPosesColl = bUtils.getPhobosPreferences().models_poses
        activeModelPoseIndex = bpy.context.scene.active_ModelPose
        selected_robot = modelsPosesColl[bpy.data.images[activeModelPoseIndex].name]

        objectlist = sUtils.getChildren(root, selected_only=True, include_hidden=False)
        sUtils.selectObjects([root] + objectlist, clear=True, active=0)
        models.loadPose(selected_robot.robot_name, selected_robot.label)
        parameter = self.decimate_ratio
        if self.decimate_type == 'UNSUBDIV':
            parameter = self.decimate_iteration
        elif self.decimate_type == 'DISSOLVE':
            parameter = self.decimate_angle_limit
        exporter.bakeModel(
            objectlist,
            root['model/name'],
            selected_robot.label,
            decimate_type=self.decimate_type,
            decimate_parameter=parameter,
        )
        sUtils.selectObjects([root] + objectlist, clear=True, active=0)
        bpy.ops.scene.reload_models_and_poses_operator()
        return {'FINISHED'}


class ExportAllPosesOperator(Operator):
    """Bake the selected model"""

    bl_idname = "phobos.export_all_poses"
    bl_label = "Export All Poses"
    # TODO update bl options
    # bl_options = {'REGISTER', 'UNDO'}
    decimate_type : EnumProperty(
        name="Decimate Type",
        items=[
            ('COLLAPSE', 'Collapse', 'COLLAPSE'),
            ('UNSUBDIV', 'Un-Subdivide', 'UNSUBDIV'),
            ('DISSOLVE', 'Planar', 'DISSOLVE'),
        ],
    )
    decimate_ratio : FloatProperty(name="Ratio", default=0.15)
    decimate_iteration : IntProperty(name="Iterations", default=1)
    decimate_angle_limit : FloatProperty(name="Angle Limit", default=5)

    @classmethod
    def poll(self, context):
        """

        Args:
          context:

        Returns:

        """
        return (
            bpy.context.selected_objects
            and context.active_object
            and sUtils.isRoot(context.active_object)
        )

    def invoke(self, context, event):
        """

        Args:
          context:
          event:

        Returns:

        """
        wm = context.window_manager
        bpy.context.scene.render.resolution_x = 256
        bpy.context.scene.render.resolution_y = 256
        bpy.context.scene.render.resolution_percentage = 100
        return wm.invoke_props_dialog(self, width=300, height=100)

    def draw(self, context):
        """

        Args:
          context:

        Returns:

        """
        row = self.layout
        row.label(text="Model Export Properties:")
        row.prop(self, "decimate_type")
        if self.decimate_type == 'COLLAPSE':
            row.prop(self, "decimate_ratio")
        elif self.decimate_type == 'UNSUBDIV':
            row.prop(self, "decimate_iteration")
        elif self.decimate_type == 'DISSOLVE':
            row.prop(self, "decimate_angle_limit")
        rd = bpy.context.scene.render
        # TODO delete me?
        # image_settings = rd.image_settings
        row.label(text="Preview Properties:")
        row.label(text="Resolution:")
        row.prop(rd, "resolution_x", text="X")
        row.prop(rd, "resolution_y", text="Y")
        row.prop(rd, "resolution_percentage", text="")
        # TODO delete me?
        # row.label(text="File Format:")
        # row.template_image_settings(image_settings, color_management=False)

    def check(self, context):
        """

        Args:
          context:

        Returns:

        """
        return True

    def execute(self, context):
        """

        Args:
          context:

        Returns:

        """
        root = sUtils.getRoot(context.selected_objects[0])
        objectlist = sUtils.getChildren(root, selected_only=True, include_hidden=False)
        sUtils.selectObjects(objectlist)
        poses = models.getPoses(root['model/name'])
        i = 1
        for pose in poses:
            sUtils.selectObjects([root] + objectlist, clear=True, active=0)
            models.loadPose(root['model/name'], pose)
            parameter = self.decimate_ratio
            if self.decimate_type == 'UNSUBDIV':
                parameter = self.decimate_iteration
            elif self.decimate_type == 'DISSOLVE':
                parameter = self.decimate_angle_limit
            exporter.bakeModel(
                objectlist,
                root['model/name'],
                pose,
                decimate_type=self.decimate_type,
                decimate_parameter=parameter,
            )
            display.setProgress(i / len(poses))
            i += 1
        display.endProgress()
        sUtils.selectObjects([root] + objectlist, clear=True, active=0)
        bpy.ops.scene.reload_models_and_poses_operator()
        return {'FINISHED'}

classes = (
    ExportSceneOperator,
    ExportModelOperator,
    ImportModelOperator,
    ReloadModelsAndPosesOperator,
    ImportLibRobot,
    ImportSelectedLibRobot,
    CreateRobotInstance,
    ExportCurrentPoseOperator,
    ExportAllPosesOperator,
    )

def register():
    """TODO Missing documentation"""
    print("Registering operators.io...")
    for classdef in classes:
        bpy.utils.register_class(classdef)


def unregister():
    """TODO Missing documentation"""
    print("Unregistering operators.io...")
    for classdef in classes:
        bpy.utils.unregister_class(classdef)
