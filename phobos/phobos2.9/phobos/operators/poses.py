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
Contains the Blender operators used to edit/add poses for Phobos models.
"""

import sys
import inspect

import bpy
import blf
import bgl
from bpy.props import StringProperty, FloatProperty, FloatVectorProperty, EnumProperty
from bpy.types import Operator
from phobos.phoboslog import log
import phobos.utils.selection as sUtils
import phobos.utils.blender as bUtils
import phobos.utils.naming as nUtils
import phobos.model.poses as poses
import phobos.model.models as models

# FIXME: this is ugly
current_robot_name = ''

# this is partly redundant, but currently only needed here
def get_robot_names(scene, context):
    """

    Args:
      scene:
      context:

    Returns:

    """
    robot_names = [(nUtils.getModelName(root),) * 3 for root in sUtils.getRootsOfSelection()]
    return robot_names


# currently only needed here, no point in putting in in poses.py
def get_pose_names(scene, context):
    """

    Args:
      scene:
      context:

    Returns:

    """
    poselist = poses.getPoses(current_robot_name)
    pose_items = [(pose,) * 3 for pose in poselist]
    return pose_items


# class StorePoseOperator2(Operator):
#     """Store the current pose of selected links in one of the scene's robots"""
#     bl_idname = 'phobos.store_pose2'
#     bl_label = "Store Current Pose"
#
#     robot_name = EnumProperty(
#         items=get_robot_names,
#         name="Robot",
#         description="Robot to store pose for"
#     )
#
#     pose_name = StringProperty(
#         name="Pose Name",
#         default="New Pose",
#         description="Name of new pose"
#     )
#
#     @classmethod
#     def poll(self, context):
#         modelsPosesColl = bUtils.getPhobosPreferences().models_poses
#         activeModelPoseIndex = bpy.context.scene.active_ModelPose
#         root = sUtils.isRoot(context.view_layer.objects.active)
#         return root and bpy.data.images[activeModelPoseIndex].name in modelsPosesColl.keys()
#
#     def invoke(self, context, event):
#         wm = context.window_manager
#         return wm.invoke_props_dialog(self,width=300,height=100)
#
#     def draw(self, context):
#         modelsPosesColl = bUtils.getPhobosPreferences().models_poses
#         activeModelPoseIndex = bpy.context.scene.active_ModelPose
#         row = self.layout
#         if modelsPosesColl[bpy.data.images[activeModelPoseIndex].name].type == 'robot_pose':
#             self.pose_name = modelsPosesColl[bpy.data.images[activeModelPoseIndex].name].label
#         else:
#             self.pose_name = "New Pose"
#         row.prop(self, "pose_name")
#
#     def execute(self, context):
#         modelsPosesColl = bUtils.getPhobosPreferences().models_poses
#         activeModelPoseIndex = bpy.context.scene.active_ModelPose
#         robot_name = modelsPosesColl[bpy.data.images[activeModelPoseIndex].name].robot_name
#         poses.storePose(robot_name, self.pose_name)
#         bpy.ops.scene.reload_models_and_poses_operator()
#         newPose = modelsPosesColl.add()
#         newPose.parent = robot_name
#         newPose.name = robot_name + '_' + self.pose_name
#         newPose.label = self.pose_name
#         # TODO delete me?
#         #newPose.path = pose["robotpath"]
#         newPose.type = "robot_pose"
#         newPose.robot_name = robot_name
#         newPose.icon = "X_VEC"
#         return {'FINISHED'}
#
#
# class LoadPoseOperator2(Operator):
#     """Load a previously stored pose for one of the scene's robots"""
#     bl_idname = 'phobos.load_pose2'
#     bl_label = "Load Selected Pose"
#
#     @classmethod
#     def poll(self, context):
#         result = False
#         modelsPosesColl = bUtils.getPhobosPreferences().models_poses
#         activeModelPoseIndex = bpy.context.scene.active_ModelPose
#         root = sUtils.isRoot(context.view_layer.objects.active)
#         if root and \
#            (bpy.data.images[activeModelPoseIndex].name in modelsPosesColl.keys()) and \
#            (modelsPosesColl[bpy.data.images[activeModelPoseIndex].name].robot_name == root["model/name"]) and \
#            (modelsPosesColl[bpy.data.images[activeModelPoseIndex].name].type == 'robot_pose'):
#             result = True
#         return result
#
#     def execute(self, context):
#         modelsPosesColl = bUtils.getPhobosPreferences().models_poses
#         activeModelPoseIndex = bpy.context.scene.active_ModelPose
#         modelPose = modelsPosesColl[bpy.data.images[activeModelPoseIndex].name]
#         root = sUtils.getRoot(context.view_layer.objects.active)
#         bpy.context.view_layer.objects.active = root
#         poses.loadPose(modelPose.robot_name, modelPose.label)
#         return {'FINISHED'}


class StorePoseOperator(Operator):
    """Store the current pose of selected links in one of the scene's robots"""

    bl_idname = 'phobos.store_pose'
    bl_label = "Store Current Pose"
    bl_options = {'REGISTER', 'UNDO'}

    robot_name : EnumProperty(
        items=get_robot_names, name="Robot", description="Robot to store pose for"
    )

    pose_name : StringProperty(name="Pose Name", default="New Pose", description="Name of new pose")

    def execute(self, context):
        """

        Args:
          context:

        Returns:

        """
        root = sUtils.getObjectByProperty('model/name', self.robot_name)
        poses.storePose(root, self.pose_name)
        return {'FINISHED'}


class LoadPoseOperator(Operator):
    """Load a previously stored pose for one of the scene's robots"""

    bl_idname = 'phobos.load_pose'
    bl_label = "Load Pose"
    bl_options = {'REGISTER', 'UNDO'}

    robot_name : EnumProperty(
        items=get_robot_names, name="Robot Name", description="Robot to load a pose for"
    )

    pose_name : EnumProperty(
        items=get_pose_names, name="Pose Name", description="Name of pose to load"
    )

    def execute(self, context):
        """

        Args:
          context:

        Returns:

        """
        global current_robot_name
        current_robot_name = self.robot_name
        poses.loadPose(self.robot_name, self.pose_name)
        return {'FINISHED'}


# show robot model on 3dview
def draw_preview_callback(self):
    """TODO Missing documentation"""

    # Search for View_3d window
    area = None
    if bpy.context.area.type != 'VIEW_3D':
        return bpy.context.area
    else:
        for oWindow in bpy.context.window_manager.windows:
            oScreen = oWindow.screen
            for oArea in oScreen.areas:
                if oArea.type == 'VIEW_3D':
                    area = oArea

    modelsPosesColl = bUtils.getPhobosPreferences().models_poses
    activeModelPoseIndex = bpy.context.scene.active_ModelPose

    if (len(modelsPosesColl) > 0) and area:

        # Draw a textured quad
        area_widths = [
            region.width for region in bpy.context.area.regions if region.type == 'WINDOW'
        ]
        area_heights = [
            region.height for region in bpy.context.area.regions if region.type == 'WINDOW'
        ]
        if (len(area_widths) > 0) and (len(area_heights) > 0):

            active_preview = modelsPosesColl[bpy.data.images[activeModelPoseIndex].name]
            im = bpy.data.images[activeModelPoseIndex]

            view_width = area_widths[0]
            view_height = area_heights[0]
            tex_start_x = 50
            tex_end_x = view_width - 50
            tex_start_y = 50
            tex_end_y = view_height - 50
            if im.size[0] < view_width:
                diff = int((view_width - im.size[0]) / 2)
                tex_start_x = diff
                tex_end_x = diff + im.size[0]
            if im.size[1] < view_height:
                diff = int((view_height - im.size[1]) / 2)
                tex_start_y = diff
                tex_end_y = diff + im.size[1]

            # Draw information
            font_id = 0  # XXX, need to find out how best to get this.
            blf.position(font_id, tex_start_x, tex_end_y + 20, 0)
            blf.size(font_id, 20, 72)
            blf.draw(font_id, active_preview.label)

            tex = im.bindcode
            bgl.glEnable(bgl.GL_TEXTURE_2D)
            # if using blender 2.77 change tex to tex[0]
            bgl.glBindTexture(bgl.GL_TEXTURE_2D, tex)

            # Background
            bgl.glEnable(bgl.GL_BLEND)

            bgl.glBegin(bgl.GL_QUADS)
            bgl.glColor4f(0, 0, 0, 0.3)
            bgl.glVertex2i(0, 0)
            bgl.glVertex2i(0, view_height)
            bgl.glVertex2i(view_width, view_height)
            bgl.glVertex2i(view_width, 0)

            # Draw Image
            bgl.glColor4f(1, 1, 1, 1)
            bgl.glTexCoord2f(0, 0)
            bgl.glVertex2i(int(tex_start_x), int(tex_start_y))
            bgl.glTexCoord2f(0, 1)
            bgl.glVertex2i(int(tex_start_x), int(tex_end_y))
            bgl.glTexCoord2f(1, 1)
            bgl.glVertex2i(int(tex_end_x), int(tex_end_y))
            bgl.glTexCoord2f(1, 0)
            bgl.glVertex2i(int(tex_end_x), int(tex_start_y))
            bgl.glEnd()

            # restore opengl defaults
            bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
            bgl.glDisable(bgl.GL_QUADS)
            bgl.glDisable(bgl.GL_BLEND)
            bgl.glDisable(bgl.GL_TEXTURE_2D)


class ChangePreviewOperator(bpy.types.Operator):
    """TODO Missing documentation"""

    bl_idname = "scene.change_preview"
    bl_label = "Change the preview texture"

    def execute(self, context):
        """

        Args:
          context:

        Returns:

        """
        modelsPosesColl = bUtils.getPhobosPreferences().models_poses
        activeModelPoseIndex = bpy.context.scene.active_ModelPose
        if bpy.data.images[activeModelPoseIndex].name in modelsPosesColl.keys():
            activeModelPose = modelsPosesColl[bpy.data.images[activeModelPoseIndex].name]
            if activeModelPose.type != "robot_name":
                # show on view_3d
                root = None
                if context.view_layer.objects.active != None:
                    root = sUtils.getRoot(context.view_layer.objects.active)
                if (
                    not bpy.context.scene.preview_visible
                    and (bpy.data.images[activeModelPoseIndex].type == 'IMAGE')
                    and (
                        root is None
                        or not sUtils.isRoot(root)
                        or not (
                            modelsPosesColl[bpy.data.images[activeModelPoseIndex].name]
                            != root["model/name"]
                        )
                        or len(bpy.context.selected_objects) == 0
                    )
                ):
                    bpy.ops.view3d.draw_preview_operator()
                    bpy.context.scene.preview_visible = True

            else:
                activeModelPose.hide = not activeModelPose.hide
                if activeModelPose.hide:
                    activeModelPose.icon = "RIGHTARROW"
                else:
                    activeModelPose.icon = "DOWNARROW_HLT"
                for modelPose in modelsPosesColl:
                    if (modelPose.type != "robot_name") and (
                        modelPose.parent == activeModelPose.name
                    ):
                        modelPose.hide = activeModelPose.hide

        return {'FINISHED'}


class DrawPreviewOperator(bpy.types.Operator):
    """TODO Missing documentation"""

    bl_idname = "view3d.draw_preview_operator"
    bl_label = "Draw preview to the View3D"

    def modal(self, context, event):
        """

        Args:
          context:
          event:

        Returns:

        """
        if event.type in {'LEFTMOUSE', 'RIGHTMOUSE', 'ESC'}:
            # TODO delete me?
            #            if bpy.context.scene.preview_visible:
            bpy.context.scene.preview_visible = False
            # TODO delete me?
            #           else:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def execute(self, context):
        """

        Args:
          context:

        Returns:

        """
        # the arguments we pass the the callback
        args = (self,)
        # Add the region OpenGL drawing callback
        # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
        if hasattr(self, "_handle") and self._handle:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')

        self._handle = bpy.types.SpaceView3D.draw_handler_add(
            draw_preview_callback, args, 'WINDOW', 'POST_PIXEL'
        )

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

classes = (
    StorePoseOperator,
    LoadPoseOperator,
    ChangePreviewOperator,
    DrawPreviewOperator,
)

def register():
    """TODO Missing documentation"""
    print("Registering operators.misc...")
    for classdef in classes:
        bpy.utils.register_class(classdef)


def unregister():
    """TODO Missing documentation"""
    print("Unregistering operators.misc...")
    for classdef in classes:
        bpy.utils.unregister_class(classdef)
