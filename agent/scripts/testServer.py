#!/usr/bin/env python

from agent.srv import PressButtonSrv, CloseGripperSrv, OpenGripperSrv, ObtainObjectSrv
import rospy

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

def main():
    rospy.init_node("test_node")
    print("Inside testServer.py")


    # rospy.wait_for_service('press_button_srv', timeout=60)
    # print("Ready to call service")
    # try:
    #     b = rospy.ServiceProxy('press_button_srv', PressButtonSrv)
    #     resp = b('left', 'left_button')
    #     print(resp.success_bool)
    # except rospy.ServiceException, e:
    #     print("Service call failed: %s"%e)

    rospy.wait_for_service('obtain_object_srv', timeout=60)
    print("Ready to call service")
    try:
        b = rospy.ServiceProxy('obtain_object_srv', ObtainObjectSrv)
        resp = b('left', 'block')
        print(resp.success_bool)
    except rospy.ServiceException, e:
        print("Service call failed: %s"%e)

if __name__ == "__main__":
    main()
