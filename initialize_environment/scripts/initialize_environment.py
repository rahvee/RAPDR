#!/usr/bin/env python
# Modified from RethinkRobotics website

import argparse
import struct
import sys
import copy

import rospy
import rospkg

from gazebo_msgs.srv import (
    SpawnModel,
    DeleteModel,
    GetModelState,
    GetLinkState,
)
from gazebo_msgs.msg import (
    LinkState,
)
from geometry_msgs.msg import (
    PoseStamped,
    Pose,
    Point,
    Quaternion,
)
from std_msgs.msg import (
    Header,
    Empty,
)

from tf.transformations import *


#SPAWN WALL AT 1.1525 z to be above table or 0.3755 to be below
def load_gazebo_models(table_pose=Pose(position=Point(x=1, y=0.0, z=0.0)),
                       table_reference_frame="world",
                       block_pose=Pose(position=Point(x=0.8, y=0.0185, z=0.8)),
                       right_button_pose=Pose(position=Point(x=0.525, y=-0.2715, z=0.8)),
                       left_button_pose=Pose(position=Point(x=0.525, y=0.1515, z=0.8)),
                       block_reference_frame="world"):
    # Get Models' Path
    #print("rospkg stuff: ")
    #print(rospkg.RosPack().get_path('initialize'))
    model_path = rospkg.RosPack().get_path('initialize_environment')+"/models/"
    # Load Table SDF
    table_xml = ''
    with open (model_path + "cafe_table/model.urdf", "r") as table_file:
        table_xml=table_file.read().replace('\n', '')
    block_xml = ''
    with open (model_path + "block/model.urdf", "r") as block_file:
        block_xml=block_file.read().replace('\n', '')
    right_button_xml = ''
    with open (model_path + "button/model.urdf", "r") as button_file:
        button_xml=button_file.read().replace('\n', '')
    left_button_xml = ''
    with open (model_path + "button/model.urdf", "r") as button_file:
        button_xml=button_file.read().replace('\n', '')
        
        
    # Spawn Table SDF
    rospy.wait_for_service('/gazebo/spawn_sdf_model')

    try:
        spawn_sdf = rospy.ServiceProxy('/gazebo/spawn_sdf_model', SpawnModel)
        resp_sdf = spawn_sdf("cafe_table", table_xml, "/",
                             table_pose, table_reference_frame)
    except rospy.ServiceException, e:
        rospy.logerr("Spawn SDF service call failed: {0}".format(e))
    
    
    # Spawn Block URDF
    rospy.wait_for_service('/gazebo/spawn_urdf_model')
    try:
        spawn_urdf = rospy.ServiceProxy('/gazebo/spawn_urdf_model', SpawnModel)
        resp_urdf = spawn_urdf("block", block_xml, "/",
                               block_pose, block_reference_frame)
    except rospy.ServiceException, e:
        rospy.logerr("Spawn URDF service call failed: {0}".format(e))
    rospy.wait_for_service('/gazebo/spawn_urdf_model')

    try:
        spawn_urdf = rospy.ServiceProxy('/gazebo/spawn_urdf_model', SpawnModel)
        resp_urdf = spawn_urdf("right_button", button_xml, "/",
                               right_button_pose, block_reference_frame)
    except rospy.ServiceException, e:
        rospy.logerr("Spawn URDF service call failed: {0}".format(e))
    rospy.wait_for_service('/gazebo/spawn_urdf_model')

    try:
        spawn_urdf = rospy.ServiceProxy('/gazebo/spawn_urdf_model', SpawnModel)
        resp_urdf = spawn_urdf("left_button", button_xml, "/",
                               left_button_pose, block_reference_frame)
    except rospy.ServiceException, e:
        rospy.logerr("Spawn URDF service call failed: {0}".format(e))


def delete_gazebo_models():
    # This will be called on ROS Exit, deleting Gazebo models
    # Do not wait for the Gazebo Delete Model service, since
    # Gazebo should already be running. If the service is not
    # available since Gazebo has been killed, it is fine to error out
    try:
        delete_model = rospy.ServiceProxy('/gazebo/delete_model', DeleteModel)
        resp_delete = delete_model("cafe_table")
        resp_delete = delete_model("block")
        resp_delete = delete_model("button")
    except rospy.ServiceException, e:
        rospy.loginfo("Delete Model service call failed: {0}".format(e))
        
def blockPoseToGripper(poseVar):
    newPose = poseVar.pose
    #newPose.position.z -= 1.075
    newPose.position.z -= 1.075
    oldOrientationQ = newPose.orientation
    #oldOrientationRPY = euler_from_quaternion([oldOrientationQ.x, oldOrientationQ.y, oldOrientationQ.z, oldOrientationQ.w])
    #print(type(oldOrientationRPY))
    #q_orientation = quaternion_from_euler(3.14, 0, 0).tolist()
    q_orientation = quaternion_from_euler(3.14, 0, 0).tolist()
    newPose.orientation = Quaternion(q_orientation [0], q_orientation [1], q_orientation [2],q_orientation [3])
    newPoseStamped = PoseStamped(header = poseVar.header, pose = newPose)
    return newPoseStamped

def main():

    rospy.init_node("search_and_rescue")
    load_gazebo_models()
    #rospy.wait_for_message("/robot/sim/started", Empty)    

    pub_cafe_table_pose = rospy.Publisher('cafe_table_pose', PoseStamped, queue_size = 10)
    pub_grey_wall_pose = rospy.Publisher('grey_wall_pose', PoseStamped, queue_size = 10)
    pub_block_pose = rospy.Publisher('block_pose', PoseStamped, queue_size = 10)
    pub_right_button_pose = rospy.Publisher('right_button_pose', PoseStamped, queue_size = 10)
    pub_left_button_pose = rospy.Publisher('left_button_pose', PoseStamped, queue_size = 10)

    pub_left_gripper_pose = rospy.Publisher('left_gripper_pose', Point, queue_size = 10)
    pub_right_gripper_pose = rospy.Publisher('right_gripper_pose', Point, queue_size = 10)
    
    frameid_var = "/world"

    while not rospy.is_shutdown():
		
        rate = rospy.Rate(10) # 10hz
		
        #Get cafe_table pose
        rospy.wait_for_service('/gazebo/get_model_state')
        try:
            cafe_table_ms = rospy.ServiceProxy('/gazebo/get_model_state', GetModelState)
            resp_cafe_table_ms = cafe_table_ms("cafe_table", "");
            pose_cafe_table = resp_cafe_table_ms.pose
            header_cafe_table = resp_cafe_table_ms.header
            header_cafe_table.frame_id = frameid_var
            poseStamped_cafe_table = PoseStamped(header=header_cafe_table, pose=pose_cafe_table)
            pub_cafe_table_pose.publish(poseStamped_cafe_table)
        except rospy.ServiceException, e:
            rospy.logerr("get_model_state for cafe_table service call failed: {0}".format(e))

        #Get grey_wall pose
        rospy.wait_for_service('/gazebo/get_link_state')
        try:
            grey_wall_ms = rospy.ServiceProxy('/gazebo/get_link_state', GetLinkState)
            resp_grey_wall_ms = grey_wall_ms("grey_wall_link", "");
            pose_grey_wall = resp_grey_wall_ms.link_state.pose
            reference_grey_wall = resp_grey_wall_ms.link_state.reference_frame
            header_grey_wall = Header(frame_id=reference_grey_wall)
            header_grey_wall.frame_id = frameid_var
            poseStamped_grey_wall = PoseStamped(header=header_grey_wall, pose=pose_grey_wall)
            pub_grey_wall_pose.publish(poseStamped_grey_wall)
        except rospy.ServiceException, e:
            rospy.logerr("get_model_state for grey_wall service call failed: {0}".format(e))

        #Get block pose
        rospy.wait_for_service('/gazebo/get_model_state')
        try:
            block_ms = rospy.ServiceProxy('/gazebo/get_model_state', GetModelState)
            resp_block_ms = block_ms("block", "");
            pose_block = resp_block_ms.pose
            header_block = resp_block_ms.header
            header_block.frame_id = frameid_var
            poseStamped_block = PoseStamped(header=header_block, pose=pose_block)
            #pub_block_pose.publish(poseStamped_block)
            pub_block_pose.publish(blockPoseToGripper(poseStamped_block))
        except rospy.ServiceException, e:
            rospy.logerr("get_model_state for block service call failed: {0}".format(e))

        #Get right_button pose
        rospy.wait_for_service('/gazebo/get_model_state')
        try:
            right_button_ms = rospy.ServiceProxy('/gazebo/get_model_state', GetModelState)
            resp_right_button_ms = right_button_ms("right_button", "");
            pose_right_button = resp_right_button_ms.pose
            header_right_button = resp_right_button_ms.header
            header_right_button.frame_id = frameid_var
            poseStamped_right_button = PoseStamped(header=header_right_button, pose=pose_right_button)
            pub_right_button_pose.publish(blockPoseToGripper(poseStamped_right_button))
        except rospy.ServiceException, e:
            rospy.logerr("get_model_state for right_button service call failed: {0}".format(e))

        #Get left_button pose
        rospy.wait_for_service('/gazebo/get_model_state')
        try:
            left_button_ms = rospy.ServiceProxy('/gazebo/get_model_state', GetModelState)
            resp_left_button_ms = left_button_ms("left_button", "");
            pose_left_button = resp_left_button_ms.pose
            header_left_button = resp_left_button_ms.header
            header_left_button.frame_id = frameid_var
            poseStamped_left_button = PoseStamped(header=header_left_button, pose=pose_left_button)
            pub_left_button_pose.publish(blockPoseToGripper(poseStamped_left_button))
        except rospy.ServiceException, e:
            rospy.logerr("get_model_state for left_button service call failed: {0}".format(e))
        

        rospy.wait_for_service('/gazebo/get_link_state')

        lglfPose = None
        lgrfPose = None

        try:
            lglf_link_state = rospy.ServiceProxy('/gazebo/get_link_state', GetLinkState)
            resp_lglf_link_state = lglf_link_state('l_gripper_l_finger', 'world')
            lglfPose = resp_lglf_link_state.link_state.pose.position
        except rospy.ServiceException, e:
            rospy.logerr("get_link_state for l_gripper_l_finger: {0}".format(e))

        try:
            lgrf_link_state = rospy.ServiceProxy('/gazebo/get_link_state', GetLinkState)
            resp_lgrf_link_state = lgrf_link_state('l_gripper_r_finger', 'world')
            lgrfPose = resp_lgrf_link_state.link_state.pose.position
        except rospy.ServiceException, e:
            rospy.logerr("get_link_state for l_gripper_r_finger: {0}".format(e))

        # global leftGripperPose
        leftGripperPose = Point()
        leftGripperPose.x = (lglfPose.x + lgrfPose.x)/2
        leftGripperPose.y = (lglfPose.y + lgrfPose.y)/2
        leftGripperPose.z = (lglfPose.z + lgrfPose.z)/2
        pub_left_gripper_pose.publish(leftGripperPose)

        # print("Left Gripper Pose: ")
        # print(leftGripperPose)


        rospy.wait_for_service('/gazebo/get_link_state')
        
        rglfPose = None
        rgrfPose = None

        try:
            rglf_link_state = rospy.ServiceProxy('/gazebo/get_link_state', GetLinkState)
            resp_rglf_link_state = rglf_link_state('r_gripper_l_finger', 'world')
            rglfPose = resp_rglf_link_state.link_state.pose.position
        except rospy.ServiceException, e:
            rospy.logerr("get_link_state for r_gripper_l_finger: {0}".format(e))

        try:
            rgrf_link_state = rospy.ServiceProxy('/gazebo/get_link_state', GetLinkState)
            resp_rgrf_link_state = rgrf_link_state('r_gripper_r_finger', 'world')
            rgrfPose = resp_rgrf_link_state.link_state.pose.position
        except rospy.ServiceException, e:
            rospy.logerr("get_link_state for r_gripper_r_finger: {0}".format(e))

        # global rightGripperPose
        rightGripperPose = Point()
        rightGripperPose.x = (rglfPose.x + rgrfPose.x)/2
        rightGripperPose.y = (rglfPose.y + rgrfPose.y)/2
        rightGripperPose.z = (rglfPose.z + rgrfPose.z)/2
        pub_right_gripper_pose.publish(rightGripperPose)

        # print("Right Gripper Pose: ")
        # print(rightGripperPose)











    rate.sleep()

    return 0

if __name__ == '__main__':
    sys.exit(main())
